from __future__ import annotations

import math
import random as _random
from dataclasses import dataclass
from enum import Enum


class DamageType(Enum):
    PHYSICAL = "physical"
    MAGICAL = "magical"


@dataclass(frozen=True)
class DamageResult:
    damage: int
    is_critical: bool
    is_evaded: bool
    raw_damage: int


@dataclass(frozen=True)
class HealResult:
    amount: int
    new_hp: int


def calculate_raw_damage(base_damage: int, modifier: int, scaling: float) -> int:
    return base_damage + math.floor(modifier * scaling + 0.5)


def critical_chance(dex_modifier: int) -> float:
    return max(0.0, dex_modifier * 0.02)


def evasion_chance(dex_modifier: int) -> float:
    return max(0.0, dex_modifier * 0.03)


def resolve_physical_attack(
    base_damage: int,
    scaling: float,
    attack_modifier: int,
    attacker_dex_modifier: int,
    defender_dex_modifier: int,
    defender_con_modifier: int,
    reduction_percent: float = 0.0,
    rng: _random.Random | None = None,
) -> DamageResult:
    if rng is None:
        rng = _random.Random()

    raw = calculate_raw_damage(base_damage, attack_modifier, scaling)

    is_crit = rng.random() < critical_chance(attacker_dex_modifier)
    if is_crit:
        raw = int(raw * 1.5)

    if rng.random() < evasion_chance(defender_dex_modifier):
        return DamageResult(damage=0, is_critical=is_crit, is_evaded=True, raw_damage=raw)

    damage = raw - defender_con_modifier

    if reduction_percent > 0:
        damage = int(damage * (1 - reduction_percent))

    damage = max(damage, 1)

    return DamageResult(damage=damage, is_critical=is_crit, is_evaded=False, raw_damage=raw)


def resolve_magical_attack(
    base_damage: int,
    scaling: float,
    attack_modifier: int,
    defender_wis_modifier: int,
    reduction_percent: float = 0.0,
) -> DamageResult:
    raw = calculate_raw_damage(base_damage, attack_modifier, scaling)

    damage = raw - defender_wis_modifier

    if reduction_percent > 0:
        damage = int(damage * (1 - reduction_percent))

    damage = max(damage, 1)

    return DamageResult(damage=damage, is_critical=False, is_evaded=False, raw_damage=raw)


def resolve_healing(
    base_heal: int,
    scaling: float,
    healer_wis_modifier: int,
    target_current_hp: int,
    target_max_hp: int,
) -> HealResult:
    raw_heal = calculate_raw_damage(base_heal, healer_wis_modifier, scaling)
    new_hp = min(target_current_hp + raw_heal, target_max_hp)
    amount = new_hp - target_current_hp
    return HealResult(amount=amount, new_hp=new_hp)
