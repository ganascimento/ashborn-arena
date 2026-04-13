import pytest

from engine.models.effect import Effect, EffectType
from engine.systems.effect_manager import EffectManager


class TestEffectType:
    def test_has_six_types(self):
        assert len(EffectType) == 6

    def test_values(self):
        assert EffectType.DOT.value == "dot"
        assert EffectType.HOT.value == "hot"
        assert EffectType.BUFF.value == "buff"
        assert EffectType.DEBUFF.value == "debuff"
        assert EffectType.CONTROL.value == "control"
        assert EffectType.SHIELD.value == "shield"


class TestEffect:
    def test_fields(self):
        e = Effect(
            tag="bleed",
            effect_type=EffectType.DOT,
            source_entity_id="A",
            duration=3,
            value=4.0,
        )
        assert e.tag == "bleed"
        assert e.effect_type == EffectType.DOT
        assert e.source_entity_id == "A"
        assert e.duration == 3
        assert e.value == 4.0

    def test_default_value(self):
        e = Effect(
            tag="taunt",
            effect_type=EffectType.CONTROL,
            source_entity_id="A",
            duration=2,
        )
        assert e.value == 0.0

    def test_mutable_duration(self):
        e = Effect(
            tag="bleed",
            effect_type=EffectType.DOT,
            source_entity_id="A",
            duration=3,
            value=4.0,
        )
        e.duration -= 1
        assert e.duration == 2


class TestStackingDOT:
    def test_same_source_same_tag_renews(self):
        em = EffectManager()
        em.apply_effect("target", Effect("bleed", EffectType.DOT, "A", 3, 4.0))
        em.apply_effect("target", Effect("bleed", EffectType.DOT, "A", 3, 4.0))
        effects = em.get_effects("target")
        assert len(effects) == 1
        assert effects[0].duration == 3

    def test_different_source_same_tag_stacks(self):
        em = EffectManager()
        em.apply_effect("target", Effect("bleed", EffectType.DOT, "A", 3, 4.0))
        em.apply_effect("target", Effect("bleed", EffectType.DOT, "B", 3, 4.0))
        effects = em.get_effects("target")
        assert len(effects) == 2

    def test_same_source_renews_duration(self):
        em = EffectManager()
        em.apply_effect("target", Effect("bleed", EffectType.DOT, "A", 1, 4.0))
        em.apply_effect("target", Effect("bleed", EffectType.DOT, "A", 3, 5.0))
        effects = em.get_effects("target")
        assert len(effects) == 1
        assert effects[0].duration == 3
        assert effects[0].value == 5.0


class TestStackingHOT:
    def test_same_source_renews(self):
        em = EffectManager()
        em.apply_effect("target", Effect("regen", EffectType.HOT, "A", 3, 5.0))
        em.apply_effect("target", Effect("regen", EffectType.HOT, "A", 3, 5.0))
        assert len(em.get_effects("target")) == 1

    def test_different_source_stacks(self):
        em = EffectManager()
        em.apply_effect("target", Effect("regen", EffectType.HOT, "A", 3, 5.0))
        em.apply_effect("target", Effect("regen", EffectType.HOT, "B", 3, 5.0))
        assert len(em.get_effects("target")) == 2


class TestStackingBuffDebuffControl:
    def test_buff_same_tag_renews(self):
        em = EffectManager()
        em.apply_effect("target", Effect("dr", EffectType.BUFF, "A", 2, 0.30))
        em.apply_effect("target", Effect("dr", EffectType.BUFF, "B", 3, 0.25))
        effects = em.get_effects("target")
        assert len(effects) == 1
        assert effects[0].duration == 3
        assert effects[0].value == pytest.approx(0.25)

    def test_control_same_tag_renews(self):
        em = EffectManager()
        em.apply_effect("target", Effect("taunt", EffectType.CONTROL, "A", 2))
        em.apply_effect("target", Effect("taunt", EffectType.CONTROL, "B", 2))
        effects = em.get_effects("target")
        assert len(effects) == 1
        assert effects[0].duration == 2

    def test_debuff_same_tag_renews(self):
        em = EffectManager()
        em.apply_effect("target", Effect("slow", EffectType.DEBUFF, "A", 2))
        em.apply_effect("target", Effect("slow", EffectType.DEBUFF, "B", 3))
        effects = em.get_effects("target")
        assert len(effects) == 1
        assert effects[0].duration == 3

    def test_different_tags_coexist(self):
        em = EffectManager()
        em.apply_effect("target", Effect("buff_a", EffectType.BUFF, "A", 2, 0.30))
        em.apply_effect("target", Effect("buff_b", EffectType.BUFF, "A", 2, 0.20))
        effects = em.get_effects("target")
        assert len(effects) == 2
        total = sum(e.value for e in effects)
        assert total == pytest.approx(0.50)

    def test_shield_same_tag_renews(self):
        em = EffectManager()
        em.apply_effect("target", Effect("barrier", EffectType.SHIELD, "A", 3, 15.0))
        em.apply_effect("target", Effect("barrier", EffectType.SHIELD, "B", 3, 20.0))
        effects = em.get_effects("target")
        assert len(effects) == 1
        assert effects[0].value == 20.0


class TestProcessTurnStart:
    def test_buff_duration_2_full_lifecycle(self):
        em = EffectManager()
        em.apply_effect("target", Effect("dr", EffectType.BUFF, "A", 2, 0.30))

        expired = em.process_turn_start("target")
        assert len(expired) == 0
        assert em.has_effect("target", "dr")
        assert em.get_effect("target", "dr").duration == 1

        expired = em.process_turn_start("target")
        assert len(expired) == 0
        assert em.has_effect("target", "dr")
        assert em.get_effect("target", "dr").duration == 0

        expired = em.process_turn_start("target")
        assert len(expired) == 1
        assert expired[0].tag == "dr"
        assert not em.has_effect("target", "dr")

    def test_debuff_duration_1(self):
        em = EffectManager()
        em.apply_effect("target", Effect("slow", EffectType.DEBUFF, "A", 1))

        expired = em.process_turn_start("target")
        assert len(expired) == 0
        assert em.has_effect("target", "slow")

        expired = em.process_turn_start("target")
        assert len(expired) == 1
        assert not em.has_effect("target", "slow")

    def test_control_expires(self):
        em = EffectManager()
        em.apply_effect("target", Effect("taunt", EffectType.CONTROL, "A", 1))
        em.process_turn_start("target")
        expired = em.process_turn_start("target")
        assert len(expired) == 1
        assert expired[0].tag == "taunt"

    def test_shield_expires(self):
        em = EffectManager()
        em.apply_effect("target", Effect("barrier", EffectType.SHIELD, "A", 1, 15.0))
        em.process_turn_start("target")
        expired = em.process_turn_start("target")
        assert len(expired) == 1

    def test_dot_not_affected(self):
        em = EffectManager()
        em.apply_effect("target", Effect("bleed", EffectType.DOT, "A", 3, 4.0))
        em.process_turn_start("target")
        e = em.get_effect("target", "bleed")
        assert e.duration == 3

    def test_hot_not_affected(self):
        em = EffectManager()
        em.apply_effect("target", Effect("regen", EffectType.HOT, "A", 3, 5.0))
        em.process_turn_start("target")
        e = em.get_effect("target", "regen")
        assert e.duration == 3

    def test_no_effects_returns_empty(self):
        em = EffectManager()
        expired = em.process_turn_start("target")
        assert expired == []


class TestProcessTurnEnd:
    def test_dot_ticks_and_decrements(self):
        em = EffectManager()
        em.apply_effect("target", Effect("bleed", EffectType.DOT, "A", 3, 4.0))

        ticks = em.process_turn_end("target")
        assert len(ticks) == 1
        assert ticks[0].tag == "bleed"
        assert ticks[0].value == 4.0
        assert em.get_effect("target", "bleed").duration == 2

    def test_dot_full_lifecycle(self):
        em = EffectManager()
        em.apply_effect("target", Effect("bleed", EffectType.DOT, "A", 3, 4.0))

        total_damage = 0.0
        for _ in range(3):
            ticks = em.process_turn_end("target")
            total_damage += sum(t.value for t in ticks)

        assert total_damage == 12.0
        assert not em.has_effect("target", "bleed")

    def test_dot_removed_after_last_tick(self):
        em = EffectManager()
        em.apply_effect("target", Effect("bleed", EffectType.DOT, "A", 1, 4.0))

        ticks = em.process_turn_end("target")
        assert len(ticks) == 1
        assert not em.has_effect("target", "bleed")

    def test_multiple_dots_tick_independently(self):
        em = EffectManager()
        em.apply_effect("target", Effect("bleed", EffectType.DOT, "A", 3, 4.0))
        em.apply_effect("target", Effect("bleed", EffectType.DOT, "B", 3, 4.0))

        ticks = em.process_turn_end("target")
        assert len(ticks) == 2
        assert sum(t.value for t in ticks) == 8.0

    def test_hot_ticks(self):
        em = EffectManager()
        em.apply_effect("target", Effect("regen", EffectType.HOT, "A", 3, 5.0))

        ticks = em.process_turn_end("target")
        assert len(ticks) == 1
        assert ticks[0].effect_type == EffectType.HOT
        assert ticks[0].value == 5.0

    def test_hot_full_lifecycle(self):
        em = EffectManager()
        em.apply_effect("target", Effect("regen", EffectType.HOT, "A", 3, 5.0))

        total_heal = 0.0
        for _ in range(3):
            ticks = em.process_turn_end("target")
            total_heal += sum(t.value for t in ticks)

        assert total_heal == 15.0
        assert not em.has_effect("target", "regen")

    def test_buff_not_ticked(self):
        em = EffectManager()
        em.apply_effect("target", Effect("dr", EffectType.BUFF, "A", 2, 0.30))

        ticks = em.process_turn_end("target")
        assert len(ticks) == 0

    def test_no_effects_returns_empty(self):
        em = EffectManager()
        ticks = em.process_turn_end("target")
        assert ticks == []


class TestQueries:
    def test_get_effects_returns_all(self):
        em = EffectManager()
        em.apply_effect("target", Effect("bleed", EffectType.DOT, "A", 3, 4.0))
        em.apply_effect("target", Effect("dr", EffectType.BUFF, "A", 2, 0.30))
        assert len(em.get_effects("target")) == 2

    def test_get_effects_returns_copy(self):
        em = EffectManager()
        em.apply_effect("target", Effect("bleed", EffectType.DOT, "A", 3, 4.0))
        effects = em.get_effects("target")
        effects.clear()
        assert len(em.get_effects("target")) == 1

    def test_get_effects_by_type(self):
        em = EffectManager()
        em.apply_effect("target", Effect("bleed", EffectType.DOT, "A", 3, 4.0))
        em.apply_effect("target", Effect("dr", EffectType.BUFF, "A", 2, 0.30))
        em.apply_effect("target", Effect("poison", EffectType.DOT, "B", 2, 3.0))

        dots = em.get_effects_by_type("target", EffectType.DOT)
        assert len(dots) == 2
        buffs = em.get_effects_by_type("target", EffectType.BUFF)
        assert len(buffs) == 1

    def test_has_effect_true(self):
        em = EffectManager()
        em.apply_effect("target", Effect("bleed", EffectType.DOT, "A", 3, 4.0))
        assert em.has_effect("target", "bleed") is True

    def test_has_effect_false(self):
        em = EffectManager()
        assert em.has_effect("target", "bleed") is False

    def test_get_effect_found(self):
        em = EffectManager()
        em.apply_effect("target", Effect("taunt", EffectType.CONTROL, "A", 2))
        e = em.get_effect("target", "taunt")
        assert e is not None
        assert e.tag == "taunt"

    def test_get_effect_not_found(self):
        em = EffectManager()
        assert em.get_effect("target", "taunt") is None

    def test_empty_entity(self):
        em = EffectManager()
        assert em.get_effects("nobody") == []
        assert em.has_effect("nobody", "bleed") is False


class TestRemoval:
    def test_remove_by_tag(self):
        em = EffectManager()
        em.apply_effect("target", Effect("bleed", EffectType.DOT, "A", 3, 4.0))
        em.apply_effect("target", Effect("bleed", EffectType.DOT, "B", 3, 4.0))
        em.apply_effect("target", Effect("dr", EffectType.BUFF, "A", 2, 0.30))

        count = em.remove_effects_by_tag("target", "bleed")
        assert count == 2
        assert not em.has_effect("target", "bleed")
        assert em.has_effect("target", "dr")

    def test_remove_all_negative(self):
        em = EffectManager()
        em.apply_effect("target", Effect("dr", EffectType.BUFF, "A", 2, 0.30))
        em.apply_effect("target", Effect("slow", EffectType.DEBUFF, "B", 2))
        em.apply_effect("target", Effect("taunt", EffectType.CONTROL, "C", 2))
        em.apply_effect("target", Effect("bleed", EffectType.DOT, "D", 3, 4.0))
        em.apply_effect("target", Effect("regen", EffectType.HOT, "E", 3, 5.0))
        em.apply_effect("target", Effect("barrier", EffectType.SHIELD, "F", 3, 15.0))

        removed = em.remove_all_negative("target")
        removed_tags = {e.tag for e in removed}
        assert removed_tags == {"slow", "taunt"}

        remaining = em.get_effects("target")
        remaining_tags = {e.tag for e in remaining}
        assert remaining_tags == {"dr", "bleed", "regen", "barrier"}

    def test_remove_all_negative_returns_removed(self):
        em = EffectManager()
        em.apply_effect("target", Effect("slow", EffectType.DEBUFF, "A", 2))
        removed = em.remove_all_negative("target")
        assert len(removed) == 1
        assert removed[0].tag == "slow"

    def test_remove_entity(self):
        em = EffectManager()
        em.apply_effect("target", Effect("bleed", EffectType.DOT, "A", 3, 4.0))
        em.apply_effect("target", Effect("dr", EffectType.BUFF, "A", 2, 0.30))
        em.remove_entity("target")
        assert em.get_effects("target") == []
