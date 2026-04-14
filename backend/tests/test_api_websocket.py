import random
import uuid

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.sessions import BattleSession, session_manager
from engine.models.character import CharacterClass
from engine.systems.battle import BattleState

client = TestClient(app)


def _create_session(
    team_a_classes=None,
    team_b_classes=None,
    team_a_builds=None,
    team_b_builds=None,
    seed=42,
):
    if team_a_classes is None:
        team_a_classes = [CharacterClass.ARCHER]
    if team_b_classes is None:
        team_b_classes = [CharacterClass.WARRIOR]
    if team_a_builds is None:
        team_a_builds = [(0, 5, 5, 0, 0)] * len(team_a_classes)
    if team_b_builds is None:
        team_b_builds = [(5, 0, 5, 0, 0)] * len(team_b_classes)

    team_a_config = list(zip(team_a_classes, team_a_builds))
    team_b_config = list(zip(team_b_classes, team_b_builds))

    rng = random.Random(seed)
    battle = BattleState.from_config(team_a_config, team_b_config, rng=rng)

    session_id = str(uuid.uuid4())
    session = BattleSession(
        session_id=session_id,
        battle_state=battle,
        difficulty="normal",
        player_entity_ids=battle.team_a_entities,
        ai_entity_ids=battle.team_b_entities,
    )
    session_manager._sessions[session_id] = session
    return session_id, battle


def _create_player_first_session():
    session_id, battle = _create_session(
        team_a_classes=[CharacterClass.ARCHER],
        team_b_classes=[CharacterClass.WARRIOR],
        team_a_builds=[(0, 5, 5, 0, 0)],
        team_b_builds=[(5, 0, 5, 0, 0)],
        seed=42,
    )
    assert battle.current_agent == battle.team_a_entities[0], (
        "Expected player to go first"
    )
    return session_id, battle


def _create_ai_first_session():
    session_id, battle = _create_session(
        team_a_classes=[CharacterClass.WARRIOR],
        team_b_classes=[CharacterClass.ARCHER],
        team_a_builds=[(5, 0, 5, 0, 0)],
        team_b_builds=[(0, 5, 5, 0, 0)],
        seed=42,
    )
    assert battle.current_agent == battle.team_b_entities[0], "Expected AI to go first"
    return session_id, battle


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------


class TestWSConnection:
    def test_connect_valid_session(self):
        session_id, battle = _create_player_first_session()
        with client.websocket_connect(f"/battle/{session_id}") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "turn_start"
            assert msg["character"] == battle.current_agent
            assert "pa" in msg
            assert "events" in msg

    def test_connect_invalid_session(self):
        fake_id = str(uuid.uuid4())
        with pytest.raises(Exception):
            with client.websocket_connect(f"/battle/{fake_id}") as ws:
                ws.receive_json()


# ---------------------------------------------------------------------------
# Player Actions
# ---------------------------------------------------------------------------


class TestPlayerActions:
    def test_player_move(self):
        session_id, battle = _create_player_first_session()
        player_id = battle.team_a_entities[0]
        pos = battle.get_position(player_id)
        reachable = battle.get_reachable_tiles(player_id)
        target = next(t for t in reachable if t != pos)

        with client.websocket_connect(f"/battle/{session_id}") as ws:
            turn_start = ws.receive_json()
            assert turn_start["type"] == "turn_start"

            ws.send_json(
                {
                    "type": "action",
                    "character": player_id,
                    "action": "move",
                    "target": [target.x, target.y],
                }
            )
            result = ws.receive_json()
            assert result["type"] == "action_result"
            assert result["character"] == player_id
            assert result["action"] == "move"
            assert "events" in result

    def test_player_end_turn(self):
        session_id, battle = _create_player_first_session()
        player_id = battle.team_a_entities[0]

        with client.websocket_connect(f"/battle/{session_id}") as ws:
            turn_start = ws.receive_json()
            assert turn_start["type"] == "turn_start"

            ws.send_json(
                {
                    "type": "action",
                    "character": player_id,
                    "action": "end_turn",
                }
            )
            result = ws.receive_json()
            assert result["type"] == "action_result"
            assert result["action"] == "end_turn"

            turn_end = ws.receive_json()
            assert turn_end["type"] == "turn_end"
            assert turn_end["character"] == player_id
            assert "next" in turn_end

    def test_player_wrong_character(self):
        session_id, battle = _create_player_first_session()
        ai_id = battle.team_b_entities[0]

        with client.websocket_connect(f"/battle/{session_id}") as ws:
            ws.receive_json()  # turn_start

            ws.send_json(
                {
                    "type": "action",
                    "character": ai_id,
                    "action": "end_turn",
                }
            )
            msg = ws.receive_json()
            assert msg["type"] == "error"
            assert "message" in msg

    def test_player_not_current_agent(self):
        session_id, battle = _create_session(
            team_a_classes=[CharacterClass.ARCHER, CharacterClass.WARRIOR],
            team_b_classes=[CharacterClass.MAGE],
            team_a_builds=[(0, 5, 5, 0, 0), (5, 0, 5, 0, 0)],
            team_b_builds=[(0, 0, 0, 5, 5)],
            seed=42,
        )
        player_ids = battle.team_a_entities
        current = battle.current_agent
        other_player = next(pid for pid in player_ids if pid != current)

        if current not in set(player_ids):
            pytest.skip("AI goes first with this seed")

        with client.websocket_connect(f"/battle/{session_id}") as ws:
            ws.receive_json()  # turn_start

            ws.send_json(
                {
                    "type": "action",
                    "character": other_player,
                    "action": "end_turn",
                }
            )
            msg = ws.receive_json()
            assert msg["type"] == "error"


# ---------------------------------------------------------------------------
# AI Turn
# ---------------------------------------------------------------------------


class TestAITurn:
    def test_ai_turn_sends_actions(self):
        session_id, battle = _create_ai_first_session()
        ai_id = battle.team_b_entities[0]

        with client.websocket_connect(f"/battle/{session_id}") as ws:
            turn_start = ws.receive_json()
            assert turn_start["type"] == "turn_start"
            assert turn_start["character"] == ai_id

            seen_ai_action = False
            seen_turn_end = False
            for _ in range(20):
                msg = ws.receive_json()
                if msg["type"] == "ai_action":
                    seen_ai_action = True
                    assert msg["character"] == ai_id
                    assert "action" in msg
                    assert "events" in msg
                    if msg["action"] == "end_turn":
                        continue
                    ws.send_json({"type": "ready"})
                elif msg["type"] == "turn_end":
                    seen_turn_end = True
                    assert msg["character"] == ai_id
                    assert "next" in msg
                    break
                elif msg["type"] == "turn_start":
                    break
                else:
                    break

            assert seen_ai_action, "Expected at least one ai_action message"
            assert seen_turn_end, "Expected turn_end after AI turn"

    def test_ai_turn_waits_for_ready(self):
        session_id, battle = _create_ai_first_session()

        with client.websocket_connect(f"/battle/{session_id}") as ws:
            ws.receive_json()  # turn_start

            first_action = ws.receive_json()
            assert first_action["type"] == "ai_action"

            if first_action["action"] != "end_turn":
                ws.send_json({"type": "ready"})
                second = ws.receive_json()
                assert second["type"] in ("ai_action", "turn_start")


# ---------------------------------------------------------------------------
# Battle End
# ---------------------------------------------------------------------------


class TestBattleEnd:
    def test_battle_end_victory(self):
        session_id, battle = _create_player_first_session()
        ai_id = battle.team_b_entities[0]

        ai_char = battle._characters[ai_id]
        ai_char.apply_damage(ai_char.current_hp + 11)
        battle._handle_death(ai_id)

        with client.websocket_connect(f"/battle/{session_id}") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "battle_end"
            assert msg["result"] == "victory"


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


class TestSerialization:
    def test_events_serialized_correctly(self):
        session_id, battle = _create_player_first_session()
        player_id = battle.team_a_entities[0]
        reachable = battle.get_reachable_tiles(player_id)
        pos = battle.get_position(player_id)
        target = next(t for t in reachable if t != pos)

        with client.websocket_connect(f"/battle/{session_id}") as ws:
            ws.receive_json()  # turn_start

            ws.send_json(
                {
                    "type": "action",
                    "character": player_id,
                    "action": "move",
                    "target": [target.x, target.y],
                }
            )
            result = ws.receive_json()
            for event in result.get("events", []):
                for key, val in event.items():
                    assert not hasattr(val, "x"), (
                        f"Position object not serialized in event key '{key}'"
                    )


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------


class TestCleanup:
    def test_session_removed_after_battle_end(self):
        session_id, battle = _create_player_first_session()
        ai_id = battle.team_b_entities[0]

        ai_char = battle._characters[ai_id]
        ai_char.apply_damage(ai_char.current_hp + 11)
        battle._handle_death(ai_id)

        with client.websocket_connect(f"/battle/{session_id}") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "battle_end"

        assert session_manager.get(session_id) is None
