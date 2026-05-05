from __future__ import annotations

from typing import TYPE_CHECKING

from engine.models.character import CharacterState

if TYPE_CHECKING:
    from engine.systems.battle import BattleState

REWARD_VICTORY = 10.0
REWARD_DEFEAT = -10.0
REWARD_KILL = 6.0
REWARD_KNOCKDOWN = 1.0
REWARD_ALLY_DEAD = -2.0
REWARD_DAMAGE_PCT = 2.0
REWARD_HEAL_SELF_PCT = 0.8
REWARD_HEAL_ALLY_PCT = 3.0
REWARD_COMBO = 0.5
REWARD_TIME_PENALTY = -0.04
REWARD_APPROACH_MELEE = 0.15
REWARD_FOLLOWUP_MELEE = 0.4
REWARD_SAVE_ALLY = 4.0
REWARD_FRIENDLY_FIRE = -4.0
REWARD_SELFISH_HEAL = -1.5
SELFISH_HEAL_HP_GAP = 0.2

MELEE_CLASSES = frozenset({"warrior", "assassin"})


def _max_hp(battle_state: "BattleState | None", entity_id: str) -> int:
    if battle_state is None or not entity_id:
        return 100
    try:
        return max(battle_state.get_character(entity_id).max_hp, 1)
    except (KeyError, AttributeError):
        return 100


def _current_hp(battle_state: "BattleState | None", entity_id: str) -> int:
    if battle_state is None or not entity_id:
        return 0
    try:
        return battle_state.get_character(entity_id).current_hp
    except (KeyError, AttributeError):
        return 0


def _missing_hp_pct_before_heal(
    battle_state: "BattleState | None", entity_id: str, applied_heal: int
) -> float:
    max_hp = _max_hp(battle_state, entity_id)
    hp_after = _current_hp(battle_state, entity_id)
    hp_before = hp_after - applied_heal
    missing_before = max_hp - hp_before
    return min(max(missing_before / max_hp, 0.0), 1.0)


def _hp_pct(battle_state: "BattleState | None", entity_id: str) -> float:
    max_hp = _max_hp(battle_state, entity_id)
    return min(max(_current_hp(battle_state, entity_id) / max_hp, 0.0), 1.0)


def _lowest_ally_hp_pct(
    battle_state: "BattleState | None",
    healer_id: str,
    healer_team: str,
    all_agents: dict[str, str],
) -> float | None:
    if battle_state is None:
        return None
    lowest: float | None = None
    for eid, team in all_agents.items():
        if eid == healer_id or team != healer_team:
            continue
        try:
            char = battle_state.get_character(eid)
        except KeyError:
            continue
        if char.state == CharacterState.DEAD:
            continue
        pct = _hp_pct(battle_state, eid)
        if lowest is None or pct < lowest:
            lowest = pct
    return lowest


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
                attacker_team = all_agents.get(attacker, "")
                target_team = all_agents.get(target, "")
                if attacker_team and attacker_team == target_team:
                    rewards[attacker] += pct * REWARD_FRIENDLY_FIRE
                else:
                    rewards[attacker] += pct * REWARD_DAMAGE_PCT
                    if (
                        etype in ("basic_attack", "ability")
                        and battle_state is not None
                    ):
                        try:
                            atk_class = battle_state.get_character(
                                attacker
                            ).character_class.value
                        except (KeyError, AttributeError):
                            atk_class = ""
                        if atk_class in MELEE_CLASSES:
                            try:
                                ability = event.get("ability_id", "")
                                ap = battle_state.get_position(attacker)
                                tp = battle_state.get_position(target)
                                dist = max(abs(ap.x - tp.x), abs(ap.y - tp.y))
                            except (KeyError, AttributeError):
                                dist = 99
                            if dist <= 1:
                                rewards[attacker] += REWARD_FOLLOWUP_MELEE

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
                missing_pct = _missing_hp_pct_before_heal(
                    battle_state, target, amount
                )
                if target == healer:
                    rewards[healer] += pct * REWARD_HEAL_SELF_PCT * missing_pct
                    healer_team = all_agents.get(healer, "")
                    healer_pct = _hp_pct(battle_state, healer)
                    lowest_ally = _lowest_ally_hp_pct(
                        battle_state, healer, healer_team, all_agents
                    )
                    if (
                        lowest_ally is not None
                        and healer_pct - lowest_ally > SELFISH_HEAL_HP_GAP
                    ):
                        rewards[healer] += REWARD_SELFISH_HEAL * pct
                else:
                    rewards[healer] += pct * REWARD_HEAL_ALLY_PCT * (
                        missing_pct ** 1.5
                    )
                    if missing_pct > 0:
                        rewards[healer] += missing_pct ** 2 * REWARD_SAVE_ALLY

        elif etype == "hot_tick":
            heal = event.get("heal", 0)
            entity = event.get("entity", "")
            if heal > 0 and entity in rewards:
                entity_max_hp = _max_hp(battle_state, entity)
                pct = min(heal / entity_max_hp, 1.0)
                missing_pct = _missing_hp_pct_before_heal(
                    battle_state, entity, heal
                )
                for eid, team in all_agents.items():
                    if team == all_agents.get(entity, ""):
                        rewards[eid] += pct * REWARD_HEAL_ALLY_PCT * missing_pct * 0.5

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

        elif etype == "move":
            entity = event.get("entity", "")
            if entity not in rewards or battle_state is None:
                continue
            from_pos = event.get("from")
            to_pos = event.get("to")
            if from_pos is None or to_pos is None:
                continue
            try:
                char_class = battle_state.get_character(entity).character_class.value
            except (KeyError, AttributeError):
                continue
            if char_class not in MELEE_CLASSES:
                continue
            entity_team = all_agents.get(entity, "")
            min_old: int | None = None
            min_new: int | None = None
            for eid, team in all_agents.items():
                if team == entity_team or eid == entity:
                    continue
                try:
                    ec = battle_state.get_character(eid)
                except KeyError:
                    continue
                if ec.state == CharacterState.DEAD:
                    continue
                try:
                    epos = battle_state.get_position(eid)
                except KeyError:
                    continue
                old_d = max(abs(epos.x - from_pos.x), abs(epos.y - from_pos.y))
                new_d = max(abs(epos.x - to_pos.x), abs(epos.y - to_pos.y))
                if min_old is None or old_d < min_old:
                    min_old = old_d
                if min_new is None or new_d < min_new:
                    min_new = new_d
            if min_old is not None and min_new is not None:
                rewards[entity] += (min_old - min_new) * REWARD_APPROACH_MELEE

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
