from __future__ import annotations

from collections import deque

from engine.models.grid import Grid, Occupant, OccupantType, Team
from engine.models.position import Position


def tiles_for_pa(pa: int) -> int:
    return pa * 2


def _is_traversable(grid: Grid, pos: Position, mover_team: Team) -> bool:
    occupants = grid.get_occupants(pos)
    if not occupants:
        return True
    for o in occupants:
        if o.occupant_type == OccupantType.CHARACTER and o.team != mover_team:
            return False
        if o.occupant_type == OccupantType.OBJECT and o.blocks_movement:
            return False
    return True


def _can_stop(grid: Grid, pos: Position) -> bool:
    occupants = grid.get_occupants(pos)
    for o in occupants:
        if o.occupant_type == OccupantType.CHARACTER:
            return False
        if o.occupant_type == OccupantType.OBJECT and o.blocks_movement:
            return False
    return True


def get_reachable_tiles(
    grid: Grid, start: Position, max_tiles: int, mover_team: Team
) -> set[Position]:
    if max_tiles <= 0:
        return set()

    visited: dict[Position, int] = {start: 0}
    queue: deque[tuple[Position, int]] = deque([(start, 0)])
    result: set[Position] = set()

    while queue:
        current, dist = queue.popleft()
        if dist >= max_tiles:
            continue
        for neighbor in grid.get_adjacent_positions(current):
            if neighbor in visited:
                continue
            if not _is_traversable(grid, neighbor, mover_team):
                continue
            visited[neighbor] = dist + 1
            queue.append((neighbor, dist + 1))
            if _can_stop(grid, neighbor):
                result.add(neighbor)

    return result


def find_path(
    grid: Grid, start: Position, end: Position, mover_team: Team
) -> list[Position] | None:
    if start == end:
        return [start]

    if not _can_stop(grid, end):
        return None

    visited: set[Position] = {start}
    queue: deque[tuple[Position, list[Position]]] = deque([(start, [start])])

    while queue:
        current, path = queue.popleft()
        for neighbor in grid.get_adjacent_positions(current):
            if neighbor in visited:
                continue
            if not _is_traversable(grid, neighbor, mover_team):
                continue
            new_path = path + [neighbor]
            if neighbor == end:
                return new_path
            visited.add(neighbor)
            queue.append((neighbor, new_path))

    return None


def execute_move(
    grid: Grid, entity_id: str, start: Position, end: Position, max_tiles: int
) -> list[Position]:
    occupants = grid.get_occupants(start)
    mover = None
    for o in occupants:
        if o.entity_id == entity_id and o.occupant_type == OccupantType.CHARACTER:
            mover = o
            break

    if mover is None:
        raise ValueError(f"No character with id '{entity_id}' at {start}")

    reachable = get_reachable_tiles(grid, start, max_tiles, mover.team)
    if end not in reachable:
        raise ValueError(f"Destination {end} is not reachable within {max_tiles} tiles")

    path = find_path(grid, start, end, mover.team)
    if path is None:
        raise ValueError(f"No path found from {start} to {end}")

    grid.remove_occupant(start, entity_id)
    grid.place_occupant(end, mover)

    return path
