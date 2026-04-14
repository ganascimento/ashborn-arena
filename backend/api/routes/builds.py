from fastapi import APIRouter

from backend.api.schemas.builds import (
    BuildsDefaultsResponse,
    ClassInfo,
    DefaultBuild,
    get_class_abilities,
)
from engine.models.character import BASE_ATTRIBUTES, BASE_HP, CharacterClass
from engine.systems.battle import _DEFAULT_ABILITIES

router = APIRouter(prefix="/builds")

_DEFAULT_BUILDS: dict[CharacterClass, list[int]] = {
    CharacterClass.WARRIOR: [5, 2, 3, 0, 0],
    CharacterClass.MAGE: [0, 0, 2, 5, 3],
    CharacterClass.CLERIC: [0, 0, 5, 0, 5],
    CharacterClass.ARCHER: [2, 5, 3, 0, 0],
    CharacterClass.ASSASSIN: [3, 5, 2, 0, 0],
}


@router.get("/defaults", response_model=BuildsDefaultsResponse)
def get_defaults():
    classes = []
    default_builds = []

    for cls in CharacterClass:
        base = BASE_ATTRIBUTES[cls]
        classes.append(
            ClassInfo(
                class_id=cls.value,
                base_attributes={
                    "str": base.str,
                    "dex": base.dex,
                    "con": base.con,
                    "int_": base.int_,
                    "wis": base.wis,
                },
                hp_base=BASE_HP[cls],
                abilities=get_class_abilities(cls),
            )
        )
        default_builds.append(
            DefaultBuild(
                class_id=cls.value,
                attribute_points=_DEFAULT_BUILDS[cls],
                ability_ids=list(_DEFAULT_ABILITIES[cls]),
            )
        )

    return BuildsDefaultsResponse(classes=classes, default_builds=default_builds)
