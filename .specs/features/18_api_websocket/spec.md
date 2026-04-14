# Feature 18 — API WebSocket

## Objetivo

Implementar o endpoint WebSocket que controla o fluxo da batalha em tempo real. O cliente conecta a uma sessao criada via POST /battle/start (feature 17), envia acoes do jogador, e recebe resultados + acoes da IA uma a uma (com protocolo ready/next para sincronizar animacoes). Inclui um agente IA temporario (acoes aleatorias validas) que sera substituido pela inference MAPPO na feature 19. Esta feature desbloqueia o frontend de batalha (features 21-24).

---

## Referencia nos Specs

- prd.md: secoes 2.2 (sistema de turnos e PA), 2.4 (ataque de oportunidade), 7.1 (plataforma), 7.3 (fluxo do jogador — tela de batalha)
- design.md: secao 6.2 (protocolo WebSocket — mensagens cliente→servidor e servidor→cliente, fluxo do turno da IA)

---

## Arquivos Envolvidos

**Criar:**

- `backend/api/routes/ws.py` — WebSocket endpoint /battle/{session_id}
- `backend/ai_agent.py` — Agente IA temporario (acoes aleatorias validas)
- `backend/tests/test_api_websocket.py` — Testes do endpoint WebSocket

**Modificar:**

- `backend/main.py` — Registrar WebSocket router
- `backend/api/routes/__init__.py` — Re-exportar WS router

---

## Criterios de Aceitacao

### Conexao

- [ ] Cliente conecta em `ws://host/battle/{session_id}` com session_id valido (criado por POST /battle/start) → conexao aceita
- [ ] Cliente conecta com session_id inexistente → conexao fechada com codigo 4004
- [ ] Apos conexao aceita, servidor envia `{"type": "turn_start", "character": "<entity_id>", "pa": 4, "events": [...]}` para o primeiro personagem ativo na ordem de iniciativa

### Mensagens cliente → servidor

- [ ] `{"type": "action", "character": "<eid>", "action": "move", "target": [x, y]}` → servidor executa BattleState.execute_action(ACTION_MOVE, tile) e retorna action_result com eventos (inclui "from" e "to")
- [ ] `{"type": "action", "character": "<eid>", "action": "basic_attack", "target": [x, y]}` → servidor executa ACTION_BASIC e retorna action_result com damage, crit, evaded
- [ ] `{"type": "action", "character": "<eid>", "action": "ability", "ability": "<ability_id>", "target": [x, y]}` → servidor resolve o slot da ability pelo id, executa ACTION_ABILITY_N e retorna action_result com eventos
- [ ] `{"type": "action", "character": "<eid>", "action": "end_turn"}` → servidor executa ACTION_END_TURN, retorna action_result com eventos de fim de turno (DOTs, HOTs), depois envia turn_end e turn_start do proximo personagem
- [ ] `{"type": "ready"}` → indica ao servidor que o cliente terminou de animar; servidor envia a proxima acao da IA
- [ ] Acao enviada com character que nao e do jogador → servidor envia `{"type": "error", "message": "..."}`
- [ ] Acao enviada para personagem que nao e o current_agent → servidor envia `{"type": "error", "message": "..."}`

### Mensagens servidor → cliente

- [ ] `action_result` inclui: type, character, action, events (lista de dicts serializados do engine — Positions convertidas para [x,y])
- [ ] `turn_start` inclui: type, character, pa (PA restante), events (lista de eventos de process_turn_start — bleed, frozen_skip, delayed_resolve, effect_expired)
- [ ] `turn_end` inclui: type, character, next (entity_id do proximo personagem)
- [ ] `ai_action` inclui: type, character, action (move/basic_attack/ability/end_turn), events (lista de eventos do engine)
- [ ] `battle_end` inclui: type, result ("victory" se team_a vence, "defeat" se team_b vence)
- [ ] `error` inclui: type, message

### Fluxo de turno da IA

- [ ] Quando o current_agent e um personagem IA, servidor envia turn_start e executa acoes automaticamente
- [ ] Cada acao da IA e enviada como mensagem `ai_action` separada
- [ ] Servidor aguarda mensagem `{"type": "ready"}` do cliente antes de enviar a proxima ai_action
- [ ] Quando a IA termina o turno (end_turn ou PA esgotado), servidor envia ai_action de end_turn seguido de turn_end
- [ ] Personagens skippados (knocked_out com bleed, frozen, dead) tem seus eventos enviados no turn_start e o turno avanca automaticamente ate encontrar um personagem ACTIVE

### Agente IA temporario

- [ ] Modulo `backend/ai_agent.py` expoe funcao que retorna uma acao valida (action_type, target_tile) dado um BattleState e entity_id
- [ ] Agente gera apenas acoes validas: respeita PA, cooldowns, alcance, LoS
- [ ] Agente prioriza atacar sobre mover aleatoriamente (heuristica minima para partidas nao degeneradas)
- [ ] Agente sempre termina o turno (encerra quando PA insuficiente para qualquer acao util)

### Serializacao de eventos

- [ ] Objetos Position no engine sao convertidos para listas [x, y] na serializacao JSON
- [ ] Todos os campos dos eventos do engine sao serializaveis (sem objetos Python complexos no JSON)

### Integracao

- [ ] WebSocket funciona lado a lado com os endpoints REST (GET /builds/defaults, POST /battle/start, GET /health)
- [ ] Sessao e removida do session_manager quando a batalha termina ou a conexao e fechada

---

## Fora do Escopo

- Inference MAPPO com checkpoints .pt (feature 19 — substitui o agente aleatorio)
- Frontend / rendering de animacoes (features 21-24)
- Reconnect de WebSocket apos desconexao (pode adicionar depois)
- Multiplos clientes conectados a mesma sessao (1 sessao = 1 conexao)
- Timeout de inatividade do jogador (pode adicionar depois)
- Persistencia de estado de batalha entre reconexoes (sem banco, sessao em memoria)
