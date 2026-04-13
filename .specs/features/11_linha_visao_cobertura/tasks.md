# Tasks — Feature 11: Linha de Visao e Cobertura

## Antes de Comecar

Ler obrigatoriamente antes de escrever qualquer codigo:

- `CLAUDE.md` — stack, estrutura do projeto, convencoes
- `.specs/features/11_linha_visao_cobertura/spec.md` — criterios de aceitacao desta feature
- `.specs/design.md` secao 4.3 (LoS — calculo, bloqueio, AoE, Meteoro, corpo a corpo)
- `.specs/prd.md` secao 6.6 (linha de visao e cobertura)
- `engine/models/grid.py` — Grid (referencia de dimensoes e adjacencia)
- `engine/models/position.py` — Position
- `engine/models/map_object.py` — MapObject, blocks_los (propriedade que determina se um objeto bloqueia visao)

---

## Plano de Execucao

2 grupos sequenciais. Grupo 1 e a fase TDD (testes primeiro). Grupo 2 e a implementacao.

- **Grupo 1**: escrever todos os testes (test_line_of_sight.py). Parar apos criar os testes.
- **Grupo 2**: implementar (line_of_sight.py + atualizar __init__.py). Rodar testes para validar.

Dependencia: Grupo 2 so executa apos aprovacao dos testes do Grupo 1.

---

### Grupo 1 — Testes (TDD)

**Tarefa:** Criar testes unitarios para o sistema de linha de visao. Cobrir todos os criterios de aceitacao do spec.md.

1. Criar `engine/tests/test_line_of_sight.py`:
   - **get_tiles_in_line:**
     - (0,0) → (4,0) retorna [(1,0), (2,0), (3,0)]
     - (0,0) → (0,4) retorna [(0,1), (0,2), (0,3)]
     - (0,0) → (3,3) retorna posicoes diagonais intermediarias
     - (3,3) → (3,3) retorna [] (mesma posicao)
     - (3,3) → (4,4) retorna [] (adjacentes sem intermediarios)
     - (5,3) → (0,3) retorna [(4,3), (3,3), (2,3), (1,3)] (direcao inversa funciona)
   - **has_line_of_sight — sem obstrucao:**
     - Linha horizontal (0,3) → (5,3), bloqueadores vazio → True
     - Linha vertical (3,0) → (3,5) → True
     - Linha diagonal (0,0) → (4,4) → True
     - Mesma posicao (3,3) → (3,3) → True
     - Adjacente (3,3) → (4,4) → True
   - **has_line_of_sight — com obstrucao:**
     - Horizontal (0,3) → (5,3), bloqueador em (3,3) → False
     - Diagonal (0,0) → (4,4), bloqueador em (2,2) → False
     - Bloqueador no origin (0,3): nao bloqueia (origin excluido) → True
     - Bloqueador no target (5,3): nao bloqueia (target excluido) → True
     - Objeto que NAO bloqueia LoS em tile intermediario → True
     - Multiplos tiles, 1 bloqueador entre eles → False

2. Rodar `pytest engine/tests/test_line_of_sight.py` e confirmar que todos os testes falham.

**Parar apos criar os testes. Nao implementar logica de producao. Aguardar aprovacao do usuario.**

---

### Grupo 2 — Implementacao (um agente)

**Tarefa:** Implementar o sistema de linha de visao. Todos os testes do Grupo 1 devem passar ao final.

1. Criar `engine/systems/line_of_sight.py`:
   - `get_tiles_in_line(origin: Position, target: Position) -> list[Position]`:
     - Usa algoritmo de Bresenham para tracar linha entre os dois tiles
     - Retorna lista de posicoes intermediarias (excluindo origin e target)
     - Se origin == target: retorna []
     - Se adjacentes sem intermediarios: retorna []
   - `has_line_of_sight(origin: Position, target: Position, blocking_positions: set[Position]) -> bool`:
     - Obtem tiles intermediarios via get_tiles_in_line
     - Retorna False se qualquer tile intermediario esta em blocking_positions
     - Retorna True caso contrario
     - O caller e responsavel por construir blocking_positions a partir dos MapObjects com blocks_los=True no grid

2. Atualizar `engine/systems/__init__.py`:
   - Adicionar imports: `from engine.systems.line_of_sight import get_tiles_in_line, has_line_of_sight`
   - Adicionar ao `__all__`

3. Rodar `pytest engine/tests/test_line_of_sight.py -v` e confirmar que todos os testes passam.

4. Rodar `pytest engine/tests/ -v` para garantir zero regressoes.

---

## Condicao de Conclusao

- Todos os criterios de aceitacao do spec.md satisfeitos
- Todos os testes passam com `pytest engine/tests/ -v`
- Atualizar `.specs/state.md`: status da feature 11 de `pendente` para `concluida`
