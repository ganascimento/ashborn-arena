# Tasks — Feature 25: Marcador do Personagem Ativo

## Antes de Comecar

Leitura obrigatoria antes de implementar:

- `CLAUDE.md` — convencoes, stack, estrutura
- `.specs/features/25_marcador_personagem_ativo/spec.md` — criterios de aceitacao
- `.specs/design.md` secao 7.1 — spec tecnica do marcador (tweens, cores, offsets)
- `.specs/prd.md` secao 7.6 — requisito de UX
- `.specs/notes.md` — notas sobre arquitetura do BattleScene (HUD modules, depth layers, CLASS_DISPLAY)
- `frontend/src/scenes/BattleScene.ts` — cena principal, `updateTurnState`, `shutdown`, `handleBattleEnd`
- `frontend/src/scenes/battle-hud.ts` — referencia de padrao (componente instanciado no BattleScene)

---

## Plano de Execucao

Feature pequena, 1 grupo unico (sequencial). Sem TDD — e um componente puramente visual (tweens Phaser), nao ha logica testavel unitariamente.

---

### Grupo 1 — Implementar marcador e integrar no BattleScene

**Tarefa:** Criar componente `BattleActiveMarker` e integrar no `BattleScene` para exibir marcador visual no personagem ativo e traduzir entity_id para nome de classe.

1. Criar `frontend/src/scenes/battle-active-marker.ts`:
   - Classe `BattleActiveMarker` com constructor recebendo `Phaser.Scene`
   - Metodo `show(worldX: number, worldY: number, team: string)`:
     - Chama `hide()` primeiro para limpar marcador anterior
     - Cria anel (`Phaser.GameObjects.Arc`): raio ~30, sem fill, stroke width 3, cor baseada em `team` (`0x4488ff` para `"player"`, `0xff4444` para outros)
     - Adiciona tween yo-yo no anel: `scaleX`/`scaleY` de 1.0 a 1.15, duracao 600ms, loop -1 (infinito)
     - Cria seta (triangulo via `Phaser.GameObjects.Triangle`): posicao `worldY - 40`, mesma cor do anel
     - Adiciona tween yo-yo na seta: `y` +-4px, duracao 800ms, loop -1
     - Depth do anel e seta: 150 (acima do grid/objetos depth 50-51, abaixo de HP bars depth 100)
   - Metodo `hide()`: destroi anel e seta se existirem, para tweens
   - Metodo `destroy()`: chama `hide()`

2. Adicionar lookup `CLASS_DISPLAY` em `BattleScene.ts` (se nao existir — ja existe em `MenuScene.ts` e `PreparationScene.ts`, copiar o mesmo mapa):
   ```typescript
   const CLASS_DISPLAY: Record<string, string> = {
     warrior: "Guerreiro", mage: "Mago", cleric: "Clerigo",
     archer: "Arqueiro", assassin: "Assassino",
   };
   ```

3. Modificar `BattleScene.ts`:
   - Adicionar campo `private activeMarker!: BattleActiveMarker`
   - No `create()`: instanciar `this.activeMarker = new BattleActiveMarker(this)`
   - Modificar `updateTurnState(entityId)`:
     - Buscar `CharacterEntry` do `entityId` no `this.characters`
     - Obter posicao pixel via `this.gridToPixel(entry.data.position.x, entry.data.position.y)`
     - Chamar `this.activeMarker.show(px, py, entry.data.team)`
     - Trocar texto do `turnIndicator` de `entityId` para `CLASS_DISPLAY[entry.data.class_id] ?? entityId`
   - Modificar `handleBattleEnd()`: chamar `this.activeMarker.hide()` antes de `this.scene.start("ResultScene", ...)`
   - Modificar `shutdown()`: adicionar `this.activeMarker?.destroy()`

4. Verificar manualmente que:
   - No primeiro turno, o marcador aparece no personagem correto
   - Ao trocar turno (jogador → IA → jogador), o marcador muda instantaneamente
   - O texto no topo mostra "Guerreiro" / "Mago" etc. em vez de entity_id

---

## Condicao de Conclusao

Todos os criterios de aceitacao em spec.md satisfeitos.
TypeScript compila sem erros (`npx tsc --noEmit`).
Testes existentes continuam passando (`npx vitest run`).
Atualizar `.specs/state.md`: setar feature 25 para `concluida`.
