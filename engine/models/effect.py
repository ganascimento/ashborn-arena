from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EffectType(Enum):
    DOT = "dot"
    HOT = "hot"
    BUFF = "buff"
    DEBUFF = "debuff"
    CONTROL = "control"
    SHIELD = "shield"


@dataclass
class Effect:
    tag: str
    effect_type: EffectType
    source_entity_id: str
    duration: int
    value: float = 0.0
