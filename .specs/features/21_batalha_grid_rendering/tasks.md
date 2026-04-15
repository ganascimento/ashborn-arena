# Tasks — Feature 21: Batalha — Grid e Rendering

## Antes de Comecar

Ler obrigatoriamente antes de escrever qualquer codigo:

- `CLAUDE.md` — stack, estrutura, convencoes (ingles, sem docstrings, models separadas)
- `.specs/features/21_batalha_grid_rendering/spec.md` — criterios de aceitacao desta feature
- `.specs/notes.md` — protocolo ready/next do WS, extensoes ao protocolo, BattlePlaceholderScene key, processEvents defensivo, readyState check
- `.specs/prd.md` secoes 6.1-6.6 — grid 10x8, movimentacao, objetos, spawn zones
- `.specs/design.md` secao 6.2 — protocolo WebSocket completo (mensagens server→client e client→server)
- `frontend/src/network/types.ts` — tipos TypeScript existentes
- `frontend/src/scenes/BattlePlaceholderScene.ts` — placeholder a ser substituido
- `frontend/src/main.ts` — setup atual do Phaser

---

## Plano de Execucao

```
Grupo 1 (TDD)       — testes do WS client, pausa obrigatoria
         |
Grupo 2              — WS types + WS client
         |
Grupo 3              — BattleScene (grid + entidades + estado + turnos + WS)
         |
Grupo 4              — Wiring: main.ts, remover placeholder, placeholder resultado
```

Execucao sequencial — cada grupo depende do anterior. O WS client e base para a BattleScene.

---

### Grupo 1 — Testes do WS Client (TDD)

**Tarefa:** Escrever testes unitarios para o WebSocket client. Nao implementar producao.

1. Adicionar tipos WS em `frontend/src/network/types.ts` (necessario para testes compilarem):

   Mensagens server→client:
   ```typescript
   interface WsTurnStart { type: "turn_start"; character: string; pa: number; events: unknown[] }
   interface WsActionResult { type: "action_result"; character: string; action: string; events: unknown[] }
   interface WsAiAction { type: "ai_action"; character: string; action: string; events: unknown[] }
   interface WsTurnEnd { type: "turn_end"; character: string; next: string }
   interface WsSkipEvent { type: "skip_event"; [key: string]: unknown }
   interface WsBattleEnd { type: "battle_end"; result: "victory" | "defeat" }
   interface WsError { type: "error"; message: string }
   type ServerMessage = WsTurnStart | WsActionResult | WsAiAction | WsTurnEnd | WsSkipEvent | WsBattleEnd | WsError
   ```

   Mensagens client→server:
   ```typescript
   interface PlayerMoveAction { type: "action"; character: string; action: "move"; target: [number, number] }
   interface PlayerAttackAction { type: "action"; character: string; action: "basic_attack"; target: [number, number] }
   interface PlayerAbilityAction { type: "action"; character: string; action: "ability"; ability: string; target: [number, number] }
   interface PlayerEndTurnAction { type: "action"; character: string; action: "end_turn" }
   interface PlayerReady { type: "ready" }
   type ClientMessage = PlayerMoveAction | PlayerAttackAction | PlayerAbilityAction | PlayerEndTurnAction | PlayerReady
   ```

2. Criar stub `frontend/src/network/ws-client.ts`:
   ```typescript
   export class BattleWsClient {
     constructor(sessionId: string, handlers: WsHandlers) { throw new Error("Not implemented"); }
     connect(): void { throw new Error("Not implemented"); }
     sendMove(character: string, target: [number, number]): void { throw new Error("Not implemented"); }
     sendBasicAttack(character: string, target: [number, number]): void { throw new Error("Not implemented"); }
     sendEndTurn(character: string): void { throw new Error("Not implemented"); }
     sendReady(): void { throw new Error("Not implemented"); }
     disconnect(): void { throw new Error("Not implemented"); }
   }
   ```

   `WsHandlers` interface:
   ```typescript
   interface WsHandlers {
     onTurnStart: (msg: WsTurnStart) => void;
     onActionResult: (msg: WsActionResult) => void;
     onAiAction: (msg: WsAiAction) => void;
     onTurnEnd: (msg: WsTurnEnd) => void;
     onSkipEvent: (msg: WsSkipEvent) => void;
     onBattleEnd: (msg: WsBattleEnd) => void;
     onError: (msg: WsError) => void;
     onDisconnect: () => void;
   }
   ```

3. Criar `frontend/src/network/__tests__/ws-client.test.ts`:
   - Mock global WebSocket (usar `vi.fn()` para simular WebSocket)
   - Testar `connect()`: cria WebSocket com URL `ws://localhost:8000/battle/{sessionId}`
   - Testar dispatch de mensagens: simular `ws.onmessage` com cada tipo de ServerMessage, verificar que o handler correspondente e chamado
   - Testar `sendMove(character, [x, y])`: verificar que `ws.send` e chamado com JSON `{ type: "action", character, action: "move", target: [x, y] }`
   - Testar `sendBasicAttack(character, [x, y])`: verificar JSON `{ type: "action", character, action: "basic_attack", target: [x, y] }`
   - Testar `sendEndTurn(character)`: verificar JSON `{ type: "action", character, action: "end_turn" }`
   - Testar `sendReady()`: verificar JSON `{ type: "ready" }`
   - Testar `disconnect()`: verificar que `ws.close()` e chamado
   - Testar `onclose`/`onerror`: verificar que handler `onDisconnect` e chamado
   - Testar que `send()` usa `readyState === 1` (nao `WebSocket.OPEN`) para verificar conexao aberta (happy-dom compat — notes.md)

**Parar apos criar os testes. Nao implementar logica de producao. Aguardar aprovacao do usuario.**

---

### Grupo 2 — WebSocket Client (um agente)

**Tarefa:** Implementar o cliente WebSocket com tipagem completa e protocolo ready/next.

1. Verificar que os tipos WS ja existem em `frontend/src/network/types.ts` (criados no Grupo 1).

2. Implementar `frontend/src/network/ws-client.ts`:
   - Classe `BattleWsClient`:
     - `constructor(sessionId: string, handlers: WsHandlers)`: salva sessionId e handlers
     - `connect()`: cria `new WebSocket("ws://localhost:8000/battle/${sessionId}")`
       - `ws.onmessage`: parseia JSON, identifica `type`, despacha para handler correspondente
       - `ws.onclose`: chama `handlers.onDisconnect()`
       - `ws.onerror`: chama `handlers.onDisconnect()`
     - `sendMove(character, target)`: envia `{ type: "action", character, action: "move", target }`
     - `sendBasicAttack(character, target)`: envia `{ type: "action", character, action: "basic_attack", target }`
     - `sendAbility(character, ability, target)`: envia `{ type: "action", character, action: "ability", ability, target }`
     - `sendEndTurn(character)`: envia `{ type: "action", character, action: "end_turn" }`
     - `sendReady()`: envia `{ type: "ready" }`
     - `disconnect()`: chama `ws.close()` se ws estiver aberto
   - `send()` usa `readyState === 1` (nao `WebSocket.OPEN`) para verificar conexao — happy-dom compat (notes.md)
   - Constante `WS_BASE_URL = "ws://localhost:8000"` no topo do arquivo
   - JSON malformado do servidor: logar no console, nao crashar

3. Executar testes: `npm run test` — todos os testes do WS client devem passar.

---

### Grupo 3 — BattleScene (um agente)

**Tarefa:** Implementar a cena de batalha completa com grid, entidades, estado e fluxo de turnos integrado ao WS client.

1. Criar `frontend/src/scenes/BattleScene.ts`:
   - Classe `BattleScene extends Phaser.Scene` com key `"BattleScene"` (mesma key do placeholder — notes.md)
   - Recebe `{ session_id: string, initial_state: InitialBattleState }` via `init(data)`

2. Constantes de layout:
   - `TILE_SIZE = 64`
   - `GRID_OFFSET_X = 32` (margem esquerda)
   - `GRID_OFFSET_Y = 104` (margem topo, espaco para indicador de turno)
   - `GRID_COLS = 10`, `GRID_ROWS = 8`
   - Grid area: 640x512px, posicionado a esquerda, deixando ~600px a direita para HUD futuro

3. Estado interno da cena:
   ```typescript
   private characters: Map<string, { data: CharacterOut; sprite: Phaser.GameObjects.Container; status: "active" | "knocked_out" | "dead" }>
   private mapObjects: Map<string, { data: MapObjectOut; sprite: Phaser.GameObjects.Rectangle }>
   private currentCharacter: string
   private isPlayerTurn: boolean
   private wsClient: BattleWsClient
   ```

4. Metodo `create()`:
   - Renderizar grid: 2 loops (x 0-9, y 0-7), criar `Phaser.GameObjects.Rectangle` por tile
     - Cor alternada: tile claro `#3a3a5c` e escuro `#2a2a4c` baseado em `(x + y) % 2`
     - Cada tile interativo (`setInteractive()`)
     - `tile.on("pointerdown")` → chama `onTileClick(x, y)`
   - Renderizar objetos de mapa do `initial_state.map_objects`:
     - Criar retangulo colorido por tipo no tile correspondente
     - Cores: crate/barrel=#8B4513, tree=#228B22, rock=#808080, bush=#90EE90, puddle=#87CEEB
     - Objetos com blocks_movement=true: borda branca (`setStrokeStyle(2, 0xffffff)`)
   - Renderizar personagens do `initial_state.characters`:
     - Criar Container por personagem: circulo (raio ~24px) + texto (abreviacao classe)
     - Cor: team="player" → #4488ff, team="ai" → #ff4444
     - Abreviacoes: warrior→G, mage→M, cleric→C, archer→A, assassin→As
     - Posicionar no centro do tile: `GRID_OFFSET_X + pos.x * TILE_SIZE + TILE_SIZE/2`, idem Y
   - Renderizar indicador de turno:
     - Texto no topo: "Turno de: {entity_id}" com cor por time
     - Texto "Seu turno" / "Turno da IA" abaixo
   - Renderizar botao "Encerrar Turno":
     - Texto interativo, visivel apenas no turno do jogador
     - On click: `wsClient.sendEndTurn(currentCharacter)`
   - Conectar WS client:
     - Criar `BattleWsClient(session_id, handlers)` com handlers mapeados para metodos da cena
     - Chamar `wsClient.connect()`

5. Handler `onTileClick(x, y)`:
   - Se nao e turno do jogador → ignorar
   - Verificar se tile tem inimigo → `wsClient.sendBasicAttack(currentCharacter, [x, y])`
   - Se tile vazio → `wsClient.sendMove(currentCharacter, [x, y])`
   - Se tile tem aliado ou objeto → ignorar

6. Handlers WS:
   - `onTurnStart(msg)`: atualizar `currentCharacter` e `isPlayerTurn`, atualizar indicador visual, mostrar/esconder botao encerrar turno
   - `onActionResult(msg)`: processar eventos — atualizar posicoes, HP, status de entidades
   - `onAiAction(msg)`: processar eventos (mesmo que actionResult), depois `wsClient.sendReady()`
   - `onTurnEnd(msg)`: atualizar currentCharacter para `msg.next`, atualizar indicador
   - `onSkipEvent(msg)`: noop visual (personagem ja estava inativo)
   - `onBattleEnd(msg)`: `wsClient.disconnect()`, `this.scene.start("ResultScene", { result: msg.result })`
   - `onError(msg)`: exibir texto de erro na tela
   - `onDisconnect()`: exibir "Conexao perdida" na tela

7. Processamento de eventos (metodo privado `processEvents(events)`):
   - Aceitar field names flexiveis do backend: `entity`/`character` para ator, `to`/`position` para destino, `amount`/`damage` para valor de dano. Posicoes como `[x, y]` ou `{ x, y }` (notes.md)
   - Iterar sobre array de eventos
   - Evento com `type: "move"`: atualizar posicao do personagem no grid (mover Container)
   - Evento com `type: "damage"` ou `type: "heal"`: atualizar HP no estado interno (visual de HP bars na feature 23)
   - Evento com `type: "death"` ou target HP < -10: marcar como dead, destruir sprite
   - Evento com `type: "knockout"` ou target HP entre -10 e 0: marcar como knocked_out, setAlpha(0.4)
   - Evento com `type: "object_destroyed"`: remover objeto do grid
   - Para eventos nao reconhecidos: ignorar silenciosamente (features futuras adicionam handlers)

8. Metodo `shutdown()` (cleanup do Phaser):
   - Chamar `wsClient.disconnect()`

9. Helper `gridToPixel(x, y)` → `{ px, py }`:
   - `px = GRID_OFFSET_X + x * TILE_SIZE + TILE_SIZE / 2`
   - `py = GRID_OFFSET_Y + y * TILE_SIZE + TILE_SIZE / 2`

10. Helper `pixelToGrid(px, py)` → `{ x, y } | null`:
    - Calcular x e y do grid a partir de pixel
    - Retornar null se fora dos limites do grid

---

### Grupo 4 — Wiring e Resultado Placeholder (um agente)

**Tarefa:** Atualizar main.ts, remover placeholder antigo, criar placeholder de resultado.

1. Modificar `frontend/src/main.ts`:
   - Remover import de `BattlePlaceholderScene`
   - Importar `BattleScene` de `./scenes/BattleScene`
   - Importar `ResultPlaceholderScene` de `./scenes/ResultPlaceholderScene`
   - Atualizar array de scenes: `[MenuScene, PreparationScene, BattleScene, ResultPlaceholderScene]`

2. Deletar `frontend/src/scenes/BattlePlaceholderScene.ts`

3. Criar `frontend/src/scenes/ResultPlaceholderScene.ts`:
   - Classe `ResultPlaceholderScene extends Phaser.Scene` com key `"ResultScene"` (notes.md: feature 24 deve manter esta key)
   - Recebe `{ result: "victory" | "defeat" }` via `init(data)`
   - Exibe "Vitoria!" (verde #44ff44) ou "Derrota!" (vermelho #ff4444) centralizado
   - Botao "Voltar ao Menu" → `this.scene.start("MenuScene")`
   - Este arquivo sera substituido pela feature 24

4. Verificar build: `npx tsc --noEmit` e `npx vite build` devem compilar sem erros.

---

## Condicao de Conclusao

- Todos os criterios de aceitacao em spec.md estao satisfeitos
- Testes do WS client passam com `npm run test` (vitest)
- Build compila sem erros: `npx tsc --noEmit`
- Fluxo completo funciona no browser (com backend rodando):
  - Menu → Preparacao → Batalha (grid visivel, personagens e objetos posicionados)
  - Turno do jogador: clicar tile para mover, clicar inimigo para atacar, encerrar turno
  - Turno da IA: acoes aparecem no grid, ready enviado automaticamente
  - Batalha encerra e transiciona para resultado
- Atualizar `.specs/state.md`: status da feature 21 para `concluida`
