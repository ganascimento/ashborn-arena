from engine.models.position import Position


def _serialize_value(val):
    if isinstance(val, Position):
        return [val.x, val.y]
    if isinstance(val, dict):
        return {k: _serialize_value(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_serialize_value(item) for item in val]
    return val


def serialize_events(events: list[dict]) -> list[dict]:
    return [_serialize_value(e) for e in events]


def make_turn_start(character: str, pa: int, events: list[dict]) -> dict:
    return {
        "type": "turn_start",
        "character": character,
        "pa": pa,
        "events": serialize_events(events),
    }


def make_turn_end(character: str, next_character: str) -> dict:
    return {"type": "turn_end", "character": character, "next": next_character}


def make_action_result(
    character: str, action: str, events: list[dict], **extra
) -> dict:
    msg = {
        "type": "action_result",
        "character": character,
        "action": action,
        "events": serialize_events(events),
    }
    msg.update(extra)
    return msg


def make_ai_action(character: str, action: str, events: list[dict], **extra) -> dict:
    msg = {
        "type": "ai_action",
        "character": character,
        "action": action,
        "events": serialize_events(events),
    }
    msg.update(extra)
    return msg


def make_battle_end(result: str) -> dict:
    return {"type": "battle_end", "result": result}


def make_error(message: str) -> dict:
    return {"type": "error", "message": message}
