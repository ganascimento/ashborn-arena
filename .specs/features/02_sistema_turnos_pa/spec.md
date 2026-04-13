# Feature 02 — Sistema de Turnos e PA

## Objetivo

Implementar o sistema de turnos, pontos de acao (PA) e cooldowns que controla o fluxo temporal da batalha. Define quem age quando (iniciativa), quantas acoes cada personagem pode executar por turno (PA), e a cadencia de uso de habilidades (cooldown). Esta feature fornece a infraestrutura de ciclo de turnos do engine — todas as features de combate, habilidades e efeitos dependem dela para saber quando cada personagem age e quantas acoes pode tomar.

---

## Referencia nos Specs

- prd.md: secoes 2.2 (sistema de turnos), 2.3 (ordem de turnos — iniciativa)
- design.md: secoes 1.1 (turnos e PA), 1.4 (timing de efeitos — apenas definicao dos hooks de inicio/fim de turno), 3.4 (sistema de iniciativa)

---

## Arquivos Envolvidos

### Criar

- `engine/systems/initiative.py` — roll_initiative(), determine_turn_order()
- `engine/systems/turn_manager.py` — TurnManager class (PA, cooldowns, fluxo de turnos e rounds)
- `engine/tests/test_initiative.py` — testes unitarios do sistema de iniciativa
- `engine/tests/test_turn_manager.py` — testes unitarios do TurnManager

### Modificar

- `engine/systems/__init__.py` — re-exportar roll_initiative, determine_turn_order, TurnManager

---

## Criterios de Aceitacao

### Iniciativa

- [ ] `roll_initiative(dex_modifier)` retorna valor no range [1 + dex_modifier, 20 + dex_modifier] (rola d20 + modificador de Destreza)
- [ ] `roll_initiative(dex_modifier=3)` retorna valor entre 4 e 23
- [ ] `roll_initiative(dex_modifier=-2)` retorna valor entre -1 e 18
- [ ] `roll_initiative` aceita parametro opcional `rng: random.Random` para resultados deterministicos em testes
- [ ] `determine_turn_order(participants, rng)` recebe lista de tuplas (entity_id, dex_modifier, dex_base) e retorna lista de entity_ids ordenados por iniciativa decrescente (maior age primeiro)
- [ ] Desempate em valor de iniciativa: personagem com maior dex_base age primeiro (conforme prd.md 2.3)
- [ ] Desempate em iniciativa e dex_base iguais: ordem definida por sorteio deterministico (via `rng`)

### Pontos de Acao (PA)

- [ ] Ao iniciar o turno de um personagem, PA e definido como 4 (constante PA_PER_TURN = 4, conforme design.md 1.1)
- [ ] `get_pa(entity_id)` retorna PA restante do personagem (0 para quem nao e o personagem ativo)
- [ ] `spend_pa(entity_id, cost)` reduz PA do personagem — spend_pa com cost=2 e PA=4 resulta em PA=2
- [ ] `spend_pa` com cost=1 seguido de cost=2 resulta em PA=1 (4 - 1 - 2 = 1)
- [ ] `spend_pa` levanta erro se cost > PA restante do personagem
- [ ] `spend_pa` levanta erro se entity_id nao e o personagem do turno atual
- [ ] `spend_pa` levanta erro se cost <= 0
- [ ] `can_spend_pa(entity_id, cost)` retorna True se PA restante >= cost, False caso contrario
- [ ] PA nao utilizado e perdido ao encerrar o turno — apos end_turn, PA do personagem anterior e 0

### Cooldowns

- [ ] Habilidade nunca usada tem cooldown 0 — `is_ability_ready(entity_id, ability_slot)` retorna True
- [ ] `get_cooldown(entity_id, ability_slot)` retorna cooldown restante (0 = pronto para uso)
- [ ] `use_ability(entity_id, ability_slot, cooldown)` define cooldown restante para o valor informado
- [ ] `use_ability` com cooldown=0 e valido (ataque basico — sem cooldown, sempre pronto)
- [ ] `use_ability` levanta erro se habilidade esta em cooldown (cooldown restante > 0)
- [ ] `use_ability` levanta erro se entity_id nao e o personagem do turno atual
- [ ] Cooldown decrementa em 1 no inicio do turno do personagem (uma vez por round), piso em 0
- [ ] Habilidade com CD 3 usada no round 1: cooldown 2 no inicio do round 2, cooldown 1 no round 3, cooldown 0 no round 4 (disponivel) — conforme design.md 1.1 "CD 3 no turno 1 -> disponivel turno 4"

### Fluxo de Turnos

- [ ] `TurnManager(turn_order)` inicializa com lista de entity_ids — primeiro entity_id e o personagem ativo, turno ja iniciado (PA=4)
- [ ] `TurnManager([])` com lista vazia levanta erro
- [ ] `current_entity` retorna entity_id do personagem cujo turno esta ativo
- [ ] `current_round` inicia em 1
- [ ] `turn_order` retorna a lista completa de entity_ids na ordem de iniciativa
- [ ] `end_turn()` encerra o turno atual, descarta PA restante, inicia turno do proximo personagem (PA=4, cooldowns decrementados)
- [ ] `end_turn()` retorna entity_id do proximo personagem ativo
- [ ] Apos o ultimo personagem da ordem encerrar seu turno, round incrementa e volta ao primeiro personagem
- [ ] 3 personagens (A, B, C): end_turn de A retorna B, end_turn de B retorna C, end_turn de C retorna A e current_round incrementa para 2
- [ ] `remove_entity(entity_id)` remove personagem da ordem de turnos
- [ ] Se o personagem removido e o atual, avanca para o proximo (proximo personagem inicia seu turno com PA=4)
- [ ] Remover personagem que nao esta na ordem levanta erro
- [ ] Ordem com 2 personagens, remover 1: turno continua normalmente para o remanescente

---

## Fora do Escopo

- Modelo de Character com atributos, HP, classe — feature 03 (TurnManager usa entity_id generico e recebe dex_modifier como parametro na iniciativa)
- Calculo de dano, defesas, esquiva, critico — feature 04
- Processamento de DOTs no fim do turno — feature 05 (TurnManager fornece o ciclo start/end de turno, nao processa efeitos)
- Decremento de buffs/debuffs no inicio do turno — feature 05/07 (idem — o hook temporal esta aqui, a logica de efeitos nao)
- Definicao e execucao de habilidades — feature 06 (TurnManager rastreia cooldowns por slot, sem saber o que a habilidade faz)
- Condicao de vitoria (todos inimigos mortos) — feature 08
- Logica de personagem caido (pular turno, sangramento) — feature 08
- Ataque de oportunidade (acao fora do turno, sem custo de PA) — feature 09
