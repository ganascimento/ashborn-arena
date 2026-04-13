# Feature 10 — Objetos Interativos

## Objetivo

Implementar o modelo de objetos interativos do cenario (Caixa, Barril, Arvore, Arbusto, Rocha, Poca d'agua) com suas propriedades (HP, bloqueio de movimento/visao, inflamabilidade, arremessabilidade), operacoes de dano/destruicao, mecanica de fogo (incendiar, dano por turno, destruicao, extinguir) e calculo de distancia de arremesso. Esta feature fornece os objetos que compoem o campo de batalha — features de LoS (11), geracao procedural (12), e o ambiente PettingZoo (13) dependem dela.

---

## Referencia nos Specs

- prd.md: secoes 6.4 (objetos interativos — tabela de propriedades), 6.5 (interacoes com o cenario — arremessar, atacar, fogo, agua/gelo)
- design.md: secao 4.2 (objetos interativos — propriedades, arremesso, ataque, fogo, agua/gelo)

---

## Arquivos Envolvidos

### Criar

- `engine/models/map_object.py` — ObjectType (enum), MapObject (classe com estado), OBJECT_TEMPLATES (constante com propriedades por tipo)
- `engine/tests/test_map_object.py` — testes unitarios dos objetos interativos

### Modificar

- `engine/models/__init__.py` — re-exportar ObjectType, MapObject, OBJECT_TEMPLATES

---

## Criterios de Aceitacao

### Modelo de Tipo

- [ ] `ObjectType` e um enum com 6 valores: CRATE, BARREL, TREE, BUSH, ROCK, PUDDLE
- [ ] `OBJECT_TEMPLATES` mapeia cada ObjectType as suas propriedades conforme prd.md 6.4

### Propriedades por Tipo (prd.md 6.4, design.md 4.2)

- [ ] Caixa: max_hp=10, blocks_movement=True, blocks_los=True, flammable=True, throwable=True
- [ ] Barril: max_hp=12, blocks_movement=True, blocks_los=True, flammable=True, throwable=True
- [ ] Arvore: max_hp=20, blocks_movement=True, blocks_los=True, flammable=True, throwable=False
- [ ] Arbusto: max_hp=5, blocks_movement=False, blocks_los=False, flammable=True, throwable=False
- [ ] Rocha: indestructible (max_hp=None), blocks_movement=True, blocks_los=True, flammable=False, throwable=False
- [ ] Poca: indestructible (max_hp=None), blocks_movement=False, blocks_los=False, flammable=False, throwable=False

### Criacao de Objetos

- [ ] `MapObject.from_type(object_type, entity_id, position)` cria objeto com propriedades corretas do template
- [ ] MapObject criado tem current_hp == max_hp (ou None para indestrutiveis)
- [ ] MapObject inicia com on_fire=False, fire_turns_remaining=0, is_destroyed=False

### Dano e Destruicao (prd.md 6.5 — atacar objeto)

- [ ] `apply_damage(amount)` reduz current_hp — Caixa HP=10, damage=5 → HP=5
- [ ] Caixa HP=10, damage=10 → HP=0, is_destroyed=True
- [ ] Caixa HP=10, damage=15 → HP=-5, is_destroyed=True (overkill)
- [ ] Objeto indestructivel (Rocha, Poca): apply_damage nao faz nada, retorna False
- [ ] Objeto ja destruido: apply_damage nao faz nada
- [ ] apply_damage retorna True se o objeto foi destruido nesta chamada, False caso contrario

### Fogo (prd.md 6.5, design.md 4.2)

- [ ] `ignite()` em objeto inflamavel → on_fire=True, fire_turns_remaining=3, retorna True
- [ ] `ignite()` em objeto nao inflamavel (Rocha, Poca) → retorna False, sem alteracao
- [ ] `ignite()` em objeto ja em chamas → retorna False (nao reseta duracao)
- [ ] `ignite()` em objeto destruido → retorna False
- [ ] `process_fire_tick()` em objeto em chamas: decrementa fire_turns_remaining, retorna fire_damage=3
- [ ] process_fire_tick com fire_turns_remaining=1 → fire_turns=0, objeto destruido (is_destroyed=True), retorna fire_damage=3
- [ ] process_fire_tick com fire_turns_remaining=3 → fire_turns=2, nao destruido, retorna 3
- [ ] process_fire_tick em objeto nao em chamas → retorna 0
- [ ] `FIRE_DAMAGE = 3` (constante — dano por turno a adjacentes)
- [ ] `FIRE_DURATION = 3` (constante — turnos de fogo antes de destruicao)

### Extinguir Fogo (prd.md 6.5 — agua/gelo apaga fogo)

- [ ] `extinguish()` em objeto em chamas → on_fire=False, fire_turns_remaining=0, retorna True
- [ ] HP do objeto mantem valor atual apos extinguir (dano acumulado persiste)
- [ ] `extinguish()` em objeto nao em chamas → retorna False
- [ ] Objeto extinguido pode ser incendiado novamente (ignite retorna True)

### Arremesso (prd.md 6.5, design.md 4.2)

- [ ] `throw_distance(str_modifier)` retorna max(1, 2 + str_modifier) — conforme design.md 4.2
- [ ] throw_distance(str_modifier=3) retorna 5 (2 + 3)
- [ ] throw_distance(str_modifier=0) retorna 2
- [ ] throw_distance(str_modifier=-3) retorna 1 (minimo 1)
- [ ] `THROW_PA_COST = 2` (constante)
- [ ] `THROW_DAMAGE_BASE = 6`, `THROW_DAMAGE_SCALING = 1.0` (constantes para dano de arremesso)
- [ ] Apenas objetos com throwable=True podem ser arremessados

### Integracao com Grid

- [ ] MapObject armazena position (Position) — posicao atual no grid
- [ ] MapObject armazena entity_id (str) — para corresponder ao Occupant no grid

---

## Fora do Escopo

- Linha de visao (LoS) e verificacao de bloqueio visual — feature 11 (blocks_los esta definido aqui, a logica de LoS nao)
- Geracao procedural de mapas e posicionamento de objetos — feature 12
- Biomas e pools de objetos — feature 12
- Resolucao do dano de arremesso pelo pipeline (caller usa THROW_DAMAGE_BASE/SCALING com resolve_physical_attack) — sistema de combate
- Remocao do Occupant do Grid quando objeto e destruido — sistema de combate (caller chama grid.remove_occupant)
- Aplicacao de dano de fogo a personagens adjacentes — sistema de combate (caller itera adjacentes e aplica FIRE_DAMAGE)
- Incendiar objetos automaticamente ao serem atingidos por habilidades de fogo — sistema de combate
- Poca d'agua apagando fogo adjacente — sistema de combate (checa proximidade a pocas)
