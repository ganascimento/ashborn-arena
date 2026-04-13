import random

import pytest

from engine.systems.damage import (
    DamageResult,
    DamageType,
    HealResult,
    calculate_raw_damage,
    critical_chance,
    evasion_chance,
    resolve_healing,
    resolve_magical_attack,
    resolve_physical_attack,
)


class TestCalculateRawDamage:
    def test_positive_modifier(self):
        assert calculate_raw_damage(base_damage=10, modifier=3, scaling=2) == 16

    def test_negative_modifier(self):
        assert calculate_raw_damage(base_damage=10, modifier=-3, scaling=2) == 4

    def test_zero_modifier(self):
        assert calculate_raw_damage(base_damage=10, modifier=0, scaling=2) == 10


class TestCriticalChance:
    def test_positive_dex(self):
        assert critical_chance(dex_modifier=4) == pytest.approx(0.08)

    def test_negative_dex(self):
        assert critical_chance(dex_modifier=-1) == 0.0

    def test_zero_dex(self):
        assert critical_chance(dex_modifier=0) == 0.0

    def test_max_dex(self):
        assert critical_chance(dex_modifier=9) == pytest.approx(0.18)


class TestEvasionChance:
    def test_positive_dex(self):
        assert evasion_chance(dex_modifier=4) == pytest.approx(0.12)

    def test_negative_dex(self):
        assert evasion_chance(dex_modifier=-1) == 0.0

    def test_max_dex(self):
        assert evasion_chance(dex_modifier=9) == pytest.approx(0.27)


class TestDamageResultFields:
    def test_fields(self):
        r = DamageResult(damage=10, is_critical=True, is_evaded=False, raw_damage=8)
        assert r.damage == 10
        assert r.is_critical is True
        assert r.is_evaded is False
        assert r.raw_damage == 8


class TestHealResultFields:
    def test_fields(self):
        r = HealResult(amount=15, new_hp=45)
        assert r.amount == 15
        assert r.new_hp == 45


class TestDamageType:
    def test_physical(self):
        assert DamageType.PHYSICAL.value == "physical"

    def test_magical(self):
        assert DamageType.MAGICAL.value == "magical"


class _NoCritNoEvadeRng:
    def random(self):
        return 0.99


class _ForceCritRng:
    def random(self):
        return 0.0


class _ForceEvadeRng:
    def __init__(self):
        self._call = 0

    def random(self):
        self._call += 1
        if self._call == 1:
            return 0.99
        return 0.0


class TestResolvePhysicalAttack:
    def test_normal_attack_warrior_vs_mage(self):
        result = resolve_physical_attack(
            base_damage=10,
            scaling=2,
            attack_modifier=3,
            attacker_dex_modifier=-1,
            defender_dex_modifier=-1,
            defender_con_modifier=-1,
            reduction_percent=0.0,
            rng=_NoCritNoEvadeRng(),
        )
        assert result.damage == 17
        assert result.raw_damage == 16
        assert result.is_critical is False
        assert result.is_evaded is False

    def test_no_crit(self):
        result = resolve_physical_attack(
            base_damage=8,
            scaling=2,
            attack_modifier=4,
            attacker_dex_modifier=4,
            defender_dex_modifier=-1,
            defender_con_modifier=2,
            reduction_percent=0.0,
            rng=_NoCritNoEvadeRng(),
        )
        assert result.damage == 14
        assert result.is_critical is False

    def test_with_crit(self):
        result = resolve_physical_attack(
            base_damage=8,
            scaling=2,
            attack_modifier=4,
            attacker_dex_modifier=4,
            defender_dex_modifier=-1,
            defender_con_modifier=2,
            reduction_percent=0.0,
            rng=_ForceCritRng(),
        )
        assert result.raw_damage == 24
        assert result.damage == 22
        assert result.is_critical is True

    def test_with_reduction(self):
        result = resolve_physical_attack(
            base_damage=8,
            scaling=2,
            attack_modifier=4,
            attacker_dex_modifier=4,
            defender_dex_modifier=-1,
            defender_con_modifier=2,
            reduction_percent=0.30,
            rng=_NoCritNoEvadeRng(),
        )
        assert result.damage == 9

    def test_evaded(self):
        result = resolve_physical_attack(
            base_damage=10,
            scaling=2,
            attack_modifier=3,
            attacker_dex_modifier=-1,
            defender_dex_modifier=4,
            defender_con_modifier=2,
            reduction_percent=0.0,
            rng=_ForceEvadeRng(),
        )
        assert result.damage == 0
        assert result.is_evaded is True

    def test_minimum_damage(self):
        result = resolve_physical_attack(
            base_damage=5,
            scaling=1,
            attack_modifier=0,
            attacker_dex_modifier=-1,
            defender_dex_modifier=-1,
            defender_con_modifier=7,
            reduction_percent=0.0,
            rng=_NoCritNoEvadeRng(),
        )
        assert result.damage == 1

    def test_accepts_optional_rng(self):
        result = resolve_physical_attack(
            base_damage=10,
            scaling=2,
            attack_modifier=3,
            attacker_dex_modifier=-1,
            defender_dex_modifier=-1,
            defender_con_modifier=-1,
        )
        assert isinstance(result, DamageResult)

    def test_negative_block_increases_damage(self):
        result = resolve_physical_attack(
            base_damage=10,
            scaling=2,
            attack_modifier=3,
            attacker_dex_modifier=-1,
            defender_dex_modifier=-1,
            defender_con_modifier=-1,
            reduction_percent=0.0,
            rng=_NoCritNoEvadeRng(),
        )
        assert result.damage == 17

    def test_positive_block_reduces_damage(self):
        result = resolve_physical_attack(
            base_damage=10,
            scaling=2,
            attack_modifier=3,
            attacker_dex_modifier=-1,
            defender_dex_modifier=-1,
            defender_con_modifier=2,
            reduction_percent=0.0,
            rng=_NoCritNoEvadeRng(),
        )
        assert result.damage == 14

    def test_stacking_reduction(self):
        result = resolve_physical_attack(
            base_damage=8,
            scaling=2,
            attack_modifier=4,
            attacker_dex_modifier=-1,
            defender_dex_modifier=-1,
            defender_con_modifier=2,
            reduction_percent=0.50,
            rng=_NoCritNoEvadeRng(),
        )
        assert result.damage == 7


class TestResolveMagicalAttack:
    def test_mage_vs_warrior(self):
        result = resolve_magical_attack(
            base_damage=12,
            scaling=2,
            attack_modifier=4,
            defender_wis_modifier=-1,
            reduction_percent=0.0,
        )
        assert result.damage == 21
        assert result.raw_damage == 20

    def test_mage_vs_cleric(self):
        result = resolve_magical_attack(
            base_damage=12,
            scaling=2,
            attack_modifier=4,
            defender_wis_modifier=3,
            reduction_percent=0.0,
        )
        assert result.damage == 17

    def test_with_reduction(self):
        result = resolve_magical_attack(
            base_damage=12,
            scaling=2,
            attack_modifier=4,
            defender_wis_modifier=3,
            reduction_percent=0.30,
        )
        assert result.damage == 11

    def test_minimum_damage(self):
        result = resolve_magical_attack(
            base_damage=5,
            scaling=1,
            attack_modifier=0,
            defender_wis_modifier=8,
            reduction_percent=0.0,
        )
        assert result.damage == 1

    def test_never_critical(self):
        result = resolve_magical_attack(
            base_damage=12,
            scaling=2,
            attack_modifier=4,
            defender_wis_modifier=-1,
        )
        assert result.is_critical is False

    def test_never_evaded(self):
        result = resolve_magical_attack(
            base_damage=12,
            scaling=2,
            attack_modifier=4,
            defender_wis_modifier=-1,
        )
        assert result.is_evaded is False

    def test_negative_resistance_increases_damage(self):
        result = resolve_magical_attack(
            base_damage=12,
            scaling=2,
            attack_modifier=4,
            defender_wis_modifier=-1,
        )
        assert result.damage == 21

    def test_no_reduction_unchanged(self):
        result = resolve_magical_attack(
            base_damage=12,
            scaling=2,
            attack_modifier=4,
            defender_wis_modifier=3,
            reduction_percent=0.0,
        )
        assert result.damage == 17


class TestResolveHealing:
    def test_normal_heal(self):
        result = resolve_healing(
            base_heal=10,
            scaling=3,
            healer_wis_modifier=3,
            target_current_hp=30,
            target_max_hp=50,
        )
        assert result.amount == 19
        assert result.new_hp == 49

    def test_heal_capped_at_max(self):
        result = resolve_healing(
            base_heal=10,
            scaling=3,
            healer_wis_modifier=3,
            target_current_hp=45,
            target_max_hp=50,
        )
        assert result.amount == 5
        assert result.new_hp == 50

    def test_heal_at_full_hp(self):
        result = resolve_healing(
            base_heal=10,
            scaling=3,
            healer_wis_modifier=3,
            target_current_hp=50,
            target_max_hp=50,
        )
        assert result.amount == 0
        assert result.new_hp == 50
