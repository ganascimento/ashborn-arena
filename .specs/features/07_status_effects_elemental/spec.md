# Feature 07 — Status Effects e Elemental

## Objetivo

Implementar o sistema de combos elementais que modifica o dano de habilidades com tags elementais quando o alvo possui o status Molhado (wet). Define a tabela de combos (Molhado+Eletrico=+50%, Molhado+Fogo=-30%, Molhado+Gelo=Congela), a funcao de resolucao de combo que consome o status, e o helper para verificar se um alvo possui status negativo (usado por Lamina Oculta). Esta feature completa a camada de efeitos do engine, permitindo que o sistema de combate aplique modificadores elementais.

---

## Referencia nos Specs

- prd.md: secao 2.6 (sistema elemental e combos — tags, tabela de combos, regras de consumo)
- design.md: secoes 2.6 (efeitos de status — Molhado, Congelado), 2.6.1 (tags elementais e combos — tabela, timing de aplicacao)

---

## Arquivos Envolvidos

### Criar

- `engine/systems/elemental.py` — ComboResult (dataclass), check_elemental_combo(), has_negative_status(), COMBO_TABLE
- `engine/tests/test_elemental.py` — testes unitarios do sistema elemental

### Modificar

- `engine/systems/__init__.py` — re-exportar ComboResult, check_elemental_combo, has_negative_status

---

## Criterios de Aceitacao

### Modelo de Resultado

- [ ] `ComboResult` e um dataclass frozen com campos: damage_modifier (float), apply_freeze (bool, default False), freeze_duration (int, default 0)

### Combo: Molhado + Eletrico (prd.md 2.6 — agua conduz eletricidade)

- [ ] Alvo com efeito "wet" (DEBUFF) + habilidade com elemental_tag="eletrico" → ComboResult(damage_modifier=1.50)
- [ ] O modificador +50% se aplica sobre o dano bruto, antes de defesas (design.md 2.6.1)
- [ ] Status Molhado (wet) e consumido (removido do EffectManager) ao ativar o combo

### Combo: Molhado + Fogo (prd.md 2.6 — agua apaga fogo)

- [ ] Alvo com efeito "wet" + elemental_tag="fogo" → ComboResult(damage_modifier=0.70)
- [ ] O modificador -30% se aplica sobre o dano bruto, antes de defesas
- [ ] Status Molhado consumido

### Combo: Molhado + Gelo (prd.md 2.6 — congela)

- [ ] Alvo com efeito "wet" + elemental_tag="gelo" → ComboResult(damage_modifier=1.0, apply_freeze=True, freeze_duration=1)
- [ ] O Congelamento (freeze) e um efeito CONTROL com tag "freeze", duracao 1 turno
- [ ] Congelado = imobiliza + nao pode agir (1 turno do personagem afetado)
- [ ] Status Molhado consumido
- [ ] O efeito freeze e aplicado ao alvo via EffectManager pela funcao check_elemental_combo

### Sem Combo

- [ ] Alvo SEM efeito "wet" + qualquer elemental_tag → retorna None
- [ ] Alvo COM "wet" + habilidade sem elemental_tag (tag="") → retorna None
- [ ] Alvo COM "wet" + elemental_tag="veneno" → retorna None (veneno nao tem combo com Molhado)

### Consumo do Status

- [ ] Apos check_elemental_combo retornar um ComboResult (nao None), o efeito "wet" nao existe mais no alvo
- [ ] Se o combo nao ativa (retorna None), o efeito "wet" permanece intacto

### Helper: has_negative_status

- [ ] `has_negative_status(effect_manager, entity_id)` retorna True se a entidade possui qualquer efeito do tipo DEBUFF, CONTROL, ou DOT
- [ ] Retorna False se a entidade so possui efeitos BUFF, HOT, SHIELD, ou nenhum efeito
- [ ] Molhado (wet, DEBUFF) conta como status negativo → has_negative_status retorna True
- [ ] Congelado (freeze, CONTROL) conta como status negativo → has_negative_status retorna True
- [ ] Sangramento (bleed, DOT) conta como status negativo → has_negative_status retorna True
- [ ] Buff de reducao de dano (BUFF) NAO conta como status negativo → has_negative_status retorna False se unico efeito

---

## Fora do Escopo

- Aplicacao de Molhado por habilidades (Toque do Inverno, Flecha Glacial ja definem o efeito "wet" na ability, quem aplica e o sistema de combate) — feature 06 define, combate aplica
- Integracao do combo no pipeline de dano (quem chama check_elemental_combo antes de resolver dano e o sistema de combate)
- Definicao de habilidades e suas tags elementais (ja feito na feature 06 — elemental_tag nos Ability)
- Efeitos de status individuais (bleed, poison, slow, etc.) — infraestrutura na feature 05, definicoes na feature 06
- Logica de Congelado impedindo acoes (sera verificado pelo sistema de combate/turnos quando checa se o personagem pode agir)
- Lamina Oculta: a logica de aplicar o bonus +50% e do sistema de combate; esta feature fornece apenas has_negative_status
