import torch
import numpy as np
import pytest

from training.agents.networks import CriticNetwork, PolicyNetwork


OBS_SIZE = 162
NUM_TYPES = 10
NUM_TARGETS = 80
BATCH = 4


class TestPolicyNetworkCreation:
    def test_creates_with_defaults(self):
        net = PolicyNetwork(OBS_SIZE, NUM_TYPES, NUM_TARGETS)
        assert net is not None

    def test_has_trainable_params(self):
        net = PolicyNetwork(OBS_SIZE, NUM_TYPES, NUM_TARGETS)
        total = sum(p.numel() for p in net.parameters() if p.requires_grad)
        assert total > 0

    def test_hidden_size_128(self):
        net = PolicyNetwork(OBS_SIZE, NUM_TYPES, NUM_TARGETS, hidden_size=128)
        assert sum(p.numel() for p in net.parameters()) > 0


class TestPolicyNetworkForward:
    def test_output_shapes(self):
        net = PolicyNetwork(OBS_SIZE, NUM_TYPES, NUM_TARGETS)
        obs = torch.randn(BATCH, OBS_SIZE)
        type_mask = torch.ones(BATCH, NUM_TYPES, dtype=torch.bool)
        target_mask = torch.ones(BATCH, NUM_TARGETS, dtype=torch.bool)
        type_logits, target_logits = net(obs, type_mask, target_mask)
        assert type_logits.shape == (BATCH, NUM_TYPES)
        assert target_logits.shape == (BATCH, NUM_TARGETS)

    def test_masking_sets_low_logits(self):
        net = PolicyNetwork(OBS_SIZE, NUM_TYPES, NUM_TARGETS)
        obs = torch.randn(1, OBS_SIZE)
        type_mask = torch.zeros(1, NUM_TYPES, dtype=torch.bool)
        type_mask[0, 8] = True
        target_mask = torch.ones(1, NUM_TARGETS, dtype=torch.bool)
        type_logits, _ = net(obs, type_mask, target_mask)
        assert type_logits[0, 0].item() < -1e6
        assert type_logits[0, 8].item() > -1e6

    def test_target_masking(self):
        net = PolicyNetwork(OBS_SIZE, NUM_TYPES, NUM_TARGETS)
        obs = torch.randn(1, OBS_SIZE)
        type_mask = torch.ones(1, NUM_TYPES, dtype=torch.bool)
        target_mask = torch.zeros(1, NUM_TARGETS, dtype=torch.bool)
        target_mask[0, 5] = True
        _, target_logits = net(obs, type_mask, target_mask)
        assert target_logits[0, 0].item() < -1e6
        assert target_logits[0, 5].item() > -1e6


class TestPolicyNetworkActions:
    def test_get_action_returns_tuple(self):
        net = PolicyNetwork(OBS_SIZE, NUM_TYPES, NUM_TARGETS)
        obs = torch.randn(1, OBS_SIZE)
        type_mask = torch.ones(1, NUM_TYPES, dtype=torch.bool)
        target_mask = torch.ones(1, NUM_TARGETS, dtype=torch.bool)
        action, log_prob, entropy = net.get_action(obs, type_mask, target_mask)
        assert len(action) == 2
        assert 0 <= action[0].item() < NUM_TYPES
        assert 0 <= action[1].item() < NUM_TARGETS
        assert log_prob.shape == (1,)
        assert entropy.shape == (1,)

    def test_evaluate_action(self):
        net = PolicyNetwork(OBS_SIZE, NUM_TYPES, NUM_TARGETS)
        obs = torch.randn(BATCH, OBS_SIZE)
        type_mask = torch.ones(BATCH, NUM_TYPES, dtype=torch.bool)
        target_mask = torch.ones(BATCH, NUM_TARGETS, dtype=torch.bool)
        actions = (torch.randint(0, NUM_TYPES, (BATCH,)), torch.randint(0, NUM_TARGETS, (BATCH,)))
        log_prob, entropy = net.evaluate_action(obs, actions, type_mask, target_mask)
        assert log_prob.shape == (BATCH,)
        assert entropy.shape == (BATCH,)

    def test_masked_action_respects_mask(self):
        net = PolicyNetwork(OBS_SIZE, NUM_TYPES, NUM_TARGETS)
        obs = torch.randn(1, OBS_SIZE)
        type_mask = torch.zeros(1, NUM_TYPES, dtype=torch.bool)
        type_mask[0, 8] = True
        target_mask = torch.zeros(1, NUM_TARGETS, dtype=torch.bool)
        target_mask[0, 0] = True
        for _ in range(10):
            action, _, _ = net.get_action(obs, type_mask, target_mask)
            assert action[0].item() == 8
            assert action[1].item() == 0


class TestCriticNetwork:
    def test_creates(self):
        global_size = OBS_SIZE * 6
        net = CriticNetwork(global_size)
        assert net is not None

    def test_has_trainable_params(self):
        net = CriticNetwork(OBS_SIZE * 6)
        total = sum(p.numel() for p in net.parameters() if p.requires_grad)
        assert total > 0

    def test_output_shape(self):
        global_size = OBS_SIZE * 6
        net = CriticNetwork(global_size)
        state = torch.randn(BATCH, global_size)
        value = net(state)
        assert value.shape == (BATCH, 1)

    def test_hidden_size_256(self):
        net = CriticNetwork(OBS_SIZE * 6, hidden_size=256)
        assert sum(p.numel() for p in net.parameters()) > 0
