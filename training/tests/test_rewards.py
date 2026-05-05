from dataclasses import dataclass

import pytest

from training.environment.rewards import (
    REWARD_HEAL_ALLY_PCT,
    REWARD_HEAL_SELF_PCT,
    REWARD_SAVE_ALLY,
    compute_rewards,
)


class _State:
    pass


@dataclass
class _Character:
    current_hp: int
    max_hp: int
    state: _State = _State()


class _BattleState:
    def __init__(self, characters: dict[str, _Character]) -> None:
        self._characters = characters

    def get_character(self, entity_id: str) -> _Character:
        return self._characters[entity_id]


def _ally_heal_reward(amount: int, hp_after: int, max_hp: int = 100) -> float:
    rewards = compute_rewards(
        [{"type": "heal", "healer": "cleric", "target": "ally", "amount": amount}],
        agent_id="cleric",
        agent_team="team_a",
        all_agents={"cleric": "team_a", "ally": "team_a"},
        battle_state=_BattleState(
            {
                "cleric": _Character(100, 100),
                "ally": _Character(hp_after, max_hp),
            }
        ),
    )
    return rewards["cleric"]


def _expected_ally_heal_reward(amount: int, hp_after: int, max_hp: int = 100) -> float:
    pct = amount / max_hp
    missing = max(0.0, min(1.0, (max_hp - (hp_after - amount)) / max_hp))
    return pct * REWARD_HEAL_ALLY_PCT * (missing ** 1.5) + missing ** 2 * REWARD_SAVE_ALLY


def test_ally_heal_reward_is_weighted_by_missing_hp_before_heal():
    low_urgency = _ally_heal_reward(amount=10, hp_after=100)
    high_urgency = _ally_heal_reward(amount=10, hp_after=30)

    assert low_urgency == pytest.approx(_expected_ally_heal_reward(10, 100))
    assert high_urgency == pytest.approx(_expected_ally_heal_reward(10, 30))
    assert high_urgency > low_urgency


def test_zero_applied_heal_has_no_reward():
    assert _ally_heal_reward(amount=0, hp_after=100) == 0.0


def test_self_heal_uses_self_pct_constant():
    rewards = compute_rewards(
        [{"type": "self_heal", "entity": "cleric", "heal": 10}],
        agent_id="cleric",
        agent_team="team_a",
        all_agents={"cleric": "team_a"},
        battle_state=_BattleState({"cleric": _Character(current_hp=30, max_hp=100)}),
    )

    assert rewards["cleric"] == pytest.approx((10 / 100) * REWARD_HEAL_SELF_PCT * 0.80)


def test_selfish_self_heal_is_penalized_when_ally_is_lower():
    rewards = compute_rewards(
        [{"type": "self_heal", "entity": "cleric", "heal": 10}],
        agent_id="cleric",
        agent_team="team_a",
        all_agents={"cleric": "team_a", "ally": "team_a"},
        battle_state=_BattleState(
            {
                "cleric": _Character(current_hp=80, max_hp=100),
                "ally": _Character(current_hp=20, max_hp=100),
            }
        ),
    )

    assert rewards["cleric"] < 0
