# Feature 13 — Mecanicas de Combate Avancadas

## Objetivo

Implementar as mecanicas de combate que faltam no BattleState: AoE com friendly fire (Nova Flamejante, Chuva de Flechas, Redemoinho de Aco, Vacuo Arcano), chain damage (Arco Voltaico salta para 2 inimigos a 70%), damage reflect (Retribuicao Divina 30%), damage redirect (Voto de Sacrificio 40%), e untargetable (Veu das Sombras). Meteoro delayed e Armadilha Espinhosa sao excluidos deste MVP por complexidade de estado entre turnos. Esta feature completa o sistema de combate do engine para que o treinamento use o conjunto real de habilidades.

---

## Referencia nos Specs

- design.md: secoes 2.7 (especificacao numerica — Arco Voltaico chain, Retribuicao Divina reflect, Voto de Sacrificio redirect, Veu das Sombras untargetable, habilidades AoE), 3.10 (area de efeito — formatos, friendly fire, esquiva nao se aplica, cadeia so inimigos)
- prd.md: secoes 3.3 (habilidades detalhamento), 6.5 (interacoes com cenario)

---

## Arquivos Envolvidos

### Modificar

- `engine/systems/battle.py` — estender _execute_ability para AoE expansion, chain, reflect, redirect, untargetable
- `engine/tests/test_battle.py` — adicionar testes para as novas mecanicas

---

## Criterios de Aceitacao

### AoE Expansion com Friendly Fire (design.md 3.10)

- [ ] Habilidades com `aoe_radius > 0` e `target == AOE` atingem TODOS os personagens (aliados e inimigos) dentro do raio a partir do tile alvo
- [ ] Nova Flamejante (raio 1): atinge todos em 1 tile do centro alvo, incluindo aliados do caster (friendly fire conforme design.md 3.10)
- [ ] Chuva de Flechas (raio 2): atinge todos em 2 tiles do centro alvo, incluindo aliados
- [ ] Vacuo Arcano (raio 1): aplica silenciar a todos no raio (controle AoE)
- [ ] Esquiva NAO se aplica contra AoE (design.md 3.10: "nao ha como desviar de uma area inteira") — defender_dex_modifier=0 para alvos AoE
- [ ] Bloqueio e resistencia se aplicam individualmente para cada alvo
- [ ] Habilidades com `target == ADJACENT`: atinge todos personagens adjacentes ao caster (Redemoinho de Aco)

### Chain Damage — Arco Voltaico (design.md 2.7)

- [ ] Alvo primario recebe dano completo: base 12, INT * 1.0
- [ ] Salta para ate 2 inimigos adicionais dentro de 2 tiles do alvo primario
- [ ] Dano nos alvos secundarios = 70% do dano causado ao primario (chain_damage_pct=0.70)
- [ ] Cadeia so salta para INIMIGOS (nao aliados — design.md 3.10: excecao ao friendly fire)
- [ ] Se menos de 2 inimigos em range, salta para quantos houver

### Damage Reflect — Retribuicao Divina (design.md 2.7)

- [ ] Efeito "reflect" (BUFF, value=0.30, 2 turnos) ja e aplicado pelo EffectManager
- [ ] Quando personagem com reflect ativo recebe dano, 30% do dano e refletido ao atacante
- [ ] Reflect e processado em `_resolve_damage` apos calcular dano final
- [ ] Dano refletido ignora defesas do atacante (dano fixo)
- [ ] Reflect nao se aplica a DOT damage (apenas dano direto de ataques/habilidades)

### Damage Redirect — Voto de Sacrificio (design.md 2.7)

- [ ] Efeito "redirect" (BUFF, value=0.40, 2 turnos, area_allies radius=2) ja e aplicado
- [ ] Quando aliado dentro de 2 tiles do caster recebe dano, 40% e redirecionado ao caster
- [ ] Aliado recebe apenas 60% do dano original
- [ ] Caster recebe os 40% redirecionados (pode matar/knockout o caster)
- [ ] Se caster esta KNOCKED_OUT ou DEAD, redirect nao funciona

### Untargetable — Veu das Sombras (design.md 2.7)

- [ ] Efeito "untargetable" (BUFF, 1 turno) ja e aplicado
- [ ] Personagem com untargetable nao pode ser selecionado como alvo de ataques/habilidades
- [ ] Action masking: excluir personagens untargetable da lista de alvos validos
- [ ] AoE que inclui tile do personagem untargetable: pula esse personagem
- [ ] Untargetable nao protege de DOT/efeitos ja aplicados

---

## Fora do Escopo

- Meteoro delayed (marcacao + resolucao no proximo turno) — requer tracking de estado entre turnos no BattleState, complexidade alta para o MVP
- Armadilha Espinhosa (colocar trap no tile, ativar quando pisada) — requer tracking de objetos temporarios no grid
- Toque Peconhento (proximos 3 ataques aplicam veneno) — requer contador de ataques por buff
- Olho do Predador / Veu das Sombras bonus dano proximo ataque — requer consumo de buff no proximo ataque
- Alcance Supremo (+2 tiles range) — requer modificar action masking para range dinamico
