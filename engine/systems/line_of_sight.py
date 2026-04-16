from __future__ import annotations

from engine.models.position import Position


def get_tiles_in_line(origin: Position, target: Position) -> list[Position]:
    if origin == target:
        return []

    # Bresenham's line algorithm — traces all tiles the line crosses
    x0, y0 = origin.x, origin.y
    x1, y1 = target.x, target.y
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x1 > x0 else -1
    sy = 1 if y1 > y0 else -1
    err = dx - dy

    result: list[Position] = []
    cx, cy = x0, y0

    while True:
        if cx == x1 and cy == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            cx += sx
        if e2 < dx:
            err += dx
            cy += sy
        if cx == x1 and cy == y1:
            break
        result.append(Position(cx, cy))

    return result


def has_line_of_sight(
    origin: Position, target: Position, blocking_positions: set[Position]
) -> bool:
    for tile in get_tiles_in_line(origin, target):
        if tile in blocking_positions:
            return False
    return True


def find_first_blocker(
    origin: Position, target: Position, blocking_positions: set[Position]
) -> Position | None:
    for tile in get_tiles_in_line(origin, target):
        if tile in blocking_positions:
            return tile
    return None
