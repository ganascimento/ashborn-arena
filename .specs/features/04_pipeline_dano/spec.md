# Feature 04 — Pipeline de Dano

## Objetivo

Implementar o pipeline completo de resolucao de dano fisico, dano magico e cura como funcoes puras no engine. Define as formulas de dano bruto, critico, esquiva, bloqueio, resistencia magica, reducao percentual de buffs, dano minimo e cura com cap de HP. Esta feature e a base de combate — todas as habilidades (feature 06), efeitos (feature 05), knockout (feature 08) e ataque de oportunidade (feature 09) dependem deste pipeline.

---

## Referencia nos Specs

- prd.md: secoes 5.6 (papel defensivo dos atributos), 5.7 (scaling de habilidades)
- design.md: secoes 3.5 (tipos de dano), 3.6 (formulas de combate), 3.7 (pipeline de resolucao de dano)

---

## Arquivos Envolvidos

### Criar

- `engine/systems/damage.py` — DamageType (enum), DamageResult (dataclass), HealResult (dataclass), funcoes do pipeline
- `engine/tests/test_damage.py` — testes unitarios do pipeline de dano

### Modificar

- `engine/systems/__init__.py` — re-exportar DamageType, DamageResult, HealResult e funcoes publicas

---

## Criterios de Aceitacao

### Dano Bruto

- [ ] `calculate_raw_damage(base_damage=10, modifier=3, scaling=2)` retorna 16 (10 + 3*2)
- [ ] `calculate_raw_damage(base_damage=10, modifier=-3, scaling=2)` retorna 4 (10 + (-3)*2)
- [ ] `calculate_raw_damage(base_damage=10, modifier=0, scaling=2)` retorna 10

### Critico (apenas fisico)

- [ ] `critical_chance(dex_modifier=4)` retorna 0.08 (max(0, 4*0.02) = 8%)
- [ ] `critical_chance(dex_modifier=-1)` retorna 0.0 (modificador negativo = 0%)
- [ ] `critical_chance(dex_modifier=0)` retorna 0.0
- [ ] `critical_chance(dex_modifier=9)` retorna 0.18 (18% — maximo possivel)
- [ ] Multiplicador de critico e 1.5x sobre o dano bruto

### Esquiva (apenas fisico)

- [ ] `evasion_chance(dex_modifier=4)` retorna 0.12 (max(0, 4*0.03) = 12%)
- [ ] `evasion_chance(dex_modifier=-1)` retorna 0.0
- [ ] `evasion_chance(dex_modifier=9)` retorna 0.27 (27% — maximo possivel)
- [ ] Esquiva evita o ataque completamente (dano = 0)

### Bloqueio (apenas fisico)

- [ ] Bloqueio = modificador_CON do defensor, subtraido do dano
- [ ] Modificador negativo aumenta o dano recebido: dano 16, CON mod -1 → 16 - (-1) = 17
- [ ] Modificador positivo reduz o dano: dano 16, CON mod +2 → 16 - 2 = 14

### Resistencia Magica (apenas magico)

- [ ] Resistencia = modificador_SAB do defensor, subtraido do dano
- [ ] Modificador negativo aumenta o dano: dano 20, SAB mod -1 → 20 - (-1) = 21
- [ ] Modificador positivo reduz o dano: dano 20, SAB mod +3 → 20 - 3 = 17

### Reducao Percentual (buffs ativos)

- [ ] Aplicada apos bloqueio/resistencia: dano 14, reducao 30% → int(14 * 0.70) = 9
- [ ] Stacking aditivo: reducao 30% + 20% = 50% → dano 14 * 0.50 = 7
- [ ] Sem reducao (0%): dano nao e alterado

### Dano Minimo

- [ ] Dano final nunca e menor que 1 (exceto esquiva que retorna 0)
- [ ] dano bruto 5, bloqueio +7 → 5 - 7 = -2 → max(-2, 1) = 1

### Pipeline Fisico Completo (resolve_physical_attack)

- [ ] Guerreiro (FOR mod +3, DES mod -1) ataca Mago (DES mod -1, CON mod -1), base=10, scaling=2, sem reducao: raw=16, crit=0%, evasion=0%, block=16-(-1)=17, **resultado=17**
- [ ] Arqueiro (DES mod +4 ataque e crit) ataca Guerreiro (DES mod -1, CON mod +2), base=8, scaling=2, sem reducao, sem crit (rng deterministico): raw=16, evasion=0%, block=16-2=14, **resultado=14**
- [ ] Mesmo ataque com crit (rng deterministico): raw=16, crit 1.5x=24, block=24-2=22, **resultado=22**
- [ ] Ataque com reducao 30%: raw=16, block=16-2=14, reducao=int(14*0.70)=9, **resultado=9**
- [ ] Ataque esquivado (rng deterministico): **resultado=0, is_evaded=True**
- [ ] Dano minimo aplicado: raw=5, block=5-7=-2, **resultado=1**
- [ ] DamageResult contem: damage (int), is_critical (bool), is_evaded (bool), raw_damage (int)
- [ ] `resolve_physical_attack` aceita parametro opcional `rng: random.Random` para resultados deterministicos

### Pipeline Magico Completo (resolve_magical_attack)

- [ ] Mago (INT mod +4) ataca Guerreiro (SAB mod -1), base=12, scaling=2, sem reducao: raw=20, resistance=20-(-1)=21, **resultado=21**
- [ ] Mago (INT mod +4) ataca Clerigo (SAB mod +3), base=12, scaling=2, sem reducao: raw=20, resistance=20-3=17, **resultado=17**
- [ ] Com reducao 30%: raw=20, resistance=20-3=17, reducao=int(17*0.70)=11, **resultado=11**
- [ ] Dano minimo: raw=5, resistance SAB mod +8 → 5-8=-3, **resultado=1**
- [ ] DamageResult.is_critical sempre False, DamageResult.is_evaded sempre False para magico

### Cura (resolve_healing)

- [ ] Clerigo (SAB mod +3), base=10, scaling=3: cura = 10 + 3*3 = 19
- [ ] Alvo com 30/50 HP: amount=19, new_hp=49
- [ ] Alvo com 45/50 HP: amount=5, new_hp=50 (cap no max_hp)
- [ ] Alvo com 50/50 HP: amount=0, new_hp=50 (ja no maximo)
- [ ] HealResult contem: amount (int — cura efetiva), new_hp (int)

---

## Fora do Escopo

- Definicao de habilidades especificas (base_damage, scaling, tipo) — feature 06
- Sistema de efeitos e buffs ativos (fonte da reducao percentual) — feature 05
- Status effects e combos elementais (Molhado+Eletrico etc) — feature 07
- Knockout, morte e transicoes de estado de HP — feature 08
- Ataque de oportunidade (invocacao do pipeline fora do turno) — feature 09
- Alvos caidos: esquiva=0% para caidos — feature 08 (o pipeline recebe o modificador ja ajustado)
- AoE e targeting (quem e atingido) — feature 06
- Aplicacao de dano ao HP do Character (current_hp -= damage) — feature 08 (o pipeline calcula, quem aplica e o sistema de combate)
