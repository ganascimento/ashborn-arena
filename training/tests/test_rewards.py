from dataclasses import dataclass

import pytest

from training.environment.rewards import (
    REWARD_HEAL_ALLY_PCT,
    REWARD_HEAL_SELF_PCT,
    REWARD_SAVE_ALLY,
    REWARD_WASTED_HEAL,
    WASTED_HEAL_HP_PCT,
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
    base = pct * REWARD_HEAL_ALLY_PCT * (missing ** 2) + missing ** 2 * REWARD_SAVE_ALLY
    hp_before_pct = max(0.0, (hp_after - amount) / max_hp)
    if hp_before_pct >= WASTED_HEAL_HP_PCT:
        base += REWARD_WASTED_HEAL
    return base


def test_ally_heal_reward_is_weighted_by_missing_hp_before_heal():
    low_urgency = _ally_heal_reward(amount=10, hp_after=60)
    high_urgency = _ally_heal_reward(amount=10, hp_after=30)

    assert low_urgency == pytest.approx(_expected_ally_heal_reward(10, 60))
    assert high_urgency == pytest.approx(_expected_ally_heal_reward(10, 30))
    assert high_urgency > low_urgency


def test_wasted_heal_on_full_ally_is_penalized():
    reward = _ally_heal_reward(amount=10, hp_after=100)
    assert reward < 0


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

    assert rewards["cleric"] == pytest.approx(
        (10 / 100) * REWARD_HEAL_SELF_PCT * (0.80 ** 3)
    )


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


def test_neglect_penalty_when_healthy_self_heals_with_critical_ally():
    rewards = compute_rewards(
        [{"type": "self_heal", "entity": "cleric", "heal": 10}],
        agent_id="cleric",
        agent_team="team_a",
        all_agents={"cleric": "team_a", "ally": "team_a"},
        battle_state=_BattleState(
            {
                "cleric": _Character(current_hp=85, max_hp=100),
                "ally": _Character(current_hp=30, max_hp=100),
            }
        ),
    )
    assert rewards["cleric"] < -0.2


def test_self_heal_at_high_hp_gives_almost_nothing():
    rewards = compute_rewards(
        [{"type": "self_heal", "entity": "cleric", "heal": 10}],
        agent_id="cleric",
        agent_team="team_a",
        all_agents={"cleric": "team_a"},
        battle_state=_BattleState({"cleric": _Character(current_hp=85, max_hp=100)}),
    )
    assert 0 <= rewards["cleric"] < 0.05
