import pytest

from engine.models.map_object import (
    FIRE_DAMAGE,
    FIRE_DURATION,
    OBJECT_TEMPLATES,
    THROW_DAMAGE_BASE,
    THROW_DAMAGE_SCALING,
    THROW_PA_COST,
    MapObject,
    ObjectType,
    throw_distance,
)
from engine.models.position import Position


class TestObjectType:
    def test_has_five_values(self):
        assert len(ObjectType) == 5

    def test_values(self):
        assert ObjectType.CRATE.value == "crate"
        assert ObjectType.BARREL.value == "barrel"
        assert ObjectType.TREE.value == "tree"
        assert ObjectType.BUSH.value == "bush"
        assert ObjectType.ROCK.value == "rock"


class TestObjectTemplates:
    def test_crate(self):
        t = OBJECT_TEMPLATES[ObjectType.CRATE]
        assert t.max_hp == 10
        assert t.blocks_movement is True
        assert t.blocks_los is True
        assert t.flammable is True
        assert t.throwable is True

    def test_barrel(self):
        t = OBJECT_TEMPLATES[ObjectType.BARREL]
        assert t.max_hp == 12
        assert t.blocks_movement is True
        assert t.blocks_los is True
        assert t.flammable is True
        assert t.throwable is True

    def test_tree(self):
        t = OBJECT_TEMPLATES[ObjectType.TREE]
        assert t.max_hp == 20
        assert t.blocks_movement is True
        assert t.blocks_los is True
        assert t.flammable is True
        assert t.throwable is False

    def test_bush(self):
        t = OBJECT_TEMPLATES[ObjectType.BUSH]
        assert t.max_hp == 5
        assert t.blocks_movement is False
        assert t.blocks_los is False
        assert t.flammable is True
        assert t.throwable is False

    def test_rock(self):
        t = OBJECT_TEMPLATES[ObjectType.ROCK]
        assert t.max_hp == 30
        assert t.blocks_movement is True
        assert t.blocks_los is True
        assert t.flammable is False
        assert t.throwable is False



class TestMapObjectCreation:
    def test_from_type_crate(self):
        obj = MapObject.from_type(ObjectType.CRATE, "crate_1", Position(3, 3))
        assert obj.entity_id == "crate_1"
        assert obj.object_type == ObjectType.CRATE
        assert obj.position == Position(3, 3)
        assert obj.current_hp == 10
        assert obj.max_hp == 10
        assert obj.blocks_movement is True
        assert obj.blocks_los is True
        assert obj.flammable is True
        assert obj.throwable is True

    def test_from_type_rock(self):
        obj = MapObject.from_type(ObjectType.ROCK, "rock_1", Position(5, 5))
        assert obj.current_hp == 30
        assert obj.max_hp == 30

    def test_initial_state(self):
        obj = MapObject.from_type(ObjectType.CRATE, "c1", Position(0, 0))
        assert obj.on_fire is False
        assert obj.fire_turns_remaining == 0
        assert obj.is_destroyed is False


class TestApplyDamage:
    def test_partial_damage(self):
        obj = MapObject.from_type(ObjectType.CRATE, "c1", Position(0, 0))
        result = obj.apply_damage(5)
        assert obj.current_hp == 5
        assert obj.is_destroyed is False
        assert result is False

    def test_exact_destroy(self):
        obj = MapObject.from_type(ObjectType.CRATE, "c1", Position(0, 0))
        result = obj.apply_damage(10)
        assert obj.current_hp == 0
        assert obj.is_destroyed is True
        assert result is True

    def test_overkill_destroy(self):
        obj = MapObject.from_type(ObjectType.CRATE, "c1", Position(0, 0))
        result = obj.apply_damage(15)
        assert obj.is_destroyed is True
        assert result is True

    def test_rock_takes_damage(self):
        obj = MapObject.from_type(ObjectType.ROCK, "r1", Position(0, 0))
        result = obj.apply_damage(10)
        assert obj.current_hp == 20
        assert obj.is_destroyed is False
        assert result is False

    def test_rock_can_be_destroyed(self):
        obj = MapObject.from_type(ObjectType.ROCK, "r1", Position(0, 0))
        result = obj.apply_damage(30)
        assert obj.is_destroyed is True
        assert result is True

    def test_destroyed_ignores_damage(self):
        obj = MapObject.from_type(ObjectType.CRATE, "c1", Position(0, 0))
        obj.apply_damage(10)
        hp_before = obj.current_hp
        result = obj.apply_damage(5)
        assert obj.current_hp == hp_before
        assert result is False


class TestIgnite:
    def test_flammable_ignites(self):
        obj = MapObject.from_type(ObjectType.CRATE, "c1", Position(0, 0))
        result = obj.ignite()
        assert result is True
        assert obj.on_fire is True
        assert obj.fire_turns_remaining == 3

    def test_non_flammable_refuses(self):
        obj = MapObject.from_type(ObjectType.ROCK, "r1", Position(0, 0))
        result = obj.ignite()
        assert result is False
        assert obj.on_fire is False

    def test_already_on_fire_refuses(self):
        obj = MapObject.from_type(ObjectType.CRATE, "c1", Position(0, 0))
        obj.ignite()
        result = obj.ignite()
        assert result is False

    def test_destroyed_refuses(self):
        obj = MapObject.from_type(ObjectType.CRATE, "c1", Position(0, 0))
        obj.apply_damage(10)
        result = obj.ignite()
        assert result is False


class TestProcessFireTick:
    def test_tick_decrements(self):
        obj = MapObject.from_type(ObjectType.CRATE, "c1", Position(0, 0))
        obj.ignite()
        dmg = obj.process_fire_tick()
        assert dmg == 3
        assert obj.fire_turns_remaining == 2
        assert obj.is_destroyed is False
        assert obj.on_fire is True

    def test_last_tick_destroys(self):
        obj = MapObject.from_type(ObjectType.CRATE, "c1", Position(0, 0))
        obj.ignite()
        obj.process_fire_tick()
        obj.process_fire_tick()
        dmg = obj.process_fire_tick()
        assert dmg == 3
        assert obj.fire_turns_remaining == 0
        assert obj.is_destroyed is True

    def test_not_on_fire_returns_zero(self):
        obj = MapObject.from_type(ObjectType.CRATE, "c1", Position(0, 0))
        dmg = obj.process_fire_tick()
        assert dmg == 0

    def test_full_fire_lifecycle(self):
        obj = MapObject.from_type(ObjectType.BARREL, "b1", Position(0, 0))
        obj.ignite()
        total = 0
        for i in range(3):
            total += obj.process_fire_tick()
        assert total == 9
        assert obj.is_destroyed is True


class TestExtinguish:
    def test_extinguish_on_fire(self):
        obj = MapObject.from_type(ObjectType.CRATE, "c1", Position(0, 0))
        obj.ignite()
        obj.apply_damage(3)
        result = obj.extinguish()
        assert result is True
        assert obj.on_fire is False
        assert obj.fire_turns_remaining == 0
        assert obj.current_hp == 7

    def test_extinguish_not_on_fire(self):
        obj = MapObject.from_type(ObjectType.CRATE, "c1", Position(0, 0))
        result = obj.extinguish()
        assert result is False

    def test_reignite_after_extinguish(self):
        obj = MapObject.from_type(ObjectType.CRATE, "c1", Position(0, 0))
        obj.ignite()
        obj.extinguish()
        result = obj.ignite()
        assert result is True
        assert obj.on_fire is True
        assert obj.fire_turns_remaining == 3


class TestThrowDistance:
    def test_positive_modifier(self):
        assert throw_distance(3) == 5

    def test_zero_modifier(self):
        assert throw_distance(0) == 2

    def test_negative_clamps_to_one(self):
        assert throw_distance(-3) == 1


class TestConstants:
    def test_fire_damage(self):
        assert FIRE_DAMAGE == 3

    def test_fire_duration(self):
        assert FIRE_DURATION == 3

    def test_throw_pa_cost(self):
        assert THROW_PA_COST == 2

    def test_throw_damage_base(self):
        assert THROW_DAMAGE_BASE == 6

    def test_throw_damage_scaling(self):
        assert THROW_DAMAGE_SCALING == pytest.approx(1.0)
