# Tasks — Feature 04: Pipeline de Dano

## Antes de Comecar

Ler obrigatoriamente antes de escrever qualquer codigo:

- `CLAUDE.md` — stack, estrutura do projeto, convencoes (ingles, sem docstrings, models separadas de entrypoints)
- `.specs/features/04_pipeline_dano/spec.md` — criterios de aceitacao desta feature
- `.specs/design.md` secoes 3.5 (tipos de dano), 3.6 (formulas de combate), 3.7 (pipeline de resolucao de dano)
- `.specs/prd.md` secoes 5.6 (papel defensivo dos atributos), 5.7 (scaling de habilidades)
- `engine/systems/initiative.py` — referencia de como sistemas existentes sao estruturados (funcoes puras com rng opcional)
- `engine/models/character.py` — referencia para Attributes.modifier()

---

## Plano de Execucao

2 grupos sequenciais. Grupo 1 e a fase TDD (testes primeiro). Grupo 2 e a implementacao.

- **Grupo 1**: escrever todos os testes (test_damage.py). Parar apos criar os testes.
- **Grupo 2**: implementar o codigo de producao (damage.py + atualizar __init__.py). Rodar testes para validar.

Dependencia: Grupo 2 so executa apos aprovacao dos testes do Grupo 1.

---

### Grupo 1 — Testes (TDD)

**Tarefa:** Criar testes unitarios para o pipeline de dano. Cobrir todos os criterios de aceitacao do spec.md com valores numericos exatos de design.md 3.6-3.7.

1. Criar `engine/tests/test_damage.py`:
   - **calculate_raw_damage:**
     - base=10, modifier=3, scaling=2 → 16
     - base=10, modifier=-3, scaling=2 → 4
     - base=10, modifier=0, scaling=2 → 10
   - **critical_chance:**
     - dex_modifier=4 → 0.08
     - dex_modifier=-1 → 0.0
     - dex_modifier=0 → 0.0
     - dex_modifier=9 → 0.18
   - **evasion_chance:**
     - dex_modifier=4 → 0.12
     - dex_modifier=-1 → 0.0
     - dex_modifier=9 → 0.27
   - **resolve_physical_attack (pipeline completo):**
     - Ataque normal sem crit/evasion: base=10, scaling=2, attack_mod=3, attacker_dex=-1, defender_dex=-1, defender_con=-1, reducao=0 → damage=17, is_critical=False, is_evaded=False, raw=16
     - Ataque normal sem crit: base=8, scaling=2, attack_mod=4, attacker_dex=4, defender_dex=-1, defender_con=2, reducao=0, rng forcar no-crit → damage=14
     - Ataque com crit: mesmos params, rng forcar crit → raw=16, crit 1.5x=24, block=24-2=22, damage=22, is_critical=True
     - Ataque com reducao 30%: base=8, scaling=2, attack_mod=4, defender_con=2, reducao=0.30, rng forcar no-crit → damage=int(14*0.70)=9
     - Ataque esquivado: rng forcar evasion → damage=0, is_evaded=True
     - Dano minimo: base=5, scaling=1, attack_mod=0, defender_con=7, reducao=0 → raw=5, block=5-7=-2, max=1
     - Aceita parametro rng opcional
   - **resolve_magical_attack (pipeline completo):**
     - Mago vs Guerreiro: base=12, scaling=2, attack_mod=4, defender_wis=-1, reducao=0 → damage=21
     - Mago vs Clerigo: base=12, scaling=2, attack_mod=4, defender_wis=3, reducao=0 → damage=17
     - Com reducao 30%: base=12, scaling=2, attack_mod=4, defender_wis=3, reducao=0.30 → damage=int(17*0.70)=11
     - Dano minimo: base=5, scaling=1, attack_mod=0, defender_wis=8, reducao=0 → raw=5, resist=5-8=-3, max=1
     - is_critical sempre False, is_evaded sempre False
   - **resolve_healing:**
     - Clerigo SAB mod +3: base=10, scaling=3 → raw_heal=19
     - Alvo 30/50 HP → amount=19, new_hp=49
     - Alvo 45/50 HP → amount=5, new_hp=50 (cap)
     - Alvo 50/50 HP → amount=0, new_hp=50
   - **DamageResult e HealResult:**
     - DamageResult tem campos: damage, is_critical, is_evaded, raw_damage
     - HealResult tem campos: amount, new_hp

2. Rodar `pytest engine/tests/test_damage.py` e confirmar que todos os testes falham (import errors — nenhum teste deve passar sem implementacao).

**Parar apos criar os testes. Nao implementar logica de producao. Aguardar aprovacao do usuario.**

---

### Grupo 2 — Implementacao (um agente)

**Tarefa:** Implementar o pipeline de dano. Todos os testes do Grupo 1 devem passar ao final.

1. Criar `engine/systems/damage.py`:
   - `class DamageType(Enum)`: PHYSICAL, MAGICAL
   - `@dataclass(frozen=True) DamageResult`: damage (int), is_critical (bool), is_evaded (bool), raw_damage (int)
   - `@dataclass(frozen=True) HealResult`: amount (int), new_hp (int)
   - `calculate_raw_damage(base_damage: int, modifier: int, scaling: int) -> int`:
     - Retorna `base_damage + (modifier * scaling)`
   - `critical_chance(dex_modifier: int) -> float`:
     - Retorna `max(0.0, dex_modifier * 0.02)`
   - `evasion_chance(dex_modifier: int) -> float`:
     - Retorna `max(0.0, dex_modifier * 0.03)`
   - `resolve_physical_attack(base_damage: int, scaling: int, attack_modifier: int, attacker_dex_modifier: int, defender_dex_modifier: int, defender_con_modifier: int, reduction_percent: float = 0.0, rng: random.Random | None = None) -> DamageResult`:
     - Segue pipeline design.md 3.7 (ataque fisico):
       1. raw = calculate_raw_damage(base_damage, attack_modifier, scaling)
       2. Crit check: gera float [0,1) via rng, se < critical_chance(attacker_dex_modifier) → raw = int(raw * 1.5), is_crit = True
       3. Evasion check: gera float [0,1), se < evasion_chance(defender_dex_modifier) → retorna DamageResult(0, is_crit, True, raw)
       4. damage = raw - defender_con_modifier
       5. Se reduction_percent > 0: damage = int(damage * (1 - reduction_percent))
       6. damage = max(damage, 1)
       7. Retorna DamageResult(damage, is_crit, False, raw)
   - `resolve_magical_attack(base_damage: int, scaling: int, attack_modifier: int, defender_wis_modifier: int, reduction_percent: float = 0.0) -> DamageResult`:
     - Segue pipeline design.md 3.7 (ataque magico):
       1. raw = calculate_raw_damage(base_damage, attack_modifier, scaling)
       2. damage = raw - defender_wis_modifier
       3. Se reduction_percent > 0: damage = int(damage * (1 - reduction_percent))
       4. damage = max(damage, 1)
       5. Retorna DamageResult(damage, False, False, raw)
   - `resolve_healing(base_heal: int, scaling: int, healer_wis_modifier: int, target_current_hp: int, target_max_hp: int) -> HealResult`:
     - raw_heal = calculate_raw_damage(base_heal, healer_wis_modifier, scaling)
     - new_hp = min(target_current_hp + raw_heal, target_max_hp)
     - amount = new_hp - target_current_hp
     - Retorna HealResult(amount, new_hp)

2. Atualizar `engine/systems/__init__.py`:
   - Adicionar imports: `from engine.systems.damage import DamageResult, DamageType, HealResult, calculate_raw_damage, critical_chance, evasion_chance, resolve_healing, resolve_magical_attack, resolve_physical_attack`
   - Adicionar ao `__all__`

3. Rodar `pytest engine/tests/test_damage.py -v` e confirmar que todos os testes passam.

4. Rodar `pytest engine/tests/ -v` para garantir que nao ha regressoes.

---

## Condicao de Conclusao

- Todos os criterios de aceitacao do spec.md satisfeitos
- Todos os testes passam com `pytest engine/tests/ -v`
- Atualizar `.specs/state.md`: status da feature 04 de `pendente` para `concluida`
