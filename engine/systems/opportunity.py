from __future__ import annotations

from engine.models.grid import Grid, OccupantType, Team
from engine.models.position import Position


def get_opportunity_attackers(
    grid: Grid,
    mover_position: Position,
    destination: Position,
    mover_team: Team,
) -> list[tuple[str, Position]]:
    if mover_position == destination:
        return []

    destination_neighbors = set(grid.get_adjacent_positions(destination))
    result: list[tuple[str, Position]] = []

    for adj_pos in grid.get_adjacent_positions(mover_position):
        for occupant in grid.get_occupants(adj_pos):
            if occupant.occupant_type != OccupantType.CHARACTER:
                continue
            if occupant.team == mover_team:
                continue
            if adj_pos not in destination_neighbors:
                result.append((occupant.entity_id, adj_pos))

    return result
