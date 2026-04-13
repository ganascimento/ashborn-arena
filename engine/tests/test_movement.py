import pytest

from engine.models.grid import Grid, Occupant, OccupantType, Team
from engine.models.position import Position
from engine.systems.movement import (
    execute_move,
    find_path,
    get_reachable_tiles,
    tiles_for_pa,
)


class TestGetReachableTilesEmptyGrid:
    def test_center_2_tiles(self):
        grid = Grid()
        result = get_reachable_tiles(grid, Position(5, 4), 2, Team.A)
        assert len(result) == 24
        assert Position(5, 4) not in result

    def test_center_2_tiles_contains_expected(self):
        grid = Grid()
        result = get_reachable_tiles(grid, Position(5, 4), 2, Team.A)
        assert Position(5, 3) in result
        assert Position(7, 4) in result
        assert Position(3, 2) in result
        assert Position(7, 6) in result

    def test_corner_2_tiles(self):
        grid = Grid()
        result = get_reachable_tiles(grid, Position(0, 0), 2, Team.A)
        assert len(result) == 8
        assert Position(0, 0) not in result

    def test_zero_budget(self):
        grid = Grid()
        result = get_reachable_tiles(grid, Position(5, 4), 0, Team.A)
        assert len(result) == 0

    def test_1_tile_center(self):
        grid = Grid()
        result = get_reachable_tiles(grid, Position(5, 4), 1, Team.A)
        assert len(result) == 8


class TestGetReachableTilesBlocking:
    def test_enemy_blocks_passage(self):
        grid = Grid()
        enemy = Occupant(
            entity_id="enemy_1", occupant_type=OccupantType.CHARACTER, team=Team.B
        )
        grid.place_occupant(Position(4, 4), enemy)
        result = get_reachable_tiles(grid, Position(3, 4), 1, Team.A)
        assert Position(4, 4) not in result

    def test_pass_through_ally_but_cannot_stop(self):
        grid = Grid()
        ally = Occupant(
            entity_id="ally_1", occupant_type=OccupantType.CHARACTER, team=Team.A
        )
        grid.place_occupant(Position(4, 4), ally)
        result = get_reachable_tiles(grid, Position(3, 4), 2, Team.A)
        assert Position(5, 4) in result
        assert Position(4, 4) not in result

    def test_blocking_object_blocks_passage(self):
        grid = Grid()
        obj = Occupant(
            entity_id="crate_1", occupant_type=OccupantType.OBJECT, blocks_movement=True
        )
        grid.place_occupant(Position(4, 4), obj)
        result = get_reachable_tiles(grid, Position(3, 4), 1, Team.A)
        assert Position(4, 4) not in result

    def test_non_blocking_object_allows_passage(self):
        grid = Grid()
        obj = Occupant(
            entity_id="bush_1", occupant_type=OccupantType.OBJECT, blocks_movement=False
        )
        grid.place_occupant(Position(4, 4), obj)
        result = get_reachable_tiles(grid, Position(3, 4), 1, Team.A)
        assert Position(4, 4) in result

    def test_obstacle_detour_required(self):
        grid = Grid()
        for x in range(3, 6):
            enemy = Occupant(
                entity_id=f"enemy_{x}",
                occupant_type=OccupantType.CHARACTER,
                team=Team.B,
            )
            grid.place_occupant(Position(x, 4), enemy)
        result = get_reachable_tiles(grid, Position(4, 3), 2, Team.A)
        assert Position(4, 5) not in result
        assert Position(4, 2) in result

    def test_enemy_wall_blocks_movement_through(self):
        grid = Grid()
        for y in range(3, 6):
            enemy = Occupant(
                entity_id=f"enemy_{y}",
                occupant_type=OccupantType.CHARACTER,
                team=Team.B,
            )
            grid.place_occupant(Position(4, y), enemy)
        result = get_reachable_tiles(grid, Position(3, 4), 2, Team.A)
        assert Position(5, 4) not in result


class TestFindPath:
    def test_empty_grid_straight_line(self):
        grid = Grid()
        path = find_path(grid, Position(3, 3), Position(5, 3), Team.A)
        assert path is not None
        assert len(path) == 3
        assert path[0] == Position(3, 3)
        assert path[-1] == Position(5, 3)

    def test_path_around_enemy(self):
        grid = Grid()
        enemy = Occupant(
            entity_id="enemy_1", occupant_type=OccupantType.CHARACTER, team=Team.B
        )
        grid.place_occupant(Position(4, 3), enemy)
        path = find_path(grid, Position(3, 3), Position(5, 3), Team.A)
        assert path is not None
        assert path[0] == Position(3, 3)
        assert path[-1] == Position(5, 3)
        assert Position(4, 3) not in path

    def test_unreachable_surrounded_by_enemies(self):
        grid = Grid()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                enemy = Occupant(
                    entity_id=f"enemy_{dx}_{dy}",
                    occupant_type=OccupantType.CHARACTER,
                    team=Team.B,
                )
                grid.place_occupant(Position(5 + dx, 5 + dy), enemy)
        path = find_path(grid, Position(0, 0), Position(5, 5), Team.A)
        assert path is None

    def test_path_includes_start_and_end(self):
        grid = Grid()
        path = find_path(grid, Position(0, 0), Position(2, 2), Team.A)
        assert path is not None
        assert path[0] == Position(0, 0)
        assert path[-1] == Position(2, 2)

    def test_diagonal_path(self):
        grid = Grid()
        path = find_path(grid, Position(0, 0), Position(2, 2), Team.A)
        assert path is not None
        assert len(path) == 3


class TestExecuteMove:
    def test_success_updates_grid(self):
        grid = Grid()
        char = Occupant(
            entity_id="warrior_1", occupant_type=OccupantType.CHARACTER, team=Team.A
        )
        grid.place_occupant(Position(3, 3), char)
        path = execute_move(grid, "warrior_1", Position(3, 3), Position(5, 3), 2)
        assert path is not None
        assert path[0] == Position(3, 3)
        assert path[-1] == Position(5, 3)
        assert grid.get_occupants(Position(3, 3)) == []
        occupants = grid.get_occupants(Position(5, 3))
        assert len(occupants) == 1
        assert occupants[0].entity_id == "warrior_1"

    def test_out_of_range_raises(self):
        grid = Grid()
        char = Occupant(
            entity_id="warrior_1", occupant_type=OccupantType.CHARACTER, team=Team.A
        )
        grid.place_occupant(Position(0, 0), char)
        with pytest.raises(ValueError):
            execute_move(grid, "warrior_1", Position(0, 0), Position(9, 7), 2)


class TestTilesForPa:
    def test_1_pa(self):
        assert tiles_for_pa(1) == 2

    def test_4_pa(self):
        assert tiles_for_pa(4) == 8

    def test_0_pa(self):
        assert tiles_for_pa(0) == 0
