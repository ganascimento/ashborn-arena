# Feature 11 — Linha de Visao e Cobertura

## Objetivo

Implementar o sistema de linha de visao (LoS) que determina se um ataque a distancia pode ser realizado entre duas posicoes no grid. O calculo traceja uma linha reta do centro do tile do atacante ao centro do tile do alvo — se qualquer tile intermediario contem um objeto com blocks_los=True, a visao e bloqueada. Corpo a corpo ignora LoS (adjacente = sempre valido). AoE requer LoS ao ponto alvo mas expande normalmente apos isso. Meteoro ignora LoS. Esta feature e essencial para o combate tatico — posicionamento atras de cobertura e uma estrategia central.

---

## Referencia nos Specs

- prd.md: secao 6.6 (linha de visao e cobertura — regras, AoE, Meteoro, corpo a corpo)
- design.md: secao 4.3 (LoS — calculo centro-a-centro, bloqueio, AoE, Meteoro, corpo a corpo)

---

## Arquivos Envolvidos

### Criar

- `engine/systems/line_of_sight.py` — has_line_of_sight(), get_tiles_in_line()
- `engine/tests/test_line_of_sight.py` — testes unitarios do sistema de LoS

### Modificar

- `engine/systems/__init__.py` — re-exportar has_line_of_sight, get_tiles_in_line

---

## Criterios de Aceitacao

### Calculo de LoS

- [ ] `has_line_of_sight(grid, origin, target, objects)` retorna True se nenhum tile intermediario (entre origin e target, exclusive) contem objeto com blocks_los=True
- [ ] `has_line_of_sight` retorna False se qualquer tile intermediario contem objeto com blocks_los=True
- [ ] O calculo usa linha reta centro-a-centro entre tiles (algoritmo de Bresenham ou similar)
- [ ] `get_tiles_in_line(origin, target)` retorna a lista de posicoes intermediarias entre origin e target (exclusive de ambos)

### Linha Reta — Sem Obstrucao

- [ ] Linha horizontal: (0,3) → (5,3), nenhum objeto → has_line_of_sight retorna True
- [ ] Linha vertical: (3,0) → (3,5), nenhum objeto → True
- [ ] Linha diagonal: (0,0) → (4,4), nenhum objeto → True
- [ ] Mesma posicao: (3,3) → (3,3) → True (sem intermediarios)
- [ ] Adjacente: (3,3) → (4,4) → True (sem intermediarios entre adjacentes)

### Bloqueio por Objetos

- [ ] Linha horizontal (0,3) → (5,3), objeto com blocks_los=True em (3,3) → False
- [ ] Linha diagonal (0,0) → (4,4), objeto com blocks_los=True em (2,2) → False
- [ ] Objeto com blocks_los=False (ex: Arbusto) em tile intermediario → True (nao bloqueia)
- [ ] Objeto blocks_los=True no tile do atacante (origin) → nao bloqueia (origin e excluido)
- [ ] Objeto blocks_los=True no tile do alvo (target) → nao bloqueia (target e excluido)
- [ ] Multiplos objetos: 1 blocks_los=True entre eles → False

### Tiles Intermediarios

- [ ] `get_tiles_in_line((0,0), (4,0))` retorna posicoes intermediarias [(1,0), (2,0), (3,0)] (excluindo origin e target)
- [ ] `get_tiles_in_line((0,0), (0,4))` retorna [(0,1), (0,2), (0,3)]
- [ ] `get_tiles_in_line((0,0), (3,3))` retorna posicoes intermediarias na diagonal
- [ ] `get_tiles_in_line((3,3), (3,3))` retorna [] (mesma posicao)
- [ ] `get_tiles_in_line((3,3), (4,4))` retorna [] (adjacentes, sem intermediarios)

### Regras Especiais (informacional — enforced pelo caller)

- [ ] Corpo a corpo (adjacente): has_line_of_sight nao precisa ser chamado — adjacente e sempre valido (design.md 4.3)
- [ ] A funcao aceita um dict/set de posicoes bloqueadoras para facilitar o uso pelo caller

---

## Fora do Escopo

- Decisao de quando LoS e necessario (o caller decide: ranged attacks requerem LoS, melee nao) — sistema de combate
- AoE expansion apos LoS ao centro (o caller verifica LoS ao ponto central, a expansao usa get_reachable_tiles ou similar) — sistema de combate
- Meteoro ignorando LoS (o caller simplesmente nao chama has_line_of_sight para Meteoro) — sistema de combate
- Colocacao de objetos no grid e gerenciamento de blocks_los por MapObject — feature 10 (ja concluida, blocks_los esta no MapObject)
- Geracao procedural de mapas com garantia de corredores abertos — feature 12
