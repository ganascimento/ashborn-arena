# Tasks — Feature 31: MAPPO com Critic Centralizado, Reward por % HP, Annealing e Eval Loop

## Antes de Comecar

Leitura obrigatoria antes de implementar:

- `CLAUDE.md` — convencoes, stack
- `.specs/features/31_mappo_critic_centralizado_eval/spec.md` — criterios de aceitacao
- `.specs/design.md` secao 5 — arquitetura da IA, MAPPO
- `training/agents/mappo.py` — `MAPPOAgent`, ciclo de update
- `training/agents/networks.py` — `PolicyNetwork`, `CriticNetwork`
- `training/agents/buffer.py` — `RolloutBuffer` (ja tem campo `global_states` plumbado)
- `training/environment/observations.py` — `encode_global_state`, `GLOBAL_STATE_SIZE`
- `training/environment/rewards.py` — funcao de reward atual
- `training/curriculum/trainer.py` — loop de treino
- `training/curriculum/logger.py` — `TrainingLogger`
- `engine/systems/battle.py` — emissao de eventos `dot_tick`, `trap_triggered`, `chain_secondary` (Grupo F)
- `engine/models/effect.py` — `Effect.source_entity_id` (consumido em F1)

---

## Plano de Execucao

6 grupos. A, B/F, C podem ser paralelos (modulos diferentes), mas D e E dependem de A. Grupo F toca o engine + rewards.py — pode rodar em paralelo com B mas idealmente apos B (compartilham `compute_rewards`). Execucao sequencial recomendada para facilitar bisseccao em caso de regressao.

---

### Grupo A — Critic Centralizado

**Tarefa A1: `MAPPOAgent` com `global_state_size` separado**

1. Em `training/agents/mappo.py`:
   - Importar `GLOBAL_STATE_SIZE` de `training.environment.observations`
   - `__init__` aceita `global_state_size: int = GLOBAL_STATE_SIZE`
   - `self.critic = CriticNetwork(global_state_size)` (era `obs_size`)
   - Salvar `self._global_state_size = global_state_size`

**Tarefa A2: `get_value(global_state)`**

1. Trocar assinatura de `get_value(obs)` para `get_value(global_state: np.ndarray)`
2. Apenas renomeacao de variavel — semantica identica (tensor → critic forward)

**Tarefa A3: `update` consome global_states do batch**

1. `update(buffer, entropy_coeff: float | None = None)`:
   - `ent_coeff = self._entropy_coeff if entropy_coeff is None else entropy_coeff`
   - Dentro do loop de batches: `global_states = batch.get("global_states", obs)` (fallback para `obs` mantem testes unitarios funcionando)
   - `values = self.critic(global_states).squeeze(-1)`
   - Aplicar `ent_coeff` no termo de entropy do loss

**Tarefa A4: Trainer plumba global_state**

1. Em `training/curriculum/trainer.py`:
   - Importar `encode_global_state` de `training.environment.observations`
   - Em `collect_rollout`, antes de `value = self._agent.get_value(...)`:
     - `global_state = encode_global_state(env._battle)`
     - `value = self._agent.get_value(global_state)`
   - Em `buffer.add(...)`, passar `global_state=global_state`

---

### Grupo B — Reward Normalizado por % HP

**Tarefa B1: Constantes e helper**

1. Em `training/environment/rewards.py`:
   - Remover `REWARD_DAMAGE = 0.1` e `REWARD_HEAL = 0.1`
   - Adicionar `REWARD_DAMAGE_PCT = 2.0` e `REWARD_HEAL_PCT = 2.0`
   - Adicionar `_max_hp(battle_state, entity_id)` que retorna `battle_state.get_character(entity_id).max_hp` ou `100` (fallback se `None` ou erro)

**Tarefa B2: Assinatura de `compute_rewards`**

1. Adicionar parametro `battle_state: BattleState | None = None` ao final
2. Usar `TYPE_CHECKING` para o import de `BattleState` (evitar import circular)

**Tarefa B3: Aplicar normalizacao**

1. Em eventos `basic_attack` / `ability` / `opportunity_attack`:
   - `target = event.get("target", "")`
   - `target_max_hp = _max_hp(battle_state, target)`
   - `pct = min(damage / target_max_hp, 1.0)`
   - `rewards[attacker] += pct * REWARD_DAMAGE_PCT`
2. Em eventos `heal` / `self_heal` / `lifesteal`: idem com `REWARD_HEAL_PCT` e `target = event.get("target", healer)`
3. Em `hot_tick`: idem com `entity` como alvo, dividindo pelo `0.5` ja existente

**Tarefa B4: Atualizar caller**

1. Em `training/environment/arena_env.py`:
   - `compute_rewards(events, agent, team, all_agents, battle_state=self._battle)`

**Tarefa B5: Atualizar testes legados**

1. `training/tests/test_arena_env.py`:
   - Trocar import `REWARD_DAMAGE` → `REWARD_DAMAGE_PCT`
   - Trocar assert para `REWARD_DAMAGE_PCT == pytest.approx(2.0)`

---

### Grupo F — Reward Shaping Estendido (AoE, chain, DoT, traps, reflect)

**Tarefa F1: Engine — adicionar `attacker` a eventos de dano indireto**

1. Em `engine/systems/battle.py`:
   - Evento `dot_tick`: adicionar `"attacker": effect.source_entity_id`
   - Evento `trap_triggered`: adicionar `"attacker": caster_id`
   - Evento `chain_secondary`: adicionar `"attacker": attacker_id` (a variavel `attacker_id` ja esta no escopo de `_resolve_chain_damage`)

**Tarefa F2: Rewards — expandir lista de eventos com reward de dano**

1. Em `training/environment/rewards.py`, dentro do mesmo bloco `if etype in (...)`:
   - Adicionar `"aoe_hit"`, `"chain_primary"`, `"chain_secondary"`, `"dot_tick"`, `"trap_triggered"` a lista
   - Logica permanece identica: extrair `damage`, `attacker`, `target`, normalizar por `target.max_hp`

2. Adicionar novo branch para `reflect`:
   ```python
   elif etype == "reflect":
       damage = event.get("damage", 0)
       reflector = event.get("source", "")
       target = event.get("target", "")
       if damage > 0 and reflector in rewards:
           target_max_hp = _max_hp(battle_state, target)
           pct = min(damage / target_max_hp, 1.0)
           rewards[reflector] += pct * REWARD_DAMAGE_PCT
   ```

3. Eventos NAO incluidos (decisao de design):
   - `bleed`: dano passivo de timer de morte por knockout, sem atacante claro
   - `redirect`: defensivo, redirecionador absorve dano por aliado — sem reward por dano
   - `delayed_resolve`: marker de resolucao, dano real ja vem em eventos subsequentes (`aoe_hit`, `ability`)

---

### Grupo C — Entropy Annealing

**Tarefa C1: Trainer recebe parametros**

1. Em `Trainer.__init__`:
   - Adicionar `entropy_initial: float = 0.05` e `entropy_final: float = 0.005`
   - Salvar como atributos privados

**Tarefa C2: Funcao de annealing**

1. Adicionar metodo:
   ```python
   def _entropy_for_progress(self, progress: float) -> float:
       progress = max(0.0, min(1.0, progress))
       return self._entropy_initial + (self._entropy_final - self._entropy_initial) * progress
   ```

**Tarefa C3: Aplicar no train_phase**

1. Antes de `self._agent.update(buffer)` na loop principal:
   - `progress = (ep + 1) / max(phase.episodes, 1)` — progresso **absoluto**, nao relativo a `episode_offset`. Isso garante que ao retomar treino do meio (ex: ep_offset=10000/20000) a entropia continue de onde parou em vez de "pular de volta" pra `entropy_initial`
   - `ent_coeff = self._entropy_for_progress(progress)`
   - `result = self._agent.update(buffer, entropy_coeff=ent_coeff)`
   - `result["entropy_coeff"] = ent_coeff`
   - `self.logger.log_update(result)`

2. **Final flush do buffer ao fim da fase**: o bloco apos a loop principal que faz update final dos episodios remanescentes (`if buffer._data and any(buffer.size(...))`) tambem deve passar `entropy_coeff` — usar `self._entropy_for_progress(1.0)` (= `entropy_final`) ja que estamos no fim da fase. Decorar `result["entropy_coeff"]` igual aos demais updates para o log ficar consistente

**Tarefa C4: Logger registra entropy_coeff**

1. Em `training/curriculum/logger.py`, dentro de `log_update`:
   - Adicionar `"entropy_coeff": round(update_result.get("entropy_coeff", 0.0), 4)` ao record jsonl

---

### Grupo D — Eval Loop Deterministico

**Tarefa D1: Deterministic policy**

1. Em `training/agents/networks.py`, `PolicyNetwork.get_action_hierarchical`:
   - Adicionar parametro `deterministic: bool = False`
   - Se `deterministic`: `action_type = type_logits.argmax(dim=-1)` em vez de `type_dist.sample()`; idem para target
2. Em `training/agents/mappo.py`, `MAPPOAgent.select_action_hierarchical`:
   - Propagar `deterministic` para `policy.get_action_hierarchical`

**Tarefa D2: Trainer.evaluate**

1. Em `Trainer.__init__`: adicionar `eval_interval: int = 1000`, `eval_episodes: int = 50`, `self._eval_rng = _random.Random(seed + 1)`
2. Implementar `evaluate(team_size: int, n_episodes: int) -> dict`:
   - Loop de `n_episodes`:
     - `seed = self._eval_rng.randint(0, 2**31)`
     - `env = ArenaEnv(team_size=team_size); env.reset(seed=seed)`
     - Loop de batalha:
       - Se `team_a`: usar `select_action_hierarchical(..., deterministic=True)`
       - Se `team_b`: acao aleatoria via `_eval_rng.choice` entre `np.where(type_mask)[0]` e `np.where(target_mask)[0]`
     - Cap de 1000 steps por episodio
   - Contabilizar `wins_a`, `wins_b`, `draws`, `total_steps`
   - Retornar dict com `n_episodes`, `team_size`, `win_rate`, `loss_rate`, `draw_rate`, `avg_steps`

**Tarefa D3: Hook no train_phase**

1. Apos o block de pool/checkpoint, adicionar:
   ```python
   if self._eval_interval > 0 and (ep + 1) % self._eval_interval == 0:
       eval_team_size = self._rng.choice(phase.team_sizes)
       eval_result = self.evaluate(team_size=eval_team_size, n_episodes=self._eval_episodes)
       self.logger.log_eval(eval_result)
   ```

**Tarefa D4: Logger.log_eval**

1. Em `TrainingLogger`, adicionar:
   ```python
   def log_eval(self, eval_result: dict) -> None:
       record = {
           "phase": self._current_phase,
           "update": self._update_count,
           "episode": self._episode_count,
           "eval": eval_result,
       }
       with open(self._log_file, "a") as f:
           f.write(json.dumps(record) + "\n")
       wr = eval_result.get("win_rate", 0.0)
       n = eval_result.get("n_episodes", 0)
       ts = eval_result.get("team_size", 0)
       print(f"  [eval] ep={self._episode_count:<5d} win_rate={wr:.2%} (n={n}, team_size={ts})")
   ```

---

### Grupo E — Resume Robusto e Cleanup

**Tarefa E1: try/except RuntimeError no resume**

1. Em `Trainer.train_phase`, no bloco que tenta carregar `resume_dir`:
   - Adicionar `except RuntimeError as exc:` com warning `Could not resume from {resume_dir}: incompatible checkpoint`
2. Mesmo tratamento para `phase.load_from`

**Tarefa E2: Atualizar testes**

1. Em `training/tests/test_mappo.py`:
   - Substituir todas as construcoes `MAPPOAgent(obs_size=OBS_SIZE)` por `MAPPOAgent(obs_size=OBS_SIZE, global_state_size=OBS_SIZE)` (incluindo no `test_save_and_load`, no `agent2`)

**Tarefa E3: Limpeza de checkpoints antigos**

1. Antes de retreinar, executar:
   ```bash
   rm -rf models/easy models/normal models/hard models/_phase_*
   ```
2. (Opcional) Manter `logs/training_full.log` antigo se quiser comparar curvas pos-treino

---

### Validacao

1. Rodar `pytest training/tests/`:
   - Esperado: 69+ testes passando (smoke unitarios sao mantidos com `global_state_size=OBS_SIZE` nos testes)
2. Smoke training run:
   ```bash
   .venv/bin/python -m training.train --phase 1 --episodes 100 --log-dir /tmp/smoke
   ```
   - Esperado: roda sem crash, registra `entropy_coeff` nos updates, eval roda apenas se `--episodes >= eval_interval`
3. Smoke programatico com eval forcado:
   - Trainer com `eval_interval=30, eval_episodes=10`, phase de 60 episodios
   - Esperado: 2 evals registrados, cada um com `win_rate` reportado, `entropy_coeff` decai linearmente entre updates

---

## Condicao de Conclusao

Todos os criterios de aceitacao em spec.md satisfeitos.
`pytest training/tests/` passa.
Smoke runs descritos acima rodam sem erro.
Atualizar `.specs/state.md`: registrar feature 31 com status `concluida`.
Treino completo deve ser refeito do zero (`models/easy|normal|hard` apagados).
