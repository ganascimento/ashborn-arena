# Feature 32 — Visualizacao de Treino com TensorBoard

## Objetivo

Adicionar visualizacao da evolucao do treinamento via TensorBoard, mantendo o JSONL atual como fonte da verdade (texto, diff-able, gravado em paralelo). O treino vai rodar em outra maquina, entao os event files do TensorBoard precisam ser persistentes em arquivo e versionados via git, permitindo que de qualquer maquina seja possivel rodar `tensorboard --logdir logs/runs/` e ver os graficos historicos sem precisar re-treinar nem transferir manualmente.

A integracao deve ser opt-in/opt-out via parametro do `TrainingLogger` para nao quebrar testes unitarios que constroem o logger em diretorios temporarios.

---

## Referencia nos Specs

- design.md: secao 5 (Sistema de IA — arquitetura das redes, pipeline de treinamento, hiperparametros)
- design.md: secao 5.4 (Pipeline de Treinamento — metricas relevantes para acompanhar convergencia)
- prd.md: secao 4 (IA — requisitos de aprendizado e acompanhamento)

---

## Arquivos Envolvidos

### Modificar

| Arquivo | Descricao |
|---|---|
| `training/curriculum/logger.py` | `TrainingLogger.__init__` aceita `enable_tensorboard: bool = True`; cria `SummaryWriter` em subdiretorio `tb/` dentro de `log_dir`; `log_update` espelha scalars de loss/policy/train no TB com `step=self._episode_count`; `log_eval` espelha scalars de eval no TB; `end_training` fecha o writer com `self._writer.close()` |
| `.gitignore` | Substitui regra `logs/training.jsonl` por estrutura `logs/scratch/` (ignorado) e mantem `logs/runs/` versionado |
| `README.md` | Adiciona secao "Visualizando o treino" com `tensorboard --logdir logs/runs/` e link para `http://localhost:6006`; menciona `logs/scratch/` para experimentos descartaveis |

### Criar

| Arquivo | Descricao |
|---|---|
| `training/tests/test_logger_tensorboard.py` | Testes unitarios: (1) `TrainingLogger` com `enable_tensorboard=False` nao cria diretorio `tb/`; (2) `TrainingLogger` com `enable_tensorboard=True` cria arquivo `events.out.tfevents.*` em `<log_dir>/tb/` apos primeiro `log_update`; (3) JSONL continua sendo gravado independente do flag; (4) `end_training` fecha o writer sem crash |
| `logs/runs/.gitkeep` | Placeholder para garantir que `logs/runs/` existe no repo mesmo vazio |
| `logs/scratch/.gitkeep` | Placeholder local; entrada do dir esta no .gitignore mas serve como referencia visual |

### Nao modificar

| Arquivo | Motivo |
|---|---|
| `training/train.py` | `--log-dir` ja existe e e propagado ao `TrainingLogger`; usuario controla onde escreve passando `--log-dir logs/runs/<nome>` ou `--log-dir logs/scratch/<id>` |
| `training/curriculum/trainer.py` | Consome o logger pela API atual (`log_update`, `log_eval`, `end_training`) — sem mudanca |
| `pyproject.toml` / `requirements.txt` | `tensorboard` ja vem como dependencia transitiva do `torch` (via `torch.utils.tensorboard`); nao adicionar duplicado |

---

## Criterios de Aceitacao

### Integracao do SummaryWriter

- [ ] `TrainingLogger.__init__` aceita parametro `enable_tensorboard: bool = True`
- [ ] Quando `enable_tensorboard=True`: cria `self._writer = SummaryWriter(log_dir=str(self._log_dir / "tb"))`
- [ ] Quando `enable_tensorboard=False`: `self._writer` e `None` e nenhum diretorio `tb/` e criado
- [ ] Import `from torch.utils.tensorboard import SummaryWriter` no topo do arquivo
- [ ] Codigo pode ser compactado com `if self._writer is not None:` antes de cada `add_scalar` para evitar erro com flag desabilitada

### Metricas de update (em `log_update`)

- [ ] Quando `self._writer is not None`, apos a escrita do JSONL, gravar:
  - `loss/policy` = `update_result["policy_loss"]`
  - `loss/value` = `update_result["value_loss"]`
  - `policy/entropy` = `update_result["entropy"]`
  - `policy/entropy_coeff` = `update_result.get("entropy_coeff", 0.0)`
  - `train/avg_reward_50` = avg_reward calculado
  - `train/avg_steps_50` = avg_steps calculado
  - `train/win_rate_50` = `win_a / max(n, 1)` (taxa de vitoria de team_a na janela de 50)
- [ ] Todos os scalars usam `global_step=self._episode_count` (eixo X = episodios; permite alinhar com eval no mesmo grafico)

### Metricas de eval (em `log_eval`)

- [ ] Quando `self._writer is not None`, apos a escrita do JSONL, gravar:
  - `eval/win_rate` = `eval_result["win_rate"]`
  - `eval/loss_rate` = `eval_result["loss_rate"]`
  - `eval/draw_rate` = `eval_result["draw_rate"]`
  - `eval/avg_steps` = `eval_result["avg_steps"]`
- [ ] Todos os scalars usam `global_step=self._episode_count`

### Encerramento

- [ ] `end_training` chama `self._writer.close()` se `self._writer is not None`
- [ ] `end_training` continua imprimindo as estatisticas finais como antes (comportamento JSONL/print preservado)

### Estrutura de pastas e gitignore

- [ ] `logs/runs/` versionado: subpastas com event files + JSONL devem entrar no git via `git add logs/runs/<nome>/`
- [ ] `logs/scratch/` totalmente ignorado pelo git
- [ ] Arquivo `logs/training.jsonl` legado (na raiz de `logs/`) continua ignorado pelo git
- [ ] `.gitignore` final tem entrada `logs/scratch/` e remove a entrada antiga `logs/training.jsonl` (substituida por `logs/*.jsonl` para cobrir o caso geral, mas event files dentro de `logs/runs/` continuam versionados)
- [ ] `logs/runs/.gitkeep` existe para garantir que a pasta esta versionada mesmo vazia

### Documentacao

- [ ] `README.md` ganha uma secao curta "Visualizando o treino" com:
  - Comando `tensorboard --logdir logs/runs/`
  - URL `http://localhost:6006`
  - Convenção: usar `logs/runs/<nome_descritivo>/` para runs marco e `logs/scratch/<id>/` para experimentos
  - Exemplo de comando: `python -m training.train --log-dir logs/runs/2026-04-28_baseline`

### Testes

- [ ] `training/tests/test_logger_tensorboard.py` criado com testes:
  - `test_tensorboard_disabled_creates_no_dir` — `TrainingLogger(log_dir=tmpdir, enable_tensorboard=False)` nao cria `tmpdir/tb/`
  - `test_tensorboard_enabled_creates_event_file` — apos `log_update`, existe pelo menos um arquivo `events.out.tfevents.*` em `tmpdir/tb/`
  - `test_jsonl_unchanged_with_tensorboard_disabled` — JSONL e escrito normalmente quando TB esta desligado
  - `test_jsonl_unchanged_with_tensorboard_enabled` — JSONL continua identico ao formato atual quando TB esta ligado
  - `test_end_training_closes_writer_safely` — `end_training` nao crasha com TB desligado nem ligado
- [ ] `pytest training/tests/` passa com 711+ testes (todos os existentes + os novos)
- [ ] Nenhum teste existente do `Trainer` ou de outras classes precisa ser alterado (compatibilidade reversa preservada com default `enable_tensorboard=True`)

### Validacao programatica

- [ ] Smoke run programatico: rodar `Trainer.train_phase` com 30+ episodios e `TrainingLogger(enable_tensorboard=True)`, verificar:
  - Arquivo `events.out.tfevents.*` existe em `<log_dir>/tb/`
  - Arquivo `training.jsonl` continua sendo gerado normalmente
  - Logs no stdout aparecem como antes (compatibilidade visual preservada)

---

## Fora do Escopo

- **Integracao com wandb ou outros backends cloud** — decisao explicita por TB local + commit dos event files. Se um dia o repo crescer demais, considerar wandb como migracao.
- **Histogramas de pesos e gradientes** (`add_histogram`) — apenas scalars nesta primeira versao. Histogramas adicionam custo significativo de I/O e tamanho do event file.
- **`add_hparams` para registrar hiperparametros** — fica para feature futura quando houver experimentacao sistematica de hiperparametros.
- **Script `jsonl_to_tb.py` para regenerar event files a partir do JSONL** — solucao alternativa caso o repo cresca demais; nao implementado agora.
- **Profiling do training step** (`torch.profiler` exportando para TB) — nao e o foco; foco e curva de aprendizado, nao performance computacional.
- **Imagens de batalha ou videos de rollout** — visualizacao de gameplay e responsabilidade do frontend (features 21-24), nao do TB.
- **Migracao automatica do `logs/training.jsonl` legado para `logs/runs/`** — usuario faz manualmente quando quiser preservar uma run antiga.
- **Mudanca em `training/train.py`** — `--log-dir` ja existe; o usuario passa o subdiretorio desejado (`logs/runs/<nome>` ou `logs/scratch/<id>`) na invocacao.
