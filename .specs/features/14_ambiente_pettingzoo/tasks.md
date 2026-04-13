# Tasks — Feature 13: Ambiente PettingZoo

## Antes de Comecar

Ler obrigatoriamente antes de escrever qualquer codigo:

- `CLAUDE.md` — stack, estrutura do projeto, convencoes
- `.specs/features/13_ambiente_pettingzoo/spec.md` — criterios de aceitacao desta feature
- `.specs/notes.md` — edge cases: TurnManager.remove_entity no ultimo, BuffDef scaling, atributo dual INT/SAB
- `.specs/design.md` secoes 5.1-5.5 (sistema de IA — redes, observacao, acoes, treinamento, modelos)
- `.specs/prd.md` secoes 4.1-4.7 (IA multi-agente — observacao, acoes, recompensa, curriculum)
- `engine/systems/` — todos os sistemas (damage, movement, turn_manager, effect_manager, elemental, opportunity, line_of_sight)
- `engine/models/` — todos os modelos (character, ability, effect, grid, map_object, position)
- `engine/generation/map_generator.py` — geracao de mapas

---

## Plano de Execucao

3 grupos sequenciais. Grupo 1 e a fase TDD. Grupo 2 implementa BattleState (orquestrador de combate no engine). Grupo 3 implementa o wrapper PettingZoo (observacao, acoes, recompensa).

- **Grupo 1**: testes para BattleState e ArenaEnv. Parar apos criar os testes.
- **Grupo 2**: implementar BattleState em engine/systems/battle.py. Rodar testes.
- **Grupo 3**: implementar ArenaEnv e modulos auxiliares em training/environment/. Rodar testes.

Dependencia: Grupo 2 depende da aprovacao do Grupo 1. Grupo 3 depende do Grupo 2.

---

### Grupo 1 — Testes (TDD)

**Tarefa:** Criar testes para o orquestrador de combate e o ambiente PettingZoo.

1. Criar `engine/tests/test_battle.py`:
   - **Setup:**
     - BattleState.from_config cria batalha 1v1 com personagens posicionados nas spawn zones
     - current_agent retorna entity_id do primeiro personagem (maior iniciativa)
     - Personagens iniciam com HP correto (formula feature 03)
   - **Ciclo de turno:**
     - process_turn_start seta PA=4, decrementa buffs
     - Personagem knocked_out: sangra 3 HP, pula turno
     - process_turn_end aplica DOTs
   - **Acoes basicas:**
     - MOVE: personagem se move, PA gasto (1 PA = 2 tiles)
     - BASIC_ATTACK: resolve dano (pipeline fisico/magico), PA gasto
     - END_TURN: avanca para proximo personagem
   - **Habilidades:**
     - Habilidade com dano direto (Impacto Brutal): dano correto, PA gasto, cooldown setado
     - Habilidade com DOT (Corte Profundo): dano + efeito bleed aplicado
     - Habilidade de cura (Toque da Aurora): HP restaurado, cap em max_hp
     - Habilidade com buff (Muralha de Ferro): efeito damage_reduction aplicado
   - **Knockout e morte:**
     - Dano que leva HP a 0: personagem fica KNOCKED_OUT
     - Dano que leva HP abaixo de -10: personagem DEAD
     - Personagem DEAD removido do TurnManager
   - **Vitoria:**
     - check_victory retorna None durante batalha
     - check_victory retorna "team_a" quando todos de team_b estao DEAD

2. Criar `training/tests/test_arena_env.py`:
   - **PettingZoo API:**
     - ArenaEnv reseta corretamente (reset retorna observacoes)
     - step(action) executa e avanca o ambiente
     - observe(agent) retorna np.ndarray com shape correto (~160,)
     - agents lista diminui conforme personagens morrem
   - **Observacao:**
     - Self observation tem shape correto e valores normalizados [0,1]
     - Mapa encoding: tile vazio = 0, tile com objeto = valor correspondente
   - **Action mask:**
     - Mascara de tipo: habilidade em cooldown mascarada
     - Mascara de tipo: PA insuficiente mascarado
     - Encerrar turno sempre disponivel
   - **Recompensa:**
     - Dano causado gera +0.1 por ponto
     - Vitoria gera +10
     - Derrota gera -10
   - **Terminacao:**
     - Ambiente termina quando check_victory retorna resultado

3. Rodar testes e confirmar que todos falham.

**Parar apos criar os testes. Nao implementar logica de producao. Aguardar aprovacao do usuario.**

---

### Grupo 2 — BattleState (um agente)

**Tarefa:** Implementar o orquestrador de combate que integra todos os sistemas do engine.

1. Criar `engine/systems/battle.py`:
   - Constantes: `ACTION_MOVE = 0, ACTION_BASIC = 1, ACTION_ABILITY_1..5 = 2..6, ACTION_THROW = 7, ACTION_END_TURN = 8, ACTION_PASS = 9`
   - Classe `BattleState`:
     - `__init__(self, characters, grid, map_objects, turn_manager, effect_manager, rng)`:
       - Armazena todos subsistemas
       - `_characters: dict[str, Character]` — entity_id → Character
       - `_positions: dict[str, Position]` — entity_id → posicao atual
       - `_teams: dict[str, Team]` — entity_id → time
       - `_builds: dict[str, tuple[Ability, ...]]` — entity_id → 5 habilidades equipadas
       - `_basic_attacks: dict[str, Ability]` — entity_id → ataque basico da classe
       - `_map_objects: dict[str, MapObject]` — entity_id → objeto
     - `@classmethod from_config(cls, team_a_config, team_b_config, biome, rng) -> BattleState`:
       - Gera mapa (generate_map)
       - Cria Characters com Attributes (base + build)
       - Posiciona nas spawn zones
       - Rola iniciativa (determine_turn_order)
       - Cria TurnManager e EffectManager
     - Properties: `current_agent`, `current_round`, `is_over`, `winner`
     - `get_character(entity_id)`, `get_position(entity_id)`, `get_team(entity_id)`
     - `process_turn_start() -> list[dict]`:
       - Se knocked_out: process_bleed, se morreu → remove_dead, avanca turno, retorna events
       - Se frozen (CONTROL freeze): avanca turno, retorna events
       - EffectManager.process_turn_start → decrementar buffs/debuffs
       - TurnManager → PA = 4
     - `process_turn_end() -> list[dict]`:
       - EffectManager.process_turn_end → DOTs/HOTs tick
       - Aplicar dano/cura dos ticks ao HP dos personagens
       - Checar knockouts/mortes
       - TurnManager.end_turn → avanca personagem
     - `execute_action(action_type: int, target: int) -> list[dict]`:
       - Dispatch para metodos internos baseado no tipo
       - Retorna lista de eventos (para observabilidade)
     - Metodos internos:
       - `_execute_move(target_tile)`: calcula PA, checa oportunidade, move
       - `_execute_basic_attack(target_tile)`: resolve pipeline de dano
       - `_execute_ability(slot, target_tile)`: resolve habilidade completa
       - `_execute_throw(target_tile)`: arremessa objeto
       - `_execute_end_turn()`: encerra turno
       - `_resolve_damage(attacker, target, ability)`: pipeline completo com elemental, execute, debuff bonus, etc.
       - `_apply_ability_effects(attacker, target, ability)`: aplica DOTs, buffs, controles
       - `_remove_dead(entity_id)`: remove do grid, turn_manager, marca como morto
       - `_check_and_handle_death(entity_id)`: checa HP, transiciona estado, remove se morto
     - `check_victory() -> str | None`

2. Atualizar `engine/systems/__init__.py`:
   - Adicionar: `from engine.systems.battle import BattleState`
   - Adicionar ao `__all__`

3. Rodar `pytest engine/tests/test_battle.py -v`.

---

### Grupo 3 — ArenaEnv e modulos auxiliares (um agente)

**Tarefa:** Implementar o wrapper PettingZoo e modulos de observacao, acao e recompensa.

1. Criar `training/environment/observations.py`:
   - `OBS_SELF_SIZE = 22` (classe 5 + HP 1 + PA 1 + pos 2 + cooldowns 5 + attrs 5 + status 3)
   - `OBS_ENTITY_SIZE = 12` (classe 5 + HP 1 + pos 2 + status 3 + presente 1)
   - `OBS_MAP_SIZE = 80`
   - `OBS_TOTAL_SIZE = OBS_SELF_SIZE + 2*OBS_ENTITY_SIZE + 3*OBS_ENTITY_SIZE + OBS_MAP_SIZE` (~162)
   - `encode_observation(battle_state, agent_id) -> np.ndarray`:
     - Normaliza HP como ratio (current/max), PA como ratio (current/4), posicao (x/9, y/7)
     - Cooldowns normalizados (current/max_cd ou 0)
     - Status flags: is_knocked_out, has_negative_status, has_buff (binarios)
     - Aliados/inimigos: sorted por distancia ou fixed order, zeros se ausente
     - Mapa: 0=empty, 1-6=ObjectType.value, +10 se on_fire
   - `encode_global_state(battle_state) -> np.ndarray`: concatena todas observacoes + info extra

2. Criar `training/environment/actions.py`:
   - `NUM_ACTION_TYPES = 10`
   - `NUM_TARGETS = 80`
   - `class ActionType(IntEnum)`: MOVE=0, BASIC_ATTACK=1, ABILITY_1..5=2..6, THROW=7, END_TURN=8, PASS=9
   - `decode_action(action_type, target, battle_state) -> tuple[int, Position | str]`:
     - Converte target index em Position (row, col) ou entity_id
   - `compute_action_mask(battle_state, agent_id) -> dict`:
     - `type_mask: np.ndarray (10,)` — bool, True=valido
     - `target_mask: np.ndarray (10, 80)` — bool
     - PA check, cooldown check, range check (get_reachable_tiles para move), LoS check (has_line_of_sight para ranged)

3. Criar `training/environment/rewards.py`:
   - Constantes: REWARD_VICTORY=10, REWARD_DEFEAT=-10, REWARD_KILL=3, REWARD_KNOCKDOWN=1, REWARD_ALLY_DEAD=-2, REWARD_DAMAGE=0.1, REWARD_HEAL=0.1, REWARD_COMBO=0.5
   - `compute_rewards(events, battle_state, agent_teams) -> dict[str, float]`:
     - Processa lista de eventos retornados por execute_action
     - Calcula recompensa por agente

4. Criar `training/environment/arena_env.py`:
   - `class ArenaEnv(pettingzoo.AECEnv)`:
     - `__init__(self, team_size=3, biome=None)`: configuracao
     - `reset(seed, options)`: cria BattleState.from_config, popula agents, reseta rewards/terminations
     - `step(action)`: decode action, execute via BattleState, compute rewards, advance agent
     - `observe(agent)`: encode_observation
     - `observation_space(agent)`: Box(low=0, high=1, shape=(OBS_TOTAL_SIZE,))
     - `action_space(agent)`: MultiDiscrete([10, 80])
     - `action_mask`: via infos dict
     - Gerencia ciclo: quando PA=0 → process_turn_end → process_turn_start do proximo → verifica se pode agir

5. Atualizar `training/environment/__init__.py`:
   - `from training.environment.arena_env import ArenaEnv`

6. Rodar `pytest training/tests/test_arena_env.py -v`.

7. Rodar `pytest engine/tests/ training/tests/ -v` para garantir zero regressoes.

---

## Condicao de Conclusao

- Todos os criterios de aceitacao do spec.md satisfeitos
- Todos os testes passam com `pytest engine/tests/ training/tests/ -v`
- Atualizar `.specs/state.md`: status da feature 13 de `pendente` para `concluida`
- Atualizar `.specs/notes.md` com edge cases descobertos durante implementacao
