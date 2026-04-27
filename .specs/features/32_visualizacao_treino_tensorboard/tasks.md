# Tasks — Feature 32: Visualizacao de Treino com TensorBoard

## Antes de Comecar

Leitura obrigatoria antes de implementar:

- `CLAUDE.md` — convencoes (codigo em ingles, sem docstrings, models separadas de entrypoints)
- `.specs/features/32_visualizacao_treino_tensorboard/spec.md` — criterios de aceitacao desta feature
- `.specs/design.md` secao 5 (Sistema de IA) e 5.4 (Pipeline de Treinamento) — contexto sobre as metricas
- `.specs/notes.md` — notas tecnicas sobre o pipeline de treinamento (per-class batching, terminal rewards, pending rewards)
- `training/curriculum/logger.py` — `TrainingLogger` atual (estado a ser estendido)
- `training/curriculum/trainer.py` — chamadas a `start_training`, `start_phase`, `log_episode`, `log_update`, `log_eval`, `end_phase`, `end_training` (entender quando cada metodo e chamado)
- `training/train.py` — entrypoint (`--log-dir` ja existe e e propagado)
- `.gitignore` — estado atual

---

## Plano de Execucao

Esta feature tem escopo pequeno e baixa complexidade — todas as mudancas estao concentradas em `TrainingLogger`. Executar em **3 grupos sequenciais** (TDD):

1. **Grupo 1** — Testes do `TrainingLogger` com flag de TB (TDD: cria testes que falham, **pausa** para aprovacao do usuario antes de implementar).
2. **Grupo 2** — Implementacao do `SummaryWriter` no logger (faz os testes do Grupo 1 passarem).
3. **Grupo 3** — Estrutura de pastas, `.gitignore` e documentacao (independente do codigo, pode ate rodar em paralelo com Grupo 2 se preferir, mas executar sequencial reduz risco).

TDD aplica: o `TrainingLogger` tem comportamento testavel (writer existe ou nao, evento gravado ou nao, JSONL preservado). Smoke programatico no final valida o pipeline ponta a ponta.

---

### Grupo 1 — Testes (TDD, parar apos criar)

**Tarefa:** Criar `training/tests/test_logger_tensorboard.py` com testes que cobrem o comportamento esperado do `TrainingLogger` com e sem TensorBoard.

1. Criar arquivo `training/tests/test_logger_tensorboard.py` com:
   - Import de `tempfile`, `pathlib.Path`, `pytest`, `from training.curriculum.logger import TrainingLogger`
   - Fixture `tmp_log_dir` que cria um diretorio temporario via `tempfile.TemporaryDirectory()`
   - Helper `_log_one_update(logger)` que chama `logger.start_training()`, `logger.start_phase(phase_number=1, team_sizes=[1], episodes=10)`, `logger.log_episode(1, {"winner": "team_a", "steps": 30, "total_reward": {"a": 1.0}})`, `logger.log_update({"policy_loss": -0.01, "value_loss": 50.0, "entropy": 2.0, "entropy_coeff": 0.05})`
   - Helper `_log_one_eval(logger)` que chama `logger.log_eval({"n_episodes": 20, "team_size": 1, "win_rate": 0.75, "loss_rate": 0.25, "draw_rate": 0.0, "avg_steps": 50.0})`

2. Adicionar testes:
   - `test_tensorboard_disabled_creates_no_dir(tmp_log_dir)`:
     - `logger = TrainingLogger(log_dir=tmp_log_dir, enable_tensorboard=False)`
     - `_log_one_update(logger)`
     - `assert not (Path(tmp_log_dir) / "tb").exists()`
   - `test_tensorboard_enabled_creates_event_file(tmp_log_dir)`:
     - `logger = TrainingLogger(log_dir=tmp_log_dir, enable_tensorboard=True)`
     - `_log_one_update(logger)`
     - `_log_one_eval(logger)`
     - `logger.end_training()`
     - `tb_dir = Path(tmp_log_dir) / "tb"`
     - `assert tb_dir.exists()`
     - `events = list(tb_dir.glob("events.out.tfevents.*"))`
     - `assert len(events) >= 1`
   - `test_jsonl_unchanged_with_tensorboard_disabled(tmp_log_dir)`:
     - Cria logger com TB desligado, faz update e eval, le `training.jsonl`, valida que tem 2 linhas (1 update + 1 eval) e que ambas sao JSON parseavel com chaves esperadas (`policy_loss`, `eval`)
   - `test_jsonl_unchanged_with_tensorboard_enabled(tmp_log_dir)`:
     - Mesmo do anterior mas com TB ligado, valida que JSONL e identico em formato (mesmas chaves)
   - `test_end_training_closes_writer_safely(tmp_log_dir)`:
     - Cria logger com TB ligado, chama `end_training` sem nenhum log antes, verifica que nao crasha
     - Cria outro logger com TB desligado, chama `end_training`, verifica que nao crasha

3. **Parar apos criar os testes. Nao implementar a logica de producao. Esperar aprovacao do usuario.**

4. Rodar `pytest training/tests/test_logger_tensorboard.py -x -q` e confirmar que **todos falham** (porque `enable_tensorboard` ainda nao existe).

---

### Grupo 2 — Implementacao do SummaryWriter

**Tarefa:** Modificar `training/curriculum/logger.py` para suportar TensorBoard via flag opcional, fazendo os testes do Grupo 1 passarem.

1. Em `training/curriculum/logger.py`:
   - Adicionar import `from torch.utils.tensorboard import SummaryWriter` no topo
   - `TrainingLogger.__init__` aceita parametro novo `enable_tensorboard: bool = True`:
     ```python
     def __init__(self, log_dir: str = "logs", enable_tensorboard: bool = True) -> None:
     ```
   - Apos criar `self._log_dir.mkdir(parents=True, exist_ok=True)`:
     ```python
     self._writer: SummaryWriter | None = None
     if enable_tensorboard:
         self._writer = SummaryWriter(log_dir=str(self._log_dir / "tb"))
     ```

2. Em `log_update`, apos o `print` final:
   ```python
   if self._writer is not None:
       step = self._episode_count
       self._writer.add_scalar("loss/policy", update_result.get("policy_loss", 0.0), step)
       self._writer.add_scalar("loss/value", update_result.get("value_loss", 0.0), step)
       self._writer.add_scalar("policy/entropy", update_result.get("entropy", 0.0), step)
       self._writer.add_scalar("policy/entropy_coeff", update_result.get("entropy_coeff", 0.0), step)
       self._writer.add_scalar("train/avg_reward_50", avg_reward, step)
       self._writer.add_scalar("train/avg_steps_50", avg_steps, step)
       self._writer.add_scalar("train/win_rate_50", win_a / max(n, 1), step)
   ```

3. Em `log_eval`, apos o `print` final:
   ```python
   if self._writer is not None:
       step = self._episode_count
       self._writer.add_scalar("eval/win_rate", eval_result.get("win_rate", 0.0), step)
       self._writer.add_scalar("eval/loss_rate", eval_result.get("loss_rate", 0.0), step)
       self._writer.add_scalar("eval/draw_rate", eval_result.get("draw_rate", 0.0), step)
       self._writer.add_scalar("eval/avg_steps", eval_result.get("avg_steps", 0.0), step)
   ```

4. Em `end_training`, antes do `print` final:
   ```python
   if self._writer is not None:
       self._writer.close()
   ```

5. Rodar `pytest training/tests/test_logger_tensorboard.py -x -q` — **todos os testes do Grupo 1 devem passar**.

6. Rodar `pytest training/tests/ engine/tests/ -x -q` — **todos os 711+ testes existentes devem continuar passando** (compatibilidade reversa via default `enable_tensorboard=True`).

7. Smoke programatico: criar script ad-hoc em `/tmp` que constroi `MAPPOAgent`, `Trainer(log_dir="/tmp/tb_smoke")`, roda `train_phase` com `phase.episodes=30, update_interval=10, eval_interval=10, eval_episodes=5`. Apos rodar, verificar com `ls /tmp/tb_smoke/tb/` que existe `events.out.tfevents.*` e com `cat /tmp/tb_smoke/training.jsonl` que o JSONL continua tendo as linhas esperadas.

---

### Grupo 3 — Estrutura, gitignore e documentacao

**Tarefa:** Criar a estrutura de pastas e atualizar configuracao de versionamento + README.

1. Criar arquivos `.gitkeep`:
   - `logs/runs/.gitkeep` (vazio, garante que a pasta esta versionada)
   - **NAO** criar `logs/scratch/.gitkeep` porque o `.gitignore` vai ignorar `logs/scratch/` inteiro

2. Atualizar `.gitignore`:
   - Remover (se existir) a linha `logs/training.jsonl`
   - Adicionar:
     ```
     logs/scratch/
     logs/training.jsonl
     logs/training_full.log
     ```
   - Garantir que `logs/runs/` e `logs/runs/.gitkeep` sao trackables (nao ignorados)

3. Atualizar `README.md`:
   - Localizar onde explica como rodar o treino (ou criar uma secao no final)
   - Adicionar secao "Visualizando o treino":
     ```markdown
     ## Visualizando o treino

     O `TrainingLogger` grava metricas em dois canais:

     - `logs/<run-dir>/training.jsonl` — log estruturado, source of truth, diff-friendly
     - `logs/<run-dir>/tb/events.out.tfevents.*` — event files do TensorBoard

     Convencao de pastas:

     - `logs/runs/<nome_descritivo>/` — runs marco, versionados via git
     - `logs/scratch/<id>/` — experimentos descartaveis, ignorados pelo git

     Exemplo de treino marco:

     ```bash
     python -m training.train --log-dir logs/runs/2026-04-28_baseline
     ```

     Para visualizar todos os runs versionados lado a lado:

     ```bash
     tensorboard --logdir logs/runs/
     ```

     Abrir no browser: http://localhost:6006

     Metricas disponiveis:
     - `loss/policy`, `loss/value`
     - `policy/entropy`, `policy/entropy_coeff`
     - `train/avg_reward_50`, `train/avg_steps_50`, `train/win_rate_50`
     - `eval/win_rate`, `eval/loss_rate`, `eval/draw_rate`, `eval/avg_steps`
     ```

4. Verificar que `tensorboard` esta acessivel:
   ```bash
   .venv/bin/python -c "from torch.utils.tensorboard import SummaryWriter; print('ok')"
   ```
   - Esperado: `ok`. Se falhar com import error, investigar — `tensorboard` deveria vir como dep transitiva do `torch`. Se nao vier, registrar nota em `notes.md` e adicionar `tensorboard` aos requirements (ainda dentro desta feature).

5. Rodar `git status` e validar que:
   - `.gitignore`, `README.md`, `logs/runs/.gitkeep`, `training/curriculum/logger.py`, `training/tests/test_logger_tensorboard.py` aparecem como modified/added
   - `logs/scratch/` nao aparece (mesmo que tenha conteudo de smoke runs locais)

---

## Condicao de Conclusao

- Todos os criterios de aceitacao em `spec.md` satisfeitos.
- `pytest training/tests/ engine/tests/ -x -q` passa (711+ testes).
- Smoke programatico do Grupo 2 confirma que TB events e JSONL coexistem.
- `tensorboard --logdir logs/runs/` (rodado manualmente pelo usuario) abre o dashboard sem erros.
- Atualizar `.specs/state.md`: status da feature 32 muda de `em desenvolvimento` para `concluida`.
- Atualizar `.specs/notes.md` se durante a implementacao surgir alguma decisao tecnica nao-obvia (ex: tags de scalar com nome diferente do esperado, tratamento de erro do SummaryWriter, etc).
