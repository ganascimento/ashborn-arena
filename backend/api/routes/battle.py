import random

from fastapi import APIRouter, HTTPException

from backend.api.routes.builds import _DEFAULT_BUILDS
from backend.api.schemas.battle import (
    BattleStartRequest,
    BattleStartResponse,
    CharacterOut,
    InitialBattleState,
    MapObjectOut,
    PositionOut,
)
from backend.api.schemas.builds import ability_to_out
from backend.sessions import session_manager
from engine.models.ability import ABILITIES, BASIC_ATTACKS
from engine.models.character import CharacterClass
from engine.systems.battle import _DEFAULT_ABILITIES, BattleState

router = APIRouter(prefix="/battle")

_VALID_DIFFICULTIES = {"easy", "normal", "hard"}
_VALID_CLASSES = {cls.value for cls in CharacterClass}


def _validate_request(req: BattleStartRequest) -> None:
    if req.difficulty not in _VALID_DIFFICULTIES:
        raise HTTPException(422, f"Invalid difficulty: {req.difficulty}")

    if not (1 <= len(req.team) <= 3):
        raise HTTPException(422, f"Team must have 1-3 characters, got {len(req.team)}")

    seen_classes: set[str] = set()
    for char_req in req.team:
        if char_req.class_id not in _VALID_CLASSES:
            raise HTTPException(422, f"Invalid class: {char_req.class_id}")

        if char_req.class_id in seen_classes:
            raise HTTPException(422, f"Duplicate class: {char_req.class_id}")
        seen_classes.add(char_req.class_id)

        pts = char_req.attribute_points
        if len(pts) != 5:
            raise HTTPException(
                422, f"attribute_points must have 5 values, got {len(pts)}"
            )
        if any(v < 0 for v in pts):
            raise HTTPException(422, "attribute_points cannot be negative")
        if any(v > 5 for v in pts):
            raise HTTPException(422, "attribute_points per attribute cannot exceed 5")
        if sum(pts) != 10:
            raise HTTPException(422, f"attribute_points must sum to 10, got {sum(pts)}")

        aids = char_req.ability_ids
        if len(aids) != 5:
            raise HTTPException(
                422, f"Must select exactly 5 abilities, got {len(aids)}"
            )
        if len(set(aids)) != len(aids):
            raise HTTPException(422, "Duplicate ability_ids")

        cls_enum = CharacterClass(char_req.class_id)
        for aid in aids:
            if aid not in ABILITIES:
                raise HTTPException(422, f"Unknown ability: {aid}")
            if cls_enum not in ABILITIES[aid].classes:
                raise HTTPException(
                    422, f"Ability {aid} not available for {char_req.class_id}"
                )


def _generate_ai_team(
    player_size: int,
) -> list[tuple[CharacterClass, tuple[int, ...], list[str]]]:
    available = list(CharacterClass)
    random.shuffle(available)
    ai_team = []
    for cls in available[:player_size]:
        build = tuple(_DEFAULT_BUILDS[cls])
        abilities = list(_DEFAULT_ABILITIES[cls])
        ai_team.append((cls, build, abilities))
    return ai_team


@router.post("/start", response_model=BattleStartResponse, status_code=201)
def start_battle(req: BattleStartRequest):
    _validate_request(req)

    team_a_config = []
    team_a_abilities = []
    for char_req in req.team:
        cls = CharacterClass(char_req.class_id)
        build = tuple(char_req.attribute_points)
        team_a_config.append((cls, build))
        team_a_abilities.append(char_req.ability_ids)

    ai_team = _generate_ai_team(len(req.team))
    team_b_config = [(cls, build) for cls, build, _ in ai_team]
    team_b_abilities = [abilities for _, _, abilities in ai_team]

    battle = BattleState.from_config(
        team_a_config=team_a_config,
        team_b_config=team_b_config,
        team_a_abilities=team_a_abilities,
        team_b_abilities=team_b_abilities,
    )

    player_ids = battle.team_a_entities
    ai_ids = battle.team_b_entities

    session = session_manager.create(battle, req.difficulty, player_ids, ai_ids, req.auto_battle)

    characters_out = []
    for eid in battle.all_entities:
        char = battle._characters[eid]
        pos = battle._positions[eid]
        team_label = "player" if eid in player_ids else "ai"
        attrs = char.attributes
        basic = BASIC_ATTACKS[char.character_class]
        equipped = battle._equipped[eid]
        abilities_out = [ability_to_out(basic)] + [ability_to_out(a) for a in equipped]
        characters_out.append(
            CharacterOut(
                entity_id=eid,
                team=team_label,
                class_id=char.character_class.value,
                attributes={
                    "str": attrs.str,
                    "dex": attrs.dex,
                    "con": attrs.con,
                    "int_": attrs.int_,
                    "wis": attrs.wis,
                },
                current_hp=char.current_hp,
                max_hp=char.max_hp,
                position=PositionOut(x=pos.x, y=pos.y),
                abilities=abilities_out,
            )
        )

    map_objects_out = []
    for obj in battle._map_objects.values():
        if obj.is_destroyed:
            continue
        map_objects_out.append(
            MapObjectOut(
                entity_id=obj.entity_id,
                object_type=obj.object_type.value,
                position=PositionOut(x=obj.position.x, y=obj.position.y),
                hp=obj.current_hp,
                max_hp=obj.max_hp,
                blocks_movement=obj.blocks_movement,
                blocks_los=obj.blocks_los,
            )
        )

    initial_state = InitialBattleState(
        grid_size={"width": 10, "height": 8},
        map_objects=map_objects_out,
        characters=characters_out,
        turn_order=battle.turn_order,
        current_character=battle.current_agent,
    )

    return BattleStartResponse(
        session_id=session.session_id,
        initial_state=initial_state,
    )
