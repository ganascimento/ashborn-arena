from __future__ import annotations

import torch
import torch.nn as nn
from torch.distributions import Categorical


class PolicyNetwork(nn.Module):
    def __init__(
        self,
        obs_size: int,
        num_action_types: int,
        num_targets: int,
        hidden_size: int = 128,
    ) -> None:
        super().__init__()
        self.shared = nn.Sequential(
            nn.Linear(obs_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
        )
        self.type_head = nn.Linear(hidden_size, num_action_types)
        self.target_head = nn.Linear(hidden_size, num_targets)

    def forward(
        self,
        obs: torch.Tensor,
        type_mask: torch.Tensor,
        target_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        features = self.shared(obs)
        type_logits = self.type_head(features)
        type_logits = type_logits.masked_fill(~type_mask, -1e8)
        target_logits = self.target_head(features)
        target_logits = target_logits.masked_fill(~target_mask, -1e8)
        return type_logits, target_logits

    def get_action(
        self,
        obs: torch.Tensor,
        type_mask: torch.Tensor,
        target_mask: torch.Tensor,
    ) -> tuple[tuple[torch.Tensor, torch.Tensor], torch.Tensor, torch.Tensor]:
        type_logits, target_logits = self.forward(obs, type_mask, target_mask)
        type_dist = Categorical(logits=type_logits)
        action_type = type_dist.sample()
        target_dist = Categorical(logits=target_logits)
        target = target_dist.sample()
        log_prob = type_dist.log_prob(action_type) + target_dist.log_prob(target)
        entropy = type_dist.entropy() + target_dist.entropy()
        return (action_type, target), log_prob, entropy

    def get_action_hierarchical(
        self,
        obs: torch.Tensor,
        type_mask: torch.Tensor,
        full_target_mask: torch.Tensor,
    ) -> tuple[tuple[torch.Tensor, torch.Tensor], torch.Tensor, torch.Tensor, torch.Tensor]:
        features = self.shared(obs)
        type_logits = self.type_head(features)
        type_logits = type_logits.masked_fill(~type_mask, -1e8)
        type_dist = Categorical(logits=type_logits)
        action_type = type_dist.sample()

        target_logits = self.target_head(features)
        selected_mask = full_target_mask[torch.arange(obs.shape[0]), action_type]
        no_valid = ~selected_mask.any(dim=-1)
        if no_valid.any():
            selected_mask[no_valid, 0] = True
        target_logits = target_logits.masked_fill(~selected_mask, -1e8)
        target_dist = Categorical(logits=target_logits)
        target = target_dist.sample()

        log_prob = type_dist.log_prob(action_type) + target_dist.log_prob(target)
        entropy = type_dist.entropy() + target_dist.entropy()
        return (action_type, target), log_prob, entropy, selected_mask

    def evaluate_action(
        self,
        obs: torch.Tensor,
        action: tuple[torch.Tensor, torch.Tensor],
        type_mask: torch.Tensor,
        target_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        type_logits, target_logits = self.forward(obs, type_mask, target_mask)
        type_dist = Categorical(logits=type_logits)
        target_dist = Categorical(logits=target_logits)
        log_prob = type_dist.log_prob(action[0]) + target_dist.log_prob(action[1])
        entropy = type_dist.entropy() + target_dist.entropy()
        return log_prob, entropy


class CriticNetwork(nn.Module):
    def __init__(self, global_state_size: int, hidden_size: int = 256) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(global_state_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 1),
        )

    def forward(self, global_state: torch.Tensor) -> torch.Tensor:
        return self.net(global_state)
