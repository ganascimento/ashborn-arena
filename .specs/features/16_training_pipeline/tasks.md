# Tasks — Feature 15: Training Pipeline

## Antes de Comecar

Ler obrigatoriamente antes de escrever qualquer codigo:

- `CLAUDE.md` — stack, estrutura do projeto, convencoes
- `.specs/features/15_training_pipeline/spec.md` — criterios de aceitacao desta feature
- `.specs/notes.md` — critic padding workaround (deve ser resolvido), habilidades complexas nao implementadas
- `.specs/design.md` secoes 5.4 (pipeline — fases, hiperparametros), 5.5 (armazenamento de modelos)
- `.specs/prd.md` secoes 4.6 (curriculum learning), 4.7 (self-play)
- `training/agents/mappo.py` — MAPPOAgent (select_action, update, save/load)
- `training/agents/buffer.py` — RolloutBuffer (sera modificado para global_state)
- `training/environment/arena_env.py` — ArenaEnv (reset, step, observe, infos)
- `training/environment/observations.py` — encode_global_state

---

## Plano de Execucao

2 grupos sequenciais. Grupo 1 e a fase TDD. Grupo 2 e a implementacao.

- **Grupo 1**: testes para phases, self-play pool, trainer. Parar apos criar os testes.
- **Grupo 2**: implementar phases.py, self_play.py, trainer.py, atualizar buffer.py e train.py. Rodar testes.

Dependencia: Grupo 2 so executa apos aprovacao dos testes do Grupo 1.

---

### Grupo 1 — Testes (TDD)

**Tarefa:** Criar testes para o pipeline de treinamento.

1. Criar `training/tests/test_training_pipeline.py`:
   - **PhaseConfig e CURRICULUM_PHASES:**
     - CURRICULUM_PHASES tem 4 entradas
     - Fase 1: team_size=1, checkpoint_dir="models/easy"
     - Fase 3: team_size=3, checkpoint_dir="models/normal"
     - Fase 4: checkpoint_dir="models/hard"
     - Cada fase carrega pesos da anterior (load_from configurado)
   - **SelfPlayPool:**
     - Pool inicia vazio, add_snapshot adiciona
     - sample_opponent retorna snapshot aleatorio
     - Pool respeita max_size (remove mais antigo)
     - Pool com 1 entrada retorna essa entrada
   - **RolloutBuffer com global_state:**
     - add aceita global_state
     - get_batches retorna global_states nos mini-batches
   - **Trainer:**
     - collect_rollout preenche o buffer (pelo menos 1 timestep)
     - train_phase executa sem erro para 2 episodios minimos
     - Checkpoint salvo no diretorio correto apos a fase

2. Rodar testes e confirmar que todos falham.

**Parar apos criar os testes. Nao implementar logica de producao. Aguardar aprovacao do usuario.**

---

### Grupo 2 — Implementacao (um agente)

**Tarefa:** Implementar o pipeline completo de treinamento.

1. Modificar `training/agents/buffer.py`:
   - Adicionar campo `global_states` na estrutura de dados por agente
   - `add(...)` aceita parametro `global_state: np.ndarray | None = None`
   - `get_batches` inclui `global_states` tensor nos mini-batches
   - Manter retrocompatibilidade (global_state=None usa padding como fallback)

2. Criar `training/curriculum/phases.py`:
   - `@dataclass class PhaseConfig`:
     - phase_number: int
     - team_sizes: list[int] (ex: [1] para 1v1, [1,2,3] para misto)
     - episodes: int
     - update_interval: int (episodios entre PPO updates)
     - pool_interval: int (episodios entre snapshots no pool)
     - checkpoint_dir: str | None (None = nao salva)
     - load_from: str | None (diretorio de onde carregar pesos)
   - `CURRICULUM_PHASES: list[PhaseConfig]`:
     - Fase 1: team_sizes=[1], episodes=500, checkpoint_dir="models/easy", load_from=None
     - Fase 2: team_sizes=[2], episodes=500, load_from="models/easy"
     - Fase 3: team_sizes=[3], episodes=500, checkpoint_dir="models/normal", load_from="models/easy"
     - Fase 4: team_sizes=[1,2,3], episodes=500, checkpoint_dir="models/hard", load_from="models/normal"
     - Numeros de episodios sao defaults (overridable via CLI)

3. Criar `training/curriculum/self_play.py`:
   - `class SelfPlayPool`:
     - `__init__(self, max_size=10)`
     - `_snapshots: list[dict[str, dict]]` — lista de state_dicts de todas policies
     - `add_snapshot(agent: MAPPOAgent)`: copia state_dicts das 5 policies, adiciona ao pool. Se pool cheio, remove o mais antigo.
     - `sample_opponent() -> dict[str, dict]`: retorna snapshot aleatorio
     - `size` property
     - `load_into(agent: MAPPOAgent, snapshot: dict)`: carrega snapshot nas policies do agent

4. Criar `training/curriculum/trainer.py`:
   - `class Trainer`:
     - `__init__(self, agent: MAPPOAgent, seed=42)`
     - `collect_rollout(self, env: ArenaEnv, buffer: RolloutBuffer) -> dict`:
       - Reseta env com seed
       - Loop ate termination:
         - agent = env.agent_selection
         - obs = env.observe(agent)
         - global_state = encode_global_state(battle_state)
         - mask = env.infos[agent]["action_mask"]
         - class_name = determina a classe do agente
         - action, log_prob, entropy = agent.select_action(class_name, obs, type_mask, target_mask)
         - value = agent.get_value(global_state)
         - env.step(action)
         - reward = env.rewards[agent]
         - done = env.terminations[agent]
         - buffer.add(agent, obs, action, log_prob, reward, value, done, type_mask, target_mask, global_state)
       - Retorna stats (total_reward, steps, winner)
     - `train_phase(self, phase: PhaseConfig, pool: SelfPlayPool) -> dict`:
       - Se phase.load_from: agent.load(phase.load_from)
       - Para cada episodio:
         - team_size = random.choice(phase.team_sizes)
         - env = ArenaEnv(team_size=team_size)
         - collect_rollout(env, buffer)
         - Se episodio % update_interval == 0: agent.update(buffer), buffer.clear()
         - Se episodio % pool_interval == 0: pool.add_snapshot(agent)
       - Se phase.checkpoint_dir: agent.save(phase.checkpoint_dir)
       - Retorna stats
     - `run_curriculum(self, phases: list[PhaseConfig])`: executa todas fases sequencialmente

5. Atualizar `training/train.py`:
   - Entrypoint: `if __name__ == "__main__":`
   - Parse args: `--phase N`, `--episodes N`, `--seed N`
   - Cria MAPPOAgent, Trainer
   - Executa curriculum (ou fase especifica)
   - Print stats ao final

6. Atualizar `training/curriculum/__init__.py`:
   - Re-exportar CURRICULUM_PHASES, PhaseConfig, SelfPlayPool, Trainer

7. Rodar `pytest training/tests/test_training_pipeline.py -v`.

8. Rodar `pytest engine/tests/ training/tests/ -v` para zero regressoes.

---

## Condicao de Conclusao

- Todos os criterios de aceitacao do spec.md satisfeitos
- Todos os testes passam com `pytest engine/tests/ training/tests/ -v`
- Atualizar `.specs/state.md`: status da feature 15 de `pendente` para `concluida`
- Atualizar `.specs/notes.md`: marcar critic padding como resolvido
