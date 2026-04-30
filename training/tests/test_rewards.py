from dataclasses import dataclass

import pytest

from training.environment.rewards import REWARD_HEAL_PCT, compute_rewards


@dataclass
class _Character:
    current_hp: int
    max_hp: int


class _BattleState:
    def __init__(self, characters: dict[str, _Character]) -> None:
        self._characters = characters

    def get_character(self, entity_id: str) -> _Character:
        return self._characters[entity_id]


def _heal_reward(amount: int, hp_after: int, max_hp: int = 100) -> float:
    rewards = compute_rewards(
        [{"type": "heal", "healer": "cleric", "target": "ally", "amount": amount}],
        agent_id="cleric",
        agent_team="team_a",
        all_agents={"cleric": "team_a", "ally": "team_a"},
        battle_state=_BattleState({"ally": _Character(hp_after, max_hp)}),
    )
    return rewards["cleric"]


def test_heal_reward_is_weighted_by_missing_hp_before_heal():
    low_urgency = _heal_reward(amount=10, hp_after=100)
    high_urgency = _heal_reward(amount=10, hp_after=30)

    assert low_urgency == pytest.approx((10 / 100) * REWARD_HEAL_PCT * 0.10)
    assert high_urgency == pytest.approx((10 / 100) * REWARD_HEAL_PCT * 0.80)
    assert high_urgency > low_urgency


def test_zero_applied_heal_has_no_reward():
    assert _heal_reward(amount=0, hp_after=100) == 0.0


def test_self_heal_uses_same_missing_hp_weight():
    rewards = compute_rewards(
        [{"type": "self_heal", "entity": "cleric", "heal": 10}],
        agent_id="cleric",
        agent_team="team_a",
        all_agents={"cleric": "team_a"},
        battle_state=_BattleState({"cleric": _Character(current_hp=30, max_hp=100)}),
    )

    assert rewards["cleric"] == pytest.approx((10 / 100) * REWARD_HEAL_PCT * 0.80)
