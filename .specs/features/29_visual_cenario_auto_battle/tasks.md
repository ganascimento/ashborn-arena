# Tasks — Feature 29: Visual, Cenario e Auto-Battle

## Antes de Comecar

Leitura obrigatoria antes de implementar:

- `CLAUDE.md` — convencoes, stack, estrutura
- `.specs/features/29_visual_cenario_auto_battle/spec.md` — criterios de aceitacao
- `.specs/prd.md` secao 6.4-6.8 — objetos, LoS, biomas, geracao
- `.specs/design.md` secao 4.2-4.5 — specs tecnicas de mapa e cenario
- `engine/systems/battle.py` — BattleState, execute_action, pipeline de dano
- `engine/systems/line_of_sight.py` — has_line_of_sight, get_tiles_in_line
- `frontend/src/scenes/BattleScene.ts` — cena principal, rendering, WS handlers
- `frontend/src/scenes/battle-animations.ts` — pipeline de animacao

---

## Plano de Execucao

Feature grande, 4 grupos. Grupos A/B sao independentes (paralelizaveis). Grupo C depende de A (engine). Grupo D e independente.

---

### Grupo A — Interceptacao de Projeteis (engine)

**Tarefa 1: `find_first_blocker` em line_of_sight.py**

1. Adicionar funcao `find_first_blocker(origin, target, blocking_positions) -> Position | None`
   - Reutiliza `get_tiles_in_line` existente
   - Retorna a posicao do primeiro tile bloqueante no caminho, ou None

**Tarefa 2: Metodos auxiliares em battle.py**

1. Adicionar `_find_object_at(pos: Position) -> MapObject | None`
   - Percorre `_map_objects`, retorna primeiro objeto nao destruido na posicao
2. Adicionar `_apply_ability_damage_to_object(attacker_id, ability, obj) -> int`
   - Calcula dano via `calculate_raw_damage` (sem esquiva/bloqueio)
   - Chama `obj.apply_damage(raw_damage)`
   - Se destruido, remove occupant do grid
   - Emite evento `object_hit` com campos: type, ability, attacker, object, position, damage, destroyed

**Tarefa 3: Interceptacao em `_execute_basic_attack`**

1. Para ataques ranged (`max_range > 1`):
   - Chamar `find_first_blocker` entre atacante e alvo
   - Se ha blocker: verificar se ha objeto na posicao do blocker
     - Se sim: gastar PA, aplicar dano ao objeto via `_apply_ability_damage_to_object`, return
   - Se nao ha blocker e alvo e personagem: pipeline normal
   - Se nao ha blocker e alvo e objeto: PA gasto, dano aplicado ao objeto
2. Melee (`max_range <= 1`): sem mudanca (ignora LoS)

**Tarefa 4: Interceptacao em `_execute_ability`**

1. Para habilidades com `damage_base > 0`, `max_range > 1`, e `not delayed`:
   - Chamar `find_first_blocker` entre agente e alvo
   - Se ha blocker:
     - Aplicar dano ao objeto
     - Se habilidade e charge (`movement_type == "charge"`):
       - Se objeto destruido: mover personagem para tile do objeto
       - Se objeto sobrevive: mover para tile adjacente (via `_find_adjacent_free`)
       - Emitir evento `ability_movement`
     - Return (nao executa resto da habilidade)
2. Para habilidades single-target sem blocker: se alvo nao e personagem, verificar se e objeto e aplicar dano
3. Habilidades delayed: sem interceptacao (Meteoro ignora LoS)

**Tarefa 5: Testes (test_los_interception.py)**

Suite de testes cobrindo:
- `TestRangedAbilityHitsBlockingObject`: habilidade ranged atinge arvore no caminho, sem blocker atinge alvo, evento emitido, objeto destruido removido do grid, PA/CD gastos
- `TestAoEBlockedByObject`: AoE bloqueada atinge objeto, nao atinge alvos atras
- `TestBasicAttackHitsBlockingObject`: basico ranged atinge arvore, melee ignora LoS, PA gasto
- `TestChargeBlockedByObject`: charge para adjacente a objeto que sobrevive, charge para no tile de objeto destruido, evento de movimento emitido
- `TestMeleeIgnoresLoS`: habilidade melee funciona normalmente
- `TestDelayedAbilityIgnoresLoS`: Meteoro nao interceptado
- `TestDirectObjectTargeting`: melee basico em objeto, ranged basico em objeto, habilidade em objeto, rocha destrutivel

---

### Grupo B — Simplificacao do Mapa (engine, paralelo com A)

**Tarefa 1: Remover Puddle e simplificar ObjectType**

1. Remover `PUDDLE` de `ObjectType` enum
2. Remover template `PUDDLE` de `OBJECT_TEMPLATES`
3. Alterar `ROCK` template: `max_hp=30` (era `None`)
4. Atualizar testes em `test_map_object.py`:
   - 5 tipos (nao 6)
   - Rock com `max_hp=30`, destrutivel
   - Remover teste de Puddle

**Tarefa 2: Simplificar Biomes e Map Generator**

1. Remover `FOREST_NIGHT` e `SWAMP` de `Biome` enum
2. Remover pools correspondentes de `_BIOME_POOLS`
3. Simplificar `generate_map`:
   - `rng` parametro opcional (default `random.Random()`)
   - Placement apenas em cols 2-7, rows 1-6 (bordas livres)
   - Sem semi-simetria (placement direto)
4. Simplificar `_ensure_center_blocking`: recalcular `used` internamente
5. Simplificar `_ensure_open_corridor`: usar `min()` em vez de loop manual, iterar apenas rows internas
6. Atualizar testes em `test_map_generator.py`:
   - 2 biomas
   - Testes parametrizados por bioma
   - Spawn + border zones validadas
   - Remover teste de semi-simetria

---

### Grupo C — Frontend Visual e Object Interaction (depende de A para eventos)

**Tarefa 1: Utilitarios compartilhados (`ui-utils.ts`)**

1. Criar `frontend/src/scenes/ui-utils.ts`:
   - `createParticleTexture(scene, key, radius, color)` — gera textura circular para particulas
   - `drawPanel(scene, x, y, w, h, opts)` — desenha retangulo arredondado com fill e borda

**Tarefa 2: Assets e Config**

1. Adicionar spritesheets: `Outdoor_Decor.png`, `barrels.png`, `Water_Tile_1.png`
2. Renomear `Grass_Tiles_1_Blob.png` para `florest.png`
3. Adicionar `pixelArt: true` na config do Phaser (`main.ts`)

**Tarefa 3: BattleScene — Grid e Objetos**

1. `preload()`: carregar spritesheets (big_oak_tree, barrels, outdoor_decor, forest_floor)
2. `create()`: definir frames customizados (tree_canopy, tree_base, barrel variants, bush, rock)
3. `renderGrid()`: substituir retangulos por tiles do spritesheet com logica de bordas/cantos/miolo; adicionar grid lines sutis
4. `renderMapObjects()`: renderizar cada tipo com sprite correto:
   - Tree: base (depth 2) + canopy (depth 12)
   - Barrel/Crate: sprite com frame aleatorio
   - Bush: sprite de outdoor_decor
   - Rock: sprite de outdoor_decor
   - Fallback: retangulo colorido (tipos desconhecidos)
5. Remover `puddle` do mapa de cores

**Tarefa 4: Animacoes de objetos (`battle-animations.ts`)**

1. `animateObjectHit(sprite)`: tint vermelho por 200ms (Image ou Rectangle)
2. `animateObjectDestroy(sprite, canopy?)`: fade out + destroy ambos
3. Em `processEventsAnimated`: handler para evento `object_hit`:
   - Buscar objeto, animar hit, floating text laranja
   - Se `destroyed`, animar destroy

**Tarefa 5: HUD para objetos (`battle-hud.ts`)**

1. `updateObjectBars(mapObjects, gridToPixel)`: criar/atualizar HP bars sobre objetos com HP
2. Chamar em `refreshHud()`

**Tarefa 6: State tracking (`update-state.ts`)**

1. Aceitar `mapObjects` como parametro
2. Em evento `object_hit`: atualizar `data.hp` do objeto

**Tarefa 7: UI — Menu, Preparacao, Resultado**

1. `MenuScene`: redesign com titulo glow, botoes container, particulas, divisor
2. `PreparationScene`: paineis arredondados, 3 colunas de habilidades, stats compactos, glow no nome de classe
3. `ResultScene`: paineis por time com accent, particulas na vitoria, botao estilizado, dots de status

**Tarefa 8: UI — Batalha (ajustes)**

1. Turn indicator em painel arredondado
2. Combat log com background arredondado
3. Click em personagem no grid abre detail panel (em vez de atacar)
4. Error handling no drain queue (try/catch)

---

### Grupo D — Auto-Battle e Robustez IA (independente)

**Tarefa 1: Backend — Schema e Session**

1. `BattleStartRequest`: adicionar `auto_battle: bool = False`
2. `BattleSession`: adicionar `auto_battle: bool = False`
3. `routes/battle.py`: passar `req.auto_battle` para `session_manager.create`

**Tarefa 2: Backend — WS auto-battle**

1. Em `battle_websocket`: ler `session.auto_battle`
2. Se `auto_battle`, tratar agentes do jogador como IA (`_handle_ai_turn` em vez de `_handle_player_turn`)

**Tarefa 3: Backend — Robustez IA**

1. Extrair `_get_ai_decision` — encapsula inference com fallback para heuristic
2. Retry loop: se acao nao produz efeito (sem eventos, PA inalterado), incrementar counter
   - Apos 5 retries: forcar `end_turn`, logar warning
3. Timeout de 10s no `receive_json` (aguardando `ready`)
   - Se timeout: forcar `end_turn`, logar warning

**Tarefa 4: Frontend — Auto-battle**

1. `api-client.ts`: parametro `autoBattle` em `startBattle()`
2. `PreparationScene`: checkbox "IA joga por mim" com toggle visual
3. `BattleScene`:
   - Receber `auto_battle` no `init()`
   - Desabilitar input (grid clicks, ability bar) quando ativo
   - Turn indicator: "IA vs IA" em vez de "Seu turno"
   - Ocultar ability bar no turno do jogador

---

## Condicao de Conclusao

Todos os criterios de aceitacao em spec.md satisfeitos.
Testes Python passando: `python -m pytest engine/tests/test_los_interception.py engine/tests/test_map_generator.py engine/tests/test_map_object.py -v`
TypeScript compila sem erros: `npx tsc --noEmit`
Atualizar `.specs/state.md`: setar feature 29 para `concluida`.
