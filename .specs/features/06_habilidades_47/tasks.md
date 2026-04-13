# Tasks — Feature 06: Habilidades (47 definicoes)

## Antes de Comecar

Ler obrigatoriamente antes de escrever qualquer codigo:

- `CLAUDE.md` — stack, estrutura do projeto, convencoes
- `.specs/features/06_habilidades_47/spec.md` — criterios de aceitacao desta feature
- `.specs/design.md` secoes 2.1-2.8 (sistema de recursos, estrutura de habilidades, ataque basico, efeitos de status, especificacao numerica de todas 47 habilidades, referencia de balanceamento)
- `.specs/prd.md` secoes 3.2-3.3 (sistema de habilidades, detalhamento)
- `engine/models/character.py` — CharacterClass enum, Attributes, BASE_ATTRIBUTES
- `engine/models/effect.py` — EffectType enum (usado em BuffDef)
- `engine/systems/damage.py` — calculate_raw_damage (sera modificado)

---

## Plano de Execucao

2 grupos sequenciais. Grupo 1 e a fase TDD (testes primeiro). Grupo 2 e a implementacao.

- **Grupo 1**: escrever todos os testes (test_ability.py). Parar apos criar os testes.
- **Grupo 2**: implementar (ability.py + atualizar damage.py e __init__.py). Rodar testes para validar.

Dependencia: Grupo 2 so executa apos aprovacao dos testes do Grupo 1.

---

### Grupo 1 — Testes (TDD)

**Tarefa:** Criar testes unitarios para o catalogo de habilidades e computacao de dano com scaling float. Cobrir todos os criterios de aceitacao do spec.md.

1. Criar `engine/tests/test_ability.py`:
   - **Modelo:**
     - AbilityTarget tem 6 valores: SINGLE_ENEMY, SINGLE_ALLY, SELF, AOE, ADJACENT, CHAIN
     - BuffDef criado com tag, effect_type, value, duration, target, radius
     - Ability criado com campos obrigatorios (id, name, pa_cost, cooldown, classes, target) — verificar defaults
   - **calculate_raw_damage com float scaling:**
     - `calculate_raw_damage(10, 3, 1.2)` == 14
     - `calculate_raw_damage(14, 3, 1.5)` == 19
     - `calculate_raw_damage(10, 3, 2)` == 16 (retrocompativel)
     - `calculate_raw_damage(10, -3, 1.2)` == 6 (10 + round(-3.6) = 10 + (-4) = 6)
     - `calculate_raw_damage(8, 4, 0.8)` == 11 (8 + round(3.2) = 8 + 3)
     - `calculate_raw_damage(6, 3, 1.0)` == 9
   - **Catalogo — Completude:**
     - len(BASIC_ATTACKS) == 5
     - len(ABILITIES) == 47
     - Cada CharacterClass aparece em exatamente 11 habilidades (filtrar ABILITIES por classe)
   - **Catalogo — 5 Ataques Basicos:**
     - Verificar pa_cost=2, cooldown=0, damage_base=6, damage_scaling=1.0 para todos
     - Guerreiro: damage_attr="str", damage_type="physical", max_range=1
     - Mago: damage_attr="int_", damage_type="magical", max_range=5
     - Clerigo: damage_attr="str", damage_type="physical", max_range=1
     - Arqueiro: damage_attr="dex", damage_type="physical", max_range=5
     - Assassino: damage_attr="dex", damage_type="physical", max_range=1
   - **Catalogo — 8 Compartilhadas (verificacao completa):**
     - Investida: classes=(WARRIOR,ASSASSIN), PA=2, CD=3, base=10, scaling=1.2, str, physical, movement_type="charge", movement_distance=4
     - Provocacao: classes=(WARRIOR,CLERIC), PA=1, CD=3, sem dano, effects tem taunt CONTROL 2 turnos
     - Corte Profundo: classes=(WARRIOR,ASSASSIN), PA=2, CD=3, base=6, scaling=0.8, str, physical, effects tem bleed DOT 4.0/turno 3 turnos
     - Escudo Inabalavel: classes=(WARRIOR,CLERIC), PA=1, CD=4, shield_block_next=True, shield_duration=3
     - Chama Sagrada: classes=(MAGE,CLERIC), PA=2, CD=2, base=8, scaling=1.0, magical, self_heal_base=4, self_heal_scaling=0.3, elemental_tag="fogo"
     - Barreira Arcana: classes=(MAGE,CLERIC), PA=1, CD=3, shield_absorb_base=8, shield_absorb_scaling=1.5, shield_duration=3
     - Tiro Certeiro: classes=(ARCHER,ASSASSIN), PA=2, CD=2, base=8, scaling=1.0, dex, physical, crit_bonus=0.15
     - Recuar: classes=(ARCHER,ASSASSIN), PA=1, CD=2, movement_type="retreat", movement_distance=2, prevents_opportunity_attack=True
   - **Catalogo — Exclusivas (spot-check por classe, 2-3 por classe):**
     - Guerreiro: Impacto Brutal (base=10, scaling=1.2), Muralha de Ferro (buff damage_reduction 0.30 2T), Sentenca do Carrasco (base=14, scaling=1.5, execute_threshold=0.30, execute_bonus=0.50)
     - Mago: Estilhaco Arcano (base=8, scaling=1.0), Nova Flamejante (base=14, scaling=1.2, aoe_radius=1, elemental_tag="fogo"), Arco Voltaico (base=12, chain_targets=2, chain_damage_pct=0.70, elemental_tag="eletrico")
     - Clerigo: Toque da Aurora (heal base=10, scaling=1.5, wis), Consagracao (HOT), Julgamento Divino (base=14, scaling=1.5, wis, magical)
     - Arqueiro: Tiro Perfurante (ignores_block_pct=0.50), Ponta Envenenada (DOT poison 4/turno 3T, elemental_tag="veneno"), Flecha Glacial (immobilize 1T + Molhado 2T, elemental_tag="gelo")
     - Assassino: Lamina Oculta (debuff_bonus=0.50), Passo Sombrio (teleport 4, prevents_opp), Marca da Morte (base=16, scaling=1.5, execute), Danca das Laminas (hit_count=2)
   - **Dano bruto com habilidades (design.md 2.8):**
     - Ataque Basico GUE (FOR +3): calculate_raw_damage(6, 3, 1.0) == 9
     - Ataque Basico MAG (INT +4): calculate_raw_damage(6, 4, 1.0) == 10
     - Impacto Brutal (FOR +3): calculate_raw_damage(10, 3, 1.2) == 14
     - Estilhaco Arcano (INT +4): calculate_raw_damage(8, 4, 1.0) == 12
     - Tiro Certeiro (DES +4): calculate_raw_damage(8, 4, 1.0) == 12
     - Lamina Oculta (DES +3): calculate_raw_damage(7, 3, 1.0) == 10
     - Sentenca do Carrasco (FOR +3): calculate_raw_damage(14, 3, 1.5) == 19
     - Meteoro (INT +4): calculate_raw_damage(20, 4, 1.5) == 26
     - Marca da Morte (DES +3): calculate_raw_damage(16, 3, 1.5) == 21
     - Toque da Aurora (SAB +3): calculate_raw_damage(10, 3, 1.5) == 15
     - Consagracao HOT (SAB +3): calculate_raw_damage(5, 3, 0.5) == 7

2. Rodar `pytest engine/tests/test_ability.py` e confirmar que todos os testes falham.

**Parar apos criar os testes. Nao implementar logica de producao. Aguardar aprovacao do usuario.**

---

### Grupo 2 — Implementacao (um agente)

**Tarefa:** Implementar o modelo de habilidade, o catalogo completo de 47 habilidades, e atualizar calculate_raw_damage para float scaling. Todos os testes do Grupo 1 devem passar ao final.

1. Atualizar `engine/systems/damage.py`:
   - Alterar `calculate_raw_damage(base_damage: int, modifier: int, scaling: float) -> int`:
     - Formula: `base_damage + math.floor(modifier * scaling + 0.5)` (round half up)
     - Importar `math` no topo do arquivo
   - Alterar `resolve_physical_attack`: `scaling: int` → `scaling: float`
   - Alterar `resolve_magical_attack`: `scaling: int` → `scaling: float`
   - Alterar `resolve_healing`: `scaling: int` → `scaling: float`
   - Rodar `pytest engine/tests/test_damage.py` para garantir retrocompatibilidade

2. Criar `engine/models/ability.py`:
   - `class AbilityTarget(Enum)`: SINGLE_ENEMY, SINGLE_ALLY, SELF, AOE, ADJACENT, CHAIN
   - `@dataclass(frozen=True) BuffDef`:
     - tag: str, effect_type: EffectType, value: float = 0.0, duration: int = 0, target: str = "enemy", radius: int = 0
   - `@dataclass(frozen=True) Ability`:
     - Campos obrigatorios: id (str), name (str), pa_cost (int), cooldown (int), classes (tuple[CharacterClass, ...]), target (AbilityTarget)
     - Targeting: min_range (int=0), max_range (int=1), aoe_radius (int=0), friendly_fire (bool=False)
     - Damage: damage_base (int=0), damage_scaling (float=0.0), damage_attr (str=""), damage_type (str="")
     - Heal: heal_base (int=0), heal_scaling (float=0.0), heal_attr (str="")
     - Self-heal: self_heal_base (int=0), self_heal_scaling (float=0.0), self_heal_attr (str="")
     - Effects: effects (tuple[BuffDef, ...]=())
     - Elemental: elemental_tag (str="")
     - Special: crit_bonus (float=0.0), ignores_block_pct (float=0.0), execute_threshold (float=0.0), execute_bonus (float=0.0), debuff_bonus (float=0.0), lifesteal_pct (float=0.0), chain_targets (int=0), chain_damage_pct (float=0.0), hit_count (int=1), prevents_opportunity_attack (bool=False)
     - Movement: movement_type (str=""), movement_distance (int=0)
     - Shield: shield_absorb_base (int=0), shield_absorb_scaling (float=0.0), shield_absorb_attr (str=""), shield_block_next (bool=False), shield_duration (int=0)
     - Delayed: delayed (bool=False)
     - Purge: remove_all_negative (bool=False)

3. Definir `BASIC_ATTACKS: dict[CharacterClass, Ability]` com os 5 ataques basicos conforme design.md 2.5:
   - Guerreiro: basic_attack_warrior, attr=str, physical, range=1
   - Mago: basic_attack_mage, attr=int_, magical, range=5
   - Clerigo: basic_attack_cleric, attr=str, physical, range=1
   - Arqueiro: basic_attack_archer, attr=dex, physical, range=5
   - Assassino: basic_attack_assassin, attr=dex, physical, range=1
   - Todos: PA=2, CD=0, base=6, scaling=1.0

4. Definir `ABILITIES: dict[str, Ability]` com as 47 habilidades conforme design.md 2.7.
   Cada habilidade deve ter o id como chave (snake_case em ingles). Valores exatos de design.md:

   **Compartilhadas (8):**
   - investida, provocacao, corte_profundo, escudo_inabalavel, chama_sagrada, barreira_arcana, tiro_certeiro, recuar

   **Guerreiro (7 exclusivas):**
   - impacto_brutal, grito_de_guerra, redemoinho_de_aco, muralha_de_ferro, furia_implacavel, sentenca_do_carrasco, bastiao

   **Mago (9 exclusivas):**
   - estilhaco_arcano, nova_flamejante, toque_do_inverno, arco_voltaico, vacuo_arcano, transposicao, sifao_vital, meteoro, canalizacao_arcana

   **Clerigo (7 exclusivas):**
   - toque_da_aurora, egide_sagrada, expurgo, consagracao, retribuicao_divina, julgamento_divino, voto_de_sacrificio

   **Arqueiro (8 exclusivas):**
   - tiro_perfurante, chuva_de_flechas, ponta_envenenada, flecha_glacial, olho_do_predador, rajada_dupla, armadilha_espinhosa, alcance_supremo, concentracao_absoluta

   **Assassino (6 exclusivas):**
   - lamina_oculta, passo_sombrio, danca_das_laminas, veu_das_sombras, toque_peconhento, marca_da_morte, sede_de_sangue

   **Nota**: Para Chama Sagrada e Barreira Arcana, que sao compartilhadas entre Mago e Clerigo e usam INT ou SAB dependendo da classe, o campo damage_attr/heal_attr/shield_absorb_attr deve usar o atributo de scaling primario. O sistema de combate (futuro) selecionara o atributo correto com base na classe de quem usa. Registrar ambos attrs possíveis nao e necessario no catalogo — a habilidade define a mecanica, o combate resolve o atributo.

5. Atualizar `engine/models/__init__.py`:
   - Adicionar imports: `from engine.models.ability import ABILITIES, BASIC_ATTACKS, Ability, AbilityTarget, BuffDef`
   - Adicionar ao `__all__`

6. Rodar `pytest engine/tests/test_ability.py -v` e confirmar que todos os testes passam.

7. Rodar `pytest engine/tests/ -v` para garantir que nao ha regressoes (especialmente test_damage.py).

---

## Condicao de Conclusao

- Todos os criterios de aceitacao do spec.md satisfeitos
- Todos os testes passam com `pytest engine/tests/ -v`
- Atualizar `.specs/state.md`: status da feature 06 de `pendente` para `concluida`
