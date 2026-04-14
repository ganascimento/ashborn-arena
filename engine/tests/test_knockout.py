from engine.models.character import (
    BASE_ATTRIBUTES,
    BLEED_DAMAGE,
    DEATH_THRESHOLD,
    Character,
    CharacterClass,
    CharacterState,
)


def _make_warrior() -> Character:
    return Character(
        "w1", CharacterClass.WARRIOR, BASE_ATTRIBUTES[CharacterClass.WARRIOR]
    )


def _make_mage() -> Character:
    return Character("m1", CharacterClass.MAGE, BASE_ATTRIBUTES[CharacterClass.MAGE])


class TestCharacterStateEnum:
    def test_has_three_values(self):
        assert len(CharacterState) == 3

    def test_values(self):
        assert CharacterState.ACTIVE.value == "active"
        assert CharacterState.KNOCKED_OUT.value == "knocked_out"
        assert CharacterState.DEAD.value == "dead"


class TestConstants:
    def test_death_threshold(self):
        assert DEATH_THRESHOLD == -10

    def test_bleed_damage(self):
        assert BLEED_DAMAGE == 3


class TestInitialState:
    def test_starts_active(self):
        c = _make_warrior()
        assert c.state == CharacterState.ACTIVE

    def test_is_knocked_out_false(self):
        c = _make_warrior()
        assert c.is_knocked_out is False


class TestApplyDamage:
    def test_partial_damage_stays_active(self):
        c = _make_warrior()
        result = c.apply_damage(10)
        assert c.current_hp == 50
        assert c.state == CharacterState.ACTIVE
        assert result == CharacterState.ACTIVE

    def test_exact_hp_knockout(self):
        c = _make_warrior()
        result = c.apply_damage(60)
        assert c.current_hp == 0
        assert c.state == CharacterState.KNOCKED_OUT
        assert result == CharacterState.KNOCKED_OUT

    def test_negative_hp_knockout(self):
        c = _make_warrior()
        result = c.apply_damage(61)
        assert c.current_hp == -1
        assert c.state == CharacterState.KNOCKED_OUT
        assert result == CharacterState.KNOCKED_OUT

    def test_exactly_minus_10_knockout(self):
        c = _make_warrior()
        result = c.apply_damage(70)
        assert c.current_hp == -10
        assert c.state == CharacterState.KNOCKED_OUT
        assert result == CharacterState.KNOCKED_OUT

    def test_overkill_dead(self):
        c = _make_warrior()
        result = c.apply_damage(71)
        assert c.current_hp == -11
        assert c.state == CharacterState.DEAD
        assert result == CharacterState.DEAD

    def test_mage_overkill_dead(self):
        c = _make_mage()
        result = c.apply_damage(36)
        assert c.current_hp == -11
        assert c.state == CharacterState.DEAD

    def test_dead_ignores_further_damage(self):
        c = _make_warrior()
        c.apply_damage(71)
        hp_before = c.current_hp
        result = c.apply_damage(10)
        assert c.current_hp == hp_before
        assert c.state == CharacterState.DEAD
        assert result == CharacterState.DEAD

    def test_returns_state(self):
        c = _make_warrior()
        assert c.apply_damage(10) == CharacterState.ACTIVE


class TestApplyHealing:
    def test_heal_active(self):
        c = _make_warrior()
        c.apply_damage(20)
        result = c.apply_healing(10)
        assert c.current_hp == 50
        assert c.state == CharacterState.ACTIVE
        assert result == CharacterState.ACTIVE

    def test_heal_capped_at_max(self):
        c = _make_warrior()
        c.apply_damage(5)
        c.apply_healing(10)
        assert c.current_hp == 60

    def test_revive_from_knockout(self):
        c = _make_warrior()
        c.apply_damage(64)
        assert c.current_hp == -4
        result = c.apply_healing(15)
        assert c.current_hp == 11
        assert c.state == CharacterState.ACTIVE
        assert result == CharacterState.ACTIVE

    def test_heal_not_enough_to_revive(self):
        c = _make_warrior()
        c.apply_damage(69)
        assert c.current_hp == -9
        result = c.apply_healing(8)
        assert c.current_hp == -1
        assert c.state == CharacterState.KNOCKED_OUT
        assert result == CharacterState.KNOCKED_OUT

    def test_revive_from_minus_10(self):
        c = _make_warrior()
        c.apply_damage(70)
        assert c.current_hp == -10
        result = c.apply_healing(11)
        assert c.current_hp == 1
        assert c.state == CharacterState.ACTIVE

    def test_heal_to_exactly_zero_still_knocked(self):
        c = _make_warrior()
        c.apply_damage(70)
        result = c.apply_healing(10)
        assert c.current_hp == 0
        assert c.state == CharacterState.KNOCKED_OUT

    def test_dead_ignores_healing(self):
        c = _make_warrior()
        c.apply_damage(71)
        hp_before = c.current_hp
        result = c.apply_healing(20)
        assert c.current_hp == hp_before
        assert c.state == CharacterState.DEAD
        assert result == CharacterState.DEAD

    def test_returns_state(self):
        c = _make_warrior()
        assert c.apply_healing(10) == CharacterState.ACTIVE


class TestProcessBleed:
    def test_knockout_bleeds(self):
        c = _make_warrior()
        c.apply_damage(60)
        assert c.current_hp == 0
        dmg = c.process_bleed()
        assert dmg == 3
        assert c.current_hp == -3
        assert c.state == CharacterState.KNOCKED_OUT

    def test_bleed_to_minus_10_survives(self):
        c = _make_warrior()
        c.apply_damage(67)
        assert c.current_hp == -7
        dmg = c.process_bleed()
        assert dmg == 3
        assert c.current_hp == -10
        assert c.state == CharacterState.KNOCKED_OUT

    def test_bleed_kills(self):
        c = _make_warrior()
        c.apply_damage(68)
        assert c.current_hp == -8
        dmg = c.process_bleed()
        assert dmg == 3
        assert c.current_hp == -11
        assert c.state == CharacterState.DEAD

    def test_active_no_bleed(self):
        c = _make_warrior()
        dmg = c.process_bleed()
        assert dmg == 0
        assert c.current_hp == 60

    def test_dead_no_bleed(self):
        c = _make_warrior()
        c.apply_damage(71)
        hp_before = c.current_hp
        dmg = c.process_bleed()
        assert dmg == 0
        assert c.current_hp == hp_before


class TestRevivificationWindow:
    def test_hp_0_survives_3_bleeds(self):
        c = _make_warrior()
        c.apply_damage(60)
        for _ in range(3):
            c.process_bleed()
            assert c.state == CharacterState.KNOCKED_OUT
        c.process_bleed()
        assert c.state == CharacterState.DEAD

    def test_hp_minus_8_dies_on_first_bleed(self):
        c = _make_warrior()
        c.apply_damage(68)
        c.process_bleed()
        assert c.state == CharacterState.DEAD


class TestIsKnockedOut:
    def test_active(self):
        c = _make_warrior()
        assert c.is_knocked_out is False

    def test_knocked_out(self):
        c = _make_warrior()
        c.apply_damage(60)
        assert c.is_knocked_out is True

    def test_dead(self):
        c = _make_warrior()
        c.apply_damage(71)
        assert c.is_knocked_out is False
