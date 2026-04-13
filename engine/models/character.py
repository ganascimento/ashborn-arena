from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CharacterClass(Enum):
    WARRIOR = "warrior"
    MAGE = "mage"
    CLERIC = "cleric"
    ARCHER = "archer"
    ASSASSIN = "assassin"


class CharacterState(Enum):
    ACTIVE = "active"
    KNOCKED_OUT = "knocked_out"
    DEAD = "dead"


@dataclass(frozen=True)
class Attributes:
    str: int
    dex: int
    con: int
    int_: int
    wis: int

    def modifier(self, attr_name: str) -> int:
        return getattr(self, attr_name) - 5

    @staticmethod
    def from_base_and_build(
        base: Attributes, build: tuple[int, int, int, int, int]
    ) -> Attributes:
        if sum(build) != 10:
            raise ValueError(f"Build points must sum to 10, got {sum(build)}")
        if any(v < 0 for v in build):
            raise ValueError("Build points cannot be negative")
        if any(v > 5 for v in build):
            raise ValueError("Build points per attribute cannot exceed 5")
        return Attributes(
            str=base.str + build[0],
            dex=base.dex + build[1],
            con=base.con + build[2],
            int_=base.int_ + build[3],
            wis=base.wis + build[4],
        )


BASE_ATTRIBUTES: dict[CharacterClass, Attributes] = {
    CharacterClass.WARRIOR: Attributes(str=8, dex=4, con=7, int_=2, wis=4),
    CharacterClass.MAGE: Attributes(str=2, dex=4, con=4, int_=9, wis=6),
    CharacterClass.CLERIC: Attributes(str=4, dex=3, con=6, int_=5, wis=8),
    CharacterClass.ARCHER: Attributes(str=3, dex=9, con=4, int_=4, wis=5),
    CharacterClass.ASSASSIN: Attributes(str=5, dex=8, con=3, int_=4, wis=5),
}

BASE_HP: dict[CharacterClass, int] = {
    CharacterClass.WARRIOR: 50,
    CharacterClass.MAGE: 30,
    CharacterClass.CLERIC: 45,
    CharacterClass.ARCHER: 35,
    CharacterClass.ASSASSIN: 35,
}

HP_PER_CON_MODIFIER = 5
DEATH_THRESHOLD = -10
BLEED_DAMAGE = 3


class Character:
    def __init__(
        self, entity_id: str, character_class: CharacterClass, attributes: Attributes
    ) -> None:
        self._entity_id = entity_id
        self._character_class = character_class
        self._attributes = attributes
        self._max_hp = BASE_HP[character_class] + (
            attributes.modifier("con") * HP_PER_CON_MODIFIER
        )
        self._current_hp = self._max_hp
        self._state = CharacterState.ACTIVE

    @property
    def entity_id(self) -> str:
        return self._entity_id

    @property
    def character_class(self) -> CharacterClass:
        return self._character_class

    @property
    def attributes(self) -> Attributes:
        return self._attributes

    @property
    def max_hp(self) -> int:
        return self._max_hp

    @property
    def current_hp(self) -> int:
        return self._current_hp

    @property
    def state(self) -> CharacterState:
        return self._state

    @property
    def is_knocked_out(self) -> bool:
        return self._state == CharacterState.KNOCKED_OUT

    def apply_damage(self, amount: int) -> CharacterState:
        if self._state == CharacterState.DEAD:
            return CharacterState.DEAD
        self._current_hp -= amount
        self._update_state()
        return self._state

    def apply_healing(self, amount: int) -> CharacterState:
        if self._state == CharacterState.DEAD:
            return CharacterState.DEAD
        self._current_hp = min(self._current_hp + amount, self._max_hp)
        self._update_state()
        return self._state

    def process_bleed(self) -> int:
        if self._state != CharacterState.KNOCKED_OUT:
            return 0
        self._current_hp -= BLEED_DAMAGE
        self._update_state()
        return BLEED_DAMAGE

    def _update_state(self) -> None:
        if self._current_hp > 0:
            self._state = CharacterState.ACTIVE
        elif self._current_hp >= DEATH_THRESHOLD:
            self._state = CharacterState.KNOCKED_OUT
        else:
            self._state = CharacterState.DEAD
