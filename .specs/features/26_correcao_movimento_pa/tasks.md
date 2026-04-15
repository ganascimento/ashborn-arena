# Tasks — Feature 26: Correcao Custo PA de Movimento

## Antes de Comecar

Leitura obrigatoria antes de implementar:

- `CLAUDE.md` — convencoes, stack
- `.specs/features/26_correcao_movimento_pa/spec.md` — criterios de aceitacao
- `.specs/design.md` secao 7.2 — explicacao tecnica do bug e sugestao de fix
- `.specs/prd.md` secao 6.2 — regra de movimentacao (2 tiles por 1 PA)
- `.specs/notes.md` — "PA e cooldowns rastreados localmente" (descreve mecanismo atual)
- `frontend/src/scenes/BattleScene.ts` — metodo `updatePAFromAction` (linhas ~462-497)

---

## Plano de Execucao

Feature pequena com logica testavel. TDD aplica-se: Grupo 1 cria testes, Grupo 2 corrige o bug.

---

### Grupo 1 — Testes para calculo de custo PA (TDD)

**Tarefa:** Criar testes unitarios que validam o calculo correto de custo de PA por movimento.

1. Criar `frontend/src/scenes/__tests__/movement-pa-cost.test.ts`:
   - Extrair a logica de calculo de custo de movimento para funcao pura testavel: `calculateMovementCost(events: Record<string, unknown>[]): number`
   - Testes:
     - Move 1 tile (from [0,0] to [1,0]) → custo 1 PA
     - Move 2 tiles (from [0,0] to [2,0]) → custo 1 PA
     - Move 3 tiles (from [0,0] to [3,0]) → custo 2 PA
     - Move 4 tiles (from [0,0] to [4,0]) → custo 2 PA
     - Move 8 tiles (from [0,0] to [8,0]) → custo 4 PA
     - Diagonal move 2 tiles (from [0,0] to [2,2]) → distancia Chebyshev = 2, custo 1 PA
     - Multi-segment path: 2 eventos de move ([0,0]→[1,0] + [1,0]→[2,0]) → distancia total 2, custo 1 PA (nao 2 PA)
     - Eventos vazios → custo 0
     - Eventos sem move (apenas outros tipos) → custo 0
   - Usar field names flexiveis: testar com `from`/`to` como arrays e como objetos `{x, y}`

**Pausa:** Parar apos criar os testes. Nao implementar logica de producao. Aguardar aprovacao do usuario.

---

### Grupo 2 — Corrigir updatePAFromAction

**Tarefa:** Extrair funcao de calculo e corrigir o bug no BattleScene.

1. Criar funcao exportada `calculateMovementCost` em `frontend/src/scenes/BattleScene.ts` (ou em arquivo utilitario separado se preferir — ex: `frontend/src/scenes/movement-cost.ts`):
   ```typescript
   export function calculateMovementCost(events: unknown[]): number {
     let totalDist = 0;
     for (const raw of events) {
       const event = raw as Record<string, unknown>;
       if (event.type === "move" || event.type === "ability_movement") {
         const from = event.from as ...;
         const to = (event.to ?? event.position) as ...;
         if (from && to) {
           const [fx, fy] = Array.isArray(from) ? from : [from.x, from.y];
           const [tx, ty] = Array.isArray(to) ? to : [to.x, to.y];
           totalDist += Math.max(Math.abs(tx - fx), Math.abs(ty - fy));
         }
       }
     }
     return Math.ceil(totalDist / 2);
   }
   ```

2. Modificar `updatePAFromAction` em `BattleScene.ts`:
   - Substituir o loop de move que calcula `cost += Math.ceil(dist / 2)` por segmento
   - Usar `cost = calculateMovementCost(msg.events)` para o caso `msg.action === "move"`
   - Manter inalterados os casos de `basic_attack` e `ability`

3. Rodar testes: `npx vitest run` — todos devem passar, incluindo os novos do Grupo 1

---

## Condicao de Conclusao

Todos os criterios de aceitacao em spec.md satisfeitos.
Todos os testes passam com `npx vitest run`.
TypeScript compila sem erros (`npx tsc --noEmit`).
Atualizar `.specs/state.md`: setar feature 26 para `concluida`.
