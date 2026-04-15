# Feature 22 — Batalha: Acoes e Animacoes

## Objetivo

Adicionar sistema de selecao e uso de habilidades, rastreamento de PA e cooldowns, e animacoes visuais para todas as acoes na cena de batalha. Atualmente (feature 21) o jogador so pode mover, atacar basico por clique, e encerrar turno. Esta feature entrega: barra de habilidades funcional com 6 acoes (ataque basico + 5 habilidades equipadas), modo de targeting para selecionar alvo, animacoes tween para movimentos e efeitos visuais para dano/cura, e processamento sequencial de eventos com fila de animacao que controla o timing do protocolo ready/next. Features 22 e 23 juntas completam a experiencia de batalha — 22 entrega a funcionalidade e o feedback visual basico, 23 adiciona polish (HP bars, status icons, numeros flutuantes, highlights de alcance/AoE).

---

## Referencia nos Specs

- prd.md: secoes 2.2 (PA, cooldowns), 3.2 (ataque basico por classe, alcance), 3.3 (5 habilidades equipadas de 11), 7.3 (fluxo de batalha — acoes do jogador), 7.5 (feedback visual basico)
- design.md: secoes 2.2-2.5 (estrutura de habilidades, ataque basico), 6.2 (protocolo WebSocket — formato de acoes, fluxo ready/next)
- notes.md: "WebSocket — protocolo ready/next", "WebSocket — extensoes ao protocolo de design.md 6.2", "Frontend — processEvents defensivo para field names"

---

## Arquivos Envolvidos

### Criar

| Arquivo | Descricao |
|---|---|
| `frontend/src/scenes/battle-animations.ts` | Classe BattleAnimations: tweens, efeitos visuais, processamento sequencial de eventos |
| `frontend/src/scenes/battle-ability-bar.ts` | Classe BattleAbilityBar: botoes de habilidade, PA counter, cooldowns, targeting state |

### Modificar

| Arquivo | Descricao |
|---|---|
| `frontend/src/scenes/BattleScene.ts` | Integrar BattleAnimations + BattleAbilityBar, processamento async, targeting, rastreamento de estado |

---

## Criterios de Aceitacao

### Barra de Habilidades e PA

- [ ] Painel no lado direito do canvas (x >= 700) exibe as acoes do personagem ativo do jogador
- [ ] Exibe 6 botoes: ataque basico + 5 habilidades equipadas (dados de CharacterOut.abilities do initial_state)
- [ ] Cada botao mostra: nome da habilidade e custo de PA
- [ ] Habilidades em cooldown mostram "CD: X" com turnos restantes
- [ ] Botoes desabilitados (cor cinza #555555) quando: PA insuficiente, habilidade em cooldown, ou nao e turno do jogador
- [ ] Botoes habilitados (cor branca #cccccc) quando: PA suficiente, sem cooldown, e turno do jogador
- [ ] Contador de PA exibe "PA: X / 4" acima dos botoes, atualizado a cada acao
- [ ] Barra atualiza suas habilidades quando o personagem ativo muda para outro personagem do jogador
- [ ] Barra oculta durante turno da IA
- [ ] Botao "Encerrar Turno" incluido na barra abaixo dos botoes de habilidades (substitui o botao standalone da feature 21)

### Targeting

- [ ] Clicar em botao de habilidade habilitado entra em modo targeting: botao destacado em dourado (#ffd700)
- [ ] Clicar novamente no botao selecionado ou pressionar Escape cancela targeting e volta ao modo normal
- [ ] Em modo targeting, clicar em tile envia `{ type: "action", character, action: "ability", ability: id, target: [x, y] }` via WS
- [ ] Em modo targeting, clicar em tile com inimigo para habilidades ofensivas ou tile com aliado para habilidades de suporte envia a acao (server valida)
- [ ] Habilidades com target "self" sao usadas imediatamente ao clicar no botao, sem necessidade de selecionar tile: envia `{ type: "action", character, action: "ability", ability: id, target: [x, y] }` com posicao do proprio personagem
- [ ] Apos enviar acao de habilidade, sai do modo targeting automaticamente
- [ ] Se nenhuma habilidade selecionada (modo normal), clique funciona como na feature 21: tile vazio = move, tile com inimigo = basic_attack
- [ ] Clicar no botao de ataque basico entra em targeting: proximo clique em tile envia basic_attack (mesmo comportamento do clique direto em inimigo, mas explicito)
- [ ] Input bloqueado (cliques ignorados) enquanto animacoes estao em andamento (`isAnimating` flag)

### Rastreamento de PA e Cooldowns

- [ ] PA inicializado com valor de `turn_start.pa` (tipicamente 4) a cada turno do personagem
- [ ] Apos cada `action_result` de acao do jogador, PA decrementado: habilidade usa `ability.pa_cost`, ataque basico usa 2, encerrar turno usa 0
- [ ] PA de movimentacao: calculado como `ceil(distancia_chebyshev / 2)` a partir do evento move (from→to)
- [ ] Cooldowns rastreados por personagem do jogador: `Map<entityId, Map<abilityId, turnosRestantes>>`
- [ ] Quando jogador usa habilidade com cooldown > 0: `cooldowns[charId][abilityId] = ability.cooldown`
- [ ] A cada `turn_start` de um personagem do jogador: decrementar todos os cooldowns desse personagem em 1 (minimo 0)
- [ ] Cooldowns de todos os personagens do jogador iniciam em 0 no comeco da batalha

### Animacoes — Movimento

- [ ] Evento `move`: tween suave do Container da posicao antiga para nova posicao em ~300ms (easing Quad.InOut)
- [ ] Evento `ability_movement` (ex: Investida, Transposicao): mesmo tween de movimento
- [ ] Posicao no estado interno atualizada ANTES do tween iniciar (estado correto para proximos eventos)

### Animacoes — Combate e Efeitos

- [ ] Eventos de dano (`basic_attack`, `ability`, `aoe_hit`, `opportunity_attack`, `chain_primary`, `chain_secondary`): flash visual vermelho no alvo (200ms) — alterar cor de preenchimento do circulo para vermelho, restaurar cor original
- [ ] Eventos de cura (`heal`, `self_heal`, `lifesteal`): flash visual verde no alvo (200ms)
- [ ] Eventos de DOT (`bleed`, `dot_tick`): flash vermelho sutil no alvo (150ms)
- [ ] Evento `knocked_out`: tween alpha do container de 1.0 para 0.4 em 200ms
- [ ] Evento `death`: tween alpha do container de atual para 0 em 300ms, depois destroy
- [ ] Evento `object_destroyed`: tween alpha do retangulo de 1.0 para 0 em 200ms, depois destroy
- [ ] Evento `heal` que revive (target sai de knocked_out para active): tween alpha de 0.4 para 1.0 em 200ms
- [ ] Eventos sem animacao especifica (`effect_applied`, `effect_expired`, `combo`, `trap_placed`, `purge`, etc.): processados instantaneamente, atualizam estado mas nao bloqueiam a fila

### Fila de Animacoes e Fluxo da IA

- [ ] Eventos dentro de uma mensagem WS processados sequencialmente: cada animacao completa (Promise resolve) antes de processar o proximo evento
- [ ] `handleAiAction`: processa todos os eventos com animacoes, envia `ready` somente APOS todas as animacoes completarem (await)
- [ ] `handleActionResult`: processa eventos com animacoes (await), depois atualiza PA/cooldowns
- [ ] `handleTurnStart`: processa eventos de inicio de turno com animacoes (bleed, frozen_skip) antes de habilitar input do jogador
- [ ] Jogador ve cada acao da IA animada individualmente, conforme protocolo ready/next (design.md 6.2)
- [ ] Se processEvents recebe array vazio ou undefined, resolve imediatamente (sem bloqueio)

---

## Fora do Escopo

- Barras de HP sobre personagens (feature 23)
- Icones de status ativos sobre personagens (feature 23)
- Numeros flutuantes de dano/cura (feature 23)
- Highlight de tiles de alcance ao selecionar habilidade (feature 23)
- Preview de area de efeito AoE (feature 23)
- Indicador de LoS bloqueada (feature 23)
- Indicador de objetos em chamas (feature 23)
- Arremessar objetos pelo jogador (acao "throw" nao esta no protocolo WS client→server em design.md 6.2)
- Sprites, tilesets e assets visuais — MVP usa formas geometricas e efeitos de cor
- Audio e efeitos sonoros
- Tela de resultado completa (feature 24)
