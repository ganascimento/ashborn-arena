from pydantic import BaseModel

from engine.models.ability import ABILITIES, Ability
from engine.models.character import CharacterClass


class AbilityOut(BaseModel):
    id: str
    name: str
    pa_cost: int
    cooldown: int
    max_range: int
    target: str
    damage_base: int
    damage_type: str
    heal_base: int
    elemental_tag: str


class ClassInfo(BaseModel):
    class_id: str
    base_attributes: dict[str, int]
    hp_base: int
    abilities: list[AbilityOut]


class DefaultBuild(BaseModel):
    class_id: str
    attribute_points: list[int]
    ability_ids: list[str]


class BuildsDefaultsResponse(BaseModel):
    classes: list[ClassInfo]
    default_builds: list[DefaultBuild]


def ability_to_out(ability: Ability) -> AbilityOut:
    return AbilityOut(
        id=ability.id,
        name=ability.name,
        pa_cost=ability.pa_cost,
        cooldown=ability.cooldown,
        max_range=ability.max_range,
        target=ability.target.value,
        damage_base=ability.damage_base,
        damage_type=ability.damage_type,
        heal_base=ability.heal_base,
        elemental_tag=ability.elemental_tag,
    )


def get_class_abilities(char_class: CharacterClass) -> list[AbilityOut]:
    return [
        ability_to_out(ability)
        for ability in ABILITIES.values()
        if char_class in ability.classes
    ]
