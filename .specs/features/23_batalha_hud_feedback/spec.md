# Feature 23 — Batalha: HUD e Feedback

## Objetivo

Adicionar todos os elementos visuais de feedback que faltam na cena de batalha: barras de HP sobre cada personagem, numeros flutuantes de dano/cura/critico, indicadores de status ativos, highlight de alcance ao selecionar habilidade, e preview de area de efeito. Feature 22 entregou a funcionalidade de acoes e animacoes basicas (flash de cor); esta feature adiciona a camada de informacao visual que permite ao jogador tomar decisoes taticas (quem esta com pouca vida, quem esta debuffado, quais tiles estao no alcance). Completa a experiencia de batalha — apos features 22 e 23, a batalha e totalmente jogavel com feedback adequado.

---

## Referencia nos Specs

- prd.md: secao 7.5 (feedback visual na batalha — lista completa dos elementos esperados)
- prd.md: secao 6.6 (LoS e cobertura — referencia para range de ataques a distancia)
- design.md: secao 2.7 (alcance e tipo de alvo de cada habilidade — max_range, target type)
- design.md: secao 2.6 (efeitos de status — tags e tipos para icones)
- notes.md: "dead characters permanecem no Map" (iterar characters para HP bars deve filtrar status dead), "processEvents defensivo para field names", "arquitetura de animacoes e ability bar"

---

## Arquivos Envolvidos

### Criar

| Arquivo | Descricao |
|---|---|
| `frontend/src/scenes/battle-hud.ts` | Classe BattleHud: HP bars, status icons, floating text |
| `frontend/src/scenes/battle-range-overlay.ts` | Classe BattleRangeOverlay: highlight de alcance, AoE preview |

### Modificar

| Arquivo | Descricao |
|---|---|
| `frontend/src/scenes/battle-animations.ts` | Adicionar callback para floating text durante processamento de eventos de dano/cura |
| `frontend/src/scenes/BattleScene.ts` | Integrar BattleHud + BattleRangeOverlay, rastrear status effects, atualizar overlays em eventos |

---

## Criterios de Aceitacao

### Barras de HP

- [ ] Cada personagem (player e IA) exibe barra de HP abaixo do circulo do personagem
- [ ] Barra com largura proporcional a `current_hp / max_hp`, largura maxima ~48px, altura ~6px
- [ ] Cor da barra: verde (#44ff44) se HP > 50%, amarelo (#ffaa00) se HP entre 25-50%, vermelho (#ff4444) se HP < 25%
- [ ] Fundo da barra em cinza escuro (#333333) para mostrar HP perdido
- [ ] Barra atualiza em tempo real quando HP muda (eventos de dano, cura, DOT, HOT)
- [ ] Personagens com status "knocked_out" exibem barra vermelha (HP negativo = largura 0, barra fica vermelha sem preenchimento)
- [ ] Personagens com status "dead" nao exibem barra (removida junto com o sprite)
- [ ] Barras de HP sao desenhadas ACIMA dos tiles e objetos (depth correto no Phaser)

### Numeros Flutuantes

- [ ] Evento de dano exibe numero vermelho (#ff4444) flutuando acima do alvo: "-{amount}"
- [ ] Evento de dano critico (campo `crit: true` no evento) exibe numero amarelo (#ffd700) maior (fontSize 20px vs 16px): "-{amount}!"
- [ ] Evento de cura exibe numero verde (#44ff44) flutuando acima do alvo: "+{amount}"
- [ ] Evento de DOT (bleed, dot_tick) exibe numero vermelho menor (fontSize 14px): "-{amount}"
- [ ] Numeros flutuam para cima (~30px) e desvanecem (alpha 1→0) em ~800ms, depois sao destruidos
- [ ] Multiplos numeros no mesmo alvo empilham sem sobreposicao (offset Y incremental)

### Indicadores de Status

- [ ] Personagens com efeitos ativos exibem labels de texto acima da barra de HP
- [ ] Tags rastreadas a partir de eventos `effect_applied` (adiciona tag) e `effect_expired` (remove tag)
- [ ] Abreviacoes por tag: bleed→"BLD", poison→"PSN", slow→"SLW", immobilize→"IMB", silence→"SIL", taunt→"TNT", wet→"WET", frozen→"FRZ", burn→"BRN"
- [ ] Cada label com cor por tipo: DOT (vermelho #ff4444), debuff (laranja #ff8800), elemental (azul claro #88ccff), controle (roxo #aa44ff)
- [ ] Labels dispostos horizontalmente acima da barra de HP, fontSize 10px
- [ ] Labels removidos quando efeito expira (evento effect_expired)

### Highlight de Alcance

- [ ] Ao selecionar habilidade na ability bar, tiles dentro do alcance (max_range) sao destacados
- [ ] Alcance calculado como distancia de Chebyshev: `max(|tx - cx|, |ty - cy|) <= ability.max_range` onde (cx, cy) e a posicao do personagem ativo
- [ ] Tiles em alcance recebem overlay semi-transparente azul claro (alpha ~0.25, cor #4488ff)
- [ ] Tiles fora do alcance nao recebem overlay
- [ ] Ao deselecionar habilidade ou cancelar targeting, overlay e removido
- [ ] Overlay nao interfere com cliques nos tiles (nao bloqueia input)
- [ ] Habilidades com target "self" nao mostram overlay de alcance (uso imediato)

### Preview de AoE

- [ ] Para habilidades com target "aoe", ao mover o mouse sobre um tile no alcance, exibe preview da area de efeito
- [ ] Area de efeito: tile central + tiles adjacentes (raio 1 = ate 9 tiles, incluindo diagonais)
- [ ] Preview usa overlay semi-transparente laranja (alpha ~0.3, cor #ff8800)
- [ ] Preview atualiza ao mover o mouse para outro tile
- [ ] Preview desaparece ao mover o mouse para fora do grid ou do alcance
- [ ] Para habilidades com target "adjacent", preview mostra tiles adjacentes ao personagem ativo (nao ao cursor)

---

## Fora do Escopo

- Indicador de LoS bloqueada (requer portar algoritmo Bresenham para TypeScript — servidor valida e retorna erro se alvo invalido)
- Indicador de objetos em chamas (requer rastrear estado de fogo por objeto — nao ha evento dedicado no protocolo atual)
- Sprites, tilesets e assets visuais — MVP usa formas geometricas e texto
- Audio e efeitos sonoros
- Tela de resultado completa (feature 24)
- Animacoes avancadas por tipo de habilidade (projeteis, slash, etc.)
