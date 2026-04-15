# Feature 26 — Correcao Custo PA de Movimento

## Objetivo

Corrigir o calculo de custo de PA por movimento no frontend. A regra do jogo e **2 tiles por 1 PA** (prd.md 6.2), mas o codigo atual calcula `Math.ceil(dist / 2)` por segmento individual do caminho, resultando em 1 PA por tile quando o jogador se move tile a tile. O fix deve acumular a distancia total do caminho primeiro e so entao aplicar `Math.ceil(total / 2)`.

---

## Referencia nos Specs

- prd.md: secao 6.2 (Movimentacao — 2 tiles por 1 PA)
- design.md: secao 7.2 (Correcao do Custo de PA por Movimento)
- notes.md: "PA e cooldowns rastreados localmente" — descreve o mecanismo atual

---

## Arquivos Envolvidos

### Modificar

| Arquivo | Descricao |
|---|---|
| `frontend/src/scenes/BattleScene.ts` | Corrigir `updatePAFromAction` — acumular distancia total antes de calcular custo |
| `frontend/src/scenes/__tests__/update-state.test.ts` | Adicionar testes para calculo de custo PA por movimento (opcional — pode ser arquivo de teste separado) |

---

## Criterios de Aceitacao

### Calculo de PA

- [ ] Mover 1 tile custa **1 PA** (`Math.ceil(1 / 2) = 1`)
- [ ] Mover 2 tiles custa **1 PA** (`Math.ceil(2 / 2) = 1`)
- [ ] Mover 3 tiles custa **2 PA** (`Math.ceil(3 / 2) = 2`)
- [ ] Mover 4 tiles custa **2 PA** (`Math.ceil(4 / 2) = 2`)
- [ ] Mover 8 tiles (maximo teorico: 4 PA) custa **4 PA** (`Math.ceil(8 / 2) = 4`)

### Correcao do Bug

- [ ] `updatePAFromAction` acumula distancia total de **todos os segmentos** de move/ability_movement no `events` array antes de aplicar `Math.ceil(totalDist / 2)`
- [ ] O custo nao e mais calculado por segmento individual (bug anterior: `Math.ceil(1/2) = 1` por tile)

### Nao-regressao

- [ ] Custo de basic_attack continua **2 PA**
- [ ] Custo de habilidades continua usando `ability.pa_cost`
- [ ] Cooldowns continuam sendo rastreados corretamente apos uso de habilidade
- [ ] PA e resetado corretamente no `handleTurnStart` (valor vem do `turn_start.pa` do servidor)

---

## Fora do Escopo

- Mudar o backend (o backend ja calcula corretamente — o bug e exclusivamente frontend)
- Validacao de alcance de movimento no frontend (o servidor rejeita movimentos invalidos)
- Exibicao de range de movimento no grid (feature futura)
