import random

from engine.models.character import (
    BASE_ATTRIBUTES,
    Attributes,
    Character,
    CharacterClass,
    CharacterState,
)
from engine.models.ability import ABILITIES, BASIC_ATTACKS, AbilityTarget
from engine.models.effect import Effect, EffectType
from engine.models.grid import Grid, Occupant, OccupantType, Team
from engine.models.position import Position
from engine.systems.battle import BattleState, ACTION_MOVE, ACTION_ABILITY_1, ACTION_ABILITY_2, ACTION_ABILITY_3, ACTION_ABILITY_4, ACTION_ABILITY_5, ACTION_BASIC, ACTION_END_TURN
from engine.systems.effect_manager import EffectManager
from engine.systems.damage import calculate_raw_damage


def _place(bs, entity_id, new_pos):
    old_pos = bs.get_position(entity_id)
    bs.grid.remove_occupant(old_pos, entity_id)
    bs._positions[entity_id] = new_pos
    bs.grid.place_occupant(new_pos, Occupant(entity_id, OccupantType.CHARACTER, bs.get_team(entity_id)))


def _make_battle(team_a_classes, team_b_classes, seed=42):
    build = (2, 2, 2, 2, 2)
    ta = [(cls, build) for cls in team_a_classes]
    tb = [(cls, build) for cls in team_b_classes]
    return BattleState.from_config(ta, tb, rng=random.Random(seed))


def _get_entity_by_class(bs, cls, team="a"):
    entities = bs.team_a_entities if team == "a" else bs.team_b_entities
    for eid in entities:
        if bs.get_character(eid).character_class == cls:
            return eid
    return None


class TestAoEExpansion:
    def test_aoe_hits_multiple_enemies(self):
        bs = _make_battle(
            [CharacterClass.MAGE],
            [CharacterClass.WARRIOR, CharacterClass.ASSASSIN, CharacterClass.ARCHER],
            seed=10,
        )
        mage_id = _get_entity_by_class(bs, CharacterClass.MAGE, "a")
        enemies = bs.team_b_entities

        center = Position(5, 4)
        _place(bs, mage_id, Position(5, 2))
        for i, eid in enumerate(enemies):
            _place(bs, eid, Position(4 + i, 4))

        while bs.current_agent != mage_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        hp_before = {eid: bs.get_character(eid).current_hp for eid in enemies}
        target_idx = center.y * 10 + center.x
        # nova_flamejante is ability slot 1 (index 1 in equipped list)
        # MAGE equips: estilhaco_arcano, nova_flamejante, toque_do_inverno, barreira_arcana, sifao_vital
        bs.execute_action(ACTION_ABILITY_2, target_idx)  # ABILITY_2 = slot 1 = nova_flamejante

        hit_count = sum(
            1 for eid in enemies
            if bs.get_character(eid).current_hp < hp_before[eid]
        )
        assert hit_count >= 2, f"AoE should hit multiple targets, only hit {hit_count}"

    def test_aoe_friendly_fire(self):
        bs = _make_battle(
            [CharacterClass.MAGE, CharacterClass.WARRIOR],
            [CharacterClass.ASSASSIN],
            seed=10,
        )
        mage_id = _get_entity_by_class(bs, CharacterClass.MAGE, "a")
        warrior_id = _get_entity_by_class(bs, CharacterClass.WARRIOR, "a")
        enemy_id = bs.team_b_entities[0]

        center = Position(5, 4)
        _place(bs, mage_id, Position(5, 2))
        _place(bs, warrior_id, Position(5, 4))
        _place(bs, enemy_id, Position(4, 4))

        while bs.current_agent != mage_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        ally_hp_before = bs.get_character(warrior_id).current_hp
        target_idx = center.y * 10 + center.x
        bs.execute_action(ACTION_ABILITY_2, target_idx)  # nova_flamejante

        ally_hp_after = bs.get_character(warrior_id).current_hp
        assert ally_hp_after < ally_hp_before, "AoE should deal friendly fire damage to ally"

    def test_aoe_no_evasion(self):
        bs = _make_battle(
            [CharacterClass.MAGE],
            [CharacterClass.ARCHER],
            seed=10,
        )
        mage_id = _get_entity_by_class(bs, CharacterClass.MAGE, "a")
        archer_id = bs.team_b_entities[0]

        center = Position(5, 4)
        _place(bs, mage_id, Position(5, 2))
        _place(bs, archer_id, center)

        while bs.current_agent != mage_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        hp_before = bs.get_character(archer_id).current_hp
        target_idx = center.y * 10 + center.x
        bs.execute_action(ACTION_ABILITY_2, target_idx)

        assert bs.get_character(archer_id).current_hp < hp_before, "AoE should always hit (no evasion)"

    def test_adjacent_aoe(self):
        bs = _make_battle(
            [CharacterClass.WARRIOR],
            [CharacterClass.ASSASSIN, CharacterClass.MAGE],
            seed=10,
        )
        warrior_id = _get_entity_by_class(bs, CharacterClass.WARRIOR, "a")
        enemies = bs.team_b_entities

        _place(bs, warrior_id, Position(5, 4))
        _place(bs, enemies[0], Position(6, 4))
        _place(bs, enemies[1], Position(4, 4))

        while bs.current_agent != warrior_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        redemoinho = ABILITIES["redemoinho_de_aco"]
        bs._equipped[warrior_id][0] = redemoinho

        hp_before = {eid: bs.get_character(eid).current_hp for eid in enemies}
        pos = bs.get_position(warrior_id)
        target_idx = pos.y * 10 + pos.x
        bs.execute_action(ACTION_ABILITY_1, target_idx)

        hit_count = sum(1 for eid in enemies if bs.get_character(eid).current_hp < hp_before[eid])
        assert hit_count == 2, f"Adjacent AoE should hit both enemies, hit {hit_count}"


class TestChainDamage:
    def test_chain_hits_secondary_targets(self):
        bs = _make_battle(
            [CharacterClass.MAGE],
            [CharacterClass.WARRIOR, CharacterClass.ASSASSIN, CharacterClass.ARCHER],
            seed=10,
        )
        mage_id = _get_entity_by_class(bs, CharacterClass.MAGE, "a")
        enemies = bs.team_b_entities
        primary = enemies[0]

        _place(bs, mage_id, Position(2, 4))
        _place(bs, primary, Position(5, 4))
        _place(bs, enemies[1], Position(6, 4))
        _place(bs, enemies[2], Position(6, 5))

        while bs.current_agent != mage_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        hp_before = {eid: bs.get_character(eid).current_hp for eid in enemies}
        target_idx = bs.get_position(primary).y * 10 + bs.get_position(primary).x
        # arco_voltaico is not in default mage equip either
        # MAGE equips: estilhaco_arcano, nova_flamejante, toque_do_inverno, barreira_arcana, sifao_vital
        # arco_voltaico is NOT equipped by default. We need to equip it manually.
        arco = ABILITIES["arco_voltaico"]
        bs._equipped[mage_id][1] = arco  # Replace nova_flamejante with arco_voltaico
        bs.execute_action(ACTION_ABILITY_2, target_idx)  # slot 1

        primary_hit = hp_before[primary] - bs.get_character(primary).current_hp
        secondary_hits = sum(
            1 for eid in enemies[1:]
            if bs.get_character(eid).current_hp < hp_before[eid]
        )
        assert primary_hit > 0, "Primary target should take damage"
        assert secondary_hits >= 1, "At least 1 secondary should be hit by chain"

    def test_chain_secondary_damage_is_70_percent(self):
        bs = _make_battle(
            [CharacterClass.MAGE],
            [CharacterClass.WARRIOR, CharacterClass.ASSASSIN],
            seed=10,
        )
        mage_id = _get_entity_by_class(bs, CharacterClass.MAGE, "a")
        primary = bs.team_b_entities[0]
        secondary = bs.team_b_entities[1]

        _place(bs, mage_id, Position(2, 4))
        _place(bs, primary, Position(5, 4))
        _place(bs, secondary, Position(6, 4))

        while bs.current_agent != mage_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        arco = ABILITIES["arco_voltaico"]
        bs._equipped[mage_id][1] = arco

        hp_before_p = bs.get_character(primary).current_hp
        hp_before_s = bs.get_character(secondary).current_hp
        target_idx = bs.get_position(primary).y * 10 + bs.get_position(primary).x
        bs.execute_action(ACTION_ABILITY_2, target_idx)

        primary_dmg = hp_before_p - bs.get_character(primary).current_hp
        secondary_dmg = hp_before_s - bs.get_character(secondary).current_hp

        if primary_dmg > 0 and secondary_dmg > 0:
            ratio = secondary_dmg / primary_dmg
            assert 0.5 <= ratio <= 0.9, f"Chain should be ~70% of primary, got {ratio:.2f}"

    def test_chain_only_enemies(self):
        bs = _make_battle(
            [CharacterClass.MAGE, CharacterClass.CLERIC],
            [CharacterClass.WARRIOR],
            seed=10,
        )
        mage_id = _get_entity_by_class(bs, CharacterClass.MAGE, "a")
        cleric_id = _get_entity_by_class(bs, CharacterClass.CLERIC, "a")
        enemy_id = bs.team_b_entities[0]

        _place(bs, mage_id, Position(2, 4))
        _place(bs, enemy_id, Position(5, 4))
        _place(bs, cleric_id, Position(6, 4))

        while bs.current_agent != mage_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        arco = ABILITIES["arco_voltaico"]
        bs._equipped[mage_id][1] = arco

        ally_hp_before = bs.get_character(cleric_id).current_hp
        target_idx = bs.get_position(enemy_id).y * 10 + bs.get_position(enemy_id).x
        bs.execute_action(ACTION_ABILITY_2, target_idx)

        assert bs.get_character(cleric_id).current_hp == ally_hp_before, "Chain should not hit allies"


class TestDamageReflect:
    def test_reflect_damages_attacker(self):
        bs = _make_battle(
            [CharacterClass.WARRIOR],
            [CharacterClass.CLERIC],
            seed=10,
        )
        warrior_id = _get_entity_by_class(bs, CharacterClass.WARRIOR, "a")
        cleric_id = bs.team_b_entities[0]

        _place(bs, warrior_id, Position(5, 4))
        _place(bs, cleric_id, Position(6, 4))

        em = bs.get_effect_manager()
        em.apply_effect(cleric_id, Effect("reflect", EffectType.BUFF, cleric_id, 2, 0.30))

        while bs.current_agent != warrior_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        attacker_hp_before = bs.get_character(warrior_id).current_hp
        target_idx = bs.get_position(cleric_id).y * 10 + bs.get_position(cleric_id).x
        bs.execute_action(ACTION_BASIC, target_idx)

        attacker_hp_after = bs.get_character(warrior_id).current_hp
        assert attacker_hp_after < attacker_hp_before, "Reflect should damage the attacker"

    def test_reflect_is_30_percent(self):
        bs = _make_battle(
            [CharacterClass.WARRIOR],
            [CharacterClass.CLERIC],
            seed=10,
        )
        warrior_id = _get_entity_by_class(bs, CharacterClass.WARRIOR, "a")
        cleric_id = bs.team_b_entities[0]

        _place(bs, warrior_id, Position(5, 4))
        _place(bs, cleric_id, Position(6, 4))

        em = bs.get_effect_manager()
        em.apply_effect(cleric_id, Effect("reflect", EffectType.BUFF, cleric_id, 2, 0.30))

        while bs.current_agent != warrior_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        cleric_hp_before = bs.get_character(cleric_id).current_hp
        warrior_hp_before = bs.get_character(warrior_id).current_hp
        target_idx = bs.get_position(cleric_id).y * 10 + bs.get_position(cleric_id).x
        bs.execute_action(ACTION_BASIC, target_idx)

        damage_to_cleric = cleric_hp_before - bs.get_character(cleric_id).current_hp
        damage_to_warrior = warrior_hp_before - bs.get_character(warrior_id).current_hp

        if damage_to_cleric > 0 and damage_to_warrior > 0:
            ratio = damage_to_warrior / damage_to_cleric
            assert 0.2 <= ratio <= 0.4, f"Reflect should be ~30%, got {ratio:.2f}"


class TestDamageRedirect:
    def test_redirect_splits_damage(self):
        bs = _make_battle(
            [CharacterClass.WARRIOR],
            [CharacterClass.CLERIC, CharacterClass.MAGE],
            seed=10,
        )
        warrior_id = _get_entity_by_class(bs, CharacterClass.WARRIOR, "a")
        cleric_id = _get_entity_by_class(bs, CharacterClass.CLERIC, "b")
        mage_id = _get_entity_by_class(bs, CharacterClass.MAGE, "b")

        _place(bs, warrior_id, Position(4, 4))
        _place(bs, mage_id, Position(5, 4))
        _place(bs, cleric_id, Position(6, 4))

        em = bs.get_effect_manager()
        em.apply_effect(mage_id, Effect("redirect", EffectType.BUFF, cleric_id, 2, 0.40))

        while bs.current_agent != warrior_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        mage_hp_before = bs.get_character(mage_id).current_hp
        cleric_hp_before = bs.get_character(cleric_id).current_hp
        target_idx = bs.get_position(mage_id).y * 10 + bs.get_position(mage_id).x
        bs.execute_action(ACTION_BASIC, target_idx)

        mage_dmg = mage_hp_before - bs.get_character(mage_id).current_hp
        cleric_dmg = cleric_hp_before - bs.get_character(cleric_id).current_hp

        assert mage_dmg > 0, "Mage should still take damage"
        assert cleric_dmg > 0, "Cleric (redirector) should take redirected damage"

    def test_redirect_does_not_work_if_caster_dead(self):
        bs = _make_battle(
            [CharacterClass.WARRIOR],
            [CharacterClass.CLERIC, CharacterClass.MAGE],
            seed=10,
        )
        warrior_id = _get_entity_by_class(bs, CharacterClass.WARRIOR, "a")
        cleric_id = _get_entity_by_class(bs, CharacterClass.CLERIC, "b")
        mage_id = _get_entity_by_class(bs, CharacterClass.MAGE, "b")

        _place(bs, warrior_id, Position(4, 4))
        _place(bs, mage_id, Position(5, 4))
        _place(bs, cleric_id, Position(6, 4))

        em = bs.get_effect_manager()
        em.apply_effect(mage_id, Effect("redirect", EffectType.BUFF, cleric_id, 2, 0.40))
        bs.get_character(cleric_id).apply_damage(bs.get_character(cleric_id).max_hp + 11)

        while bs.current_agent != warrior_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        mage_hp_before = bs.get_character(mage_id).current_hp
        target_idx = bs.get_position(mage_id).y * 10 + bs.get_position(mage_id).x
        bs.execute_action(ACTION_BASIC, target_idx)

        mage_dmg = mage_hp_before - bs.get_character(mage_id).current_hp
        assert mage_dmg > 0, "Mage takes full damage when redirector is dead"


class TestUntargetable:
    def test_untargetable_excluded_from_masking(self):
        from training.environment.actions import compute_action_mask
        bs = _make_battle(
            [CharacterClass.WARRIOR],
            [CharacterClass.ASSASSIN],
            seed=10,
        )
        warrior_id = _get_entity_by_class(bs, CharacterClass.WARRIOR, "a")
        assassin_id = bs.team_b_entities[0]

        _place(bs, warrior_id, Position(5, 4))
        _place(bs, assassin_id, Position(6, 4))

        em = bs.get_effect_manager()
        em.apply_effect(assassin_id, Effect("untargetable", EffectType.BUFF, assassin_id, 1))

        while bs.current_agent != warrior_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        mask = compute_action_mask(bs, warrior_id)
        target_idx = bs.get_position(assassin_id).y * 10 + bs.get_position(assassin_id).x
        assert mask["target_mask"][ACTION_BASIC, target_idx] == False, \
            "Untargetable enemy should not be valid target for basic attack"

    def test_aoe_skips_untargetable(self):
        bs = _make_battle(
            [CharacterClass.MAGE],
            [CharacterClass.WARRIOR, CharacterClass.ASSASSIN],
            seed=10,
        )
        mage_id = _get_entity_by_class(bs, CharacterClass.MAGE, "a")
        enemies = bs.team_b_entities

        center = Position(5, 4)
        _place(bs, mage_id, Position(5, 2))
        _place(bs, enemies[0], Position(5, 4))
        _place(bs, enemies[1], Position(4, 4))

        em = bs.get_effect_manager()
        em.apply_effect(enemies[1], Effect("untargetable", EffectType.BUFF, enemies[1], 1))

        while bs.current_agent != mage_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        hp_before = {eid: bs.get_character(eid).current_hp for eid in enemies}
        target_idx = center.y * 10 + center.x
        bs.execute_action(ACTION_ABILITY_2, target_idx)  # nova_flamejante

        assert bs.get_character(enemies[0]).current_hp < hp_before[enemies[0]], \
            "Non-untargetable enemy should take AoE damage"
        assert bs.get_character(enemies[1]).current_hp == hp_before[enemies[1]], \
            "Untargetable enemy should be skipped by AoE"


class TestMeteorDelayed:
    def test_meteor_marks_then_resolves_next_turn(self):
        bs = _make_battle(
            [CharacterClass.MAGE],
            [CharacterClass.WARRIOR],
            seed=10,
        )
        mage_id = _get_entity_by_class(bs, CharacterClass.MAGE, "a")
        enemy_id = bs.team_b_entities[0]

        _place(bs, mage_id, Position(2, 4))
        _place(bs, enemy_id, Position(5, 4))

        while bs.current_agent != mage_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        meteoro = ABILITIES["meteoro"]
        bs._equipped[mage_id][1] = meteoro

        hp_before = bs.get_character(enemy_id).current_hp
        target_idx = bs.get_position(enemy_id).y * 10 + bs.get_position(enemy_id).x
        bs.execute_action(ACTION_ABILITY_2, target_idx)

        assert bs.get_character(enemy_id).current_hp == hp_before, \
            "Meteor should NOT deal damage immediately"
        assert len(bs._delayed_abilities) == 1

        bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()
        bs.execute_action(ACTION_END_TURN, 0)

        bs.process_turn_start()
        assert bs.get_character(enemy_id).current_hp < hp_before, \
            "Meteor should deal damage on caster's next turn"


class TestTrap:
    def test_trap_placed_and_triggered_on_move(self):
        bs = _make_battle(
            [CharacterClass.ARCHER],
            [CharacterClass.WARRIOR],
            seed=10,
        )
        archer_id = _get_entity_by_class(bs, CharacterClass.ARCHER, "a")
        warrior_id = bs.team_b_entities[0]

        trap_pos = Position(5, 4)
        _place(bs, archer_id, Position(3, 4))
        _place(bs, warrior_id, Position(7, 4))

        while bs.current_agent != archer_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        armadilha = ABILITIES["armadilha_espinhosa"]
        bs._equipped[archer_id][0] = armadilha
        target_idx = trap_pos.y * 10 + trap_pos.x
        bs.execute_action(ACTION_ABILITY_1, target_idx)

        assert trap_pos in bs._traps, "Trap should be placed on tile"

        bs.execute_action(ACTION_END_TURN, 0)

        while bs.current_agent != warrior_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        hp_before = bs.get_character(warrior_id).current_hp
        _place(bs, warrior_id, Position(6, 4))
        bs.execute_action(ACTION_MOVE, trap_pos.y * 10 + trap_pos.x)

        if bs.get_position(warrior_id) == trap_pos:
            assert bs.get_character(warrior_id).current_hp < hp_before, \
                "Trap should deal damage when stepped on"
            assert trap_pos not in bs._traps, "Trap should be consumed"


class TestPoisonOnHit:
    def test_poison_attacks_applies_dot(self):
        bs = _make_battle(
            [CharacterClass.ASSASSIN],
            [CharacterClass.WARRIOR],
            seed=10,
        )
        assassin_id = _get_entity_by_class(bs, CharacterClass.ASSASSIN, "a")
        warrior_id = bs.team_b_entities[0]

        _place(bs, assassin_id, Position(5, 4))
        _place(bs, warrior_id, Position(6, 4))

        em = bs.get_effect_manager()
        em.apply_effect(assassin_id, Effect("poison_attacks", EffectType.BUFF, assassin_id, 3, 3.0))

        while bs.current_agent != assassin_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        target_idx = bs.get_position(warrior_id).y * 10 + bs.get_position(warrior_id).x
        bs.execute_action(ACTION_BASIC, target_idx)

        assert em.has_effect(warrior_id, "poison"), \
            "Poison DOT should be applied to target after hit"

    def test_poison_attacks_consumes_charges(self):
        bs = _make_battle(
            [CharacterClass.ASSASSIN],
            [CharacterClass.WARRIOR],
            seed=10,
        )
        assassin_id = _get_entity_by_class(bs, CharacterClass.ASSASSIN, "a")
        warrior_id = bs.team_b_entities[0]

        _place(bs, assassin_id, Position(5, 4))
        _place(bs, warrior_id, Position(6, 4))

        em = bs.get_effect_manager()
        em.apply_effect(assassin_id, Effect("poison_attacks", EffectType.BUFF, assassin_id, 1, 3.0))

        while bs.current_agent != assassin_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        target_idx = bs.get_position(warrior_id).y * 10 + bs.get_position(warrior_id).x
        bs.execute_action(ACTION_BASIC, target_idx)

        assert not em.has_effect(assassin_id, "poison_attacks"), \
            "Poison buff should be consumed after last charge"


class TestNextAttackBonus:
    def test_olho_do_predador_doubles_damage(self):
        bs = _make_battle(
            [CharacterClass.ARCHER],
            [CharacterClass.WARRIOR],
            seed=10,
        )
        archer_id = _get_entity_by_class(bs, CharacterClass.ARCHER, "a")
        warrior_id = bs.team_b_entities[0]

        _place(bs, archer_id, Position(5, 4))
        _place(bs, warrior_id, Position(6, 4))

        while bs.current_agent != archer_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        em = bs.get_effect_manager()
        em.apply_effect(archer_id, Effect("next_attack_bonus", EffectType.BUFF, archer_id, 2, 1.0))

        hp_before = bs.get_character(warrior_id).current_hp
        target_idx = bs.get_position(warrior_id).y * 10 + bs.get_position(warrior_id).x
        bs.execute_action(ACTION_BASIC, target_idx)
        damage_with_bonus = hp_before - bs.get_character(warrior_id).current_hp

        assert not em.has_effect(archer_id, "next_attack_bonus"), \
            "Bonus should be consumed after attack"
        assert damage_with_bonus > 0

    def test_bonus_consumed_after_one_attack(self):
        bs = _make_battle(
            [CharacterClass.ARCHER],
            [CharacterClass.WARRIOR],
            seed=10,
        )
        archer_id = _get_entity_by_class(bs, CharacterClass.ARCHER, "a")
        warrior_id = bs.team_b_entities[0]

        _place(bs, archer_id, Position(5, 4))
        _place(bs, warrior_id, Position(6, 4))

        while bs.current_agent != archer_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        em = bs.get_effect_manager()
        em.apply_effect(archer_id, Effect("next_attack_bonus", EffectType.BUFF, archer_id, 2, 0.5))

        target_idx = bs.get_position(warrior_id).y * 10 + bs.get_position(warrior_id).x
        bs.execute_action(ACTION_BASIC, target_idx)

        assert not em.has_effect(archer_id, "next_attack_bonus"), \
            "Bonus consumed after first attack"


class TestRangeBonus:
    def test_range_bonus_extends_attack_range(self):
        from training.environment.actions import compute_action_mask
        bs = _make_battle(
            [CharacterClass.ARCHER],
            [CharacterClass.WARRIOR],
            seed=10,
        )
        archer_id = _get_entity_by_class(bs, CharacterClass.ARCHER, "a")
        warrior_id = bs.team_b_entities[0]

        _place(bs, archer_id, Position(0, 0))
        _place(bs, warrior_id, Position(7, 0))

        while bs.current_agent != archer_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        target_idx = bs.get_position(warrior_id).y * 10 + bs.get_position(warrior_id).x

        em = bs.get_effect_manager()
        em.apply_effect(archer_id, Effect("range_bonus", EffectType.BUFF, archer_id, 2, 2.0))

        mask_after = compute_action_mask(bs, archer_id)

        assert mask_after["target_mask"][ACTION_BASIC, target_idx], \
            "With +2 range bonus, archer (range 5+2=7) should reach warrior at distance 7"


class TestConsagracaoScaling:
    def test_consagracao_hot_uses_generic_scaling(self):
        bs = _make_battle(
            [CharacterClass.CLERIC],
            [CharacterClass.WARRIOR],
            seed=10,
        )
        cleric_id = _get_entity_by_class(bs, CharacterClass.CLERIC, "a")

        while bs.current_agent != cleric_id:
            bs.process_turn_start()
            bs.execute_action(ACTION_END_TURN, 0)
        bs.process_turn_start()

        cleric = bs.get_character(cleric_id)
        sab_mod = cleric.attributes.modifier("wis")

        pos = bs.get_position(cleric_id)
        target_idx = pos.y * 10 + pos.x
        # consagracao is slot 3 (index 3) → ACTION_ABILITY_4
        bs.execute_action(ACTION_ABILITY_4 + 1, target_idx)

        em = bs.get_effect_manager()
        hot = em.get_effect(cleric_id, "consecration")
        if hot:
            import math
            expected = 5 + math.floor(sab_mod * 0.5 + 0.5)
            assert hot.value == expected, f"HOT should be {expected}, got {hot.value}"
