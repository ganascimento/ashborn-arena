import pytest

from engine.models.character import (
    BASE_ATTRIBUTES,
    BASE_HP,
    Attributes,
    Character,
    CharacterClass,
)


class TestCharacterClass:
    def test_has_five_classes(self):
        assert len(CharacterClass) == 5

    def test_warrior(self):
        assert CharacterClass.WARRIOR.value == "warrior"

    def test_mage(self):
        assert CharacterClass.MAGE.value == "mage"

    def test_cleric(self):
        assert CharacterClass.CLERIC.value == "cleric"

    def test_archer(self):
        assert CharacterClass.ARCHER.value == "archer"

    def test_assassin(self):
        assert CharacterClass.ASSASSIN.value == "assassin"


class TestBaseAttributes:
    def test_warrior(self):
        a = BASE_ATTRIBUTES[CharacterClass.WARRIOR]
        assert (a.str, a.dex, a.con, a.int_, a.wis) == (8, 4, 7, 2, 4)

    def test_mage(self):
        a = BASE_ATTRIBUTES[CharacterClass.MAGE]
        assert (a.str, a.dex, a.con, a.int_, a.wis) == (2, 4, 4, 9, 6)

    def test_cleric(self):
        a = BASE_ATTRIBUTES[CharacterClass.CLERIC]
        assert (a.str, a.dex, a.con, a.int_, a.wis) == (4, 3, 6, 5, 8)

    def test_archer(self):
        a = BASE_ATTRIBUTES[CharacterClass.ARCHER]
        assert (a.str, a.dex, a.con, a.int_, a.wis) == (3, 9, 4, 4, 5)

    def test_assassin(self):
        a = BASE_ATTRIBUTES[CharacterClass.ASSASSIN]
        assert (a.str, a.dex, a.con, a.int_, a.wis) == (5, 8, 3, 4, 5)


class TestBaseHP:
    def test_warrior(self):
        assert BASE_HP[CharacterClass.WARRIOR] == 50

    def test_mage(self):
        assert BASE_HP[CharacterClass.MAGE] == 30

    def test_cleric(self):
        assert BASE_HP[CharacterClass.CLERIC] == 45

    def test_archer(self):
        assert BASE_HP[CharacterClass.ARCHER] == 35

    def test_assassin(self):
        assert BASE_HP[CharacterClass.ASSASSIN] == 35


class TestModifiers:
    def test_warrior_base(self):
        a = BASE_ATTRIBUTES[CharacterClass.WARRIOR]
        assert a.modifier("str") == 3
        assert a.modifier("dex") == -1
        assert a.modifier("con") == 2
        assert a.modifier("int_") == -3
        assert a.modifier("wis") == -1

    def test_mage_base(self):
        a = BASE_ATTRIBUTES[CharacterClass.MAGE]
        assert a.modifier("str") == -3
        assert a.modifier("dex") == -1
        assert a.modifier("con") == -1
        assert a.modifier("int_") == 4
        assert a.modifier("wis") == 1

    def test_cleric_base(self):
        a = BASE_ATTRIBUTES[CharacterClass.CLERIC]
        assert a.modifier("str") == -1
        assert a.modifier("dex") == -2
        assert a.modifier("con") == 1
        assert a.modifier("int_") == 0
        assert a.modifier("wis") == 3

    def test_archer_base(self):
        a = BASE_ATTRIBUTES[CharacterClass.ARCHER]
        assert a.modifier("str") == -2
        assert a.modifier("dex") == 4
        assert a.modifier("con") == -1
        assert a.modifier("int_") == -1
        assert a.modifier("wis") == 0

    def test_assassin_base(self):
        a = BASE_ATTRIBUTES[CharacterClass.ASSASSIN]
        assert a.modifier("str") == 0
        assert a.modifier("dex") == 3
        assert a.modifier("con") == -2
        assert a.modifier("int_") == -1
        assert a.modifier("wis") == 0

    def test_neutral_value(self):
        a = Attributes(str=5, dex=5, con=5, int_=5, wis=5)
        assert a.modifier("str") == 0
        assert a.modifier("dex") == 0

    def test_max_possible_modifier(self):
        a = Attributes(str=14, dex=14, con=14, int_=14, wis=14)
        assert a.modifier("str") == 9


class TestBuildValidation:
    def test_valid_balanced(self):
        base = BASE_ATTRIBUTES[CharacterClass.WARRIOR]
        result = Attributes.from_base_and_build(base, (3, 2, 2, 2, 1))
        assert result.str == 11
        assert result.dex == 6
        assert result.con == 9
        assert result.int_ == 4
        assert result.wis == 5

    def test_valid_max_two_attributes(self):
        base = BASE_ATTRIBUTES[CharacterClass.WARRIOR]
        result = Attributes.from_base_and_build(base, (5, 5, 0, 0, 0))
        assert result.str == 13
        assert result.dex == 9

    def test_valid_even_split(self):
        base = BASE_ATTRIBUTES[CharacterClass.MAGE]
        result = Attributes.from_base_and_build(base, (2, 2, 2, 2, 2))
        assert result.str == 4
        assert result.int_ == 11

    def test_invalid_sum_too_low(self):
        base = BASE_ATTRIBUTES[CharacterClass.WARRIOR]
        with pytest.raises(ValueError):
            Attributes.from_base_and_build(base, (2, 2, 2, 1, 1))

    def test_invalid_sum_too_high(self):
        base = BASE_ATTRIBUTES[CharacterClass.WARRIOR]
        with pytest.raises(ValueError):
            Attributes.from_base_and_build(base, (3, 3, 3, 2, 1))

    def test_invalid_single_over_cap(self):
        base = BASE_ATTRIBUTES[CharacterClass.WARRIOR]
        with pytest.raises(ValueError):
            Attributes.from_base_and_build(base, (6, 1, 1, 1, 1))

    def test_invalid_negative_value(self):
        base = BASE_ATTRIBUTES[CharacterClass.WARRIOR]
        with pytest.raises(ValueError):
            Attributes.from_base_and_build(base, (-1, 3, 3, 3, 2))

    def test_build_modifier_result(self):
        base = BASE_ATTRIBUTES[CharacterClass.WARRIOR]
        result = Attributes.from_base_and_build(base, (5, 0, 0, 0, 5))
        assert result.modifier("str") == 8
        assert result.modifier("wis") == 4


class TestHP:
    def test_warrior_no_build(self):
        attrs = BASE_ATTRIBUTES[CharacterClass.WARRIOR]
        c = Character("w1", CharacterClass.WARRIOR, attrs)
        assert c.max_hp == 60

    def test_mage_no_build(self):
        attrs = BASE_ATTRIBUTES[CharacterClass.MAGE]
        c = Character("m1", CharacterClass.MAGE, attrs)
        assert c.max_hp == 25

    def test_cleric_no_build(self):
        attrs = BASE_ATTRIBUTES[CharacterClass.CLERIC]
        c = Character("c1", CharacterClass.CLERIC, attrs)
        assert c.max_hp == 50

    def test_archer_no_build(self):
        attrs = BASE_ATTRIBUTES[CharacterClass.ARCHER]
        c = Character("a1", CharacterClass.ARCHER, attrs)
        assert c.max_hp == 30

    def test_assassin_no_build(self):
        attrs = BASE_ATTRIBUTES[CharacterClass.ASSASSIN]
        c = Character("s1", CharacterClass.ASSASSIN, attrs)
        assert c.max_hp == 25

    def test_warrior_max_con_build(self):
        base = BASE_ATTRIBUTES[CharacterClass.WARRIOR]
        attrs = Attributes.from_base_and_build(base, (0, 0, 5, 5, 0))
        c = Character("w2", CharacterClass.WARRIOR, attrs)
        assert c.max_hp == 85

    def test_mage_max_con_build(self):
        base = BASE_ATTRIBUTES[CharacterClass.MAGE]
        attrs = Attributes.from_base_and_build(base, (0, 0, 5, 5, 0))
        c = Character("m2", CharacterClass.MAGE, attrs)
        assert c.max_hp == 50

    def test_current_hp_equals_max_hp(self):
        attrs = BASE_ATTRIBUTES[CharacterClass.WARRIOR]
        c = Character("w1", CharacterClass.WARRIOR, attrs)
        assert c.current_hp == c.max_hp


class TestCharacter:
    def test_entity_id(self):
        attrs = BASE_ATTRIBUTES[CharacterClass.ARCHER]
        c = Character("archer_1", CharacterClass.ARCHER, attrs)
        assert c.entity_id == "archer_1"

    def test_character_class(self):
        attrs = BASE_ATTRIBUTES[CharacterClass.ASSASSIN]
        c = Character("assassin_1", CharacterClass.ASSASSIN, attrs)
        assert c.character_class == CharacterClass.ASSASSIN

    def test_attributes_accessible(self):
        attrs = BASE_ATTRIBUTES[CharacterClass.CLERIC]
        c = Character("cleric_1", CharacterClass.CLERIC, attrs)
        assert c.attributes == attrs
        assert c.attributes.wis == 8
