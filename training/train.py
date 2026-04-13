from __future__ import annotations

import argparse

from training.agents.mappo import MAPPOAgent
from training.curriculum.phases import CURRICULUM_PHASES, PhaseConfig
from training.curriculum.self_play import SelfPlayPool
from training.curriculum.trainer import Trainer


def main() -> None:
    parser = argparse.ArgumentParser(description="Ashborn Arena MAPPO Training")
    parser.add_argument("--phase", type=int, default=0, help="Run only phase N (1-4). 0 = all phases.")
    parser.add_argument("--episodes", type=int, default=0, help="Override episodes per phase. 0 = use defaults.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--log-dir", type=str, default="logs", help="Directory for training logs.")
    args = parser.parse_args()

    agent = MAPPOAgent()
    trainer = Trainer(agent, seed=args.seed, log_dir=args.log_dir)

    phases = list(CURRICULUM_PHASES)
    if args.episodes > 0:
        phases = [
            PhaseConfig(
                phase_number=p.phase_number,
                team_sizes=p.team_sizes,
                episodes=args.episodes,
                update_interval=p.update_interval,
                pool_interval=p.pool_interval,
                checkpoint_dir=p.checkpoint_dir,
                load_from=p.load_from,
            )
            for p in phases
        ]

    if args.phase > 0:
        phase_idx = args.phase - 1
        if 0 <= phase_idx < len(phases):
            pool = SelfPlayPool(max_size=10)
            trainer.logger.start_training()
            trainer.train_phase(phases[phase_idx], pool)
            trainer.logger.end_training()
        else:
            print(f"Invalid phase {args.phase}. Valid: 1-{len(phases)}")
    else:
        trainer.run_curriculum(phases)


if __name__ == "__main__":
    main()
