# Tasks — Feature 02: Sistema de Turnos e PA

## Antes de Comecar

Ler obrigatoriamente antes de escrever qualquer codigo:

- `CLAUDE.md` — stack, estrutura do projeto, convencoes (ingles, sem docstrings, models separadas de entrypoints)
- `.specs/features/02_sistema_turnos_pa/spec.md` — criterios de aceitacao desta feature
- `.specs/design.md` secoes 1.1 (turnos e PA), 1.4 (timing de efeitos), 3.4 (sistema de iniciativa)
- `.specs/prd.md` secoes 2.2 (sistema de turnos), 2.3 (ordem de turnos)
- `engine/systems/movement.py` — referencia de como sistemas existentes sao estruturados (funcoes puras operando sobre Grid)
- `engine/models/grid.py` — referencia de como models existentes sao estruturadas

---

## Plano de Execucao

2 grupos sequenciais. Grupo 1 e a fase TDD (testes primeiro). Grupo 2 e a implementacao.

- **Grupo 1**: escrever todos os testes (test_initiative.py + test_turn_manager.py). Parar apos criar os testes.
- **Grupo 2**: implementar o codigo de producao (initiative.py + turn_manager.py + atualizar __init__.py). Rodar testes para validar.

Dependencia: Grupo 2 so executa apos aprovacao dos testes do Grupo 1.

---

### Grupo 1 — Testes (TDD)

**Tarefa:** Criar testes unitarios para o sistema de iniciativa e o TurnManager. Cobrir todos os criterios de aceitacao do spec.md.

1. Criar `engine/tests/test_initiative.py`:
   - Testar `roll_initiative(dex_modifier=0)` retorna valor entre 1 e 20
   - Testar `roll_initiative(dex_modifier=3)` retorna valor entre 4 e 23
   - Testar `roll_initiative(dex_modifier=-2)` retorna valor entre -1 e 18
   - Testar `roll_initiative` com `rng=Random(seed)` produz resultado deterministico e reproduzivel
   - Testar `determine_turn_order` com 3 participantes de iniciativas diferentes: retorna ordem decrescente
   - Testar desempate por dex_base: dois personagens com mesma iniciativa, maior dex_base age primeiro
   - Testar desempate por sorteio: dois personagens com mesma iniciativa e mesmo dex_base, ordem determinada por rng

2. Criar `engine/tests/test_turn_manager.py`:
   - **Inicializacao:**
     - TurnManager com ["A", "B", "C"] — current_entity e "A", current_round e 1, turn_order e ["A", "B", "C"]
     - TurnManager com lista vazia levanta erro
     - PA do personagem ativo inicia em 4
   - **PA:**
     - spend_pa("A", 2) reduz PA de 4 para 2
     - spend_pa("A", 1) seguido de spend_pa("A", 2) resulta em PA=1
     - spend_pa("A", 5) com PA=4 levanta erro
     - spend_pa("A", 0) levanta erro (cost <= 0)
     - spend_pa("A", -1) levanta erro
     - spend_pa("B", 1) quando turno e de "A" levanta erro
     - can_spend_pa("A", 4) retorna True, can_spend_pa("A", 5) retorna False
     - get_pa("B") retorna 0 (nao e o turno de B)
   - **Cooldowns:**
     - is_ability_ready("A", 0) retorna True para habilidade nunca usada
     - get_cooldown("A", 0) retorna 0 para habilidade nunca usada
     - use_ability("A", 1, 3) define cooldown do slot 1 para 3
     - is_ability_ready("A", 1) retorna False apos use_ability com CD 3
     - use_ability("A", 1, 3) seguido de use_ability("A", 1, 2) levanta erro (ainda em cooldown)
     - use_ability("A", 0, 0) e valido (ataque basico, CD 0)
     - use_ability("B", 1, 3) quando turno e de "A" levanta erro
     - Ciclo completo de cooldown: use_ability com CD 3 no round 1, verificar CD=2 no round 2, CD=1 no round 3, CD=0 no round 4 (pronto)
   - **Fluxo de turnos:**
     - end_turn() com turno de "A" retorna "B"
     - end_turn() de "B" retorna "C"
     - end_turn() de "C" retorna "A" e current_round incrementa para 2
     - PA de "A" e 0 apos end_turn (descartado), PA de "B" e 4 (novo turno)
     - Apos end_turn, cooldowns do novo personagem sao decrementados
   - **Remocao:**
     - remove_entity("B") com turno de "A": "B" sai da ordem, end_turn de "A" retorna "C"
     - remove_entity("A") quando turno e de "A": avanca para "B" (B inicia turno com PA=4)
     - remove_entity com entity_id inexistente levanta erro
     - Ordem com 2 personagens, remover 1: turno continua para o remanescente, round incrementa normalmente

3. Rodar `pytest engine/tests/test_initiative.py engine/tests/test_turn_manager.py` e confirmar que todos os testes falham (import errors ou AssertionError — nenhum teste deve passar sem implementacao).

**Parar apos criar os testes. Nao implementar logica de producao. Aguardar aprovacao do usuario.**

---

### Grupo 2 — Implementacao (um agente)

**Tarefa:** Implementar o sistema de iniciativa e o TurnManager. Todos os testes do Grupo 1 devem passar ao final.

1. Criar `engine/systems/initiative.py`:
   - `roll_initiative(dex_modifier: int, rng: random.Random | None = None) -> int`
     - Rola d20 (1-20) usando `rng.randint(1, 20)` se fornecido, senao `random.randint(1, 20)`
     - Retorna rolar + dex_modifier
   - `determine_turn_order(participants: list[tuple[str, int, int]], rng: random.Random | None = None) -> list[str]`
     - participants: lista de (entity_id, dex_modifier, dex_base)
     - Para cada participante, rola iniciativa via roll_initiative
     - Ordena por: iniciativa decrescente → dex_base decrescente → sorteio via rng
     - Retorna lista de entity_ids na ordem final

2. Criar `engine/systems/turn_manager.py`:
   - Constante `PA_PER_TURN = 4`
   - Classe `TurnManager`:
     - `__init__(self, turn_order: list[str])` — recebe entity_ids ja ordenados por iniciativa. Levanta ValueError se lista vazia. Armazena ordem, inicia turno do primeiro personagem (PA=4, cooldowns iniciais vazios).
     - `current_entity -> str` (property) — retorna entity_id ativo
     - `current_round -> int` (property) — retorna numero do round (inicia em 1)
     - `turn_order -> list[str]` (property) — retorna copia da lista de entity_ids
     - `get_pa(entity_id: str) -> int` — retorna PA restante (0 se nao e o turno do entity)
     - `spend_pa(entity_id: str, cost: int) -> None` — valida: entity_id == current_entity, cost > 0, cost <= PA restante. Reduz PA.
     - `can_spend_pa(entity_id: str, cost: int) -> bool` — retorna True se entity_id e atual e PA >= cost
     - `use_ability(entity_id: str, ability_slot: int, cooldown: int) -> None` — valida: entity_id == current_entity, is_ability_ready. Define cooldown do slot.
     - `is_ability_ready(entity_id: str, ability_slot: int) -> bool` — retorna True se cooldown do slot == 0
     - `get_cooldown(entity_id: str, ability_slot: int) -> int` — retorna cooldown restante (0 se nunca usado)
     - `end_turn() -> str` — descarta PA do atual (set 0), avanca indice (wrap + round increment), inicia turno do proximo (PA=4, decrementa cooldowns do novo personagem). Retorna entity_id do novo personagem ativo.
     - `remove_entity(entity_id: str) -> None` — remove da ordem. Se era o atual, inicia turno do proximo. Levanta erro se entity_id nao existe na ordem.
   - Metodo interno `_start_turn()` — set PA=4 para current_entity, decrementa todos cooldowns do current_entity em 1 (piso 0), remove entradas com cooldown 0 do dict.

3. Atualizar `engine/systems/__init__.py`:
   - Adicionar imports: `from engine.systems.initiative import roll_initiative, determine_turn_order`
   - Adicionar imports: `from engine.systems.turn_manager import TurnManager, PA_PER_TURN`

4. Rodar `pytest engine/tests/test_initiative.py engine/tests/test_turn_manager.py -v` e confirmar que todos os testes passam.

---

## Condicao de Conclusao

- Todos os criterios de aceitacao do spec.md satisfeitos
- Todos os testes passam com `pytest engine/tests/ -v`
- Atualizar `.specs/state.md`: status da feature 02 de `pendente` para `concluida`
