# Feature 24 — Resultado

## Objetivo

Implementar a tela de resultado que e exibida apos o termino da batalha. Substitui o ResultPlaceholderScene da feature 21 com uma tela completa que exibe vitoria ou derrota, um resumo da batalha mostrando o status final de cada personagem de ambos os times, e botao para retornar ao menu. Esta e a ultima feature do frontend — apos ela, o ciclo completo Menu → Preparacao → Batalha → Resultado → Menu esta funcional.

---

## Referencia nos Specs

- prd.md: secao 7.3 (fluxo do jogador — tela de resultado: "Vitoria ou derrota, resumo da batalha")
- design.md: secao 6.2 (protocolo WebSocket — mensagem `battle_end` com campo `result`)
- notes.md: "BattlePlaceholderScene com key BattleScene — Feature 24 deve substituir ResultPlaceholderScene mantendo key ResultScene"

---

## Arquivos Envolvidos

### Criar

| Arquivo | Descricao |
|---|---|
| `frontend/src/scenes/ResultScene.ts` | Cena de resultado: banner vitoria/derrota, resumo da batalha, navegacao |

### Modificar

| Arquivo | Descricao |
|---|---|
| `frontend/src/scenes/BattleScene.ts` | Passar dados de resumo dos personagens ao transicionar para ResultScene |
| `frontend/src/main.ts` | Substituir import de ResultPlaceholderScene por ResultScene |

### Remover

| Arquivo | Descricao |
|---|---|
| `frontend/src/scenes/ResultPlaceholderScene.ts` | Substituido por ResultScene |

---

## Criterios de Aceitacao

### Banner de Resultado

- [ ] Exibe "VITORIA!" em verde (#44ff44) centralizado no topo (y ~150) se resultado e "victory"
- [ ] Exibe "DERROTA!" em vermelho (#ff4444) centralizado no topo (y ~150) se resultado e "defeat"
- [ ] Texto em fontSize 52px, fontFamily monospace, bold

### Resumo da Batalha

- [ ] Exibe dois blocos lado a lado: "Seu Time" (esquerda, x ~400) e "Time da IA" (direita, x ~880)
- [ ] Titulo de cada bloco em fontSize 22px, cor #e0e0e0
- [ ] Cada personagem listado com: nome da classe em portugues (Guerreiro/Mago/Clerigo/Arqueiro/Assassino) e status final
- [ ] Status exibido como texto colorido: "Vivo" em verde (#44ff44) para status "active", "Caido" em amarelo (#ffaa00) para "knocked_out", "Morto" em vermelho (#ff4444) para "dead"
- [ ] Personagens listados verticalmente com spacing ~40px entre cada

### Dados Passados pelo BattleScene

- [ ] BattleScene.handleBattleEnd passa ao ResultScene: `{ result, characters: [{ class_id, team, status }] }` contendo todos os personagens com status final
- [ ] Dados extraidos do `characters` Map do BattleScene no momento do battle_end

### Navegacao

- [ ] Botao "Voltar ao Menu" centralizado na parte inferior (y ~600)
- [ ] Botao interativo com hover (cor muda para branco, scale 1.1)
- [ ] Clique no botao transiciona para MenuScene
- [ ] Scene key mantida como "ResultScene" (compatibilidade com BattleScene.handleBattleEnd)

### Wiring

- [ ] main.ts importa ResultScene em vez de ResultPlaceholderScene
- [ ] Array de scenes em Phaser.Game atualizado: `[MenuScene, PreparationScene, BattleScene, ResultScene]`
- [ ] ResultPlaceholderScene.ts removido do projeto
- [ ] Build compila sem erros: `npx tsc --noEmit`

---

## Fora do Escopo

- Estatisticas detalhadas da batalha (dano total, curas, kills por personagem)
- Replay ou log de acoes
- Leaderboard ou historico de batalhas
- Botao "Jogar Novamente" direto (jogador usa "Voltar ao Menu" e inicia nova batalha pelo fluxo normal)
- Animacoes de entrada ou transicoes entre cenas
- Audio e efeitos sonoros
