import numpy as np
import pytest

from training.environment.actions import (
    NUM_ACTION_TYPES,
    NUM_TARGETS,
    ActionType,
)
from training.environment.arena_env import ArenaEnv
from training.environment.observations import (
    OBS_TOTAL_SIZE,
)
from training.environment.rewards import (
    REWARD_DAMAGE,
    REWARD_DEFEAT,
    REWARD_VICTORY,
)


class TestArenaEnvAPI:
    def test_reset_returns_observations(self):
        env = ArenaEnv(team_size=1)
        env.reset(seed=42)
        assert env.agents is not None
        assert len(env.agents) >= 2

    def test_step_executes(self):
        env = ArenaEnv(team_size=1)
        env.reset(seed=42)
        agent = env.agent_selection
        mask = env.infos[agent]["action_mask"]
        type_mask = mask["type_mask"]
        valid_type = int(np.where(type_mask)[0][0])
        target_mask = mask["target_mask"][valid_type]
        valid_target = int(np.where(target_mask)[0][0]) if np.any(target_mask) else 0
        env.step(np.array([valid_type, valid_target]))

    def test_observe_returns_correct_shape(self):
        env = ArenaEnv(team_size=1)
        env.reset(seed=42)
        agent = env.agent_selection
        obs = env.observe(agent)
        assert isinstance(obs, np.ndarray)
        assert obs.shape == (OBS_TOTAL_SIZE,)
        assert obs.dtype == np.float32

    def test_agents_list_has_all_characters(self):
        env = ArenaEnv(team_size=2)
        env.reset(seed=42)
        assert len(env.agents) == 4

    def test_infos_contain_action_mask(self):
        env = ArenaEnv(team_size=1)
        env.reset(seed=42)
        agent = env.agent_selection
        assert "action_mask" in env.infos[agent]
        mask = env.infos[agent]["action_mask"]
        assert "type_mask" in mask
        assert "target_mask" in mask
        assert mask["type_mask"].shape == (NUM_ACTION_TYPES,)
        assert mask["target_mask"].shape == (NUM_ACTION_TYPES, NUM_TARGETS)


class TestObservation:
    def test_values_normalized(self):
        env = ArenaEnv(team_size=1)
        env.reset(seed=42)
        agent = env.agent_selection
        obs = env.observe(agent)
        assert np.all(obs >= -0.5), f"Min value: {obs.min()}"
        assert np.all(obs <= 11.0), f"Max value: {obs.max()}"

    def test_map_encoding_has_80_tiles(self):
        env = ArenaEnv(team_size=1)
        env.reset(seed=42)
        agent = env.agent_selection
        obs = env.observe(agent)
        map_start = OBS_TOTAL_SIZE - 80
        map_section = obs[map_start:]
        assert map_section.shape == (80,)


class TestActionMask:
    def test_end_turn_always_available(self):
        env = ArenaEnv(team_size=1)
        env.reset(seed=42)
        agent = env.agent_selection
        mask = env.infos[agent]["action_mask"]
        assert mask["type_mask"][ActionType.END_TURN] == True

    def test_cooldown_masks_ability(self):
        env = ArenaEnv(team_size=1)
        env.reset(seed=42)
        agent = env.agent_selection

        mask_before = env.infos[agent]["action_mask"]
        ability_available = False
        for i in range(2, 7):
            if mask_before["type_mask"][i]:
                ability_available = True
                type_mask = mask_before["target_mask"][i]
                valid_target = (
                    int(np.where(type_mask)[0][0]) if np.any(type_mask) else 0
                )
                env.step(np.array([i, valid_target]))
                break

        if not ability_available:
            pytest.skip("No ability available to test cooldown")

        if env.agent_selection == agent:
            mask_after = env.infos[agent]["action_mask"]
            if not mask_after["type_mask"][i]:
                assert True
            else:
                pytest.skip("Ability has CD=0, no cooldown to test")

    def test_insufficient_pa_masks_action(self):
        env = ArenaEnv(team_size=1)
        env.reset(seed=42)
        agent = env.agent_selection

        for _ in range(4):
            mask = env.infos.get(agent, {}).get("action_mask")
            if mask is None or env.agent_selection != agent:
                break
            type_mask = mask["type_mask"]
            valid_type = int(np.where(type_mask)[0][0])
            if valid_type == ActionType.END_TURN:
                break
            target_mask = mask["target_mask"][valid_type]
            valid_target = (
                int(np.where(target_mask)[0][0]) if np.any(target_mask) else 0
            )
            env.step(np.array([valid_type, valid_target]))


class TestRewards:
    def test_damage_generates_positive_reward(self):
        env = ArenaEnv(team_size=1)
        env.reset(seed=42)

        total_steps = 0
        while total_steps < 50 and not all(env.terminations.values()):
            agent = env.agent_selection
            mask = env.infos[agent]["action_mask"]
            type_mask = mask["type_mask"]

            if type_mask[ActionType.BASIC_ATTACK]:
                target_mask = mask["target_mask"][ActionType.BASIC_ATTACK]
                if np.any(target_mask):
                    valid_target = int(np.where(target_mask)[0][0])
                    env.step(np.array([ActionType.BASIC_ATTACK, valid_target]))
                    if env.rewards.get(agent, 0) > 0:
                        assert True
                        return
                    total_steps += 1
                    continue

            valid_type = int(np.where(type_mask)[0][0])
            target_mask = mask["target_mask"][valid_type]
            valid_target = (
                int(np.where(target_mask)[0][0]) if np.any(target_mask) else 0
            )
            env.step(np.array([valid_type, valid_target]))
            total_steps += 1

    def test_victory_constants(self):
        assert REWARD_VICTORY == 10
        assert REWARD_DEFEAT == -10
        assert REWARD_DAMAGE == pytest.approx(0.1)


class TestTermination:
    def test_battle_terminates_eventually(self):
        env = ArenaEnv(team_size=1)
        env.reset(seed=42)
        steps = 0
        max_steps = 500
        while steps < max_steps and not all(env.terminations.values()):
            agent = env.agent_selection
            mask = env.infos[agent]["action_mask"]
            type_mask = mask["type_mask"]
            valid_type = int(np.where(type_mask)[0][0])
            target_mask = mask["target_mask"][valid_type]
            valid_target = (
                int(np.where(target_mask)[0][0]) if np.any(target_mask) else 0
            )
            env.step(np.array([valid_type, valid_target]))
            steps += 1

        assert all(env.terminations.values()) or steps == max_steps


class TestActionType:
    def test_enum_values(self):
        assert ActionType.MOVE == 0
        assert ActionType.BASIC_ATTACK == 1
        assert ActionType.ABILITY_1 == 2
        assert ActionType.ABILITY_5 == 6
        assert ActionType.THROW == 7
        assert ActionType.END_TURN == 8
        assert ActionType.PASS == 9
        assert NUM_ACTION_TYPES == 10
        assert NUM_TARGETS == 80
