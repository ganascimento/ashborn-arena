# Ashborn Arena — Notas Tecnicas

Notas sobre decisoes de implementacao e limitacoes conhecidas. Consultado por `/describe-feature` ao escrever specs e atualizado por `/build-feature` ao concluir features.

---

## Limitacoes Conhecidas (MVP)

Nenhuma limitacao pendente no game engine. Todas as mecanicas de combate foram implementadas na feature 13.

---

## Decisoes de Implementacao

### BattleState — acesso a atributos privados pelo backend

O route `POST /battle/start` acessa `battle._characters`, `battle._positions`, `battle._equipped`, `battle._map_objects` diretamente para serializar o estado inicial. O WS handler (feature 18) e o inference (feature 19) usam a API publica do BattleState (get_character, get_position, etc.). Nao foram adicionados properties publicos para os dicts internos — o engine nao conhece o backend.

### AI team generation — classes aleatorias com builds default

`POST /battle/start` gera o time da IA com classes aleatorias (sem duplicata) e builds default. A dificuldade (easy/normal/hard) determina qual checkpoint MAPPO e carregado pelo modulo de inference (feature 19). Quando modelos nao estao disponiveis, o agente heuristico e usado como fallback.

### WebSocket — agente IA com inference MAPPO + fallback heuristico

Feature 19 integrou inference MAPPO no WS handler. `_handle_ai_turn` recebe `policies` (dict classe→PolicyNetwork) carregadas via `get_policies(session.difficulty)`. Se policies estao disponiveis, usa `get_inference_action`; senao, faz fallback para `get_ai_action` (heuristica). O agente heuristico (`backend/ai_agent.py`) permanece como fallback quando modelos nao estao presentes.

### Inference — cache de modelos global

`backend/inference/model_loader.py` cacheia PolicyNetwork em dict module-level `_cache`. Modelos sao carregados uma vez e reutilizados entre sessoes. `clear_cache()` esta disponivel para testes. Se o processo reiniciar, modelos sao recarregados na primeira chamada.

### WebSocket — protocolo ready/next para sincronizar animacoes

Cada ai_action e enviada individualmente e o servidor espera `{"type": "ready"}` antes de enviar a proxima. O frontend (feature 21+) deve enviar ready apos concluir a animacao de cada acao da IA. Se o frontend nao enviar ready, o servidor fica bloqueado esperando — nao ha timeout implementado.

### WebSocket — extensoes ao protocolo de design.md 6.2

O protocolo implementado estende o design.md 6.2 nos seguintes pontos:
- `turn_start` inclui `pa` (PA restante) e `events` (eventos de inicio de turno como bleed, frozen_skip) alem de `type` e `character`
- `turn_end` e enviado apos cada turno (jogador ou IA) com `character` e `next`
- `skip_event` e enviado para personagens skippados (knocked_out, frozen, dead) antes do turn_start do proximo personagem ativo. Frontend deve tratar ou ignorar.
- `action_result` e `ai_action` incluem campo `events` (lista de eventos do engine serializados)
- ACTION_PASS (9) e tratado como end_turn no protocolo WS
- JSON malformado do cliente e tratado com error message (nao crash)
- `_advance_to_active` chama `check_victory()` apos cada `process_turn_start` — mortes por bleed durante inicio de turno encerram a batalha corretamente (engine so chama check_victory dentro de execute_action)

### _DEFAULT_ABILITIES e _DEFAULT_BUILDS — referenciados pelo backend

O route `battle.py` importa `_DEFAULT_ABILITIES` (private dict do engine) e `_DEFAULT_BUILDS` (definido em `builds.py`). Se `_DEFAULT_ABILITIES` for renomeado no engine, o backend quebra. Considerar tornar publico se isso se tornar um problema.

### calculate_raw_damage — round half up

Formula: `base_damage + math.floor(modifier * scaling + 0.5)`. Usa round-half-up (nao banker's rounding do Python) para ser consistente com a tabela de balanceamento do design.md 2.8.

### Hierarchical action sampling

A PolicyNetwork tem dois heads (type + target) independentes, mas o sampling e sequencial: primeiro samplea o type, depois aplica a target_mask especifica daquele type. Isso garante que toda acao sampleada e valida no environment. O `evaluate_action` usa a mask armazenada no buffer (a do type selecionado).

### PPO update per-class

Cada uma das 5 policies so e atualizada com dados da sua propria classe. O buffer armazena `class_name` por timestep, `get_batches_by_class()` separa os dados, e o update itera por policy com seus proprios batches.

### Terminal reward injection

Apos cada episodio, agentes que nao receberam `done=True` durante o loop tem: (1) rewards pendentes de outros agentes acumulados, (2) VICTORY/DEFEAT injetado na ultima entry do buffer, (3) `done=True` forcado. Isso garante que o GAE sabe que o episodio terminou e que losers veem reward negativo.

### Pending rewards para multi-agent

Em ambiente AEC (1 agente por step), eventos que afetam outros agentes (ALLY_DEAD, KILL) geram rewards que sao acumulados em `pending_rewards` e somados ao reward do agente no seu proximo turno.

---

## Resolvidos

- TurnManager.remove_entity no ultimo personagem: BattleState protege contra isso (feature 13)
- Chama Sagrada/Barreira Arcana dual attr (INT/SAB): `_get_scaling_attr` seleciona SAB para Clerigo (feature 13)
- Global state size variavel: `encode_global_state` retorna tamanho fixo 972 (code review #1)
- Action-target independente: hierarchical sampling resolve (code review #1)
- Losers sem DEFEAT/-10: terminal injection resolve (code review #2)
- PPO todas policies em todos dados: per-class batching resolve (code review #3)
- Adam momentum decay: `zero_grad(set_to_none=True)` (code review #4)
- Grid.remove_occupant memory leak: limpa entradas vazias (code review engine)
- LoS interpolacao: trocado para Bresenham (code review engine)
