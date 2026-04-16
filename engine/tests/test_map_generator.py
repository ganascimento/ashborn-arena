import random

import pytest

from engine.generation.map_generator import Biome, generate_map
from engine.models.grid import Grid, OccupantType
from engine.models.map_object import MapObject, ObjectType
from engine.models.position import Position


class TestBiomeEnum:
    def test_has_two_values(self):
        assert len(Biome) == 2

    def test_values(self):
        assert Biome.FOREST_DAY.value == "forest_day"
        assert Biome.VILLAGE.value == "village"


class TestGenerateMapBasic:
    @pytest.mark.parametrize("biome", list(Biome))
    def test_returns_grid_and_objects(self, biome):
        grid, objects = generate_map(biome, random.Random(42))
        assert isinstance(grid, Grid)
        assert isinstance(objects, list)
        assert all(isinstance(o, MapObject) for o in objects)

    @pytest.mark.parametrize("biome", list(Biome))
    def test_grid_dimensions(self, biome):
        grid, _ = generate_map(biome, random.Random(42))
        assert grid.COLS == 10
        assert grid.ROWS == 8


class TestDensity:
    @pytest.mark.parametrize("seed", range(20))
    def test_object_count_in_range(self, seed):
        _, objects = generate_map(Biome.VILLAGE, random.Random(seed))
        assert 10 <= len(objects) <= 18, f"seed {seed}: got {len(objects)} objects"


class TestSpawnAndBorderZones:
    @pytest.mark.parametrize("biome", list(Biome))
    @pytest.mark.parametrize("seed", range(10))
    def test_no_objects_in_spawn_or_border(self, biome, seed):
        _, objects = generate_map(biome, random.Random(seed))
        for obj in objects:
            assert 2 <= obj.position.x <= 7, (
                f"Object at col {obj.position.x} outside inner cols"
            )
            assert 1 <= obj.position.y <= 6, (
                f"Object at row {obj.position.y} on border row"
            )


class TestStructuralGuarantees:
    @pytest.mark.parametrize("biome", list(Biome))
    @pytest.mark.parametrize("seed", range(20))
    def test_min_2_blocking_in_center(self, biome, seed):
        _, objects = generate_map(biome, random.Random(seed))
        blocking_center = [
            o for o in objects if o.blocks_movement and 3 <= o.position.x <= 6
        ]
        assert len(blocking_center) >= 2, (
            f"seed {seed}: only {len(blocking_center)} blocking objects in center"
        )

    @pytest.mark.parametrize("biome", list(Biome))
    @pytest.mark.parametrize("seed", range(20))
    def test_min_1_open_corridor(self, biome, seed):
        _, objects = generate_map(biome, random.Random(seed))
        blocking_positions = {o.position for o in objects if o.blocks_movement}
        open_rows = 0
        for row in range(1, 7):
            row_clear = all(
                Position(col, row) not in blocking_positions for col in range(2, 8)
            )
            if row_clear:
                open_rows += 1
        assert open_rows >= 1, f"seed {seed}: no open corridor row found"


class TestBiomePools:
    _POOLS = {
        Biome.FOREST_DAY: {
            ObjectType.TREE,
            ObjectType.BUSH,
            ObjectType.ROCK,
        },
        Biome.VILLAGE: {
            ObjectType.CRATE,
            ObjectType.BARREL,
            ObjectType.ROCK,
            ObjectType.BUSH,
        },
    }

    @pytest.mark.parametrize("biome", list(Biome))
    def test_objects_from_pool(self, biome):
        _, objects = generate_map(biome, random.Random(42))
        allowed = self._POOLS[biome]
        for obj in objects:
            assert obj.object_type in allowed, (
                f"{biome.name}: {obj.object_type} not in pool {allowed}"
            )


class TestValidity:
    @pytest.mark.parametrize("biome", list(Biome))
    def test_no_duplicate_positions(self, biome):
        _, objects = generate_map(biome, random.Random(42))
        positions = [o.position for o in objects]
        assert len(positions) == len(set(positions))

    @pytest.mark.parametrize("biome", list(Biome))
    def test_unique_entity_ids(self, biome):
        _, objects = generate_map(biome, random.Random(42))
        ids = [o.entity_id for o in objects]
        assert len(ids) == len(set(ids))

    @pytest.mark.parametrize("biome", list(Biome))
    def test_grid_occupants_match_objects(self, biome):
        grid, objects = generate_map(biome, random.Random(42))
        for obj in objects:
            occupants = grid.get_occupants(obj.position)
            matching = [
                o
                for o in occupants
                if o.entity_id == obj.entity_id
                and o.occupant_type == OccupantType.OBJECT
            ]
            assert len(matching) == 1, (
                f"No matching occupant for {obj.entity_id} at {obj.position}"
            )
            assert matching[0].blocks_movement == obj.blocks_movement


class TestDeterminism:
    @pytest.mark.parametrize("biome", list(Biome))
    def test_same_seed_same_map(self, biome):
        _, objects_a = generate_map(biome, random.Random(42))
        _, objects_b = generate_map(biome, random.Random(42))
        positions_a = [(o.object_type, o.position) for o in objects_a]
        positions_b = [(o.object_type, o.position) for o in objects_b]
        assert positions_a == positions_b

    def test_different_seeds_different_maps(self):
        _, objects_a = generate_map(Biome.VILLAGE, random.Random(42))
        _, objects_b = generate_map(Biome.VILLAGE, random.Random(99))
        positions_a = {o.position for o in objects_a}
        positions_b = {o.position for o in objects_b}
        assert positions_a != positions_b
