# Tasks — Feature 28: Painel de Detalhes do Personagem

## Antes de Comecar

Leitura obrigatoria antes de implementar:

- `CLAUDE.md` — convencoes, stack
- `.specs/features/28_painel_detalhes_aliado/spec.md` — criterios de aceitacao
- `.specs/design.md` secao 7.4 — spec tecnica (layouts, dados, implementacao)
- `.specs/prd.md` secao 7.8 — requisito de UX
- `.specs/notes.md` — "efeitos ativos rastreados localmente", "PA e cooldowns rastreados localmente"
- `frontend/src/scenes/BattleScene.ts` — `characters` map, `playerCooldowns`, `activeEffects`, `currentCharacter`, `currentPA`, `isAnimating`
- `frontend/src/network/types.ts` — `CharacterOut` (attributes, abilities), `AbilityOut`

---

## Plano de Execucao

2 grupos sequenciais. Sem TDD — componente primariamente visual. O Grupo 1 cria o componente, o Grupo 2 integra no BattleScene.

---

### Grupo 1 — Componente CharacterDetailPanel

**Tarefa:** Criar componente que renderiza o painel de detalhes com base nos dados recebidos.

1. Criar `frontend/src/scenes/battle-detail-panel.ts`:
   - Interface `DetailPanelData`:
     ```typescript
     interface DetailPanelData {
       className: string;          // nome em portugues
       team: string;               // "player" ou "ai"
       currentHp: number;
       maxHp: number;
       pa?: number;                // undefined se nao for o personagem ativo
       attributes?: Record<string, number>;  // atributos finais (somente aliados)
       effects: { tag: string; duration: number }[];
       abilities?: { name: string; cooldownRemaining: number }[];  // somente aliados
     }
     ```
   - Classe `CharacterDetailPanel` com constructor recebendo `Phaser.Scene`
   - Propriedades internas:
     - `container: Phaser.GameObjects.Container | null`
     - `objects: Phaser.GameObjects.GameObject[]` — todos os objetos criados (para cleanup)
   - Metodo `show(data: DetailPanelData)`:
     - Chama `hide()` primeiro
     - Calcula tamanho do painel baseado no conteudo (aliado = maior, inimigo = menor)
     - Cria container Phaser em posicao centralizada na tela (640, 360) com depth 300
     - Renderiza background: retangulo solido `0x1a1a2e` com borda (stroke 2): `0x4488ff` para player, `0xff4444` para outros
     - Renderiza header: "{className}    HP: {currentHp}/{maxHp}"
     - Se `pa !== undefined`: renderiza "PA: {pa}/4"
     - Se `attributes` presente (aliado):
       - Renderizar 5 atributos com modificador: `FOR: {val} ({mod})` etc.
       - Usar `ATTR_LABELS` lookup: str→FOR, dex→DES, con→CON, int_→INT, wis→SAB
       - Modificador = valor - 5, formatado como "+N" ou "-N"
     - Se `effects.length > 0`: renderizar lista de efeitos com duracao
     - Se `effects.length === 0`: renderizar "Nenhum efeito"
     - Se `abilities` presente (aliado):
       - Renderizar cada habilidade com estado: nome + "OK" ou "CD: {n}"
     - Texto: monospace 14px para header, 13px para body, cores claras
   - Metodo `hide()`: destroi container e todos os objects
   - Metodo `isVisible(): boolean`: retorna `container !== null`
   - Metodo `destroy()`: chama `hide()`

---

### Grupo 2 — Integrar no BattleScene

**Tarefa:** Detectar cliques em sprites de personagens, coletar dados, e abrir/fechar o painel.

1. Modificar `BattleScene.ts`:
   - Importar `CharacterDetailPanel` e `DetailPanelData`
   - Adicionar campo `private detailPanel!: CharacterDetailPanel`
   - No `create()`: instanciar `this.detailPanel = new CharacterDetailPanel(this)`

2. Tornar sprites de personagens clicaveis:
   - No `renderCharacters()`, adicionar `container.setInteractive(...)` com hitArea circular (raio ~24)
   - Adicionar handler `container.on("pointerdown", () => this.onCharacterClick(char.entity_id))`
   - Isso deve **nao** conflitar com `onTileClick` — o clique no personagem deve ter prioridade (sprites estao acima dos tiles por z-depth)

3. Implementar `private onCharacterClick(entityId: string)`:
   - Se `this.detailPanel.isVisible()`, fechar e se o entityId for o mesmo, return (toggle)
   - Buscar entry no `this.characters`
   - Se `entry.status === "dead"`, return
   - Montar `DetailPanelData`:
     - `className`: `CLASS_DISPLAY[entry.data.class_id]`
     - `team`: `entry.data.team`
     - `currentHp`: `entry.data.current_hp`
     - `maxHp`: `entry.data.max_hp`
     - `pa`: se `entityId === this.currentCharacter`, usar `this.currentPA`; senao, `undefined`
     - Se aliado (`team === "player"`):
       - `attributes`: `entry.data.attributes`
       - `abilities`: mapear `entry.data.abilities` com cooldown do `this.playerCooldowns.get(entityId)`
       - Para cada ability: `{ name: ability.name, cooldownRemaining: cds?.get(ability.id) ?? 0 }`
     - `effects`: mapear `this.activeEffects.get(entityId)` — nota: atualmente o `activeEffects` armazena apenas tags (Set<string>), nao duracao. Se duracao nao estiver disponivel, exibir apenas a tag sem duracao. Considerar estender `activeEffects` para `Map<string, { tag: string, duration: number }>` se o backend enviar duracao no evento `effect_applied`.
   - Chamar `this.detailPanel.show(data)`

4. Fechar o painel:
   - No handler `keydown-ESC` existente: adicionar `this.detailPanel.hide()`
   - No `onTileClick`: adicionar `this.detailPanel.hide()` no inicio (antes de processar o clique no tile)
   - Nos handlers async (`handleTurnStart`, `handleActionResult`, `handleAiAction`): adicionar `this.detailPanel.hide()` quando `isAnimating` se torna true

5. Cleanup:
   - Em `shutdown()`: adicionar `this.detailPanel?.destroy()`
   - Em `handleBattleEnd()`: adicionar `this.detailPanel?.hide()`

6. Verificar manualmente que:
   - Clicar em aliado mostra painel completo com HP, PA, atributos, efeitos, habilidades
   - Clicar em inimigo mostra painel reduzido (HP + efeitos apenas)
   - ESC fecha o painel
   - Clicar em tile fecha o painel
   - O painel fecha automaticamente ao iniciar animacao

---

## Condicao de Conclusao

Todos os criterios de aceitacao em spec.md satisfeitos.
TypeScript compila sem erros (`npx tsc --noEmit`).
Testes existentes continuam passando (`npx vitest run`).
Atualizar `.specs/state.md`: setar feature 28 para `concluida`.
