import pytest

from engine.models.effect import Effect, EffectType
from engine.systems.effect_manager import EffectManager
from engine.systems.elemental import (
    ComboResult,
    check_elemental_combo,
    has_negative_status,
)


class TestComboResult:
    def test_fields(self):
        r = ComboResult(damage_modifier=1.5)
        assert r.damage_modifier == pytest.approx(1.5)
        assert r.apply_freeze is False
        assert r.freeze_duration == 0

    def test_freeze_fields(self):
        r = ComboResult(damage_modifier=1.0, apply_freeze=True, freeze_duration=1)
        assert r.apply_freeze is True
        assert r.freeze_duration == 1


class TestComboWetEletrico:
    def test_returns_combo(self):
        em = EffectManager()
        em.apply_effect("target", Effect("wet", EffectType.DEBUFF, "X", 2))
        result = check_elemental_combo(em, "target", "eletrico")
        assert result is not None
        assert result.damage_modifier == pytest.approx(1.50)
        assert result.apply_freeze is False

    def test_consumes_wet(self):
        em = EffectManager()
        em.apply_effect("target", Effect("wet", EffectType.DEBUFF, "X", 2))
        check_elemental_combo(em, "target", "eletrico")
        assert em.has_effect("target", "wet") is False


class TestComboWetFogo:
    def test_returns_combo(self):
        em = EffectManager()
        em.apply_effect("target", Effect("wet", EffectType.DEBUFF, "X", 2))
        result = check_elemental_combo(em, "target", "fogo")
        assert result is not None
        assert result.damage_modifier == pytest.approx(0.70)
        assert result.apply_freeze is False

    def test_consumes_wet(self):
        em = EffectManager()
        em.apply_effect("target", Effect("wet", EffectType.DEBUFF, "X", 2))
        check_elemental_combo(em, "target", "fogo")
        assert em.has_effect("target", "wet") is False


class TestComboWetGelo:
    def test_returns_combo(self):
        em = EffectManager()
        em.apply_effect("target", Effect("wet", EffectType.DEBUFF, "X", 2))
        result = check_elemental_combo(em, "target", "gelo")
        assert result is not None
        assert result.damage_modifier == pytest.approx(1.0)
        assert result.apply_freeze is True
        assert result.freeze_duration == 1

    def test_consumes_wet(self):
        em = EffectManager()
        em.apply_effect("target", Effect("wet", EffectType.DEBUFF, "X", 2))
        check_elemental_combo(em, "target", "gelo")
        assert em.has_effect("target", "wet") is False

    def test_applies_freeze_effect(self):
        em = EffectManager()
        em.apply_effect("target", Effect("wet", EffectType.DEBUFF, "X", 2))
        check_elemental_combo(em, "target", "gelo")
        assert em.has_effect("target", "freeze") is True
        freeze = em.get_effect("target", "freeze")
        assert freeze.effect_type == EffectType.CONTROL
        assert freeze.duration == 1


class TestNoCombo:
    def test_no_wet_returns_none(self):
        em = EffectManager()
        result = check_elemental_combo(em, "target", "eletrico")
        assert result is None

    def test_empty_tag_returns_none(self):
        em = EffectManager()
        em.apply_effect("target", Effect("wet", EffectType.DEBUFF, "X", 2))
        result = check_elemental_combo(em, "target", "")
        assert result is None

    def test_veneno_tag_returns_none(self):
        em = EffectManager()
        em.apply_effect("target", Effect("wet", EffectType.DEBUFF, "X", 2))
        result = check_elemental_combo(em, "target", "veneno")
        assert result is None

    def test_no_combo_preserves_wet(self):
        em = EffectManager()
        em.apply_effect("target", Effect("wet", EffectType.DEBUFF, "X", 2))
        check_elemental_combo(em, "target", "veneno")
        assert em.has_effect("target", "wet") is True

    def test_no_wet_preserves_nothing(self):
        em = EffectManager()
        check_elemental_combo(em, "target", "eletrico")
        assert em.get_effects("target") == []


class TestHasNegativeStatus:
    def test_debuff_is_negative(self):
        em = EffectManager()
        em.apply_effect("e", Effect("wet", EffectType.DEBUFF, "X", 2))
        assert has_negative_status(em, "e") is True

    def test_control_is_negative(self):
        em = EffectManager()
        em.apply_effect("e", Effect("freeze", EffectType.CONTROL, "X", 1))
        assert has_negative_status(em, "e") is True

    def test_dot_is_negative(self):
        em = EffectManager()
        em.apply_effect("e", Effect("bleed", EffectType.DOT, "X", 3, 4.0))
        assert has_negative_status(em, "e") is True

    def test_buff_only_is_not_negative(self):
        em = EffectManager()
        em.apply_effect("e", Effect("dr", EffectType.BUFF, "X", 2, 0.30))
        assert has_negative_status(em, "e") is False

    def test_hot_only_is_not_negative(self):
        em = EffectManager()
        em.apply_effect("e", Effect("regen", EffectType.HOT, "X", 3, 5.0))
        assert has_negative_status(em, "e") is False

    def test_shield_only_is_not_negative(self):
        em = EffectManager()
        em.apply_effect("e", Effect("barrier", EffectType.SHIELD, "X", 3, 15.0))
        assert has_negative_status(em, "e") is False

    def test_no_effects_is_not_negative(self):
        em = EffectManager()
        assert has_negative_status(em, "e") is False

    def test_buff_plus_debuff_is_negative(self):
        em = EffectManager()
        em.apply_effect("e", Effect("dr", EffectType.BUFF, "X", 2, 0.30))
        em.apply_effect("e", Effect("slow", EffectType.DEBUFF, "Y", 2))
        assert has_negative_status(em, "e") is True
