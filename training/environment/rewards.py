from __future__ import annotations

REWARD_VICTORY = 10.0
REWARD_DEFEAT = -10.0
REWARD_KILL = 3.0
REWARD_KNOCKDOWN = 1.0
REWARD_ALLY_DEAD = -2.0
REWARD_DAMAGE = 0.1
REWARD_HEAL = 0.1
REWARD_COMBO = 0.5


def compute_rewards(
    events: list[dict],
    agent_id: str,
    agent_team: str,
    all_agents: dict[str, str],
) -> dict[str, float]:
    rewards: dict[str, float] = {eid: 0.0 for eid in all_agents}

    for event in events:
        etype = event.get("type", "")

        if etype in ("basic_attack", "ability", "opportunity_attack"):
            damage = event.get("damage", 0)
            attacker = event.get("attacker", "")
            if damage > 0 and attacker in rewards:
                rewards[attacker] += damage * REWARD_DAMAGE

        elif etype == "heal" or etype == "self_heal" or etype == "lifesteal":
            amount = event.get("amount", event.get("heal", 0))
            healer = event.get("healer", event.get("entity", ""))
            if amount > 0 and healer in rewards:
                rewards[healer] += amount * REWARD_HEAL

        elif etype == "hot_tick":
            heal = event.get("heal", 0)
            entity = event.get("entity", "")
            if heal > 0 and entity in rewards:
                for eid, team in all_agents.items():
                    if team == all_agents.get(entity, ""):
                        rewards[eid] += heal * REWARD_HEAL * 0.5

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
