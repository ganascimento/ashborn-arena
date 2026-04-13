from __future__ import annotations

from collections import defaultdict

import numpy as np
import torch


class RolloutBuffer:
    def __init__(self) -> None:
        self._data: dict[str, dict[str, list]] = defaultdict(
            lambda: {
                "obs": [], "actions_type": [], "actions_target": [],
                "log_probs": [], "rewards": [], "values": [], "dones": [],
                "type_masks": [], "target_masks": [], "global_states": [],
                "advantages": [], "returns": [],
            }
        )

    def add(
        self,
        agent_id: str,
        obs: np.ndarray,
        action: tuple[int, int],
        log_prob: float,
        reward: float,
        value: float,
        done: bool,
        type_mask: np.ndarray,
        target_mask: np.ndarray,
        global_state: np.ndarray | None = None,
        class_name: str = "",
    ) -> None:
        d = self._data[agent_id]
        d["obs"].append(obs.copy())
        d["actions_type"].append(action[0])
        d["actions_target"].append(action[1])
        d["log_probs"].append(log_prob)
        d["rewards"].append(reward)
        d["values"].append(value)
        d["dones"].append(done)
        d["type_masks"].append(type_mask.copy())
        d["target_masks"].append(target_mask.copy())
        if global_state is not None:
            d["global_states"].append(global_state.copy())
        d.setdefault("class_names", []).append(class_name)

    def size(self, agent_id: str) -> int:
        if agent_id not in self._data:
            return 0
        return len(self._data[agent_id]["obs"])

    def get_agent_data(self, agent_id: str) -> dict[str, list]:
        return self._data[agent_id]

    def compute_returns(self, gamma: float = 0.99, gae_lambda: float = 0.95) -> None:
        for agent_id, d in self._data.items():
            n = len(d["rewards"])
            if n == 0:
                continue

            advantages = [0.0] * n
            last_gae = 0.0

            for t in reversed(range(n)):
                if t == n - 1:
                    next_value = 0.0
                    next_non_terminal = 0.0
                else:
                    next_value = d["values"][t + 1]
                    next_non_terminal = 1.0 - float(d["dones"][t])

                delta = d["rewards"][t] + gamma * next_value * next_non_terminal - d["values"][t]
                last_gae = delta + gamma * gae_lambda * next_non_terminal * last_gae
                advantages[t] = last_gae

            returns = [advantages[t] + d["values"][t] for t in range(n)]

            adv_arr = np.array(advantages, dtype=np.float32)
            std = adv_arr.std()
            if std > 1e-8:
                adv_arr = (adv_arr - adv_arr.mean()) / std
            else:
                adv_arr = adv_arr - adv_arr.mean()

            d["advantages"] = adv_arr.tolist()
            d["returns"] = returns

    def get_batches_by_class(self, batch_size: int = 64) -> dict[str, list[dict]]:
        by_class: dict[str, dict[str, list]] = {}

        for d in self._data.values():
            n = len(d["obs"])
            if n == 0 or not d["advantages"]:
                continue
            class_names = d.get("class_names", [""] * n)
            for i in range(n):
                cn = class_names[i] if i < len(class_names) else ""
                if cn not in by_class:
                    by_class[cn] = {
                        "obs": [], "actions_type": [], "actions_target": [],
                        "log_probs": [], "advantages": [], "returns": [],
                        "type_masks": [], "target_masks": [], "global_states": [],
                    }
                bc = by_class[cn]
                bc["obs"].append(d["obs"][i])
                bc["actions_type"].append(d["actions_type"][i])
                bc["actions_target"].append(d["actions_target"][i])
                bc["log_probs"].append(d["log_probs"][i])
                bc["advantages"].append(d["advantages"][i])
                bc["returns"].append(d["returns"][i])
                bc["type_masks"].append(d["type_masks"][i])
                bc["target_masks"].append(d["target_masks"][i])
                if i < len(d["global_states"]):
                    bc["global_states"].append(d["global_states"][i])

        result: dict[str, list[dict]] = {}
        for cn, pool in by_class.items():
            n = len(pool["obs"])
            if n == 0:
                continue
            has_global = len(pool["global_states"]) == n
            batches: list[dict] = []
            indices = np.random.permutation(n)
            for start in range(0, n, batch_size):
                end = min(start + batch_size, n)
                idx = indices[start:end]
                batch = {
                    "obs": torch.tensor(np.array([pool["obs"][i] for i in idx]), dtype=torch.float32),
                    "actions_type": torch.tensor([pool["actions_type"][i] for i in idx], dtype=torch.long),
                    "actions_target": torch.tensor([pool["actions_target"][i] for i in idx], dtype=torch.long),
                    "old_log_probs": torch.tensor([pool["log_probs"][i] for i in idx], dtype=torch.float32),
                    "advantages": torch.tensor([pool["advantages"][i] for i in idx], dtype=torch.float32),
                    "returns": torch.tensor([pool["returns"][i] for i in idx], dtype=torch.float32),
                    "type_masks": torch.tensor(np.array([pool["type_masks"][i] for i in idx]), dtype=torch.bool),
                    "target_masks": torch.tensor(np.array([pool["target_masks"][i] for i in idx]), dtype=torch.bool),
                }
                if has_global:
                    batch["global_states"] = torch.tensor(
                        np.array([pool["global_states"][i] for i in idx]), dtype=torch.float32
                    )
                batches.append(batch)
            result[cn] = batches
        return result

    def get_batches(self, batch_size: int = 64):
        all_obs, all_at, all_atrg = [], [], []
        all_lp, all_adv, all_ret = [], [], []
        all_tm, all_trgm, all_gs = [], [], []

        for d in self._data.values():
            n = len(d["obs"])
            if n == 0 or not d["advantages"]:
                continue
            all_obs.extend(d["obs"])
            all_at.extend(d["actions_type"])
            all_atrg.extend(d["actions_target"])
            all_lp.extend(d["log_probs"])
            all_adv.extend(d["advantages"])
            all_ret.extend(d["returns"])
            all_tm.extend(d["type_masks"])
            all_trgm.extend(d["target_masks"])
            all_gs.extend(d["global_states"])

        n = len(all_obs)
        if n == 0:
            return

        has_global = len(all_gs) == n
        indices = np.random.permutation(n)
        for start in range(0, n, batch_size):
            end = min(start + batch_size, n)
            idx = indices[start:end]
            batch = {
                "obs": torch.tensor(np.array([all_obs[i] for i in idx]), dtype=torch.float32),
                "actions_type": torch.tensor([all_at[i] for i in idx], dtype=torch.long),
                "actions_target": torch.tensor([all_atrg[i] for i in idx], dtype=torch.long),
                "old_log_probs": torch.tensor([all_lp[i] for i in idx], dtype=torch.float32),
                "advantages": torch.tensor([all_adv[i] for i in idx], dtype=torch.float32),
                "returns": torch.tensor([all_ret[i] for i in idx], dtype=torch.float32),
                "type_masks": torch.tensor(np.array([all_tm[i] for i in idx]), dtype=torch.bool),
                "target_masks": torch.tensor(np.array([all_trgm[i] for i in idx]), dtype=torch.bool),
            }
            if has_global:
                batch["global_states"] = torch.tensor(
                    np.array([all_gs[i] for i in idx]), dtype=torch.float32
                )
            yield batch

    def clear(self) -> None:
        self._data.clear()
