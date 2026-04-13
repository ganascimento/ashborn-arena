# Feature 13 — Ambiente PettingZoo

## Objetivo

Implementar o ambiente PettingZoo (AEC API) que encapsula o motor de combate completo para treinamento RL multi-agente. Inclui o orquestrador de batalha (BattleState) que gerencia o ciclo de turnos, resolucao de habilidades, aplicacao de dano/cura/efeitos, e condicao de vitoria; e o wrapper PettingZoo que codifica observacoes (~160 valores), espaco de acoes (tipo + alvo), mascara de acoes invalidas, e funcao de recompensa. Esta feature e o ponto de integracao entre o game engine (features 01-12) e o sistema de RL (features 14-15).

---

## Referencia nos Specs

- prd.md: secoes 4.1 (abordagem IA — PettingZoo, CTDE), 4.3 (observacao do agente), 4.4 (espaco de acoes — micro-decisoes), 4.5 (funcao de recompensa), 2.2-2.5 (regras de turno, knockout)
- design.md: secoes 5.2 (representacao do estado — dimensoes da observacao), 5.3 (espaco de acoes — tipo + alvo + mascara), 5.4 (pipeline de treinamento — fases), 3.7 (pipeline de resolucao de dano), 1.4 (timing de efeitos)
- .specs/notes.md: edge cases de TurnManager, BuffDef scaling, atributo dual INT/SAB

---

## Arquivos Envolvidos

### Criar

- `engine/systems/battle.py` — BattleState (orquestrador de combate: setup, execute_action, process_turn_start/end, check_victory)
- `training/environment/arena_env.py` — ArenaEnv (PettingZoo AEC environment wrapper)
- `training/environment/observations.py` — encode_observation(), encode_global_state()
- `training/environment/actions.py` — ActionType (enum), decode_action(), compute_action_mask()
- `training/environment/rewards.py` — compute_rewards()
- `engine/tests/test_battle.py` — testes do orquestrador de combate
- `training/tests/test_arena_env.py` — testes do ambiente PettingZoo

### Modificar

- `engine/systems/__init__.py` — re-exportar BattleState
- `training/environment/__init__.py` — re-exportar ArenaEnv

---

## Criterios de Aceitacao

### BattleState — Setup

- [ ] `BattleState(team_a, team_b, grid, map_objects, effect_manager, rng)` cria estado de batalha com todos os subsistemas
- [ ] `BattleState.from_config(team_a_builds, team_b_builds, biome, rng)` cria batalha completa: gera mapa, cria Characters, posiciona nas spawn zones, rola iniciativa, inicializa TurnManager
- [ ] Personagens posicionados nas spawn zones: Team A colunas 0-1, Team B colunas 8-9
- [ ] Turno inicia com o personagem de maior iniciativa (conforme feature 02)

### BattleState — Ciclo de Turno

- [ ] `current_agent` retorna entity_id do personagem ativo
- [ ] Inicio do turno: `process_turn_start()` decrementa buffs/debuffs (EffectManager), PA=4
- [ ] Se personagem ativo esta KNOCKED_OUT: aplica sangramento (3 HP), checa morte, avanca para proximo
- [ ] Se personagem ativo esta DEAD: avanca para proximo (ja removido)
- [ ] Fim do turno: `process_turn_end()` aplica DOTs/HOTs, checa knockouts/mortes resultantes

### BattleState — Execucao de Acoes

- [ ] `execute_action(action_type, target)` executa uma micro-decisao e retorna resultado
- [ ] MOVE: calcula tiles por PA disponivel, executa execute_move, gasta PA (1 PA por 2 tiles), checa ataques de oportunidade (get_opportunity_attackers)
- [ ] BASIC_ATTACK: resolve via damage pipeline (resolve_physical_attack/resolve_magical_attack conforme classe), aplica dano ao alvo, gasta PA=2
- [ ] ABILITY (slots 1-5): resolve habilidade do catalogo — dano direto, DOT, cura, buff/debuff, controle, self-heal, movimento, shield. Gasta PA e set cooldown
- [ ] THROW: verifica objeto adjacente arremessavel, calcula throw_distance, resolve dano (base 6, FOR*1.0), destroi objeto, gasta PA=2
- [ ] END_TURN: encerra turno voluntariamente, descarta PA restante
- [ ] Acoes de oportunidade resolvidas automaticamente quando MOVE provoca (ataque basico gratuito dos inimigos adjacentes)
- [ ] Apos cada acao que causa dano: checa knockout/morte do alvo. Se morto, remove do TurnManager (checando vitoria ANTES — conforme notes.md)

### BattleState — Resolucao de Habilidades

- [ ] Habilidades com dano direto: usa calculate_raw_damage(base, modifier, scaling) com o atributo correto do personagem
- [ ] Habilidades dual-attribute (Chama Sagrada, Barreira Arcana): usa INT para Mago, SAB para Clerigo (conforme notes.md)
- [ ] Habilidades com BuffDef: computa valor final via calculate_raw_damage quando BuffDef tem scaling (ex: Consagracao HOT valor = calculate_raw_damage(5, sab_mod, 0.5) — conforme notes.md)
- [ ] Combos elementais: checa check_elemental_combo antes de aplicar defesas, aplica damage_modifier ao dano bruto
- [ ] Crit bonus de habilidade (Tiro Certeiro +15%): adiciona ao crit_chance base do atacante
- [ ] Execute bonus (Sentenca do Carrasco): se alvo abaixo de threshold% HP, aplica bonus% ao dano
- [ ] Debuff bonus (Lamina Oculta): se alvo tem status negativo (has_negative_status), aplica bonus% ao dano
- [ ] Lifesteal (Sifao Vital): cura o atacante em lifesteal_pct% do dano causado

### BattleState — Condicao de Vitoria

- [ ] Batalha termina quando todos os personagens de um time estao DEAD (nao KNOCKED_OUT — caidos contam como vivos)
- [ ] `check_victory()` retorna None (em andamento), "team_a" ou "team_b"

### Observacao (design.md 5.2)

- [ ] `encode_observation(battle_state, agent_id)` retorna np.ndarray float32 com ~160 valores
- [ ] Self (~22): classe one-hot (5), HP ratio (1), PA normalizado (1), posicao normalizada (2), cooldowns normalizados (5), modificadores de atributo normalizados (5), status flags (3)
- [ ] Aliados (2 slots x ~12): classe one-hot (5), HP ratio (1), posicao (2), status flags (3), presente flag (1). Masked (zeros) se ausente
- [ ] Inimigos (3 slots x ~12): mesma estrutura. Masked se ausente
- [ ] Mapa (80): grid 10x8 flattened, encoding tipo de objeto por tile (0=vazio, 1-6=tipos, +flag fogo)
- [ ] `encode_global_state(battle_state)` retorna estado completo para o critic (todas observacoes + info oculta)

### Espaco de Acoes (design.md 5.3)

- [ ] Action space: MultiDiscrete([10, 80]) — tipo (10) + alvo/tile (80)
- [ ] Tipos: 0=mover, 1=ataque_basico, 2-6=habilidade_1..5, 7=arremessar, 8=encerrar_turno, 9=passar
- [ ] Alvo: indice de tile (row * 10 + col) para mover/AoE/arremessar; tile do alvo para ataques direcionados

### Mascara de Acoes (design.md 5.3)

- [ ] `compute_action_mask(battle_state, agent_id)` retorna dict com type_mask (10,) e target_mask (10, 80)
- [ ] Mover: masked se PA < 1, target masked se tile nao alcancavel (get_reachable_tiles)
- [ ] Ataque basico: masked se PA < 2, target masked se fora de alcance ou sem LoS (ranged)
- [ ] Habilidade N: masked se PA insuficiente OU em cooldown, target masked conforme alcance/LoS/tipo de alvo
- [ ] Arremessar: masked se PA < 2 ou nenhum objeto adjacente arremessavel
- [ ] Encerrar turno: sempre disponivel
- [ ] Personagem knocked_out ou frozen: todas acoes masked exceto encerrar_turno

### Funcao de Recompensa (prd.md 4.5)

- [ ] Vitoria: +10 para todos do time vencedor
- [ ] Derrota: -10 para todos do time perdedor
- [ ] Matar inimigo: +3 para o agente
- [ ] Derrubar inimigo (caido): +1 para o agente
- [ ] Aliado morto: -2 para todos do time
- [ ] Dano causado: +0.1 por ponto de dano
- [ ] Cura realizada: +0.1 por ponto curado
- [ ] Combo elemental ativado: +0.5 para o agente

### PettingZoo AEC API

- [ ] `ArenaEnv` implementa PettingZoo AECEnv: reset(), step(action), observe(agent), agent_selection, agents, rewards, terminations, truncations, infos
- [ ] `reset(seed, options)` cria nova batalha (biome aleatoria, builds configurados, mapa gerado)
- [ ] `step(action)` executa micro-decisao para o agente atual, avanca estado
- [ ] `observe(agent)` retorna observacao local do agente
- [ ] `infos[agent]` contem action_mask para o agente
- [ ] Apos termination de todos agentes, env esta done
- [ ] Ambiente suporta 1v1, 2v2 e 3v3 (configuravel via options)

---

## Fora do Escopo

- Redes neurais (policy, critic) — feature 14
- Loop de treinamento MAPPO e self-play — feature 15
- Curriculum learning (fases 1v1→3v3) — feature 15
- Mecanicas complexas de habilidades nao cobertas pelo engine (Meteoro delayed, Armadilha, Voto de Sacrificio redirecionamento, Retribuicao Divina reflexao, Veu das Sombras untargetable) — implementar versoes simplificadas ou ignorar no MVP do ambiente, refinar pos-treinamento
- API REST/WebSocket — features 16-17
- Frontend — features 19-23
