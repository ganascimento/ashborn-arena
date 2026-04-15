# Tasks — Feature 22: Batalha — Acoes e Animacoes

## Antes de Comecar

Ler obrigatoriamente antes de escrever qualquer codigo:

- `CLAUDE.md` — stack, estrutura, convencoes (ingles, sem docstrings, models separadas)
- `.specs/features/22_batalha_acoes_animacoes/spec.md` — criterios de aceitacao desta feature
- `.specs/notes.md` — protocolo ready/next do WS, extensoes ao protocolo, processEvents defensivo, readyState check
- `.specs/prd.md` secoes 2.2 (PA, cooldowns), 3.2 (ataque basico), 3.3 (habilidades por classe)
- `.specs/design.md` secao 6.2 — protocolo WebSocket (mensagens client→server e server→client, fluxo ready/next)
- `frontend/src/scenes/BattleScene.ts` — cena atual a ser modificada
- `frontend/src/network/types.ts` — tipos TypeScript (AbilityOut, CharacterOut, WS messages)
- `frontend/src/network/ws-client.ts` — BattleWsClient (sendAbility ja existe)

---

## Plano de Execucao

```
Grupo 1 ─┐
          ├─ paralelo ─► Grupo 3 (integracao, sequencial)
Grupo 2 ─┘
```

Grupos 1 e 2 sao independentes (arquivos diferentes). Grupo 3 depende de ambos (modifica BattleScene.ts para integrar os dois modulos).

---

### Grupo 1 — Sistema de Animacoes (um agente)

**Tarefa:** Criar modulo de animacoes com tweens Phaser e processamento sequencial de eventos.

1. Criar `frontend/src/scenes/battle-animations.ts`:

2. Classe `BattleAnimations`:
   - Constructor: `(scene: Phaser.Scene)`
   - Armazena referencia a `scene` para criar tweens

3. Helper privado para converter tween em Promise:
   ```typescript
   private tweenPromise(config: Phaser.Types.Tweens.TweenBuilderConfig): Promise<void> {
     return new Promise(resolve => {
       this.scene.tweens.add({ ...config, onComplete: () => resolve() });
     });
   }
   ```

4. Helper privado para delay:
   ```typescript
   private delay(ms: number): Promise<void> {
     return new Promise(resolve => this.scene.time.delayedCall(ms, resolve));
   }
   ```

5. Metodos de animacao (cada um retorna `Promise<void>`):

   - `animateMove(container: Phaser.GameObjects.Container, toPx: number, toPy: number): Promise<void>`
     - Tween: `{ targets: container, x: toPx, y: toPy, duration: 300, ease: 'Quad.InOut' }`

   - `animateDamage(container: Phaser.GameObjects.Container, originalColor: number): Promise<void>`
     - Obter primeiro filho do container (circulo): `container.getAt(0) as Phaser.GameObjects.Arc`
     - Mudar fillColor para `0xff4444` (vermelho)
     - Delay 200ms
     - Restaurar fillColor para `originalColor`

   - `animateHeal(container: Phaser.GameObjects.Container, originalColor: number): Promise<void>`
     - Mesmo padrao: mudar fillColor para `0x44ff44` (verde), delay 200ms, restaurar

   - `animateDot(container: Phaser.GameObjects.Container, originalColor: number): Promise<void>`
     - Mudar fillColor para `0xcc4444`, delay 150ms, restaurar

   - `animateKnockout(container: Phaser.GameObjects.Container): Promise<void>`
     - Tween: `{ targets: container, alpha: 0.4, duration: 200 }`

   - `animateRevive(container: Phaser.GameObjects.Container): Promise<void>`
     - Tween: `{ targets: container, alpha: 1.0, duration: 200 }`

   - `animateDeath(container: Phaser.GameObjects.Container): Promise<void>`
     - Tween: `{ targets: container, alpha: 0, duration: 300 }`
     - No onComplete do tween: `container.destroy()`

   - `animateObjectDestroy(rect: Phaser.GameObjects.Rectangle): Promise<void>`
     - Tween: `{ targets: rect, alpha: 0, duration: 200 }`
     - No onComplete: `rect.destroy()`

6. Tipos de evento para o processador (nao exportar, uso interno):
   - Mapear event.type a uma categoria de animacao:
     - MOVE: `move`, `ability_movement`
     - DAMAGE: `basic_attack`, `ability`, `aoe_hit`, `opportunity_attack`, `chain_primary`, `chain_secondary`
     - HEAL: `heal`, `self_heal`, `lifesteal`
     - DOT: `bleed`, `dot_tick`
     - HOT: `hot_tick`
     - KNOCKOUT: `knocked_out`
     - DEATH: `death`
     - OBJECT_DESTROYED: `object_destroyed`
     - NONE: todos os demais (processamento instantaneo)

7. Metodo principal `processEventsAnimated(events, getCharacter, getMapObject, gridToPixel, updateState)`:
   ```typescript
   async processEventsAnimated(
     events: unknown[],
     getCharacter: (id: string) => CharacterEntry | undefined,
     getMapObject: (id: string) => MapObjectEntry | undefined,
     gridToPixel: (x: number, y: number) => { px: number; py: number },
     updateState: (event: Record<string, unknown>) => void,
   ): Promise<void>
   ```
   - Se events e undefined ou vazio, retornar imediatamente
   - Iterar sequencialmente sobre cada evento (usar `for...of` com `await`)
   - Para cada evento:
     a. Chamar `updateState(event)` primeiro (atualiza estado interno: posicao, HP, status)
     b. Determinar categoria de animacao pelo `event.type`
     c. Se categoria tem animacao: executar animacao correspondente e `await`
     d. Se categoria NONE: continuar sem delay
   - Campo defensivo: entity pode ser `event.entity` ou `event.character`; target pode ser `event.target`; position pode ser `event.to` ou `event.position`, formato `[x,y]` ou `{x,y}` (notes.md)

---

### Grupo 2 — Barra de Habilidades (um agente)

**Tarefa:** Criar modulo da barra de habilidades com botoes, PA counter, cooldown tracking e estado de targeting.

1. Criar `frontend/src/scenes/battle-ability-bar.ts`:

2. Interface de callback:
   ```typescript
   interface AbilityBarCallbacks {
     onAbilitySelected: (ability: AbilityOut) => void;
     onAbilityDeselected: () => void;
     onEndTurn: () => void;
   }
   ```

3. Classe `BattleAbilityBar`:
   - Constructor: `(scene: Phaser.Scene, x: number, y: number, callbacks: AbilityBarCallbacks)`
   - Armazena referencia a scene, posicao base, callbacks

4. Estado interno:
   ```typescript
   private abilities: AbilityOut[] = []
   private currentPA: number = 4
   private maxPA: number = 4
   private cooldowns: Map<string, number> = new Map()  // abilityId → turns remaining
   private selectedAbilityId: string | null = null
   private visible: boolean = false
   private objects: Phaser.GameObjects.GameObject[] = []
   private paText: Phaser.GameObjects.Text | null = null
   ```

5. Metodo `show(abilities: AbilityOut[], pa: number, cooldowns: Map<string, number>)`:
   - Limpar objetos anteriores (`destroy()` cada um)
   - Armazenar abilities, PA, cooldowns
   - Renderizar PA counter: texto "PA: X / 4" na posicao (x, y)
   - Renderizar botoes de habilidade (y += 35 para cada):
     - Para cada habilidade (basic attack primeiro, depois as 5 equipadas):
       - Retangulo de fundo: 280x38px, cor #2a2a4c
       - Texto: "{nome}  PA:{custo}" + (se em cooldown: "  CD:{turns}")
       - Cor do texto: habilitado #cccccc, desabilitado #555555, selecionado #ffd700
       - Habilitado se: PA >= custo E cooldown == 0
       - `setInteractive({ useHandCursor: habilitado })`
       - On pointerdown: se habilitado, chamar `selectAbility(ability)`
       - On pointerover: se habilitado e nao selecionado, cor #ffffff
       - On pointerout: restaurar cor baseada no estado
   - Renderizar botao "Encerrar Turno" abaixo:
     - Retangulo + texto, cor #ffd700
     - On pointerdown: `callbacks.onEndTurn()`
   - Setar `visible = true`

6. Metodo `hide()`:
   - Destruir todos os objetos
   - `visible = false`, `selectedAbilityId = null`

7. Metodo `selectAbility(ability: AbilityOut)`:
   - Se `selectedAbilityId === ability.id`: deselecionar (chamar `clearSelection()`)
   - Senao: `selectedAbilityId = ability.id`, chamar `callbacks.onAbilitySelected(ability)`, re-renderizar botoes para atualizar cores
   - Para habilidades com `target === "self"`: nao entrar em targeting, chamar `onAbilitySelected` imediatamente (BattleScene envia a acao com posicao do proprio personagem)

8. Metodo `clearSelection()`:
   - `selectedAbilityId = null`
   - Chamar `callbacks.onAbilityDeselected()`
   - Atualizar cores dos botoes

9. Metodo `getSelectedAbility(): AbilityOut | null`:
   - Retornar habilidade selecionada ou null

10. Metodo `deductPA(cost: number)`:
    - `currentPA = Math.max(0, currentPA - cost)`
    - Atualizar texto do PA counter
    - Re-avaliar botoes habilitados/desabilitados (re-renderizar ou atualizar cores)

11. Metodo `startCooldown(abilityId: string, turns: number)`:
    - `cooldowns.set(abilityId, turns)`
    - Atualizar visual do botao correspondente

12. Metodo `tickCooldowns()`:
    - Para cada entry em cooldowns: decrementar por 1, remover se <= 0
    - Atualizar visual

13. Metodo `destroy()`:
    - Destruir todos os objetos Phaser

---

### Grupo 3 — Integracao na BattleScene (um agente, apos Grupos 1 e 2)

**Tarefa:** Integrar BattleAnimations e BattleAbilityBar na BattleScene, tornar event processing async, adicionar targeting e rastreamento de estado.

1. Ler o codigo atual de `frontend/src/scenes/BattleScene.ts` (feature 21).
   Ler os modulos criados: `battle-animations.ts` e `battle-ability-bar.ts`.

2. Adicionar imports em BattleScene.ts:
   ```typescript
   import { BattleAnimations } from "./battle-animations";
   import { BattleAbilityBar } from "./battle-ability-bar";
   ```

3. Adicionar novos campos privados:
   ```typescript
   private animations!: BattleAnimations
   private abilityBar!: BattleAbilityBar
   private isAnimating = false
   private cooldowns: Map<string, Map<string, number>> = new Map()  // charId → (abilityId → turns)
   private currentPA = 4
   private selectedAbility: AbilityOut | null = null
   ```

4. No metodo `create()`, apos renderizar grid/objetos/personagens:
   - Instanciar `BattleAnimations(this)`
   - Instanciar `BattleAbilityBar(this, 700, 104, callbacks)` com callbacks:
     - `onAbilitySelected`: setar `selectedAbility`
     - `onAbilityDeselected`: setar `selectedAbility = null`
     - `onEndTurn`: `wsClient.sendEndTurn(currentCharacter)`
   - Remover o botao "Encerrar Turno" standalone (`endTurnBtn`) — substituido pela barra
   - Inicializar `cooldowns` vazio para cada personagem do jogador
   - Adicionar listener de teclado: `this.input.keyboard.on('keydown-ESC', () => abilityBar.clearSelection())`

5. Refatorar `processEvents()` para ser metodo de atualizacao de estado puro (sem animacao):
   - Renomear para `updateStateFromEvent(event: Record<string, unknown>)`:
     - Processar move: atualizar posicao no data (sem mover sprite — animacao faz isso)
     - Processar damage/heal: atualizar HP
     - Processar death/knockout: atualizar status
     - Processar object_destroyed: remover do mapa
     - Processar heal que revive (HP volta de negativo para positivo): status = "active"
   - Este metodo e passado como callback `updateState` para `BattleAnimations.processEventsAnimated()`

6. Refatorar `handleAiAction` para ser async:
   ```typescript
   private async handleAiAction(msg: WsAiAction) {
     this.isAnimating = true;
     await this.animations.processEventsAnimated(
       msg.events,
       (id) => this.characters.get(id),
       (id) => this.mapObjects.get(id),
       (x, y) => this.gridToPixel(x, y),
       (event) => this.updateStateFromEvent(event),
     );
     this.isAnimating = false;
     this.wsClient.sendReady();
   }
   ```

7. Refatorar `handleActionResult` para ser async:
   ```typescript
   private async handleActionResult(msg: WsActionResult) {
     this.isAnimating = true;
     await this.animations.processEventsAnimated(
       msg.events,
       (id) => this.characters.get(id),
       (id) => this.mapObjects.get(id),
       (x, y) => this.gridToPixel(x, y),
       (event) => this.updateStateFromEvent(event),
     );
     this.isAnimating = false;
     // PA e cooldown atualizados apos animacao
     this.updatePAFromAction(msg);
     this.abilityBar.clearSelection();
   }
   ```

8. Refatorar `handleTurnStart` para ser async:
   ```typescript
   private async handleTurnStart(msg: WsTurnStart) {
     this.updateTurnState(msg.character);
     // Tick cooldowns do personagem do jogador
     if (this.isPlayerCharacter(msg.character)) {
       this.tickCooldownsForCharacter(msg.character);
       this.currentPA = msg.pa;
       const charEntry = this.characters.get(msg.character);
       if (charEntry) {
         this.abilityBar.show(
           charEntry.data.abilities,
           msg.pa,
           this.cooldowns.get(msg.character) ?? new Map(),
         );
       }
     } else {
       this.abilityBar.hide();
     }
     if (msg.events && msg.events.length > 0) {
       this.isAnimating = true;
       await this.animations.processEventsAnimated(
         msg.events,
         (id) => this.characters.get(id),
         (id) => this.mapObjects.get(id),
         (x, y) => this.gridToPixel(x, y),
         (event) => this.updateStateFromEvent(event),
       );
       this.isAnimating = false;
     }
   }
   ```

9. Refatorar `onTileClick(x, y)`:
   ```
   Se isAnimating ou nao isPlayerTurn → ignorar
   Se selectedAbility != null:
     → wsClient.sendAbility(currentCharacter, selectedAbility.id, [x, y])
     → return
   (comportamento original da feature 21 para modo sem habilidade selecionada)
   ```

10. Metodo `updatePAFromAction(msg: WsActionResult)`:
    - Identificar custo da acao:
      - `msg.action === "move"`: calcular PA pelo evento move (ceil(dist/2))
      - `msg.action === "basic_attack"`: 2 PA
      - `msg.action === "ability"`: encontrar habilidade nos dados do personagem, usar `pa_cost`
      - `msg.action === "end_turn"`: 0 PA
    - `currentPA -= cost`
    - Se ability com cooldown > 0: `startCooldownForCharacter(currentCharacter, abilityId, cd)`
    - `abilityBar.deductPA(cost)`

11. Metodos de cooldown:
    - `tickCooldownsForCharacter(charId)`: pegar map do charId, decrementar cada valor por 1, remover zerados
    - `startCooldownForCharacter(charId, abilityId, turns)`: setar no map

12. Tratar habilidades com target "self" na callback `onAbilitySelected`:
    - Se `ability.target === "self"`: enviar imediatamente `wsClient.sendAbility(currentCharacter, ability.id, [charPos.x, charPos.y])` sem esperar clique

13. Verificar que `handleTurnEnd` chama `abilityBar.hide()` ao transicionar para personagem da IA.

14. Executar testes existentes: `npm run test` — testes do WS client devem continuar passando.
    Verificar build: `npx tsc --noEmit` e `npx vite build` sem erros.
    Testar no browser (com backend rodando):
    - Turno do jogador: barra de habilidades visivel, PA counter correto
    - Clicar habilidade → targeting mode → clicar tile → acao enviada
    - Animacao de movimento suave (tween)
    - Animacao de dano (flash vermelho no alvo)
    - Turno da IA: acoes animadas uma a uma, ready automatico
    - Cooldowns atualizados corretamente entre turnos

---

## Condicao de Conclusao

- Todos os criterios de aceitacao em spec.md estao satisfeitos
- Testes existentes do WS client passam com `npm run test` (vitest)
- Build compila sem erros: `npx tsc --noEmit`
- Fluxo completo funciona no browser (com backend rodando):
  - Barra de habilidades aparece no turno do jogador, some no turno da IA
  - Jogador seleciona habilidade, clica alvo, acao enviada e animada
  - Movimento com tween suave, dano com flash vermelho, cura com flash verde
  - Turno da IA animado sequencialmente com ready apos cada acao
  - PA e cooldowns rastreados corretamente
- Atualizar `.specs/state.md`: status da feature 22 para `concluida`
