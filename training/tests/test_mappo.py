import os
import tempfile

import numpy as np
import torch

from training.agents.buffer import RolloutBuffer
from training.agents.mappo import MAPPOAgent

OBS_SIZE = 162
NUM_TYPES = 10
NUM_TARGETS = 80


class TestRolloutBuffer:
    def _fill_buffer(self, buf, n_steps=20):
        for i in range(n_steps):
            buf.add(
                agent_id="agent_0",
                obs=np.random.randn(OBS_SIZE).astype(np.float32),
                action=(np.random.randint(NUM_TYPES), np.random.randint(NUM_TARGETS)),
                log_prob=-1.0,
                reward=0.1 * (i % 5),
                value=0.5,
                done=i == n_steps - 1,
                type_mask=np.ones(NUM_TYPES, dtype=bool),
                target_mask=np.ones(NUM_TARGETS, dtype=bool),
            )

    def test_add_stores_data(self):
        buf = RolloutBuffer()
        self._fill_buffer(buf, 5)
        assert buf.size("agent_0") == 5

    def test_compute_returns(self):
        buf = RolloutBuffer()
        self._fill_buffer(buf, 20)
        buf.compute_returns(gamma=0.99, gae_lambda=0.95)
        data = buf.get_agent_data("agent_0")
        assert "advantages" in data
        assert "returns" in data
        assert len(data["advantages"]) == 20

    def test_advantages_normalized(self):
        buf = RolloutBuffer()
        self._fill_buffer(buf, 50)
        buf.compute_returns()
        data = buf.get_agent_data("agent_0")
        advs = np.array(data["advantages"])
        assert abs(advs.mean()) < 0.5

    def test_get_batches(self):
        buf = RolloutBuffer()
        self._fill_buffer(buf, 64)
        buf.compute_returns()
        batches = list(buf.get_batches(batch_size=32))
        assert len(batches) >= 1
        batch = batches[0]
        assert "obs" in batch
        assert "actions_type" in batch
        assert "actions_target" in batch
        assert "old_log_probs" in batch
        assert "advantages" in batch
        assert "returns" in batch
        assert "type_masks" in batch
        assert "target_masks" in batch

    def test_clear(self):
        buf = RolloutBuffer()
        self._fill_buffer(buf, 10)
        buf.clear()
        assert buf.size("agent_0") == 0


class TestMAPPOAgent:
    def test_creates_with_5_policies(self):
        agent = MAPPOAgent(obs_size=OBS_SIZE, global_state_size=OBS_SIZE)
        assert len(agent.policies) == 5

    def test_creates_with_1_critic(self):
        agent = MAPPOAgent(obs_size=OBS_SIZE, global_state_size=OBS_SIZE)
        assert agent.critic is not None

    def test_select_action(self):
        agent = MAPPOAgent(obs_size=OBS_SIZE, global_state_size=OBS_SIZE)
        obs = np.random.randn(OBS_SIZE).astype(np.float32)
        type_mask = np.ones(NUM_TYPES, dtype=bool)
        target_mask = np.ones(NUM_TARGETS, dtype=bool)
        action, log_prob, entropy = agent.select_action(
            "warrior", obs, type_mask, target_mask
        )
        assert len(action) == 2
        assert 0 <= action[0] < NUM_TYPES
        assert 0 <= action[1] < NUM_TARGETS
        assert isinstance(log_prob, float)

    def test_select_action_all_classes(self):
        agent = MAPPOAgent(obs_size=OBS_SIZE, global_state_size=OBS_SIZE)
        obs = np.random.randn(OBS_SIZE).astype(np.float32)
        type_mask = np.ones(NUM_TYPES, dtype=bool)
        target_mask = np.ones(NUM_TARGETS, dtype=bool)
        for cls in ["warrior", "mage", "cleric", "archer", "assassin"]:
            action, _, _ = agent.select_action(cls, obs, type_mask, target_mask)
            assert len(action) == 2

    def test_get_value(self):
        agent = MAPPOAgent(obs_size=OBS_SIZE, global_state_size=OBS_SIZE)
        obs = np.random.randn(OBS_SIZE).astype(np.float32)
        value = agent.get_value(obs)
        assert isinstance(value, float)

    def test_update_runs(self):
        agent = MAPPOAgent(obs_size=OBS_SIZE, global_state_size=OBS_SIZE)
        buf = RolloutBuffer()
        for step in range(64):
            buf.add(
                agent_id="warrior_0",
                obs=np.random.randn(OBS_SIZE).astype(np.float32),
                action=(np.random.randint(NUM_TYPES), np.random.randint(NUM_TARGETS)),
                log_prob=-2.0,
                reward=0.1,
                value=0.5,
                done=step == 63,
                type_mask=np.ones(NUM_TYPES, dtype=bool),
                target_mask=np.ones(NUM_TARGETS, dtype=bool),
            )
        agent.update(buf)

    def test_save_and_load(self):
        agent = MAPPOAgent(obs_size=OBS_SIZE, global_state_size=OBS_SIZE)
        obs = torch.randn(1, OBS_SIZE)
        type_mask = torch.ones(1, NUM_TYPES, dtype=torch.bool)
        target_mask = torch.ones(1, NUM_TARGETS, dtype=torch.bool)

        with torch.no_grad():
            logits_before, _ = agent.policies["warrior"](obs, type_mask, target_mask)

        with tempfile.TemporaryDirectory() as tmpdir:
            agent.save(tmpdir)
            assert os.path.exists(os.path.join(tmpdir, "warrior.pt"))
            assert os.path.exists(os.path.join(tmpdir, "mage.pt"))
            assert os.path.exists(os.path.join(tmpdir, "critic.pt"))

            agent2 = MAPPOAgent(obs_size=OBS_SIZE, global_state_size=OBS_SIZE)
            agent2.load(tmpdir)

            with torch.no_grad():
                logits_after, _ = agent2.policies["warrior"](
                    obs, type_mask, target_mask
                )

            assert torch.allclose(logits_before, logits_after)
