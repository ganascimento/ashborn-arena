# Tasks — Feature 24: Resultado

## Antes de Comecar

Ler obrigatoriamente antes de escrever qualquer codigo:

- `CLAUDE.md` — stack, estrutura, convencoes (ingles, sem docstrings, models separadas)
- `.specs/features/24_resultado/spec.md` — criterios de aceitacao desta feature
- `.specs/notes.md` — "BattlePlaceholderScene com key BattleScene — Feature 24 deve substituir ResultPlaceholderScene mantendo key ResultScene"
- `frontend/src/scenes/ResultPlaceholderScene.ts` — placeholder atual a ser substituido
- `frontend/src/scenes/BattleScene.ts` — handleBattleEnd que transiciona para ResultScene
- `frontend/src/main.ts` — setup atual do Phaser (importa ResultPlaceholderScene)

---

## Plano de Execucao

```
Grupo 1 — ResultScene + wiring (um unico agente)
```

Feature pequena com um unico grupo. Todos os arquivos estao inter-relacionados (criar ResultScene, modificar BattleScene para passar dados, atualizar main.ts, remover placeholder).

---

### Grupo 1 — ResultScene e Wiring (um agente)

**Tarefa:** Criar a cena de resultado completa, atualizar BattleScene para passar dados de resumo, e fazer wiring em main.ts.

1. Criar `frontend/src/scenes/ResultScene.ts`:

   - Classe `ResultScene extends Phaser.Scene` com key `"ResultScene"` (mesma key do placeholder — notes.md)

   - Interface para dados recebidos:
     ```typescript
     interface BattleSummaryChar {
       class_id: string;
       team: string;
       status: "active" | "knocked_out" | "dead";
     }

     interface ResultSceneData {
       result: "victory" | "defeat";
       characters: BattleSummaryChar[];
     }
     ```

   - Constante de display:
     ```typescript
     const CLASS_DISPLAY: Record<string, string> = {
       warrior: "Guerreiro",
       mage: "Mago",
       cleric: "Clerigo",
       archer: "Arqueiro",
       assassin: "Assassino",
     };
     const STATUS_DISPLAY: Record<string, { text: string; color: string }> = {
       active: { text: "Vivo", color: "#44ff44" },
       knocked_out: { text: "Caido", color: "#ffaa00" },
       dead: { text: "Morto", color: "#ff4444" },
     };
     ```

   - Metodo `init(data: ResultSceneData)`: armazenar data em campo privado

   - Metodo `create()`:
     a. Banner de resultado (centralizado, y=150):
        - "VITORIA!" em verde #44ff44 ou "DERROTA!" em vermelho #ff4444
        - fontSize 52px, fontFamily monospace, fontStyle bold
        - setOrigin(0.5) em x=640

     b. Subtitulo "Resumo da Batalha" (x=640, y=220, fontSize 18px, cor #888888)

     c. Bloco "Seu Time" (x=400, y=280):
        - Titulo "Seu Time" fontSize 22px, cor #e0e0e0, setOrigin(0.5)
        - Filtrar characters por team === "player"
        - Para cada personagem (i), y = 320 + i * 40:
          - Texto: `{CLASS_DISPLAY[class_id]}  —  {STATUS_DISPLAY[status].text}`
          - Cor do nome: #cccccc
          - Cor do status: STATUS_DISPLAY[status].color
          - Pode ser um unico texto com cor do status, ou dois textos lado a lado

     d. Bloco "Time da IA" (x=880, y=280):
        - Mesmo layout, filtrando team !== "player"

     e. Botao "Voltar ao Menu" (x=640, y=600):
        - Texto fontSize 24px, cor #aaaaaa, fontFamily monospace
        - setOrigin(0.5), setInteractive({ useHandCursor: true })
        - pointerover: setColor("#ffffff"), setScale(1.1)
        - pointerout: setColor("#aaaaaa"), setScale(1)
        - pointerdown: `this.scene.start("MenuScene")`

   - Export: `export default class ResultScene`

2. Modificar `frontend/src/scenes/BattleScene.ts`:

   - No metodo `handleBattleEnd(msg)`, substituir:
     ```typescript
     this.scene.start("ResultScene", { result: msg.result });
     ```
     por:
     ```typescript
     const characters: { class_id: string; team: string; status: string }[] = [];
     for (const [, entry] of this.characters) {
       characters.push({
         class_id: entry.data.class_id,
         team: entry.data.team,
         status: entry.status,
       });
     }
     this.scene.start("ResultScene", { result: msg.result, characters });
     ```

3. Modificar `frontend/src/main.ts`:

   - Substituir `import ResultPlaceholderScene from "./scenes/ResultPlaceholderScene"` por `import ResultScene from "./scenes/ResultScene"`
   - Atualizar array de scenes: `[MenuScene, PreparationScene, BattleScene, ResultScene]`

4. Deletar `frontend/src/scenes/ResultPlaceholderScene.ts`

5. Verificar build: `npx tsc --noEmit` e `npx vite build` devem compilar sem erros.
   Verificar testes: `npm run test -- --run` deve passar todos os testes existentes.

---

## Condicao de Conclusao

- Todos os criterios de aceitacao em spec.md estao satisfeitos
- Testes existentes passam com `npm run test` (vitest)
- Build compila sem erros: `npx tsc --noEmit`
- Fluxo completo funciona no browser (com backend rodando):
  - Menu → Preparacao → Batalha → Resultado
  - Resultado exibe banner de vitoria ou derrota
  - Resumo mostra personagens de ambos os times com status final
  - "Voltar ao Menu" retorna a MenuScene
  - Novo ciclo Menu → Preparacao → Batalha → Resultado funciona sem problemas
- Atualizar `.specs/state.md`: status da feature 24 para `concluida`
