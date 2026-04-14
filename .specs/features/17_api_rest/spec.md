# Feature 17 — API REST

## Objetivo

Implementar os endpoints REST do backend FastAPI que suportam o fluxo pre-batalha: consulta de classes/builds e criacao de sessao de batalha. Esses endpoints sao consumidos pelo frontend (feature 20) na tela de menu e preparacao, e a sessao criada e reutilizada pelo WebSocket (feature 18) durante a batalha.

---

## Referencia nos Specs

- prd.md: secoes 2.1 (composicao de times), 3.2 (sistema de habilidades), 5.4 (build — distribuicao de pontos), 7.1-7.4 (interface, fluxo, builds pre-definidos)
- design.md: secoes 6.1 (arquitetura), 6.2 (protocolo REST)

---

## Arquivos Envolvidos

**Criar:**

- `backend/api/schemas/builds.py` — Schemas Pydantic para GET /builds/defaults
- `backend/api/schemas/battle.py` — Schemas Pydantic para POST /battle/start (request + response)
- `backend/api/routes/builds.py` — Router com endpoint GET /builds/defaults
- `backend/api/routes/battle.py` — Router com endpoint POST /battle/start
- `backend/sessions.py` — Gerenciamento de sessoes de batalha em memoria
- `backend/tests/test_api_rest.py` — Testes dos endpoints REST

**Modificar:**

- `backend/main.py` — Registrar routers de builds e battle
- `backend/api/routes/__init__.py` — Re-exportar routers
- `backend/api/schemas/__init__.py` — Re-exportar schemas

---

## Criterios de Aceitacao

### Schemas

- [ ] Schema `AbilityOut` expoe: id, name, pa_cost, cooldown, max_range, damage_base, damage_type, heal_base, target (AbilityTarget.value), elemental_tag
- [ ] Schema `ClassInfo` expoe: class_id (CharacterClass.value), base_attributes (FOR, DES, CON, INT, SAB), hp_base, abilities (lista de 11 AbilityOut disponiveis para a classe)
- [ ] Schema `DefaultBuild` expoe: class_id, attribute_points (lista de 5 inteiros), ability_ids (lista de 5 strings)
- [ ] Schema `BuildsDefaultsResponse` retorna: classes (lista de 5 ClassInfo), default_builds (lista de 5 DefaultBuild)
- [ ] Schema `CharacterRequest` aceita: class_id (string), attribute_points (lista de 5 inteiros), ability_ids (lista de 5 strings)
- [ ] Schema `BattleStartRequest` aceita: difficulty (string: "easy"/"normal"/"hard"), team (lista de 1-3 CharacterRequest)
- [ ] Schema `BattleStartResponse` retorna: session_id (string UUID), initial_state com grid_size, map_objects, characters (ambos times), turn_order, current_character

### GET /builds/defaults

- [ ] Retorna status 200 com 5 ClassInfo (uma por classe)
- [ ] Cada ClassInfo contem exatamente 11 abilities disponiveis para a classe, extraidas de ABILITIES (engine)
- [ ] Atributos base correspondem a BASE_ATTRIBUTES do engine (ex: Guerreiro FOR=8, DES=4, CON=7, INT=2, SAB=4)
- [ ] HP base corresponde a BASE_HP do engine (ex: Guerreiro=50, Mago=30)
- [ ] Default builds correspondem a prd.md secao 7.4: Guerreiro (5,2,3,0,0), Mago (0,0,2,5,3), Clerigo (0,0,5,0,5), Arqueiro (2,5,3,0,0), Assassino (3,5,2,0,0) — formato: (FOR, DES, CON, INT, SAB)
- [ ] Default ability_ids correspondem a _DEFAULT_ABILITIES de battle.py

### POST /battle/start

- [ ] Request valido com 1-3 personagens retorna 201 com session_id UUID e initial_state
- [ ] Valida que team tem entre 1 e 3 personagens; retorna 422 se vazio ou mais de 3
- [ ] Valida que nao ha classes duplicadas no time; retorna 422 se houver
- [ ] Valida que attribute_points soma 10, cada valor entre 0 e 5; retorna 422 se invalido
- [ ] Valida que cada ability_id pertence a classe do personagem; retorna 422 se invalido
- [ ] Valida que nao ha ability_ids duplicadas para o mesmo personagem; retorna 422 se houver
- [ ] Valida que difficulty e "easy", "normal" ou "hard"; retorna 422 se invalido
- [ ] Gera time IA com mesma quantidade de personagens que o jogador, classes aleatorias sem duplicata, usando builds default
- [ ] Cria BattleState via engine (BattleState.from_config ou construcao equivalente com abilities customizadas)
- [ ] initial_state.characters inclui personagens dos dois times com: id, team ("player"/"ai"), class_id, attributes (final), current_hp, max_hp, position (x,y), abilities (lista de AbilityOut)
- [ ] initial_state.map_objects inclui: id, type (ObjectType.value), position (x,y), hp (ou null para indestrutiveis), blocks_movement, blocks_los
- [ ] initial_state.turn_order e lista de entity_ids na ordem de iniciativa
- [ ] initial_state.current_character e o entity_id de quem age primeiro

### Sessoes

- [ ] Sessao armazenada em memoria (dict) indexada por session_id (UUID string)
- [ ] Sessao contem o BattleState, difficulty, e player_team_ids (para o WebSocket saber quem o jogador controla)
- [ ] Multiplas sessoes podem coexistir independentemente

### Integracao

- [ ] FastAPI app em main.py registra ambos routers com prefixo adequado
- [ ] GET /health continua funcionando
- [ ] CORS habilitado para permitir requests do frontend (origins: ["*"] no MVP)

---

## Fora do Escopo

- WebSocket para batalha em tempo real (feature 18)
- Inference da IA / carregamento de modelos .pt (feature 19)
- Frontend / consumo dos endpoints (feature 20)
- Persistencia em banco de dados (sem banco, tudo em memoria — spec do projeto)
- Autenticacao / sessoes de usuario (spec diz sem auth)
- Logica de turno da IA durante a batalha (feature 18+19)
- Limpeza automatica de sessoes expiradas (pode adicionar depois se necessario)
