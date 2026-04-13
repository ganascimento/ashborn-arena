from __future__ import annotations

from engine.models.effect import Effect, EffectType

_TICK_TYPES = {EffectType.DOT, EffectType.HOT}
_DURATION_TYPES = {
    EffectType.BUFF,
    EffectType.DEBUFF,
    EffectType.CONTROL,
    EffectType.SHIELD,
}
_NEGATIVE_TYPES = {EffectType.DEBUFF, EffectType.CONTROL}


class EffectManager:
    def __init__(self) -> None:
        self._effects: dict[str, list[Effect]] = {}

    def apply_effect(self, target_entity_id: str, effect: Effect) -> None:
        effects = self._effects.setdefault(target_entity_id, [])

        if effect.effect_type in _TICK_TYPES:
            for existing in effects:
                if (
                    existing.tag == effect.tag
                    and existing.effect_type == effect.effect_type
                    and existing.source_entity_id == effect.source_entity_id
                ):
                    existing.duration = effect.duration
                    existing.value = effect.value
                    return
        else:
            for existing in effects:
                if (
                    existing.tag == effect.tag
                    and existing.effect_type == effect.effect_type
                ):
                    existing.duration = effect.duration
                    existing.value = effect.value
                    existing.source_entity_id = effect.source_entity_id
                    return

        effects.append(effect)

    def get_effects(self, entity_id: str) -> list[Effect]:
        return list(self._effects.get(entity_id, []))

    def get_effects_by_type(
        self, entity_id: str, effect_type: EffectType
    ) -> list[Effect]:
        return [
            e for e in self._effects.get(entity_id, []) if e.effect_type == effect_type
        ]

    def has_effect(self, entity_id: str, tag: str) -> bool:
        return any(e.tag == tag for e in self._effects.get(entity_id, []))

    def get_effect(self, entity_id: str, tag: str) -> Effect | None:
        for e in self._effects.get(entity_id, []):
            if e.tag == tag:
                return e
        return None

    def remove_effects_by_tag(self, entity_id: str, tag: str) -> int:
        effects = self._effects.get(entity_id, [])
        before = len(effects)
        self._effects[entity_id] = [e for e in effects if e.tag != tag]
        return before - len(self._effects[entity_id])

    def remove_all_negative(self, entity_id: str) -> list[Effect]:
        effects = self._effects.get(entity_id, [])
        removed = [e for e in effects if e.effect_type in _NEGATIVE_TYPES]
        self._effects[entity_id] = [
            e for e in effects if e.effect_type not in _NEGATIVE_TYPES
        ]
        return removed

    def remove_entity(self, entity_id: str) -> None:
        self._effects.pop(entity_id, None)

    def process_turn_start(self, entity_id: str) -> list[Effect]:
        effects = self._effects.get(entity_id, [])
        expired: list[Effect] = []
        remaining: list[Effect] = []

        for e in effects:
            if e.effect_type in _DURATION_TYPES:
                e.duration -= 1
                if e.duration < 0:
                    expired.append(e)
                    continue
            remaining.append(e)

        self._effects[entity_id] = remaining
        return expired

    def process_turn_end(self, entity_id: str) -> list[Effect]:
        effects = self._effects.get(entity_id, [])
        ticked: list[Effect] = []
        remaining: list[Effect] = []

        for e in effects:
            if e.effect_type in _TICK_TYPES:
                ticked.append(e)
                e.duration -= 1
                if e.duration > 0:
                    remaining.append(e)
            else:
                remaining.append(e)

        self._effects[entity_id] = remaining
        return ticked
