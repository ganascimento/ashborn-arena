import random

from engine.models.character import CharacterClass
from engine.models.grid import Occupant, OccupantType
from engine.models.map_object import MapObject, ObjectType
from engine.models.position import Position
from engine.systems.battle import (
    ACTION_ABILITY_1,
    ACTION_ABILITY_3,
    ACTION_BASIC,
    ACTION_END_TURN,
    BattleState,
)


def _place(bs, entity_id, new_pos):
    old_pos = bs.get_position(entity_id)
    bs.grid.remove_occupant(old_pos, entity_id)
    bs._positions[entity_id] = new_pos
    bs.grid.place_occupant(
        new_pos, Occupant(entity_id, OccupantType.CHARACTER, bs.get_team(entity_id))
    )


def _make_battle(team_a_classes, team_b_classes, seed=42):
    build = (2, 2, 2, 2, 2)
    ta = [(cls, build) for cls in team_a_classes]
    tb = [(cls, build) for cls in team_b_classes]
    return BattleState.from_config(ta, tb, rng=random.Random(seed))


def _get_entity_by_class(bs, cls, team="a"):
    entities = bs.team_a_entities if team == "a" else bs.team_b_entities
    for eid in entities:
        if bs.get_character(eid).character_class == cls:
            return eid
    return None


def _clear_map_objects(bs):
    for obj in list(bs._map_objects.values()):
        bs.grid.remove_occupant(obj.position, obj.entity_id)
    bs._map_objects.clear()


def _place_object(bs, obj_type, entity_id, pos):
    obj = MapObject.from_type(obj_type, entity_id, pos)
    bs._map_objects[entity_id] = obj
    bs.grid.place_occupant(
        pos,
        Occupant(entity_id, OccupantType.OBJECT, blocks_movement=obj.blocks_movement),
    )
    return obj


def _advance_to(bs, agent_id):
    while bs.current_agent != agent_id:
        bs.process_turn_start()
        bs.execute_action(ACTION_END_TURN, 0)
    bs.process_turn_start()


class TestRangedAbilityHitsBlockingObject:
    def test_single_target_ranged_hits_tree(self):
        bs = _make_battle([CharacterClass.MAGE], [CharacterClass.WARRIOR], seed=10)
        mage_id = _get_entity_by_class(bs, CharacterClass.MAGE, "a")
        enemy_id = bs.team_b_entities[0]
        _clear_map_objects(bs)

        _place(bs, mage_id, Position(0, 3))
        _place(bs, enemy_id, Position(5, 3))
        tree = _place_object(bs, ObjectType.TREE, "tree_1", Position(3, 3))

        _advance_to(bs, mage_id)
        enemy_hp_before = bs.get_character(enemy_id).current_hp
        tree_hp_before = tree.current_hp

        target_idx = 3 * 10 + 5  # Position(5, 3)
        # estilhaco_arcano = slot 0 = ABILITY_1
        bs.execute_action(ACTION_ABILITY_1, target_idx)

        assert tree.current_hp < tree_hp_before, "Tree should have taken damage"
        assert bs.get_character(enemy_id).current_hp == enemy_hp_before, (
            "Enemy should NOT take damage when projectile hits tree"
        )

    def test_single_target_ranged_no_blocker_hits_target(self):
        bs = _make_battle([CharacterClass.MAGE], [CharacterClass.WARRIOR], seed=10)
        mage_id = _get_entity_by_class(bs, CharacterClass.MAGE, "a")
        enemy_id = bs.team_b_entities[0]
        _clear_map_objects(bs)

        _place(bs, mage_id, Position(0, 3))
        _place(bs, enemy_id, Position(3, 3))

        _advance_to(bs, mage_id)
        enemy_hp_before = bs.get_character(enemy_id).current_hp

        target_idx = 3 * 10 + 3  # Position(3, 3)
        bs.execute_action(ACTION_ABILITY_1, target_idx)

        assert bs.get_character(enemy_id).current_hp < enemy_hp_before, (
            "Enemy should take damage when no blocker in path"
        )

    def test_object_hit_event_emitted(self):
        bs = _make_battle([CharacterClass.MAGE], [CharacterClass.WARRIOR], seed=10)
        mage_id = _get_entity_by_class(bs, CharacterClass.MAGE, "a")
        enemy_id = bs.team_b_entities[0]
        _clear_map_objects(bs)

        _place(bs, mage_id, Position(0, 3))
        _place(bs, enemy_id, Position(5, 3))
        _place_object(bs, ObjectType.CRATE, "crate_1", Position(3, 3))

        _advance_to(bs, mage_id)
        bs._events.clear()
        target_idx = 3 * 10 + 5
        bs.execute_action(ACTION_ABILITY_1, target_idx)

        object_hit_events = [e for e in bs._events if e["type"] == "object_hit"]
        assert len(object_hit_events) == 1
        assert object_hit_events[0]["object"] == "crate_1"
        assert object_hit_events[0]["damage"] > 0

    def test_destroyed_object_removed_from_grid(self):
        bs = _make_battle([CharacterClass.MAGE], [CharacterClass.WARRIOR], seed=10)
        mage_id = _get_entity_by_class(bs, CharacterClass.MAGE, "a")
        enemy_id = bs.team_b_entities[0]
        _clear_map_objects(bs)

        _place(bs, mage_id, Position(0, 3))
        _place(bs, enemy_id, Position(5, 3))
        # Bush has HP=5, very easy to destroy
        bush = _place_object(bs, ObjectType.BUSH, "bush_1", Position(3, 3))

        _advance_to(bs, mage_id)
        target_idx = 3 * 10 + 5
        bs.execute_action(ACTION_ABILITY_1, target_idx)

        if bush.is_destroyed:
            occupants = bs.grid.get_occupants(Position(3, 3))
            obj_occupants = [o for o in occupants if o.entity_id == "bush_1"]
            assert len(obj_occupants) == 0, (
                "Destroyed object should be removed from grid"
            )

    def test_pa_and_cooldown_spent_when_hitting_object(self):
        bs = _make_battle([CharacterClass.MAGE], [CharacterClass.WARRIOR], seed=10)
        mage_id = _get_entity_by_class(bs, CharacterClass.MAGE, "a")
        enemy_id = bs.team_b_entities[0]
        _clear_map_objects(bs)

        _place(bs, mage_id, Position(0, 3))
        _place(bs, enemy_id, Position(5, 3))
        _place_object(bs, ObjectType.TREE, "tree_1", Position(3, 3))

        _advance_to(bs, mage_id)
        pa_before = bs.get_pa(mage_id)
        ability = bs.get_equipped_abilities(mage_id)[0]

        target_idx = 3 * 10 + 5
        bs.execute_action(ACTION_ABILITY_1, target_idx)

        pa_after = bs.get_pa(mage_id)
        assert pa_after == pa_before - ability.pa_cost, (
            "PA should be spent when projectile hits object"
        )


class TestAoEBlockedByObject:
    def test_aoe_blocked_hits_object_not_targets(self):
        bs = _make_battle(
            [CharacterClass.MAGE],
            [CharacterClass.WARRIOR, CharacterClass.ASSASSIN],
            seed=10,
        )
        mage_id = _get_entity_by_class(bs, CharacterClass.MAGE, "a")
        enemies = bs.team_b_entities
        _clear_map_objects(bs)

        _place(bs, mage_id, Position(0, 3))
        _place(bs, enemies[0], Position(5, 3))
        _place(bs, enemies[1], Position(5, 4))
        tree = _place_object(bs, ObjectType.TREE, "tree_1", Position(3, 3))

        _advance_to(bs, mage_id)
        hp_before = {eid: bs.get_character(eid).current_hp for eid in enemies}
        tree_hp_before = tree.current_hp

        # nova_flamejante = slot 1 = ACTION_ABILITY_2
        from engine.systems.battle import ACTION_ABILITY_2

        target_idx = 3 * 10 + 5  # AoE center at (5,3)
        bs.execute_action(ACTION_ABILITY_2, target_idx)

        assert tree.current_hp < tree_hp_before, "Tree should be hit by blocked AoE"
        for eid in enemies:
            assert bs.get_character(eid).current_hp == hp_before[eid], (
                "Enemies should NOT be hit when AoE is blocked"
            )


class TestBasicAttackHitsBlockingObject:
    def test_ranged_basic_attack_hits_tree(self):
        bs = _make_battle([CharacterClass.ARCHER], [CharacterClass.WARRIOR], seed=10)
        archer_id = _get_entity_by_class(bs, CharacterClass.ARCHER, "a")
        enemy_id = bs.team_b_entities[0]
        _clear_map_objects(bs)

        _place(bs, archer_id, Position(0, 3))
        _place(bs, enemy_id, Position(5, 3))
        tree = _place_object(bs, ObjectType.TREE, "tree_1", Position(3, 3))

        _advance_to(bs, archer_id)
        enemy_hp_before = bs.get_character(enemy_id).current_hp
        tree_hp_before = tree.current_hp

        target_idx = 3 * 10 + 5
        bs.execute_action(ACTION_BASIC, target_idx)

        assert tree.current_hp < tree_hp_before, (
            "Tree should take damage from basic ranged attack"
        )
        assert bs.get_character(enemy_id).current_hp == enemy_hp_before, (
            "Enemy should NOT take damage when basic attack hits tree"
        )

    def test_melee_basic_attack_ignores_los(self):
        bs = _make_battle([CharacterClass.WARRIOR], [CharacterClass.MAGE], seed=10)
        warrior_id = _get_entity_by_class(bs, CharacterClass.WARRIOR, "a")
        enemy_id = bs.team_b_entities[0]
        _clear_map_objects(bs)

        _place(bs, warrior_id, Position(3, 3))
        _place(bs, enemy_id, Position(4, 3))

        _advance_to(bs, warrior_id)
        enemy_hp_before = bs.get_character(enemy_id).current_hp

        target_idx = 3 * 10 + 4
        bs.execute_action(ACTION_BASIC, target_idx)

        assert bs.get_character(enemy_id).current_hp < enemy_hp_before, (
            "Melee basic attack should work regardless of LoS"
        )

    def test_basic_attack_pa_spent_when_hitting_object(self):
        bs = _make_battle([CharacterClass.ARCHER], [CharacterClass.WARRIOR], seed=10)
        archer_id = _get_entity_by_class(bs, CharacterClass.ARCHER, "a")
        enemy_id = bs.team_b_entities[0]
        _clear_map_objects(bs)

        _place(bs, archer_id, Position(0, 3))
        _place(bs, enemy_id, Position(5, 3))
        _place_object(bs, ObjectType.TREE, "tree_1", Position(3, 3))

        _advance_to(bs, archer_id)
        pa_before = bs.get_pa(archer_id)
        basic = bs.get_basic_attack(archer_id)

        target_idx = 3 * 10 + 5
        bs.execute_action(ACTION_BASIC, target_idx)

        pa_after = bs.get_pa(archer_id)
        assert pa_after == pa_before - basic.pa_cost, (
            "PA should be spent when basic attack hits object"
        )


class TestChargeBlockedByObject:
    def test_charge_stops_adjacent_to_surviving_object(self):
        bs = _make_battle([CharacterClass.WARRIOR], [CharacterClass.MAGE], seed=10)
        warrior_id = _get_entity_by_class(bs, CharacterClass.WARRIOR, "a")
        enemy_id = bs.team_b_entities[0]
        _clear_map_objects(bs)

        _place(bs, warrior_id, Position(0, 3))
        _place(bs, enemy_id, Position(5, 3))
        # Tree has HP=20, should survive the charge
        tree = _place_object(bs, ObjectType.TREE, "tree_1", Position(3, 3))

        _advance_to(bs, warrior_id)
        tree_hp_before = tree.current_hp
        enemy_hp_before = bs.get_character(enemy_id).current_hp

        # investida = slot 2 = ACTION_ABILITY_3
        target_idx = 3 * 10 + 5
        bs.execute_action(ACTION_ABILITY_3, target_idx)

        assert tree.current_hp < tree_hp_before, "Tree should take charge damage"
        assert not tree.is_destroyed, "Tree should survive the charge"
        assert bs.get_character(enemy_id).current_hp == enemy_hp_before, (
            "Enemy should NOT be damaged"
        )

        warrior_pos = bs.get_position(warrior_id)
        dist_to_tree = max(abs(warrior_pos.x - 3), abs(warrior_pos.y - 3))
        assert dist_to_tree == 1, (
            f"Warrior should be adjacent to tree, but is at {warrior_pos}"
        )

    def test_charge_lands_on_tile_when_object_destroyed(self):
        bs = _make_battle([CharacterClass.WARRIOR], [CharacterClass.MAGE], seed=10)
        warrior_id = _get_entity_by_class(bs, CharacterClass.WARRIOR, "a")
        enemy_id = bs.team_b_entities[0]
        _clear_map_objects(bs)

        _place(bs, warrior_id, Position(0, 3))
        _place(bs, enemy_id, Position(5, 3))
        # Bush has HP=5, should be destroyed easily
        bush = _place_object(bs, ObjectType.BUSH, "bush_1", Position(3, 3))

        _advance_to(bs, warrior_id)

        target_idx = 3 * 10 + 5
        bs.execute_action(ACTION_ABILITY_3, target_idx)

        if bush.is_destroyed:
            warrior_pos = bs.get_position(warrior_id)
            assert warrior_pos == Position(3, 3), (
                f"Warrior should land on destroyed object's tile, got {warrior_pos}"
            )

    def test_charge_emits_movement_event(self):
        bs = _make_battle([CharacterClass.WARRIOR], [CharacterClass.MAGE], seed=10)
        warrior_id = _get_entity_by_class(bs, CharacterClass.WARRIOR, "a")
        enemy_id = bs.team_b_entities[0]
        _clear_map_objects(bs)

        _place(bs, warrior_id, Position(0, 3))
        _place(bs, enemy_id, Position(5, 3))
        _place_object(bs, ObjectType.TREE, "tree_1", Position(3, 3))

        _advance_to(bs, warrior_id)
        bs._events.clear()

        target_idx = 3 * 10 + 5
        bs.execute_action(ACTION_ABILITY_3, target_idx)

        move_events = [e for e in bs._events if e["type"] == "ability_movement"]
        assert len(move_events) == 1
        assert move_events[0]["entity"] == warrior_id
        assert move_events[0]["movement"] == "charge"


class TestMeleeIgnoresLoS:
    def test_melee_ability_not_blocked(self):
        bs = _make_battle([CharacterClass.WARRIOR], [CharacterClass.ASSASSIN], seed=10)
        warrior_id = _get_entity_by_class(bs, CharacterClass.WARRIOR, "a")
        enemy_id = bs.team_b_entities[0]
        _clear_map_objects(bs)

        _place(bs, warrior_id, Position(3, 3))
        _place(bs, enemy_id, Position(4, 3))

        _advance_to(bs, warrior_id)
        enemy_hp_before = bs.get_character(enemy_id).current_hp

        # impacto_brutal = slot 0 = ACTION_ABILITY_1, melee AoE max_range=1
        target_idx = 3 * 10 + 4
        bs.execute_action(ACTION_ABILITY_1, target_idx)

        assert bs.get_character(enemy_id).current_hp < enemy_hp_before, (
            "Melee ability should work regardless of LoS"
        )


class TestDelayedAbilityIgnoresLoS:
    def test_meteoro_ignores_blocking_object(self):
        bs = _make_battle([CharacterClass.MAGE], [CharacterClass.WARRIOR], seed=10)
        mage_id = _get_entity_by_class(bs, CharacterClass.MAGE, "a")
        enemy_id = bs.team_b_entities[0]
        _clear_map_objects(bs)

        _place(bs, mage_id, Position(0, 3))
        _place(bs, enemy_id, Position(5, 3))
        tree = _place_object(bs, ObjectType.TREE, "tree_1", Position(3, 3))

        # Find if mage has meteoro equipped - it might not be in default loadout
        abilities = bs.get_equipped_abilities(mage_id)
        delayed_slot = None
        for i, ab in enumerate(abilities):
            if ab.delayed:
                delayed_slot = i
                break

        if delayed_slot is not None:
            _advance_to(bs, mage_id)
            tree_hp_before = tree.current_hp

            from engine.systems.battle import ACTION_ABILITY_1

            action = ACTION_ABILITY_1 + delayed_slot
            target_idx = 3 * 10 + 5
            bs.execute_action(action, target_idx)

            assert tree.current_hp == tree_hp_before, (
                "Tree should NOT be hit by delayed ability (Meteoro ignores LoS)"
            )
            delayed_marks = [e for e in bs._events if e["type"] == "delayed_mark"]
            assert len(delayed_marks) == 1, "Delayed mark should be placed"


class TestDirectObjectTargeting:
    def test_melee_basic_attack_targets_object(self):
        bs = _make_battle([CharacterClass.WARRIOR], [CharacterClass.MAGE], seed=10)
        warrior_id = _get_entity_by_class(bs, CharacterClass.WARRIOR, "a")
        _clear_map_objects(bs)

        _place(bs, warrior_id, Position(3, 3))
        # Place enemy far away so it doesn't interfere
        enemy_id = bs.team_b_entities[0]
        _place(bs, enemy_id, Position(9, 7))

        crate = _place_object(bs, ObjectType.CRATE, "crate_1", Position(4, 3))

        _advance_to(bs, warrior_id)
        crate_hp_before = crate.current_hp
        pa_before = bs.get_pa(warrior_id)

        target_idx = 3 * 10 + 4  # Position(4, 3)
        bs.execute_action(ACTION_BASIC, target_idx)

        assert crate.current_hp < crate_hp_before, (
            "Crate should take damage from melee basic attack"
        )
        assert bs.get_pa(warrior_id) < pa_before, "PA should be spent"

    def test_ranged_basic_attack_targets_object(self):
        bs = _make_battle([CharacterClass.ARCHER], [CharacterClass.MAGE], seed=10)
        archer_id = _get_entity_by_class(bs, CharacterClass.ARCHER, "a")
        _clear_map_objects(bs)

        _place(bs, archer_id, Position(0, 3))
        enemy_id = bs.team_b_entities[0]
        _place(bs, enemy_id, Position(9, 7))

        tree = _place_object(bs, ObjectType.TREE, "tree_1", Position(3, 3))

        _advance_to(bs, archer_id)
        tree_hp_before = tree.current_hp

        target_idx = 3 * 10 + 3  # Position(3, 3)
        bs.execute_action(ACTION_BASIC, target_idx)

        assert tree.current_hp < tree_hp_before, (
            "Tree should take damage from ranged basic attack targeting it"
        )

    def test_ability_targets_object_directly(self):
        bs = _make_battle([CharacterClass.MAGE], [CharacterClass.WARRIOR], seed=10)
        mage_id = _get_entity_by_class(bs, CharacterClass.MAGE, "a")
        _clear_map_objects(bs)

        _place(bs, mage_id, Position(0, 3))
        enemy_id = bs.team_b_entities[0]
        _place(bs, enemy_id, Position(9, 7))

        rock = _place_object(bs, ObjectType.ROCK, "rock_1", Position(3, 3))

        _advance_to(bs, mage_id)
        rock_hp_before = rock.current_hp

        target_idx = 3 * 10 + 3  # Position(3, 3) — the rock itself
        bs.execute_action(ACTION_ABILITY_1, target_idx)

        assert rock.current_hp < rock_hp_before, (
            "Rock should take damage from ability targeting it directly"
        )

    def test_rock_is_destructible(self):
        bs = _make_battle([CharacterClass.WARRIOR], [CharacterClass.MAGE], seed=10)
        warrior_id = _get_entity_by_class(bs, CharacterClass.WARRIOR, "a")
        _clear_map_objects(bs)

        _place(bs, warrior_id, Position(3, 3))
        enemy_id = bs.team_b_entities[0]
        _place(bs, enemy_id, Position(9, 7))

        rock = _place_object(bs, ObjectType.ROCK, "rock_1", Position(4, 3))
        assert rock.max_hp == 30

        rock.apply_damage(30)
        assert rock.is_destroyed is True
