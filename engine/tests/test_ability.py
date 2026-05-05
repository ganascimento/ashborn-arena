import pytest

from engine.models.ability import (
    ABILITIES,
    BASIC_ATTACKS,
    Ability,
    AbilityTarget,
    BuffDef,
)
from engine.models.character import CharacterClass
from engine.models.effect import EffectType
from engine.systems.damage import calculate_raw_damage


class TestAbilityTarget:
    def test_has_six_values(self):
        assert len(AbilityTarget) == 6

    def test_values(self):
        assert AbilityTarget.SINGLE_ENEMY.value == "single_enemy"
        assert AbilityTarget.SINGLE_ALLY.value == "single_ally"
        assert AbilityTarget.SELF.value == "self"
        assert AbilityTarget.AOE.value == "aoe"
        assert AbilityTarget.ADJACENT.value == "adjacent"
        assert AbilityTarget.CHAIN.value == "chain"


class TestBuffDef:
    def test_creation(self):
        b = BuffDef(
            tag="dr", effect_type=EffectType.BUFF, value=0.30, duration=2, target="self"
        )
        assert b.tag == "dr"
        assert b.effect_type == EffectType.BUFF
        assert b.value == pytest.approx(0.30)
        assert b.duration == 2
        assert b.target == "self"
        assert b.radius == 0


class TestAbilityDefaults:
    def test_minimal_creation(self):
        a = Ability(
            id="test",
            name="Test",
            pa_cost=1,
            cooldown=0,
            classes=(CharacterClass.WARRIOR,),
            target=AbilityTarget.SELF,
        )
        assert a.damage_base == 0
        assert a.damage_scaling == 0.0
        assert a.effects == ()
        assert a.hit_count == 1
        assert a.friendly_fire is False


class TestCalculateRawDamageFloatScaling:
    def test_scaling_1_2(self):
        assert calculate_raw_damage(10, 3, 1.2) == 14

    def test_scaling_1_5_round_half_up(self):
        assert calculate_raw_damage(14, 3, 1.5) == 19

    def test_scaling_int_retrocompat(self):
        assert calculate_raw_damage(10, 3, 2) == 16

    def test_negative_modifier_scaling_1_2(self):
        assert calculate_raw_damage(10, -3, 1.2) == 6

    def test_scaling_0_8(self):
        assert calculate_raw_damage(8, 4, 0.8) == 11

    def test_scaling_1_0(self):
        assert calculate_raw_damage(6, 3, 1.0) == 9

    def test_scaling_0_5(self):
        assert calculate_raw_damage(5, 3, 0.5) == 7

    def test_zero_modifier(self):
        assert calculate_raw_damage(10, 0, 1.2) == 10


class TestCatalogCompleteness:
    def test_basic_attacks_count(self):
        assert len(BASIC_ATTACKS) == 5

    def test_basic_attacks_all_classes(self):
        for cls in CharacterClass:
            assert cls in BASIC_ATTACKS

    def test_abilities_count(self):
        assert len(ABILITIES) == 47

    def test_each_class_has_11_abilities(self):
        for cls in CharacterClass:
            count = sum(1 for a in ABILITIES.values() if cls in a.classes)
            assert count == 11, f"{cls.name} has {count} abilities, expected 11"


class TestBasicAttacks:
    @pytest.fixture(params=list(CharacterClass))
    def basic(self, request):
        return BASIC_ATTACKS[request.param], request.param

    def test_pa_cost(self, basic):
        a, _ = basic
        assert a.pa_cost == 2

    def test_cooldown(self, basic):
        a, _ = basic
        assert a.cooldown == 0

    def test_damage_base(self, basic):
        a, _ = basic
        assert a.damage_base == 6

    def test_damage_scaling(self, basic):
        a, _ = basic
        assert a.damage_scaling == pytest.approx(1.0)

    def test_warrior_basic(self):
        a = BASIC_ATTACKS[CharacterClass.WARRIOR]
        assert a.damage_attr == "str"
        assert a.damage_type == "physical"
        assert a.max_range == 1

    def test_mage_basic(self):
        a = BASIC_ATTACKS[CharacterClass.MAGE]
        assert a.damage_attr == "int_"
        assert a.damage_type == "magical"
        assert a.max_range == 5

    def test_cleric_basic(self):
        a = BASIC_ATTACKS[CharacterClass.CLERIC]
        assert a.damage_attr == "str"
        assert a.damage_type == "physical"
        assert a.max_range == 1

    def test_archer_basic(self):
        a = BASIC_ATTACKS[CharacterClass.ARCHER]
        assert a.damage_attr == "dex"
        assert a.damage_type == "physical"
        assert a.max_range == 5

    def test_assassin_basic(self):
        a = BASIC_ATTACKS[CharacterClass.ASSASSIN]
        assert a.damage_attr == "dex"
        assert a.damage_type == "physical"
        assert a.max_range == 1


class TestSharedInvestida:
    @pytest.fixture
    def ability(self):
        return ABILITIES["investida"]

    def test_classes(self, ability):
        assert set(ability.classes) == {CharacterClass.WARRIOR, CharacterClass.ASSASSIN}

    def test_cost(self, ability):
        assert ability.pa_cost == 2
        assert ability.cooldown == 3

    def test_damage(self, ability):
        assert ability.damage_base == 10
        assert ability.damage_scaling == pytest.approx(1.2)
        assert ability.damage_attr == "str"
        assert ability.damage_type == "physical"

    def test_movement(self, ability):
        assert ability.movement_type == "charge"
        assert ability.movement_distance == 4


class TestSharedProvocacao:
    @pytest.fixture
    def ability(self):
        return ABILITIES["provocacao"]

    def test_classes(self, ability):
        assert set(ability.classes) == {CharacterClass.WARRIOR, CharacterClass.CLERIC}

    def test_cost(self, ability):
        assert ability.pa_cost == 1
        assert ability.cooldown == 3

    def test_no_damage(self, ability):
        assert ability.damage_base == 0

    def test_taunt_effect(self, ability):
        taunt = [e for e in ability.effects if e.tag == "taunt"]
        assert len(taunt) == 1
        assert taunt[0].effect_type == EffectType.CONTROL
        assert taunt[0].duration == 2


class TestSharedCorteProfundo:
    @pytest.fixture
    def ability(self):
        return ABILITIES["corte_profundo"]

    def test_classes(self, ability):
        assert set(ability.classes) == {CharacterClass.WARRIOR, CharacterClass.ASSASSIN}

    def test_cost(self, ability):
        assert ability.pa_cost == 2
        assert ability.cooldown == 3

    def test_damage(self, ability):
        assert ability.damage_base == 6
        assert ability.damage_scaling == pytest.approx(0.8)
        assert ability.damage_attr == "str"
        assert ability.damage_type == "physical"

    def test_bleed_dot(self, ability):
        bleed = [e for e in ability.effects if e.tag == "bleed"]
        assert len(bleed) == 1
        assert bleed[0].effect_type == EffectType.DOT
        assert bleed[0].value == pytest.approx(4.0)
        assert bleed[0].duration == 3


class TestSharedEscudoInabalavel:
    @pytest.fixture
    def ability(self):
        return ABILITIES["escudo_inabalavel"]

    def test_classes(self, ability):
        assert set(ability.classes) == {CharacterClass.WARRIOR, CharacterClass.CLERIC}

    def test_cost(self, ability):
        assert ability.pa_cost == 1
        assert ability.cooldown == 4

    def test_shield(self, ability):
        assert ability.shield_block_next is True
        assert ability.shield_duration == 3


class TestSharedChamaSagrada:
    @pytest.fixture
    def ability(self):
        return ABILITIES["chama_sagrada"]

    def test_classes(self, ability):
        assert set(ability.classes) == {CharacterClass.MAGE, CharacterClass.CLERIC}

    def test_cost(self, ability):
        assert ability.pa_cost == 2
        assert ability.cooldown == 3

    def test_damage(self, ability):
        assert ability.damage_base == 8
        assert ability.damage_scaling == pytest.approx(1.0)
        assert ability.damage_type == "magical"

    def test_self_heal(self, ability):
        assert ability.self_heal_base == 2
        assert ability.self_heal_scaling == pytest.approx(0.2)

    def test_elemental(self, ability):
        assert ability.elemental_tag == "fire"


class TestSharedBarreiraArcana:
    @pytest.fixture
    def ability(self):
        return ABILITIES["barreira_arcana"]

    def test_classes(self, ability):
        assert set(ability.classes) == {CharacterClass.MAGE, CharacterClass.CLERIC}

    def test_cost(self, ability):
        assert ability.pa_cost == 1
        assert ability.cooldown == 2

    def test_shield(self, ability):
        assert ability.shield_absorb_base == 8
        assert ability.shield_absorb_scaling == pytest.approx(1.5)
        assert ability.shield_duration == 3


class TestSharedTiroCerteiro:
    @pytest.fixture
    def ability(self):
        return ABILITIES["tiro_certeiro"]

    def test_classes(self, ability):
        assert set(ability.classes) == {CharacterClass.ARCHER, CharacterClass.ASSASSIN}

    def test_cost(self, ability):
        assert ability.pa_cost == 2
        assert ability.cooldown == 2

    def test_damage(self, ability):
        assert ability.damage_base == 8
        assert ability.damage_scaling == pytest.approx(1.0)
        assert ability.damage_attr == "dex"
        assert ability.damage_type == "physical"

    def test_crit_bonus(self, ability):
        assert ability.crit_bonus == pytest.approx(0.15)


class TestSharedRecuar:
    @pytest.fixture
    def ability(self):
        return ABILITIES["recuar"]

    def test_classes(self, ability):
        assert set(ability.classes) == {CharacterClass.ARCHER, CharacterClass.ASSASSIN}

    def test_cost(self, ability):
        assert ability.pa_cost == 1
        assert ability.cooldown == 2

    def test_movement(self, ability):
        assert ability.movement_type == "retreat"
        assert ability.movement_distance == 2
        assert ability.prevents_opportunity_attack is True


class TestGuerreiroExclusives:
    def test_impacto_brutal(self):
        a = ABILITIES["impacto_brutal"]
        assert CharacterClass.WARRIOR in a.classes
        assert a.pa_cost == 2
        assert a.cooldown == 2
        assert a.damage_base == 10
        assert a.damage_scaling == pytest.approx(1.2)
        assert a.damage_attr == "str"
        assert a.damage_type == "physical"

    def test_muralha_de_ferro(self):
        a = ABILITIES["muralha_de_ferro"]
        assert a.pa_cost == 1
        assert a.cooldown == 3
        dr = [e for e in a.effects if e.tag == "damage_reduction"]
        assert len(dr) == 1
        assert dr[0].effect_type == EffectType.BUFF
        assert dr[0].value == pytest.approx(0.30)
        assert dr[0].duration == 2
        assert dr[0].target == "self"

    def test_sentenca_do_carrasco(self):
        a = ABILITIES["sentenca_do_carrasco"]
        assert a.pa_cost == 3
        assert a.cooldown == 5
        assert a.damage_base == 14
        assert a.damage_scaling == pytest.approx(1.5)
        assert a.damage_attr == "str"
        assert a.damage_type == "physical"
        assert a.execute_threshold == pytest.approx(0.30)
        assert a.execute_bonus == pytest.approx(0.50)

    def test_redemoinho_de_aco(self):
        a = ABILITIES["redemoinho_de_aco"]
        assert a.pa_cost == 3
        assert a.cooldown == 4
        assert a.damage_base == 12
        assert a.damage_scaling == pytest.approx(1.0)
        assert a.damage_attr == "str"
        assert a.damage_type == "physical"
        assert a.target == AbilityTarget.ADJACENT

    def test_grito_de_guerra(self):
        a = ABILITIES["grito_de_guerra"]
        assert a.pa_cost == 1
        assert a.cooldown == 4
        buff = [e for e in a.effects if e.tag == "damage_increase"]
        assert len(buff) == 1
        assert buff[0].value == pytest.approx(0.25)
        assert buff[0].duration == 2

    def test_furia_implacavel(self):
        a = ABILITIES["furia_implacavel"]
        assert a.pa_cost == 1
        assert a.cooldown == 4
        assert len(a.effects) == 2
        buff = [e for e in a.effects if e.effect_type == EffectType.BUFF]
        debuff = [e for e in a.effects if e.effect_type == EffectType.DEBUFF]
        assert len(buff) == 1
        assert buff[0].value == pytest.approx(0.35)
        assert len(debuff) == 1
        assert debuff[0].value == pytest.approx(0.20)

    def test_bastiao(self):
        a = ABILITIES["bastiao"]
        assert a.pa_cost == 1
        assert a.cooldown == 4
        assert len(a.effects) >= 2


class TestMagoExclusives:
    def test_estilhaco_arcano(self):
        a = ABILITIES["estilhaco_arcano"]
        assert a.pa_cost == 2
        assert a.cooldown == 1
        assert a.damage_base == 8
        assert a.damage_scaling == pytest.approx(1.0)
        assert a.damage_attr == "int_"
        assert a.damage_type == "magical"

    def test_nova_flamejante(self):
        a = ABILITIES["nova_flamejante"]
        assert a.pa_cost == 3
        assert a.cooldown == 4
        assert a.damage_base == 14
        assert a.damage_scaling == pytest.approx(1.2)
        assert a.damage_type == "magical"
        assert a.aoe_radius == 1
        assert a.friendly_fire is True
        assert a.elemental_tag == "fire"

    def test_arco_voltaico(self):
        a = ABILITIES["arco_voltaico"]
        assert a.pa_cost == 3
        assert a.cooldown == 4
        assert a.damage_base == 12
        assert a.damage_scaling == pytest.approx(1.0)
        assert a.damage_type == "magical"
        assert a.chain_targets == 2
        assert a.chain_damage_pct == pytest.approx(0.70)
        assert a.elemental_tag == "electric"

    def test_meteoro(self):
        a = ABILITIES["meteoro"]
        assert a.pa_cost == 3
        assert a.cooldown == 5
        assert a.damage_base == 20
        assert a.damage_scaling == pytest.approx(1.5)
        assert a.damage_type == "magical"
        assert a.aoe_radius == 1
        assert a.delayed is True

    def test_sifao_vital(self):
        a = ABILITIES["sifao_vital"]
        assert a.damage_base == 8
        assert a.damage_scaling == pytest.approx(1.0)
        assert a.lifesteal_pct == pytest.approx(0.50)

    def test_transposicao(self):
        a = ABILITIES["transposicao"]
        assert a.pa_cost == 1
        assert a.cooldown == 3
        assert a.movement_type == "teleport"
        assert a.movement_distance == 4
        assert a.prevents_opportunity_attack is True

    def test_toque_do_inverno(self):
        a = ABILITIES["toque_do_inverno"]
        assert a.damage_base == 8
        assert a.damage_scaling == pytest.approx(0.8)
        assert a.elemental_tag == "ice"
        slow = [e for e in a.effects if e.tag == "slow"]
        assert len(slow) == 1
        assert slow[0].duration == 2
        wet = [e for e in a.effects if e.tag == "wet"]
        assert len(wet) == 1
        assert wet[0].duration == 2


class TestClerigoExclusives:
    def test_toque_da_aurora(self):
        a = ABILITIES["toque_da_aurora"]
        assert a.pa_cost == 2
        assert a.cooldown == 2
        assert a.max_range == 3
        assert a.heal_base == 10
        assert a.heal_scaling == pytest.approx(1.5)
        assert a.heal_attr == "wis"

    def test_consagracao(self):
        a = ABILITIES["consagracao"]
        assert a.pa_cost == 2
        assert a.cooldown == 4
        hot = [e for e in a.effects if e.effect_type == EffectType.HOT]
        assert len(hot) == 1
        assert hot[0].value == pytest.approx(7.0)
        assert hot[0].duration == 3
        assert a.aoe_radius == 2

    def test_expurgo(self):
        a = ABILITIES["expurgo"]
        assert a.pa_cost == 1
        assert a.cooldown == 3
        assert a.remove_all_negative is True

    def test_julgamento_divino(self):
        a = ABILITIES["julgamento_divino"]
        assert a.pa_cost == 3
        assert a.cooldown == 4
        assert a.damage_base == 14
        assert a.damage_scaling == pytest.approx(1.5)
        assert a.damage_attr == "wis"
        assert a.damage_type == "magical"

    def test_egide_sagrada(self):
        a = ABILITIES["egide_sagrada"]
        assert a.pa_cost == 1
        assert a.cooldown == 3
        dr = [e for e in a.effects if e.tag == "damage_reduction"]
        assert len(dr) == 1
        assert dr[0].value == pytest.approx(0.20)
        assert dr[0].duration == 2

    def test_retribuicao_divina(self):
        a = ABILITIES["retribuicao_divina"]
        assert a.pa_cost == 1
        assert a.cooldown == 4
        reflect = [e for e in a.effects if e.tag == "reflect"]
        assert len(reflect) == 1
        assert reflect[0].value == pytest.approx(0.30)
        assert reflect[0].duration == 2


class TestArqueiroExclusives:
    def test_tiro_perfurante(self):
        a = ABILITIES["tiro_perfurante"]
        assert a.pa_cost == 2
        assert a.cooldown == 2
        assert a.damage_base == 8
        assert a.damage_scaling == pytest.approx(1.0)
        assert a.damage_attr == "dex"
        assert a.damage_type == "physical"
        assert a.ignores_block_pct == pytest.approx(0.50)

    def test_chuva_de_flechas(self):
        a = ABILITIES["chuva_de_flechas"]
        assert a.pa_cost == 3
        assert a.cooldown == 4
        assert a.damage_base == 10
        assert a.damage_scaling == pytest.approx(0.8)
        assert a.aoe_radius == 2
        assert a.friendly_fire is True

    def test_ponta_envenenada(self):
        a = ABILITIES["ponta_envenenada"]
        assert a.pa_cost == 2
        assert a.cooldown == 3
        assert a.damage_base == 6
        assert a.damage_scaling == pytest.approx(0.8)
        assert a.elemental_tag == "poison"
        poison = [e for e in a.effects if e.tag == "poison"]
        assert len(poison) == 1
        assert poison[0].effect_type == EffectType.DOT
        assert poison[0].value == pytest.approx(4.0)
        assert poison[0].duration == 3

    def test_flecha_glacial(self):
        a = ABILITIES["flecha_glacial"]
        assert a.pa_cost == 2
        assert a.cooldown == 3
        assert a.damage_base == 7
        assert a.damage_scaling == pytest.approx(0.8)
        assert a.elemental_tag == "ice"
        immobilize = [e for e in a.effects if e.tag == "immobilize"]
        assert len(immobilize) == 1
        assert immobilize[0].duration == 1
        wet = [e for e in a.effects if e.tag == "wet"]
        assert len(wet) == 1
        assert wet[0].duration == 2

    def test_rajada_dupla(self):
        a = ABILITIES["rajada_dupla"]
        assert a.pa_cost == 3
        assert a.cooldown == 3
        assert a.damage_base == 7
        assert a.damage_scaling == pytest.approx(0.8)
        assert a.hit_count == 2


class TestAssassinoExclusives:
    def test_lamina_oculta(self):
        a = ABILITIES["lamina_oculta"]
        assert a.pa_cost == 1
        assert a.cooldown == 1
        assert a.damage_base == 7
        assert a.damage_scaling == pytest.approx(1.0)
        assert a.damage_attr == "dex"
        assert a.damage_type == "physical"
        assert a.debuff_bonus == pytest.approx(0.50)

    def test_passo_sombrio(self):
        a = ABILITIES["passo_sombrio"]
        assert a.pa_cost == 1
        assert a.cooldown == 3
        assert a.movement_type == "teleport"
        assert a.movement_distance == 4
        assert a.prevents_opportunity_attack is True

    def test_marca_da_morte(self):
        a = ABILITIES["marca_da_morte"]
        assert a.pa_cost == 3
        assert a.cooldown == 5
        assert a.damage_base == 16
        assert a.damage_scaling == pytest.approx(1.5)
        assert a.damage_attr == "dex"
        assert a.damage_type == "physical"
        assert a.execute_threshold == pytest.approx(0.25)

    def test_danca_das_laminas(self):
        a = ABILITIES["danca_das_laminas"]
        assert a.pa_cost == 3
        assert a.cooldown == 3
        assert a.damage_base == 7
        assert a.damage_scaling == pytest.approx(1.0)
        assert a.hit_count == 2

    def test_sede_de_sangue(self):
        a = ABILITIES["sede_de_sangue"]
        assert a.pa_cost == 1
        assert a.cooldown == 4
        buff = [e for e in a.effects if e.effect_type == EffectType.BUFF]
        assert len(buff) == 1
        assert buff[0].value == pytest.approx(0.35)
        debuff = [e for e in a.effects if e.effect_type == EffectType.DEBUFF]
        assert len(debuff) == 1


class TestRawDamageBalancing:
    def test_basic_attack_warrior(self):
        assert calculate_raw_damage(6, 3, 1.0) == 9

    def test_basic_attack_mage(self):
        assert calculate_raw_damage(6, 4, 1.0) == 10

    def test_impacto_brutal(self):
        assert calculate_raw_damage(10, 3, 1.2) == 14

    def test_estilhaco_arcano(self):
        assert calculate_raw_damage(8, 4, 1.0) == 12

    def test_tiro_certeiro(self):
        assert calculate_raw_damage(8, 4, 1.0) == 12

    def test_lamina_oculta(self):
        assert calculate_raw_damage(7, 3, 1.0) == 10

    def test_sentenca_do_carrasco(self):
        assert calculate_raw_damage(14, 3, 1.5) == 19

    def test_meteoro(self):
        assert calculate_raw_damage(20, 4, 1.5) == 26

    def test_marca_da_morte(self):
        assert calculate_raw_damage(16, 3, 1.5) == 21

    def test_toque_da_aurora(self):
        assert calculate_raw_damage(10, 3, 1.5) == 15

    def test_consagracao_hot(self):
        assert calculate_raw_damage(5, 3, 0.5) == 7
