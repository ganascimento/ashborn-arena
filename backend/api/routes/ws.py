import asyncio
import logging
import random

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.ai_agent import get_ai_action
from backend.api.ws_helpers import (
    make_action_result,
    make_ai_action,
    make_battle_end,
    make_error,
    make_turn_end,
    make_turn_start,
    serialize_events,
)
from backend.inference import get_inference_action, get_policies
from backend.sessions import session_manager
from engine.models.character import CharacterState
from engine.systems.battle import (
    ACTION_ABILITY_1,
    ACTION_BASIC,
    ACTION_END_TURN,
    ACTION_MOVE,
    ACTION_PASS,
)

logger = logging.getLogger(__name__)

router = APIRouter()

_AI_READY_TIMEOUT = 10
_AI_MAX_RETRIES = 5

_ACTION_TYPE_NAMES = {
    ACTION_MOVE: "move",
    ACTION_BASIC: "basic_attack",
    ACTION_END_TURN: "end_turn",
    ACTION_PASS: "end_turn",
}
for _i in range(5):
    _ACTION_TYPE_NAMES[ACTION_ABILITY_1 + _i] = "ability"


async def _advance_to_active(ws: WebSocket, battle) -> str | None:
    while not battle.is_over:
        events = battle.process_turn_start()

        if not battle.is_over:
            battle._winner = battle.check_victory()

        agent = battle.current_agent
        char = battle.get_character(agent)

        if events:
            for event in serialize_events(events):
                await ws.send_json({"type": "skip_event", **event})

        if battle.is_over:
            return None

        if char.state == CharacterState.ACTIVE:
            pa = battle.get_pa(agent)
            await ws.send_json(make_turn_start(agent, pa, events))
            return agent

    return None


def _translate_player_action(
    battle, char_id: str, data: dict
) -> tuple[int | None, int]:
    action = data.get("action")
    target = data.get("target")

    if action == "move":
        if not isinstance(target, list) or len(target) != 2:
            return None, 0
        return ACTION_MOVE, target[1] * 10 + target[0]

    if action == "basic_attack":
        if not isinstance(target, list) or len(target) != 2:
            return None, 0
        return ACTION_BASIC, target[1] * 10 + target[0]

    if action == "ability":
        ability_id = data.get("ability")
        if not ability_id:
            return None, 0
        equipped = battle.get_equipped_abilities(char_id)
        slot = None
        for i, ab in enumerate(equipped):
            if ab.id == ability_id:
                slot = i
                break
        if slot is None:
            return None, 0
        if isinstance(target, list) and len(target) == 2:
            tile = target[1] * 10 + target[0]
        else:
            return None, 0
        return ACTION_ABILITY_1 + slot, tile

    if action == "end_turn":
        return ACTION_END_TURN, 0

    return None, 0


async def _handle_player_turn(ws: WebSocket, battle, agent: str, player_ids: set[str]):
    while not battle.is_over:
        try:
            data = await ws.receive_json()
        except ValueError:
            await ws.send_json(make_error("Malformed JSON"))
            continue

        if data.get("type") == "ready":
            continue

        if data.get("type") != "action":
            await ws.send_json(make_error("Expected action message"))
            continue

        char_id = data.get("character")
        if char_id not in player_ids:
            await ws.send_json(
                make_error(f"Character {char_id} is not a player character")
            )
            continue
        if char_id != battle.current_agent:
            await ws.send_json(
                make_error(f"Not {char_id}'s turn, current is {battle.current_agent}")
            )
            continue

        action_str = data.get("action")
        action_type, target_tile = _translate_player_action(battle, char_id, data)
        if action_type is None:
            await ws.send_json(make_error(f"Invalid action: {action_str}"))
            continue

        events = battle.execute_action(action_type, target_tile)
        pa = battle.get_pa(char_id)
        extra: dict = {"pa": pa}
        if action_str == "ability":
            extra["ability"] = data.get("ability")
        await ws.send_json(make_action_result(char_id, action_str, events, **extra))

        if action_str == "end_turn":
            if not battle.is_over:
                await ws.send_json(make_turn_end(agent, battle.current_agent))
            return
        if battle.is_over:
            return


def _get_ai_decision(
    battle, agent: str, rng: random.Random, policies=None
) -> tuple[int, int]:
    if policies:
        class_name = battle.get_character(agent).character_class.value
        policy = policies.get(class_name)
        if policy:
            try:
                return get_inference_action(battle, agent, policy)
            except Exception:
                logger.exception("Inference failed for %s, falling back to heuristic AI", agent)
    return get_ai_action(battle, agent, rng)


async def _handle_ai_turn(
    ws: WebSocket, battle, agent: str, rng: random.Random, policies=None
):
    retries = 0

    while not battle.is_over and battle.current_agent == agent:
        action_type, target_tile = _get_ai_decision(
            battle, agent, rng, policies
        )

        pa_before = battle.get_pa(agent)
        events = battle.execute_action(action_type, target_tile)

        if (
            not events
            and battle.current_agent == agent
            and battle.get_pa(agent) == pa_before
            and action_type not in (ACTION_END_TURN, ACTION_PASS)
        ):
            retries += 1
            logger.warning(
                "AI action had no effect for %s (attempt %d/%d)",
                agent, retries, _AI_MAX_RETRIES,
            )
            if retries >= _AI_MAX_RETRIES:
                logger.warning("Forcing end_turn for %s after %d failed actions", agent, retries)
                events = battle.execute_action(ACTION_END_TURN, 0)
                await ws.send_json(make_ai_action(agent, "end_turn", events))
                break
            continue
        retries = 0

        action_name = _ACTION_TYPE_NAMES.get(action_type, "end_turn")
        await ws.send_json(make_ai_action(agent, action_name, events))

        if action_type in (ACTION_END_TURN, ACTION_PASS):
            break

        if battle.current_agent != agent:
            break

        try:
            await asyncio.wait_for(ws.receive_json(), timeout=_AI_READY_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning("Timed out waiting for ready from client during %s turn, forcing end_turn", agent)
            events = battle.execute_action(ACTION_END_TURN, 0)
            await ws.send_json(make_ai_action(agent, "end_turn", events))
            break
        except ValueError:
            pass

    if not battle.is_over:
        await ws.send_json(make_turn_end(agent, battle.current_agent))


@router.websocket("/battle/{session_id}")
async def battle_websocket(websocket: WebSocket, session_id: str):
    session = session_manager.get(session_id)
    if not session:
        await websocket.close(code=4004)
        return

    await websocket.accept()
    battle = session.battle_state
    player_ids = set(session.player_entity_ids)
    auto_battle = session.auto_battle
    rng = random.Random()
    policies = get_policies(session.difficulty)

    try:
        while not battle.is_over:
            agent = await _advance_to_active(websocket, battle)
            if agent is None or battle.is_over:
                break

            if agent in player_ids and not auto_battle:
                await _handle_player_turn(websocket, battle, agent, player_ids)
            else:
                await _handle_ai_turn(websocket, battle, agent, rng, policies)

        result = "victory" if battle.winner == "team_a" else "defeat"
        await websocket.send_json(make_battle_end(result))
    except WebSocketDisconnect:
        pass
    finally:
        session_manager.remove(session_id)
