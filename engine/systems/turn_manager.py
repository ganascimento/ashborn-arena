from __future__ import annotations

PA_PER_TURN = 4


class TurnManager:
    def __init__(self, turn_order: list[str]) -> None:
        if not turn_order:
            raise ValueError("turn_order must not be empty")

        self._turn_order = list(turn_order)
        self._index = 0
        self._round = 1
        self._pa: dict[str, int] = {}
        self._cooldowns: dict[str, dict[int, int]] = {eid: {} for eid in turn_order}
        self._start_turn()

    @property
    def current_entity(self) -> str:
        return self._turn_order[self._index]

    @property
    def current_round(self) -> int:
        return self._round

    @property
    def turn_order(self) -> list[str]:
        return list(self._turn_order)

    def get_pa(self, entity_id: str) -> int:
        if entity_id != self.current_entity:
            return 0
        return self._pa.get(entity_id, 0)

    def spend_pa(self, entity_id: str, cost: int) -> None:
        if entity_id != self.current_entity:
            raise ValueError(f"Not {entity_id}'s turn")
        if cost <= 0:
            raise ValueError(f"Cost must be positive, got {cost}")
        current = self._pa[entity_id]
        if cost > current:
            raise ValueError(f"Not enough PA: need {cost}, have {current}")
        self._pa[entity_id] = current - cost

    def can_spend_pa(self, entity_id: str, cost: int) -> bool:
        if entity_id != self.current_entity:
            return False
        return self._pa.get(entity_id, 0) >= cost

    def use_ability(self, entity_id: str, ability_slot: int, cooldown: int) -> None:
        if entity_id != self.current_entity:
            raise ValueError(f"Not {entity_id}'s turn")
        if not self.is_ability_ready(entity_id, ability_slot):
            raise ValueError(f"Ability slot {ability_slot} is on cooldown")
        if cooldown > 0:
            self._cooldowns[entity_id][ability_slot] = cooldown

    def is_ability_ready(self, entity_id: str, ability_slot: int) -> bool:
        return self.get_cooldown(entity_id, ability_slot) == 0

    def get_cooldown(self, entity_id: str, ability_slot: int) -> int:
        return self._cooldowns.get(entity_id, {}).get(ability_slot, 0)

    def end_turn(self) -> str:
        self._pa[self.current_entity] = 0
        self._advance()
        self._start_turn()
        return self.current_entity

    def remove_entity(self, entity_id: str) -> None:
        if entity_id not in self._turn_order:
            raise ValueError(f"Entity {entity_id} not in turn order")

        removed_index = self._turn_order.index(entity_id)
        is_current = removed_index == self._index

        self._turn_order.remove(entity_id)
        self._pa.pop(entity_id, None)
        self._cooldowns.pop(entity_id, None)

        if is_current:
            if self._index >= len(self._turn_order):
                self._index = 0
                self._round += 1
            self._start_turn()
        elif removed_index < self._index:
            self._index -= 1

    def _start_turn(self) -> None:
        entity = self.current_entity
        self._pa[entity] = PA_PER_TURN
        cds = self._cooldowns.get(entity, {})
        to_remove = []
        for slot, cd in cds.items():
            new_cd = max(0, cd - 1)
            if new_cd == 0:
                to_remove.append(slot)
            else:
                cds[slot] = new_cd
        for slot in to_remove:
            del cds[slot]

    def _advance(self) -> None:
        self._index += 1
        if self._index >= len(self._turn_order):
            self._index = 0
            self._round += 1
