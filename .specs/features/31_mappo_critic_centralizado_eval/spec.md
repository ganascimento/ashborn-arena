# Feature 31 — MAPPO com Critic Centralizado, Reward por % HP, Annealing e Eval Loop

## Objetivo

Conjunto de melhorias no pipeline de treinamento RL que enderecam multiplas deficiencias identificadas no agente atual (treinado em 20k episodios da fase 1 com performance medocre):

- **(A) Critic centralizado**: ate entao o critic recebia apenas a `obs` local de um agente — efetivamente IPPO disfarcado de MAPPO. O critic agora consome o `global_state` (obs concatenadas de todos os agentes), que e a definicao formal de MAPPO (Yu et al., 2022)
- **(B) Reward de dano e cura normalizado por % HP do alvo**: substitui a recompensa proporcional ao dano absoluto, que enviesava o agente a focar alvos com HP alto em vez de alvos prioritarios
- **(C) Entropy annealing linear**: substitui o coeficiente fixo (`0.01`) por um decay linear (`0.05 → 0.005`) ao longo de cada fase, balanceando exploracao no inicio e convergencia no fim
- **(D) Eval loop deterministico**: adiciona uma rotina de avaliacao executada periodicamente durante o treino — agentes do `team_a` jogam com policy deterministica (`argmax`) contra um oponente totalmente aleatorio. A win rate dessa avaliacao e a unica metrica confiavel de progresso real (independente de self-play e estocasticidade da policy)
- **(F) Reward shaping para AoE, chain, DoT, traps e reflect**: anteriormente apenas `basic_attack`, `ability` (single-target) e `opportunity_attack` geravam reward de dano. Eventos de AoE (`aoe_hit`), cadeia (`chain_primary`, `chain_secondary`), dano de tempo (`dot_tick`), armadilhas (`trap_triggered`) e reflexao (`reflect`) nao geravam sinal nenhum — Mago, Arqueiro e Assassino tinham ~50% das suas habilidades sem feedback de aprendizado

Tambem inclui:
- **(E) Resume robusto**: tratamento de incompatibilidade de checkpoint (state_dict size mismatch) sem crash — o treino comeca do zero com warning, em vez de falhar
- **(G) Engine: campo `attacker` em DoT, trap e chain_secondary**: para que (F) funcione, o engine agora propaga o source/caster como `attacker` em `dot_tick`, `trap_triggered` e `chain_secondary` (que antes nao traziam essa info no payload)
- Encerramento dos checkpoints antigos: a mudanca em (A) altera o `input_size` do `CriticNetwork`, tornando os `.pt` salvos incompativeis. O treino deve ser refeito do zero

---

## Referencia nos Specs

- design.md: secao 5 (arquitetura da IA, MAPPO)
- prd.md: secao 4 (requisitos da IA)
- Yu et al., 2022 — "The Surprising Effectiveness of PPO in Cooperative, Multi-Agent Games"

---

## Arquivos Envolvidos

### Modificar

| Arquivo | Descricao |
|---|---|
| `training/agents/mappo.py` | `MAPPOAgent.__init__` aceita `global_state_size` separado de `obs_size`; `CriticNetwork` construido com `global_state_size`; `get_value(global_state)` substitui `get_value(obs)`; `update(buffer, entropy_coeff=...)` aceita override; critic forward passa por `global_states` do batch (com fallback para `obs` quando ausente — usado pelos testes unitarios); `select_action_hierarchical` aceita `deterministic` |
| `training/agents/networks.py` | `PolicyNetwork.get_action_hierarchical` aceita `deterministic: bool = False` (argmax em vez de sample) |
| `training/environment/rewards.py` | Substitui `REWARD_DAMAGE = 0.1` por `REWARD_DAMAGE_PCT = 2.0`; idem `REWARD_HEAL_PCT`; `compute_rewards` agora aceita `battle_state: BattleState | None` opcional para lookup de `target.max_hp`; reward de dano/cura/HoT escala por `min(amount / max_hp, 1.0) * pct_const`. Lista de eventos com reward de dano expandida para incluir `aoe_hit`, `chain_primary`, `chain_secondary`, `dot_tick`, `trap_triggered`. Novo branch para `reflect` (credita o `source` que refletiu) |
| `training/environment/arena_env.py` | `compute_rewards` chamada com `battle_state=self._battle` |
| `engine/systems/battle.py` | Eventos `dot_tick`, `trap_triggered` e `chain_secondary` passam a incluir o campo `attacker` (= `effect.source_entity_id`, `caster_id` e `attacker_id` respectivamente). Necessario para que o reward shaping em (F) atribua credito correto |
| `training/curriculum/trainer.py` | `Trainer.__init__` aceita `eval_interval=1000`, `eval_episodes=50`, `entropy_initial=0.05`, `entropy_final=0.005`; novo `evaluate(team_size, n_episodes)` (deterministic team_a vs random team_b); `_entropy_for_progress(progress)` (linear); em `train_phase`: `encode_global_state` passado pro buffer/critic; `entropy_coeff` calculado a cada update; **annealing usa progresso absoluto (`(ep + 1) / phase.episodes`), nao relativo ao `episode_offset` — garantindo continuidade correta em resume**; **final flush do buffer ao fim da fase tambem passa `entropy_coeff` (= `_entropy_for_progress(1.0)`) e decora o resultado com o coeficiente para o log**; eval rodado a cada `eval_interval` episodios; resume com `try/except RuntimeError` para incompatibilidade |
| `training/curriculum/logger.py` | Novo `log_eval(eval_result)` — registro estruturado com `win_rate`, `loss_rate`, `draw_rate`, `avg_steps`, e print humanizado; `log_update` agora inclui `entropy_coeff` |
| `training/environment/observations.py` | (sem mudanca — `encode_global_state` e `GLOBAL_STATE_SIZE` ja existiam, agora sao consumidos) |
| `training/agents/buffer.py` | (sem mudanca — campo `global_states` ja existia, agora e populado) |
| `training/tests/test_mappo.py` | Construcao do agente nos testes passa `global_state_size=OBS_SIZE` para manter o smoke test compativel sem expandir o tamanho do estado |
| `training/tests/test_arena_env.py` | Substitui import e assert de `REWARD_DAMAGE` por `REWARD_DAMAGE_PCT` |

### Remover

| Caminho | Descricao |
|---|---|
| `models/easy/`, `models/normal/`, `models/hard/` | Checkpoints antigos (IPPO disfarcado, critic com input_size errado). Devem ser apagados antes de retreinar — `RuntimeError` por size mismatch ja e tratado, mas deixar arquivos orfaos so polui o working tree |

---

## Criterios de Aceitacao

### A — Critic Centralizado

- [ ] `MAPPOAgent` aceita parametro `global_state_size` (default = `GLOBAL_STATE_SIZE = OBS_TOTAL_SIZE * 6`)
- [ ] `CriticNetwork` e instanciado com `global_state_size`, nao `obs_size`
- [ ] `MAPPOAgent.get_value(global_state)` recebe o estado global e retorna `float`
- [ ] No `update`, o critic forward usa `batch["global_states"]` quando presente; fallback para `obs` apenas para preservar smoke tests
- [ ] No `Trainer.collect_rollout`, `encode_global_state(env._battle)` e calculado a cada step e passado para `buffer.add(global_state=...)`
- [ ] Treino completo (smoke test minimo de 60 episodios) roda sem erro de shape no critic

### B — Reward Normalizado por % HP

- [ ] `REWARD_DAMAGE = 0.1` removido; substituido por `REWARD_DAMAGE_PCT = 2.0`
- [ ] `REWARD_HEAL` removido; substituido por `REWARD_HEAL_PCT = 2.0`
- [ ] Para eventos `basic_attack`, `ability`, `opportunity_attack`: reward = `min(damage / target.max_hp, 1.0) * REWARD_DAMAGE_PCT`
- [ ] Para eventos `heal`, `self_heal`, `lifesteal`: reward = `min(amount / target.max_hp, 1.0) * REWARD_HEAL_PCT`
- [ ] Para `hot_tick`: cada aliado recebe `min(heal / entity.max_hp, 1.0) * REWARD_HEAL_PCT * 0.5`
- [ ] Quando `battle_state` nao e fornecido (ex: testes legados), `_max_hp` retorna fallback `100`
- [ ] `apply_terminal_rewards`, `REWARD_VICTORY`, `REWARD_DEFEAT`, `REWARD_KILL`, `REWARD_KNOCKDOWN`, `REWARD_ALLY_DEAD`, `REWARD_COMBO` permanecem inalterados

### F — Reward Shaping Estendido

- [ ] Eventos `aoe_hit`, `chain_primary`, `chain_secondary`, `dot_tick`, `trap_triggered` produzem reward de dano para o `attacker` na mesma escala que `basic_attack`/`ability` — `min(damage / target.max_hp, 1.0) * REWARD_DAMAGE_PCT`
- [ ] Evento `reflect` produz reward para o campo `source` (entidade que refletiu o dano) na mesma escala
- [ ] Evento `redirect` continua sem reward — comportamento defensivo intencional, sem credito por dano (decisao de design para evitar confusao com defesa ativa)
- [ ] Evento `bleed` (dano passivo de knockout/morte progressiva) continua sem reward — nao ha atacante claro, e dano de timer de morte
- [ ] Eventos sem `attacker` valido (ex: DoT cuja `source_entity_id` e vazia ou ja morreu) sao silenciosamente ignorados (`if attacker in rewards`)

### G — Engine: campo `attacker` em eventos de dano indireto

- [ ] `engine/systems/battle.py`: evento `dot_tick` agora inclui `attacker: effect.source_entity_id`
- [ ] `engine/systems/battle.py`: evento `trap_triggered` agora inclui `attacker: caster_id`
- [ ] `engine/systems/battle.py`: evento `chain_secondary` agora inclui `attacker: attacker_id` (mesmo `attacker_id` do `chain_primary` correspondente)
- [ ] Estrutura dos demais eventos (campos existentes) nao alterada — testes em `engine/tests/` continuam passando

### C — Entropy Annealing

- [ ] `Trainer.__init__` aceita `entropy_initial=0.05` e `entropy_final=0.005`
- [ ] `_entropy_for_progress(progress)` retorna `initial + (final - initial) * clamp(progress, 0, 1)`
- [ ] Em `train_phase`, antes de cada `agent.update`, `progress = (ep + 1 - episode_offset) / max(phase.episodes - episode_offset, 1)` e `entropy_coeff = _entropy_for_progress(progress)`
- [ ] `MAPPOAgent.update(buffer, entropy_coeff=ent)` aplica o valor passado em vez do `self._entropy_coeff` interno (que vira default fallback de `0.05`)
- [ ] O log de cada update inclui o campo `entropy_coeff` (arredondado a 4 casas)

### D — Eval Loop Deterministico

- [ ] `Trainer.evaluate(team_size: int, n_episodes: int) -> dict` implementado
- [ ] Cada episodio de eval: novo `ArenaEnv(team_size=team_size)`, reset com seed do `_eval_rng` (separado do `_rng` do treino para reprodutibilidade independente)
- [ ] Agentes em `team_a`: `select_action_hierarchical(..., deterministic=True)` (argmax do logit mascarado)
- [ ] Agentes em `team_b`: acao aleatoria — `a_type` uniforme entre tipos validos, `a_target` uniforme entre alvos validos para o tipo
- [ ] Resultado contem: `n_episodes`, `team_size`, `win_rate`, `loss_rate`, `draw_rate`, `avg_steps`
- [ ] Em `train_phase`, eval e disparado a cada `eval_interval` episodios (default `1000`); `team_size` do eval e amostrado de `phase.team_sizes`
- [ ] `eval_interval=0` desativa o eval
- [ ] `logger.log_eval(eval_result)` registra em jsonl com `phase`, `update`, `episode`, `eval` aninhado; print humano `[eval] ep=N win_rate=XX% (n=N, team_size=N)`

### E — Resume Robusto

- [ ] `Trainer.train_phase` envolve `self._agent.load(resume_dir)` em try/except que captura `RuntimeError`
- [ ] Em caso de mismatch, imprime warning `[warn] Could not resume from {dir}: incompatible checkpoint (RuntimeError). Starting phase from scratch.` e segue treino do zero
- [ ] Mesmo tratamento aplicado a `phase.load_from`
- [ ] `FileNotFoundError` continua sendo tratado silenciosamente (comportamento original)

### Validacao

- [ ] `pytest training/tests/` passa (69+ testes)
- [ ] Smoke run `--phase 1 --episodes 60` roda end-to-end sem crash
- [ ] Smoke run dispara pelo menos 1 eval e registra `entropy_coeff` decrescente entre os primeiros e ultimos updates
- [ ] Treino completo (4 fases × 20k = 80k episodios) deve ser refeito do zero — checkpoints antigos sao incompativeis e devem ser removidos

---

## Fora do Escopo

- Mudar `phase.episodes` (mantido em 20k para todas as 4 fases)
- Reformulacao do curriculum (fases continuam 1 → 1v1, 2 → 2v2, 3 → 3v3, 4 → mixed)
- Eval contra checkpoint inicial / Elo / TrueSkill — apenas vs random nesta iteracao
- Distillation ou warm start de checkpoints antigos para nova arquitetura
- Versionamento de checkpoint (formato com metadata.architecture)
- Prioritized experience replay ou outras melhorias do PPO base
