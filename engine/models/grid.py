from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from engine.models.position import Position


class Team(Enum):
    A = "A"
    B = "B"


class OccupantType(Enum):
    CHARACTER = "character"
    OBJECT = "object"


@dataclass
class Occupant:
    entity_id: str
    occupant_type: OccupantType
    team: Team | None = None
    blocks_movement: bool = True


class Grid:
    COLS = 10
    ROWS = 8

    def __init__(self) -> None:
        self._cells: dict[Position, list[Occupant]] = {}

    def is_within_bounds(self, position: Position) -> bool:
        return 0 <= position.x < self.COLS and 0 <= position.y < self.ROWS

    def place_occupant(self, position: Position, occupant: Occupant) -> None:
        if not self.is_within_bounds(position):
            raise ValueError(f"Position {position} is out of bounds")
        occupants = self._cells.get(position, [])
        if occupant.occupant_type == OccupantType.CHARACTER:
            if any(o.occupant_type == OccupantType.CHARACTER for o in occupants):
                raise ValueError(f"Tile {position} already has a character")
        if position not in self._cells:
            self._cells[position] = []
        self._cells[position].append(occupant)

    def remove_occupant(self, position: Position, entity_id: str) -> None:
        occupants = self._cells.get(position, [])
        filtered = [o for o in occupants if o.entity_id != entity_id]
        if filtered:
            self._cells[position] = filtered
        elif position in self._cells:
            del self._cells[position]

    def get_occupants(self, position: Position) -> list[Occupant]:
        return list(self._cells.get(position, []))

    def get_spawn_positions(self, team: Team) -> set[Position]:
        if team == Team.A:
            cols = (0, 1)
        else:
            cols = (8, 9)
        return {Position(x, y) for x in cols for y in range(self.ROWS)}

    def get_adjacent_positions(self, position: Position) -> list[Position]:
        result = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                neighbor = Position(position.x + dx, position.y + dy)
                if self.is_within_bounds(neighbor):
                    result.append(neighbor)
        return result
