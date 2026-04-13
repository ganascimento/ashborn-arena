from __future__ import annotations

import random as _random
from enum import Enum

from engine.models.grid import Grid, Occupant, OccupantType
from engine.models.map_object import OBJECT_TEMPLATES, MapObject, ObjectType
from engine.models.position import Position


class Biome(Enum):
    FOREST_DAY = "forest_day"
    FOREST_NIGHT = "forest_night"
    VILLAGE = "village"
    SWAMP = "swamp"


_BIOME_POOLS: dict[Biome, list[ObjectType]] = {
    Biome.FOREST_DAY: [
        ObjectType.TREE,
        ObjectType.BUSH,
        ObjectType.ROCK,
        ObjectType.PUDDLE,
    ],
    Biome.FOREST_NIGHT: [
        ObjectType.TREE,
        ObjectType.BUSH,
        ObjectType.ROCK,
        ObjectType.PUDDLE,
    ],
    Biome.VILLAGE: [
        ObjectType.CRATE,
        ObjectType.BARREL,
        ObjectType.ROCK,
        ObjectType.BUSH,
    ],
    Biome.SWAMP: [ObjectType.PUDDLE, ObjectType.BUSH, ObjectType.TREE],
}

_MIN_OBJECTS = 12
_MAX_OBJECTS = 16
_LEFT_COLS = range(2, 5)
_RIGHT_COLS = range(5, 8)
_ROWS = range(8)
_CENTER_COLS = range(3, 7)


def generate_map(biome: Biome, rng: _random.Random) -> tuple[Grid, list[MapObject]]:
    pool = _BIOME_POOLS[biome]
    total_objects = rng.randint(_MIN_OBJECTS, _MAX_OBJECTS)

    half = total_objects // 2
    extra = total_objects % 2

    available_left: list[Position] = [Position(x, y) for x in _LEFT_COLS for y in _ROWS]
    rng.shuffle(available_left)

    left_positions: list[Position] = available_left[: half + extra]
    left_types: list[ObjectType] = [rng.choice(pool) for _ in left_positions]

    right_positions: list[Position] = []
    right_types: list[ObjectType] = []
    used: set[Position] = set(left_positions)

    for pos, obj_type in zip(left_positions[:half], left_types[:half]):
        mirror_x = 9 - pos.x
        mirror_y = pos.y
        if rng.random() < 0.3:
            mirror_y = max(0, min(7, mirror_y + rng.choice([-1, 0, 1])))
        mirror = Position(mirror_x, mirror_y)
        if mirror not in used:
            right_positions.append(mirror)
            right_types.append(rng.choice(pool))
            used.add(mirror)

    remaining_needed = total_objects - len(left_positions) - len(right_positions)
    if remaining_needed > 0:
        available_right = [
            Position(x, y)
            for x in _RIGHT_COLS
            for y in _ROWS
            if Position(x, y) not in used
        ]
        rng.shuffle(available_right)
        for pos in available_right[:remaining_needed]:
            right_positions.append(pos)
            right_types.append(rng.choice(pool))
            used.add(pos)

    all_positions = left_positions + right_positions
    all_types = left_types + right_types

    all_positions, all_types = _ensure_center_blocking(
        all_positions, all_types, pool, used, rng
    )
    all_positions, all_types = _ensure_open_corridor(all_positions, all_types, used)

    grid = Grid()
    objects: list[MapObject] = []

    for i, (pos, obj_type) in enumerate(zip(all_positions, all_types)):
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
    used: set[Position],
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

    while center_blocking < 2:
        for i, (pos, t) in enumerate(zip(positions, types)):
            if 3 <= pos.x <= 6 and not OBJECT_TEMPLATES[t].blocks_movement:
                types[i] = rng.choice(blocking_types)
                center_blocking += 1
                if center_blocking >= 2:
                    break
        else:
            available = [
                Position(x, y)
                for x in _CENTER_COLS
                for y in _ROWS
                if Position(x, y) not in used
            ]
            if available:
                pos = rng.choice(available)
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
    used: set[Position],
) -> tuple[list[Position], list[ObjectType]]:
    blocking_positions = {
        pos for pos, t in zip(positions, types) if OBJECT_TEMPLATES[t].blocks_movement
    }

    for row in range(8):
        row_clear = all(
            Position(col, row) not in blocking_positions for col in range(2, 8)
        )
        if row_clear:
            return positions, types

    best_row = 0
    min_blockers = 999
    for row in range(8):
        count = sum(
            1 for col in range(2, 8) if Position(col, row) in blocking_positions
        )
        if count < min_blockers:
            min_blockers = count
            best_row = row

    to_remove: list[int] = []
    for i, (pos, t) in enumerate(zip(positions, types)):
        if (
            pos.y == best_row
            and OBJECT_TEMPLATES[t].blocks_movement
            and 2 <= pos.x <= 7
        ):
            to_remove.append(i)

    for idx in reversed(to_remove):
        removed_pos = positions[idx]
        positions.pop(idx)
        types.pop(idx)
        used.discard(removed_pos)

    return positions, types
