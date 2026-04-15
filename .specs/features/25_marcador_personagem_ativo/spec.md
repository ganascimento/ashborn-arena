# Feature 25 — Marcador do Personagem Ativo

## Objetivo

Adicionar indicadores visuais claros no grid que identifiquem qual personagem esta com o turno ativo. Atualmente o jogador depende de ler o entity_id no texto superior e associar manualmente a abreviacao da classe — isso e confuso e lento. Esta feature adiciona um anel pulsante e uma seta flutuante no sprite do personagem ativo, alem de traduzir o texto do turno para o nome da classe em portugues.

---

## Referencia nos Specs

- prd.md: secao 7.6 (Marcador do Personagem Ativo)
- design.md: secao 7.1 (spec tecnica do componente visual)

---

## Arquivos Envolvidos

### Criar

| Arquivo | Descricao |
|---|---|
| `frontend/src/scenes/battle-active-marker.ts` | Componente `BattleActiveMarker` — gerencia anel pulsante e seta indicadora sobre o personagem ativo |

### Modificar

| Arquivo | Descricao |
|---|---|
| `frontend/src/scenes/BattleScene.ts` | Instanciar `BattleActiveMarker`, chamar `show(entityId)` ao mudar de turno, traduzir entity_id para nome de classe no turn indicator |

---

## Criterios de Aceitacao

### Visual

- [ ] Personagem ativo exibe um **anel pulsante** ao redor do sprite (cor `0x4488ff` para jogador, `0xff4444` para IA)
- [ ] O anel pulsa com tween de escala yo-yo: 1.0 a 1.15, duracao 600ms, loop infinito
- [ ] Uma **seta triangular** aparece acima do sprite ativo, offset Y = -40px do centro do container
- [ ] A seta flutua com tween yo-yo de Y +-4px, duracao 800ms, loop infinito
- [ ] A cor da seta segue a mesma regra: azul jogador, vermelho IA

### Transicao de Turno

- [ ] Ao mudar de turno, o marcador do personagem anterior e **destruido** e um novo e criado no proximo personagem (transicao instantanea)
- [ ] O marcador aparece corretamente no primeiro turno da batalha (personagem inicial do `initial_state.current_character`)
- [ ] O marcador acompanha corretamente todos os turnos — jogador e IA

### Texto do Turn Indicator

- [ ] O texto "Turno de: {entity_id}" e substituido por "Turno de: {nome_classe}" usando o nome em portugues (Guerreiro, Mago, Clerigo, Arqueiro, Assassino)
- [ ] O subtexto "Seu turno" / "Turno da IA" permanece inalterado

### Cleanup

- [ ] O marcador e destruido no `shutdown()` do BattleScene
- [ ] O marcador e destruido quando `handleBattleEnd` e chamado (antes de transicionar para ResultScene)

---

## Fora do Escopo

- Log de combate (feature 27)
- Painel de detalhes ao clicar em personagem (feature 28)
- Animacao de transicao suave entre marcadores (definido como instantaneo no design.md 7.1)
