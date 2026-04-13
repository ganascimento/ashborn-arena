import numpy as np
import torch
import pytest

from training.agents.mappo import MAPPOAgent
from training.agents.buffer import RolloutBuffer
from training.curriculum.trainer import Trainer
from training.environment.arena_env import ArenaEnv
from training.environment.observations import OBS_TOTAL_SIZE, GLOBAL_STATE_SIZE, encode_global_state
from training.environment.actions import NUM_ACTION_TYPES, NUM_TARGETS


@pytest.fixture
def setup():
    agent = MAPPOAgent()
    trainer = Trainer(agent, seed=42)
    buf = RolloutBuffer()
    for _ in range(3):
        env = ArenaEnv(team_size=1)
        trainer.collect_rollout(env, buf)
    return agent, trainer, buf


class TestObservationIntegrity:
    def test_obs_shape_and_dtype(self):
        env = ArenaEnv(team_size=1)
        env.reset(seed=42)
        obs = env.observe(env.agent_selection)
        assert obs.shape == (OBS_TOTAL_SIZE,)
        assert obs.dtype == np.float32
        assert not np.isnan(obs).any()
        assert not np.isinf(obs).any()

    def test_global_state_fixed_size(self):
        env = ArenaEnv(team_size=1)
        env.reset(seed=42)
        gs = encode_global_state(env._battle)
        assert gs.shape == (GLOBAL_STATE_SIZE,)
        assert not np.isnan(gs).any()

    def test_global_state_same_size_all_team_sizes(self):
        for ts in [1, 2, 3]:
            env = ArenaEnv(team_size=ts)
            env.reset(seed=42)
            gs = encode_global_state(env._battle)
            assert gs.shape == (GLOBAL_STATE_SIZE,), f"team_size={ts}: got {gs.shape}"


class TestActionMaskingIntegrity:
    def test_valid_types_have_valid_targets(self):
        env = ArenaEnv(team_size=1)
        env.reset(seed=42)
        mask = env.infos[env.agent_selection]["action_mask"]
        tm = mask["type_mask"]
        ftm = mask["target_mask"]
        for i in range(NUM_ACTION_TYPES):
            if tm[i]:
                assert ftm[i].any(), f"type {i} enabled but no valid targets"

    def test_hierarchical_action_always_valid(self):
        agent = MAPPOAgent()
        env = ArenaEnv(team_size=1)
        env.reset(seed=42)
        for _ in range(20):
            aid = env.agent_selection
            if env.terminations.get(aid, True):
                env.step(None)
                continue
            mask = env.infos[aid]["action_mask"]
            tm = mask["type_mask"]
            ftm = mask["target_mask"]
            char = env._battle.get_character(aid)
            action, _, _, _ = agent.select_action_hierarchical(
                char.character_class.value, env.observe(aid), tm, ftm
            )
            assert tm[action[0]], f"selected invalid type {action[0]}"
            assert ftm[action[0], action[1]], f"selected invalid target {action[1]} for type {action[0]}"
            env.step(np.array([action[0], action[1]]))
            if all(env.terminations.values()):
                break


class TestBufferDataIntegrity:
    def test_all_lists_same_length(self, setup):
        _, _, buf = setup
        for aid, d in buf._data.items():
            n = len(d["obs"])
            if n == 0:
                continue
            assert len(d["actions_type"]) == n
            assert len(d["rewards"]) == n
            assert len(d["values"]) == n
            assert len(d["dones"]) == n
            assert len(d["type_masks"]) == n
            assert len(d["target_masks"]) == n
            assert len(d["global_states"]) == n, f"{aid}: gs={len(d['global_states'])} vs {n}"
            assert len(d.get("class_names", [])) == n, f"{aid}: cn={len(d.get('class_names',[]))} vs {n}"

    def test_last_entry_has_done_true(self, setup):
        _, _, buf = setup
        for aid, d in buf._data.items():
            if len(d["obs"]) == 0:
                continue
            assert d["dones"][-1] == True, f"{aid}: last done={d['dones'][-1]}"

    def test_class_names_valid(self, setup):
        _, _, buf = setup
        valid = {"warrior", "mage", "cleric", "archer", "assassin"}
        for aid, d in buf._data.items():
            for cn in d.get("class_names", []):
                assert cn in valid, f"{aid}: invalid class '{cn}'"

    def test_log_probs_finite(self, setup):
        _, _, buf = setup
        for aid, d in buf._data.items():
            for lp in d["log_probs"]:
                assert np.isfinite(lp), f"{aid}: non-finite log_prob {lp}"


class TestGAEIntegrity:
    def test_advantages_and_returns_correct_length(self, setup):
        _, _, buf = setup
        buf.compute_returns()
        for aid, d in buf._data.items():
            n = len(d["obs"])
            if n == 0:
                continue
            assert len(d["advantages"]) == n
            assert len(d["returns"]) == n

    def test_no_nan_or_inf(self, setup):
        _, _, buf = setup
        buf.compute_returns()
        for d in buf._data.values():
            if not d["advantages"]:
                continue
            assert not np.isnan(d["advantages"]).any()
            assert not np.isinf(d["advantages"]).any()
            assert not any(np.isnan(r) or np.isinf(r) for r in d["returns"])


class TestPerClassBatching:
    def test_batches_separated_by_class(self, setup):
        _, _, buf = setup
        buf.compute_returns()
        bbc = buf.get_batches_by_class(64)
        valid = {"warrior", "mage", "cleric", "archer", "assassin"}
        for cn in bbc:
            assert cn in valid, f"invalid class '{cn}'"

    def test_batch_tensors_consistent(self, setup):
        _, _, buf = setup
        buf.compute_returns()
        bbc = buf.get_batches_by_class(64)
        for cn, batches in bbc.items():
            for batch in batches:
                bs = batch["obs"].shape[0]
                assert batch["actions_type"].shape[0] == bs
                assert batch["advantages"].shape[0] == bs
                assert batch["returns"].shape[0] == bs
                assert batch["old_log_probs"].shape[0] == bs


class TestPPORatios:
    def test_pre_update_ratio_is_one(self, setup):
        agent, _, buf = setup
        buf.compute_returns()
        bbc = buf.get_batches_by_class(64)
        for cn, batches in bbc.items():
            if not batches:
                continue
            batch = batches[0]
            policy = agent.policies[cn]
            with torch.no_grad():
                new_lp, _ = policy.evaluate_action(
                    batch["obs"], (batch["actions_type"], batch["actions_target"]),
                    batch["type_masks"], batch["target_masks"]
                )
            ratio = torch.exp(new_lp - batch["old_log_probs"])
            assert torch.allclose(ratio, torch.ones_like(ratio), atol=1e-5), \
                f"{cn}: ratio mean={ratio.mean():.6f}, std={ratio.std():.6f}"

    def test_update_changes_weights(self, setup):
        agent, _, buf = setup
        w_before = {n: p.type_head.weight.data.clone() for n, p in agent.policies.items()}
        result = agent.update(buf)
        assert np.isfinite(result["policy_loss"])
        assert np.isfinite(result["value_loss"])
        assert result["entropy"] > 0
        changed = any(
            (p.type_head.weight.data - w_before[n]).abs().mean().item() > 0
            for n, p in agent.policies.items()
        )
        assert changed, "no policy weights changed after update"


class TestTerminalRewards:
    def test_losers_see_negative_reward(self):
        agent = MAPPOAgent()
        trainer = Trainer(agent, seed=99)
        losers_total = 0
        losers_with_defeat = 0
        for seed in range(15):
            buf = RolloutBuffer()
            env = ArenaEnv(team_size=1)
            trainer._rng.seed(seed * 777)
            stats = trainer.collect_rollout(env, buf)
            winner = stats["winner"]
            if not winner:
                continue
            for aid, d in buf._data.items():
                if len(d["obs"]) == 0:
                    continue
                team = "team_a" if "team_a" in aid else "team_b"
                if team != winner:
                    losers_total += 1
                    if sum(d["rewards"]) < 0:
                        losers_with_defeat += 1
        assert losers_total > 0, "no losers found in 15 episodes"
        assert losers_with_defeat == losers_total, \
            f"only {losers_with_defeat}/{losers_total} losers see negative reward"
