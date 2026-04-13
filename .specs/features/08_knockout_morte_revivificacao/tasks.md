# Tasks — Feature 08: Knockout, Morte e Revivificacao

## Antes de Comecar

Ler obrigatoriamente antes de escrever qualquer codigo:

- `CLAUDE.md` — stack, estrutura do projeto, convencoes
- `.specs/features/08_knockout_morte_revivificacao/spec.md` — criterios de aceitacao desta feature
- `.specs/design.md` secao 3.9 (knockout e morte — thresholds, sangramento, revivificacao, janela)
- `.specs/prd.md` secao 2.5 (morte, knockout e revivificacao — exemplos numericos)
- `engine/models/character.py` — Character class atual (sera modificado)
- `engine/tests/test_character.py` — testes existentes (nao devem quebrar)

---

## Plano de Execucao

2 grupos sequenciais. Grupo 1 e a fase TDD (testes primeiro). Grupo 2 e a implementacao.

- **Grupo 1**: escrever todos os testes (test_knockout.py). Parar apos criar os testes.
- **Grupo 2**: modificar character.py e __init__.py. Rodar testes para validar.

Dependencia: Grupo 2 so executa apos aprovacao dos testes do Grupo 1.

---

### Grupo 1 — Testes (TDD)

**Tarefa:** Criar testes unitarios para o sistema de knockout, morte e revivificacao. Cobrir todos os criterios de aceitacao do spec.md.

1. Criar `engine/tests/test_knockout.py`:
   - **CharacterState e constantes:**
     - CharacterState tem 3 valores: ACTIVE, KNOCKED_OUT, DEAD
     - DEATH_THRESHOLD == -10
     - BLEED_DAMAGE == 3
     - Character inicia com state == ACTIVE
   - **apply_damage:**
     - Guerreiro (HP=60), damage=10 → HP=50, ACTIVE
     - Guerreiro (HP=60), damage=60 → HP=0, KNOCKED_OUT
     - Guerreiro (HP=60), damage=61 → HP=-1, KNOCKED_OUT
     - Guerreiro (HP=60), damage=70 → HP=-10, KNOCKED_OUT
     - Guerreiro (HP=60), damage=71 → HP=-11, DEAD
     - Mago (HP=25), damage=36 → HP=-11, DEAD
     - DEAD character, damage=10 → HP unchanged, DEAD
     - Retorna CharacterState
   - **apply_healing:**
     - ACTIVE HP=40/60, heal=10 → HP=50, ACTIVE
     - ACTIVE HP=55/60, heal=10 → HP=60 (cap)
     - KNOCKED_OUT HP=-4, heal=15 → HP=11, ACTIVE (revivido)
     - KNOCKED_OUT HP=-9, heal=8 → HP=-1, KNOCKED_OUT
     - KNOCKED_OUT HP=-10, heal=11 → HP=1, ACTIVE
     - KNOCKED_OUT HP=-10, heal=10 → HP=0, KNOCKED_OUT
     - DEAD, heal=20 → HP unchanged, DEAD
     - Retorna CharacterState
   - **process_bleed:**
     - KNOCKED_OUT HP=0, bleed → HP=-3, KNOCKED_OUT, retorna 3
     - KNOCKED_OUT HP=-7, bleed → HP=-10, KNOCKED_OUT, retorna 3
     - KNOCKED_OUT HP=-8, bleed → HP=-11, DEAD, retorna 3
     - ACTIVE, bleed → HP unchanged, retorna 0
     - DEAD, bleed → HP unchanged, retorna 0
   - **Janela de revivificacao (ciclo completo):**
     - HP=0: 3 bleeds sobrevive (0→-3→-6→-9), 4o mata (-9→-12 DEAD)
     - HP=-8: 1 bleed mata (-8→-11 DEAD)
   - **is_knocked_out:**
     - ACTIVE → False
     - KNOCKED_OUT → True
     - DEAD → False

2. Rodar `pytest engine/tests/test_knockout.py` e confirmar que todos os testes falham.

**Parar apos criar os testes. Nao implementar logica de producao. Aguardar aprovacao do usuario.**

---

### Grupo 2 — Implementacao (um agente)

**Tarefa:** Implementar o sistema de knockout no Character. Todos os testes do Grupo 1 devem passar, e os testes existentes de test_character.py nao devem quebrar.

1. Modificar `engine/models/character.py`:
   - Adicionar `class CharacterState(Enum)`: ACTIVE, KNOCKED_OUT, DEAD
   - Adicionar constantes: `DEATH_THRESHOLD = -10`, `BLEED_DAMAGE = 3`
   - Na classe `Character.__init__`: adicionar `self._state = CharacterState.ACTIVE`
   - Adicionar property `state -> CharacterState`: retorna `self._state`
   - Adicionar property `is_knocked_out -> bool`: retorna `self._state == CharacterState.KNOCKED_OUT`
   - Adicionar metodo interno `_update_state(self) -> None`:
     - Se `self._current_hp > 0`: state = ACTIVE
     - Se `0 >= self._current_hp >= DEATH_THRESHOLD`: state = KNOCKED_OUT
     - Se `self._current_hp < DEATH_THRESHOLD`: state = DEAD
   - Adicionar `apply_damage(self, amount: int) -> CharacterState`:
     - Se state == DEAD: retorna DEAD (nao faz nada)
     - `self._current_hp -= amount`
     - `self._update_state()`
     - Retorna `self._state`
   - Adicionar `apply_healing(self, amount: int) -> CharacterState`:
     - Se state == DEAD: retorna DEAD (nao faz nada)
     - `self._current_hp = min(self._current_hp + amount, self._max_hp)`
     - `self._update_state()`
     - Retorna `self._state`
   - Adicionar `process_bleed(self) -> int`:
     - Se state != KNOCKED_OUT: retorna 0
     - `self._current_hp -= BLEED_DAMAGE`
     - `self._update_state()`
     - Retorna `BLEED_DAMAGE`

2. Atualizar `engine/models/__init__.py`:
   - Adicionar imports: `from engine.models.character import BLEED_DAMAGE, DEATH_THRESHOLD, CharacterState`
   - Adicionar ao `__all__`

3. Rodar `pytest engine/tests/test_knockout.py -v` e confirmar que todos os testes passam.

4. Rodar `pytest engine/tests/test_character.py -v` e confirmar que testes existentes nao quebraram.

5. Rodar `pytest engine/tests/ -v` para garantir zero regressoes.

---

## Condicao de Conclusao

- Todos os criterios de aceitacao do spec.md satisfeitos
- Todos os testes passam com `pytest engine/tests/ -v`
- Atualizar `.specs/state.md`: status da feature 08 de `pendente` para `concluida`
