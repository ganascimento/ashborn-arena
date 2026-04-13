# Tasks — Feature 12: Geracao Procedural de Mapas

## Antes de Comecar

Ler obrigatoriamente antes de escrever qualquer codigo:

- `CLAUDE.md` — stack, estrutura do projeto, convencoes
- `.specs/features/12_geracao_procedural_mapas/spec.md` — criterios de aceitacao desta feature
- `.specs/design.md` secoes 4.4 (geracao procedural), 4.5 (biomas)
- `.specs/prd.md` secoes 6.7 (biomas), 6.8 (geracao procedural)
- `engine/models/grid.py` — Grid, Occupant, OccupantType (para popular o grid)
- `engine/models/map_object.py` — ObjectType, MapObject, OBJECT_TEMPLATES (objetos a serem colocados)
- `engine/models/position.py` — Position

---

## Plano de Execucao

2 grupos sequenciais. Grupo 1 e a fase TDD (testes primeiro). Grupo 2 e a implementacao.

- **Grupo 1**: escrever todos os testes (test_map_generator.py). Parar apos criar os testes.
- **Grupo 2**: implementar (map_generator.py + atualizar generation/__init__.py). Rodar testes para validar.

Dependencia: Grupo 2 so executa apos aprovacao dos testes do Grupo 1.

---

### Grupo 1 — Testes (TDD)

**Tarefa:** Criar testes unitarios para a geracao procedural de mapas. Cobrir todos os criterios de aceitacao do spec.md.

1. Criar `engine/tests/test_map_generator.py`:
   - **Biome enum:**
     - Biome tem 4 valores: FOREST_DAY, FOREST_NIGHT, VILLAGE, SWAMP
   - **Geracao basica:**
     - generate_map(Biome.VILLAGE, Random(42)) retorna (Grid, list[MapObject])
     - Grid tem dimensoes 10x8
   - **Densidade:**
     - Numero de objetos entre 12 e 16 (testar com multiplas seeds, todas dentro do range)
   - **Zonas de spawn:**
     - Nenhum objeto nas colunas 0-1 (verificar todas posicoes de spawn Team A)
     - Nenhum objeto nas colunas 8-9 (verificar todas posicoes de spawn Team B)
   - **Semi-simetria:**
     - Para cada objeto em (x, y), verificar que existe um objeto proximo de (9-x, y) (dentro de tolerancia de 1 tile) OU que o total de pares espelhados e > 50% dos objetos
   - **Garantias estruturais:**
     - Pelo menos 2 objetos com blocks_movement=True nas colunas 3-6
     - Pelo menos 1 row (0-7) onde nenhuma posicao (col 2-7) tem objeto com blocks_movement=True
   - **Pool do bioma:**
     - VILLAGE: todos objetos sao CRATE, BARREL, ROCK, ou BUSH
     - FOREST_DAY: todos objetos sao TREE, BUSH, ROCK, ou PUDDLE
     - SWAMP: todos objetos sao PUDDLE, BUSH, ou TREE
     - FOREST_NIGHT: mesmo pool que FOREST_DAY
   - **Validade:**
     - Nao ha dois MapObjects na mesma posicao
     - Todos entity_ids sao unicos
     - Cada MapObject tem Occupant correspondente no grid
   - **Determinismo:**
     - generate_map com mesma seed produz mesma lista de objetos (mesmas posicoes e tipos)
     - Seeds diferentes produzem mapas diferentes

2. Rodar `pytest engine/tests/test_map_generator.py` e confirmar que todos os testes falham.

**Parar apos criar os testes. Nao implementar logica de producao. Aguardar aprovacao do usuario.**

---

### Grupo 2 — Implementacao (um agente)

**Tarefa:** Implementar a geracao procedural de mapas. Todos os testes do Grupo 1 devem passar ao final.

1. Criar `engine/generation/map_generator.py`:
   - `class Biome(Enum)`: FOREST_DAY, FOREST_NIGHT, VILLAGE, SWAMP
   - `_BIOME_POOLS: dict[Biome, list[ObjectType]]`:
     - FOREST_DAY: [TREE, BUSH, ROCK, PUDDLE]
     - FOREST_NIGHT: [TREE, BUSH, ROCK, PUDDLE]
     - VILLAGE: [CRATE, BARREL, ROCK, BUSH]
     - SWAMP: [PUDDLE, BUSH, TREE]
   - `generate_map(biome: Biome, rng: random.Random) -> tuple[Grid, list[MapObject]]`:
     - Algoritmo:
       1. Determinar quantidade de objetos: rng.randint(12, 16)
       2. Gerar metade dos objetos no lado esquerdo (colunas 2-4)
       3. Espelhar para o lado direito (colunas 5-7) com pequena variacao via rng
       4. Validar spawn zones (cols 0-1 e 8-9 livres)
       5. Garantir min 2 objetos blocks_movement nas colunas centrais (3-6)
       6. Garantir min 1 row com corredor aberto (cols 2-7 sem blocks_movement)
       7. Criar Grid, colocar Occupants, criar MapObjects
       8. Retornar (grid, list[MapObject])
     - Cada objeto: escolher ObjectType do pool do bioma via rng.choice
     - Entity IDs: "obj_{index}" (0-indexed, unico)
     - Occupant: entity_id, OccupantType.OBJECT, blocks_movement do template

2. Atualizar `engine/generation/__init__.py`:
   - Adicionar: `from engine.generation.map_generator import Biome, generate_map`
   - Adicionar `__all__`

3. Rodar `pytest engine/tests/test_map_generator.py -v` e confirmar que todos os testes passam.

4. Rodar `pytest engine/tests/ -v` para garantir zero regressoes.

---

## Condicao de Conclusao

- Todos os criterios de aceitacao do spec.md satisfeitos
- Todos os testes passam com `pytest engine/tests/ -v`
- Atualizar `.specs/state.md`: status da feature 12 de `pendente` para `concluida`
