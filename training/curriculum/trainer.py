from __future__ import annotations

import json
import random as _random
from pathlib import Path

import numpy as np
import torch

from training.agents.buffer import RolloutBuffer
from training.agents.mappo import MAPPOAgent
from training.curriculum.logger import TrainingLogger
from training.curriculum.phases import PhaseConfig
from training.curriculum.self_play import SelfPlayPool
from training.environment.arena_env import ArenaEnv
from training.environment.observations import encode_global_state


def _save_meta(directory: str, episodes: int, updates: int) -> None:
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    (path / "meta.json").write_text(
        json.dumps({"episodes": episodes, "updates": updates})
    )


def _load_meta(directory: str) -> dict:
    path = Path(directory) / "meta.json"
    if path.exists():
        return json.loads(path.read_text())
    return {"episodes": 0, "updates": 0}


def _resume_dir(phase: PhaseConfig) -> str:
    return phase.checkpoint_dir or f"models/_phase_{phase.phase_number}"


class Trainer:
    def __init__(
        self,
        agent: MAPPOAgent,
        seed: int = 42,
        log_dir: str = "logs",
        eval_interval: int = 1000,
        eval_episodes: int = 50,
        entropy_initial: float = 0.05,
        entropy_final: float = 0.005,
    ) -> None:
        self._agent = agent
        self._seed = seed
        self._rng = _random.Random(seed)
        self._eval_rng = _random.Random(seed + 1)
        np.random.seed(seed)
        torch.manual_seed(seed)
        self._episode_count = 0
        self._eval_interval = eval_interval
        self._eval_episodes = eval_episodes
        self._entropy_initial = entropy_initial
        self._entropy_final = entropy_final
        self.logger = TrainingLogger(log_dir=log_dir)

    def _sample_opponent_agent(self, pool: SelfPlayPool) -> MAPPOAgent | None:
        if pool.size == 0:
            return None

        opponent = MAPPOAgent(
            obs_size=self._agent._obs_size,
            global_state_size=self._agent._global_state_size,
            num_action_types=self._agent._num_action_types,
            num_targets=self._agent._num_targets,
        )
        pool.load_into(opponent, pool.sample_opponent())
        return opponent

    def collect_rollout(
        self,
        env: ArenaEnv,
        buffer: RolloutBuffer,
        opponent_agent: MAPPOAgent | None = None,
        opponent_team: str = "team_b",
    ) -> dict:
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

            team = env._agent_teams.get(agent_id, "")
            acting_agent = (
                opponent_agent
                if team == opponent_team and opponent_agent is not None
                else self._agent
            )
            should_train = acting_agent is self._agent

            accumulated = pending_rewards.get(agent_id, 0.0) if should_train else 0.0
            if should_train:
                pending_rewards[agent_id] = 0.0

            action, log_prob, entropy, used_target_mask = (
                acting_agent.select_action_hierarchical(
                    class_name,
                    obs,
                    type_mask,
                    full_target_mask,
                )
            )

            global_state = encode_global_state(env._battle)
            value = self._agent.get_value(global_state) if should_train else 0.0

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

            if should_train:
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
                    global_state=global_state,
                    class_name=class_name,
                )

            if done and should_train:
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

    def evaluate(self, team_size: int, n_episodes: int) -> dict:
        wins_a = 0
        wins_b = 0
        draws = 0
        total_steps = 0

        for _ in range(n_episodes):
            seed = self._eval_rng.randint(0, 2**31)
            env = ArenaEnv(team_size=team_size)
            env.reset(seed=seed)
            steps = 0

            while not all(env.terminations.values()):
                agent_id = env.agent_selection
                if env.terminations.get(agent_id, True):
                    env.step(None)
                    continue

                mask = env.infos[agent_id]["action_mask"]
                type_mask = mask["type_mask"]
                full_target_mask = mask["target_mask"]

                valid_type_idx = np.where(type_mask)[0]
                if len(valid_type_idx) == 0:
                    env.step(np.array([8, 0]))
                    steps += 1
                    continue

                team = env._agent_teams.get(agent_id, "")
                if team == "team_a":
                    obs = env.observe(agent_id)
                    char = env._battle.get_character(agent_id)
                    class_name = char.character_class.value
                    action, _, _, _ = self._agent.select_action_hierarchical(
                        class_name,
                        obs,
                        type_mask,
                        full_target_mask,
                        deterministic=True,
                    )
                    env.step(np.array([action[0], action[1]]))
                else:
                    a_type = int(self._eval_rng.choice(valid_type_idx.tolist()))
                    target_mask = full_target_mask[a_type]
                    valid_targets = np.where(target_mask)[0]
                    if len(valid_targets) == 0:
                        a_target = 0
                    else:
                        a_target = int(
                            self._eval_rng.choice(valid_targets.tolist())
                        )
                    env.step(np.array([a_type, a_target]))

                steps += 1
                if steps > 1000:
                    break

            winner = env._battle.check_victory() if env._battle else None
            if winner == "team_a":
                wins_a += 1
            elif winner == "team_b":
                wins_b += 1
            else:
                draws += 1
            total_steps += steps

        n = max(n_episodes, 1)
        return {
            "n_episodes": n_episodes,
            "team_size": team_size,
            "win_rate": wins_a / n,
            "loss_rate": wins_b / n,
            "draw_rate": draws / n,
            "avg_steps": total_steps / n,
        }

    def _entropy_for_progress(self, progress: float) -> float:
        progress = max(0.0, min(1.0, progress))
        return (
            self._entropy_initial
            + (self._entropy_final - self._entropy_initial) * progress
        )

    def train_phase(self, phase: PhaseConfig, pool: SelfPlayPool) -> dict:
        resume_dir = _resume_dir(phase)
        episode_offset = 0
        update_offset = 0
        resumed = False

        if (Path(resume_dir) / "meta.json").exists():
            try:
                self._agent.load(resume_dir)
                meta = _load_meta(resume_dir)
                episode_offset = meta.get("episodes", 0)
                update_offset = meta.get("updates", 0)
                resumed = True
            except FileNotFoundError:
                pass
            except RuntimeError as exc:
                print(
                    f"  [warn] Could not resume from {resume_dir}: incompatible "
                    f"checkpoint ({exc.__class__.__name__}). Starting phase from scratch."
                )

        if not resumed and phase.load_from:
            try:
                self._agent.load(phase.load_from)
            except FileNotFoundError:
                pass
            except RuntimeError as exc:
                print(
                    f"  [warn] Could not load from {phase.load_from}: incompatible "
                    f"checkpoint ({exc.__class__.__name__}). Starting from random init."
                )

        if episode_offset >= phase.episodes:
            print(
                f"\nPhase {phase.phase_number} already complete "
                f"({episode_offset}/{phase.episodes} episodes). Skipping."
            )
            return {"episodes_completed": 0, "wins": {}}

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

        for ep in range(episode_offset, phase.episodes):
            team_size = self._rng.choice(phase.team_sizes)
            env = ArenaEnv(team_size=team_size)

            opponent_agent = self._sample_opponent_agent(pool)
            opponent_team = self._rng.choice(["team_a", "team_b"])
            stats = self.collect_rollout(
                env,
                buffer,
                opponent_agent=opponent_agent,
                opponent_team=opponent_team,
            )
            total_episodes += 1

            winner = stats.get("winner")
            if winner:
                total_wins[winner] = total_wins.get(winner, 0) + 1
            else:
                total_wins["draw"] += 1

            self.logger.log_episode(ep + 1, stats)

            if (ep + 1) % phase.update_interval == 0:
                progress = (ep + 1) / max(phase.episodes, 1)
                ent_coeff = self._entropy_for_progress(progress)
                result = self._agent.update(buffer, entropy_coeff=ent_coeff)
                result["entropy_coeff"] = ent_coeff
                self.logger.log_update(result)
                buffer.clear()

            if (ep + 1) % phase.pool_interval == 0:
                pool.add_snapshot(self._agent)
                self._agent.save(resume_dir)
                _save_meta(
                    resume_dir,
                    episodes=ep + 1,
                    updates=self.logger._update_count,
                )

            if self._eval_interval > 0 and (ep + 1) % self._eval_interval == 0:
                eval_team_size = self._rng.choice(phase.team_sizes)
                eval_result = self.evaluate(
                    team_size=eval_team_size,
                    n_episodes=self._eval_episodes,
                )
                self.logger.log_eval(eval_result)

        if buffer._data and any(buffer.size(aid) > 0 for aid in buffer._data):
            ent_coeff = self._entropy_for_progress(1.0)
            result = self._agent.update(buffer, entropy_coeff=ent_coeff)
            result["entropy_coeff"] = ent_coeff
            self.logger.log_update(result)
            buffer.clear()

        self._agent.save(resume_dir)
        _save_meta(
            resume_dir,
            episodes=phase.episodes,
            updates=self.logger._update_count,
        )

        if phase.checkpoint_dir and phase.checkpoint_dir != resume_dir:
            self._agent.save(phase.checkpoint_dir)
            _save_meta(
                phase.checkpoint_dir,
                episodes=phase.episodes,
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
