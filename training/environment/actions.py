from __future__ import annotations

from enum import IntEnum

import numpy as np

from engine.models.ability import AbilityTarget
from engine.models.character import CharacterState
from engine.models.position import Position
from engine.systems.battle import BattleState
from engine.systems.line_of_sight import has_line_of_sight

NUM_ACTION_TYPES = 10
NUM_TARGETS = 80


class ActionType(IntEnum):
    MOVE = 0
    BASIC_ATTACK = 1
    ABILITY_1 = 2
    ABILITY_2 = 3
    ABILITY_3 = 4
    ABILITY_4 = 5
    ABILITY_5 = 6
    THROW = 7
    END_TURN = 8
    PASS = 9


def _pos_to_idx(pos: Position) -> int:
    return pos.y * 10 + pos.x


def _idx_to_pos(idx: int) -> Position:
    return Position(idx % 10, idx // 10)


def compute_action_mask(battle_state: BattleState, agent_id: str) -> dict:
    type_mask = np.zeros(NUM_ACTION_TYPES, dtype=bool)
    target_mask = np.zeros((NUM_ACTION_TYPES, NUM_TARGETS), dtype=bool)

    char = battle_state.get_character(agent_id)
    if char.state != CharacterState.ACTIVE:
        type_mask[ActionType.END_TURN] = True
        target_mask[ActionType.END_TURN, 0] = True
        return {"type_mask": type_mask, "target_mask": target_mask}

    pa = battle_state.get_pa(agent_id)
    pos = battle_state.get_position(agent_id)
    team = battle_state.get_team(agent_id)
    blockers = battle_state.get_blocking_positions()

    type_mask[ActionType.END_TURN] = True
    target_mask[ActionType.END_TURN, 0] = True
    type_mask[ActionType.PASS] = True
    target_mask[ActionType.PASS, 0] = True

    if pa >= 1:
        reachable = battle_state.get_reachable_tiles(agent_id)
        if reachable:
            type_mask[ActionType.MOVE] = True
            for tile in reachable:
                target_mask[ActionType.MOVE, _pos_to_idx(tile)] = True

    em = battle_state.get_effect_manager()

    range_bonus_effect = em.get_effect(agent_id, "range_bonus")
    range_bonus = int(range_bonus_effect.value) if range_bonus_effect else 0

    basic = battle_state.get_basic_attack(agent_id)
    if pa >= basic.pa_cost:
        enemies = (
            battle_state.team_b_entities
            if team.value == "A"
            else battle_state.team_a_entities
        )
        for eid in enemies:
            echar = battle_state.get_character(eid)
            if echar.state == CharacterState.DEAD:
                continue
            if em.has_effect(eid, "untargetable"):
                continue
            epos = battle_state.get_position(eid)
            effective_range = basic.max_range + (range_bonus if basic.max_range > 1 else 0)
            dist = max(abs(epos.x - pos.x), abs(epos.y - pos.y))
            if dist > effective_range:
                continue
            if effective_range > 1 and not has_line_of_sight(pos, epos, blockers):
                continue
            type_mask[ActionType.BASIC_ATTACK] = True
            target_mask[ActionType.BASIC_ATTACK, _pos_to_idx(epos)] = True

    abilities = battle_state.get_equipped_abilities(agent_id)
    for i, ability in enumerate(abilities):
        action_idx = ActionType.ABILITY_1 + i
        if pa < ability.pa_cost:
            continue
        if not battle_state._turn_manager.is_ability_ready(agent_id, i):
            continue

        if ability.target == AbilityTarget.SELF:
            type_mask[action_idx] = True
            target_mask[action_idx, _pos_to_idx(pos)] = True
        elif ability.target in (AbilityTarget.SINGLE_ENEMY, AbilityTarget.CHAIN):
            enemies = (
                battle_state.team_b_entities
                if team.value == "A"
                else battle_state.team_a_entities
            )
            for eid in enemies:
                echar = battle_state.get_character(eid)
                if echar.state == CharacterState.DEAD:
                    continue
                if em.has_effect(eid, "untargetable"):
                    continue
                epos = battle_state.get_position(eid)
                eff_range = ability.max_range + (range_bonus if ability.max_range > 1 else 0)
                dist = max(abs(epos.x - pos.x), abs(epos.y - pos.y))
                if dist > eff_range:
                    continue
                if eff_range > 1 and not has_line_of_sight(pos, epos, blockers):
                    continue
                type_mask[action_idx] = True
                target_mask[action_idx, _pos_to_idx(epos)] = True
        elif ability.target == AbilityTarget.SINGLE_ALLY:
            allies = (
                battle_state.team_a_entities
                if team.value == "A"
                else battle_state.team_b_entities
            )
            for eid in allies:
                achar = battle_state.get_character(eid)
                if achar.state == CharacterState.DEAD:
                    continue
                apos = battle_state.get_position(eid)
                dist = max(abs(apos.x - pos.x), abs(apos.y - pos.y))
                if dist > ability.max_range:
                    continue
                type_mask[action_idx] = True
                target_mask[action_idx, _pos_to_idx(apos)] = True
        elif ability.target in (AbilityTarget.AOE, AbilityTarget.ADJACENT):
            type_mask[action_idx] = True
            if ability.target == AbilityTarget.ADJACENT:
                target_mask[action_idx, _pos_to_idx(pos)] = True
            else:
                for row in range(8):
                    for col in range(10):
                        tile = Position(col, row)
                        dist = max(abs(tile.x - pos.x), abs(tile.y - pos.y))
                        if dist <= ability.max_range:
                            target_mask[action_idx, _pos_to_idx(tile)] = True

    return {"type_mask": type_mask, "target_mask": target_mask}
