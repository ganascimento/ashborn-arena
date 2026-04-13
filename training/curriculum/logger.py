from __future__ import annotations

import json
import time
from collections import deque
from pathlib import Path


class TrainingLogger:
    def __init__(self, log_dir: str = "logs") -> None:
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = self._log_dir / "training.jsonl"
        self._phase_start: float = 0.0
        self._global_start: float = 0.0
        self._update_count = 0
        self._episode_count = 0
        self._current_phase = 0

        self._reward_window: deque[float] = deque(maxlen=50)
        self._steps_window: deque[int] = deque(maxlen=50)
        self._wins_window: deque[str] = deque(maxlen=50)

        self._phase_rewards: list[float] = []
        self._phase_steps: list[int] = []

    def start_training(self) -> None:
        self._global_start = time.time()
        self._log_file.write_text("")

    def start_phase(self, phase_number: int, team_sizes: list[int], episodes: int) -> None:
        self._current_phase = phase_number
        self._phase_start = time.time()
        self._phase_rewards.clear()
        self._phase_steps.clear()
        self._reward_window.clear()
        self._steps_window.clear()
        self._wins_window.clear()

        msg = f"Phase {phase_number} | teams={team_sizes} | {episodes} episodes"
        print(f"\n{'='*60}")
        print(f"  {msg}")
        print(f"{'='*60}")

    def log_episode(self, episode: int, stats: dict) -> None:
        self._episode_count += 1
        winner = stats.get("winner")
        steps = stats.get("steps", 0)
        total_r = sum(stats.get("total_reward", {}).values())

        self._reward_window.append(total_r)
        self._steps_window.append(steps)
        self._wins_window.append(winner or "draw")
        self._phase_rewards.append(total_r)
        self._phase_steps.append(steps)

    def log_update(self, update_result: dict, buffer_stats: dict | None = None) -> None:
        self._update_count += 1
        elapsed = time.time() - self._phase_start

        n = len(self._reward_window)
        avg_reward = sum(self._reward_window) / max(n, 1)
        avg_steps = sum(self._steps_window) / max(n, 1)
        win_a = sum(1 for w in self._wins_window if w == "team_a")
        win_b = sum(1 for w in self._wins_window if w == "team_b")
        draws = sum(1 for w in self._wins_window if w == "draw")

        record = {
            "phase": self._current_phase,
            "update": self._update_count,
            "episode": self._episode_count,
            "elapsed_s": round(elapsed, 1),
            "policy_loss": round(update_result.get("policy_loss", 0), 6),
            "value_loss": round(update_result.get("value_loss", 0), 2),
            "entropy": round(update_result.get("entropy", 0), 4),
            "avg_reward_50": round(avg_reward, 2),
            "avg_steps_50": round(avg_steps, 1),
            "wins_50": {"a": win_a, "b": win_b, "draw": draws},
        }
        if buffer_stats:
            record["buffer"] = buffer_stats

        with open(self._log_file, "a") as f:
            f.write(json.dumps(record) + "\n")

        ploss = update_result.get("policy_loss", 0)
        vloss = update_result.get("value_loss", 0)
        ent = update_result.get("entropy", 0)
        print(
            f"  [{self._update_count:4d}] "
            f"ep={self._episode_count:<5d} "
            f"r={avg_reward:6.1f} "
            f"steps={avg_steps:5.1f} "
            f"ploss={ploss:+.4f} "
            f"vloss={vloss:7.1f} "
            f"ent={ent:.3f} "
            f"w={win_a}/{win_b}/{draws} "
            f"({elapsed:.0f}s)"
        )

    def end_phase(self, checkpoint_dir: str | None = None) -> None:
        elapsed = time.time() - self._phase_start
        n = len(self._phase_rewards)
        avg_r = sum(self._phase_rewards) / max(n, 1)
        avg_s = sum(self._phase_steps) / max(n, 1)
        print(f"  Phase {self._current_phase} done: {n} eps, {elapsed:.0f}s, avg_r={avg_r:.1f}, avg_steps={avg_s:.1f}")
        if checkpoint_dir:
            print(f"  Checkpoint: {checkpoint_dir}/")

    def end_training(self) -> None:
        total = time.time() - self._global_start
        print(f"\nTraining complete: {self._episode_count} episodes, {self._update_count} updates, {total:.0f}s")
        print(f"Log: {self._log_file}")
