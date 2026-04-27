from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.systems.battle import BattleState

REWARD_VICTORY = 10.0
REWARD_DEFEAT = -10.0
REWARD_KILL = 3.0
REWARD_KNOCKDOWN = 1.0
REWARD_ALLY_DEAD = -2.0
REWARD_DAMAGE_PCT = 2.0
REWARD_HEAL_PCT = 2.0
REWARD_COMBO = 0.5


def _max_hp(battle_state: "BattleState | None", entity_id: str) -> int:
    if battle_state is None or not entity_id:
        return 100
    try:
        return max(battle_state.get_character(entity_id).max_hp, 1)
    except (KeyError, AttributeError):
        return 100


def compute_rewards(
    events: list[dict],
    agent_id: str,
    agent_team: str,
    all_agents: dict[str, str],
    battle_state: "BattleState | None" = None,
) -> dict[str, float]:
    rewards: dict[str, float] = {eid: 0.0 for eid in all_agents}

    for event in events:
        etype = event.get("type", "")

        if etype in (
            "basic_attack",
            "ability",
            "opportunity_attack",
            "aoe_hit",
            "chain_primary",
            "chain_secondary",
            "dot_tick",
            "trap_triggered",
        ):
            damage = event.get("damage", 0)
            attacker = event.get("attacker", "")
            target = event.get("target", "")
            if damage > 0 and attacker in rewards:
                target_max_hp = _max_hp(battle_state, target)
                pct = min(damage / target_max_hp, 1.0)
                rewards[attacker] += pct * REWARD_DAMAGE_PCT

        elif etype == "reflect":
            damage = event.get("damage", 0)
            reflector = event.get("source", "")
            target = event.get("target", "")
            if damage > 0 and reflector in rewards:
                target_max_hp = _max_hp(battle_state, target)
                pct = min(damage / target_max_hp, 1.0)
                rewards[reflector] += pct * REWARD_DAMAGE_PCT

        elif etype == "heal" or etype == "self_heal" or etype == "lifesteal":
            amount = event.get("amount", event.get("heal", 0))
            healer = event.get("healer", event.get("entity", ""))
            target = event.get("target", healer)
            if amount > 0 and healer in rewards:
                target_max_hp = _max_hp(battle_state, target)
                pct = min(amount / target_max_hp, 1.0)
                rewards[healer] += pct * REWARD_HEAL_PCT

        elif etype == "hot_tick":
            heal = event.get("heal", 0)
            entity = event.get("entity", "")
            if heal > 0 and entity in rewards:
                entity_max_hp = _max_hp(battle_state, entity)
                pct = min(heal / entity_max_hp, 1.0)
                for eid, team in all_agents.items():
                    if team == all_agents.get(entity, ""):
                        rewards[eid] += pct * REWARD_HEAL_PCT * 0.5

        elif etype == "knocked_out":
            entity = event.get("entity", "")
            entity_team = all_agents.get(entity, "")
            for eid, team in all_agents.items():
                if team != entity_team:
                    rewards[eid] += REWARD_KNOCKDOWN

        elif etype == "death":
            entity = event.get("entity", "")
            entity_team = all_agents.get(entity, "")
            for eid, team in all_agents.items():
                if team != entity_team:
                    rewards[eid] += REWARD_KILL
                elif team == entity_team and eid != entity:
                    rewards[eid] += REWARD_ALLY_DEAD

        elif etype == "combo":
            if agent_id in rewards:
                rewards[agent_id] += REWARD_COMBO

    return rewards


def apply_terminal_rewards(
    rewards: dict[str, float],
    winner: str,
    all_agents: dict[str, str],
) -> None:
    for eid, team in all_agents.items():
        if team == winner:
            rewards[eid] = rewards.get(eid, 0.0) + REWARD_VICTORY
        else:
            rewards[eid] = rewards.get(eid, 0.0) + REWARD_DEFEAT
