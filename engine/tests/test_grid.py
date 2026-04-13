import pytest

from engine.models.grid import Grid, Occupant, OccupantType, Team
from engine.models.position import Position


class TestPosition:
    def test_immutable(self):
        pos = Position(3, 4)
        with pytest.raises(AttributeError):
            pos.x = 5

    def test_hashable_in_set(self):
        pos = Position(3, 4)
        s = {pos, Position(3, 4), Position(1, 2)}
        assert len(s) == 2
        assert pos in s

    def test_hashable_as_dict_key(self):
        pos = Position(3, 4)
        d = {pos: "value"}
        assert d[Position(3, 4)] == "value"

    def test_equality(self):
        assert Position(3, 4) == Position(3, 4)

    def test_inequality(self):
        assert Position(0, 0) != Position(0, 1)
        assert Position(0, 0) != Position(1, 0)


class TestGridDimensions:
    def test_constants(self):
        assert Grid.COLS == 10
        assert Grid.ROWS == 8

    def test_grid_creates_successfully(self):
        grid = Grid()
        assert grid is not None


class TestGridBounds:
    def test_origin_is_valid(self):
        grid = Grid()
        assert grid.is_within_bounds(Position(0, 0)) is True

    def test_max_corner_is_valid(self):
        grid = Grid()
        assert grid.is_within_bounds(Position(9, 7)) is True

    def test_center_is_valid(self):
        grid = Grid()
        assert grid.is_within_bounds(Position(5, 4)) is True

    def test_negative_x(self):
        grid = Grid()
        assert grid.is_within_bounds(Position(-1, 0)) is False

    def test_negative_y(self):
        grid = Grid()
        assert grid.is_within_bounds(Position(0, -1)) is False

    def test_x_out_of_range(self):
        grid = Grid()
        assert grid.is_within_bounds(Position(10, 0)) is False

    def test_y_out_of_range(self):
        grid = Grid()
        assert grid.is_within_bounds(Position(0, 8)) is False


class TestGridOccupants:
    def test_place_and_get_character(self):
        grid = Grid()
        occupant = Occupant(
            entity_id="warrior_1", occupant_type=OccupantType.CHARACTER, team=Team.A
        )
        grid.place_occupant(Position(3, 4), occupant)
        occupants = grid.get_occupants(Position(3, 4))
        assert len(occupants) == 1
        assert occupants[0].entity_id == "warrior_1"
        assert occupants[0].occupant_type == OccupantType.CHARACTER
        assert occupants[0].team == Team.A

    def test_place_out_of_bounds_raises(self):
        grid = Grid()
        occupant = Occupant(
            entity_id="warrior_1", occupant_type=OccupantType.CHARACTER, team=Team.A
        )
        with pytest.raises(ValueError):
            grid.place_occupant(Position(10, 0), occupant)

    def test_place_two_characters_same_tile_raises(self):
        grid = Grid()
        char1 = Occupant(
            entity_id="warrior_1", occupant_type=OccupantType.CHARACTER, team=Team.A
        )
        char2 = Occupant(
            entity_id="mage_1", occupant_type=OccupantType.CHARACTER, team=Team.A
        )
        grid.place_occupant(Position(3, 4), char1)
        with pytest.raises(ValueError):
            grid.place_occupant(Position(3, 4), char2)

    def test_place_character_and_non_blocking_object(self):
        grid = Grid()
        obj = Occupant(
            entity_id="bush_1", occupant_type=OccupantType.OBJECT, blocks_movement=False
        )
        char = Occupant(
            entity_id="warrior_1", occupant_type=OccupantType.CHARACTER, team=Team.A
        )
        grid.place_occupant(Position(3, 4), obj)
        grid.place_occupant(Position(3, 4), char)
        occupants = grid.get_occupants(Position(3, 4))
        assert len(occupants) == 2
        entity_ids = {o.entity_id for o in occupants}
        assert entity_ids == {"bush_1", "warrior_1"}

    def test_remove_occupant(self):
        grid = Grid()
        occupant = Occupant(
            entity_id="warrior_1", occupant_type=OccupantType.CHARACTER, team=Team.A
        )
        grid.place_occupant(Position(3, 4), occupant)
        grid.remove_occupant(Position(3, 4), "warrior_1")
        assert grid.get_occupants(Position(3, 4)) == []

    def test_remove_one_of_multiple_occupants(self):
        grid = Grid()
        obj = Occupant(
            entity_id="bush_1", occupant_type=OccupantType.OBJECT, blocks_movement=False
        )
        char = Occupant(
            entity_id="warrior_1", occupant_type=OccupantType.CHARACTER, team=Team.A
        )
        grid.place_occupant(Position(3, 4), obj)
        grid.place_occupant(Position(3, 4), char)
        grid.remove_occupant(Position(3, 4), "warrior_1")
        occupants = grid.get_occupants(Position(3, 4))
        assert len(occupants) == 1
        assert occupants[0].entity_id == "bush_1"

    def test_get_occupants_empty_tile(self):
        grid = Grid()
        assert grid.get_occupants(Position(5, 5)) == []


class TestGridSpawnPositions:
    def test_team_a_spawn_count(self):
        grid = Grid()
        positions = grid.get_spawn_positions(Team.A)
        assert len(positions) == 16

    def test_team_a_spawn_columns(self):
        grid = Grid()
        positions = grid.get_spawn_positions(Team.A)
        for pos in positions:
            assert pos.x in (0, 1)
            assert 0 <= pos.y <= 7

    def test_team_b_spawn_count(self):
        grid = Grid()
        positions = grid.get_spawn_positions(Team.B)
        assert len(positions) == 16

    def test_team_b_spawn_columns(self):
        grid = Grid()
        positions = grid.get_spawn_positions(Team.B)
        for pos in positions:
            assert pos.x in (8, 9)
            assert 0 <= pos.y <= 7


class TestGridAdjacentPositions:
    def test_center_has_8_neighbors(self):
        grid = Grid()
        adj = grid.get_adjacent_positions(Position(4, 4))
        assert len(adj) == 8
        expected = {
            Position(3, 3), Position(4, 3), Position(5, 3),
            Position(3, 4),                 Position(5, 4),
            Position(3, 5), Position(4, 5), Position(5, 5),
        }
        assert set(adj) == expected

    def test_corner_0_0_has_3_neighbors(self):
        grid = Grid()
        adj = grid.get_adjacent_positions(Position(0, 0))
        assert len(adj) == 3
        expected = {Position(1, 0), Position(0, 1), Position(1, 1)}
        assert set(adj) == expected

    def test_corner_9_7_has_3_neighbors(self):
        grid = Grid()
        adj = grid.get_adjacent_positions(Position(9, 7))
        assert len(adj) == 3
        expected = {Position(8, 6), Position(9, 6), Position(8, 7)}
        assert set(adj) == expected

    def test_edge_5_0_has_5_neighbors(self):
        grid = Grid()
        adj = grid.get_adjacent_positions(Position(5, 0))
        assert len(adj) == 5
        expected = {
            Position(4, 0), Position(6, 0),
            Position(4, 1), Position(5, 1), Position(6, 1),
        }
        assert set(adj) == expected
