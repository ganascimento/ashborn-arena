# Feature 15 — Training Pipeline

## Objetivo

Implementar o pipeline completo de treinamento: o loop de coleta de rollouts via ArenaEnv, o curriculum learning em 4 fases (1v1→2v2→3v3→misto), o self-play pool para diversidade de oponentes, e a persistencia de checkpoints nos diretórios `models/easy/`, `models/normal/`, `models/hard/`. O entrypoint `training/train.py` executa o treinamento de ponta a ponta. Esta feature fecha o bloco de treinamento — apos sua conclusao, os modelos .pt estao prontos para uso pelo backend (feature 18).

---

## Referencia nos Specs

- prd.md: secoes 4.2 (niveis de dificuldade — checkpoints por fase), 4.5 (funcao de recompensa), 4.6 (curriculum learning — 4 fases), 4.7 (self-play — pool de politicas)
- design.md: secoes 5.4 (pipeline de treinamento — fases, hiperparametros), 5.5 (armazenamento de modelos — estrutura de diretorios)
- .specs/notes.md: critic padding workaround (deve ser resolvido nesta feature coletando global state no buffer)

---

## Arquivos Envolvidos

### Criar

- `training/curriculum/phases.py` — PhaseConfig, CURRICULUM_PHASES (definicao das 4 fases)
- `training/curriculum/self_play.py` — SelfPlayPool (pool de politicas para diversidade de oponentes)
- `training/curriculum/trainer.py` — Trainer (loop de coleta + update, coordena fases e self-play)
- `training/tests/test_training_pipeline.py` — testes do pipeline

### Modificar

- `training/train.py` — entrypoint que instancia Trainer e executa o curriculum
- `training/agents/buffer.py` — adicionar campo global_state para o critic (resolver notes.md)
- `training/curriculum/__init__.py` — re-exportar

---

## Criterios de Aceitacao

### Curriculum Learning (prd.md 4.6, design.md 5.4)

- [ ] 4 fases definidas: Fase 1 (1v1), Fase 2 (2v2), Fase 3 (3v3), Fase 4 (composicoes mistas 1v2, 2v3)
- [ ] Cada fase carrega os pesos da fase anterior (exceto Fase 1 que inicia do zero)
- [ ] Fase 1 salva checkpoint em `models/easy/` (5 .pt files, um por classe)
- [ ] Fase 3 salva checkpoint em `models/normal/`
- [ ] Fase 4 salva checkpoint em `models/hard/`
- [ ] Cada fase define: team_size (ou range de sizes), numero de episodios, e se salva checkpoint

### Self-Play Pool (prd.md 4.7)

- [ ] `SelfPlayPool` mantém pool de snapshots de politicas anteriores
- [ ] Oponente selecionado aleatoriamente do pool a cada episodio
- [ ] Versao atual adicionada ao pool periodicamente (a cada N episodios, configuravel)
- [ ] Pool tem tamanho maximo (ex: 10) — versoes mais antigas removidas
- [ ] Na Fase 1 (inicio), pool contem apenas a politica atual (bootstrap)

### Rollout Collection

- [ ] `Trainer.collect_rollout(env, agent, buffer)` executa 1 episodio completo no ArenaEnv
- [ ] Para cada micro-decisao: coleta obs, action_mask, seleciona acao via MAPPOAgent, armazena no buffer
- [ ] Global state coletado e armazenado no buffer para o critic (resolver notes.md — nao usar padding)
- [ ] Rewards acumulados do ambiente sao armazenados no buffer
- [ ] Episodio termina quando env reporta terminacao de todos agentes
- [ ] Buffer acumula N episodios antes de trigger o PPO update

### Training Loop

- [ ] `Trainer.train_phase(phase_config)` executa uma fase completa: N episodios com collect + update
- [ ] A cada `update_interval` episodios: executa `agent.update(buffer)`, limpa buffer
- [ ] A cada `pool_interval` episodios: adiciona snapshot ao self-play pool
- [ ] Ao final da fase: salva checkpoint se configurado
- [ ] Logging basico: episodio, reward medio, policy_loss, value_loss (print)

### Entrypoint (train.py)

- [ ] `python -m training.train` executa o pipeline completo (4 fases sequenciais)
- [ ] Aceita argumentos opcionais: `--phase N` para rodar apenas uma fase, `--episodes N` para override
- [ ] Seed configuravel para reproducibilidade

### Armazenamento de Modelos (design.md 5.5)

- [ ] Checkpoints salvos em `models/{difficulty}/` com 5 arquivos: guerreiro.pt, mago.pt, clerigo.pt, arqueiro.pt, assassino.pt
- [ ] Formato compativel com MAPPOAgent.save/load

### RolloutBuffer — Global State (resolver notes.md)

- [ ] Buffer armazena `global_state` por timestep (alem de obs local)
- [ ] `get_batches` retorna `global_states` nos mini-batches
- [ ] MAPPO update usa global_states para o critic (sem padding)

---

## Fora do Escopo

- Tuning de hiperparametros (valores iniciais de design.md 5.4 usados, ajustes sao iterativos pos-feature)
- Metricas avançadas de convergencia (tensorboard, wandb) — pode ser adicionado depois
- Inference para o backend — feature 18
- Treinamento distribuido/GPU — fora do escopo do MVP (CPU only, 2 cores)
- Mecanicas complexas nao implementadas no BattleState (conforme notes.md) — o treinamento usa o que o BattleState suporta
