# Feature 01 — Grid e Movimentacao

## Objetivo

Implementar o grid de batalha (10x8) e o sistema de movimentacao que permite personagens se deslocarem pelo campo respeitando regras de bloqueio, aliados e inimigos. Esta e a camada espacial fundamental do engine — todas as features de combate, habilidades, LoS, objetos interativos e geracao procedural dependem dela.

---

## Referencia nos Specs

- prd.md: secoes 6.1 (grid), 6.2 (movimentacao), 6.3 (zonas de spawn)
- design.md: secoes 1.3 (movimentacao), 4.1 (grid e movimentacao)

---

## Arquivos Envolvidos

### Criar

- `engine/models/position.py` — dataclass Position(x, y), imutavel e hashable
- `engine/models/grid.py` — Team enum, OccupantType enum, Occupant dataclass, Grid class (10x8)
- `engine/systems/movement.py` — get_reachable_tiles(), find_path(), execute_move(), tiles_for_pa()
- `engine/tests/test_grid.py` — testes unitarios do Grid
- `engine/tests/test_movement.py` — testes unitarios do sistema de movimentacao

### Modificar

- `engine/models/__init__.py` — re-exportar Position, Team, OccupantType, Occupant, Grid
- `engine/systems/__init__.py` — re-exportar funcoes de movement

---

## Criterios de Aceitacao

### Grid

- [ ] Grid possui 10 colunas (x: 0-9) e 8 linhas (y: 0-7), totalizando 80 tiles
- [ ] `is_within_bounds(Position(0, 0))` retorna True; `is_within_bounds(Position(10, 0))` retorna False; `is_within_bounds(Position(-1, 0))` retorna False; `is_within_bounds(Position(0, 8))` retorna False
- [ ] `place_occupant(position, occupant)` adiciona ocupante ao tile; raise se posicao fora dos limites; raise se ja existe CHARACTER no tile e novo ocupante tambem e CHARACTER
- [ ] `remove_occupant(position, entity_id)` remove ocupante especifico do tile pelo entity_id
- [ ] `get_occupants(position)` retorna lista de ocupantes no tile (lista vazia se nenhum)
- [ ] Tile suporta multiplos ocupantes (personagem sobre objeto nao-bloqueante), mas no maximo 1 CHARACTER por tile
- [ ] `get_spawn_positions(Team.A)` retorna 16 posicoes (colunas 0-1, linhas 0-7); `get_spawn_positions(Team.B)` retorna 16 posicoes (colunas 8-9, linhas 0-7)
- [ ] `get_adjacent_positions(Position(4, 4))` retorna 8 posicoes (8 direcoes); `get_adjacent_positions(Position(0, 0))` retorna 3 posicoes; `get_adjacent_positions(Position(5, 0))` retorna 5 posicoes (borda)
- [ ] Position e imutavel e hashable — pode ser usada em sets e como chave de dict

### Movimentacao

- [ ] `get_reachable_tiles(grid, start, max_tiles, mover_team)` retorna conjunto de posicoes alcancaveis via BFS respeitando bloqueios
- [ ] Diagonal custa o mesmo que ortogonal — cada passo (8 direcoes) consome 1 tile de budget
- [ ] Grid vazio, Position(5, 4), max_tiles=2: retorna 24 tiles (quadrado 5x5 centrado, menos o centro, todos dentro dos limites do grid)
- [ ] Grid vazio, Position(0, 0), max_tiles=2: retorna 8 tiles (limitado pelas bordas)
- [ ] max_tiles=0: retorna conjunto vazio (nao pode mover)
- [ ] Inimigo em (4, 4): personagem em (3, 4) com max_tiles=1 NAO alcanca (4, 4) — inimigo bloqueia passagem
- [ ] Aliado em (4, 4): personagem em (3, 4) com max_tiles=2 alcanca (5, 4) passando atraves do aliado — mas (4, 4) NAO esta no resultado (nao pode parar em tile de aliado)
- [ ] Objeto com blocks_movement=True bloqueia passagem para qualquer equipe
- [ ] Objeto com blocks_movement=False NAO bloqueia — tile esta no resultado de reachable
- [ ] `find_path(grid, start, end, mover_team)` retorna caminho mais curto como lista de Positions (incluindo start e end), ou None se inalcancavel
- [ ] Grid vazio, (3, 3) a (5, 3): path de 3 posicoes [(3,3), (4,3), (5,3)] — 2 passos
- [ ] Inimigo em (4, 3): caminho de (3, 3) a (5, 3) contorna o inimigo (path com mais de 3 posicoes)
- [ ] `execute_move(grid, entity_id, start, end, max_tiles)` valida movimento, atualiza grid (remove de start, coloca em end), retorna caminho percorrido
- [ ] `execute_move` falha (raise) se destino nao e alcancavel dentro de max_tiles
- [ ] `tiles_for_pa(pa)` retorna `pa * 2` (2 tiles por 1 PA, conforme design.md 4.1)
- [ ] `tiles_for_pa(4)` retorna 8 (maximo teorico: 4 PA gastos em movimentacao = 8 tiles)

---

## Fora do Escopo

- Consumo e tracking de PA durante o turno — feature 02 (sistema de turnos e PA)
- Ataque de oportunidade ao sair do corpo a corpo — feature 09
- Objetos interativos com HP, fogo, arremesso — feature 10 (grid armazena ocupantes genericos com flag blocks_movement, sem logica de interacao)
- Linha de visao e cobertura — feature 11
- Geracao procedural de mapas — feature 12
- Modelo de Character com atributos, HP, habilidades — feature 03 (grid usa entity_id generico e Team)
