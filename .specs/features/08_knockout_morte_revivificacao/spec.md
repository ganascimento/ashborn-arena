# Feature 08 — Knockout, Morte e Revivificacao

## Objetivo

Implementar as transicoes de estado de HP dos personagens: ativo (HP > 0), caido/knockout (0 >= HP >= -10), e morto permanentemente (HP < -10). Inclui aplicacao de dano e cura ao HP, sangramento automatico de caidos (3 HP/turno), revivificacao via cura sobre HP negativo, e verificacao de condicao de vitoria. Esta feature torna o combate consequente — personagens podem cair, ser finalizados, revividos, ou morrer por sangramento.

---

## Referencia nos Specs

- prd.md: secao 2.5 (morte, knockout e revivificacao — estados, sangramento, exemplos numericos)
- design.md: secao 3.9 (knockout e morte — thresholds, estado caido, revivificacao, morte permanente, janela de revivificacao)

---

## Arquivos Envolvidos

### Criar

- `engine/tests/test_knockout.py` — testes unitarios de estado, dano, cura, sangramento e vitoria

### Modificar

- `engine/models/character.py` — adicionar CharacterState (enum), DEATH_THRESHOLD, BLEED_DAMAGE, metodos apply_damage, apply_healing, process_bleed, property state
- `engine/models/__init__.py` — re-exportar CharacterState, DEATH_THRESHOLD, BLEED_DAMAGE

---

## Criterios de Aceitacao

### Modelo de Estado

- [ ] `CharacterState` e um enum com 3 valores: ACTIVE, KNOCKED_OUT, DEAD
- [ ] `DEATH_THRESHOLD = -10` (constante — HP < -10 = morte)
- [ ] `BLEED_DAMAGE = 3` (constante — sangramento por turno de caido)
- [ ] Character inicia com state = ACTIVE
- [ ] `Character.state` retorna o estado atual

### Aplicacao de Dano (apply_damage)

- [ ] `apply_damage(amount)` reduz current_hp em amount
- [ ] Guerreiro (HP=60), apply_damage(10) → HP=50, state=ACTIVE
- [ ] Guerreiro (HP=60), apply_damage(60) → HP=0, state=KNOCKED_OUT
- [ ] Guerreiro (HP=60), apply_damage(61) → HP=-1, state=KNOCKED_OUT
- [ ] Guerreiro (HP=60), apply_damage(70) → HP=-10, state=KNOCKED_OUT (exatamente -10 ainda esta vivo, conforme design.md 3.9)
- [ ] Guerreiro (HP=60), apply_damage(71) → HP=-11, state=DEAD (overkill — prd.md 2.5 exemplo: 4 HP leva 15 = -11 = morto)
- [ ] Mago (HP=25), apply_damage(36) → HP=-11, state=DEAD
- [ ] apply_damage em personagem DEAD nao altera HP nem estado
- [ ] apply_damage retorna o CharacterState resultante

### Aplicacao de Cura (apply_healing)

- [ ] `apply_healing(amount)` aumenta current_hp em amount, cap em max_hp
- [ ] Character ACTIVE com HP=40/60, apply_healing(10) → HP=50, state=ACTIVE
- [ ] Character ACTIVE com HP=55/60, apply_healing(10) → HP=60 (cap no max_hp)
- [ ] Character KNOCKED_OUT com HP=-4, apply_healing(15) → HP=11, state=ACTIVE (revivido — prd.md 2.5 exemplo)
- [ ] Character KNOCKED_OUT com HP=-9, apply_healing(8) → HP=-1, state=KNOCKED_OUT (ainda caido — prd.md 2.5 exemplo)
- [ ] Character KNOCKED_OUT com HP=-10, apply_healing(11) → HP=1, state=ACTIVE
- [ ] Character KNOCKED_OUT com HP=-10, apply_healing(10) → HP=0, state=KNOCKED_OUT (exatamente 0 ainda e caido)
- [ ] apply_healing em personagem DEAD nao altera HP nem estado (morte permanente, nao pode ser revivido)
- [ ] apply_healing retorna o CharacterState resultante

### Sangramento Automatico (process_bleed)

- [ ] `process_bleed()` aplica BLEED_DAMAGE (3) ao personagem se state == KNOCKED_OUT
- [ ] Character KNOCKED_OUT com HP=0, process_bleed → HP=-3, state=KNOCKED_OUT
- [ ] Character KNOCKED_OUT com HP=-7, process_bleed → HP=-10, state=KNOCKED_OUT (ainda vivo)
- [ ] Character KNOCKED_OUT com HP=-8, process_bleed → HP=-11, state=DEAD (morre por sangramento)
- [ ] process_bleed em personagem ACTIVE nao faz nada, retorna 0
- [ ] process_bleed em personagem DEAD nao faz nada, retorna 0
- [ ] process_bleed retorna o dano causado (3 se aplicado, 0 se nao)

### Janela de Revivificacao (design.md 3.9 — derivada do sangramento)

- [ ] HP=0: sobrevive 3 sangamentos (0→-3→-6→-9), morre no 4o (-9→-12)
- [ ] HP=-1: sobrevive 3 sangamentos (-1→-4→-7→-10), morre no 4o (-10→-13)
- [ ] HP=-4: sobrevive 2 sangamentos (-4→-7→-10), morre no 3o (-10→-13)
- [ ] HP=-8: sobrevive 0 sangamentos, morre no 1o (-8→-11)

### Regras de Caido para Pipeline de Dano (informacional)

- [ ] Character KNOCKED_OUT: property `is_knocked_out` retorna True (util para o sistema de combate definir evasion=0%)
- [ ] Character ACTIVE: `is_knocked_out` retorna False
- [ ] Character DEAD: `is_knocked_out` retorna False (morto, nao caido)

---

## Fora do Escopo

- Integracao com TurnManager (quem chama process_bleed no inicio do turno) — sera do sistema de combate
- Remocao do personagem morto da grid e do TurnManager — sera do sistema de combate
- Condicao de vitoria (todos inimigos mortos) — sera do sistema de combate (depende de teams, nao apenas de Character)
- Decisao da IA sobre atacar caidos vs outros alvos — feature 14
- Logica de Escudo Inabalavel / Barreira Arcana absorvendo dano antes de apply_damage — sistema de combate
- Evasion=0% para caidos — o caller (sistema de combate) passa 0 para defender_dex_modifier, nao e enforced aqui
