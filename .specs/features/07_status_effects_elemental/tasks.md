# Tasks — Feature 07: Status Effects e Elemental

## Antes de Comecar

Ler obrigatoriamente antes de escrever qualquer codigo:

- `CLAUDE.md` — stack, estrutura do projeto, convencoes
- `.specs/features/07_status_effects_elemental/spec.md` — criterios de aceitacao desta feature
- `.specs/design.md` secoes 2.6 (efeitos de status), 2.6.1 (tags elementais e combos)
- `.specs/prd.md` secao 2.6 (sistema elemental e combos)
- `engine/models/effect.py` — Effect, EffectType (usado nos testes e implementacao)
- `engine/systems/effect_manager.py` — EffectManager (dependencia direta — aplica/remove efeitos)

---

## Plano de Execucao

2 grupos sequenciais. Grupo 1 e a fase TDD (testes primeiro). Grupo 2 e a implementacao.

- **Grupo 1**: escrever todos os testes (test_elemental.py). Parar apos criar os testes.
- **Grupo 2**: implementar (elemental.py + atualizar __init__.py). Rodar testes para validar.

Dependencia: Grupo 2 so executa apos aprovacao dos testes do Grupo 1.

---

### Grupo 1 — Testes (TDD)

**Tarefa:** Criar testes unitarios para o sistema elemental. Cobrir todos os criterios de aceitacao do spec.md.

1. Criar `engine/tests/test_elemental.py`:
   - **ComboResult:**
     - ComboResult criado com damage_modifier=1.5, apply_freeze=False, freeze_duration=0 — campos acessiveis
     - ComboResult defaults: apply_freeze=False, freeze_duration=0
   - **Combo Molhado + Eletrico:**
     - Criar EffectManager, aplicar Effect(tag="wet", EffectType.DEBUFF, source="X", duration=2) ao alvo
     - check_elemental_combo(em, "target", "eletrico") retorna ComboResult(damage_modifier=1.50)
     - Apos chamada: em.has_effect("target", "wet") e False (consumido)
   - **Combo Molhado + Fogo:**
     - Aplicar wet ao alvo
     - check_elemental_combo(em, "target", "fogo") retorna ComboResult(damage_modifier=0.70)
     - wet consumido
   - **Combo Molhado + Gelo:**
     - Aplicar wet ao alvo
     - check_elemental_combo(em, "target", "gelo") retorna ComboResult(damage_modifier=1.0, apply_freeze=True, freeze_duration=1)
     - wet consumido
     - em.has_effect("target", "freeze") e True — efeito CONTROL aplicado com duracao 1
   - **Sem combo:**
     - Alvo sem wet + tag "eletrico" → None
     - Alvo com wet + tag "" → None
     - Alvo com wet + tag "veneno" → None
   - **Consumo:**
     - Combo ativa → wet removido
     - Combo nao ativa → wet permanece
   - **has_negative_status:**
     - Entidade com DEBUFF (wet) → True
     - Entidade com CONTROL (freeze) → True
     - Entidade com DOT (bleed) → True
     - Entidade com BUFF apenas → False
     - Entidade com HOT apenas → False
     - Entidade com SHIELD apenas → False
     - Entidade sem efeitos → False
     - Entidade com BUFF + DEBUFF → True (qualquer negativo basta)

2. Rodar `pytest engine/tests/test_elemental.py` e confirmar que todos os testes falham.

**Parar apos criar os testes. Nao implementar logica de producao. Aguardar aprovacao do usuario.**

---

### Grupo 2 — Implementacao (um agente)

**Tarefa:** Implementar o sistema elemental. Todos os testes do Grupo 1 devem passar ao final.

1. Criar `engine/systems/elemental.py`:
   - `@dataclass(frozen=True) ComboResult`:
     - damage_modifier: float
     - apply_freeze: bool = False
     - freeze_duration: int = 0
   - Constante `_COMBO_TABLE: dict[str, ComboResult]`:
     - `"eletrico"`: ComboResult(damage_modifier=1.50)
     - `"fogo"`: ComboResult(damage_modifier=0.70)
     - `"gelo"`: ComboResult(damage_modifier=1.0, apply_freeze=True, freeze_duration=1)
   - `_NEGATIVE_TYPES = {EffectType.DEBUFF, EffectType.CONTROL, EffectType.DOT}`
   - `check_elemental_combo(effect_manager: EffectManager, target_entity_id: str, elemental_tag: str) -> ComboResult | None`:
     - Se elemental_tag vazio ou nao esta em _COMBO_TABLE → retorna None
     - Se alvo nao tem efeito "wet" → retorna None
     - Obtem ComboResult de _COMBO_TABLE[elemental_tag]
     - Remove efeito "wet" do alvo via effect_manager.remove_effects_by_tag(target_entity_id, "wet")
     - Se combo.apply_freeze: aplica Effect(tag="freeze", EffectType.CONTROL, source=target_entity_id, duration=combo.freeze_duration) ao alvo
     - Retorna ComboResult
   - `has_negative_status(effect_manager: EffectManager, entity_id: str) -> bool`:
     - Retorna True se qualquer efeito ativo da entidade tem effect_type em _NEGATIVE_TYPES
     - Itera effect_manager.get_effects(entity_id) e checa tipos

2. Atualizar `engine/systems/__init__.py`:
   - Adicionar imports: `from engine.systems.elemental import ComboResult, check_elemental_combo, has_negative_status`
   - Adicionar ao `__all__`

3. Rodar `pytest engine/tests/test_elemental.py -v` e confirmar que todos os testes passam.

4. Rodar `pytest engine/tests/ -v` para garantir que nao ha regressoes.

---

## Condicao de Conclusao

- Todos os criterios de aceitacao do spec.md satisfeitos
- Todos os testes passam com `pytest engine/tests/ -v`
- Atualizar `.specs/state.md`: status da feature 07 de `pendente` para `concluida`
