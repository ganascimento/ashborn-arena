# Tasks — Feature 17: API REST

## Antes de Comecar

Leitura obrigatoria antes de escrever qualquer codigo:

- `CLAUDE.md` — convencoes, estrutura do projeto, dependencias entre pacotes
- `.specs/features/17_api_rest/spec.md` — criterios de aceitacao desta feature
- `.specs/design.md` secao 6.1-6.2 — arquitetura e protocolo REST
- `.specs/prd.md` secoes 2.1 (composicao de times), 3.2 (sistema de habilidades), 5.4 (build), 7.3-7.4 (fluxo e builds pre-definidos)
- `engine/models/character.py` — CharacterClass, Attributes, BASE_ATTRIBUTES, BASE_HP
- `engine/models/ability.py` — Ability, ABILITIES, BASIC_ATTACKS, AbilityTarget
- `engine/models/map_object.py` — MapObject, ObjectType, OBJECT_TEMPLATES
- `engine/models/grid.py` — Grid, Team
- `engine/systems/battle.py` — BattleState, BattleState.from_config, _DEFAULT_ABILITIES
- `backend/main.py` — FastAPI app atual

---

## Plano de Execucao

```
Grupo 1 (TDD) ─── sequencial (pausa obrigatoria)
       │
       ▼
Grupo 2 ──┬── paralelo
Grupo 3 ──┘
       │
       ▼
Grupo 4 ─── sequencial (depende de 2 + 3)
```

- **Grupo 1**: Escrever todos os testes. Parar e aguardar aprovacao.
- **Grupo 2** e **Grupo 3**: Rodam em paralelo apos aprovacao dos testes.
- **Grupo 4**: Depende de Grupo 2 (schemas) e Grupo 3 (sessoes + engine). Roda por ultimo.

---

### Grupo 1 — Testes (TDD) (um agente)

**Tarefa:** Escrever os testes dos endpoints REST usando FastAPI TestClient. Nao implementar producao.

1. Criar `backend/tests/__init__.py` (vazio se nao existir).

2. Criar `backend/tests/test_api_rest.py` com os seguintes testes:

   **GET /builds/defaults:**
   - `test_builds_defaults_returns_200` — status 200, response tem `classes` (lista de 5) e `default_builds` (lista de 5)
   - `test_builds_defaults_classes_have_correct_attributes` — cada classe tem `class_id`, `base_attributes`, `hp_base`, `abilities` (lista de 11 items)
   - `test_builds_defaults_warrior_values` — Guerreiro: base_attributes = {str: 8, dex: 4, con: 7, int_: 2, wis: 4}, hp_base = 50
   - `test_builds_defaults_ability_fields` — cada ability tem no minimo: id, name, pa_cost, cooldown, max_range, target
   - `test_builds_defaults_build_points_sum_10` — cada default build tem attribute_points que soma 10, cada valor entre 0 e 5
   - `test_builds_defaults_build_ability_ids_valid` — cada default build tem 5 ability_ids, todos presentes na lista de abilities da respectiva classe

   **POST /battle/start — sucesso:**
   - `test_battle_start_valid_request` — request com 1 personagem valido retorna 201, response tem session_id (UUID valido) e initial_state
   - `test_battle_start_3v3` — request com 3 personagens retorna 201, initial_state tem 6 characters (3 player + 3 ai)
   - `test_battle_start_initial_state_structure` — initial_state tem grid_size, map_objects, characters, turn_order, current_character
   - `test_battle_start_characters_have_correct_fields` — cada character em initial_state.characters tem: entity_id, team, class_id, attributes, current_hp, max_hp, position, abilities
   - `test_battle_start_turn_order_includes_all` — turn_order contem todos entity_ids dos characters

   **POST /battle/start — validacao:**
   - `test_battle_start_empty_team` — team vazio retorna 422
   - `test_battle_start_team_too_large` — team com 4 personagens retorna 422
   - `test_battle_start_duplicate_classes` — dois Guerreiros no team retorna 422
   - `test_battle_start_invalid_build_sum` — attribute_points somando 11 retorna 422
   - `test_battle_start_invalid_build_cap` — attribute_points com valor 6 retorna 422
   - `test_battle_start_invalid_build_negative` — attribute_points com valor negativo retorna 422
   - `test_battle_start_invalid_ability` — ability_id que nao pertence a classe retorna 422
   - `test_battle_start_duplicate_abilities` — ability_ids com duplicata retorna 422
   - `test_battle_start_wrong_ability_count` — menos ou mais de 5 abilities retorna 422
   - `test_battle_start_invalid_difficulty` — difficulty "impossible" retorna 422
   - `test_battle_start_invalid_class` — class_id "necromancer" retorna 422

3. Todos os testes usam `from fastapi.testclient import TestClient` com a app do `backend.main`.

4. **Parar aqui.** Nao implementar codigo de producao. Aguardar aprovacao dos testes.

---

### Grupo 2 — Schemas Pydantic (um agente)

**Tarefa:** Criar todos os schemas Pydantic para request/response dos endpoints REST.

1. Criar `backend/api/schemas/builds.py`:

   ```python
   class AbilityOut(BaseModel):
       id: str
       name: str
       pa_cost: int
       cooldown: int
       max_range: int
       target: str          # AbilityTarget.value
       damage_base: int
       damage_type: str     # "physical", "magical", ""
       heal_base: int
       elemental_tag: str
   ```

   ```python
   class ClassInfo(BaseModel):
       class_id: str        # CharacterClass.value ("warrior", "mage", ...)
       base_attributes: dict[str, int]  # {"str": 8, "dex": 4, "con": 7, "int_": 2, "wis": 4}
       hp_base: int
       abilities: list[AbilityOut]  # 11 abilities disponiveis
   ```

   ```python
   class DefaultBuild(BaseModel):
       class_id: str
       attribute_points: list[int]  # [FOR, DES, CON, INT, SAB], soma=10
       ability_ids: list[str]       # 5 ability IDs
   ```

   ```python
   class BuildsDefaultsResponse(BaseModel):
       classes: list[ClassInfo]
       default_builds: list[DefaultBuild]
   ```

   Funcao helper `ability_to_out(ability: Ability) -> AbilityOut` que converte engine Ability para AbilityOut.

   Funcao helper `get_class_abilities(char_class: CharacterClass) -> list[AbilityOut]` que filtra ABILITIES por classe e retorna lista de AbilityOut.

2. Criar `backend/api/schemas/battle.py`:

   ```python
   class CharacterRequest(BaseModel):
       class_id: str
       attribute_points: list[int]  # [FOR, DES, CON, INT, SAB]
       ability_ids: list[str]       # 5 ability IDs

   class BattleStartRequest(BaseModel):
       difficulty: str   # "easy", "normal", "hard"
       team: list[CharacterRequest]  # 1-3 personagens
   ```

   ```python
   class PositionOut(BaseModel):
       x: int
       y: int

   class CharacterOut(BaseModel):
       entity_id: str
       team: str           # "player" ou "ai"
       class_id: str       # CharacterClass.value
       attributes: dict[str, int]  # atributos finais
       current_hp: int
       max_hp: int
       position: PositionOut
       abilities: list[AbilityOut]  # basic_attack + 5 equipped

   class MapObjectOut(BaseModel):
       entity_id: str
       object_type: str    # ObjectType.value
       position: PositionOut
       hp: int | None      # None para indestrutiveis (rocha, poca)
       max_hp: int | None
       blocks_movement: bool
       blocks_los: bool

   class InitialBattleState(BaseModel):
       grid_size: dict[str, int]  # {"width": 10, "height": 8}
       map_objects: list[MapObjectOut]
       characters: list[CharacterOut]
       turn_order: list[str]
       current_character: str

   class BattleStartResponse(BaseModel):
       session_id: str
       initial_state: InitialBattleState
   ```

3. Atualizar `backend/api/schemas/__init__.py` — re-exportar todos os schemas publicos.

---

### Grupo 3 — Sessoes e extensao do engine (um agente)

**Tarefa:** Criar o gerenciador de sessoes em memoria e estender BattleState.from_config para aceitar habilidades customizadas.

1. Criar `backend/sessions.py`:

   ```python
   @dataclass
   class BattleSession:
       session_id: str
       battle_state: BattleState
       difficulty: str
       player_entity_ids: list[str]
       ai_entity_ids: list[str]

   class SessionManager:
       def __init__(self):
           self._sessions: dict[str, BattleSession] = {}

       def create(self, battle_state, difficulty, player_ids, ai_ids) -> BattleSession:
           # Gera UUID, armazena, retorna sessao

       def get(self, session_id: str) -> BattleSession | None:
           # Retorna sessao ou None

       def remove(self, session_id: str) -> None:
           # Remove sessao
   ```

   Instanciar um `session_manager` singleton no modulo (variavel de modulo).

2. Estender `BattleState.from_config` em `engine/systems/battle.py`:

   Adicionar parametros opcionais para habilidades customizadas:

   ```python
   @classmethod
   def from_config(
       cls,
       team_a_config: list[tuple[CharacterClass, tuple[int, ...]]],
       team_b_config: list[tuple[CharacterClass, tuple[int, ...]]],
       biome: Biome | None = None,
       rng: _random.Random | None = None,
       team_a_abilities: list[list[str]] | None = None,
       team_b_abilities: list[list[str]] | None = None,
   ) -> BattleState:
   ```

   - Se `team_a_abilities` e None, usa `_DEFAULT_ABILITIES` (comportamento atual).
   - Se fornecido, `team_a_abilities[i]` e lista de 5 ability IDs para o i-th personagem.
   - Mesma logica para `team_b_abilities`.
   - Linha que muda (para team_a):
     ```python
     # Antes:
     equipped[eid] = [ABILITIES[aid] for aid in _DEFAULT_ABILITIES[cls_type]]
     # Depois:
     ability_ids = team_a_abilities[i] if team_a_abilities else _DEFAULT_ABILITIES[cls_type]
     equipped[eid] = [ABILITIES[aid] for aid in ability_ids]
     ```
   - Mesma alteracao para team_b com `team_b_abilities`.

3. Verificar que testes existentes do engine continuam passando (a mudanca e backward-compatible).

---

### Grupo 4 — Rotas e registro (um agente)

**Tarefa:** Implementar os endpoints REST e registrar os routers no FastAPI app.

1. Criar `backend/api/routes/builds.py`:

   - Router FastAPI com prefix="/builds".
   - `GET /defaults` → `BuildsDefaultsResponse`:
     - Iterar sobre as 5 CharacterClass
     - Para cada classe: extrair base_attributes de BASE_ATTRIBUTES, hp_base de BASE_HP, filtrar abilities de ABILITIES onde `cls_type in ability.classes`
     - Montar default_builds com os builds de prd.md 7.4:
       ```python
       DEFAULT_BUILDS = {
           CharacterClass.WARRIOR: ([5, 2, 3, 0, 0], _DEFAULT_ABILITIES[CharacterClass.WARRIOR]),
           CharacterClass.MAGE: ([0, 0, 2, 5, 3], _DEFAULT_ABILITIES[CharacterClass.MAGE]),
           CharacterClass.CLERIC: ([0, 0, 5, 0, 5], _DEFAULT_ABILITIES[CharacterClass.CLERIC]),
           CharacterClass.ARCHER: ([2, 5, 3, 0, 0], _DEFAULT_ABILITIES[CharacterClass.ARCHER]),
           CharacterClass.ASSASSIN: ([3, 5, 2, 0, 0], _DEFAULT_ABILITIES[CharacterClass.ASSASSIN]),
       }
       ```
     - Incluir basic_attack na lista de abilities de cada ClassInfo? Nao — basic attack e automatico, nao faz parte das 11 selecionaveis. So incluir as 11 de ABILITIES.
     - Incluir basic_attack na lista de abilities de cada CharacterOut no initial_state? Sim — o frontend precisa saber o basic attack do personagem.

2. Criar `backend/api/routes/battle.py`:

   - Router FastAPI com prefix="/battle".
   - `POST /start` → `BattleStartResponse`:
     - Validar request (ver criterios):
       - `len(team)` entre 1 e 3
       - Classes nao duplicadas
       - Para cada personagem: attribute_points soma 10, cada 0-5, 5 ability_ids validos e sem duplicata
       - difficulty in ("easy", "normal", "hard")
       - Retornar HTTPException(422) com mensagem descritiva se qualquer validacao falhar
     - Gerar time IA:
       - Mesma quantidade de personagens que o jogador
       - Classes aleatorias sem duplicar (e sem duplicar com si mesmo)
       - Builds default (attribute_points e abilities de DEFAULT_BUILDS)
     - Montar configs para BattleState.from_config:
       - team_a_config = [(CharacterClass(cr.class_id), tuple(cr.attribute_points)) for cr in request.team]
       - team_a_abilities = [cr.ability_ids for cr in request.team]
       - team_b_config = [(cls, DEFAULT_BUILDS[cls][0]) for cls in ai_classes]
       - team_b_abilities = None (usa default)
     - Criar BattleState via `BattleState.from_config(...)`
     - Criar BattleSession via session_manager.create(...)
     - Serializar BattleState para InitialBattleState:
       - grid_size: {"width": 10, "height": 8}
       - characters: iterar sobre battle_state._characters, mapear para CharacterOut com team="player" ou "ai" baseado em player_entity_ids
       - map_objects: iterar sobre battle_state._map_objects, mapear para MapObjectOut
       - turn_order: battle_state.turn_order
       - current_character: battle_state.current_agent
     - Retornar BattleStartResponse com status 201

3. Atualizar `backend/api/routes/__init__.py` — re-exportar routers.

4. Atualizar `backend/main.py`:
   - Importar routers de builds e battle
   - `app.include_router(builds_router)`
   - `app.include_router(battle_router)`
   - Adicionar `CORSMiddleware` com `allow_origins=["*"]`, `allow_methods=["*"]`, `allow_headers=["*"]`

5. Rodar todos os testes: `pytest backend/tests/test_api_rest.py -v`. Todos devem passar.

---

## Condicao de Conclusao

- Todos os criterios de aceitacao em spec.md satisfeitos.
- Todos os testes passam com `pytest backend/tests/ -v`.
- Testes existentes do engine continuam passando: `pytest engine/tests/ -v`.
- Atualizar `.specs/state.md`: status da feature 17 para `concluida`.
