# Tasks — Feature 19: Inference IA

## Antes de Comecar

Leitura obrigatoria antes de escrever qualquer codigo:

- `CLAUDE.md` — convencoes, estrutura do projeto
- `.specs/features/19_inference_ia/spec.md` — criterios de aceitacao desta feature
- `.specs/design.md` secoes 5.1-5.5 — arquitetura das redes, observacao, acoes, modelos
- `.specs/notes.md` — nota sobre agente IA temporario e interface `get_ai_action`
- `training/agents/networks.py` — PolicyNetwork (arquitetura, get_action_hierarchical)
- `training/agents/mappo.py` — MAPPOAgent.select_action_hierarchical (referencia de como usar a policy)
- `training/environment/observations.py` — encode_observation, OBS_TOTAL_SIZE
- `training/environment/actions.py` — compute_action_mask, NUM_ACTION_TYPES, NUM_TARGETS
- `backend/ai_agent.py` — get_ai_action (interface do agente heuristico)
- `backend/api/routes/ws.py` — _handle_ai_turn (onde integrar inference)
- `backend/sessions.py` — BattleSession (tem campo difficulty)
- `models/easy/` — arquivos .pt existentes para teste

---

## Plano de Execucao

```
Grupo 1 (TDD) ─── sequencial (pausa obrigatoria)
       │
       ▼
Grupo 2 ─── sequencial
       │
       ▼
Grupo 3 ─── sequencial (depende de Grupo 2)
```

- **Grupo 1**: Escrever testes. Parar e aguardar aprovacao.
- **Grupo 2**: Implementar modulo de inference (model_loader + inference_agent).
- **Grupo 3**: Integrar com WS handler. Depende de Grupo 2.

---

### Grupo 1 — Testes (TDD) (um agente)

**Tarefa:** Escrever testes para carregamento de modelos e geracao de acoes via inference.

1. Criar `backend/tests/test_inference.py` com:

   **Carregamento de modelos:**
   - `test_get_policies_loads_all_classes` — `get_policies("easy")` retorna dict com 5 keys: warrior, mage, cleric, archer, assassin. Cada valor e uma PolicyNetwork.
   - `test_get_policies_caches` — chamadas subsequentes retornam o mesmo objeto (cache funciona)
   - `test_get_policies_eval_mode` — todas as policies retornadas estao em `training=False` (eval mode)
   - `test_get_policies_invalid_difficulty` — `get_policies("impossible")` retorna None (diretorio nao existe)
   - `test_get_policies_all_difficulties` — "easy", "normal", "hard" todos carregam com sucesso (modelos existem em models/)

   **Geracao de acoes:**
   - `test_get_inference_action_returns_tuple` — retorna tupla (int, int) com action_type entre 0-9 e target entre 0-79
   - `test_get_inference_action_valid_action_type` — action_type retornado e uma acao que estava unmasked (valida)
   - `test_get_inference_action_with_battle` — criar BattleState simples, carregar policy, gerar acao, verificar que nao levanta exception

   **Fallback:**
   - `test_fallback_when_no_models` — se get_policies retorna None, o sistema usa agente heuristico (testar via WS ou diretamente)

2. Para os testes de inference, usar BattleState.from_config com seed fixo para ter estado deterministic. Carregar policies reais de `models/easy/`.

3. **Parar aqui.** Nao implementar codigo de producao. Aguardar aprovacao dos testes.

---

### Grupo 2 — Modulo de inference (um agente)

**Tarefa:** Criar model_loader e inference_agent no pacote `backend/inference/`.

1. Criar `backend/inference/model_loader.py`:

   ```python
   from pathlib import Path
   import torch
   from training.agents.networks import PolicyNetwork
   from training.environment.observations import OBS_TOTAL_SIZE
   from training.environment.actions import NUM_ACTION_TYPES, NUM_TARGETS

   _CLASS_NAMES = ["warrior", "mage", "cleric", "archer", "assassin"]
   _cache: dict[str, dict[str, PolicyNetwork]] = {}

   def get_policies(difficulty: str) -> dict[str, PolicyNetwork] | None:
       if difficulty in _cache:
           return _cache[difficulty]
       path = Path("models") / difficulty
       if not path.is_dir():
           return None
       policies = {}
       for class_name in _CLASS_NAMES:
           pt_file = path / f"{class_name}.pt"
           if not pt_file.exists():
               return None
           policy = PolicyNetwork(OBS_TOTAL_SIZE, NUM_ACTION_TYPES, NUM_TARGETS)
           policy.load_state_dict(torch.load(pt_file, weights_only=True))
           policy.eval()
           policies[class_name] = policy
       _cache[difficulty] = policies
       return policies

   def clear_cache() -> None:
       _cache.clear()
   ```

2. Criar `backend/inference/inference_agent.py`:

   ```python
   import torch
   from training.agents.networks import PolicyNetwork
   from training.environment.observations import encode_observation
   from training.environment.actions import compute_action_mask
   from engine.systems.battle import BattleState

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
   ```

3. Atualizar `backend/inference/__init__.py`:

   ```python
   from backend.inference.inference_agent import get_inference_action
   from backend.inference.model_loader import clear_cache, get_policies

   __all__ = ["get_inference_action", "get_policies", "clear_cache"]
   ```

---

### Grupo 3 — Integracao com WebSocket (um agente)

**Tarefa:** Modificar o WS handler para usar inference quando modelos estao disponiveis.

1. Modificar `backend/api/routes/ws.py`:

   a. No inicio de `battle_websocket`, apos obter a sessao, carregar policies:
      ```python
      from backend.inference import get_policies
      policies = get_policies(session.difficulty)
      ```

   b. Passar `policies` para `_handle_ai_turn`:
      ```python
      await _handle_ai_turn(websocket, battle, agent, rng, policies)
      ```

   c. Modificar `_handle_ai_turn` para aceitar `policies` e usasr inference:
      ```python
      async def _handle_ai_turn(ws, battle, agent, rng, policies=None):
          while not battle.is_over and battle.current_agent == agent:
              if policies:
                  class_name = battle.get_character(agent).character_class.value
                  policy = policies.get(class_name)
                  if policy:
                      from backend.inference import get_inference_action
                      action_type, target_tile = get_inference_action(battle, agent, policy)
                  else:
                      action_type, target_tile = get_ai_action(battle, agent, rng)
              else:
                  action_type, target_tile = get_ai_action(battle, agent, rng)
              # ... resto do loop inalterado
      ```

2. Rodar testes existentes do WS: `pytest backend/tests/test_api_websocket.py -v` — todos devem passar (os testes criam sessoes diretamente sem modelos, entao o fallback e usado).

3. Rodar testes de inference: `pytest backend/tests/test_inference.py -v`.

4. Rodar testes REST: `pytest backend/tests/test_api_rest.py -v` — nenhuma regressao.

---

## Condicao de Conclusao

- Todos os criterios de aceitacao em spec.md satisfeitos.
- Todos os testes passam com `pytest backend/tests/ -v`.
- Testes do engine continuam passando: `pytest engine/tests/ -v`.
- Atualizar `.specs/state.md`: status da feature 19 para `concluida`.
