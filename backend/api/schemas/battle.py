from pydantic import BaseModel

from backend.api.schemas.builds import AbilityOut


class CharacterRequest(BaseModel):
    class_id: str
    attribute_points: list[int]
    ability_ids: list[str]


class BattleStartRequest(BaseModel):
    difficulty: str
    team: list[CharacterRequest]


class PositionOut(BaseModel):
    x: int
    y: int


class CharacterOut(BaseModel):
    entity_id: str
    team: str
    class_id: str
    attributes: dict[str, int]
    current_hp: int
    max_hp: int
    position: PositionOut
    abilities: list[AbilityOut]


class MapObjectOut(BaseModel):
    entity_id: str
    object_type: str
    position: PositionOut
    hp: int | None
    max_hp: int | None
    blocks_movement: bool
    blocks_los: bool


class InitialBattleState(BaseModel):
    grid_size: dict[str, int]
    map_objects: list[MapObjectOut]
    characters: list[CharacterOut]
    turn_order: list[str]
    current_character: str


class BattleStartResponse(BaseModel):
    session_id: str
    initial_state: InitialBattleState
