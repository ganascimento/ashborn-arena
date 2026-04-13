from engine.models.grid import Grid, Occupant, OccupantType, Team
from engine.models.position import Position
from engine.systems.opportunity import get_opportunity_attackers


class TestBasicTrigger:
    def test_enemy_loses_adjacency(self):
        grid = Grid()
        grid.place_occupant(
            Position(3, 3), Occupant("mover", OccupantType.CHARACTER, Team.A)
        )
        grid.place_occupant(
            Position(4, 4), Occupant("enemy", OccupantType.CHARACTER, Team.B)
        )
        result = get_opportunity_attackers(grid, Position(3, 3), Position(1, 3), Team.A)
        assert len(result) == 1
        assert result[0] == ("enemy", Position(4, 4))


class TestNoTriggerStaysAdjacent:
    def test_enemy_still_adjacent_at_destination(self):
        grid = Grid()
        grid.place_occupant(
            Position(3, 3), Occupant("mover", OccupantType.CHARACTER, Team.A)
        )
        grid.place_occupant(
            Position(4, 4), Occupant("enemy", OccupantType.CHARACTER, Team.B)
        )
        result = get_opportunity_attackers(grid, Position(3, 3), Position(3, 4), Team.A)
        assert result == []


class TestNoTriggerNeverAdjacent:
    def test_enemy_far_away(self):
        grid = Grid()
        grid.place_occupant(
            Position(3, 3), Occupant("mover", OccupantType.CHARACTER, Team.A)
        )
        grid.place_occupant(
            Position(6, 6), Occupant("enemy", OccupantType.CHARACTER, Team.B)
        )
        result = get_opportunity_attackers(grid, Position(3, 3), Position(3, 5), Team.A)
        assert result == []


class TestMultipleEnemies:
    def test_both_trigger(self):
        grid = Grid()
        grid.place_occupant(
            Position(3, 3), Occupant("mover", OccupantType.CHARACTER, Team.A)
        )
        grid.place_occupant(
            Position(4, 3), Occupant("e1", OccupantType.CHARACTER, Team.B)
        )
        grid.place_occupant(
            Position(2, 3), Occupant("e2", OccupantType.CHARACTER, Team.B)
        )
        result = get_opportunity_attackers(grid, Position(3, 3), Position(3, 5), Team.A)
        ids = {r[0] for r in result}
        assert ids == {"e1", "e2"}

    def test_only_one_triggers(self):
        grid = Grid()
        grid.place_occupant(
            Position(3, 3), Occupant("mover", OccupantType.CHARACTER, Team.A)
        )
        grid.place_occupant(
            Position(4, 4), Occupant("e1", OccupantType.CHARACTER, Team.B)
        )
        grid.place_occupant(
            Position(4, 3), Occupant("e2", OccupantType.CHARACTER, Team.B)
        )
        result = get_opportunity_attackers(grid, Position(3, 3), Position(4, 5), Team.A)
        ids = {r[0] for r in result}
        assert "e2" in ids
        assert "e1" not in ids


class TestTeamFiltering:
    def test_ally_does_not_trigger(self):
        grid = Grid()
        grid.place_occupant(
            Position(3, 3), Occupant("mover", OccupantType.CHARACTER, Team.A)
        )
        grid.place_occupant(
            Position(4, 4), Occupant("ally", OccupantType.CHARACTER, Team.A)
        )
        result = get_opportunity_attackers(grid, Position(3, 3), Position(3, 5), Team.A)
        assert result == []


class TestObjectFiltering:
    def test_object_does_not_trigger(self):
        grid = Grid()
        grid.place_occupant(
            Position(3, 3), Occupant("mover", OccupantType.CHARACTER, Team.A)
        )
        grid.place_occupant(
            Position(4, 4), Occupant("crate", OccupantType.OBJECT, blocks_movement=True)
        )
        result = get_opportunity_attackers(grid, Position(3, 3), Position(3, 5), Team.A)
        assert result == []


class TestEdgeCases:
    def test_grid_corner(self):
        grid = Grid()
        grid.place_occupant(
            Position(0, 0), Occupant("mover", OccupantType.CHARACTER, Team.A)
        )
        grid.place_occupant(
            Position(1, 1), Occupant("enemy", OccupantType.CHARACTER, Team.B)
        )
        result = get_opportunity_attackers(grid, Position(0, 0), Position(0, 3), Team.A)
        assert len(result) == 1
        assert result[0] == ("enemy", Position(1, 1))

    def test_same_position_no_trigger(self):
        grid = Grid()
        grid.place_occupant(
            Position(3, 3), Occupant("mover", OccupantType.CHARACTER, Team.A)
        )
        grid.place_occupant(
            Position(4, 4), Occupant("enemy", OccupantType.CHARACTER, Team.B)
        )
        result = get_opportunity_attackers(grid, Position(3, 3), Position(3, 3), Team.A)
        assert result == []

    def test_empty_grid_no_trigger(self):
        grid = Grid()
        grid.place_occupant(
            Position(3, 3), Occupant("mover", OccupantType.CHARACTER, Team.A)
        )
        result = get_opportunity_attackers(grid, Position(3, 3), Position(3, 5), Team.A)
        assert result == []
