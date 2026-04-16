# Feature 29 — Visual, Cenario e Auto-Battle

## Objetivo

Conjunto de melhorias que engloba: (A) overhaul visual do frontend — sprites para objetos do mapa, tilemap para o grid, polish de UI em todas as telas; (B) mecanica de interceptacao de projeteis — ataques a distancia bloqueados por objetos atingem o objeto em vez de simplesmente falharem; (C) simplificacao do mapa — remocao de Poca e dos biomas Floresta Noite e Pantano, Rocha agora destrutivel; (D) modo auto-battle — IA joga no lugar do jogador; (E) robustez do turno da IA — retry e timeout.

---

## Referencia nos Specs

- prd.md: secao 6.4-6.8 (objetos, biomas, geracao), secao 7.3 (fluxo do jogador)
- design.md: secao 4.2-4.5 (objetos, LoS, geracao, biomas)

---

## A — Interceptacao de Projeteis (engine)

### Arquivos Envolvidos

| Arquivo | Descricao |
|---|---|
| `engine/systems/line_of_sight.py` | Nova funcao `find_first_blocker` — retorna a posicao do primeiro objeto bloqueante no caminho |
| `engine/systems/battle.py` | Logica de interceptacao em `_execute_basic_attack` e `_execute_ability`; metodos `_find_object_at`, `_apply_ability_damage_to_object` |
| `engine/tests/test_los_interception.py` | Suite completa de testes (novo arquivo) |

### Criterios de Aceitacao

#### Ataque basico ranged

- [ ] Ao atacar um alvo com ataque basico ranged (Mago, Arqueiro), se ha um objeto bloqueante no caminho, o objeto recebe o dano em vez do alvo
- [ ] PA e gasto normalmente quando o projetil atinge o objeto
- [ ] Evento `object_hit` emitido com `attacker`, `object`, `damage`, `destroyed`
- [ ] Se o objeto e destruido pelo ataque, ele e removido do grid
- [ ] Ataque basico melee (alcance 1) ignora LoS — funciona normalmente em adjacencia

#### Habilidades ranged (single target)

- [ ] Habilidades ranged com `damage_base > 0` e `max_range > 1` verificam blocker no caminho
- [ ] Se ha blocker, a habilidade atinge o objeto (dano calculado via pipeline normal, sem esquiva/bloqueio)
- [ ] PA e cooldown sao gastos normalmente
- [ ] Habilidades delayed (Meteoro) ignoram LoS — nao sao interceptadas

#### Habilidades AoE

- [ ] Se o ponto central da AoE nao tem LoS, o objeto bloqueante mais proximo no caminho recebe o dano
- [ ] Alvos atras do blocker nao sao atingidos

#### Investida (charge) bloqueada

- [ ] Se a Investida encontra um objeto no caminho ate o alvo, o objeto recebe o dano da habilidade
- [ ] Se o objeto sobrevive: personagem para adjacente ao objeto (1 tile antes)
- [ ] Se o objeto e destruido: personagem para no tile do objeto destruido
- [ ] Evento `ability_movement` emitido com a posicao final
- [ ] Alvo original nao recebe dano

#### Targeting direto de objetos

- [ ] Ataque basico melee pode mirar diretamente em um tile com objeto (sem personagem)
- [ ] Ataque basico ranged pode mirar diretamente em um tile com objeto (sem bloqueio no caminho)
- [ ] Habilidades podem mirar diretamente em objetos — dano aplicado ao objeto

---

## B — Simplificacao do Mapa (engine)

### Arquivos Envolvidos

| Arquivo | Descricao |
|---|---|
| `engine/models/map_object.py` | Removido `ObjectType.PUDDLE`; `ROCK` agora com `max_hp=30` |
| `engine/generation/map_generator.py` | Removidos biomas `FOREST_NIGHT` e `SWAMP`; simplificacao do gerador (sem semi-simetria, placement em area interna cols 2-7, rows 1-6) |
| `engine/tests/test_map_generator.py` | Testes atualizados para 2 biomas e novas restricoes |
| `engine/tests/test_map_object.py` | Testes atualizados (5 tipos, Rocha destrutivel) |

### Criterios de Aceitacao

- [ ] `ObjectType` tem 5 valores: CRATE, BARREL, TREE, BUSH, ROCK (sem PUDDLE)
- [ ] `ROCK` tem `max_hp=30`, `blocks_movement=True`, `blocks_los=True`, `flammable=False`
- [ ] `Biome` tem 2 valores: FOREST_DAY, VILLAGE
- [ ] Objetos sao posicionados apenas nas colunas 2-7 e linhas 1-6 (bordas e spawn livres)
- [ ] `generate_map` aceita `rng` opcional (default = `random.Random()`)
- [ ] Garantias estruturais mantidas: min 2 blocking no centro, min 1 corredor aberto
- [ ] 12-16 objetos por mapa (mesma faixa)

---

## C — Overhaul Visual do Frontend

### Arquivos Envolvidos

#### Criar

| Arquivo | Descricao |
|---|---|
| `frontend/src/scenes/ui-utils.ts` | Utilitarios compartilhados: `drawPanel` (retangulo arredondado), `createParticleTexture` |
| `frontend/public/assets/spritesheets/Outdoor_Decor.png` | Spritesheet com bush e rock |
| `frontend/public/assets/spritesheets/barrels.png` | Spritesheet com variantes de barril |
| `frontend/public/assets/spritesheets/Water_Tile_1.png` | (asset auxiliar) |

#### Modificar

| Arquivo | Descricao |
|---|---|
| `frontend/src/main.ts` | Adicionado `pixelArt: true` na config do Phaser |
| `frontend/src/scenes/BattleScene.ts` | Grid com tilemap (forest floor), sprites para objetos (arvore com canopy, barril, arbusto, rocha), paineis arredondados, object_hit handling |
| `frontend/src/scenes/MenuScene.ts` | Redesign completo — titulo com glow, botoes com container, particulas douradas, layout dark theme |
| `frontend/src/scenes/PreparationScene.ts` | Paineis arredondados, layout melhorado, habilidades em 3 colunas, stats compactos |
| `frontend/src/scenes/ResultScene.ts` | Paineis arredondados por time, particulas na vitoria, botao estilizado |
| `frontend/src/scenes/battle-animations.ts` | Animacoes para `object_hit` (tint vermelho) e `object_destroyed` (fade + destroy canopy) |
| `frontend/src/scenes/battle-combat-log.ts` | Background arredondado, evento `object_hit` no log |
| `frontend/src/scenes/battle-detail-panel.ts` | Ajuste menor |
| `frontend/src/scenes/battle-hud.ts` | HP bars para objetos do mapa (`updateObjectBars`), status icons ajustados |
| `frontend/src/scenes/update-state.ts` | Tracking de HP de objetos via evento `object_hit` |
| `frontend/public/assets/spritesheets/florest.png` | Renomeado de `Grass_Tiles_1_Blob.png` |

### Criterios de Aceitacao

#### Grid e Tiles

- [ ] Grid renderizado com tilemap (spritesheet `forest_floor`) — bordas e cantos com frames corretos, miolo com frame de terra
- [ ] Phaser configurado com `pixelArt: true` para renderizacao crisp
- [ ] Grid lines sutis (alpha 0.12) sobrepostas ao tilemap

#### Objetos com Sprites

- [ ] Arvores renderizadas com sprite split: base (depth 2) + canopy (depth 12, acima dos personagens)
- [ ] Barris e caixas renderizados com sprites do spritesheet `barrels.png` (frame aleatorio entre 5 variantes)
- [ ] Arbustos renderizados com sprite do `Outdoor_Decor.png`
- [ ] Rochas renderizadas com sprite do `Outdoor_Decor.png`
- [ ] Tipo `puddle` removido do mapa de cores

#### Animacoes de Objetos

- [ ] `object_hit` aplica tint vermelho (200ms) no sprite do objeto; floating text laranja com dano
- [ ] `object_destroyed` faz fade out do sprite + canopy, depois destroy
- [ ] HP bars aparecem sobre objetos que tem HP

#### UI — Menu

- [ ] Titulo "ASHBORN ARENA" com glow dourado e shadow
- [ ] Divisor ornamental com circulo central
- [ ] Botoes de dificuldade em containers com borda, hover com scale e cor
- [ ] Particulas douradas subindo do fundo (blend ADD)
- [ ] Footer com versao

#### UI — Preparacao

- [ ] Paineis arredondados para classe e build
- [ ] Habilidades dispostas em 3 colunas (4 por coluna)
- [ ] Stats compactos (PA:X CD:X R:X D:X H:X)
- [ ] Nome da classe com glow dourado

#### UI — Resultado

- [ ] Titulo com glow (dourado na vitoria, vermelho na derrota)
- [ ] Paineis por time com accent color (azul jogador, vermelho IA)
- [ ] Dot colorido de status por personagem
- [ ] Particulas na vitoria
- [ ] Botao "Voltar ao Menu" estilizado com hover

#### UI — Batalha

- [ ] Turn indicator em painel arredondado (depth 99-100)
- [ ] Combat log com background arredondado
- [ ] Click em tile com personagem abre detail panel em vez de atacar

---

## D — Modo Auto-Battle

### Arquivos Envolvidos

| Arquivo | Descricao |
|---|---|
| `backend/api/schemas/battle.py` | Campo `auto_battle: bool = False` no `BattleStartRequest` |
| `backend/sessions.py` | Campo `auto_battle` no `BattleSession` |
| `backend/api/routes/battle.py` | Passa `auto_battle` para `session_manager.create` |
| `backend/api/routes/ws.py` | Se `auto_battle`, trata jogadores como IA no turno |
| `frontend/src/network/api-client.ts` | Parametro `autoBattle` em `startBattle()` |
| `frontend/src/scenes/PreparationScene.ts` | Checkbox "IA joga por mim" |
| `frontend/src/scenes/BattleScene.ts` | Desabilita input do jogador quando auto_battle ativo |

### Criterios de Aceitacao

- [ ] Checkbox "IA joga por mim" na tela de preparacao (toggle com visual feedback)
- [ ] Quando ativo: `auto_battle: true` enviado no POST `/battle/start`
- [ ] Backend trata personagens do jogador como IA — mesma logica de `_handle_ai_turn`
- [ ] Frontend desabilita clicks no grid, ability bar, e detail panel durante auto-battle
- [ ] Turn indicator mostra "IA vs IA" em vez de "Seu turno"
- [ ] Habilidades e ability bar sao ocultadas no turno do jogador

---

## E — Robustez do Turno da IA (backend)

### Arquivos Envolvidos

| Arquivo | Descricao |
|---|---|
| `backend/api/routes/ws.py` | `_get_ai_decision` com fallback, retry loop, timeout no `receive_json` |

### Criterios de Aceitacao

- [ ] Se inference falha (excecao), cai para heuristic AI com log de warning
- [ ] Se acao da IA nao produz efeito (sem eventos, mesmo PA), incrementa retry counter
- [ ] Apos 5 retries sem efeito, forca `end_turn` e loga warning
- [ ] Timeout de 10s no `receive_json` (aguardando `ready` do client) — se excede, forca `end_turn`
- [ ] Counter de retries reseta apos acao bem-sucedida

---

## Fora do Escopo

- Sistema elemental com agua/gelo (removido junto com Poca, simplificacao deliberada)
- Fog of war ou LoS parcial
- Multiplayer real (auto-battle e IA vs IA local)
- Biomas com efeitos mecanicos
