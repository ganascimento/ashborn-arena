from __future__ import annotations

import random as _random
from enum import Enum

from engine.models.grid import Grid, Occupant, OccupantType
from engine.models.map_object import OBJECT_TEMPLATES, MapObject, ObjectType
from engine.models.position import Position


class Biome(Enum):
    FOREST_DAY = "forest_day"
    VILLAGE = "village"


_BIOME_POOLS: dict[Biome, list[ObjectType]] = {
    Biome.FOREST_DAY: [
        ObjectType.TREE,
        ObjectType.BUSH,
        ObjectType.ROCK,
    ],
    Biome.VILLAGE: [
        ObjectType.CRATE,
        ObjectType.BARREL,
        ObjectType.ROCK,
        ObjectType.BUSH,
    ],
}

_MIN_OBJECTS = 12
_MAX_OBJECTS = 16
_INNER_COLS = range(2, 8)
_ROWS = range(1, 7)


def generate_map(
    biome: Biome, rng: _random.Random | None = None
) -> tuple[Grid, list[MapObject]]:
    if rng is None:
        rng = _random.Random()

    pool = _BIOME_POOLS[biome]
    total = rng.randint(_MIN_OBJECTS, _MAX_OBJECTS)

    available = [Position(x, y) for x in _INNER_COLS for y in _ROWS]
    rng.shuffle(available)
    positions = available[:total]

    types: list[ObjectType] = [rng.choice(pool) for _ in positions]
    positions, types = _ensure_center_blocking(positions, types, pool, rng)
    positions, types = _ensure_open_corridor(positions, types)

    grid = Grid()
    objects: list[MapObject] = []

    for i, (pos, obj_type) in enumerate(zip(positions, types)):
        entity_id = f"obj_{i}"
        template = OBJECT_TEMPLATES[obj_type]
        occupant = Occupant(
            entity_id=entity_id,
            occupant_type=OccupantType.OBJECT,
            blocks_movement=template.blocks_movement,
        )
        grid.place_occupant(pos, occupant)
        obj = MapObject(entity_id, obj_type, pos, template)
        objects.append(obj)

    return grid, objects


def _ensure_center_blocking(
    positions: list[Position],
    types: list[ObjectType],
    pool: list[ObjectType],
    rng: _random.Random,
) -> tuple[list[Position], list[ObjectType]]:
    blocking_types = [t for t in pool if OBJECT_TEMPLATES[t].blocks_movement]
    if not blocking_types:
        return positions, types

    center_blocking = sum(
        1
        for pos, t in zip(positions, types)
        if 3 <= pos.x <= 6 and OBJECT_TEMPLATES[t].blocks_movement
    )

    used = set(positions)
    while center_blocking < 2:
        for i, (pos, t) in enumerate(zip(positions, types)):
            if 3 <= pos.x <= 6 and not OBJECT_TEMPLATES[t].blocks_movement:
                types[i] = rng.choice(blocking_types)
                center_blocking += 1
                if center_blocking >= 2:
                    break
        else:
            candidates = [
                Position(x, y)
                for x in range(3, 7)
                for y in _ROWS
                if Position(x, y) not in used
            ]
            if candidates:
                pos = rng.choice(candidates)
                positions.append(pos)
                types.append(rng.choice(blocking_types))
                used.add(pos)
                center_blocking += 1
            else:
                break

    return positions, types


def _ensure_open_corridor(
    positions: list[Position],
    types: list[ObjectType],
) -> tuple[list[Position], list[ObjectType]]:
    blocking_positions = {
        pos for pos, t in zip(positions, types) if OBJECT_TEMPLATES[t].blocks_movement
    }

    for row in _ROWS:
        row_clear = all(
            Position(col, row) not in blocking_positions for col in _INNER_COLS
        )
        if row_clear:
            return positions, types

    best_row = min(
        _ROWS,
        key=lambda row: sum(
            1 for col in _INNER_COLS if Position(col, row) in blocking_positions
        ),
    )

    to_remove: list[int] = []
    for i, (pos, t) in enumerate(zip(positions, types)):
        if pos.y == best_row and OBJECT_TEMPLATES[t].blocks_movement:
            to_remove.append(i)

    for idx in reversed(to_remove):
        positions.pop(idx)
        types.pop(idx)

    return positions, types
