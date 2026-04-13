from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

from training.agents.buffer import RolloutBuffer
from training.agents.networks import CriticNetwork, PolicyNetwork
from training.environment.observations import OBS_TOTAL_SIZE

_CLASS_NAMES = ["warrior", "mage", "cleric", "archer", "assassin"]


class MAPPOAgent:
    def __init__(
        self,
        obs_size: int = OBS_TOTAL_SIZE,
        num_action_types: int = 10,
        num_targets: int = 80,
        lr: float = 3e-4,
        clip_range: float = 0.2,
        entropy_coeff: float = 0.01,
        value_coeff: float = 0.5,
        max_grad_norm: float = 0.5,
        epochs: int = 4,
    ) -> None:
        self.policies: dict[str, PolicyNetwork] = {
            name: PolicyNetwork(obs_size, num_action_types, num_targets)
            for name in _CLASS_NAMES
        }
        self.critic = CriticNetwork(obs_size)

        self._clip_range = clip_range
        self._entropy_coeff = entropy_coeff
        self._value_coeff = value_coeff
        self._max_grad_norm = max_grad_norm
        self._epochs = epochs
        self._obs_size = obs_size
        self._num_action_types = num_action_types
        self._num_targets = num_targets

        all_params = []
        for policy in self.policies.values():
            all_params.extend(policy.parameters())
        all_params.extend(self.critic.parameters())
        self._optimizer = torch.optim.Adam(all_params, lr=lr)

    def select_action(
        self,
        class_name: str,
        obs: np.ndarray,
        type_mask: np.ndarray,
        target_mask: np.ndarray,
    ) -> tuple[tuple[int, int], float, float]:
        policy = self.policies[class_name]
        obs_t = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)
        tm = torch.tensor(type_mask, dtype=torch.bool).unsqueeze(0)
        trgm = torch.tensor(target_mask, dtype=torch.bool).unsqueeze(0)

        with torch.no_grad():
            action, log_prob, entropy = policy.get_action(obs_t, tm, trgm)

        return (
            (action[0].item(), action[1].item()),
            log_prob.item(),
            entropy.item(),
        )

    def select_action_hierarchical(
        self,
        class_name: str,
        obs: np.ndarray,
        type_mask: np.ndarray,
        full_target_mask: np.ndarray,
    ) -> tuple[tuple[int, int], float, float, np.ndarray]:
        policy = self.policies[class_name]
        obs_t = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)
        tm = torch.tensor(type_mask, dtype=torch.bool).unsqueeze(0)
        ftm = torch.tensor(full_target_mask, dtype=torch.bool).unsqueeze(0)

        with torch.no_grad():
            action, log_prob, entropy, used_mask = policy.get_action_hierarchical(
                obs_t, tm, ftm
            )

        return (
            (action[0].item(), action[1].item()),
            log_prob.item(),
            entropy.item(),
            used_mask.squeeze(0).numpy(),
        )

    def get_value(self, obs: np.ndarray) -> float:
        obs_t = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            value = self.critic(obs_t)
        return value.item()

    def update(self, buffer: RolloutBuffer) -> dict[str, float]:
        buffer.compute_returns()
        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy = 0.0
        n_updates = 0

        for _ in range(self._epochs):
            batches_by_class = buffer.get_batches_by_class(batch_size=64)
            for name, policy in self.policies.items():
                class_batches = batches_by_class.get(name, [])
                for batch in class_batches:
                    obs = batch["obs"]
                    actions_type = batch["actions_type"]
                    actions_target = batch["actions_target"]
                    old_log_probs = batch["old_log_probs"]
                    advantages = batch["advantages"]
                    returns = batch["returns"]
                    type_masks = batch["type_masks"]
                    target_masks = batch["target_masks"]

                    adv_batch = advantages
                    if adv_batch.numel() > 1 and adv_batch.std() > 1e-8:
                        adv_batch = (adv_batch - adv_batch.mean()) / (
                            adv_batch.std() + 1e-8
                        )

                    new_log_probs, new_entropy = policy.evaluate_action(
                        obs,
                        (actions_type, actions_target),
                        type_masks,
                        target_masks,
                    )
                    ratio = torch.exp(new_log_probs - old_log_probs)
                    surr1 = ratio * adv_batch
                    surr2 = (
                        torch.clamp(ratio, 1 - self._clip_range, 1 + self._clip_range)
                        * adv_batch
                    )
                    policy_loss = -torch.min(surr1, surr2).mean()
                    entropy_bonus = new_entropy.mean()

                    values = self.critic(obs).squeeze(-1)
                    value_loss = nn.functional.mse_loss(values, returns)

                    loss = (
                        policy_loss
                        + self._value_coeff * value_loss
                        - self._entropy_coeff * entropy_bonus
                    )

                    self._optimizer.zero_grad(set_to_none=True)
                    loss.backward()
                    nn.utils.clip_grad_norm_(policy.parameters(), self._max_grad_norm)
                    nn.utils.clip_grad_norm_(
                        self.critic.parameters(), self._max_grad_norm
                    )
                    self._optimizer.step()

                    total_policy_loss += policy_loss.item()
                    total_value_loss += value_loss.item()
                    total_entropy += entropy_bonus.item()
                    n_updates += 1

        return {
            "policy_loss": total_policy_loss / max(n_updates, 1),
            "value_loss": total_value_loss / max(n_updates, 1),
            "entropy": total_entropy / max(n_updates, 1),
        }

    def save(self, directory: str) -> None:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        for name, policy in self.policies.items():
            torch.save(policy.state_dict(), path / f"{name}.pt")
        torch.save(self.critic.state_dict(), path / "critic.pt")

    def load(self, directory: str) -> None:
        path = Path(directory)
        for name, policy in self.policies.items():
            policy.load_state_dict(torch.load(path / f"{name}.pt", weights_only=True))
        self.critic.load_state_dict(torch.load(path / "critic.pt", weights_only=True))
