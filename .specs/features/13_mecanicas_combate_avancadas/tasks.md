# Tasks — Feature 13: Mecanicas de Combate Avancadas

## Antes de Comecar

Ler obrigatoriamente antes de escrever qualquer codigo:

- `CLAUDE.md` — stack, estrutura do projeto, convencoes
- `.specs/features/13_mecanicas_combate_avancadas/spec.md` — criterios de aceitacao desta feature
- `.specs/notes.md` — limitacoes conhecidas do BattleState
- `.specs/design.md` secoes 2.7 (habilidades com AoE, chain, reflect, redirect, untargetable), 3.10 (regras de AoE — friendly fire, esquiva, cadeia)
- `engine/systems/battle.py` — BattleState (sera modificado)
- `engine/models/ability.py` — Ability, AbilityTarget, BuffDef (aoe_radius, friendly_fire, chain_targets, chain_damage_pct)
- `engine/models/grid.py` — Grid.get_adjacent_positions
- `engine/systems/effect_manager.py` — EffectManager (para checar reflect/redirect/untargetable)
- `training/environment/actions.py` — compute_action_mask (para untargetable)

---

## Plano de Execucao

2 grupos sequenciais. Grupo 1 e a fase TDD. Grupo 2 e a implementacao.

- **Grupo 1**: testes para AoE, chain, reflect, redirect, untargetable. Parar apos criar os testes.
- **Grupo 2**: implementar tudo no BattleState + atualizar action masking. Rodar testes.

Dependencia: Grupo 2 so executa apos aprovacao dos testes do Grupo 1.

---

### Grupo 1 — Testes (TDD)

**Tarefa:** Criar testes para todas as mecanicas de combate avancadas no BattleState.

1. Adicionar testes em `engine/tests/test_battle.py`:
   - **AoE Expansion:**
     - Setup: 3 personagens adjacentes ao tile alvo. Usar habilidade AoE raio 1 no tile. Todos 3 recebem dano.
     - Friendly fire: aliado do caster na area recebe dano tambem.
     - Esquiva NAO se aplica contra AoE (verificar que dano e sempre aplicado, sem evasion).
     - Habilidade ADJACENT (Redemoinho): atinge todos adjacentes ao caster.
   - **Chain (Arco Voltaico):**
     - Setup: alvo primario + 2 inimigos dentro de 2 tiles. Primario recebe dano cheio, secundarios recebem 70%.
     - So salta para inimigos (nao aliados).
     - Se so 1 inimigo em range, so salta para 1.
     - Se 0 inimigos em range, so o primario recebe.
   - **Reflect (Retribuicao Divina):**
     - Personagem com efeito "reflect" recebe ataque. 30% do dano e aplicado ao atacante.
     - Reflect nao se aplica a DOT.
   - **Redirect (Voto de Sacrificio):**
     - Aliado com caster de redirect proximo (2 tiles) recebe ataque. Aliado leva 60%, caster leva 40%.
     - Se caster knocked_out, redirect nao funciona.
   - **Untargetable (Veu das Sombras):**
     - Personagem com "untargetable" nao aparece como alvo valido no action masking.
     - AoE pula personagem untargetable.

2. Rodar testes e confirmar que todos falham.

**Parar apos criar os testes. Nao implementar logica de producao. Aguardar aprovacao do usuario.**

---

### Grupo 2 — Implementacao (um agente)

**Tarefa:** Implementar AoE, chain, reflect, redirect e untargetable no BattleState e action masking.

1. Modificar `engine/systems/battle.py` — `_execute_ability`:
   - **AoE expansion**: quando `ability.aoe_radius > 0` e `ability.target in (AOE, ADJACENT)`:
     - Calcular todos tiles dentro do raio a partir do tile alvo (ou posicao do caster para ADJACENT)
     - Encontrar todos personagens nesses tiles (aliados e inimigos se friendly_fire=True)
     - Para cada personagem encontrado: resolver dano com `defender_dex_modifier=0` (sem esquiva em AoE)
     - Para controle AoE (Vacuo Arcano): aplicar efeitos a todos no raio
   - **Chain (Arco Voltaico)**: quando `ability.chain_targets > 0`:
     - Resolver dano no alvo primario normalmente
     - Encontrar ate `chain_targets` inimigos (nao aliados) dentro de 2 tiles do primario
     - Para cada alvo secundario: resolver dano com `damage * chain_damage_pct`

2. Modificar `engine/systems/battle.py` — `_resolve_damage`:
   - **Reflect**: apos calcular dano final, checar se defensor tem efeito "reflect":
     - Se sim: `reflected = int(final_damage * reflect_value)`, aplicar ao atacante via `attacker.apply_damage(reflected)`
     - Registrar evento de reflect
   - **Redirect**: antes de aplicar dano ao defensor, checar se ha caster com efeito "redirect" proximo:
     - Iterar efeitos "redirect" de todos personagens (source_entity_id = quem castou)
     - Se caster alive e dentro de radius (2 tiles) do defensor: `redirected = int(damage * redirect_value)`, defensor recebe `damage - redirected`, caster recebe `redirected`
     - Registrar evento de redirect

3. Modificar `engine/systems/battle.py` — adicionar helper `_get_characters_in_radius(center, radius, include_allies, caster_team)`:
   - Retorna lista de entity_ids dentro do raio a partir do center tile
   - Filtra por team se necessario

4. Modificar `engine/systems/battle.py` — `_execute_ability` e `_resolve_damage`:
   - **Untargetable**: antes de resolver dano direto, checar se defensor tem efeito "untargetable". Se sim, pular.
   - Em AoE expansion: pular personagens untargetable.

5. Modificar `training/environment/actions.py` — `compute_action_mask`:
   - Ao listar alvos validos para BASIC_ATTACK e ABILITY (SINGLE_ENEMY/SINGLE_ALLY):
     - Excluir personagens com efeito "untargetable" da lista

6. Rodar `pytest engine/tests/test_battle.py -v`.

7. Rodar `pytest engine/tests/ training/tests/ -v` para zero regressoes.

---

## Condicao de Conclusao

- Todos os criterios de aceitacao do spec.md satisfeitos
- Todos os testes passam com `pytest engine/tests/ training/tests/ -v`
- Atualizar `.specs/state.md`: status da feature 13 de `pendente` para `concluida`
- Atualizar `.specs/notes.md`: remover habilidades implementadas da lista de limitacoes
