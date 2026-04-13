# Feature 12 — Geracao Procedural de Mapas

## Objetivo

Implementar a geracao procedural de mapas de batalha com objetos interativos posicionados de acordo com o bioma selecionado. O gerador produz mapas semi-simetricos (espelhados no eixo central com variacoes), respeita zonas de spawn livres, garante cobertura minima no centro e pelo menos um corredor aberto para linha de visao. Cada batalha usa um mapa unico gerado a partir de uma seed. Esta feature completa o campo de batalha — o ambiente PettingZoo (feature 13) depende dela para gerar cenarios de treinamento.

---

## Referencia nos Specs

- prd.md: secoes 6.7 (biomas — pools de objetos por bioma), 6.8 (geracao procedural — simetria, densidade, spawn, garantias)
- design.md: secoes 4.4 (geracao procedural — regras, densidade, garantias), 4.5 (biomas — pools e tendencias)

---

## Arquivos Envolvidos

### Criar

- `engine/generation/map_generator.py` — Biome (enum), generate_map(), BiomeConfig
- `engine/generation/__init__.py` — re-exportar Biome, generate_map
- `engine/tests/test_map_generator.py` — testes unitarios da geracao procedural

### Modificar

- (nenhum arquivo existente modificado)

---

## Criterios de Aceitacao

### Biomas

- [ ] `Biome` e um enum com 4 valores: FOREST_DAY, FOREST_NIGHT, VILLAGE, SWAMP
- [ ] Cada bioma define um pool de ObjectTypes permitidos conforme prd.md 6.7:
  - Floresta (dia/noite): TREE, BUSH, ROCK, PUDDLE
  - Vila: CRATE, BARREL, ROCK, BUSH
  - Pantano: PUDDLE, BUSH, TREE

### Geracao de Mapa

- [ ] `generate_map(biome, rng)` retorna um Grid populado com Occupants + lista de MapObjects
- [ ] Aceita parametro `rng: random.Random` para resultados deterministicos (mesma seed = mesmo mapa)
- [ ] Grid gerado tem dimensoes 10x8 (Grid padrao)

### Densidade (prd.md 6.8, design.md 4.4)

- [ ] Mapa gerado contem entre 12 e 16 objetos (inclusive)
- [ ] Cobertura aproximada de 15-20% dos tiles (12-16 de 80 tiles)

### Zonas de Spawn (prd.md 6.8, design.md 4.4)

- [ ] Colunas 0-1 (spawn Time A) nao contem objetos
- [ ] Colunas 8-9 (spawn Time B) nao contem objetos
- [ ] Objetos so podem ser colocados nas colunas 2-7 (6 colunas centrais)

### Semi-simetria (prd.md 6.8, design.md 4.4)

- [ ] Mapa e aproximadamente espelhado no eixo central (entre colunas 4 e 5): objeto em (x, y) tem correspondente em (9-x, y) com pequena variacao
- [ ] Variacao permitida: nem todo objeto precisa ter espelho exato (semi-simetrico, nao perfeitamente simetrico)

### Garantias Estruturais (prd.md 6.8, design.md 4.4)

- [ ] Minimo 2 objetos com blocks_movement=True nas colunas centrais (3-6) — garantia de cobertura no meio
- [ ] Minimo 1 linha (row) com corredor aberto de coluna 2 a coluna 7 sem objetos com blocks_movement=True — garantia de LoS

### Validade dos Objetos

- [ ] Todos os objetos gerados pertencem ao pool do bioma selecionado
- [ ] Nao ha dois objetos na mesma posicao
- [ ] Cada MapObject tem entity_id unico
- [ ] Cada MapObject no grid tem um Occupant correspondente na mesma posicao com blocks_movement correto

### Determinismo

- [ ] `generate_map(Biome.VILLAGE, Random(42))` produz exatamente o mesmo mapa se chamado duas vezes
- [ ] Seeds diferentes produzem mapas diferentes (com alta probabilidade)

---

## Fora do Escopo

- Efeitos visuais ou variantes de bioma alem do pool de objetos (Floresta dia vs noite e so visual — mesmo pool mecanico) — frontend
- Colocacao de personagens nas zonas de spawn — sistema de combate
- Validacao de LoS do corredor aberto (feature 11 fornece has_line_of_sight, esta feature garante a existencia do corredor) — o corredor garante que a LoS e possivel, nao verifica com has_line_of_sight
- Balanceamento fino da distribuicao de objetos por bioma (ajustes de peso/probabilidade sao iterativos) — pode ser refinado pos-treinamento
