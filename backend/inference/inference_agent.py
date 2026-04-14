import torch

from engine.systems.battle import BattleState
from training.agents.networks import PolicyNetwork
from training.environment.actions import compute_action_mask
from training.environment.observations import encode_observation


def get_inference_action(
    battle: BattleState, entity_id: str, policy: PolicyNetwork
) -> tuple[int, int]:
    obs = encode_observation(battle, entity_id)
    masks = compute_action_mask(battle, entity_id)

    obs_t = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)
    type_mask = torch.tensor(masks["type_mask"], dtype=torch.bool).unsqueeze(0)
    target_mask = torch.tensor(masks["target_mask"], dtype=torch.bool).unsqueeze(0)

    with torch.no_grad():
        (action_type, target), _, _, _ = policy.get_action_hierarchical(
            obs_t, type_mask, target_mask
        )

    return (action_type.item(), target.item())
