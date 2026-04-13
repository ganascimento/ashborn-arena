import pytest

from engine.models.position import Position
from engine.systems.line_of_sight import get_tiles_in_line, has_line_of_sight


class TestGetTilesInLineHorizontal:
    def test_left_to_right(self):
        result = get_tiles_in_line(Position(0, 3), Position(4, 3))
        assert result == [Position(1, 3), Position(2, 3), Position(3, 3)]

    def test_right_to_left(self):
        result = get_tiles_in_line(Position(5, 3), Position(0, 3))
        assert result == [Position(4, 3), Position(3, 3), Position(2, 3), Position(1, 3)]


class TestGetTilesInLineVertical:
    def test_top_to_bottom(self):
        result = get_tiles_in_line(Position(3, 0), Position(3, 4))
        assert result == [Position(3, 1), Position(3, 2), Position(3, 3)]

    def test_bottom_to_top(self):
        result = get_tiles_in_line(Position(3, 4), Position(3, 0))
        assert result == [Position(3, 3), Position(3, 2), Position(3, 1)]


class TestGetTilesInLineDiagonal:
    def test_diagonal_down_right(self):
        result = get_tiles_in_line(Position(0, 0), Position(3, 3))
        assert result == [Position(1, 1), Position(2, 2)]

    def test_diagonal_up_left(self):
        result = get_tiles_in_line(Position(3, 3), Position(0, 0))
        assert result == [Position(2, 2), Position(1, 1)]


class TestGetTilesInLineEdgeCases:
    def test_same_position(self):
        result = get_tiles_in_line(Position(3, 3), Position(3, 3))
        assert result == []

    def test_adjacent_no_intermediaries(self):
        result = get_tiles_in_line(Position(3, 3), Position(4, 4))
        assert result == []

    def test_adjacent_horizontal(self):
        result = get_tiles_in_line(Position(3, 3), Position(4, 3))
        assert result == []

    def test_non_axis_aligned(self):
        result = get_tiles_in_line(Position(0, 0), Position(2, 4))
        assert len(result) > 0
        for pos in result:
            assert pos != Position(0, 0)
            assert pos != Position(2, 4)


class TestHasLosClear:
    def test_horizontal_clear(self):
        assert has_line_of_sight(Position(0, 3), Position(5, 3), set()) is True

    def test_vertical_clear(self):
        assert has_line_of_sight(Position(3, 0), Position(3, 5), set()) is True

    def test_diagonal_clear(self):
        assert has_line_of_sight(Position(0, 0), Position(4, 4), set()) is True

    def test_same_position(self):
        assert has_line_of_sight(Position(3, 3), Position(3, 3), set()) is True

    def test_adjacent(self):
        assert has_line_of_sight(Position(3, 3), Position(4, 4), set()) is True


class TestHasLosBlocked:
    def test_horizontal_blocked(self):
        blockers = {Position(3, 3)}
        assert has_line_of_sight(Position(0, 3), Position(5, 3), blockers) is False

    def test_diagonal_blocked(self):
        blockers = {Position(2, 2)}
        assert has_line_of_sight(Position(0, 0), Position(4, 4), blockers) is False

    def test_multiple_tiles_one_blocker(self):
        blockers = {Position(2, 3)}
        assert has_line_of_sight(Position(0, 3), Position(5, 3), blockers) is False


class TestHasLosOriginTargetExcluded:
    def test_blocker_at_origin_not_blocking(self):
        blockers = {Position(0, 3)}
        assert has_line_of_sight(Position(0, 3), Position(5, 3), blockers) is True

    def test_blocker_at_target_not_blocking(self):
        blockers = {Position(5, 3)}
        assert has_line_of_sight(Position(0, 3), Position(5, 3), blockers) is True


class TestHasLosNonBlockingObject:
    def test_non_blocking_position_does_not_block(self):
        blockers = set()
        assert has_line_of_sight(Position(0, 3), Position(5, 3), blockers) is True

    def test_only_blocking_positions_block(self):
        non_blockers = set()
        blockers = {Position(3, 3)}
        assert has_line_of_sight(Position(0, 3), Position(5, 3), blockers) is False
        assert has_line_of_sight(Position(0, 3), Position(5, 3), non_blockers) is True
