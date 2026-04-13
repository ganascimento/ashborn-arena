# Tasks — Feature 09: Ataque de Oportunidade

## Antes de Comecar

Ler obrigatoriamente antes de escrever qualquer codigo:

- `CLAUDE.md` — stack, estrutura do projeto, convencoes
- `.specs/features/09_ataque_oportunidade/spec.md` — criterios de aceitacao desta feature
- `.specs/design.md` secao 3.11 (ataque de oportunidade — regras, habilidades que nao provocam)
- `.specs/prd.md` secao 2.4 (ataque de oportunidade)
- `engine/models/grid.py` — Grid, Occupant, OccupantType, Team, get_adjacent_positions
- `engine/models/position.py` — Position

---

## Plano de Execucao

2 grupos sequenciais. Grupo 1 e a fase TDD (testes primeiro). Grupo 2 e a implementacao.

- **Grupo 1**: escrever todos os testes (test_opportunity.py). Parar apos criar os testes.
- **Grupo 2**: implementar (opportunity.py + atualizar __init__.py). Rodar testes para validar.

Dependencia: Grupo 2 so executa apos aprovacao dos testes do Grupo 1.

---

### Grupo 1 — Testes (TDD)

**Tarefa:** Criar testes unitarios para a deteccao de ataques de oportunidade. Cobrir todos os criterios de aceitacao do spec.md.

1. Criar `engine/tests/test_opportunity.py`:
   - **Trigger basico:**
     - Grid com mover (Team.A) em (3,3), inimigo (Team.B) em (4,4), mover vai para (3,5). Inimigo adjacente em (3,3) mas NAO em (3,5) → retorna [(enemy_id, Position(4,4))]
   - **Sem trigger — permanece adjacente:**
     - Mover em (3,3), inimigo em (4,4), destino (3,4). Inimigo adjacente em ambas posicoes → lista vazia
   - **Sem trigger — nunca adjacente:**
     - Mover em (3,3), inimigo em (6,6), destino (3,5) → lista vazia
   - **Multiplos inimigos — ambos triggeram:**
     - Mover em (3,3), inimigos em (4,3) e (2,3), destino (3,5). Ambos perdem adjacencia → retorna 2 tuplas
   - **Multiplos inimigos — apenas 1 trigger:**
     - Mover em (3,3), inimigos em (4,4) e (4,3), destino (4,5). Inimigo em (4,4) adjacente a (4,5) → nao trigger. Inimigo em (4,3) nao adjacente a (4,5) → trigger. Lista retorna 1.
   - **Aliado nao trigger:**
     - Mover (Team.A) em (3,3), aliado (Team.A) em (4,4), destino (3,5) → lista vazia
   - **Objeto nao trigger:**
     - Mover em (3,3), objeto em (4,4), destino (3,5) → lista vazia
   - **Borda do grid:**
     - Mover em (0,0), inimigo em (1,1), destino (0,2). Inimigo adjacente em (0,0) mas nao em (0,2) → trigger
   - **Mesma posicao:**
     - Mover em (3,3), destino (3,3), inimigo em (4,4) → lista vazia
   - **Grid vazio (sem inimigos):**
     - Mover em (3,3), destino (3,5), ninguem mais → lista vazia

2. Rodar `pytest engine/tests/test_opportunity.py` e confirmar que todos os testes falham.

**Parar apos criar os testes. Nao implementar logica de producao. Aguardar aprovacao do usuario.**

---

### Grupo 2 — Implementacao (um agente)

**Tarefa:** Implementar a deteccao de ataques de oportunidade. Todos os testes do Grupo 1 devem passar ao final.

1. Criar `engine/systems/opportunity.py`:
   - `get_opportunity_attackers(grid: Grid, mover_position: Position, destination: Position, mover_team: Team) -> list[tuple[str, Position]]`:
     - Se mover_position == destination: retorna []
     - Obtem posicoes adjacentes a mover_position via grid.get_adjacent_positions
     - Para cada posicao adjacente:
       - Obtem ocupantes via grid.get_occupants
       - Para cada ocupante que e CHARACTER e team != mover_team:
         - Verifica se a posicao do inimigo NAO e adjacente ao destination
         - Se nao adjacente ao destino: adiciona (entity_id, posicao) ao resultado
     - "Adjacente ao destino" = posicao do inimigo esta em grid.get_adjacent_positions(destination)
     - Retorna lista de (entity_id, position)

2. Atualizar `engine/systems/__init__.py`:
   - Adicionar import: `from engine.systems.opportunity import get_opportunity_attackers`
   - Adicionar ao `__all__`

3. Rodar `pytest engine/tests/test_opportunity.py -v` e confirmar que todos os testes passam.

4. Rodar `pytest engine/tests/ -v` para garantir zero regressoes.

---

## Condicao de Conclusao

- Todos os criterios de aceitacao do spec.md satisfeitos
- Todos os testes passam com `pytest engine/tests/ -v`
- Atualizar `.specs/state.md`: status da feature 09 de `pendente` para `concluida`
