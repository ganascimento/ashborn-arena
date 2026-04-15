# Tasks — Feature 23: Batalha — HUD e Feedback

## Antes de Comecar

Ler obrigatoriamente antes de escrever qualquer codigo:

- `CLAUDE.md` — stack, estrutura, convencoes (ingles, sem docstrings, models separadas)
- `.specs/features/23_batalha_hud_feedback/spec.md` — criterios de aceitacao desta feature
- `.specs/notes.md` — "dead characters permanecem no Map", "arquitetura de animacoes e ability bar", "processEvents defensivo"
- `.specs/prd.md` secao 7.5 — feedback visual na batalha
- `.specs/design.md` secao 2.6 — efeitos de status (tags e tipos)
- `.specs/design.md` secao 2.7 — alcance e tipo de alvo de cada habilidade
- `frontend/src/scenes/BattleScene.ts` — cena atual, estado dos personagens, updateStateFromEvent
- `frontend/src/scenes/battle-animations.ts` — BattleAnimations, processEventsAnimated
- `frontend/src/scenes/battle-ability-bar.ts` — BattleAbilityBar, callbacks onAbilitySelected/Deselected
- `frontend/src/network/types.ts` — AbilityOut (target field: "single_enemy", "single_ally", "self", "aoe", "adjacent", "chain"), CharacterOut

---

## Plano de Execucao

```
Grupo 1 ─┐
          ├─ paralelo ─► Grupo 3 (integracao, sequencial)
Grupo 2 ─┘
```

Grupos 1 e 2 criam arquivos novos independentes. Grupo 3 modifica BattleScene.ts e battle-animations.ts para integrar os modulos.

---

### Grupo 1 — BattleHud: HP bars, status icons, floating text (um agente)

**Tarefa:** Criar modulo de HUD com barras de HP, indicadores de status e numeros flutuantes.

1. Criar `frontend/src/scenes/battle-hud.ts`:

2. Constantes:
   ```typescript
   const HP_BAR_WIDTH = 48;
   const HP_BAR_HEIGHT = 6;
   const HP_BAR_OFFSET_Y = 30; // abaixo do centro do personagem
   ```

3. Mapeamento de tags de status para abreviacoes e cores:
   ```typescript
   const STATUS_ABBR: Record<string, string> = {
     bleed: "BLD", poison: "PSN", slow: "SLW", immobilize: "IMB",
     silence: "SIL", taunt: "TNT", wet: "WET", frozen: "FRZ", burn: "BRN",
   };
   const STATUS_COLORS: Record<string, string> = {
     bleed: "#ff4444", poison: "#ff4444",       // DOT = vermelho
     slow: "#ff8800", silence: "#ff8800",        // debuff = laranja
     immobilize: "#aa44ff", taunt: "#aa44ff", frozen: "#aa44ff", // controle = roxo
     wet: "#88ccff", burn: "#ff8800",            // elemental = azul claro / laranja
   };
   ```

4. Classe `BattleHud`:
   - Constructor: `(scene: Phaser.Scene)`
   - Estado interno:
     ```typescript
     private hpBars: Map<string, { bg: Phaser.GameObjects.Rectangle; fill: Phaser.GameObjects.Rectangle }>
     private statusLabels: Map<string, Phaser.GameObjects.Text>
     ```

5. Metodo `createHpBar(entityId: string, worldX: number, worldY: number, currentHp: number, maxHp: number)`:
   - Criar retangulo de fundo: largura HP_BAR_WIDTH, altura HP_BAR_HEIGHT, cor 0x333333
   - Posicao: (worldX, worldY + HP_BAR_OFFSET_Y)
   - Criar retangulo de preenchimento: largura proporcional a currentHp/maxHp, mesma posicao
   - Cor do preenchimento baseada na porcentagem:
     - HP > 50%: 0x44ff44 (verde)
     - HP 25-50%: 0xffaa00 (amarelo)
     - HP < 25%: 0xff4444 (vermelho)
   - Ambos com depth alto (ex: 100) para ficar acima de tiles/objetos
   - Armazenar em hpBars Map pelo entityId

6. Metodo `updateHpBar(entityId: string, worldX: number, worldY: number, currentHp: number, maxHp: number)`:
   - Se nao existe, chamar createHpBar
   - Atualizar posicao dos retangulos (personagem pode ter se movido)
   - Recalcular largura do preenchimento: `Math.max(0, (currentHp / maxHp)) * HP_BAR_WIDTH`
   - Atualizar cor baseada na porcentagem
   - Se currentHp <= 0 (knocked_out): largura 0, borda vermelha no fundo

7. Metodo `removeHpBar(entityId: string)`:
   - Destruir retangulos bg e fill
   - Remover do Map

8. Metodo `updateStatusIcons(entityId: string, worldX: number, worldY: number, effects: Set<string>)`:
   - Destruir label anterior do entityId se existir
   - Se effects vazio, remover e retornar
   - Construir texto concatenado: ex "BLD PSN SLW"
   - Construir cor — usar a cor do primeiro efeito (simplificado) ou criar texto multi-cor
   - Para simplificar: usar texto unico com cor do tipo mais grave (controle > debuff > DOT > elemental)
   - Posicionar acima da barra de HP: (worldX, worldY + HP_BAR_OFFSET_Y - 14)
   - fontSize 10px, fontFamily monospace, centered (setOrigin 0.5)
   - Depth alto (101, acima das barras)
   - Armazenar no statusLabels Map

9. Metodo `spawnFloatingText(worldX: number, worldY: number, text: string, color: string, fontSize: string)`:
   - Criar texto na posicao (worldX, worldY - 20)
   - Cor e fontSize passados como parametro
   - setOrigin(0.5), depth alto (200)
   - Tween: mover y -30px e alpha 0 em 800ms
   - No onComplete do tween: destruir o texto
   - Para empilhar multiplos: adicionar offset baseado em contador temporal (incrementar um yOffset que reseta apos 800ms, ou usar random offset -5 a +5 no X)

10. Metodo `updateAllBars(characters: Map, gridToPixel)`:
    - Para cada entry em characters (iterar entries):
      - Se status === "dead": chamar removeHpBar, continuar
      - Calcular worldX, worldY com gridToPixel(entry.data.position.x, y)
      - Chamar updateHpBar(entityId, worldX, worldY, current_hp, max_hp)

11. Metodo `destroy()`:
    - Destruir todas as barras e labels

12. Export: `export class BattleHud`

---

### Grupo 2 — BattleRangeOverlay: alcance e AoE (um agente)

**Tarefa:** Criar modulo de overlay para highlight de alcance e preview de area de efeito.

1. Criar `frontend/src/scenes/battle-range-overlay.ts`:

2. Classe `BattleRangeOverlay`:
   - Constructor: `(scene: Phaser.Scene, tileSize: number, gridOffsetX: number, gridOffsetY: number, gridCols: number, gridRows: number)`
   - Estado interno:
     ```typescript
     private rangeOverlays: Phaser.GameObjects.Rectangle[] = []
     private aoeOverlays: Phaser.GameObjects.Rectangle[] = []
     ```

3. Metodo `showRange(centerX: number, centerY: number, maxRange: number)`:
   - Limpar overlays anteriores chamando `clearRange()`
   - Para cada tile (tx, ty) no grid (0..cols-1, 0..rows-1):
     - Calcular distancia de Chebyshev: `Math.max(Math.abs(tx - centerX), Math.abs(ty - centerY))`
     - Se distancia <= maxRange E distancia > 0 (nao incluir tile do proprio personagem):
       - Criar retangulo semi-transparente: posicao no centro do tile, tamanho tileSize x tileSize
       - Cor: 0x4488ff, alpha 0.25
       - Depth baixo (ex: 50, acima dos tiles mas abaixo dos personagens)
       - NAO setInteractive — overlay nao bloqueia input
       - Adicionar ao array rangeOverlays

4. Metodo `showAdjacentRange(centerX: number, centerY: number)`:
   - Chamar `showRange(centerX, centerY, 1)` — alcance 1 = tiles adjacentes

5. Metodo `clearRange()`:
   - Destruir todos os retangulos em rangeOverlays
   - Limpar array

6. Metodo `showAoePreview(centerX: number, centerY: number)`:
   - Limpar preview anterior chamando `clearAoePreview()`
   - Para cada tile (tx, ty) dentro de raio 1 do centro (incluindo diagonais, max 9 tiles):
     - Se dentro dos limites do grid:
       - Criar retangulo: posicao no centro do tile, tileSize x tileSize
       - Cor: 0xff8800, alpha 0.3
       - Depth 51 (acima do range overlay)
       - Adicionar ao array aoeOverlays

7. Metodo `clearAoePreview()`:
   - Destruir todos os retangulos em aoeOverlays
   - Limpar array

8. Metodo `clear()`:
   - Chamar clearRange() + clearAoePreview()

9. Metodo `destroy()`:
   - Chamar clear()

10. Helper privado `gridToPixel(gx, gy)` → `{ x, y }`:
    - `x = gridOffsetX + gx * tileSize + tileSize / 2`
    - `y = gridOffsetY + gy * tileSize + tileSize / 2`
    - (duplica logica do BattleScene, mas mantido local para evitar dependencia circular)

11. Export: `export class BattleRangeOverlay`

---

### Grupo 3 — Integracao na BattleScene e BattleAnimations (um agente, apos Grupos 1 e 2)

**Tarefa:** Integrar BattleHud e BattleRangeOverlay na BattleScene. Modificar BattleAnimations para disparar floating text. Adicionar rastreamento de efeitos ativos.

#### Parte A — Modificar battle-animations.ts

1. Alterar assinatura de `processEventsAnimated` para aceitar callback opcional:
   ```typescript
   async processEventsAnimated(
     events: unknown[],
     getCharacter: ...,
     getMapObject: ...,
     gridToPixel: ...,
     updateState: ...,
     onFloatingText?: (worldX: number, worldY: number, text: string, color: string, fontSize: string) => void,
   ): Promise<void>
   ```

2. Nos blocos de processamento de eventos de DAMAGE (dentro de `DAMAGE_TYPES.has(type)`):
   - Apos a animacao de dano, chamar `onFloatingText` se definido:
     - `amount` = `event.damage ?? event.amount` (ja extraido para state update)
     - `crit` = `event.crit` como boolean
     - Se crit: `onFloatingText(px, py, `-${amount}!`, "#ffd700", "20px")`
     - Senao: `onFloatingText(px, py, `-${amount}`, "#ff4444", "16px")`
   - Obter px/py do container do alvo: `entry.sprite.x, entry.sprite.y`

3. Nos blocos de HEAL:
   - `amount` = `event.amount ?? event.heal`
   - `onFloatingText(px, py, `+${amount}`, "#44ff44", "16px")`

4. Nos blocos de DOT:
   - `amount` = `event.damage ?? event.amount`
   - `onFloatingText(px, py, `-${amount}`, "#ff4444", "14px")`

5. Nos blocos de HOT:
   - `amount` = `event.heal ?? event.amount`
   - `onFloatingText(px, py, `+${amount}`, "#44ff44", "14px")`

#### Parte B — Modificar BattleScene.ts

6. Adicionar imports:
   ```typescript
   import { BattleHud } from "./battle-hud";
   import { BattleRangeOverlay } from "./battle-range-overlay";
   ```

7. Adicionar campos privados:
   ```typescript
   private hud!: BattleHud;
   private rangeOverlay!: BattleRangeOverlay;
   private activeEffects: Map<string, Set<string>> = new Map();
   ```

8. No `create()`:
   - Instanciar `this.hud = new BattleHud(this)`
   - Instanciar `this.rangeOverlay = new BattleRangeOverlay(this, TILE_SIZE, GRID_OFFSET_X, GRID_OFFSET_Y, GRID_COLS, GRID_ROWS)`
   - Criar HP bars iniciais para todos os personagens:
     ```typescript
     for (const [id, entry] of this.characters) {
       const { px, py } = this.gridToPixel(entry.data.position.x, entry.data.position.y);
       this.hud.createHpBar(id, px, py, entry.data.current_hp, entry.data.max_hp);
     }
     ```
   - Inicializar activeEffects vazio para cada personagem

9. Modificar callback `onAbilitySelected` no BattleAbilityBar constructor:
   - Apos setar `this.selectedAbility = ability`:
     - Se ability.target !== "self":
       - Obter posicao do personagem ativo
       - Se ability.target === "adjacent": `this.rangeOverlay.showAdjacentRange(pos.x, pos.y)`
       - Senao: `this.rangeOverlay.showRange(pos.x, pos.y, ability.max_range)`

10. Modificar callback `onAbilityDeselected`:
    - Apos setar `this.selectedAbility = null`:
      - `this.rangeOverlay.clear()`

11. No ESC handler, apos clearSelection:
    - `this.rangeOverlay.clear()`

12. Adicionar evento `pointermove` nos tiles do grid (em renderGrid):
    - `tile.on("pointermove", () => this.onTileHover(x, y))`

13. Metodo `onTileHover(x: number, y: number)`:
    - Se `selectedAbility` e null ou isAnimating: `this.rangeOverlay.clearAoePreview(); return`
    - Se `selectedAbility.target === "aoe"`:
      - Verificar se tile esta no alcance (Chebyshev distance <= max_range)
      - Se sim: `this.rangeOverlay.showAoePreview(x, y)`
      - Se nao: `this.rangeOverlay.clearAoePreview()`
    - Se `selectedAbility.target === "adjacent"`:
      - Sempre mostrar preview ao redor do personagem ativo (nao do cursor)
      - (ja mostrado pelo showAdjacentRange, nao precisa de hover adicional)

14. Estender `updateStateFromEvent` para rastrear efeitos:
    - Caso `effect_applied`:
      ```typescript
      const targetId = event.target as string | undefined;
      const tag = event.tag as string | undefined;
      if (targetId && tag) {
        if (!this.activeEffects.has(targetId)) this.activeEffects.set(targetId, new Set());
        this.activeEffects.get(targetId)!.add(tag);
      }
      ```
    - Caso `effect_expired`:
      ```typescript
      const entityId = event.entity as string | undefined;
      const tag = event.tag as string | undefined;
      if (entityId && tag) {
        this.activeEffects.get(entityId)?.delete(tag);
      }
      ```

15. Atualizar chamadas a `processEventsAnimated` nos 3 handlers async (handleAiAction, handleActionResult, handleTurnStart):
    - Passar `onFloatingText` callback:
      ```typescript
      (worldX, worldY, text, color, fontSize) => this.hud.spawnFloatingText(worldX, worldY, text, color, fontSize)
      ```
    - Apos o await, chamar refresh de barras e icons:
      ```typescript
      this.refreshHud();
      ```

16. Metodo `refreshHud()`:
    - Chamar `this.hud.updateAllBars(this.characters, (x, y) => this.gridToPixel(x, y))`
    - Para cada personagem ativo, atualizar status icons:
      ```typescript
      for (const [id, entry] of this.characters) {
        if (entry.status === "dead") continue;
        const { px, py } = this.gridToPixel(entry.data.position.x, entry.data.position.y);
        const effects = this.activeEffects.get(id) ?? new Set();
        this.hud.updateStatusIcons(id, px, py, effects);
      }
      ```

17. Nos handlers que limpam targeting (handleActionResult, ESC, clearSelection):
    - `this.rangeOverlay.clear()`

18. Atualizar `shutdown()`:
    - Adicionar `this.hud?.destroy()` e `this.rangeOverlay?.destroy()`

19. Verificar build: `npx tsc --noEmit` e `npm run test -- --run` devem passar.
    Testar no browser:
    - HP bars visiveis sobre todos os personagens
    - Dano reduz barra, cura aumenta
    - Numeros flutuantes aparecem em dano/cura
    - Crits exibem numero amarelo maior
    - Status icons aparecem com effect_applied e somem com effect_expired
    - Selecionar habilidade destaca tiles no alcance
    - Mover mouse sobre tile com AoE selecionado mostra preview laranja

---

## Condicao de Conclusao

- Todos os criterios de aceitacao em spec.md estao satisfeitos
- Testes existentes do WS client passam com `npm run test` (vitest)
- Build compila sem erros: `npx tsc --noEmit`
- Fluxo completo funciona no browser (com backend rodando):
  - HP bars visiveis e atualizando em tempo real
  - Numeros flutuantes de dano (vermelho), cura (verde), critico (amarelo)
  - Status icons aparecem e desaparecem corretamente
  - Range highlight ao selecionar habilidade
  - AoE preview ao hover durante targeting
- Atualizar `.specs/state.md`: status da feature 23 para `concluida`
