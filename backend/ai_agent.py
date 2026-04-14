import random as _random

from engine.models.ability import Ability, AbilityTarget
from engine.models.character import CharacterState
from engine.models.grid import Team
from engine.models.position import Position
from engine.systems.battle import (
    ACTION_ABILITY_1,
    ACTION_BASIC,
    ACTION_END_TURN,
    ACTION_MOVE,
    BattleState,
)
from engine.systems.line_of_sight import has_line_of_sight


def _pos_to_tile(pos: Position) -> int:
    return pos.y * 10 + pos.x


def _chebyshev(a: Position, b: Position) -> int:
    return max(abs(a.x - b.x), abs(a.y - b.y))


def _get_enemies(battle: BattleState, entity_id: str) -> list[str]:
    team = battle.get_team(entity_id)
    if team == Team.A:
        candidates = battle.team_b_entities
    else:
        candidates = battle.team_a_entities
    return [
        eid
        for eid in candidates
        if battle.get_character(eid).state != CharacterState.DEAD
    ]


def _get_allies(battle: BattleState, entity_id: str) -> list[str]:
    team = battle.get_team(entity_id)
    if team == Team.A:
        candidates = battle.team_a_entities
    else:
        candidates = battle.team_b_entities
    return [
        eid
        for eid in candidates
        if eid != entity_id and battle.get_character(eid).state != CharacterState.DEAD
    ]


def _find_enemy_target(
    battle: BattleState,
    entity_id: str,
    ability: Ability,
    enemies: list[str],
) -> int | None:
    my_pos = battle.get_position(entity_id)
    blocking = battle.get_blocking_positions()
    needs_los = ability.max_range > 1

    for eid in enemies:
        enemy_pos = battle.get_position(eid)
        dist = _chebyshev(my_pos, enemy_pos)
        if dist > ability.max_range:
            continue
        if ability.min_range and dist < ability.min_range:
            continue
        if needs_los and not has_line_of_sight(my_pos, enemy_pos, blocking):
            continue
        return _pos_to_tile(enemy_pos)
    return None


def _find_ally_target(
    battle: BattleState, entity_id: str, ability: Ability
) -> int | None:
    allies = _get_allies(battle, entity_id)
    if not allies:
        return None

    my_pos = battle.get_position(entity_id)
    blocking = battle.get_blocking_positions()
    needs_los = ability.max_range > 1
    best_eid = None
    best_hp_pct = 2.0

    for eid in allies:
        ally_pos = battle.get_position(eid)
        dist = _chebyshev(my_pos, ally_pos)
        if dist > ability.max_range:
            continue
        if ability.min_range and dist < ability.min_range:
            continue
        if needs_los and not has_line_of_sight(my_pos, ally_pos, blocking):
            continue
        char = battle.get_character(eid)
        hp_pct = char.current_hp / max(char.max_hp, 1)
        if hp_pct < best_hp_pct:
            best_hp_pct = hp_pct
            best_eid = eid

    if best_eid is None:
        return None
    return _pos_to_tile(battle.get_position(best_eid))


def _find_target_for_ability(
    battle: BattleState,
    entity_id: str,
    ability: Ability,
    enemies: list[str],
) -> int | None:
    my_pos = battle.get_position(entity_id)

    if ability.target in (AbilityTarget.SINGLE_ENEMY, AbilityTarget.CHAIN):
        return _find_enemy_target(battle, entity_id, ability, enemies)

    if ability.target == AbilityTarget.AOE:
        return _find_enemy_target(battle, entity_id, ability, enemies)

    if ability.target == AbilityTarget.ADJACENT:
        return _pos_to_tile(my_pos)

    if ability.target == AbilityTarget.SELF:
        return _pos_to_tile(my_pos)

    if ability.target == AbilityTarget.SINGLE_ALLY:
        return _find_ally_target(battle, entity_id, ability)

    return None


def get_ai_action(
    battle: BattleState, entity_id: str, rng: _random.Random
) -> tuple[int, int]:
    pa = battle.get_pa(entity_id)
    enemies = _get_enemies(battle, entity_id)

    if not enemies:
        return (ACTION_END_TURN, 0)

    attack_options: list[tuple[int, int]] = []

    abilities = battle.get_equipped_abilities(entity_id)
    for slot, ability in enumerate(abilities):
        if pa < ability.pa_cost:
            continue
        if not battle._turn_manager.is_ability_ready(entity_id, slot):
            continue
        target_tile = _find_target_for_ability(battle, entity_id, ability, enemies)
        if target_tile is not None:
            attack_options.append((ACTION_ABILITY_1 + slot, target_tile))

    basic = battle.get_basic_attack(entity_id)
    if pa >= basic.pa_cost:
        target_tile = _find_enemy_target(battle, entity_id, basic, enemies)
        if target_tile is not None:
            attack_options.append((ACTION_BASIC, target_tile))

    if attack_options:
        return rng.choice(attack_options)

    reachable = battle.get_reachable_tiles(entity_id)
    if reachable:
        my_pos = battle.get_position(entity_id)
        nearest_enemy_pos = min(
            (battle.get_position(eid) for eid in enemies),
            key=lambda p: _chebyshev(my_pos, p),
        )
        best_tile = min(reachable, key=lambda t: _chebyshev(t, nearest_enemy_pos))
        if _chebyshev(best_tile, nearest_enemy_pos) < _chebyshev(
            my_pos, nearest_enemy_pos
        ):
            return (ACTION_MOVE, _pos_to_tile(best_tile))

    return (ACTION_END_TURN, 0)
