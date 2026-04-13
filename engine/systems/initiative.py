from __future__ import annotations

import random as _random


def roll_initiative(dex_modifier: int, rng: _random.Random | None = None) -> int:
    if rng is None:
        roll = _random.randint(1, 20)
    else:
        roll = rng.randint(1, 20)
    return roll + dex_modifier


def determine_turn_order(
    participants: list[tuple[str, int, int]], rng: _random.Random | None = None
) -> list[str]:
    if rng is None:
        rng = _random.Random()

    rolls: list[tuple[str, int, int, float]] = []
    for entity_id, dex_modifier, dex_base in participants:
        initiative = roll_initiative(dex_modifier, rng=rng)
        tiebreaker = rng.random()
        rolls.append((entity_id, initiative, dex_base, tiebreaker))

    rolls.sort(key=lambda r: (r[1], r[2], r[3]), reverse=True)
    return [r[0] for r in rolls]
