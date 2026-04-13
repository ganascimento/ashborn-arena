# Feature 05 — Sistema de Efeitos

## Objetivo

Implementar a infraestrutura de efeitos temporarios (DOTs, HOTs, buffs, debuffs, controles, escudos) que pode ser aplicada a personagens durante a batalha. Define o modelo de efeito, regras de stacking, processamento temporal (inicio e fim de turno), e metodos de consulta para integracao com o pipeline de dano. Esta feature e a base sobre a qual habilidades (feature 06), status effects elementais (feature 07), e knockout/sangramento (feature 08) operam.

---

## Referencia nos Specs

- prd.md: secoes 2.6 (sistema elemental — tags de efeitos), 3.3 (efeitos listados nas habilidades)
- design.md: secoes 1.1 (stacking aditivo de buffs), 1.4 (timing de efeitos — DOTs fim de turno, buffs/debuffs inicio de turno), 2.6 (efeitos de status — tipos e regras de stack), 2.7 (efeitos especificos de cada habilidade)

---

## Arquivos Envolvidos

### Criar

- `engine/models/effect.py` — EffectType (enum), Effect (dataclass)
- `engine/systems/effect_manager.py` — EffectManager (classe que gerencia efeitos ativos por entidade)
- `engine/tests/test_effect_manager.py` — testes unitarios do sistema de efeitos

### Modificar

- `engine/models/__init__.py` — re-exportar EffectType, Effect
- `engine/systems/__init__.py` — re-exportar EffectManager

---

## Criterios de Aceitacao

### Modelo de Efeito

- [ ] `EffectType` e um enum com 6 valores: DOT, HOT, BUFF, DEBUFF, CONTROL, SHIELD
- [ ] `Effect` tem campos: tag (str), effect_type (EffectType), source_entity_id (str), duration (int), value (float, default 0.0)
- [ ] Effect e mutavel (duration precisa ser decrementada in-place)

### Aplicacao com Regras de Stacking

- [ ] DOT mesmo tag + mesma source: renova duracao, nao duplica (conforme design.md 2.6 "DOT da mesma fonte: renova duracao, nao stacka")
- [ ] DOT mesmo tag + source diferente: coexistem independentemente (conforme design.md 2.6 "DOTs de fontes diferentes: stackam independentemente")
- [ ] BUFF/DEBUFF/CONTROL/SHIELD mesmo tag: renova duracao e atualiza value, independente da source (conforme design.md 2.6 "nova aplicacao renova duracao, nao stacka")
- [ ] HOT segue mesma regra de DOT: mesma source renova, source diferente stacka
- [ ] Efeitos com tags diferentes sempre coexistem (stacking aditivo entre diferentes efeitos — conforme design.md 1.1)

### Processamento de Inicio de Turno (buffs/debuffs/controles/escudos)

- [ ] `process_turn_start(entity_id)` decrementa duracao de todos os efeitos BUFF, DEBUFF, CONTROL e SHIELD da entidade
- [ ] Efeito com duracao < 0 apos decremento e removido (expirado)
- [ ] Buff com duracao 2: ativo durante 2 turnos completos, removido no inicio do 3o turno (conforme design.md 1.4)
- [ ] Concretamente: duracao 2 → decrementa para 1 (ativo) → decrementa para 0 (ativo) → decrementa para -1 (removido)
- [ ] `process_turn_start` retorna lista de efeitos expirados (removidos neste tick)
- [ ] DOTs e HOTs NAO sao decrementados no inicio do turno

### Processamento de Fim de Turno (DOTs e HOTs)

- [ ] `process_turn_end(entity_id)` aplica o valor de cada DOT e HOT ativo, decrementa duracao, e remove quando duracao chega a 0
- [ ] DOT sangramento 4/turno por 3 turnos: 3 aplicacoes de 4 dano (total 12), removido apos 3o tick
- [ ] DOTs de fontes diferentes tickam independentemente: bleed source A (4/turno) + bleed source B (4/turno) = 8 dano total por turn_end
- [ ] HOT 5/turno por 3 turnos: 3 aplicacoes de 5 cura (total 15), removido apos 3o tick
- [ ] DOTs ignoram defesas — o valor retornado e fixo (conforme design.md 1.4 "DOTs ignoram defesas: dano fixo")
- [ ] `process_turn_end` retorna lista de efeitos que tickaram (tag, effect_type, value) para o chamador aplicar dano/cura
- [ ] Buffs/debuffs/controles/escudos NAO sao processados no fim do turno

### Consultas

- [ ] `get_effects(entity_id)` retorna todos os efeitos ativos da entidade (copia da lista)
- [ ] `get_effects_by_type(entity_id, effect_type)` retorna apenas efeitos do tipo especificado
- [ ] `has_effect(entity_id, tag)` retorna True se existe efeito ativo com esse tag, False caso contrario
- [ ] `get_effect(entity_id, tag)` retorna o primeiro efeito com esse tag, ou None
- [ ] Entidade sem efeitos: `get_effects` retorna lista vazia, `has_effect` retorna False

### Remocao

- [ ] `remove_effects_by_tag(entity_id, tag)` remove todos os efeitos com esse tag (incluindo DOTs stackados de sources diferentes)
- [ ] `remove_all_negative(entity_id)` remove todos os efeitos do tipo DEBUFF e CONTROL, mantendo BUFFs, DOTs, HOTs e SHIELDs
- [ ] `remove_all_negative` retorna lista dos efeitos removidos
- [ ] `remove_entity(entity_id)` remove todos os efeitos da entidade (para quando morre/sai da batalha)

---

## Fora do Escopo

- Definicao de habilidades especificas e seus efeitos (tags, valores, duracoes) — feature 06
- Sistema elemental e combos (Molhado+Gelo, Molhado+Eletrico) — feature 07
- Aplicacao de dano/cura ao HP do Character (pipeline de dano calcula, efeito retorna valor, quem aplica ao HP e o sistema de combate) — features 06/08
- Integracao com TurnManager (quem chama process_turn_start/end no momento certo) — feature 06/08
- Mecanica de escudo absorvente e reflexao (Barreira Arcana, Retribuicao Divina, Escudo Inabalavel) — feature 06 (define os efeitos, feature 05 fornece o tipo SHIELD)
- Sangramento automatico de caidos (3 HP/turno) — feature 08
- Provocacao/Taunt (restricao de alvo) — a tag e registrada aqui, a logica de restricao e da IA/combate
