from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhaseConfig:
    phase_number: int
    team_sizes: list[int]
    episodes: int
    update_interval: int
    pool_interval: int
    checkpoint_dir: str | None
    load_from: str | None


CURRICULUM_PHASES: list[PhaseConfig] = [
    PhaseConfig(
        phase_number=1,
        team_sizes=[1],
        episodes=2000,
        update_interval=10,
        pool_interval=50,
        checkpoint_dir="models/easy",
        load_from=None,
    ),
    PhaseConfig(
        phase_number=2,
        team_sizes=[2],
        episodes=2000,
        update_interval=10,
        pool_interval=50,
        checkpoint_dir=None,
        load_from="models/easy",
    ),
    PhaseConfig(
        phase_number=3,
        team_sizes=[3],
        episodes=2000,
        update_interval=10,
        pool_interval=50,
        checkpoint_dir="models/normal",
        load_from="models/easy",
    ),
    PhaseConfig(
        phase_number=4,
        team_sizes=[1, 2, 3],
        episodes=2000,
        update_interval=10,
        pool_interval=50,
        checkpoint_dir="models/hard",
        load_from="models/normal",
    ),
]
