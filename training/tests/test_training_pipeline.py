import os
import tempfile

import numpy as np
import pytest

from training.agents.buffer import RolloutBuffer
from training.agents.mappo import MAPPOAgent
from training.curriculum.phases import CURRICULUM_PHASES, PhaseConfig
from training.curriculum.self_play import SelfPlayPool
from training.curriculum.trainer import Trainer

OBS_SIZE = 162
GLOBAL_SIZE = OBS_SIZE * 6
NUM_TYPES = 10
NUM_TARGETS = 80


class TestCurriculumPhases:
    def test_has_4_phases(self):
        assert len(CURRICULUM_PHASES) == 4

    def test_phase_1_is_1v1_easy(self):
        p = CURRICULUM_PHASES[0]
        assert 1 in p.team_sizes
        assert p.checkpoint_dir == "models/easy"
        assert p.load_from is None

    def test_phase_2_loads_from_easy(self):
        p = CURRICULUM_PHASES[1]
        assert 2 in p.team_sizes
        assert p.load_from == "models/easy"

    def test_phase_3_saves_normal(self):
        p = CURRICULUM_PHASES[2]
        assert 3 in p.team_sizes
        assert p.checkpoint_dir == "models/normal"

    def test_phase_4_saves_hard(self):
        p = CURRICULUM_PHASES[3]
        assert p.checkpoint_dir == "models/hard"
        assert len(p.team_sizes) >= 2

    def test_each_phase_has_episodes(self):
        for p in CURRICULUM_PHASES:
            assert p.episodes > 0


class TestSelfPlayPool:
    def test_starts_empty(self):
        pool = SelfPlayPool(max_size=5)
        assert pool.size == 0

    def test_add_snapshot(self):
        pool = SelfPlayPool(max_size=5)
        agent = MAPPOAgent(obs_size=OBS_SIZE, global_state_size=GLOBAL_SIZE)
        pool.add_snapshot(agent)
        assert pool.size == 1

    def test_sample_opponent(self):
        pool = SelfPlayPool(max_size=5)
        agent = MAPPOAgent(obs_size=OBS_SIZE, global_state_size=GLOBAL_SIZE)
        pool.add_snapshot(agent)
        snapshot = pool.sample_opponent()
        assert snapshot is not None
        assert "warrior" in snapshot

    def test_max_size_respected(self):
        pool = SelfPlayPool(max_size=3)
        agent = MAPPOAgent(obs_size=OBS_SIZE, global_state_size=GLOBAL_SIZE)
        for _ in range(5):
            pool.add_snapshot(agent)
        assert pool.size == 3

    def test_load_into_agent(self):
        pool = SelfPlayPool(max_size=5)
        agent = MAPPOAgent(obs_size=OBS_SIZE, global_state_size=GLOBAL_SIZE)
        pool.add_snapshot(agent)
        snapshot = pool.sample_opponent()
        agent2 = MAPPOAgent(obs_size=OBS_SIZE, global_state_size=GLOBAL_SIZE)
        pool.load_into(agent2, snapshot)


class TestRolloutBufferGlobalState:
    def test_add_with_global_state(self):
        buf = RolloutBuffer()
        buf.add(
            agent_id="a",
            obs=np.zeros(OBS_SIZE, dtype=np.float32),
            action=(0, 0),
            log_prob=-1.0,
            reward=0.0,
            value=0.0,
            done=False,
            type_mask=np.ones(NUM_TYPES, dtype=bool),
            target_mask=np.ones(NUM_TARGETS, dtype=bool),
            global_state=np.zeros(GLOBAL_SIZE, dtype=np.float32),
        )
        assert buf.size("a") == 1

    def test_get_batches_includes_global_states(self):
        buf = RolloutBuffer()
        for i in range(32):
            buf.add(
                agent_id="a",
                obs=np.random.randn(OBS_SIZE).astype(np.float32),
                action=(0, 0),
                log_prob=-1.0,
                reward=0.1,
                value=0.5,
                done=i == 31,
                type_mask=np.ones(NUM_TYPES, dtype=bool),
                target_mask=np.ones(NUM_TARGETS, dtype=bool),
                global_state=np.random.randn(GLOBAL_SIZE).astype(np.float32),
            )
        buf.compute_returns()
        batches = list(buf.get_batches(batch_size=32))
        assert len(batches) >= 1
        assert "global_states" in batches[0]
        assert batches[0]["global_states"].shape[1] == GLOBAL_SIZE


class TestTrainer:
    def test_collect_rollout_fills_buffer(self):
        agent = MAPPOAgent(obs_size=OBS_SIZE, global_state_size=GLOBAL_SIZE)
        trainer = Trainer(agent, seed=42)
        buf = RolloutBuffer()
        from training.environment.arena_env import ArenaEnv
        env = ArenaEnv(team_size=1)
        stats = trainer.collect_rollout(env, buf)
        total = sum(buf.size(aid) for aid in buf._data)
        assert total > 0
        assert "winner" in stats

    def test_train_phase_runs(self):
        agent = MAPPOAgent(obs_size=OBS_SIZE, global_state_size=GLOBAL_SIZE)
        trainer = Trainer(agent, seed=42)
        phase = PhaseConfig(
            phase_number=1,
            team_sizes=[1],
            episodes=2,
            update_interval=2,
            pool_interval=2,
            checkpoint_dir=None,
            load_from=None,
        )
        pool = SelfPlayPool(max_size=3)
        stats = trainer.train_phase(phase, pool)
        assert "episodes_completed" in stats

    def test_checkpoint_saved(self):
        agent = MAPPOAgent(obs_size=OBS_SIZE, global_state_size=GLOBAL_SIZE)
        trainer = Trainer(agent, seed=42)
        with tempfile.TemporaryDirectory() as tmpdir:
            phase = PhaseConfig(
                phase_number=1,
                team_sizes=[1],
                episodes=2,
                update_interval=2,
                pool_interval=2,
                checkpoint_dir=tmpdir,
                load_from=None,
            )
            pool = SelfPlayPool(max_size=3)
            trainer.train_phase(phase, pool)
            assert os.path.exists(os.path.join(tmpdir, "warrior.pt"))
            assert os.path.exists(os.path.join(tmpdir, "mage.pt"))
            assert os.path.exists(os.path.join(tmpdir, "cleric.pt"))
            assert os.path.exists(os.path.join(tmpdir, "archer.pt"))
            assert os.path.exists(os.path.join(tmpdir, "assassin.pt"))
