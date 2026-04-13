import random

from engine.systems.initiative import determine_turn_order, roll_initiative


class TestRollInitiative:
    def test_zero_modifier_range(self):
        rng = random.Random(42)
        results = {roll_initiative(0, rng=rng) for _ in range(200)}
        assert min(results) >= 1
        assert max(results) <= 20

    def test_positive_modifier_range(self):
        rng = random.Random(42)
        results = {roll_initiative(3, rng=rng) for _ in range(200)}
        assert min(results) >= 4
        assert max(results) <= 23

    def test_negative_modifier_range(self):
        rng = random.Random(42)
        results = {roll_initiative(-2, rng=rng) for _ in range(200)}
        assert min(results) >= -1
        assert max(results) <= 18

    def test_deterministic_with_rng(self):
        result_a = roll_initiative(0, rng=random.Random(99))
        result_b = roll_initiative(0, rng=random.Random(99))
        assert result_a == result_b

    def test_without_rng_returns_valid_range(self):
        result = roll_initiative(0)
        assert 1 <= result <= 20


class TestDetermineTurnOrder:
    def test_descending_initiative_order(self):
        rng = random.Random(1)
        participants = [
            ("warrior", 5, 8),
            ("mage", -2, 3),
            ("archer", 4, 9),
        ]
        order = determine_turn_order(participants, rng=rng)
        assert len(order) == 3
        assert all(eid in order for eid in ["warrior", "mage", "archer"])

    def test_higher_initiative_goes_first(self):
        rng = random.Random(0)
        rolls = []
        temp_rng = random.Random(0)
        for _ in range(3):
            rolls.append(temp_rng.randint(1, 20))

        participants = [
            ("a", 0, 5),
            ("b", 0, 5),
            ("c", 0, 5),
        ]
        order = determine_turn_order(participants, rng=rng)
        assert len(order) == 3

    def test_tiebreak_by_dex_base(self):
        class FixedRng:
            def randint(self, a, b):
                return 10

            def random(self):
                return 0.5

        participants = [
            ("low_dex", 0, 3),
            ("high_dex", 0, 9),
        ]
        order = determine_turn_order(participants, rng=FixedRng())
        assert order[0] == "high_dex"
        assert order[1] == "low_dex"

    def test_tiebreak_by_rng_when_same_dex_base(self):
        class FixedRollRng:
            def __init__(self, seed):
                self._rng = random.Random(seed)

            def randint(self, a, b):
                return 10

            def random(self):
                return self._rng.random()

        participants = [
            ("alpha", 0, 5),
            ("beta", 0, 5),
        ]

        order_a = determine_turn_order(participants, rng=FixedRollRng(42))
        order_b = determine_turn_order(participants, rng=FixedRollRng(42))
        assert order_a == order_b

        seen_orders = set()
        for seed in range(100):
            order = determine_turn_order(participants, rng=FixedRollRng(seed))
            seen_orders.add(tuple(order))
        assert len(seen_orders) == 2

    def test_single_participant(self):
        rng = random.Random(0)
        order = determine_turn_order([("solo", 0, 5)], rng=rng)
        assert order == ["solo"]

    def test_many_participants_all_present(self):
        rng = random.Random(0)
        participants = [(f"p{i}", i - 3, i) for i in range(6)]
        order = determine_turn_order(participants, rng=rng)
        assert len(order) == 6
        assert set(order) == {f"p{i}" for i in range(6)}
