import random

import pytest

from engine.models.character import (
    CharacterClass,
    CharacterState,
)
from engine.systems.battle import BattleState


def _build(cls: CharacterClass) -> tuple[int, ...]:
    return (2, 2, 2, 2, 2)


def _make_1v1(seed=42):
    team_a = [(CharacterClass.WARRIOR, _build(CharacterClass.WARRIOR))]
    team_b = [(CharacterClass.MAGE, _build(CharacterClass.MAGE))]
    return BattleState.from_config(team_a, team_b, rng=random.Random(seed))


def _make_1v1_melee(seed=42):
    team_a = [(CharacterClass.WARRIOR, _build(CharacterClass.WARRIOR))]
    team_b = [(CharacterClass.ASSASSIN, _build(CharacterClass.ASSASSIN))]
    return BattleState.from_config(team_a, team_b, rng=random.Random(seed))


class TestBattleSetup:
    def test_from_config_creates_battle(self):
        bs = _make_1v1()
        assert bs is not None
        assert bs.current_agent is not None

    def test_characters_in_spawn_zones(self):
        bs = _make_1v1()
        for eid in bs.team_a_entities:
            pos = bs.get_position(eid)
            assert pos.x <= 1, f"Team A {eid} at col {pos.x}"
        for eid in bs.team_b_entities:
            pos = bs.get_position(eid)
            assert pos.x >= 8, f"Team B {eid} at col {pos.x}"

    def test_characters_have_correct_hp(self):
        bs = _make_1v1()
        for eid in bs.team_a_entities:
            c = bs.get_character(eid)
            assert c.current_hp == c.max_hp
            assert c.state == CharacterState.ACTIVE

    def test_current_agent_is_valid(self):
        bs = _make_1v1()
        agent = bs.current_agent
        assert agent in bs.team_a_entities or agent in bs.team_b_entities


class TestTurnCycle:
    def test_process_turn_start_sets_pa(self):
        bs = _make_1v1()
        bs.process_turn_start()
        agent = bs.current_agent
        assert bs.get_pa(agent) == 4

    def test_end_turn_advances_agent(self):
        bs = _make_1v1()
        bs.process_turn_start()
        first = bs.current_agent
        bs.execute_action(8, 0)  # END_TURN
        bs.process_turn_start()
        second = bs.current_agent
        assert second != first

    def test_knocked_out_bleeds_and_skips(self):
        bs = _make_1v1()
        agent = bs.current_agent
        char = bs.get_character(agent)
        char.apply_damage(char.max_hp)
        assert char.state == CharacterState.KNOCKED_OUT
        hp_before = char.current_hp
        bs.process_turn_start()
        if bs.current_agent == agent:
            assert char.current_hp == hp_before - 3


class TestBasicActions:
    def test_move(self):
        bs = _make_1v1()
        bs.process_turn_start()
        agent = bs.current_agent
        pos_before = bs.get_position(agent)
        reachable = bs.get_reachable_tiles(agent)
        if reachable:
            target_pos = next(iter(reachable))
            target_idx = target_pos.y * 10 + target_pos.x
            events = bs.execute_action(0, target_idx)  # MOVE
            pos_after = bs.get_position(agent)
            assert pos_after != pos_before
            assert bs.get_pa(agent) < 4

    def test_basic_attack_deals_damage(self):
        bs = _make_1v1_melee(seed=10)
        bs.process_turn_start()
        attacker = bs.current_agent
        attacker_char = bs.get_character(attacker)

        defenders = (
            bs.team_b_entities if attacker in bs.team_a_entities else bs.team_a_entities
        )
        defender_id = defenders[0]
        defender_char = bs.get_character(defender_id)
        defender_pos = bs.get_position(defender_id)

        from engine.models.grid import Occupant, OccupantType
        from engine.models.position import Position

        attacker_pos = bs.get_position(attacker)
        new_pos = Position(max(0, defender_pos.x - 1), defender_pos.y)
        if new_pos == defender_pos:
            new_pos = Position(min(9, defender_pos.x + 1), defender_pos.y)
        bs.grid.remove_occupant(attacker_pos, attacker)
        bs._positions[attacker] = new_pos
        bs.grid.place_occupant(
            new_pos, Occupant(attacker, OccupantType.CHARACTER, bs.get_team(attacker))
        )

        hp_before = defender_char.current_hp
        target_idx = defender_pos.y * 10 + defender_pos.x
        bs.execute_action(1, target_idx)  # BASIC_ATTACK
        assert defender_char.current_hp < hp_before

    def test_end_turn(self):
        bs = _make_1v1()
        bs.process_turn_start()
        first = bs.current_agent
        bs.execute_action(8, 0)  # END_TURN
        assert bs.current_agent != first or len(bs.all_entities) == 1


class TestAbilityExecution:
    def test_ability_with_damage(self):
        for seed in range(20):
            bs = _make_1v1_melee(seed=seed)
            bs.process_turn_start()
            attacker = bs.current_agent
            attacker_char = bs.get_character(attacker)

            if attacker_char.character_class != CharacterClass.WARRIOR:
                bs.execute_action(8, 0)
                bs.process_turn_start()
                attacker = bs.current_agent
                attacker_char = bs.get_character(attacker)

            if attacker_char.character_class != CharacterClass.WARRIOR:
                continue

            defenders = (
                bs.team_b_entities
                if attacker in bs.team_a_entities
                else bs.team_a_entities
            )
            defender_id = defenders[0]
            defender_char = bs.get_character(defender_id)
            defender_pos = bs.get_position(defender_id)

            from engine.models.grid import Occupant, OccupantType
            from engine.models.position import Position

            attacker_pos = bs.get_position(attacker)
            new_pos = Position(max(0, defender_pos.x - 1), defender_pos.y)
            if new_pos == defender_pos:
                new_pos = Position(min(9, defender_pos.x + 1), defender_pos.y)
            bs.grid.remove_occupant(attacker_pos, attacker)
            bs._positions[attacker] = new_pos
            bs.grid.place_occupant(
                new_pos,
                Occupant(attacker, OccupantType.CHARACTER, bs.get_team(attacker)),
            )

            hp_before = defender_char.current_hp
            target_idx = defender_pos.y * 10 + defender_pos.x
            assert bs.get_pa(attacker) >= 2
            bs.execute_action(2, target_idx)  # ABILITY_1 (impacto_brutal)
            if defender_char.current_hp < hp_before:
                return
        pytest.fail("Could not set up warrior ability test in any seed")

    def test_healing_ability(self):
        team_a = [(CharacterClass.CLERIC, (2, 2, 2, 2, 2))]
        team_b = [(CharacterClass.WARRIOR, (2, 2, 2, 2, 2))]
        bs = BattleState.from_config(team_a, team_b, rng=random.Random(42))
        bs.process_turn_start()

        cleric_id = None
        for eid in bs.all_entities:
            if bs.get_character(eid).character_class == CharacterClass.CLERIC:
                cleric_id = eid
                break

        if cleric_id is None or bs.current_agent != cleric_id:
            pytest.skip("Cleric not first in turn order")

        cleric = bs.get_character(cleric_id)
        cleric.apply_damage(20)
        hp_before = cleric.current_hp

        equipped = bs.get_equipped_abilities(cleric_id)
        heal_slot = None
        for i, ab in enumerate(equipped):
            if ab and ab.heal_base > 0:
                heal_slot = i
                break

        if heal_slot is None:
            pytest.skip("Cleric has no heal ability equipped")

        cleric_pos = bs.get_position(cleric_id)
        target_idx = cleric_pos.y * 10 + cleric_pos.x
        bs.execute_action(2 + heal_slot, target_idx)
        assert cleric.current_hp > hp_before


class TestKnockoutAndDeath:
    def test_damage_to_zero_knocks_out(self):
        bs = _make_1v1()
        bs.process_turn_start()
        victim_id = bs.team_b_entities[0]
        victim = bs.get_character(victim_id)
        victim.apply_damage(victim.max_hp)
        assert victim.state == CharacterState.KNOCKED_OUT

    def test_damage_below_threshold_kills(self):
        bs = _make_1v1()
        bs.process_turn_start()
        victim_id = bs.team_b_entities[0]
        victim = bs.get_character(victim_id)
        victim.apply_damage(victim.max_hp + 11)
        assert victim.state == CharacterState.DEAD

    def test_dead_removed_from_turn_order(self):
        bs = _make_1v1()
        bs.process_turn_start()
        victim_id = bs.team_b_entities[0]
        victim = bs.get_character(victim_id)
        victim.apply_damage(victim.max_hp + 11)
        bs.handle_death(victim_id)
        assert victim_id not in bs.turn_order


class TestVictory:
    def test_no_victory_during_battle(self):
        bs = _make_1v1()
        assert bs.check_victory() is None

    def test_victory_when_all_enemies_dead(self):
        bs = _make_1v1()
        for eid in list(bs.team_b_entities):
            char = bs.get_character(eid)
            char.apply_damage(char.max_hp + 11)
            bs.handle_death(eid)
        result = bs.check_victory()
        assert result == "team_a"

    def test_knocked_out_counts_as_defeated(self):
        bs = _make_1v1()
        for eid in bs.team_b_entities:
            char = bs.get_character(eid)
            char.apply_damage(char.max_hp)
        assert bs.check_victory() == "team_a"
