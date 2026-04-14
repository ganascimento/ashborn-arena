# Tasks — Feature 18: API WebSocket

## Antes de Comecar

Leitura obrigatoria antes de escrever qualquer codigo:

- `CLAUDE.md` — convencoes, estrutura do projeto
- `.specs/features/18_api_websocket/spec.md` — criterios de aceitacao desta feature
- `.specs/design.md` secao 6.2 — protocolo WebSocket (mensagens, fluxo do turno da IA)
- `.specs/notes.md` — nota sobre acesso a atributos privados do BattleState pelo backend
- `engine/systems/battle.py` — BattleState completo: execute_action, process_turn_start, process_turn_end, ACTION_* constants, _tile_to_pos, _pos_to_tile
- `engine/models/ability.py` — Ability, ABILITIES, AbilityTarget
- `engine/models/character.py` — Character, CharacterClass, CharacterState
- `engine/models/position.py` — Position (namedtuple com x, y)
- `backend/sessions.py` — BattleSession, SessionManager, session_manager
- `backend/api/routes/battle.py` — POST /battle/start (para entender como a sessao e criada)
- `backend/main.py` — app FastAPI atual

---

## Plano de Execucao

```
Grupo 1 (TDD) ─── sequencial (pausa obrigatoria)
       │
       ▼
Grupo 2 ──┬── paralelo
Grupo 3 ──┘
       │
       ▼
Grupo 4 ─── sequencial (depende de 2 + 3)
```

- **Grupo 1**: Escrever todos os testes. Parar e aguardar aprovacao.
- **Grupo 2** e **Grupo 3**: Rodam em paralelo apos aprovacao dos testes.
- **Grupo 4**: Depende de Grupo 2 (AI agent) e Grupo 3 (event helpers). Roda por ultimo.

---

### Grupo 1 — Testes (TDD) (um agente)

**Tarefa:** Escrever os testes do endpoint WebSocket usando FastAPI TestClient com WebSocket support.

1. Criar `backend/tests/test_api_websocket.py`.

2. Helper para criar sessao de teste controlada:

   ```python
   def create_test_session(team_a_classes, team_b_classes, seed=42):
       """Cria BattleState com RNG fixo e insere no session_manager.
       Retorna (session_id, battle_state, player_ids, ai_ids).
       Usa builds default para ambos os times."""
   ```

   Usar `BattleState.from_config(...)` com `rng=random.Random(seed)` para ter ordem de iniciativa deterministica. Usar builds default `(0,0,0,0,10)` ou similar simples. O importante e que a ordem dos turnos seja previsivel para os testes.

   Nao usar POST /battle/start nos testes WS — criar sessoes diretamente para ter controle total.

3. Testes de conexao:

   - `test_connect_valid_session` — cria sessao, conecta em `/battle/{session_id}`, recebe turn_start como primeira mensagem
   - `test_connect_invalid_session` — conecta com UUID invalido, conexao fechada (WebSocketDisconnect)

4. Testes de acao do jogador (criar sessao onde o primeiro turno e do jogador):

   - `test_player_move` — envia action move com target valido, recebe action_result com type "action_result" e action "move"
   - `test_player_end_turn` — envia action end_turn, recebe action_result seguido de turn_end e turn_start do proximo personagem
   - `test_player_wrong_character` — envia acao com entity_id de personagem IA, recebe error
   - `test_player_not_current_agent` — envia acao com entity_id de personagem do jogador que nao e o current_agent, recebe error

5. Testes de turno da IA:

   - `test_ai_turn_sends_actions` — criar sessao onde o primeiro turno e da IA. Receber turn_start, depois receber ai_action. Enviar ready. Receber mais ai_actions ou turn_end. Verificar que ai_actions tem type "ai_action".
   - `test_ai_turn_waits_for_ready` — verificar que o servidor so envia a proxima ai_action apos receber ready

6. Teste de fim de batalha:

   - `test_battle_end_victory` — criar sessao com 1v1 (player warrior forte vs AI fraco), executar acoes ate matar o inimigo, verificar que recebe `{"type": "battle_end", "result": "victory"}`

7. Teste de serializacao:

   - `test_events_serialized_correctly` — verificar que Positions nos eventos sao listas [x, y], nao objetos

8. Teste de cleanup:

   - `test_session_removed_after_battle_end` — apos battle_end, session_manager.get(session_id) retorna None

9. **Parar aqui.** Nao implementar codigo de producao. Aguardar aprovacao dos testes.

---

### Grupo 2 — Agente IA temporario (um agente)

**Tarefa:** Criar modulo `backend/ai_agent.py` com agente que gera acoes aleatorias validas.

1. Criar `backend/ai_agent.py` com a funcao principal:

   ```python
   import random as _random
   from engine.systems.battle import BattleState, ACTION_MOVE, ACTION_BASIC, ACTION_ABILITY_1, ACTION_END_TURN

   def get_ai_action(battle: BattleState, entity_id: str, rng: _random.Random) -> tuple[int, int]:
       """Retorna (action_type, target_tile) — uma acao valida para o agente."""
   ```

2. Logica de decisao (heuristica simples, nao IA treinada):

   a. **Tentar atacar** — verificar se ha inimigos no alcance de habilidades ou ataque basico:
      - Para cada ability equipada (slot 0-4): checar PA >= custo, cooldown ready, inimigo no alcance
      - Para basic attack: checar PA >= 2, inimigo no alcance
      - Se ha ataque disponivel: escolher um aleatoriamente, retornar (action_type, tile do alvo)

   b. **Mover em direcao ao inimigo mais proximo** — se nenhum ataque valido:
      - Obter reachable_tiles via `battle.get_reachable_tiles(entity_id)`
      - Encontrar inimigo mais proximo
      - Escolher o tile alcancavel mais perto do inimigo
      - Retornar (ACTION_MOVE, target_tile)

   c. **Encerrar turno** — se nao pode atacar nem mover util:
      - Retornar (ACTION_END_TURN, 0)

3. Funcoes auxiliares necessarias dentro do modulo:

   ```python
   def _get_enemies(battle: BattleState, entity_id: str) -> list[str]:
       """Retorna entity_ids dos inimigos vivos."""

   def _pos_to_tile(pos: Position) -> int:
       return pos.y * 10 + pos.x

   def _enemy_in_range(battle: BattleState, attacker_pos: Position, target_pos: Position, max_range: int) -> bool:
       """Chebyshev distance <= max_range."""

   def _is_ability_usable(battle: BattleState, entity_id: str, slot: int, ability: Ability) -> bool:
       """PA suficiente, cooldown ready, ha alvo valido."""
   ```

4. Para habilidades com LoS (ranged): usar `has_line_of_sight` de `engine.systems.line_of_sight`.

5. Para alvos de habilidades AOE: escolher tile do inimigo como centro (simplificacao — nao otimiza posicionamento AoE).

6. Para habilidades SELF (buffs): target e a propria posicao do agente.

7. Para habilidades SINGLE_ALLY (cura, buff de aliado): escolher aliado com menor HP percentual.

---

### Grupo 3 — Helpers de serializacao e protocolo (um agente)

**Tarefa:** Criar modulo de helpers para serializar eventos do engine em mensagens JSON do protocolo WS.

1. Criar `backend/api/ws_helpers.py` com:

   ```python
   from engine.models.position import Position

   def serialize_events(events: list[dict]) -> list[dict]:
       """Converte todos Position nos eventos para [x, y]."""

   def make_turn_start(character: str, pa: int, events: list[dict]) -> dict:
       return {"type": "turn_start", "character": character, "pa": pa, "events": serialize_events(events)}

   def make_turn_end(character: str, next_character: str) -> dict:
       return {"type": "turn_end", "character": character, "next": next_character}

   def make_action_result(character: str, action: str, events: list[dict], **extra) -> dict:
       msg = {"type": "action_result", "character": character, "action": action, "events": serialize_events(events)}
       msg.update(extra)
       return msg

   def make_ai_action(character: str, action: str, events: list[dict], **extra) -> dict:
       msg = {"type": "ai_action", "character": character, "action": action, "events": serialize_events(events)}
       msg.update(extra)
       return msg

   def make_battle_end(result: str) -> dict:
       return {"type": "battle_end", "result": result}

   def make_error(message: str) -> dict:
       return {"type": "error", "message": message}
   ```

2. `serialize_events` deve percorrer recursivamente cada dict nos eventos:
   - Se um valor e `Position`, converter para `[pos.x, pos.y]`
   - Se um valor e um dict, recursivamente serializar
   - Se um valor e uma lista, recursivamente serializar cada item
   - Outros valores (str, int, float, bool, None) passam inalterados

---

### Grupo 4 — WebSocket handler e registro (um agente)

**Tarefa:** Implementar o endpoint WebSocket e registrar no app FastAPI.

1. Criar `backend/api/routes/ws.py`:

   ```python
   from fastapi import APIRouter, WebSocket, WebSocketDisconnect

   router = APIRouter()

   @router.websocket("/battle/{session_id}")
   async def battle_websocket(websocket: WebSocket, session_id: str):
       ...
   ```

2. Fluxo principal do handler:

   ```python
   async def battle_websocket(websocket: WebSocket, session_id: str):
       session = session_manager.get(session_id)
       if not session:
           await websocket.close(code=4004)
           return

       await websocket.accept()
       battle = session.battle_state
       player_ids = set(session.player_entity_ids)
       rng = random.Random()

       try:
           # Loop principal: processar turnos ate batalha acabar
           while not battle.is_over:
               # Avancar turnos skippados (knocked_out, frozen, dead)
               agent = await _advance_to_active(websocket, battle)
               if agent is None or battle.is_over:
                   break

               if agent in player_ids:
                   await _handle_player_turn(websocket, battle, agent, player_ids)
               else:
                   await _handle_ai_turn(websocket, battle, agent, rng)

           # Batalha acabou
           result = "victory" if battle.winner == "team_a" else "defeat"
           await websocket.send_json(make_battle_end(result))
       except WebSocketDisconnect:
           pass
       finally:
           session_manager.remove(session_id)
   ```

3. `_advance_to_active`:

   ```python
   async def _advance_to_active(ws, battle) -> str | None:
       """Processa turn_start ate encontrar um agente ACTIVE. Envia eventos de skip (bleed, frozen)."""
       while not battle.is_over:
           events = battle.process_turn_start()
           agent = battle.current_agent
           char = battle.get_character(agent)

           if char.state == CharacterState.ACTIVE:
               pa = battle.get_pa(agent)
               await ws.send_json(make_turn_start(agent, pa, events))
               return agent

           # Agente foi skippado — enviar eventos de skip e continuar loop
           if events:
               for event in serialize_events(events):
                   await ws.send_json({"type": "skip_event", **event})

       return None
   ```

4. `_handle_player_turn`:

   ```python
   async def _handle_player_turn(ws, battle, agent, player_ids):
       """Recebe acoes do jogador ate end_turn ou battle_end."""
       while not battle.is_over:
           data = await ws.receive_json()

           if data.get("type") == "ready":
               continue  # Ignorar ready fora de turno de IA

           if data.get("type") != "action":
               await ws.send_json(make_error("Expected action message"))
               continue

           # Validar character
           char_id = data.get("character")
           if char_id not in player_ids:
               await ws.send_json(make_error(f"Character {char_id} is not a player character"))
               continue
           if char_id != battle.current_agent:
               await ws.send_json(make_error(f"Not {char_id}'s turn, current is {battle.current_agent}"))
               continue

           # Traduzir acao
           action_str = data.get("action")
           action_type, target_tile = _translate_player_action(battle, char_id, data)
           if action_type is None:
               await ws.send_json(make_error(f"Invalid action: {action_str}"))
               continue

           # Executar
           events = battle.execute_action(action_type, target_tile)
           await ws.send_json(make_action_result(char_id, action_str, events))

           if action_str == "end_turn" or battle.is_over:
               return
   ```

5. `_translate_player_action` — traduz mensagem do cliente para (action_type, target_tile):

   - `"move"` + target [x,y] → (ACTION_MOVE, y*10+x)
   - `"basic_attack"` + target [x,y] → (ACTION_BASIC, y*10+x)
   - `"ability"` + ability_id + target [x,y] → encontrar slot da ability no equipped do personagem, (ACTION_ABILITY_1 + slot, y*10+x)
   - `"end_turn"` → (ACTION_END_TURN, 0)
   - Retorna (None, None) se invalido

   Para encontrar o slot da ability: iterar `battle.get_equipped_abilities(char_id)` e comparar `ability.id == ability_id`.

6. `_handle_ai_turn`:

   ```python
   async def _handle_ai_turn(ws, battle, agent, rng):
       """Executa acoes da IA uma a uma com protocolo ready."""
       while not battle.is_over and battle.current_agent == agent:
           action_type, target_tile = get_ai_action(battle, agent, rng)

           events = battle.execute_action(action_type, target_tile)

           # Determinar nome da acao para o protocolo
           action_name = _action_type_to_name(action_type)
           await ws.send_json(make_ai_action(agent, action_name, events))

           if action_type == ACTION_END_TURN:
               return

           # Aguardar ready do cliente antes da proxima acao
           data = await ws.receive_json()
           # Aceitar ready, ignorar outros tipos
   ```

7. Atualizar `backend/api/routes/__init__.py` — adicionar `ws_router`.

8. Atualizar `backend/main.py` — registrar `ws_router`:
   ```python
   from backend.api.routes import ws_router
   app.include_router(ws_router)
   ```

9. Rodar todos os testes: `pytest backend/tests/test_api_websocket.py -v`. Todos devem passar.

10. Rodar tambem os testes REST para confirmar que nao houve regressao: `pytest backend/tests/test_api_rest.py -v`.

---

## Condicao de Conclusao

- Todos os criterios de aceitacao em spec.md satisfeitos.
- Todos os testes passam com `pytest backend/tests/ -v`.
- Testes do engine continuam passando: `pytest engine/tests/ -v`.
- Atualizar `.specs/state.md`: status da feature 18 para `concluida`.
