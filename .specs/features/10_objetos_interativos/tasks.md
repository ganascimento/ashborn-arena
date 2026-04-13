# Tasks — Feature 10: Objetos Interativos

## Antes de Comecar

Ler obrigatoriamente antes de escrever qualquer codigo:

- `CLAUDE.md` — stack, estrutura do projeto, convencoes
- `.specs/features/10_objetos_interativos/spec.md` — criterios de aceitacao desta feature
- `.specs/design.md` secao 4.2 (objetos interativos — propriedades, arremesso, fogo, agua/gelo)
- `.specs/prd.md` secoes 6.4 (objetos interativos — tabela), 6.5 (interacoes com o cenario)
- `engine/models/grid.py` — Occupant, OccupantType (referencia de como objetos sao colocados no grid)
- `engine/models/position.py` — Position

---

## Plano de Execucao

2 grupos sequenciais. Grupo 1 e a fase TDD (testes primeiro). Grupo 2 e a implementacao.

- **Grupo 1**: escrever todos os testes (test_map_object.py). Parar apos criar os testes.
- **Grupo 2**: implementar (map_object.py + atualizar __init__.py). Rodar testes para validar.

Dependencia: Grupo 2 so executa apos aprovacao dos testes do Grupo 1.

---

### Grupo 1 — Testes (TDD)

**Tarefa:** Criar testes unitarios para os objetos interativos. Cobrir todos os criterios de aceitacao do spec.md.

1. Criar `engine/tests/test_map_object.py`:
   - **ObjectType:**
     - ObjectType tem 6 valores: CRATE, BARREL, TREE, BUSH, ROCK, PUDDLE
   - **OBJECT_TEMPLATES — propriedades por tipo (prd.md 6.4):**
     - CRATE: max_hp=10, blocks_movement=True, blocks_los=True, flammable=True, throwable=True
     - BARREL: max_hp=12, blocks_movement=True, blocks_los=True, flammable=True, throwable=True
     - TREE: max_hp=20, blocks_movement=True, blocks_los=True, flammable=True, throwable=False
     - BUSH: max_hp=5, blocks_movement=False, blocks_los=False, flammable=True, throwable=False
     - ROCK: max_hp=None, blocks_movement=True, blocks_los=True, flammable=False, throwable=False
     - PUDDLE: max_hp=None, blocks_movement=False, blocks_los=False, flammable=False, throwable=False
   - **Criacao:**
     - MapObject.from_type(CRATE, "crate_1", Position(3,3)) → current_hp=10, on_fire=False, is_destroyed=False
     - Indestructible (ROCK): current_hp=None
   - **Dano e destruicao:**
     - Caixa HP=10, damage=5 → HP=5, not destroyed, returns False
     - Caixa HP=10, damage=10 → HP=0, is_destroyed=True, returns True
     - Caixa HP=10, damage=15 → is_destroyed=True
     - Rocha: apply_damage(10) → nada muda, returns False
     - Objeto destruido: apply_damage(5) → nada muda
   - **Fogo:**
     - Caixa ignite → on_fire=True, fire_turns=3, returns True
     - Rocha ignite → returns False, on_fire=False
     - Caixa ja em chamas ignite → returns False
     - Caixa destruida ignite → returns False
     - Caixa em chamas process_fire_tick (fire_turns=3) → fire_turns=2, returns 3, not destroyed
     - Caixa em chamas process_fire_tick (fire_turns=1) → fire_turns=0, returns 3, is_destroyed=True
     - Caixa nao em chamas process_fire_tick → returns 0
     - FIRE_DAMAGE == 3, FIRE_DURATION == 3
   - **Extinguir:**
     - Caixa em chamas extinguish → on_fire=False, fire_turns=0, returns True, HP mantido
     - Caixa nao em chamas extinguish → returns False
     - Caixa extinguida pode ser incendiada novamente (ignite returns True)
   - **Arremesso:**
     - throw_distance(3) == 5
     - throw_distance(0) == 2
     - throw_distance(-3) == 1
     - THROW_PA_COST == 2, THROW_DAMAGE_BASE == 6, THROW_DAMAGE_SCALING == 1.0

2. Rodar `pytest engine/tests/test_map_object.py` e confirmar que todos os testes falham.

**Parar apos criar os testes. Nao implementar logica de producao. Aguardar aprovacao do usuario.**

---

### Grupo 2 — Implementacao (um agente)

**Tarefa:** Implementar o modelo de objetos interativos. Todos os testes do Grupo 1 devem passar ao final.

1. Criar `engine/models/map_object.py`:
   - Constantes:
     - `FIRE_DAMAGE = 3`
     - `FIRE_DURATION = 3`
     - `THROW_PA_COST = 2`
     - `THROW_DAMAGE_BASE = 6`
     - `THROW_DAMAGE_SCALING = 1.0`
   - `class ObjectType(Enum)`: CRATE, BARREL, TREE, BUSH, ROCK, PUDDLE
   - `@dataclass(frozen=True) ObjectTemplate`:
     - max_hp: int | None (None = indestructible)
     - blocks_movement: bool
     - blocks_los: bool
     - flammable: bool
     - throwable: bool
   - `OBJECT_TEMPLATES: dict[ObjectType, ObjectTemplate]` com os 6 tipos conforme prd.md 6.4
   - `class MapObject`:
     - `__init__(self, entity_id, object_type, position, template)`:
       - Armazena entity_id, object_type, position
       - max_hp, current_hp = template.max_hp (ou None)
       - blocks_movement, blocks_los, flammable, throwable = do template
       - on_fire = False, fire_turns_remaining = 0, _is_destroyed = False
     - `@classmethod from_type(cls, object_type, entity_id, position) -> MapObject`:
       - Busca template em OBJECT_TEMPLATES, cria MapObject
     - Properties: entity_id, object_type, position, max_hp, current_hp, blocks_movement, blocks_los, flammable, throwable, on_fire, fire_turns_remaining, is_destroyed
     - `apply_damage(self, amount: int) -> bool`:
       - Se indestructible ou destroyed: retorna False
       - current_hp -= amount
       - Se current_hp <= 0: _is_destroyed = True, retorna True
       - Retorna False
     - `ignite(self) -> bool`:
       - Se nao flammable, destroyed, ou ja on_fire: retorna False
       - on_fire = True, fire_turns_remaining = FIRE_DURATION
       - Retorna True
     - `extinguish(self) -> bool`:
       - Se nao on_fire: retorna False
       - on_fire = False, fire_turns_remaining = 0
       - Retorna True
     - `process_fire_tick(self) -> int`:
       - Se nao on_fire: retorna 0
       - fire_turns_remaining -= 1
       - Se fire_turns_remaining <= 0: _is_destroyed = True, on_fire = False
       - Retorna FIRE_DAMAGE
   - `def throw_distance(str_modifier: int) -> int`:
     - Retorna `max(1, 2 + str_modifier)`

2. Atualizar `engine/models/__init__.py`:
   - Adicionar imports: `from engine.models.map_object import FIRE_DAMAGE, FIRE_DURATION, OBJECT_TEMPLATES, THROW_DAMAGE_BASE, THROW_DAMAGE_SCALING, THROW_PA_COST, MapObject, ObjectType, throw_distance`
   - Adicionar ao `__all__`

3. Rodar `pytest engine/tests/test_map_object.py -v` e confirmar que todos os testes passam.

4. Rodar `pytest engine/tests/ -v` para garantir zero regressoes.

---

## Condicao de Conclusao

- Todos os criterios de aceitacao do spec.md satisfeitos
- Todos os testes passam com `pytest engine/tests/ -v`
- Atualizar `.specs/state.md`: status da feature 10 de `pendente` para `concluida`
