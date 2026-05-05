from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from engine.models.character import CharacterClass
from engine.models.effect import EffectType


class AbilityTarget(Enum):
    SINGLE_ENEMY = "single_enemy"
    SINGLE_ALLY = "single_ally"
    SELF = "self"
    AOE = "aoe"
    ADJACENT = "adjacent"
    CHAIN = "chain"


@dataclass(frozen=True)
class BuffDef:
    tag: str
    effect_type: EffectType
    value: float = 0.0
    duration: int = 0
    target: str = "enemy"
    radius: int = 0
    scaling_attr: str = ""
    scaling_factor: float = 0.0


@dataclass(frozen=True)
class Ability:
    id: str
    name: str
    pa_cost: int
    cooldown: int
    classes: tuple[CharacterClass, ...]
    target: AbilityTarget

    min_range: int = 0
    max_range: int = 1
    aoe_radius: int = 0
    friendly_fire: bool = False

    damage_base: int = 0
    damage_scaling: float = 0.0
    damage_attr: str = ""
    damage_type: str = ""

    heal_base: int = 0
    heal_scaling: float = 0.0
    heal_attr: str = ""

    self_heal_base: int = 0
    self_heal_scaling: float = 0.0
    self_heal_attr: str = ""

    effects: tuple[BuffDef, ...] = ()

    elemental_tag: str = ""
    crit_bonus: float = 0.0
    ignores_block_pct: float = 0.0
    execute_threshold: float = 0.0
    execute_bonus: float = 0.0
    debuff_bonus: float = 0.0
    lifesteal_pct: float = 0.0
    chain_targets: int = 0
    chain_damage_pct: float = 0.0
    hit_count: int = 1
    prevents_opportunity_attack: bool = False

    movement_type: str = ""
    movement_distance: int = 0

    shield_absorb_base: int = 0
    shield_absorb_scaling: float = 0.0
    shield_absorb_attr: str = ""
    shield_block_next: bool = False
    shield_duration: int = 0

    delayed: bool = False
    remove_all_negative: bool = False


# ---------------------------------------------------------------------------
# Basic Attacks (design.md 2.5)
# All: PA=2, CD=0, base=6, scaling=1.0
# ---------------------------------------------------------------------------

_W = CharacterClass.WARRIOR
_M = CharacterClass.MAGE
_C = CharacterClass.CLERIC
_A = CharacterClass.ARCHER
_S = CharacterClass.ASSASSIN

BASIC_ATTACKS: dict[CharacterClass, Ability] = {
    _W: Ability(
        id="basic_attack_warrior",
        name="Basic Attack",
        pa_cost=2,
        cooldown=0,
        classes=(_W,),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=1,
        damage_base=6,
        damage_scaling=1.0,
        damage_attr="str",
        damage_type="physical",
    ),
    _M: Ability(
        id="basic_attack_mage",
        name="Basic Attack",
        pa_cost=2,
        cooldown=0,
        classes=(_M,),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=5,
        damage_base=6,
        damage_scaling=1.0,
        damage_attr="int_",
        damage_type="magical",
    ),
    _C: Ability(
        id="basic_attack_cleric",
        name="Basic Attack",
        pa_cost=2,
        cooldown=0,
        classes=(_C,),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=1,
        damage_base=6,
        damage_scaling=1.0,
        damage_attr="str",
        damage_type="physical",
    ),
    _A: Ability(
        id="basic_attack_archer",
        name="Basic Attack",
        pa_cost=2,
        cooldown=0,
        classes=(_A,),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=5,
        damage_base=6,
        damage_scaling=1.0,
        damage_attr="dex",
        damage_type="physical",
    ),
    _S: Ability(
        id="basic_attack_assassin",
        name="Basic Attack",
        pa_cost=2,
        cooldown=0,
        classes=(_S,),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=1,
        damage_base=6,
        damage_scaling=1.0,
        damage_attr="dex",
        damage_type="physical",
    ),
}

# ---------------------------------------------------------------------------
# 47 Abilities (design.md 2.7)
# ---------------------------------------------------------------------------

ABILITIES: dict[str, Ability] = {
    # === Shared (8) ===
    "investida": Ability(
        id="investida",
        name="Investida",
        pa_cost=2,
        cooldown=3,
        classes=(_W, _S),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=4,
        damage_base=10,
        damage_scaling=1.2,
        damage_attr="str",
        damage_type="physical",
        movement_type="charge",
        movement_distance=4,
    ),
    "provocacao": Ability(
        id="provocacao",
        name="Provocacao",
        pa_cost=1,
        cooldown=3,
        classes=(_W, _C),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=1,
        effects=(
            BuffDef(
                tag="taunt", effect_type=EffectType.CONTROL, duration=2, target="enemy"
            ),
        ),
    ),
    "corte_profundo": Ability(
        id="corte_profundo",
        name="Corte Profundo",
        pa_cost=2,
        cooldown=3,
        classes=(_W, _S),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=1,
        damage_base=6,
        damage_scaling=0.8,
        damage_attr="str",
        damage_type="physical",
        effects=(
            BuffDef(
                tag="bleed",
                effect_type=EffectType.DOT,
                value=4.0,
                duration=3,
                target="enemy",
            ),
        ),
    ),
    "escudo_inabalavel": Ability(
        id="escudo_inabalavel",
        name="Escudo Inabalavel",
        pa_cost=1,
        cooldown=4,
        classes=(_W, _C),
        target=AbilityTarget.SELF,
        shield_block_next=True,
        shield_duration=3,
    ),
    "chama_sagrada": Ability(
        id="chama_sagrada",
        name="Chama Sagrada",
        pa_cost=2,
        cooldown=3,
        classes=(_M, _C),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=5,
        damage_base=8,
        damage_scaling=1.0,
        damage_attr="int_",
        damage_type="magical",
        self_heal_base=2,
        self_heal_scaling=0.2,
        self_heal_attr="int_",
        elemental_tag="fire",
    ),
    "barreira_arcana": Ability(
        id="barreira_arcana",
        name="Barreira Arcana",
        pa_cost=1,
        cooldown=2,
        classes=(_M, _C),
        target=AbilityTarget.SINGLE_ALLY,
        max_range=5,
        shield_absorb_base=8,
        shield_absorb_scaling=1.5,
        shield_absorb_attr="int_",
        shield_duration=3,
    ),
    "tiro_certeiro": Ability(
        id="tiro_certeiro",
        name="Tiro Certeiro",
        pa_cost=2,
        cooldown=2,
        classes=(_A, _S),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=5,
        damage_base=8,
        damage_scaling=1.0,
        damage_attr="dex",
        damage_type="physical",
        crit_bonus=0.15,
    ),
    "recuar": Ability(
        id="recuar",
        name="Recuar",
        pa_cost=1,
        cooldown=2,
        classes=(_A, _S),
        target=AbilityTarget.SELF,
        movement_type="retreat",
        movement_distance=2,
        prevents_opportunity_attack=True,
    ),
    # === Guerreiro Exclusives (7) ===
    "impacto_brutal": Ability(
        id="impacto_brutal",
        name="Impacto Brutal",
        pa_cost=2,
        cooldown=2,
        classes=(_W,),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=1,
        damage_base=10,
        damage_scaling=1.2,
        damage_attr="str",
        damage_type="physical",
    ),
    "grito_de_guerra": Ability(
        id="grito_de_guerra",
        name="Grito de Guerra",
        pa_cost=1,
        cooldown=4,
        classes=(_W,),
        target=AbilityTarget.SELF,
        effects=(
            BuffDef(
                tag="damage_increase",
                effect_type=EffectType.BUFF,
                value=0.25,
                duration=2,
                target="area_allies",
                radius=2,
            ),
        ),
    ),
    "redemoinho_de_aco": Ability(
        id="redemoinho_de_aco",
        name="Redemoinho de Aco",
        pa_cost=3,
        cooldown=4,
        classes=(_W,),
        target=AbilityTarget.ADJACENT,
        damage_base=12,
        damage_scaling=1.0,
        damage_attr="str",
        damage_type="physical",
    ),
    "muralha_de_ferro": Ability(
        id="muralha_de_ferro",
        name="Muralha de Ferro",
        pa_cost=1,
        cooldown=3,
        classes=(_W,),
        target=AbilityTarget.SELF,
        effects=(
            BuffDef(
                tag="damage_reduction",
                effect_type=EffectType.BUFF,
                value=0.30,
                duration=2,
                target="self",
            ),
        ),
    ),
    "furia_implacavel": Ability(
        id="furia_implacavel",
        name="Furia Implacavel",
        pa_cost=1,
        cooldown=4,
        classes=(_W,),
        target=AbilityTarget.SELF,
        effects=(
            BuffDef(
                tag="damage_increase",
                effect_type=EffectType.BUFF,
                value=0.35,
                duration=2,
                target="self",
            ),
            BuffDef(
                tag="damage_taken_increase",
                effect_type=EffectType.DEBUFF,
                value=0.20,
                duration=2,
                target="self",
            ),
        ),
    ),
    "sentenca_do_carrasco": Ability(
        id="sentenca_do_carrasco",
        name="Sentenca do Carrasco",
        pa_cost=3,
        cooldown=5,
        classes=(_W,),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=1,
        damage_base=14,
        damage_scaling=1.5,
        damage_attr="str",
        damage_type="physical",
        execute_threshold=0.30,
        execute_bonus=0.50,
    ),
    "bastiao": Ability(
        id="bastiao",
        name="Bastiao",
        pa_cost=1,
        cooldown=4,
        classes=(_W,),
        target=AbilityTarget.SELF,
        effects=(
            BuffDef(
                tag="damage_reduction",
                effect_type=EffectType.BUFF,
                value=0.25,
                duration=2,
                target="area_allies",
                radius=1,
            ),
            BuffDef(
                tag="damage_taken_increase",
                effect_type=EffectType.DEBUFF,
                value=0.20,
                duration=2,
                target="self",
            ),
        ),
    ),
    # === Mago Exclusives (9) ===
    "estilhaco_arcano": Ability(
        id="estilhaco_arcano",
        name="Estilhaco Arcano",
        pa_cost=2,
        cooldown=1,
        classes=(_M,),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=5,
        damage_base=8,
        damage_scaling=1.0,
        damage_attr="int_",
        damage_type="magical",
    ),
    "nova_flamejante": Ability(
        id="nova_flamejante",
        name="Nova Flamejante",
        pa_cost=3,
        cooldown=4,
        classes=(_M,),
        target=AbilityTarget.AOE,
        max_range=5,
        damage_base=14,
        damage_scaling=1.2,
        damage_attr="int_",
        damage_type="magical",
        aoe_radius=1,
        friendly_fire=True,
        elemental_tag="fire",
    ),
    "toque_do_inverno": Ability(
        id="toque_do_inverno",
        name="Toque do Inverno",
        pa_cost=2,
        cooldown=3,
        classes=(_M,),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=5,
        damage_base=8,
        damage_scaling=0.8,
        damage_attr="int_",
        damage_type="magical",
        elemental_tag="ice",
        effects=(
            BuffDef(
                tag="slow", effect_type=EffectType.DEBUFF, duration=2, target="enemy"
            ),
            BuffDef(
                tag="wet", effect_type=EffectType.DEBUFF, duration=2, target="enemy"
            ),
        ),
    ),
    "arco_voltaico": Ability(
        id="arco_voltaico",
        name="Arco Voltaico",
        pa_cost=3,
        cooldown=4,
        classes=(_M,),
        target=AbilityTarget.CHAIN,
        max_range=5,
        damage_base=12,
        damage_scaling=1.0,
        damage_attr="int_",
        damage_type="magical",
        chain_targets=2,
        chain_damage_pct=0.70,
        elemental_tag="electric",
    ),
    "vacuo_arcano": Ability(
        id="vacuo_arcano",
        name="Vacuo Arcano",
        pa_cost=2,
        cooldown=5,
        classes=(_M,),
        target=AbilityTarget.AOE,
        max_range=5,
        aoe_radius=1,
        effects=(
            BuffDef(
                tag="silence",
                effect_type=EffectType.CONTROL,
                duration=1,
                target="enemy",
            ),
        ),
    ),
    "transposicao": Ability(
        id="transposicao",
        name="Transposicao",
        pa_cost=1,
        cooldown=3,
        classes=(_M,),
        target=AbilityTarget.SELF,
        movement_type="teleport",
        movement_distance=4,
        prevents_opportunity_attack=True,
    ),
    "sifao_vital": Ability(
        id="sifao_vital",
        name="Sifao Vital",
        pa_cost=2,
        cooldown=3,
        classes=(_M,),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=5,
        damage_base=8,
        damage_scaling=1.0,
        damage_attr="int_",
        damage_type="magical",
        lifesteal_pct=0.50,
    ),
    "meteoro": Ability(
        id="meteoro",
        name="Meteoro",
        pa_cost=3,
        cooldown=5,
        classes=(_M,),
        target=AbilityTarget.AOE,
        max_range=5,
        damage_base=20,
        damage_scaling=1.5,
        damage_attr="int_",
        damage_type="magical",
        aoe_radius=1,
        friendly_fire=True,
        delayed=True,
    ),
    "canalizacao_arcana": Ability(
        id="canalizacao_arcana",
        name="Canalizacao Arcana",
        pa_cost=1,
        cooldown=4,
        classes=(_M,),
        target=AbilityTarget.SELF,
        effects=(
            BuffDef(
                tag="magic_damage_increase",
                effect_type=EffectType.BUFF,
                value=0.40,
                duration=2,
                target="self",
            ),
            BuffDef(
                tag="immobilize",
                effect_type=EffectType.DEBUFF,
                duration=2,
                target="self",
            ),
        ),
    ),
    # === Clerigo Exclusives (7) ===
    "toque_da_aurora": Ability(
        id="toque_da_aurora",
        name="Toque da Aurora",
        pa_cost=2,
        cooldown=2,
        classes=(_C,),
        target=AbilityTarget.SINGLE_ALLY,
        max_range=3,
        heal_base=10,
        heal_scaling=1.5,
        heal_attr="wis",
    ),
    "egide_sagrada": Ability(
        id="egide_sagrada",
        name="Egide Sagrada",
        pa_cost=1,
        cooldown=3,
        classes=(_C,),
        target=AbilityTarget.SINGLE_ALLY,
        max_range=5,
        effects=(
            BuffDef(
                tag="damage_reduction",
                effect_type=EffectType.BUFF,
                value=0.20,
                duration=2,
                target="ally",
            ),
        ),
    ),
    "expurgo": Ability(
        id="expurgo",
        name="Expurgo",
        pa_cost=1,
        cooldown=3,
        classes=(_C,),
        target=AbilityTarget.SINGLE_ALLY,
        max_range=5,
        remove_all_negative=True,
    ),
    "consagracao": Ability(
        id="consagracao",
        name="Consagracao",
        pa_cost=2,
        cooldown=4,
        classes=(_C,),
        target=AbilityTarget.AOE,
        max_range=0,
        aoe_radius=2,
        effects=(
            BuffDef(
                tag="consecration",
                effect_type=EffectType.HOT,
                value=7.0,
                duration=3,
                target="area_allies",
                radius=2,
                scaling_attr="wis",
                scaling_factor=0.5,
            ),
        ),
    ),
    "retribuicao_divina": Ability(
        id="retribuicao_divina",
        name="Retribuicao Divina",
        pa_cost=1,
        cooldown=4,
        classes=(_C,),
        target=AbilityTarget.SELF,
        effects=(
            BuffDef(
                tag="reflect",
                effect_type=EffectType.BUFF,
                value=0.30,
                duration=2,
                target="self",
            ),
        ),
    ),
    "julgamento_divino": Ability(
        id="julgamento_divino",
        name="Julgamento Divino",
        pa_cost=3,
        cooldown=4,
        classes=(_C,),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=5,
        damage_base=14,
        damage_scaling=1.5,
        damage_attr="wis",
        damage_type="magical",
    ),
    "voto_de_sacrificio": Ability(
        id="voto_de_sacrificio",
        name="Voto de Sacrificio",
        pa_cost=1,
        cooldown=4,
        classes=(_C,),
        target=AbilityTarget.SELF,
        effects=(
            BuffDef(
                tag="redirect",
                effect_type=EffectType.BUFF,
                value=0.40,
                duration=2,
                target="area_allies",
                radius=2,
            ),
        ),
    ),
    # === Arqueiro Exclusives (9) ===
    "tiro_perfurante": Ability(
        id="tiro_perfurante",
        name="Tiro Perfurante",
        pa_cost=2,
        cooldown=2,
        classes=(_A,),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=5,
        damage_base=8,
        damage_scaling=1.0,
        damage_attr="dex",
        damage_type="physical",
        ignores_block_pct=0.50,
    ),
    "chuva_de_flechas": Ability(
        id="chuva_de_flechas",
        name="Chuva de Flechas",
        pa_cost=3,
        cooldown=4,
        classes=(_A,),
        target=AbilityTarget.AOE,
        max_range=5,
        damage_base=10,
        damage_scaling=0.8,
        damage_attr="dex",
        damage_type="physical",
        aoe_radius=2,
        friendly_fire=True,
    ),
    "ponta_envenenada": Ability(
        id="ponta_envenenada",
        name="Ponta Envenenada",
        pa_cost=2,
        cooldown=3,
        classes=(_A,),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=5,
        damage_base=6,
        damage_scaling=0.8,
        damage_attr="dex",
        damage_type="physical",
        elemental_tag="poison",
        effects=(
            BuffDef(
                tag="poison",
                effect_type=EffectType.DOT,
                value=4.0,
                duration=3,
                target="enemy",
            ),
        ),
    ),
    "flecha_glacial": Ability(
        id="flecha_glacial",
        name="Flecha Glacial",
        pa_cost=2,
        cooldown=3,
        classes=(_A,),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=5,
        damage_base=7,
        damage_scaling=0.8,
        damage_attr="dex",
        damage_type="physical",
        elemental_tag="ice",
        effects=(
            BuffDef(
                tag="immobilize",
                effect_type=EffectType.CONTROL,
                duration=1,
                target="enemy",
            ),
            BuffDef(
                tag="wet", effect_type=EffectType.DEBUFF, duration=2, target="enemy"
            ),
        ),
    ),
    "olho_do_predador": Ability(
        id="olho_do_predador",
        name="Olho do Predador",
        pa_cost=1,
        cooldown=4,
        classes=(_A,),
        target=AbilityTarget.SELF,
        effects=(
            BuffDef(
                tag="next_attack_bonus",
                effect_type=EffectType.BUFF,
                value=1.00,
                duration=2,
                target="self",
            ),
        ),
    ),
    "rajada_dupla": Ability(
        id="rajada_dupla",
        name="Rajada Dupla",
        pa_cost=3,
        cooldown=3,
        classes=(_A,),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=5,
        damage_base=7,
        damage_scaling=0.8,
        damage_attr="dex",
        damage_type="physical",
        hit_count=2,
    ),
    "armadilha_espinhosa": Ability(
        id="armadilha_espinhosa",
        name="Armadilha Espinhosa",
        pa_cost=1,
        cooldown=3,
        classes=(_A,),
        target=AbilityTarget.AOE,
        max_range=5,
        damage_base=6,
        damage_scaling=0.5,
        damage_attr="dex",
        damage_type="physical",
        effects=(
            BuffDef(
                tag="slow", effect_type=EffectType.DEBUFF, duration=2, target="enemy"
            ),
        ),
    ),
    "alcance_supremo": Ability(
        id="alcance_supremo",
        name="Alcance Supremo",
        pa_cost=1,
        cooldown=4,
        classes=(_A,),
        target=AbilityTarget.SELF,
        effects=(
            BuffDef(
                tag="range_bonus",
                effect_type=EffectType.BUFF,
                value=2.0,
                duration=2,
                target="self",
            ),
        ),
    ),
    "concentracao_absoluta": Ability(
        id="concentracao_absoluta",
        name="Concentracao Absoluta",
        pa_cost=1,
        cooldown=4,
        classes=(_A,),
        target=AbilityTarget.SELF,
        effects=(
            BuffDef(
                tag="crit_bonus",
                effect_type=EffectType.BUFF,
                value=0.15,
                duration=2,
                target="self",
            ),
            BuffDef(
                tag="ranged_damage_increase",
                effect_type=EffectType.BUFF,
                value=0.30,
                duration=2,
                target="self",
            ),
            BuffDef(
                tag="immobilize",
                effect_type=EffectType.DEBUFF,
                duration=2,
                target="self",
            ),
        ),
    ),
    # === Assassino Exclusives (7) ===
    "lamina_oculta": Ability(
        id="lamina_oculta",
        name="Lamina Oculta",
        pa_cost=1,
        cooldown=1,
        classes=(_S,),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=1,
        damage_base=7,
        damage_scaling=1.0,
        damage_attr="dex",
        damage_type="physical",
        debuff_bonus=0.50,
    ),
    "passo_sombrio": Ability(
        id="passo_sombrio",
        name="Passo Sombrio",
        pa_cost=1,
        cooldown=3,
        classes=(_S,),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=4,
        movement_type="teleport",
        movement_distance=4,
        prevents_opportunity_attack=True,
    ),
    "danca_das_laminas": Ability(
        id="danca_das_laminas",
        name="Danca das Laminas",
        pa_cost=3,
        cooldown=3,
        classes=(_S,),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=1,
        damage_base=7,
        damage_scaling=1.0,
        damage_attr="dex",
        damage_type="physical",
        hit_count=2,
    ),
    "veu_das_sombras": Ability(
        id="veu_das_sombras",
        name="Veu das Sombras",
        pa_cost=2,
        cooldown=5,
        classes=(_S,),
        target=AbilityTarget.SELF,
        effects=(
            BuffDef(
                tag="untargetable",
                effect_type=EffectType.BUFF,
                duration=1,
                target="self",
            ),
            BuffDef(
                tag="next_attack_bonus",
                effect_type=EffectType.BUFF,
                value=0.50,
                duration=2,
                target="self",
            ),
        ),
    ),
    "toque_peconhento": Ability(
        id="toque_peconhento",
        name="Toque Peconhento",
        pa_cost=1,
        cooldown=4,
        classes=(_S,),
        target=AbilityTarget.SELF,
        elemental_tag="poison",
        effects=(
            BuffDef(
                tag="poison_attacks",
                effect_type=EffectType.BUFF,
                value=3.0,
                duration=3,
                target="self",
            ),
        ),
    ),
    "marca_da_morte": Ability(
        id="marca_da_morte",
        name="Marca da Morte",
        pa_cost=3,
        cooldown=5,
        classes=(_S,),
        target=AbilityTarget.SINGLE_ENEMY,
        max_range=1,
        damage_base=16,
        damage_scaling=1.5,
        damage_attr="dex",
        damage_type="physical",
        execute_threshold=0.25,
        execute_bonus=0.50,
    ),
    "sede_de_sangue": Ability(
        id="sede_de_sangue",
        name="Sede de Sangue",
        pa_cost=1,
        cooldown=4,
        classes=(_S,),
        target=AbilityTarget.SELF,
        effects=(
            BuffDef(
                tag="damage_increase",
                effect_type=EffectType.BUFF,
                value=0.35,
                duration=2,
                target="self",
            ),
            BuffDef(
                tag="evasion_nullify",
                effect_type=EffectType.DEBUFF,
                duration=2,
                target="self",
            ),
        ),
    ),
}
