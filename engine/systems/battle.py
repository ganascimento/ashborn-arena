from __future__ import annotations

import random as _random

from engine.generation.map_generator import Biome, generate_map
from engine.models.ability import (
    ABILITIES,
    BASIC_ATTACKS,
    Ability,
    AbilityTarget,
    BuffDef,
)
from engine.models.character import (
    BASE_ATTRIBUTES,
    Attributes,
    Character,
    CharacterClass,
    CharacterState,
)
from engine.models.effect import Effect, EffectType
from engine.models.grid import Grid, Occupant, OccupantType, Team
from engine.models.map_object import MapObject
from engine.models.position import Position
from engine.systems.damage import (
    calculate_raw_damage,
    resolve_healing,
    resolve_magical_attack,
    resolve_physical_attack,
)
from engine.systems.effect_manager import EffectManager
from engine.systems.elemental import check_elemental_combo, has_negative_status
from engine.systems.initiative import determine_turn_order
from engine.systems.movement import execute_move, get_reachable_tiles, tiles_for_pa
from engine.systems.opportunity import get_opportunity_attackers
from engine.systems.turn_manager import TurnManager

ACTION_MOVE = 0
ACTION_BASIC = 1
ACTION_ABILITY_1 = 2
ACTION_ABILITY_2 = 3
ACTION_ABILITY_3 = 4
ACTION_ABILITY_4 = 5
ACTION_ABILITY_5 = 6
ACTION_THROW = 7
ACTION_END_TURN = 8
ACTION_PASS = 9

_DEFAULT_ABILITIES: dict[CharacterClass, list[str]] = {
    CharacterClass.WARRIOR: [
        "impacto_brutal",
        "muralha_de_ferro",
        "investida",
        "corte_profundo",
        "sentenca_do_carrasco",
    ],
    CharacterClass.MAGE: [
        "estilhaco_arcano",
        "nova_flamejante",
        "toque_do_inverno",
        "barreira_arcana",
        "sifao_vital",
    ],
    CharacterClass.CLERIC: [
        "toque_da_aurora",
        "egide_sagrada",
        "chama_sagrada",
        "consagracao",
        "julgamento_divino",
    ],
    CharacterClass.ARCHER: [
        "tiro_perfurante",
        "chuva_de_flechas",
        "ponta_envenenada",
        "flecha_glacial",
        "tiro_certeiro",
    ],
    CharacterClass.ASSASSIN: [
        "lamina_oculta",
        "passo_sombrio",
        "danca_das_laminas",
        "tiro_certeiro",
        "corte_profundo",
    ],
}


def _tile_to_pos(tile_idx: int) -> Position:
    return Position(tile_idx % 10, tile_idx // 10)


def _pos_to_tile(pos: Position) -> int:
    return pos.y * 10 + pos.x


def _get_scaling_attr(ability: Ability, char_class: CharacterClass) -> str:
    attr = (
        ability.damage_attr
        or ability.heal_attr
        or ability.self_heal_attr
        or ability.shield_absorb_attr
    )
    if not attr:
        return "str"
    if attr == "int_" and char_class == CharacterClass.CLERIC:
        return "wis"
    return attr


class BattleState:
    def __init__(
        self,
        characters: dict[str, Character],
        positions: dict[str, Position],
        teams: dict[str, Team],
        equipped: dict[str, list[Ability]],
        basic_attacks: dict[str, Ability],
        grid: Grid,
        map_objects: dict[str, MapObject],
        turn_manager: TurnManager,
        effect_manager: EffectManager,
        rng: _random.Random,
        team_a_entities: list[str],
        team_b_entities: list[str],
    ) -> None:
        self._characters = characters
        self._positions = positions
        self._teams = teams
        self._equipped = equipped
        self._basic_attacks = basic_attacks
        self.grid = grid
        self._map_objects = map_objects
        self._turn_manager = turn_manager
        self._effect_manager = effect_manager
        self._rng = rng
        self._team_a = list(team_a_entities)
        self._team_b = list(team_b_entities)
        self._winner: str | None = None
        self._events: list[dict] = []
        self._delayed_abilities: list[dict] = []
        self._traps: dict[Position, dict] = {}

    @classmethod
    def from_config(
        cls,
        team_a_config: list[tuple[CharacterClass, tuple[int, ...]]],
        team_b_config: list[tuple[CharacterClass, tuple[int, ...]]],
        biome: Biome | None = None,
        rng: _random.Random | None = None,
    ) -> BattleState:
        if rng is None:
            rng = _random.Random()
        if biome is None:
            biome = rng.choice(list(Biome))

        grid, map_objects_list = generate_map(biome, rng)
        map_objects = {o.entity_id: o for o in map_objects_list}

        characters: dict[str, Character] = {}
        positions: dict[str, Position] = {}
        teams: dict[str, Team] = {}
        equipped: dict[str, list[Ability]] = {}
        basic_atks: dict[str, Ability] = {}
        team_a_ids: list[str] = []
        team_b_ids: list[str] = []

        spawn_a = sorted(grid.get_spawn_positions(Team.A), key=lambda p: (p.x, p.y))
        spawn_b = sorted(grid.get_spawn_positions(Team.B), key=lambda p: (p.x, p.y))
        rng.shuffle(spawn_a)
        rng.shuffle(spawn_b)

        for i, (cls_type, build) in enumerate(team_a_config):
            eid = f"team_a_{cls_type.value}_{i}"
            base = BASE_ATTRIBUTES[cls_type]
            attrs = Attributes.from_base_and_build(base, build)
            char = Character(eid, cls_type, attrs)
            pos = spawn_a[i]
            characters[eid] = char
            positions[eid] = pos
            teams[eid] = Team.A
            basic_atks[eid] = BASIC_ATTACKS[cls_type]
            equipped[eid] = [ABILITIES[aid] for aid in _DEFAULT_ABILITIES[cls_type]]
            team_a_ids.append(eid)
            grid.place_occupant(pos, Occupant(eid, OccupantType.CHARACTER, Team.A))

        for i, (cls_type, build) in enumerate(team_b_config):
            eid = f"team_b_{cls_type.value}_{i}"
            base = BASE_ATTRIBUTES[cls_type]
            attrs = Attributes.from_base_and_build(base, build)
            char = Character(eid, cls_type, attrs)
            pos = spawn_b[i]
            characters[eid] = char
            positions[eid] = pos
            teams[eid] = Team.B
            basic_atks[eid] = BASIC_ATTACKS[cls_type]
            equipped[eid] = [ABILITIES[aid] for aid in _DEFAULT_ABILITIES[cls_type]]
            team_b_ids.append(eid)
            grid.place_occupant(pos, Occupant(eid, OccupantType.CHARACTER, Team.B))

        participants = [
            (
                eid,
                characters[eid].attributes.modifier("dex"),
                characters[eid].attributes.dex,
            )
            for eid in list(team_a_ids) + list(team_b_ids)
        ]
        order = determine_turn_order(participants, rng)
        tm = TurnManager(order)
        em = EffectManager()

        return cls(
            characters,
            positions,
            teams,
            equipped,
            basic_atks,
            grid,
            map_objects,
            tm,
            em,
            rng,
            team_a_ids,
            team_b_ids,
        )

    @property
    def current_agent(self) -> str:
        return self._turn_manager.current_entity

    @property
    def current_round(self) -> int:
        return self._turn_manager.current_round

    @property
    def team_a_entities(self) -> list[str]:
        return list(self._team_a)

    @property
    def team_b_entities(self) -> list[str]:
        return list(self._team_b)

    @property
    def all_entities(self) -> list[str]:
        return list(self._team_a) + list(self._team_b)

    @property
    def turn_order(self) -> list[str]:
        return self._turn_manager.turn_order

    @property
    def is_over(self) -> bool:
        return self._winner is not None

    @property
    def winner(self) -> str | None:
        return self._winner

    def get_character(self, entity_id: str) -> Character:
        return self._characters[entity_id]

    def get_position(self, entity_id: str) -> Position:
        return self._positions[entity_id]

    def get_team(self, entity_id: str) -> Team:
        return self._teams[entity_id]

    def get_pa(self, entity_id: str) -> int:
        return self._turn_manager.get_pa(entity_id)

    def get_equipped_abilities(self, entity_id: str) -> list[Ability]:
        return list(self._equipped.get(entity_id, []))

    def get_basic_attack(self, entity_id: str) -> Ability:
        return self._basic_attacks[entity_id]

    def get_effect_manager(self) -> EffectManager:
        return self._effect_manager

    def get_reachable_tiles(self, entity_id: str) -> set[Position]:
        pa = self._turn_manager.get_pa(entity_id)
        max_tiles = tiles_for_pa(pa)
        pos = self._positions[entity_id]
        team = self._teams[entity_id]
        return get_reachable_tiles(self.grid, pos, max_tiles, team)

    def get_blocking_positions(self) -> set[Position]:
        result: set[Position] = set()
        for obj in self._map_objects.values():
            if not obj.is_destroyed and obj.blocks_los:
                result.add(obj.position)
        return result

    def process_turn_start(self) -> list[dict]:
        events: list[dict] = []
        agent = self.current_agent
        char = self._characters.get(agent)

        if char is None or char.state == CharacterState.DEAD:
            self._advance_to_next_alive()
            return events

        if char.state == CharacterState.KNOCKED_OUT:
            bleed = char.process_bleed()
            if bleed > 0:
                events.append({"type": "bleed", "entity": agent, "damage": bleed})
            if char.state == CharacterState.DEAD:
                events.extend(self._handle_death(agent))
            self._skip_turn()
            return events

        frozen = self._effect_manager.get_effect(agent, "freeze")
        if frozen:
            self._skip_turn()
            events.append({"type": "frozen_skip", "entity": agent})
            return events

        expired = self._effect_manager.process_turn_start(agent)
        for e in expired:
            events.append({"type": "effect_expired", "entity": agent, "tag": e.tag})

        pending = [d for d in self._delayed_abilities if d["caster_id"] == agent]
        for d in pending:
            self._delayed_abilities.remove(d)
            self._resolve_aoe_damage(d["caster_id"], d["target_pos"], d["ability"])
            events.append(
                {
                    "type": "delayed_resolve",
                    "ability": d["ability"].id,
                    "target": d["target_pos"],
                }
            )

        to_remove = []
        for pos, trap in self._traps.items():
            trap["turns_remaining"] -= 1
            if trap["turns_remaining"] <= 0:
                to_remove.append(pos)
        for pos in to_remove:
            del self._traps[pos]

        return events

    def process_turn_end(self) -> list[dict]:
        events: list[dict] = []
        agent = self.current_agent
        char = self._characters.get(agent)
        if char is None or char.state != CharacterState.ACTIVE:
            return events

        ticked = self._effect_manager.process_turn_end(agent)
        for effect in ticked:
            if effect.effect_type == EffectType.DOT:
                state = char.apply_damage(int(effect.value))
                events.append(
                    {
                        "type": "dot_tick",
                        "entity": agent,
                        "tag": effect.tag,
                        "damage": int(effect.value),
                    }
                )
                if state == CharacterState.DEAD:
                    events.extend(self._handle_death(agent))
                elif state == CharacterState.KNOCKED_OUT:
                    events.append({"type": "knocked_out", "entity": agent})
            elif effect.effect_type == EffectType.HOT:
                char.apply_healing(int(effect.value))
                events.append(
                    {
                        "type": "hot_tick",
                        "entity": agent,
                        "tag": effect.tag,
                        "heal": int(effect.value),
                    }
                )

        return events

    def execute_action(self, action_type: int, target: int) -> list[dict]:
        self._events = []

        if self.is_over:
            return self._events

        agent = self.current_agent
        char = self._characters[agent]
        if char.state != CharacterState.ACTIVE:
            return self._events

        if action_type == ACTION_MOVE:
            self._execute_move(agent, _tile_to_pos(target))
        elif action_type == ACTION_BASIC:
            self._execute_basic_attack(agent, _tile_to_pos(target))
        elif ACTION_ABILITY_1 <= action_type <= ACTION_ABILITY_5:
            slot = action_type - ACTION_ABILITY_1
            self._execute_ability(agent, slot, _tile_to_pos(target))
        elif action_type == ACTION_THROW:
            self._execute_throw(agent, _tile_to_pos(target))
        elif action_type == ACTION_END_TURN:
            self._execute_end_turn(agent)
        elif action_type == ACTION_PASS:
            self._execute_end_turn(agent)

        self._winner = self.check_victory()
        return self._events

    def check_victory(self) -> str | None:
        a_alive = any(
            self._characters[eid].state != CharacterState.DEAD
            for eid in self._team_a
            if eid in self._characters
        )
        b_alive = any(
            self._characters[eid].state != CharacterState.DEAD
            for eid in self._team_b
            if eid in self._characters
        )
        if not b_alive:
            return "team_a"
        if not a_alive:
            return "team_b"
        return None

    def handle_death(self, entity_id: str) -> list[dict]:
        return self._handle_death(entity_id)

    def _handle_death(self, entity_id: str) -> list[dict]:
        events: list[dict] = []
        remaining_in_order = self._turn_manager.turn_order
        if entity_id in remaining_in_order and len(remaining_in_order) > 1:
            self._turn_manager.remove_entity(entity_id)
        elif entity_id in remaining_in_order and len(remaining_in_order) == 1:
            pass
        self.grid.remove_occupant(self._positions[entity_id], entity_id)
        self._effect_manager.remove_entity(entity_id)
        events.append({"type": "death", "entity": entity_id})
        return events

    def _skip_turn(self) -> None:
        self.process_turn_end()
        self._turn_manager.end_turn()

    def _advance_to_next_alive(self) -> None:
        for _ in range(len(self._turn_manager.turn_order) + 1):
            agent = self.current_agent
            char = self._characters.get(agent)
            if char and char.state == CharacterState.ACTIVE:
                return
            if char and char.state == CharacterState.KNOCKED_OUT:
                return
            self._turn_manager.end_turn()

    def _execute_move(self, agent: str, target: Position) -> None:
        pos = self._positions[agent]
        team = self._teams[agent]
        pa = self._turn_manager.get_pa(agent)
        max_tiles = tiles_for_pa(pa)
        reachable = get_reachable_tiles(self.grid, pos, max_tiles, team)

        if target not in reachable:
            return

        opp_attackers = get_opportunity_attackers(self.grid, pos, target, team)
        for opp_eid, opp_pos in opp_attackers:
            opp_char = self._characters.get(opp_eid)
            if opp_char and opp_char.state == CharacterState.ACTIVE:
                self._resolve_basic_attack(opp_eid, agent)
                if self._characters[agent].state != CharacterState.ACTIVE:
                    return

        path = execute_move(self.grid, agent, pos, target, max_tiles)
        self._positions[agent] = target
        tiles_moved = len(path) - 1
        pa_cost = max(1, (tiles_moved + 1) // 2)
        self._turn_manager.spend_pa(
            agent, min(pa_cost, self._turn_manager.get_pa(agent))
        )
        self._events.append(
            {"type": "move", "entity": agent, "from": pos, "to": target}
        )

        if target in self._traps:
            trap = self._traps.pop(target)
            trap_ability = trap["ability"]
            caster_id = trap["caster_id"]
            caster = self._characters.get(caster_id)
            if caster:
                attr = _get_scaling_attr(trap_ability, caster.character_class)
                modifier = caster.attributes.modifier(attr)
                trap_damage = calculate_raw_damage(
                    trap_ability.damage_base, modifier, trap_ability.damage_scaling
                )
                self._characters[agent].apply_damage(trap_damage)
                self._events.append(
                    {"type": "trap_triggered", "target": agent, "damage": trap_damage}
                )
                for bd in trap_ability.effects:
                    effect = Effect(
                        tag=bd.tag,
                        effect_type=bd.effect_type,
                        source_entity_id=caster_id,
                        duration=bd.duration,
                        value=bd.value,
                    )
                    self._effect_manager.apply_effect(agent, effect)
                if self._characters[agent].state == CharacterState.DEAD:
                    self._events.extend(self._handle_death(agent))
                elif self._characters[agent].state == CharacterState.KNOCKED_OUT:
                    self._events.append({"type": "knocked_out", "entity": agent})

    def _execute_basic_attack(self, agent: str, target_pos: Position) -> None:
        ability = self._basic_attacks[agent]
        if self._turn_manager.get_pa(agent) < ability.pa_cost:
            return

        target_id = self._find_character_at(target_pos)
        if target_id is None:
            return

        self._turn_manager.spend_pa(agent, ability.pa_cost)
        result = self._resolve_damage(agent, target_id, ability)
        self._events.append(
            {
                "type": "basic_attack",
                "attacker": agent,
                "target": target_id,
                "damage": result.get("damage", 0),
                "crit": result.get("crit", False),
                "evaded": result.get("evaded", False),
            }
        )

    def _execute_ability(self, agent: str, slot: int, target_pos: Position) -> None:
        abilities = self._equipped.get(agent, [])
        if slot >= len(abilities):
            return
        ability = abilities[slot]
        pa = self._turn_manager.get_pa(agent)
        if pa < ability.pa_cost:
            return
        if not self._turn_manager.is_ability_ready(agent, slot):
            return

        self._turn_manager.spend_pa(agent, ability.pa_cost)
        if ability.cooldown > 0:
            self._turn_manager.use_ability(agent, slot, ability.cooldown)

        char = self._characters[agent]

        if ability.damage_base > 0 and ability.delayed:
            self._delayed_abilities.append(
                {
                    "caster_id": agent,
                    "ability": ability,
                    "target_pos": target_pos,
                }
            )
            self._events.append(
                {"type": "delayed_mark", "ability": ability.id, "target": target_pos}
            )
        elif ability.id == "armadilha_espinhosa":
            self._traps[target_pos] = {
                "caster_id": agent,
                "ability": ability,
                "turns_remaining": 5,
            }
            self._events.append({"type": "trap_placed", "position": target_pos})
        elif ability.damage_base > 0:
            if ability.chain_targets > 0:
                self._resolve_chain_damage(agent, target_pos, ability)
            elif ability.target == AbilityTarget.ADJACENT or (
                ability.aoe_radius > 0 and ability.target == AbilityTarget.AOE
            ):
                self._resolve_aoe_damage(agent, target_pos, ability)
            else:
                target_id = self._find_character_at(target_pos)
                if target_id and not self._is_untargetable(target_id):
                    result = self._resolve_damage(agent, target_id, ability)
                    self._events.append(
                        {
                            "type": "ability",
                            "ability": ability.id,
                            "attacker": agent,
                            "target": target_id,
                            "damage": result.get("damage", 0),
                        }
                    )
                    if ability.lifesteal_pct > 0 and result.get("damage", 0) > 0:
                        heal_amount = int(result["damage"] * ability.lifesteal_pct)
                        if heal_amount > 0:
                            char.apply_healing(heal_amount)
                            self._events.append(
                                {
                                    "type": "lifesteal",
                                    "entity": agent,
                                    "heal": heal_amount,
                                }
                            )

        if ability.heal_base > 0:
            target_id = self._find_character_at(target_pos)
            if target_id is None:
                target_id = agent
            self._resolve_heal(agent, target_id, ability)

        if ability.self_heal_base > 0:
            attr = ability.self_heal_attr if ability.self_heal_attr else "wis"
            if attr == "int_" and char.character_class == CharacterClass.CLERIC:
                attr = "wis"
            modifier = char.attributes.modifier(attr)
            heal_raw = calculate_raw_damage(
                ability.self_heal_base, modifier, ability.self_heal_scaling
            )
            char.apply_healing(heal_raw)
            self._events.append(
                {"type": "self_heal", "entity": agent, "heal": heal_raw}
            )

        for buff_def in ability.effects:
            if buff_def.target == "enemy" and ability.target in (
                AbilityTarget.AOE,
                AbilityTarget.ADJACENT,
            ):
                center = (
                    self._positions[agent]
                    if ability.target == AbilityTarget.ADJACENT
                    else target_pos
                )
                targets_in_area = self._get_characters_in_radius(
                    center, ability.aoe_radius, agent
                )
                caster_team = self._teams[agent]
                for tid in targets_in_area:
                    if self._teams[tid] != caster_team and not self._is_untargetable(
                        tid
                    ):
                        self._apply_buff_effect_to(agent, tid, ability, buff_def)
            else:
                self._apply_buff_effect(agent, target_pos, ability, buff_def)

        if ability.movement_type and ability.movement_distance > 0:
            self._events.append(
                {
                    "type": "ability_movement",
                    "entity": agent,
                    "movement": ability.movement_type,
                }
            )

        if ability.remove_all_negative:
            target_id = self._find_character_at(target_pos)
            if target_id:
                removed = self._effect_manager.remove_all_negative(target_id)
                self._events.append(
                    {"type": "purge", "target": target_id, "removed": len(removed)}
                )

    def _execute_throw(self, agent: str, target_pos: Position) -> None:
        if self._turn_manager.get_pa(agent) < 2:
            return
        self._turn_manager.spend_pa(agent, 2)
        self._events.append({"type": "throw", "entity": agent, "target": target_pos})

    def _execute_end_turn(self, agent: str) -> None:
        events = self.process_turn_end()
        self._events.extend(events)
        next_agent = self._turn_manager.end_turn()
        self._events.append({"type": "end_turn", "entity": agent, "next": next_agent})

    def _resolve_damage(
        self,
        attacker_id: str,
        target_id: str,
        ability: Ability,
        no_evasion: bool = False,
    ) -> dict:
        attacker = self._characters[attacker_id]
        target = self._characters[target_id]

        attr_name = _get_scaling_attr(ability, attacker.character_class)
        attack_mod = attacker.attributes.modifier(attr_name)

        extra_crit = ability.crit_bonus
        damage_multiplier = 1.0

        next_atk = self._effect_manager.get_effect(attacker_id, "next_attack_bonus")
        if next_atk:
            damage_multiplier *= 1.0 + next_atk.value
            self._effect_manager.remove_effects_by_tag(attacker_id, "next_attack_bonus")
            self._events.append(
                {
                    "type": "next_attack_consumed",
                    "entity": attacker_id,
                    "bonus": next_atk.value,
                }
            )

        if ability.elemental_tag:
            combo = check_elemental_combo(
                self._effect_manager, target_id, ability.elemental_tag
            )
            if combo:
                damage_multiplier *= combo.damage_modifier
                self._events.append(
                    {
                        "type": "combo",
                        "tag": ability.elemental_tag,
                        "modifier": combo.damage_modifier,
                    }
                )

        if ability.execute_threshold > 0 and target.current_hp > 0:
            if target.current_hp / target.max_hp <= ability.execute_threshold:
                damage_multiplier *= 1 + ability.execute_bonus

        if ability.debuff_bonus > 0 and has_negative_status(
            self._effect_manager, target_id
        ):
            damage_multiplier *= 1 + ability.debuff_bonus

        reduction = sum(
            e.value
            for e in self._effect_manager.get_effects_by_type(
                target_id, EffectType.BUFF
            )
            if "damage_reduction" in e.tag
        )

        if ability.damage_type == "physical":
            attacker_dex = attacker.attributes.modifier("dex")
            defender_dex = (
                0
                if target.is_knocked_out or no_evasion
                else target.attributes.modifier("dex")
            )
            defender_con = target.attributes.modifier("con")

            result = resolve_physical_attack(
                base_damage=ability.damage_base,
                scaling=ability.damage_scaling,
                attack_modifier=attack_mod,
                attacker_dex_modifier=attacker_dex,
                defender_dex_modifier=defender_dex,
                defender_con_modifier=defender_con,
                reduction_percent=reduction,
                rng=self._rng,
            )
            final_damage = result.damage
            if damage_multiplier != 1.0 and not result.is_evaded:
                final_damage = max(
                    1, int(result.raw_damage * damage_multiplier) - defender_con
                )
                if reduction > 0:
                    final_damage = max(1, int(final_damage * (1 - reduction)))

            if result.is_evaded:
                final_damage = 0

            if final_damage > 0:
                final_damage = self._apply_redirect(target_id, final_damage)
                state = target.apply_damage(final_damage)
                if state == CharacterState.DEAD:
                    self._events.extend(self._handle_death(target_id))
                elif state == CharacterState.KNOCKED_OUT:
                    self._events.append({"type": "knocked_out", "entity": target_id})
                self._apply_reflect(attacker_id, target_id, final_damage)

            if final_damage > 0:
                self._apply_poison_on_hit(attacker_id, target_id)

            return {
                "damage": final_damage,
                "crit": result.is_critical,
                "evaded": result.is_evaded,
            }

        else:
            defender_wis = target.attributes.modifier("wis")
            result = resolve_magical_attack(
                base_damage=ability.damage_base,
                scaling=ability.damage_scaling,
                attack_modifier=attack_mod,
                defender_wis_modifier=defender_wis,
                reduction_percent=reduction,
            )
            final_damage = result.damage
            if damage_multiplier != 1.0:
                raw_modified = int(result.raw_damage * damage_multiplier)
                final_damage = max(1, raw_modified - defender_wis)
                if reduction > 0:
                    final_damage = max(1, int(final_damage * (1 - reduction)))

            final_damage = self._apply_redirect(target_id, final_damage)
            state = target.apply_damage(final_damage)
            if state == CharacterState.DEAD:
                self._events.extend(self._handle_death(target_id))
            elif state == CharacterState.KNOCKED_OUT:
                self._events.append({"type": "knocked_out", "entity": target_id})
            self._apply_reflect(attacker_id, target_id, final_damage)

            if final_damage > 0:
                self._apply_poison_on_hit(attacker_id, target_id)

            return {"damage": final_damage, "crit": False, "evaded": False}

    def _resolve_basic_attack(self, attacker_id: str, target_id: str) -> None:
        ability = self._basic_attacks[attacker_id]
        result = self._resolve_damage(attacker_id, target_id, ability)
        self._events.append(
            {
                "type": "opportunity_attack",
                "attacker": attacker_id,
                "target": target_id,
                "damage": result.get("damage", 0),
            }
        )

    def _resolve_heal(self, healer_id: str, target_id: str, ability: Ability) -> None:
        healer = self._characters[healer_id]
        target = self._characters[target_id]
        attr = ability.heal_attr or "wis"
        if attr == "int_" and healer.character_class == CharacterClass.CLERIC:
            attr = "wis"
        modifier = healer.attributes.modifier(attr)
        result = resolve_healing(
            base_heal=ability.heal_base,
            scaling=ability.heal_scaling,
            healer_wis_modifier=modifier,
            target_current_hp=target.current_hp,
            target_max_hp=target.max_hp,
        )
        target.apply_healing(result.amount)
        self._events.append(
            {
                "type": "heal",
                "healer": healer_id,
                "target": target_id,
                "amount": result.amount,
            }
        )

    def _apply_buff_effect(
        self, caster_id: str, target_pos: Position, ability: Ability, buff_def: BuffDef
    ) -> None:
        char = self._characters[caster_id]
        value = buff_def.value

        if buff_def.scaling_attr and buff_def.scaling_factor > 0:
            attr = buff_def.scaling_attr
            if attr == "int_" and char.character_class == CharacterClass.CLERIC:
                attr = "wis"
            modifier = char.attributes.modifier(attr)
            value = float(
                calculate_raw_damage(
                    int(buff_def.value), modifier, buff_def.scaling_factor
                )
            )
        elif (
            ability.shield_absorb_base > 0
            and ability.shield_absorb_scaling > 0
            and buff_def.effect_type == EffectType.SHIELD
        ):
            attr = _get_scaling_attr(ability, char.character_class)
            modifier = char.attributes.modifier(attr)
            value = float(
                calculate_raw_damage(
                    ability.shield_absorb_base, modifier, ability.shield_absorb_scaling
                )
            )

        if buff_def.target == "self":
            target_id = caster_id
        elif buff_def.target == "enemy":
            target_id = self._find_character_at(target_pos)
            if target_id is None:
                return
        elif buff_def.target == "ally":
            target_id = self._find_character_at(target_pos)
            if target_id is None:
                target_id = caster_id
        else:
            target_id = caster_id

        effect = Effect(
            tag=buff_def.tag,
            effect_type=buff_def.effect_type,
            source_entity_id=caster_id,
            duration=buff_def.duration,
            value=value,
        )
        self._effect_manager.apply_effect(target_id, effect)
        self._events.append(
            {"type": "effect_applied", "target": target_id, "tag": buff_def.tag}
        )

    def _apply_poison_on_hit(self, attacker_id: str, target_id: str) -> None:
        poison_buff = self._effect_manager.get_effect(attacker_id, "poison_attacks")
        if not poison_buff:
            return
        poison_dot = Effect(
            tag="poison",
            effect_type=EffectType.DOT,
            source_entity_id=attacker_id,
            duration=2,
            value=poison_buff.value,
        )
        self._effect_manager.apply_effect(target_id, poison_dot)
        self._events.append(
            {"type": "poison_applied", "attacker": attacker_id, "target": target_id}
        )
        poison_buff.duration -= 1
        if poison_buff.duration <= 0:
            self._effect_manager.remove_effects_by_tag(attacker_id, "poison_attacks")

    def _apply_reflect(self, attacker_id: str, target_id: str, damage: int) -> None:
        if damage <= 0:
            return
        reflect_effect = self._effect_manager.get_effect(target_id, "reflect")
        if not reflect_effect:
            return
        reflected = max(1, int(damage * reflect_effect.value))
        attacker = self._characters[attacker_id]
        if attacker.state == CharacterState.DEAD:
            return
        state = attacker.apply_damage(reflected)
        self._events.append(
            {
                "type": "reflect",
                "source": target_id,
                "target": attacker_id,
                "damage": reflected,
            }
        )
        if state == CharacterState.DEAD:
            self._events.extend(self._handle_death(attacker_id))
        elif state == CharacterState.KNOCKED_OUT:
            self._events.append({"type": "knocked_out", "entity": attacker_id})

    def _apply_redirect(self, target_id: str, damage: int) -> int:
        if damage <= 0:
            return damage
        redirect_effect = self._effect_manager.get_effect(target_id, "redirect")
        if not redirect_effect:
            return damage
        redirector_id = redirect_effect.source_entity_id
        redirector = self._characters.get(redirector_id)
        if not redirector or redirector.state != CharacterState.ACTIVE:
            return damage
        redirector_pos = self._positions.get(redirector_id)
        target_pos = self._positions.get(target_id)
        if not redirector_pos or not target_pos:
            return damage
        dist = max(
            abs(redirector_pos.x - target_pos.x), abs(redirector_pos.y - target_pos.y)
        )
        if dist > 2:
            return damage
        if redirector_id == target_id:
            return damage
        redirected = int(damage * redirect_effect.value)
        remaining = damage - redirected
        state = redirector.apply_damage(redirected)
        self._events.append(
            {
                "type": "redirect",
                "from": target_id,
                "to": redirector_id,
                "damage": redirected,
            }
        )
        if state == CharacterState.DEAD:
            self._events.extend(self._handle_death(redirector_id))
        elif state == CharacterState.KNOCKED_OUT:
            self._events.append({"type": "knocked_out", "entity": redirector_id})
        return max(1, remaining)

    def _is_untargetable(self, entity_id: str) -> bool:
        return self._effect_manager.has_effect(entity_id, "untargetable")

    def _get_characters_in_radius(
        self, center: Position, radius: int, exclude_id: str = ""
    ) -> list[str]:
        result = []
        for eid, pos in self._positions.items():
            if eid == exclude_id:
                continue
            char = self._characters[eid]
            if char.state == CharacterState.DEAD:
                continue
            dist = max(abs(pos.x - center.x), abs(pos.y - center.y))
            if dist <= radius:
                result.append(eid)
        return result

    def _resolve_aoe_damage(
        self, attacker_id: str, target_pos: Position, ability: Ability
    ) -> None:
        center = (
            self._positions[attacker_id]
            if ability.target == AbilityTarget.ADJACENT
            else target_pos
        )
        radius = ability.aoe_radius if ability.aoe_radius > 0 else 1
        targets = self._get_characters_in_radius(center, radius, attacker_id)
        caster_team = self._teams[attacker_id]

        for tid in targets:
            if self._is_untargetable(tid):
                continue
            if not ability.friendly_fire and self._teams[tid] == caster_team:
                continue
            result = self._resolve_damage(attacker_id, tid, ability, no_evasion=True)
            self._events.append(
                {
                    "type": "aoe_hit",
                    "ability": ability.id,
                    "attacker": attacker_id,
                    "target": tid,
                    "damage": result.get("damage", 0),
                }
            )

    def _resolve_chain_damage(
        self, attacker_id: str, target_pos: Position, ability: Ability
    ) -> None:
        primary_id = self._find_character_at(target_pos)
        if not primary_id or self._is_untargetable(primary_id):
            return

        result = self._resolve_damage(attacker_id, primary_id, ability)
        primary_damage = result.get("damage", 0)
        self._events.append(
            {
                "type": "chain_primary",
                "ability": ability.id,
                "attacker": attacker_id,
                "target": primary_id,
                "damage": primary_damage,
            }
        )

        if primary_damage <= 0 or ability.chain_targets <= 0:
            return

        primary_pos = self._positions[primary_id]
        caster_team = self._teams[attacker_id]
        candidates = []
        for eid, pos in self._positions.items():
            if eid == primary_id or eid == attacker_id:
                continue
            char = self._characters[eid]
            if char.state == CharacterState.DEAD:
                continue
            if self._teams[eid] == caster_team:
                continue
            if self._is_untargetable(eid):
                continue
            dist = max(abs(pos.x - primary_pos.x), abs(pos.y - primary_pos.y))
            if dist <= 2:
                candidates.append(eid)

        chain_damage = max(1, int(primary_damage * ability.chain_damage_pct))
        for i, tid in enumerate(candidates[: ability.chain_targets]):
            self._characters[tid].apply_damage(chain_damage)
            self._events.append(
                {
                    "type": "chain_secondary",
                    "ability": ability.id,
                    "target": tid,
                    "damage": chain_damage,
                }
            )
            if self._characters[tid].state == CharacterState.DEAD:
                self._events.extend(self._handle_death(tid))
            elif self._characters[tid].state == CharacterState.KNOCKED_OUT:
                self._events.append({"type": "knocked_out", "entity": tid})

    def _apply_buff_effect_to(
        self, caster_id: str, target_id: str, ability: Ability, buff_def: BuffDef
    ) -> None:
        value = buff_def.value
        effect = Effect(
            tag=buff_def.tag,
            effect_type=buff_def.effect_type,
            source_entity_id=caster_id,
            duration=buff_def.duration,
            value=value,
        )
        self._effect_manager.apply_effect(target_id, effect)
        self._events.append(
            {"type": "effect_applied", "target": target_id, "tag": buff_def.tag}
        )

    def _find_character_at(self, pos: Position) -> str | None:
        for eid, p in self._positions.items():
            if p == pos and self._characters[eid].state != CharacterState.DEAD:
                return eid
        return None
