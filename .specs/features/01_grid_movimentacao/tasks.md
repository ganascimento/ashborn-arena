# Tasks — Feature 01: Grid e Movimentacao

## Antes de Comecar

- `CLAUDE.md` — stack, estrutura do projeto, convencoes (ingles, sem docstrings)
- `.specs/features/01_grid_movimentacao/spec.md` — criterios de aceitacao desta feature
- `.specs/prd.md` secoes 6.1-6.3 — grid, movimentacao, zonas de spawn
- `.specs/design.md` secoes 1.3, 4.1 — movimentacao, grid e movimentacao

---

## Plano de Execucao

2 grupos sequenciais. Grupo 1 (TDD) cria os testes e para. Grupo 2 implementa o codigo de producao para fazer os testes passarem.

- **Grupo 1** → pausa obrigatoria → aprovacao do usuario → **Grupo 2**

---

### Grupo 1 — Testes (TDD red phase)

**Tarefa:** Criar testes unitarios para o grid e sistema de movimentacao cobrindo todos os criterios de aceitacao do spec.md.

1. Criar `engine/tests/test_grid.py`:
   - Testar criacao do Grid com dimensoes 10x8
   - Testar `is_within_bounds` com posicoes validas: (0,0), (9,7), (5,4)
   - Testar `is_within_bounds` com posicoes invalidas: (-1,0), (10,0), (0,8), (0,-1)
   - Testar `place_occupant` + `get_occupants` — colocar CHARACTER e verificar presenca
   - Testar `place_occupant` com posicao fora dos limites — deve levantar erro
   - Testar `place_occupant` de dois CHARACTERs no mesmo tile — deve levantar erro
   - Testar `place_occupant` de CHARACTER + OBJECT (blocks_movement=False) no mesmo tile — deve funcionar
   - Testar `remove_occupant` — remover por entity_id e verificar tile atualizado
   - Testar `get_occupants` em tile vazio — retorna lista vazia
   - Testar `get_spawn_positions(Team.A)` retorna 16 posicoes nas colunas 0-1
   - Testar `get_spawn_positions(Team.B)` retorna 16 posicoes nas colunas 8-9
   - Testar `get_adjacent_positions(Position(4,4))` retorna 8 posicoes
   - Testar `get_adjacent_positions(Position(0,0))` retorna 3 posicoes
   - Testar `get_adjacent_positions(Position(9,7))` retorna 3 posicoes
   - Testar `get_adjacent_positions(Position(5,0))` retorna 5 posicoes
   - Testar que Position e imutavel (frozen dataclass) e hashable (usavel em set e dict)
   - Testar igualdade: `Position(3, 4) == Position(3, 4)` e True

2. Criar `engine/tests/test_movement.py`:
   - Testar `get_reachable_tiles` em grid vazio: Position(5,4), max_tiles=2 retorna 24 tiles
   - Testar `get_reachable_tiles` em grid vazio: Position(0,0), max_tiles=2 retorna 8 tiles
   - Testar `get_reachable_tiles` com max_tiles=0 retorna conjunto vazio
   - Testar bloqueio por inimigo: Team.B em (4,4), mover Team.A de (3,4) max_tiles=1 — (4,4) ausente do resultado
   - Testar passagem por aliado: Team.A em (4,4), mover Team.A de (3,4) max_tiles=2 — (5,4) presente, (4,4) ausente
   - Testar bloqueio por objeto: OBJECT com blocks_movement=True em (4,4) — (4,4) ausente e nao serve como passagem
   - Testar objeto nao-bloqueante: OBJECT com blocks_movement=False em (4,4) — (4,4) presente no resultado
   - Testar contorno de obstaculo: inimigos formando parede parcial, tiles atras da parede so alcancaveis pelo caminho longo
   - Testar `find_path` em grid vazio: (3,3) a (5,3) retorna path com 3 posicoes incluindo start e end
   - Testar `find_path` contornando inimigo: inimigo em (4,3), path de (3,3) a (5,3) tem mais de 3 posicoes
   - Testar `find_path` para destino completamente cercado por inimigos: retorna None
   - Testar `execute_move` com sucesso: personagem muda de posicao no grid, tile antigo fica livre, tile novo tem o personagem
   - Testar `execute_move` com destino fora de alcance: raise erro
   - Testar `tiles_for_pa(1)` retorna 2
   - Testar `tiles_for_pa(4)` retorna 8
   - Testar `tiles_for_pa(0)` retorna 0

3. **PARAR apos criar os testes. Nao implementar codigo de producao. Aguardar aprovacao do usuario.**

---

### Grupo 2 — Implementacao (grid model + movement system)

**Tarefa:** Implementar os domain models do grid e o sistema de movimentacao para passar em todos os testes do Grupo 1.

1. Criar `engine/models/position.py`:
   - Classe `Position` como `@dataclass(frozen=True)` com `x: int` e `y: int`
   - Frozen garante imutabilidade e hashability

2. Criar `engine/models/grid.py`:
   - `Team(Enum)` com valores `A` e `B`
   - `OccupantType(Enum)` com valores `CHARACTER` e `OBJECT`
   - `Occupant` como dataclass com: `entity_id: str`, `occupant_type: OccupantType`, `team: Team | None` (None para objetos), `blocks_movement: bool`
   - `Grid` classe:
     - Constantes `COLS = 10`, `ROWS = 8`
     - Armazenamento interno: `dict[Position, list[Occupant]]`
     - `is_within_bounds(pos)` → bool: `0 <= x < COLS` e `0 <= y < ROWS`
     - `place_occupant(pos, occupant)` → None: valida bounds, valida que nao ha CHARACTER duplicado, adiciona
     - `remove_occupant(pos, entity_id)` → None: remove ocupante com o entity_id do tile
     - `get_occupants(pos)` → list[Occupant]: retorna ocupantes ou lista vazia
     - `get_spawn_positions(team)` → set[Position]: Team.A = colunas 0-1, Team.B = colunas 8-9, todas as linhas
     - `get_adjacent_positions(pos)` → list[Position]: 8 direcoes (dx, dy em [-1, 0, +1]), filtrado por bounds

3. Criar `engine/systems/movement.py`:
   - `get_reachable_tiles(grid, start, max_tiles, mover_team)` → set[Position]:
     - BFS a partir de start, ate max_tiles passos
     - 8 direcoes por passo (diagonal custa o mesmo que ortogonal)
     - Tile e transitavel se: vazio, ou CHARACTER do mesmo team, ou OBJECT com blocks_movement=False
     - Resultado inclui apenas tiles onde o personagem pode PARAR: transitavel E sem nenhum CHARACTER presente
     - Start nao faz parte do resultado
   - `find_path(grid, start, end, mover_team)` → list[Position] | None:
     - BFS de start a end, respeitando as mesmas regras de transitabilidade
     - Retorna caminho incluindo start e end
     - Retorna None se inalcancavel
   - `execute_move(grid, entity_id, start, end, max_tiles)` → list[Position]:
     - Busca team do ocupante CHARACTER em start
     - Verifica que end e alcancavel via get_reachable_tiles com max_tiles
     - Obtem path via find_path
     - Remove ocupante de start, coloca em end (atualiza grid)
     - Retorna path percorrido
     - Raise ValueError se destino inalcancavel ou max_tiles insuficiente
   - `tiles_for_pa(pa: int)` → int: retorna `pa * 2`

4. Atualizar `engine/models/__init__.py`: exportar Position, Team, OccupantType, Occupant, Grid
5. Atualizar `engine/systems/__init__.py`: exportar get_reachable_tiles, find_path, execute_move, tiles_for_pa
6. Rodar `pytest engine/tests/` — todos os testes devem passar

---

## Condicao de Conclusao

- Todos os criterios de aceitacao em spec.md estao satisfeitos
- Todos os testes passam com `pytest engine/tests/`
- Atualizar `.specs/state.md`: status da feature 01 de `pendente` para `concluida`
