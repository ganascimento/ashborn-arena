from __future__ import annotations

import json
import random as _random
from pathlib import Path

import numpy as np

from training.agents.buffer import RolloutBuffer
from training.agents.mappo import MAPPOAgent
from training.curriculum.logger import TrainingLogger
from training.curriculum.phases import PhaseConfig
from training.curriculum.self_play import SelfPlayPool
from training.environment.arena_env import ArenaEnv
from training.environment.rewards import REWARD_DEFEAT, REWARD_VICTORY


def _save_meta(directory: str, episodes: int, updates: int) -> None:
    path = Path(directory) / "meta.json"
    path.write_text(json.dumps({"episodes": episodes, "updates": updates}))


def _load_meta(directory: str) -> dict:
    path = Path(directory) / "meta.json"
    if path.exists():
        return json.loads(path.read_text())
    return {"episodes": 0, "updates": 0}


class Trainer:
    def __init__(
        self, agent: MAPPOAgent, seed: int = 42, log_dir: str = "logs"
    ) -> None:
        self._agent = agent
        self._seed = seed
        self._rng = _random.Random(seed)
        self._episode_count = 0
        self.logger = TrainingLogger(log_dir=log_dir)

    def collect_rollout(self, env: ArenaEnv, buffer: RolloutBuffer) -> dict:
        seed = self._rng.randint(0, 2**31)
        env.reset(seed=seed)

        total_reward: dict[str, float] = {}
        steps = 0
        pending_rewards: dict[str, float] = {a: 0.0 for a in env.agents}
        agents_with_done: set[str] = set()

        while not all(env.terminations.values()):
            agent_id = env.agent_selection
            if env.terminations.get(agent_id, True):
                env.step(None)
                continue

            obs = env.observe(agent_id)
            mask = env.infos[agent_id]["action_mask"]
            type_mask = mask["type_mask"]
            full_target_mask = mask["target_mask"]

            valid_type_idx = np.where(type_mask)[0]
            if len(valid_type_idx) == 0:
                env.step(np.array([8, 0]))
                continue

            char = env._battle.get_character(agent_id)
            class_name = char.character_class.value

            accumulated = pending_rewards.get(agent_id, 0.0)
            pending_rewards[agent_id] = 0.0

            action, log_prob, entropy, used_target_mask = (
                self._agent.select_action_hierarchical(
                    class_name,
                    obs,
                    type_mask,
                    full_target_mask,
                )
            )

            value = self._agent.get_value(obs)

            env.step(np.array([action[0], action[1]]))

            step_reward = env.rewards.get(agent_id, 0.0)
            reward = accumulated + step_reward
            done = env.terminations.get(agent_id, False)

            for other_id in env.agents:
                if other_id != agent_id:
                    other_r = env.rewards.get(other_id, 0.0)
                    if other_r != 0.0:
                        pending_rewards[other_id] = (
                            pending_rewards.get(other_id, 0.0) + other_r
                        )

            buffer.add(
                agent_id=agent_id,
                obs=obs,
                action=action,
                log_prob=log_prob,
                reward=reward,
                value=value,
                done=done,
                type_mask=type_mask,
                target_mask=used_target_mask,
                class_name=class_name,
            )

            if done:
                agents_with_done.add(agent_id)

            total_reward[agent_id] = total_reward.get(agent_id, 0.0) + reward
            steps += 1

            if steps > 1000:
                break

        winner = env._battle.check_victory() if env._battle else None

        for agent_id in env.possible_agents:
            if agent_id in agents_with_done:
                continue
            if buffer.size(agent_id) == 0:
                continue

            terminal_reward = pending_rewards.get(agent_id, 0.0)
            team = "team_a" if "team_a" in agent_id else "team_b"
            if winner:
                if team == winner:
                    terminal_reward += REWARD_VICTORY
                else:
                    terminal_reward += REWARD_DEFEAT

            d = buffer._data[agent_id]
            if d["rewards"]:
                d["rewards"][-1] += terminal_reward
                d["dones"][-1] = True
            total_reward[agent_id] = total_reward.get(agent_id, 0.0) + terminal_reward

        return {
            "winner": winner,
            "steps": steps,
            "total_reward": total_reward,
        }

    def train_phase(self, phase: PhaseConfig, pool: SelfPlayPool) -> dict:
        episode_offset = 0
        update_offset = 0
        if phase.load_from:
            try:
                self._agent.load(phase.load_from)
                meta = _load_meta(phase.load_from)
                episode_offset = meta["episodes"]
                update_offset = meta["updates"]
            except FileNotFoundError:
                pass

        self.logger.start_phase(
            phase.phase_number,
            phase.team_sizes,
            phase.episodes,
            episode_offset=episode_offset,
            update_offset=update_offset,
        )

        buffer = RolloutBuffer()
        total_episodes = 0
        total_wins = {"team_a": 0, "team_b": 0, "draw": 0}

        for ep in range(phase.episodes):
            team_size = self._rng.choice(phase.team_sizes)
            env = ArenaEnv(team_size=team_size)

            stats = self.collect_rollout(env, buffer)
            total_episodes += 1

            winner = stats.get("winner")
            if winner:
                total_wins[winner] = total_wins.get(winner, 0) + 1
            else:
                total_wins["draw"] += 1

            self.logger.log_episode(ep + 1, stats)

            if (ep + 1) % phase.update_interval == 0:
                result = self._agent.update(buffer)
                self.logger.log_update(result)
                buffer.clear()

            if (ep + 1) % phase.pool_interval == 0:
                pool.add_snapshot(self._agent)

        if buffer._data and any(buffer.size(aid) > 0 for aid in buffer._data):
            result = self._agent.update(buffer)
            self.logger.log_update(result)
            buffer.clear()

        if phase.checkpoint_dir:
            self._agent.save(phase.checkpoint_dir)
            _save_meta(
                phase.checkpoint_dir,
                episodes=episode_offset + total_episodes,
                updates=self.logger._update_count,
            )

        self.logger.end_phase(phase.checkpoint_dir)

        return {
            "episodes_completed": total_episodes,
            "wins": total_wins,
        }

    def run_curriculum(self, phases: list[PhaseConfig]) -> None:
        self.logger.start_training()
        pool = SelfPlayPool(max_size=10)
        for phase in phases:
            self.train_phase(phase, pool)
        self.logger.end_training()
