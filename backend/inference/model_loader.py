from pathlib import Path

import torch

from training.agents.networks import PolicyNetwork
from training.environment.actions import NUM_ACTION_TYPES, NUM_TARGETS
from training.environment.observations import OBS_TOTAL_SIZE

_CLASS_NAMES = ["warrior", "mage", "cleric", "archer", "assassin"]
_cache: dict[str, dict[str, PolicyNetwork]] = {}


def get_policies(difficulty: str) -> dict[str, PolicyNetwork] | None:
    if difficulty in _cache:
        return _cache[difficulty]
    path = Path("models") / difficulty
    if not path.is_dir():
        return None
    policies = {}
    for class_name in _CLASS_NAMES:
        pt_file = path / f"{class_name}.pt"
        if not pt_file.exists():
            return None
        policy = PolicyNetwork(OBS_TOTAL_SIZE, NUM_ACTION_TYPES, NUM_TARGETS)
        policy.load_state_dict(torch.load(pt_file, weights_only=True))
        policy.eval()
        policies[class_name] = policy
    _cache[difficulty] = policies
    return policies


def clear_cache() -> None:
    _cache.clear()
