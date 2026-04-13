# Tasks — Feature 05: Sistema de Efeitos

## Antes de Comecar

Ler obrigatoriamente antes de escrever qualquer codigo:

- `CLAUDE.md` — stack, estrutura do projeto, convencoes (ingles, sem docstrings, models separadas de entrypoints)
- `.specs/features/05_sistema_efeitos/spec.md` — criterios de aceitacao desta feature
- `.specs/design.md` secoes 1.4 (timing de efeitos), 2.6 (efeitos de status e regras de stack)
- `.specs/prd.md` secao 2.6 (sistema elemental — para entender os tipos de efeito)
- `engine/models/character.py` — referencia de como models sao estruturadas (dataclass, enum)
- `engine/models/grid.py` — referencia de como enums sao definidas
- `engine/systems/turn_manager.py` — referencia de como sistemas existentes sao estruturados

---

## Plano de Execucao

2 grupos sequenciais. Grupo 1 e a fase TDD (testes primeiro). Grupo 2 e a implementacao.

- **Grupo 1**: escrever todos os testes (test_effect_manager.py). Parar apos criar os testes.
- **Grupo 2**: implementar o codigo de producao (effect.py + effect_manager.py + atualizar __init__.py). Rodar testes para validar.

Dependencia: Grupo 2 so executa apos aprovacao dos testes do Grupo 1.

---

### Grupo 1 — Testes (TDD)

**Tarefa:** Criar testes unitarios para o modelo de efeito e o EffectManager. Cobrir todos os criterios de aceitacao do spec.md.

1. Criar `engine/tests/test_effect_manager.py`:
   - **EffectType e Effect:**
     - EffectType tem 6 valores: DOT, HOT, BUFF, DEBUFF, CONTROL, SHIELD
     - Effect criado com tag, effect_type, source_entity_id, duration, value — todos acessiveis
     - Effect.value default e 0.0
     - Effect e mutavel: duration pode ser alterada
   - **Stacking — DOT:**
     - Aplicar DOT (tag="bleed", source="A", duration=3, value=4). Aplicar mesmo DOT (tag="bleed", source="A", duration=3, value=4) → apenas 1 efeito, duracao renovada
     - Aplicar DOT (tag="bleed", source="A") + DOT (tag="bleed", source="B") → 2 efeitos independentes
   - **Stacking — BUFF/DEBUFF/CONTROL:**
     - Aplicar BUFF (tag="dr", source="A", value=0.30, duration=2). Aplicar BUFF (tag="dr", source="B", value=0.25, duration=3) → apenas 1 efeito, duration=3, value=0.25
     - Aplicar CONTROL (tag="taunt", source="A", duration=2). Aplicar CONTROL (tag="taunt", source="B", duration=2) → apenas 1 efeito, duration=2 renovada
   - **Stacking — tags diferentes:**
     - Aplicar BUFF (tag="buff_a", value=0.30) + BUFF (tag="buff_b", value=0.20) → 2 efeitos coexistem
   - **process_turn_start:**
     - Buff com duration=2: process_turn_start 1x → duracao 1 (ativo), 2x → duracao 0 (ativo), 3x → duracao -1 (removido, retornado como expirado)
     - Debuff com duration=1: process_turn_start 1x → duracao 0 (ativo), 2x → removido
     - DOT NAO e afetado por process_turn_start: aplicar DOT + process_turn_start → DOT permanece com mesma duracao
     - HOT NAO e afetado por process_turn_start
   - **process_turn_end:**
     - DOT sangramento 4/turno, 3 turnos: process_turn_end 1x → retorna tick com value=4, duracao decrementada para 2. Repetir 3x total → 3 ticks de 4, DOT removido.
     - 2 DOTs de fontes diferentes (bleed A=4, bleed B=4): process_turn_end → retorna 2 ticks, total value 8
     - HOT 5/turno, 3 turnos: process_turn_end 1x → retorna tick HOT com value=5. 3x total → removido.
     - Buff NAO ticka em process_turn_end: aplicar BUFF + process_turn_end → nenhum tick retornado
   - **Consultas:**
     - get_effects retorna todos os efeitos ativos
     - get_effects_by_type(DOT) retorna apenas DOTs
     - has_effect("bleed") retorna True se bleed ativo, False se nao
     - get_effect("bleed") retorna o efeito ou None
     - Entidade sem efeitos: get_effects retorna [], has_effect retorna False
   - **Remocao:**
     - remove_effects_by_tag("bleed"): remove todos os bleeds (incluindo de fontes diferentes)
     - remove_all_negative: remove DEBUFFs e CONTROLs, mantem BUFFs, DOTs, HOTs, SHIELDs. Retorna lista dos removidos.
     - remove_entity: limpa todos os efeitos da entidade

2. Rodar `pytest engine/tests/test_effect_manager.py` e confirmar que todos os testes falham (import errors — nenhum teste deve passar sem implementacao).

**Parar apos criar os testes. Nao implementar logica de producao. Aguardar aprovacao do usuario.**

---

### Grupo 2 — Implementacao (um agente)

**Tarefa:** Implementar o modelo de efeito e o EffectManager. Todos os testes do Grupo 1 devem passar ao final.

1. Criar `engine/models/effect.py`:
   - `class EffectType(Enum)`: DOT, HOT, BUFF, DEBUFF, CONTROL, SHIELD
   - `@dataclass class Effect` (mutavel — sem frozen):
     - `tag: str` — identificador unico do efeito (ex: "bleed", "muralha_de_ferro", "taunt")
     - `effect_type: EffectType`
     - `source_entity_id: str` — quem aplicou o efeito
     - `duration: int` — turnos restantes
     - `value: float = 0.0` — payload numerico (dano/turno para DOT, % para buff, etc.)

2. Criar `engine/systems/effect_manager.py`:
   - Classe `EffectManager`:
     - `__init__(self)` — inicializa dict vazio `_effects: dict[str, list[Effect]]`
     - `apply_effect(self, target_entity_id: str, effect: Effect) -> None`:
       - Para DOT/HOT: chave de stacking = (tag, source_entity_id). Se existe efeito com mesma chave → renova duration e value. Senao, adiciona novo.
       - Para BUFF/DEBUFF/CONTROL/SHIELD: chave de stacking = tag. Se existe efeito com mesmo tag → renova duration e value. Senao, adiciona novo.
     - `get_effects(self, entity_id: str) -> list[Effect]` — retorna copia da lista
     - `get_effects_by_type(self, entity_id: str, effect_type: EffectType) -> list[Effect]` — filtra por tipo
     - `has_effect(self, entity_id: str, tag: str) -> bool` — True se qualquer efeito com esse tag existe
     - `get_effect(self, entity_id: str, tag: str) -> Effect | None` — primeiro efeito com esse tag
     - `remove_effects_by_tag(self, entity_id: str, tag: str) -> int` — remove todos com esse tag, retorna count
     - `remove_all_negative(self, entity_id: str) -> list[Effect]` — remove DEBUFF e CONTROL, retorna removidos
     - `remove_entity(self, entity_id: str) -> None` — limpa todos os efeitos da entidade
     - `process_turn_start(self, entity_id: str) -> list[Effect]`:
       - Itera sobre efeitos BUFF, DEBUFF, CONTROL, SHIELD da entidade
       - Decrementa duration em 1
       - Se duration < 0: remove e adiciona a lista de expirados
       - Retorna lista de efeitos expirados
     - `process_turn_end(self, entity_id: str) -> list[Effect]`:
       - Itera sobre efeitos DOT e HOT da entidade
       - Coleta cada efeito como "tick" (o caller usa .tag, .effect_type, .value)
       - Decrementa duration em 1
       - Se duration <= 0: remove o efeito
       - Retorna lista de efeitos que tickaram (copias snapshot antes do decremento? ou os proprios objetos)

3. Atualizar `engine/models/__init__.py`:
   - Adicionar imports: `from engine.models.effect import Effect, EffectType`
   - Adicionar ao `__all__`

4. Atualizar `engine/systems/__init__.py`:
   - Adicionar imports: `from engine.systems.effect_manager import EffectManager`
   - Adicionar ao `__all__`

5. Rodar `pytest engine/tests/test_effect_manager.py -v` e confirmar que todos os testes passam.

6. Rodar `pytest engine/tests/ -v` para garantir que nao ha regressoes.

---

## Condicao de Conclusao

- Todos os criterios de aceitacao do spec.md satisfeitos
- Todos os testes passam com `pytest engine/tests/ -v`
- Atualizar `.specs/state.md`: status da feature 05 de `pendente` para `concluida`
