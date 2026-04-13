from __future__ import annotations

from dataclasses import dataclass

from engine.models.effect import Effect, EffectType
from engine.systems.effect_manager import EffectManager

_NEGATIVE_TYPES = {EffectType.DEBUFF, EffectType.CONTROL, EffectType.DOT}


@dataclass(frozen=True)
class ComboResult:
    damage_modifier: float
    apply_freeze: bool = False
    freeze_duration: int = 0


_COMBO_TABLE: dict[str, ComboResult] = {
    "electric": ComboResult(damage_modifier=1.50),
    "fire": ComboResult(damage_modifier=0.70),
    "ice": ComboResult(damage_modifier=1.0, apply_freeze=True, freeze_duration=1),
}


def check_elemental_combo(
    effect_manager: EffectManager,
    target_entity_id: str,
    elemental_tag: str,
) -> ComboResult | None:
    if not elemental_tag or elemental_tag not in _COMBO_TABLE:
        return None

    if not effect_manager.has_effect(target_entity_id, "wet"):
        return None

    combo = _COMBO_TABLE[elemental_tag]
    effect_manager.remove_effects_by_tag(target_entity_id, "wet")

    if combo.apply_freeze:
        effect_manager.apply_effect(
            target_entity_id,
            Effect(
                tag="freeze",
                effect_type=EffectType.CONTROL,
                source_entity_id=target_entity_id,
                duration=combo.freeze_duration,
            ),
        )

    return combo


def has_negative_status(effect_manager: EffectManager, entity_id: str) -> bool:
    return any(
        e.effect_type in _NEGATIVE_TYPES for e in effect_manager.get_effects(entity_id)
    )
