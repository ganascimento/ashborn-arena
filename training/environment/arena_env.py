from __future__ import annotations

import functools
import random as _random

import gymnasium
import numpy as np
from pettingzoo import AECEnv
from pettingzoo.utils import agent_selector

from engine.generation.map_generator import Biome
from engine.models.character import CharacterClass, CharacterState
from engine.systems.battle import BattleState
from training.environment.actions import (
    NUM_ACTION_TYPES,
    NUM_TARGETS,
    ActionType,
    compute_action_mask,
)
from training.environment.observations import OBS_TOTAL_SIZE, encode_observation
from training.environment.rewards import (
    LOOP_HISTORY_LEN,
    REWARD_IDLE_END_TURN,
    REWARD_LOOP_MOVE,
    REWARD_OFFENSIVE_HIT,
    REWARD_TIME_PENALTY,
    apply_terminal_rewards,
    compute_rewards,
)

_DEFAULT_BUILD = (2, 2, 2, 2, 2)
_ALL_CLASSES = list(CharacterClass)


class ArenaEnv(AECEnv):
    metadata = {"name": "arena_v0"}

    def __init__(self, team_size: int = 3, biome: Biome | None = None):
        super().__init__()
        self._team_size = team_size
        self._biome = biome
        self._battle: BattleState | None = None
        self._agent_teams: dict[str, str] = {}
        self._selector: agent_selector | None = None

        self.agents: list[str] = []
        self.possible_agents: list[str] = []
        self.rewards: dict[str, float] = {}
        self.terminations: dict[str, bool] = {}
        self.truncations: dict[str, bool] = {}
        self.infos: dict[str, dict] = {}
        self._cumulative_rewards: dict[str, float] = {}
        self.agent_selection: str = ""
        self._move_history: dict[str, list[tuple[int, int]]] = {}

    @functools.lru_cache(maxsize=None)
    def observation_space(self, agent: str) -> gymnasium.spaces.Space:
        return gymnasium.spaces.Box(
            low=-1.0, high=20.0, shape=(OBS_TOTAL_SIZE,), dtype=np.float32
        )

    @functools.lru_cache(maxsize=None)
    def action_space(self, agent: str) -> gymnasium.spaces.Space:
        return gymnasium.spaces.MultiDiscrete([NUM_ACTION_TYPES, NUM_TARGETS])

    def observe(self, agent: str) -> np.ndarray:
        if self._battle is None:
            return np.zeros(OBS_TOTAL_SIZE, dtype=np.float32)
        char = self._battle.get_character(agent)
        if char.state == CharacterState.DEAD:
            return np.zeros(OBS_TOTAL_SIZE, dtype=np.float32)
        return encode_observation(self._battle, agent)

    def reset(self, seed: int | None = None, options: dict | None = None) -> None:
        rng = _random.Random(seed)

        classes_a = rng.sample(_ALL_CLASSES, self._team_size)
        classes_b = rng.sample(_ALL_CLASSES, self._team_size)

        team_a_config = [(cls, _DEFAULT_BUILD) for cls in classes_a]
        team_b_config = [(cls, _DEFAULT_BUILD) for cls in classes_b]

        biome = self._biome or rng.choice(list(Biome))
        self._battle = BattleState.from_config(
            team_a_config, team_b_config, biome=biome, rng=rng
        )

        all_entities = self._battle.turn_order
        self.possible_agents = list(all_entities)
        self.agents = list(all_entities)

        self._agent_teams = {}
        for eid in self._battle.team_a_entities:
            self._agent_teams[eid] = "team_a"
        for eid in self._battle.team_b_entities:
            self._agent_teams[eid] = "team_b"

        self.rewards = {a: 0.0 for a in self.agents}
        self._cumulative_rewards = {a: 0.0 for a in self.agents}
        self.terminations = {a: False for a in self.agents}
        self.truncations = {a: False for a in self.agents}
        self.infos = {}
        self._move_history = {a: [] for a in self.agents}

        self._battle.process_turn_start()
        self._advance_to_active_agent()

        for a in self.agents:
            self._update_info(a)

        self.agent_selection = self._battle.current_agent

    def step(self, action: np.ndarray | None) -> None:
        if self._battle is None:
            return

        agent = self.agent_selection
        if self.terminations.get(agent, True) or self.truncations.get(agent, True):
            self._was_dead_step(action)
            return

        self.rewards = {a: 0.0 for a in self.agents}

        action_type = int(action[0]) if action is not None else ActionType.END_TURN
        target = int(action[1]) if action is not None else 0

        pre_action_mask = self.infos.get(agent, {}).get("action_mask")
        pre_action_pa = self._battle.get_pa(agent)

        events = self._battle.execute_action(action_type, target)

        loop_penalty = 0.0
        for ev in events:
            if ev.get("type") != "move" or ev.get("entity") != agent:
                continue
            to_pos = ev.get("to")
            if to_pos is None:
                continue
            tile = (to_pos.x, to_pos.y)
            history = self._move_history.setdefault(agent, [])
            if tile in history:
                loop_penalty += REWARD_LOOP_MOVE
            history.append(tile)
            if len(history) > LOOP_HISTORY_LEN:
                history.pop(0)

        offensive_bonus = 0.0
        is_offensive_action = (
            action_type == ActionType.BASIC_ATTACK
            or ActionType.ABILITY_1 <= action_type <= ActionType.ABILITY_5
            or action_type == ActionType.THROW
        )
        if is_offensive_action:
            for ev in events:
                etype = ev.get("type", "")
                if etype not in (
                    "basic_attack",
                    "ability",
                    "aoe_hit",
                    "chain_primary",
                    "chain_secondary",
                ):
                    continue
                if ev.get("attacker") != agent:
                    continue
                if ev.get("damage", 0) <= 0:
                    continue
                tgt = ev.get("target", "")
                if self._agent_teams.get(tgt, "") == self._agent_teams.get(agent, ""):
                    continue
                offensive_bonus = REWARD_OFFENSIVE_HIT
                break

        idle_penalty = 0.0
        if action_type in (ActionType.END_TURN, ActionType.PASS):
            if pre_action_pa >= 2 and pre_action_mask is not None:
                tm = pre_action_mask.get("type_mask")
                if tm is not None:
                    has_offensive = bool(
                        tm[ActionType.BASIC_ATTACK]
                        or tm[ActionType.ABILITY_1]
                        or tm[ActionType.ABILITY_2]
                        or tm[ActionType.ABILITY_3]
                        or tm[ActionType.ABILITY_4]
                        or tm[ActionType.ABILITY_5]
                    )
                    if has_offensive:
                        idle_penalty = REWARD_IDLE_END_TURN

        step_rewards = compute_rewards(
            events,
            agent,
            self._agent_teams.get(agent, ""),
            self._agent_teams,
            battle_state=self._battle,
        )
        for eid, r in step_rewards.items():
            if eid in self.rewards:
                self.rewards[eid] += r

        if agent in self.rewards:
            self.rewards[agent] += REWARD_TIME_PENALTY
            self.rewards[agent] += loop_penalty
            self.rewards[agent] += offensive_bonus
            self.rewards[agent] += idle_penalty

        winner = self._battle.check_victory()
        if winner:
            apply_terminal_rewards(self.rewards, winner, self._agent_teams)
            for a in self.agents:
                self.terminations[a] = True

        self._remove_dead_agents()

        extra_events: list[dict] = []
        events_seen = len(self._battle._events)
        if not all(self.terminations.values()):
            if action_type in (ActionType.END_TURN, ActionType.PASS):
                extra_events.extend(self._battle.process_turn_start())
                self._advance_to_active_agent()

            pa = (
                self._battle.get_pa(self._battle.current_agent)
                if not self._battle.is_over
                else 0
            )
            if pa <= 0 and not self._battle.is_over:
                extra_events.extend(self._battle.process_turn_end())
                self._battle._turn_manager.end_turn()
                extra_events.extend(self._battle.process_turn_start())
                self._advance_to_active_agent()

        indirect = self._battle._events[events_seen:]
        if indirect:
            extra_events.extend(indirect)

        if extra_events:
            extra_rewards = compute_rewards(
                extra_events,
                agent,
                self._agent_teams.get(agent, ""),
                self._agent_teams,
                battle_state=self._battle,
            )
            for eid, r in extra_rewards.items():
                if eid in self.rewards:
                    self.rewards[eid] += r

            winner = self._battle.check_victory()
            if winner:
                apply_terminal_rewards(self.rewards, winner, self._agent_teams)
                for a in self.agents:
                    self.terminations[a] = True
            self._remove_dead_agents()

        for a in self.agents:
            self._update_info(a)
            self._cumulative_rewards[a] = self._cumulative_rewards.get(
                a, 0.0
            ) + self.rewards.get(a, 0.0)

        if self.agents and not all(self.terminations.values()):
            self.agent_selection = self._battle.current_agent
        elif self.agents:
            self.agent_selection = self.agents[0]

    def _advance_to_active_agent(self) -> None:
        if self._battle is None or self._battle.is_over:
            return
        for _ in range(20):
            agent = self._battle.current_agent
            char = self._battle.get_character(agent)
            if char.state == CharacterState.ACTIVE:
                return
            if char.state == CharacterState.KNOCKED_OUT:
                self._battle.process_turn_start()
                continue
            if char.state == CharacterState.DEAD:
                if (
                    agent in self._battle.turn_order
                    and len(self._battle.turn_order) > 1
                ):
                    self._battle._turn_manager.end_turn()
                else:
                    return

    def _remove_dead_agents(self) -> None:
        for eid in list(self.agents):
            if eid in self._battle._characters:
                char = self._battle.get_character(eid)
                if char.state == CharacterState.DEAD:
                    self.terminations[eid] = True

    def _update_info(self, agent: str) -> None:
        if self._battle is None or self.terminations.get(agent, True):
            self.infos[agent] = {
                "action_mask": {
                    "type_mask": np.zeros(NUM_ACTION_TYPES, dtype=bool),
                    "target_mask": np.zeros(
                        (NUM_ACTION_TYPES, NUM_TARGETS), dtype=bool
                    ),
                }
            }
            return
        self.infos[agent] = {"action_mask": compute_action_mask(self._battle, agent)}

    def _was_dead_step(self, action) -> None:
        if self.agents:
            next_agents = [a for a in self.agents if not self.terminations.get(a, True)]
            if next_agents:
                self.agent_selection = next_agents[0]
            else:
                self.agent_selection = self.agents[0]
