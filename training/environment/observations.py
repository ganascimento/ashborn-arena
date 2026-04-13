from __future__ import annotations

import numpy as np

from engine.models.character import CharacterClass, CharacterState
from engine.models.effect import EffectType
from engine.models.map_object import ObjectType
from engine.systems.battle import BattleState
from engine.systems.elemental import has_negative_status

OBS_SELF_SIZE = 22
OBS_ENTITY_SIZE = 12
OBS_MAP_SIZE = 80
OBS_TOTAL_SIZE = (
    OBS_SELF_SIZE + 2 * OBS_ENTITY_SIZE + 3 * OBS_ENTITY_SIZE + OBS_MAP_SIZE
)

_CLASS_ORDER = [
    CharacterClass.WARRIOR,
    CharacterClass.MAGE,
    CharacterClass.CLERIC,
    CharacterClass.ARCHER,
    CharacterClass.ASSASSIN,
]


def _one_hot_class(cls: CharacterClass) -> list[float]:
    return [1.0 if c == cls else 0.0 for c in _CLASS_ORDER]


def _encode_entity(battle_state: BattleState, entity_id: str) -> list[float]:
    char = battle_state.get_character(entity_id)
    pos = battle_state.get_position(entity_id)
    em = battle_state.get_effect_manager()

    result = _one_hot_class(char.character_class)
    result.append(char.current_hp / max(char.max_hp, 1))
    result.append(pos.x / 9.0)
    result.append(pos.y / 7.0)
    result.append(1.0 if char.is_knocked_out else 0.0)
    result.append(1.0 if has_negative_status(em, entity_id) else 0.0)
    has_buff = any(e.effect_type == EffectType.BUFF for e in em.get_effects(entity_id))
    result.append(1.0 if has_buff else 0.0)
    result.append(1.0)
    return result


def _empty_entity() -> list[float]:
    return [0.0] * OBS_ENTITY_SIZE


def encode_observation(battle_state: BattleState, agent_id: str) -> np.ndarray:
    char = battle_state.get_character(agent_id)
    pos = battle_state.get_position(agent_id)
    em = battle_state.get_effect_manager()
    team = battle_state.get_team(agent_id)

    obs: list[float] = []

    obs.extend(_one_hot_class(char.character_class))
    obs.append(char.current_hp / max(char.max_hp, 1))
    obs.append(battle_state.get_pa(agent_id) / 4.0)
    obs.append(pos.x / 9.0)
    obs.append(pos.y / 7.0)

    abilities = battle_state.get_equipped_abilities(agent_id)
    for i in range(5):
        if i < len(abilities):
            cd = battle_state._turn_manager.get_cooldown(agent_id, i)
            max_cd = abilities[i].cooldown if abilities[i].cooldown > 0 else 1
            obs.append(cd / max_cd)
        else:
            obs.append(0.0)

    obs.append(char.attributes.modifier("str") / 9.0)
    obs.append(char.attributes.modifier("dex") / 9.0)
    obs.append(char.attributes.modifier("con") / 9.0)
    obs.append(char.attributes.modifier("int_") / 9.0)
    obs.append(char.attributes.modifier("wis") / 9.0)

    obs.append(1.0 if char.is_knocked_out else 0.0)
    obs.append(1.0 if has_negative_status(em, agent_id) else 0.0)
    has_buff = any(e.effect_type == EffectType.BUFF for e in em.get_effects(agent_id))
    obs.append(1.0 if has_buff else 0.0)

    allies = (
        battle_state.team_a_entities
        if team.value == "A"
        else battle_state.team_b_entities
    )
    ally_slots = [
        eid
        for eid in allies
        if eid != agent_id
        and battle_state.get_character(eid).state != CharacterState.DEAD
    ]
    for i in range(2):
        if i < len(ally_slots):
            obs.extend(_encode_entity(battle_state, ally_slots[i]))
        else:
            obs.extend(_empty_entity())

    enemies = (
        battle_state.team_b_entities
        if team.value == "A"
        else battle_state.team_a_entities
    )
    enemy_slots = [
        eid
        for eid in enemies
        if battle_state.get_character(eid).state != CharacterState.DEAD
    ]
    for i in range(3):
        if i < len(enemy_slots):
            obs.extend(_encode_entity(battle_state, enemy_slots[i]))
        else:
            obs.extend(_empty_entity())

    map_data = [0.0] * 80
    for obj in battle_state._map_objects.values():
        if obj.is_destroyed:
            continue
        idx = obj.position.y * 10 + obj.position.x
        val = float(list(ObjectType).index(obj.object_type) + 1)
        if obj.on_fire:
            val += 10.0
        map_data[idx] = val
    obs.extend(map_data)

    return np.array(obs, dtype=np.float32)


GLOBAL_STATE_MAX_AGENTS = 6
GLOBAL_STATE_SIZE = OBS_TOTAL_SIZE * GLOBAL_STATE_MAX_AGENTS


def encode_global_state(battle_state: BattleState) -> np.ndarray:
    all_obs: list[float] = []
    entities = battle_state.all_entities
    for i in range(GLOBAL_STATE_MAX_AGENTS):
        if i < len(entities):
            eid = entities[i]
            char = battle_state.get_character(eid)
            if char.state != CharacterState.DEAD:
                entity_obs = encode_observation(battle_state, eid)
                all_obs.extend(entity_obs.tolist())
            else:
                all_obs.extend([0.0] * OBS_TOTAL_SIZE)
        else:
            all_obs.extend([0.0] * OBS_TOTAL_SIZE)
    return np.array(all_obs, dtype=np.float32)
