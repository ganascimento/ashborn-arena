# Feature 27 — Log de Combate e Ritmo da IA

## Objetivo

Adicionar um painel de log de combate que registra todas as acoes da batalha em texto legivel, e aumentar o delay entre acoes da IA para que o jogador consiga acompanhar visualmente o que esta acontecendo. Atualmente as acoes da IA passam rapido demais e nao ha registro textual do que aconteceu — o jogador perde informacao critica para tomar decisoes taticas.

---

## Referencia nos Specs

- prd.md: secao 7.7 (Log de Combate — requisitos de UX e ritmo da IA)
- design.md: secao 7.3 (spec tecnica do componente, mapeamento de eventos, layout)

---

## Arquivos Envolvidos

### Criar

| Arquivo | Descricao |
|---|---|
| `frontend/src/scenes/battle-combat-log.ts` | Componente `BattleCombatLog` — painel de log com scroll, FIFO 50 entradas |

### Modificar

| Arquivo | Descricao |
|---|---|
| `frontend/src/scenes/BattleScene.ts` | Instanciar `BattleCombatLog`, alimentar log a cada evento processado, adicionar delay de 800ms apos animacoes da IA |

---

## Criterios de Aceitacao

### Log Visual

- [ ] Painel de log visivel na lateral direita da tela de batalha (x: 700, abaixo da ability bar)
- [ ] Background semi-transparente (`0x1a1a2e`, alpha 0.85), ~300px largura, ~200px altura
- [ ] Texto monospace 12px, cor `#cccccc`
- [ ] Log exibe as entradas mais recentes na parte inferior (scroll automatico)
- [ ] Maximo de 50 entradas — entradas mais antigas sao removidas (FIFO)
- [ ] O log persiste durante toda a batalha (nao limpa entre turnos)

### Mapeamento de Eventos

- [ ] `move` / `ability_movement` → "{Classe} moveu para ({x},{y})"
- [ ] `basic_attack` → "{Classe} atacou {Alvo} — {dano} dano"
- [ ] `ability` → "{Classe} usou {nome_habilidade} em {Alvo} — {dano} dano" ou "{cura} cura"
- [ ] `aoe_hit` → "{Alvo} recebeu {dano} dano [AoE]"
- [ ] `bleed` / `dot_tick` → "{Classe} sofreu {dano} dano ({tipo_efeito})"
- [ ] `heal` / `hot_tick` → "{Classe} recuperou {cura} HP"
- [ ] `knocked_out` → "{Classe} foi nocauteado!"
- [ ] `death` → "{Classe} morreu!"
- [ ] `effect_applied` → "{Classe} recebeu efeito: {tag}"
- [ ] `effect_expired` → "Efeito {tag} expirou em {Classe}"
- [ ] Nomes de classe exibidos em portugues (Guerreiro, Mago, etc.)
- [ ] Para resolver entity_id → nome de classe, usar o `characters` map do BattleScene (entry.data.class_id → CLASS_DISPLAY)

### Ritmo da IA

- [ ] Apos cada `ai_action` ser animada, aguardar **800ms adicionais** antes de enviar `ready` ao servidor
- [ ] O delay e aplicado **apos** a animacao completar (nao durante)
- [ ] O delay **nao** se aplica a acoes do jogador (apenas IA)

### Cleanup

- [ ] O log e destruido no `shutdown()` do BattleScene
- [ ] O log e destruido no `handleBattleEnd`

---

## Fora do Escopo

- Possibilidade de rolar o log para cima com mouse/scroll (MVP mostra apenas as ultimas entradas visiveis)
- Filtros de log (mostrar apenas dano, apenas cura, etc.)
- Exportar log apos a batalha
- Painel de detalhes do personagem (feature 28)
