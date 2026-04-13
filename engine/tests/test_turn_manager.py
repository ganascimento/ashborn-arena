import pytest

from engine.systems.turn_manager import PA_PER_TURN, TurnManager


class TestTurnManagerInit:
    def test_first_entity_is_active(self):
        tm = TurnManager(["A", "B", "C"])
        assert tm.current_entity == "A"

    def test_current_round_starts_at_1(self):
        tm = TurnManager(["A", "B", "C"])
        assert tm.current_round == 1

    def test_turn_order_matches_input(self):
        tm = TurnManager(["A", "B", "C"])
        assert tm.turn_order == ["A", "B", "C"]

    def test_empty_list_raises(self):
        with pytest.raises(ValueError):
            TurnManager([])

    def test_active_entity_starts_with_4_pa(self):
        tm = TurnManager(["A", "B", "C"])
        assert tm.get_pa("A") == 4

    def test_pa_per_turn_constant(self):
        assert PA_PER_TURN == 4


class TestPA:
    def test_spend_pa_reduces(self):
        tm = TurnManager(["A", "B"])
        tm.spend_pa("A", 2)
        assert tm.get_pa("A") == 2

    def test_spend_pa_multiple_times(self):
        tm = TurnManager(["A", "B"])
        tm.spend_pa("A", 1)
        tm.spend_pa("A", 2)
        assert tm.get_pa("A") == 1

    def test_spend_pa_exceeds_remaining_raises(self):
        tm = TurnManager(["A", "B"])
        with pytest.raises(ValueError):
            tm.spend_pa("A", 5)

    def test_spend_pa_zero_raises(self):
        tm = TurnManager(["A", "B"])
        with pytest.raises(ValueError):
            tm.spend_pa("A", 0)

    def test_spend_pa_negative_raises(self):
        tm = TurnManager(["A", "B"])
        with pytest.raises(ValueError):
            tm.spend_pa("A", -1)

    def test_spend_pa_wrong_entity_raises(self):
        tm = TurnManager(["A", "B"])
        with pytest.raises(ValueError):
            tm.spend_pa("B", 1)

    def test_can_spend_pa_true(self):
        tm = TurnManager(["A", "B"])
        assert tm.can_spend_pa("A", 4) is True

    def test_can_spend_pa_false_exceeds(self):
        tm = TurnManager(["A", "B"])
        assert tm.can_spend_pa("A", 5) is False

    def test_can_spend_pa_false_wrong_entity(self):
        tm = TurnManager(["A", "B"])
        assert tm.can_spend_pa("B", 1) is False

    def test_get_pa_non_active_entity_returns_0(self):
        tm = TurnManager(["A", "B"])
        assert tm.get_pa("B") == 0

    def test_pa_discarded_after_end_turn(self):
        tm = TurnManager(["A", "B"])
        tm.spend_pa("A", 1)
        tm.end_turn()
        assert tm.get_pa("A") == 0


class TestCooldowns:
    def test_unused_ability_is_ready(self):
        tm = TurnManager(["A", "B"])
        assert tm.is_ability_ready("A", 0) is True

    def test_unused_ability_cooldown_is_0(self):
        tm = TurnManager(["A", "B"])
        assert tm.get_cooldown("A", 0) == 0

    def test_use_ability_sets_cooldown(self):
        tm = TurnManager(["A", "B"])
        tm.use_ability("A", 1, 3)
        assert tm.get_cooldown("A", 1) == 3

    def test_ability_not_ready_after_use(self):
        tm = TurnManager(["A", "B"])
        tm.use_ability("A", 1, 3)
        assert tm.is_ability_ready("A", 1) is False

    def test_use_ability_on_cooldown_raises(self):
        tm = TurnManager(["A", "B"])
        tm.use_ability("A", 1, 3)
        with pytest.raises(ValueError):
            tm.use_ability("A", 1, 2)

    def test_use_ability_zero_cooldown_valid(self):
        tm = TurnManager(["A", "B"])
        tm.use_ability("A", 0, 0)
        assert tm.is_ability_ready("A", 0) is True

    def test_use_ability_wrong_entity_raises(self):
        tm = TurnManager(["A", "B"])
        with pytest.raises(ValueError):
            tm.use_ability("B", 1, 3)

    def test_cooldown_full_cycle(self):
        tm = TurnManager(["A", "B"])
        tm.use_ability("A", 1, 3)
        assert tm.get_cooldown("A", 1) == 3

        tm.end_turn()
        tm.end_turn()
        assert tm.get_cooldown("A", 1) == 2

        tm.end_turn()
        tm.end_turn()
        assert tm.get_cooldown("A", 1) == 1

        tm.end_turn()
        tm.end_turn()
        assert tm.get_cooldown("A", 1) == 0
        assert tm.is_ability_ready("A", 1) is True


class TestTurnFlow:
    def test_end_turn_returns_next(self):
        tm = TurnManager(["A", "B", "C"])
        assert tm.end_turn() == "B"

    def test_end_turn_sequence(self):
        tm = TurnManager(["A", "B", "C"])
        assert tm.end_turn() == "B"
        assert tm.end_turn() == "C"

    def test_round_increments_after_full_cycle(self):
        tm = TurnManager(["A", "B", "C"])
        tm.end_turn()
        tm.end_turn()
        result = tm.end_turn()
        assert result == "A"
        assert tm.current_round == 2

    def test_pa_reset_on_new_turn(self):
        tm = TurnManager(["A", "B", "C"])
        tm.spend_pa("A", 3)
        tm.end_turn()
        assert tm.get_pa("A") == 0
        assert tm.get_pa("B") == 4

    def test_cooldowns_decrement_on_turn_start(self):
        tm = TurnManager(["A", "B"])
        tm.use_ability("A", 1, 2)
        tm.end_turn()
        tm.end_turn()
        assert tm.get_cooldown("A", 1) == 1


class TestRemoveEntity:
    def test_remove_non_active_entity(self):
        tm = TurnManager(["A", "B", "C"])
        tm.remove_entity("B")
        assert tm.end_turn() == "C"

    def test_remove_active_entity_advances(self):
        tm = TurnManager(["A", "B", "C"])
        tm.remove_entity("A")
        assert tm.current_entity == "B"
        assert tm.get_pa("B") == 4

    def test_remove_nonexistent_raises(self):
        tm = TurnManager(["A", "B"])
        with pytest.raises(ValueError):
            tm.remove_entity("Z")

    def test_remove_leaves_one_entity(self):
        tm = TurnManager(["A", "B"])
        tm.remove_entity("B")
        tm.end_turn()
        assert tm.current_entity == "A"
        assert tm.current_round == 2

    def test_remove_last_in_order_wraps_round(self):
        tm = TurnManager(["A", "B", "C"])
        tm.end_turn()
        tm.end_turn()
        tm.remove_entity("C")
        assert tm.current_entity == "A"
        assert tm.current_round == 2
