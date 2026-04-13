# Tasks — Feature 03: Atributos, Modificadores e HP

## Antes de Comecar

Ler obrigatoriamente antes de escrever qualquer codigo:

- `CLAUDE.md` — stack, estrutura do projeto, convencoes (ingles, sem docstrings, models separadas de entrypoints)
- `.specs/features/03_atributos_modificadores_hp/spec.md` — criterios de aceitacao desta feature
- `.specs/design.md` secoes 3.1 (atributos primarios), 3.2 (composicao), 3.3 (modificador — fator de corte), 3.8 (formula de HP)
- `.specs/prd.md` secoes 5.1-5.5 (atributos, base por classe, HP, build, modificadores)
- `engine/models/grid.py` — referencia de como models existentes sao estruturadas (dataclass, enum)
- `engine/models/position.py` — referencia de dataclass frozen

---

## Plano de Execucao

2 grupos sequenciais. Grupo 1 e a fase TDD (testes primeiro). Grupo 2 e a implementacao.

- **Grupo 1**: escrever todos os testes (test_character.py). Parar apos criar os testes.
- **Grupo 2**: implementar o codigo de producao (character.py + atualizar __init__.py). Rodar testes para validar.

Dependencia: Grupo 2 so executa apos aprovacao dos testes do Grupo 1.

---

### Grupo 1 — Testes (TDD)

**Tarefa:** Criar testes unitarios para o modelo de personagem. Cobrir todos os criterios de aceitacao do spec.md.

1. Criar `engine/tests/test_character.py`:
   - **CharacterClass:**
     - CharacterClass tem exatamente 5 valores: WARRIOR, MAGE, CLERIC, ARCHER, ASSASSIN
   - **BASE_ATTRIBUTES e BASE_HP:**
     - BASE_ATTRIBUTES[WARRIOR] = Attributes(str=8, dex=4, con=7, int_=2, wis=4)
     - BASE_ATTRIBUTES[MAGE] = Attributes(str=2, dex=4, con=4, int_=9, wis=6)
     - BASE_ATTRIBUTES[CLERIC] = Attributes(str=4, dex=3, con=6, int_=5, wis=8)
     - BASE_ATTRIBUTES[ARCHER] = Attributes(str=3, dex=9, con=4, int_=4, wis=5)
     - BASE_ATTRIBUTES[ASSASSIN] = Attributes(str=5, dex=8, con=3, int_=4, wis=5)
     - BASE_HP[WARRIOR]=50, BASE_HP[MAGE]=30, BASE_HP[CLERIC]=45, BASE_HP[ARCHER]=35, BASE_HP[ASSASSIN]=35
   - **Modificadores (Attributes.modifier):**
     - Guerreiro base: modifier("str")=3, modifier("dex")=-1, modifier("con")=2, modifier("int_")=-3, modifier("wis")=-1
     - Mago base: modifier("str")=-3, modifier("dex")=-1, modifier("con")=-1, modifier("int_")=4, modifier("wis")=1
     - Clerigo base: modifier("str")=-1, modifier("dex")=-2, modifier("con")=1, modifier("int_")=0, modifier("wis")=3
     - Arqueiro base: modifier("str")=-2, modifier("dex")=4, modifier("con")=-1, modifier("int_")=-1, modifier("wis")=0
     - Assassino base: modifier("str")=0, modifier("dex")=3, modifier("con")=-2, modifier("int_")=-1, modifier("wis")=0
   - **Build (Attributes.from_base_and_build):**
     - Build valido (3,2,2,2,1): soma=10, nenhum >5 — cria Attributes corretamente
     - Build valido (5,5,0,0,0): soma=10, nenhum >5 — OK
     - Build valido (2,2,2,2,2): soma=10 — OK
     - Build invalido soma=8 (2,2,2,1,1) levanta ValueError
     - Build invalido soma=12 (3,3,3,2,1) levanta ValueError
     - Build invalido valor=6 (6,1,1,1,1) levanta ValueError
     - Build invalido valor=-1 (-1,3,3,3,2) levanta ValueError
     - Build com atributo resultante: Guerreiro base FOR=8 + build FOR=5 = 13, modifier("str")=8
   - **HP (Character.max_hp):**
     - Guerreiro sem build: HP = 50 + (2*5) = 60
     - Mago sem build: HP = 30 + (-1*5) = 25
     - Clerigo sem build: HP = 45 + (1*5) = 50
     - Arqueiro sem build: HP = 35 + (-1*5) = 30
     - Assassino sem build: HP = 35 + (-2*5) = 25
     - Guerreiro com +5 CON: HP = 50 + (7*5) = 85
     - Mago com +5 CON: HP = 30 + (4*5) = 50
   - **Character:**
     - Character criado com entity_id, character_class, attributes — todos acessiveis
     - current_hp inicia igual a max_hp

2. Rodar `pytest engine/tests/test_character.py` e confirmar que todos os testes falham (import errors — nenhum teste deve passar sem implementacao).

**Parar apos criar os testes. Nao implementar logica de producao. Aguardar aprovacao do usuario.**

---

### Grupo 2 — Implementacao (um agente)

**Tarefa:** Implementar o modelo de personagem. Todos os testes do Grupo 1 devem passar ao final.

1. Criar `engine/models/character.py`:
   - `CharacterClass(Enum)` com valores: WARRIOR, MAGE, CLERIC, ARCHER, ASSASSIN
   - `@dataclass(frozen=True) Attributes`:
     - Campos: `str: int`, `dex: int`, `con: int`, `int_: int`, `wis: int`
     - `modifier(self, attr_name: str) -> int` — retorna `getattr(self, attr_name) - 5`
     - `@staticmethod from_base_and_build(base: Attributes, build: tuple[int, int, int, int, int]) -> Attributes`:
       - Valida: sum(build) == 10, all(0 <= v <= 5 for v in build)
       - Retorna Attributes(base.str + build[0], base.dex + build[1], base.con + build[2], base.int_ + build[3], base.wis + build[4])
   - `BASE_ATTRIBUTES: dict[CharacterClass, Attributes]` — constante com os 5 valores de prd.md 5.2
   - `BASE_HP: dict[CharacterClass, int]` — constante com os 5 valores de prd.md 5.2
   - `Character`:
     - `__init__(self, entity_id: str, character_class: CharacterClass, attributes: Attributes)`:
       - Armazena entity_id, character_class, attributes
       - Calcula max_hp: `BASE_HP[character_class] + (attributes.modifier("con") * 5)`
       - Define current_hp = max_hp
     - Properties: `entity_id`, `character_class`, `attributes`, `max_hp`, `current_hp`

2. Atualizar `engine/models/__init__.py`:
   - Adicionar imports: `from engine.models.character import Attributes, BASE_ATTRIBUTES, BASE_HP, Character, CharacterClass`
   - Adicionar ao `__all__`

3. Rodar `pytest engine/tests/test_character.py -v` e confirmar que todos os testes passam.

4. Rodar `pytest engine/tests/ -v` para garantir que nao ha regressoes.

---

## Condicao de Conclusao

- Todos os criterios de aceitacao do spec.md satisfeitos
- Todos os testes passam com `pytest engine/tests/ -v`
- Atualizar `.specs/state.md`: status da feature 03 de `pendente` para `concluida`
