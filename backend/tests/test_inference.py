import random

from engine.models.character import CharacterClass
from engine.systems.battle import BattleState
from training.agents.networks import PolicyNetwork


def _create_battle(seed=42):
    return BattleState.from_config(
        [(CharacterClass.WARRIOR, (5, 0, 5, 0, 0))],
        [(CharacterClass.ARCHER, (0, 5, 5, 0, 0))],
        rng=random.Random(seed),
    )


# ---------------------------------------------------------------------------
# Model Loading
# ---------------------------------------------------------------------------


class TestModelLoading:
    def test_get_policies_loads_all_classes(self):
        from backend.inference.model_loader import clear_cache, get_policies

        clear_cache()
        policies = get_policies("easy")
        assert policies is not None
        assert set(policies.keys()) == {
            "warrior",
            "mage",
            "cleric",
            "archer",
            "assassin",
        }
        for policy in policies.values():
            assert isinstance(policy, PolicyNetwork)

    def test_get_policies_caches(self):
        from backend.inference.model_loader import clear_cache, get_policies

        clear_cache()
        first = get_policies("easy")
        second = get_policies("easy")
        assert first is second

    def test_get_policies_eval_mode(self):
        from backend.inference.model_loader import clear_cache, get_policies

        clear_cache()
        policies = get_policies("easy")
        assert policies is not None
        for policy in policies.values():
            assert not policy.training

    def test_get_policies_invalid_difficulty(self):
        from backend.inference.model_loader import clear_cache, get_policies

        clear_cache()
        result = get_policies("impossible")
        assert result is None

    def test_get_policies_all_difficulties(self):
        from backend.inference.model_loader import clear_cache, get_policies

        clear_cache()
        for difficulty in ("easy", "normal", "hard"):
            policies = get_policies(difficulty)
            assert policies is not None, f"Failed to load {difficulty}"
            assert len(policies) == 5


# ---------------------------------------------------------------------------
# Action Generation
# ---------------------------------------------------------------------------


class TestInferenceAction:
    def test_returns_tuple_of_ints(self):
        from backend.inference.inference_agent import get_inference_action
        from backend.inference.model_loader import clear_cache, get_policies

        clear_cache()
        policies = get_policies("easy")
        assert policies is not None

        battle = _create_battle()
        ai_id = battle.team_b_entities[0]
        class_name = battle.get_character(ai_id).character_class.value
        policy = policies[class_name]

        action_type, target = get_inference_action(battle, ai_id, policy)
        assert isinstance(action_type, int)
        assert isinstance(target, int)
        assert 0 <= action_type <= 9
        assert 0 <= target <= 79

    def test_valid_action_type(self):
        from backend.inference.inference_agent import get_inference_action
        from backend.inference.model_loader import clear_cache, get_policies
        from training.environment.actions import compute_action_mask

        clear_cache()
        policies = get_policies("easy")
        assert policies is not None

        battle = _create_battle()
        ai_id = battle.team_b_entities[0]
        class_name = battle.get_character(ai_id).character_class.value
        policy = policies[class_name]

        masks = compute_action_mask(battle, ai_id)
        action_type, _ = get_inference_action(battle, ai_id, policy)
        assert masks["type_mask"][action_type], (
            f"Action type {action_type} was masked (invalid)"
        )

    def test_no_exception_during_inference(self):
        from backend.inference.inference_agent import get_inference_action
        from backend.inference.model_loader import clear_cache, get_policies

        clear_cache()
        for difficulty in ("easy", "normal", "hard"):
            policies = get_policies(difficulty)
            assert policies is not None

            battle = _create_battle()
            ai_id = battle.team_b_entities[0]
            class_name = battle.get_character(ai_id).character_class.value
            policy = policies[class_name]
            get_inference_action(battle, ai_id, policy)


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------


class TestFallback:
    def test_ws_works_without_models(self):
        import uuid

        from fastapi.testclient import TestClient

        from backend.main import app
        from backend.sessions import BattleSession, session_manager

        battle = _create_battle()
        session_id = str(uuid.uuid4())
        session = BattleSession(
            session_id=session_id,
            battle_state=battle,
            difficulty="impossible",
            player_entity_ids=battle.team_a_entities,
            ai_entity_ids=battle.team_b_entities,
        )
        session_manager._sessions[session_id] = session

        client = TestClient(app)
        with client.websocket_connect(f"/battle/{session_id}") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "turn_start"
