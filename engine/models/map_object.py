from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from engine.models.position import Position

FIRE_DAMAGE = 3
FIRE_DURATION = 3
THROW_PA_COST = 2
THROW_DAMAGE_BASE = 6
THROW_DAMAGE_SCALING = 1.0


class ObjectType(Enum):
    CRATE = "crate"
    BARREL = "barrel"
    TREE = "tree"
    BUSH = "bush"
    ROCK = "rock"


@dataclass(frozen=True)
class ObjectTemplate:
    max_hp: int | None
    blocks_movement: bool
    blocks_los: bool
    flammable: bool
    throwable: bool


OBJECT_TEMPLATES: dict[ObjectType, ObjectTemplate] = {
    ObjectType.CRATE: ObjectTemplate(
        max_hp=10, blocks_movement=True, blocks_los=True, flammable=True, throwable=True
    ),
    ObjectType.BARREL: ObjectTemplate(
        max_hp=12, blocks_movement=True, blocks_los=True, flammable=True, throwable=True
    ),
    ObjectType.TREE: ObjectTemplate(
        max_hp=20,
        blocks_movement=True,
        blocks_los=True,
        flammable=True,
        throwable=False,
    ),
    ObjectType.BUSH: ObjectTemplate(
        max_hp=5,
        blocks_movement=False,
        blocks_los=False,
        flammable=True,
        throwable=False,
    ),
    ObjectType.ROCK: ObjectTemplate(
        max_hp=30,
        blocks_movement=True,
        blocks_los=True,
        flammable=False,
        throwable=False,
    ),
}


class MapObject:
    def __init__(
        self,
        entity_id: str,
        object_type: ObjectType,
        position: Position,
        template: ObjectTemplate,
    ) -> None:
        self._entity_id = entity_id
        self._object_type = object_type
        self._position = position
        self._max_hp = template.max_hp
        self._current_hp = template.max_hp
        self._blocks_movement = template.blocks_movement
        self._blocks_los = template.blocks_los
        self._flammable = template.flammable
        self._throwable = template.throwable
        self._on_fire = False
        self._fire_turns_remaining = 0
        self._is_destroyed = False

    @classmethod
    def from_type(
        cls, object_type: ObjectType, entity_id: str, position: Position
    ) -> MapObject:
        return cls(entity_id, object_type, position, OBJECT_TEMPLATES[object_type])

    @property
    def entity_id(self) -> str:
        return self._entity_id

    @property
    def object_type(self) -> ObjectType:
        return self._object_type

    @property
    def position(self) -> Position:
        return self._position

    @property
    def max_hp(self) -> int | None:
        return self._max_hp

    @property
    def current_hp(self) -> int | None:
        return self._current_hp

    @property
    def blocks_movement(self) -> bool:
        return self._blocks_movement

    @property
    def blocks_los(self) -> bool:
        return self._blocks_los

    @property
    def flammable(self) -> bool:
        return self._flammable

    @property
    def throwable(self) -> bool:
        return self._throwable

    @property
    def on_fire(self) -> bool:
        return self._on_fire

    @property
    def fire_turns_remaining(self) -> int:
        return self._fire_turns_remaining

    @property
    def is_destroyed(self) -> bool:
        return self._is_destroyed

    def apply_damage(self, amount: int) -> bool:
        if self._max_hp is None or self._is_destroyed:
            return False
        self._current_hp -= amount
        if self._current_hp <= 0:
            self._is_destroyed = True
            return True
        return False

    def ignite(self) -> bool:
        if not self._flammable or self._is_destroyed or self._on_fire:
            return False
        self._on_fire = True
        self._fire_turns_remaining = FIRE_DURATION
        return True

    def extinguish(self) -> bool:
        if not self._on_fire:
            return False
        self._on_fire = False
        self._fire_turns_remaining = 0
        return True

    def process_fire_tick(self) -> int:
        if not self._on_fire:
            return 0
        self._fire_turns_remaining -= 1
        if self._fire_turns_remaining <= 0:
            self._is_destroyed = True
            self._on_fire = False
        return FIRE_DAMAGE


def throw_distance(str_modifier: int) -> int:
    return max(1, 2 + str_modifier)
