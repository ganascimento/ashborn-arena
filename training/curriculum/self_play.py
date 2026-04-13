from __future__ import annotations

import copy
import random as _random

from training.agents.mappo import MAPPOAgent


class SelfPlayPool:
    def __init__(self, max_size: int = 10) -> None:
        self._max_size = max_size
        self._snapshots: list[dict[str, dict]] = []

    @property
    def size(self) -> int:
        return len(self._snapshots)

    def add_snapshot(self, agent: MAPPOAgent) -> None:
        snapshot = {
            name: copy.deepcopy(policy.state_dict())
            for name, policy in agent.policies.items()
        }
        self._snapshots.append(snapshot)
        if len(self._snapshots) > self._max_size:
            self._snapshots.pop(0)

    def sample_opponent(self) -> dict[str, dict]:
        return _random.choice(self._snapshots)

    def load_into(self, agent: MAPPOAgent, snapshot: dict[str, dict]) -> None:
        for name, state_dict in snapshot.items():
            if name in agent.policies:
                agent.policies[name].load_state_dict(state_dict)
