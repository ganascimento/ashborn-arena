# Feature 06 — Habilidades (47 definicoes)

## Objetivo

Definir o modelo de habilidade (Ability) e registrar todas as 47 habilidades do jogo como dados declarativos no engine, com valores numericos exatos de design.md secao 2.7. Inclui os 5 ataques basicos, 8 habilidades compartilhadas e 39 habilidades exclusivas de classe. Tambem atualiza `calculate_raw_damage` para suportar scaling float (1.2, 0.8, 1.5) com arredondamento correto. Esta feature fornece o catalogo completo de habilidades que sera usado pelo sistema de combate, IA, e frontend.

---

## Referencia nos Specs

- prd.md: secoes 3.2 (sistema de habilidades), 3.3 (habilidades detalhamento)
- design.md: secoes 2.1-2.5 (recursos, estrutura, ataque basico), 2.6 (efeitos de status), 2.7 (especificacao numerica — 47 habilidades), 2.8 (referencia de balanceamento)

---

## Arquivos Envolvidos

### Criar

- `engine/models/ability.py` — AbilityTarget (enum), BuffDef (dataclass), Ability (dataclass), BASIC_ATTACKS (dict), ABILITIES (dict)
- `engine/tests/test_ability.py` — testes do catalogo de habilidades e computacao de dano

### Modificar

- `engine/systems/damage.py` — atualizar `calculate_raw_damage`, `resolve_physical_attack`, `resolve_magical_attack`, `resolve_healing` para aceitar scaling float
- `engine/models/__init__.py` — re-exportar Ability, AbilityTarget, BuffDef, BASIC_ATTACKS, ABILITIES

---

## Criterios de Aceitacao

### Modelo de Dados

- [ ] `AbilityTarget` e um enum com valores: SINGLE_ENEMY, SINGLE_ALLY, SELF, AOE, ADJACENT, CHAIN
- [ ] `BuffDef` e um dataclass frozen com campos: tag (str), effect_type (EffectType), value (float), duration (int), target (str — "self"/"enemy"/"ally"/"area_allies"/"area_enemies"), radius (int)
- [ ] `Ability` e um dataclass frozen com campos obrigatorios: id (str), name (str), pa_cost (int), cooldown (int), classes (tuple[CharacterClass, ...]), target (AbilityTarget)
- [ ] `Ability` tem campos opcionais com default para: range, dano, cura, self-cura, efeitos (BuffDef tuple), tags elementais, flags especiais (crit_bonus, execute, lifesteal, chain, hit_count, movement, etc.)

### Atualizacao do Pipeline de Dano

- [ ] `calculate_raw_damage(base_damage, modifier, scaling)` aceita scaling float — `calculate_raw_damage(10, 3, 1.2)` retorna 14 (10 + round_half_up(3*1.2) = 10 + 4)
- [ ] `calculate_raw_damage(14, 3, 1.5)` retorna 19 (14 + round_half_up(4.5) = 14 + 5) — arredondamento half-up, nao banker's
- [ ] `calculate_raw_damage(10, 3, 2)` retorna 16 — retrocompativel com scaling inteiro
- [ ] `resolve_physical_attack` e `resolve_magical_attack` aceitam scaling float
- [ ] Testes existentes da feature 04 continuam passando

### Catalogo — Completude

- [ ] `BASIC_ATTACKS` contem exatamente 5 entradas (uma por CharacterClass)
- [ ] `ABILITIES` contem exatamente 47 entradas (keyed por ability id)
- [ ] Cada classe possui exatamente 11 habilidades disponiveis (8 compartilhadas contribuem 2x)
- [ ] Total de habilidades unicas: 47 (39 exclusivas + 8 compartilhadas)

### Catalogo — Ataques Basicos (design.md 2.5)

- [ ] Guerreiro: PA=2, CD=0, base=6, scaling=1.0, attr=str, tipo=physical, range=1
- [ ] Mago: PA=2, CD=0, base=6, scaling=1.0, attr=int_, tipo=magical, range=5
- [ ] Clerigo: PA=2, CD=0, base=6, scaling=1.0, attr=str, tipo=physical, range=1
- [ ] Arqueiro: PA=2, CD=0, base=6, scaling=1.0, attr=dex, tipo=physical, range=5
- [ ] Assassino: PA=2, CD=0, base=6, scaling=1.0, attr=dex, tipo=physical, range=1

### Catalogo — Habilidades Compartilhadas (design.md 2.7)

- [ ] Investida (GUE, ASS): PA=2, CD=3, base=10, scaling=1.2, attr=str, physical, movement=charge max 4
- [ ] Provocacao (GUE, CLE): PA=1, CD=3, control=taunt 2 turnos, sem dano
- [ ] Corte Profundo (GUE, ASS): PA=2, CD=3, base=6, scaling=0.8, attr=str, physical + DOT bleed 4/turno 3 turnos
- [ ] Escudo Inabalavel (GUE, CLE): PA=1, CD=4, shield block_next, duracao 3 turnos
- [ ] Chama Sagrada (MAG, CLE): PA=2, CD=2, base=8, scaling=1.0, attr=int_/wis, magical + self-heal 4+attr*0.3, tag=fogo
- [ ] Barreira Arcana (MAG, CLE): PA=1, CD=3, shield absorb 8+attr*1.5, duracao 3 turnos
- [ ] Tiro Certeiro (ARQ, ASS): PA=2, CD=2, base=8, scaling=1.0, attr=dex, physical, crit_bonus=0.15
- [ ] Recuar (ARQ, ASS): PA=1, CD=2, movement=retreat 2 tiles, prevents_opportunity_attack

### Catalogo — Guerreiro Exclusivas (amostra)

- [ ] Impacto Brutal: PA=2, CD=2, base=10, scaling=1.2, attr=str, physical
- [ ] Muralha de Ferro: PA=1, CD=3, buff -30% dano recebido 2 turnos (self)
- [ ] Sentenca do Carrasco: PA=3, CD=5, base=14, scaling=1.5, attr=str, physical, execute_threshold=0.30, execute_bonus=0.50
- [ ] Redemoinho de Aco: PA=3, CD=4, base=12, scaling=1.0, attr=str, physical, target=ADJACENT

### Catalogo — Mago Exclusivas (amostra)

- [ ] Estilhaco Arcano: PA=2, CD=1, base=8, scaling=1.0, attr=int_, magical
- [ ] Nova Flamejante: PA=3, CD=4, base=14, scaling=1.2, attr=int_, magical, AoE raio 1, friendly_fire, tag=fogo
- [ ] Arco Voltaico: PA=3, CD=4, base=12, scaling=1.0, attr=int_, magical, chain_targets=2, chain_damage_pct=0.70, tag=eletrico
- [ ] Meteoro: PA=3, CD=5, base=20, scaling=1.5, attr=int_, magical, AoE raio 1, delayed=True

### Catalogo — Clerigo Exclusivas (amostra)

- [ ] Toque da Aurora: PA=2, CD=1, heal base=10, scaling=1.5, attr=wis
- [ ] Consagracao: PA=2, CD=4, HOT 5+SAB*0.5/turno, 3 turnos, AoE raio 1 aliados
- [ ] Expurgo: PA=1, CD=3, remove_all_negative=True
- [ ] Julgamento Divino: PA=3, CD=4, base=14, scaling=1.5, attr=wis, magical

### Catalogo — Arqueiro Exclusivas (amostra)

- [ ] Tiro Perfurante: PA=2, CD=2, base=8, scaling=1.0, attr=dex, physical, ignores_block_pct=0.50
- [ ] Chuva de Flechas: PA=3, CD=4, base=10, scaling=0.8, attr=dex, physical, AoE raio 2, friendly_fire
- [ ] Ponta Envenenada: PA=2, CD=3, base=6, scaling=0.8, attr=dex, physical + DOT poison 4/turno 3 turnos, tag=veneno
- [ ] Flecha Glacial: PA=2, CD=3, base=7, scaling=0.8, attr=dex, physical, immobilize 1 turno + Molhado 2 turnos, tag=gelo

### Catalogo — Assassino Exclusivas (amostra)

- [ ] Lamina Oculta: PA=2, CD=1, base=7, scaling=1.0, attr=dex, physical, debuff_bonus=0.50
- [ ] Passo Sombrio: PA=1, CD=3, movement=teleport max 4, prevents_opportunity_attack
- [ ] Marca da Morte: PA=3, CD=5, base=16, scaling=1.5, attr=dex, physical, execute_threshold=0.25, execute_bonus (guaranteed crit)
- [ ] Danca das Laminas: PA=3, CD=3, base=7, scaling=1.0, attr=dex, physical, hit_count=2

### Dano Bruto — Verificacao com design.md 2.8

- [ ] Ataque Basico Guerreiro (FOR +3, scaling 1.0): raw = 6 + 3 = 9
- [ ] Ataque Basico Mago (INT +4, scaling 1.0): raw = 6 + 4 = 10
- [ ] Impacto Brutal (FOR +3, scaling 1.2): raw = 10 + round(3.6) = 14
- [ ] Estilhaco Arcano (INT +4, scaling 1.0): raw = 8 + 4 = 12
- [ ] Tiro Certeiro (DES +4, scaling 1.0): raw = 8 + 4 = 12
- [ ] Lamina Oculta (DES +3, scaling 1.0): raw = 7 + 3 = 10
- [ ] Sentenca do Carrasco (FOR +3, scaling 1.5): raw = 14 + round(4.5) = 19
- [ ] Meteoro (INT +4, scaling 1.5): raw = 20 + round(6.0) = 26
- [ ] Marca da Morte (DES +3, scaling 1.5): raw = 16 + round(4.5) = 21
- [ ] Toque da Aurora (SAB +3, scaling 1.5): raw_heal = 10 + round(4.5) = 15
- [ ] Consagracao (SAB +3, scaling 0.5): raw_hot = 5 + round(1.5) = 7/turno

---

## Fora do Escopo

- Resolucao completa de habilidades (selecao de alvo, aplicacao de dano ao HP, aplicacao de efeitos) — sera parte do sistema de combate em features 08+
- Sistema elemental e combos (Molhado+Gelo etc) — feature 07 (as tags elementais sao registradas aqui, a logica de combo nao)
- Mecanica de Meteoro com delay (marcacao + resolucao proximo turno) — sera implementada no sistema de combate
- Mecanica de Armadilha Espinhosa (colocacao no tile, ativacao por pisada) — sera implementada no sistema de combate
- Mecanica de Voto de Sacrificio (redirecionamento de dano) e Retribuicao Divina (reflexao) — sera implementada no sistema de combate
- Mecanica de Veu das Sombras (untargetable) — sera implementada no sistema de combate
- AoE targeting e friendly fire (quem e atingido) — sera implementada no sistema de combate com grid
- Integracao com TurnManager (spend_pa, use_ability) — as habilidades definem PA e CD, quem consome e o sistema de combate
