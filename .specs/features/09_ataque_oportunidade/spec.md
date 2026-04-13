# Feature 09 — Ataque de Oportunidade

## Objetivo

Implementar a deteccao de ataques de oportunidade quando um personagem se move para fora do alcance corpo a corpo de um inimigo. A funcao recebe a posicao atual, o destino, e retorna a lista de inimigos que podem realizar ataques de oportunidade gratuitos (ataque basico, sem custo de PA). Esta feature completa as regras de movimentacao tatica — posicionamento e comprometimento tem consequencias reais.

---

## Referencia nos Specs

- prd.md: secao 2.4 (ataque de oportunidade — regras, multiplos inimigos, desengajamento)
- design.md: secoes 2.4 (ataque de oportunidade — regras detalhadas), 3.11 (ataque de oportunidade — pipeline de dano, habilidades que nao provocam)

---

## Arquivos Envolvidos

### Criar

- `engine/systems/opportunity.py` — get_opportunity_attackers()
- `engine/tests/test_opportunity.py` — testes unitarios do sistema de ataque de oportunidade

### Modificar

- `engine/systems/__init__.py` — re-exportar get_opportunity_attackers

---

## Criterios de Aceitacao

### Deteccao de Ataques de Oportunidade

- [ ] `get_opportunity_attackers(grid, mover_position, destination, mover_team)` retorna lista de tuplas (entity_id, position) dos inimigos que podem atacar
- [ ] Inimigo adjacente ao mover na posicao inicial e NAO adjacente no destino → incluido na lista (provoca ataque de oportunidade)
- [ ] Inimigo adjacente ao mover na posicao inicial E adjacente no destino → NAO incluido (mover permanece no alcance)
- [ ] Inimigo NAO adjacente ao mover na posicao inicial → NAO incluido (nunca esteve no alcance)
- [ ] Adjacencia inclui diagonais (8 tiles ao redor, conforme Grid.get_adjacent_positions)

### Multiplos Inimigos

- [ ] Mover adjacente a 2 inimigos, ambos perdem adjacencia no destino → lista retorna 2 atacantes (prd.md 2.4: "cada um realiza seu ataque de oportunidade")
- [ ] Mover adjacente a 2 inimigos, apenas 1 perde adjacencia → lista retorna 1 atacante
- [ ] Mover sem inimigos adjacentes → lista vazia

### Filtragem por Time

- [ ] Apenas personagens do time oposto provocam ataque de oportunidade — aliados adjacentes nunca sao incluidos
- [ ] Objetos (OccupantType.OBJECT) nao provocam ataques de oportunidade, apenas CHARACTER

### Personagens Validos

- [ ] Apenas CHARACTER do time oposto com ocupacao valida no grid sao considerados

### Casos de Borda

- [ ] Mover na borda do grid com menos de 8 vizinhos: funciona corretamente
- [ ] Mover e destino sao a mesma posicao → lista vazia (sem movimento)
- [ ] Nenhum ocupante no grid alem do mover → lista vazia

---

## Fora do Escopo

- Resolucao do ataque basico (dano, crit, esquiva) — o caller usa o pipeline de dano (feature 04) com BASIC_ATTACKS
- Aplicacao de dano ao HP do mover — feature 08 (apply_damage)
- Cancelamento de movimento se o mover morre — sistema de combate
- Verificacao de `prevents_opportunity_attack` da habilidade — o caller (sistema de combate) decide se chama esta funcao baseado na flag da Ability (feature 06)
- Estado de knockout/morte dos inimigos (filtrar inimigos caidos/mortos que nao podem atacar) — sistema de combate filtra antes de chamar
- Timing "antes do movimento ser concluido" — o caller garante a ordem (checa oportunidade → resolve ataques → executa movimento)
