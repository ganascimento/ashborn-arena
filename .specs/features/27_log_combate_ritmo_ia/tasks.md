# Tasks — Feature 27: Log de Combate e Ritmo da IA

## Antes de Comecar

Leitura obrigatoria antes de implementar:

- `CLAUDE.md` — convencoes, stack
- `.specs/features/27_log_combate_ritmo_ia/spec.md` — criterios de aceitacao
- `.specs/design.md` secao 7.3 — spec tecnica do log (layout, mapeamento de eventos, delay)
- `.specs/prd.md` secao 7.7 — requisito de UX
- `.specs/notes.md` — "processEvents defensivo para field names", "arquitetura de animacoes"
- `frontend/src/scenes/BattleScene.ts` — handlers `handleAiAction`, `handleActionResult`, `handleTurnStart`, callback `floatingTextCallback`
- `frontend/src/scenes/battle-animations.ts` — `processEventsAnimated` (onde os eventos sao iterados)
- `frontend/src/scenes/battle-hud.ts` — referencia de padrao para componente HUD

---

## Plano de Execucao

2 grupos paralelos: Grupo 1 cria o componente de log (independente), Grupo 2 integra no BattleScene e adiciona delay da IA. Grupo 2 depende do Grupo 1 estar pronto — executar sequencialmente.

Sem TDD formal — o log e primariamente visual. A funcao de formatacao de eventos pode ser testada unitariamente, mas o componente Phaser nao.

---

### Grupo 1 — Componente BattleCombatLog

**Tarefa:** Criar componente standalone que gerencia o painel de log de combate.

1. Criar `frontend/src/scenes/battle-combat-log.ts`:
   - Classe `BattleCombatLog` com constructor recebendo `Phaser.Scene`, `x: number`, `y: number`, `width: number`, `height: number`
   - Propriedades internas:
     - `entries: string[]` — array de strings (max 50)
     - `bg: Phaser.GameObjects.Rectangle` — background semi-transparente
     - `textObj: Phaser.GameObjects.Text` — texto renderizado
   - No constructor:
     - Criar `bg` como retangulo em (x, y) com dimensoes (width, height), cor `0x1a1a2e`, alpha 0.85, depth 250
     - Criar `textObj` com fontSize 12px, fontFamily monospace, cor `#cccccc`, wordWrap width-10, depth 251
   - Metodo `addEntry(text: string)`:
     - Push no `entries`, se length > 50 fazer shift()
     - Recalcular texto visivel: calcular quantas linhas cabem na altura (~height / 16), pegar as ultimas N entries, juntar com `\n`, setar no textObj
   - Metodo `destroy()`: destroi bg e textObj

2. Criar funcao exportada `formatEventForLog(event: Record<string, unknown>, resolveClass: (entityId: string) => string): string | null`:
   - Pode ficar no mesmo arquivo ou em `frontend/src/scenes/combat-log-formatter.ts`
   - Implementar mapeamento conforme design.md 7.3:
     - `move` / `ability_movement` → `"{classe} moveu para ({x},{y})"`
     - `basic_attack` → `"{classe} atacou {alvo} — {dano} dano"`
     - `ability` → `"{classe} usou {habilidade} em {alvo} — {dano} dano"` ou `"— +{cura} cura"` se heal_base > 0
     - `aoe_hit` → `"{alvo} recebeu {dano} dano [AoE]"`
     - `bleed` / `dot_tick` → `"{classe} sofreu {dano} dano ({tipo})"`
     - `heal` / `hot_tick` → `"{classe} recuperou {cura} HP"`
     - `knocked_out` → `"{classe} foi nocauteado!"`
     - `death` → `"{classe} morreu!"`
     - `effect_applied` → `"{classe} recebeu efeito: {tag}"`
     - `effect_expired` → `"Efeito {tag} expirou em {classe}"`
   - Retornar `null` para tipos nao mapeados (evento ignorado)
   - `resolveClass(entityId)` recebe entity_id e retorna nome da classe em portugues (lookup via characters map → class_id → CLASS_DISPLAY)

---

### Grupo 2 — Integrar log no BattleScene + delay da IA

**Tarefa:** Instanciar o log no BattleScene, alimenta-lo a cada evento, e adicionar delay de 800ms apos animacoes da IA.

1. Modificar `BattleScene.ts`:
   - Importar `BattleCombatLog` e `formatEventForLog`
   - Adicionar campo `private combatLog!: BattleCombatLog`
   - No `create()`: instanciar `this.combatLog = new BattleCombatLog(this, 700, 450, 300, 200)` (ajustar Y conforme espaco disponivel abaixo da ability bar)
   - Adicionar `CLASS_DISPLAY` lookup se nao existir (ja deve existir da feature 25)
   - Criar helper `private resolveClassName(entityId: string): string` que busca no `this.characters` map e retorna `CLASS_DISPLAY[entry.data.class_id] ?? entityId`

2. Alimentar o log — modificar o callback `updateStateFromEvent` ou criar novo callback para o log:
   - Opcao recomendada: no `processEventsAnimated`, apos o `updateState(event)` callback, chamar tambem um callback de log
   - Alternativa mais simples: nos 3 handlers async (`handleTurnStart`, `handleActionResult`, `handleAiAction`), apos `processEventsAnimated`, iterar `msg.events` e chamar `formatEventForLog` + `combatLog.addEntry` para cada evento
   - A alternativa mais simples evita mudar a assinatura de `processEventsAnimated`

3. Adicionar delay apos acoes da IA — modificar `handleAiAction`:
   ```typescript
   private async handleAiAction(msg: WsAiAction) {
     this.isAnimating = true;
     try {
       await this.animations.processEventsAnimated(...);
     } finally {
       this.isAnimating = false;
     }
     this.logEvents(msg.events);  // alimentar log
     this.refreshHud();
     await this.delay(800);       // delay adicional para o jogador acompanhar
     this.wsClient.sendReady();
     this.drainQueue();
   }
   ```
   - Criar helper `private delay(ms: number): Promise<void>` usando `this.time.delayedCall` (mesmo padrao do BattleAnimations)
   - **Nao** adicionar delay em `handleActionResult` (acoes do jogador) nem em `handleTurnStart`

4. Cleanup:
   - Em `shutdown()`: adicionar `this.combatLog?.destroy()`
   - Em `handleBattleEnd()`: adicionar `this.combatLog?.destroy()` antes de transicionar para ResultScene

5. Verificar manualmente que:
   - O log exibe entradas para acoes do jogador e da IA
   - Ha uma pausa perceptivel entre cada acao da IA
   - O log faz scroll automatico para a entrada mais recente
   - Apos 50+ entradas, as mais antigas sao descartadas

---

## Condicao de Conclusao

Todos os criterios de aceitacao em spec.md satisfeitos.
TypeScript compila sem erros (`npx tsc --noEmit`).
Testes existentes continuam passando (`npx vitest run`).
Atualizar `.specs/state.md`: setar feature 27 para `concluida`.
