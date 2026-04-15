# Ashborn Arena — Notas Tecnicas

Notas sobre decisoes de implementacao e limitacoes conhecidas. Consultado por `/describe-feature` ao escrever specs e atualizado por `/build-feature` ao concluir features.

---

## Limitacoes Conhecidas (MVP)

Nenhuma limitacao pendente no game engine. Todas as mecanicas de combate foram implementadas na feature 13.

---

## Decisoes de Implementacao

### Frontend — game dimensions 1280x720

Feature 20 alterou o canvas do Phaser de 800x600 para 1280x720 com `Scale.FIT` + `Scale.CENTER_BOTH`. A tela de preparacao precisa de espaco para o painel de classes (esquerda) + painel de build (direita) com 11 habilidades em 2 colunas.

### Frontend — happy-dom para testes

`vitest` usa `happy-dom` como environment (nao jsdom). jsdom tem incompatibilidade ESM com a versao atual do Node. happy-dom fornece localStorage e DOM suficiente para os testes unitarios.

### Frontend — Scene keys (resolvido)

Feature 21 substituiu BattlePlaceholderScene. Feature 24 substituiu ResultPlaceholderScene. Keys finais: `"MenuScene"`, `"PreparationScene"`, `"BattleScene"`, `"ResultScene"`. Todos os placeholders removidos.

### Frontend — processEvents defensivo para field names

`BattleScene.updateStateFromEvent()` e `BattleAnimations.processEventsAnimated()` aceitam field names flexiveis do backend: `entity`/`character` para ator, `to`/`position` para destino, `amount`/`damage`/`heal` para valor. Posicoes como `[x, y]` ou `{ x, y }`. Feature 22 refatorou `processEvents` em dois: `updateStateFromEvent` (estado puro, sem sprites) e `processEventsAnimated` (animacoes via tweens). Feature 23 que adiciona feedback visual deve estender `processEventsAnimated` ou consumir os mesmos callbacks.

### Frontend — WebSocket readyState check

`BattleWsClient.send()` usa `readyState === 1` (nao `WebSocket.OPEN`) porque `WebSocket.OPEN` como static nao esta disponivel em happy-dom. Funciona corretamente — `1` e o valor padrao de `OPEN`.

### Frontend — arquitetura de animacoes e ability bar (feature 22)

`BattleScene` delega animacoes para `BattleAnimations` (battle-animations.ts) e a barra de habilidades para `BattleAbilityBar` (battle-ability-bar.ts). Ambos recebem `Phaser.Scene` no constructor. `processEventsAnimated` e async — os handlers WS (`handleAiAction`, `handleActionResult`, `handleTurnStart`) sao async e usam `isAnimating` flag para bloquear input durante animacoes. O `ready` do protocolo WS so e enviado apos todas as animacoes completarem.

### Frontend — PA e cooldowns rastreados localmente

PA vem de `turn_start.pa` e e decrementado localmente apos cada `action_result` (custo conhecido: 2 para basic_attack, ability.pa_cost para habilidades, ceil(dist/2) para move). Cooldowns rastreados por personagem do jogador em `playerCooldowns: Map<charId, Map<abilityId, turnsRestantes>>`. Tick de cooldowns acontece no `handleTurnStart` de cada personagem. O servidor e a fonte de verdade — se rejeitar uma acao, o jogador ve a mensagem de erro mas o PA local pode ficar dessincronizado ate o proximo turn_start.

### Frontend — dead characters permanecem no Map (resolvido)

Feature 22 nao remove personagens mortos do `characters` Map apos animacao de morte. Feature 23 trata isso corretamente: `updateAllBars` chama `removeHpBar` para entries com `status === "dead"`, e `refreshHud` filtra `status === "dead"` ao atualizar status icons.

### Frontend — HUD modules e overlays (feature 23)

`BattleHud` (battle-hud.ts) gerencia HP bars, status icons e floating text. `BattleRangeOverlay` (battle-range-overlay.ts) gerencia highlights de alcance e preview de AoE. Ambos instanciados no `create()` do BattleScene. HP bars usam depth 100-101, floating text depth 200, range overlay depth 50-51 (abaixo de personagens). `refreshHud()` e chamado apos cada batch de animacoes nos 3 handlers async.

### Frontend — efeitos ativos rastreados localmente

`BattleScene.activeEffects: Map<string, Set<string>>` rastreia tags de efeitos por personagem, atualizados via `effect_applied`/`effect_expired` em `updateStateFromEvent`. Status icons exibem abreviacoes (BLD, PSN, SLW, etc.) com cor por prioridade: controle (roxo) > debuff (laranja) > DOT (vermelho) > elemental (azul). Se o backend nao enviar `effect_expired`, os icons ficam presos — nao ha timeout local.

### Frontend — AoE preview assume raio 1

Preview de AoE mostra 3x3 tiles (raio 1) para todas as habilidades com target "aoe". O engine usa raio 1 para AoE no design.md. Se futuras habilidades usarem raio diferente, precisara de campo `aoe_radius` no AbilityOut.

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
