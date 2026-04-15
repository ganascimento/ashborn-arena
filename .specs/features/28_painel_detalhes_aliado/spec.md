# Feature 28 — Painel de Detalhes do Personagem

## Objetivo

Permitir que o jogador clique em um personagem no grid para ver informacoes detalhadas: HP numerico, PA restante, atributos, efeitos ativos com duracao, e cooldowns de habilidades. Isso e essencial para formar estrategia — atualmente so e possivel ver a barrinha de HP e abreviacoes de status. Aliados mostram painel completo; inimigos mostram apenas HP e efeitos.

---

## Referencia nos Specs

- prd.md: secao 7.8 (Painel de Detalhes do Aliado)
- design.md: secao 7.4 (spec tecnica do componente, layouts, dados)

---

## Arquivos Envolvidos

### Criar

| Arquivo | Descricao |
|---|---|
| `frontend/src/scenes/battle-detail-panel.ts` | Componente `CharacterDetailPanel` — overlay com informacoes do personagem |

### Modificar

| Arquivo | Descricao |
|---|---|
| `frontend/src/scenes/BattleScene.ts` | Instanciar painel, detectar clique em sprite de personagem, abrir/fechar painel |
| `frontend/src/network/types.ts` | Verificar que `CharacterOut.attributes` e `AbilityOut` ja contem os dados necessarios (nao deve precisar de mudanca) |

---

## Criterios de Aceitacao

### Ativacao

- [ ] Clicar em um **personagem aliado** no grid abre o painel completo
- [ ] Clicar em um **personagem inimigo** no grid abre o painel reduzido
- [ ] Clicar **fora do painel** fecha o painel
- [ ] Pressionar **ESC** fecha o painel
- [ ] Clicar em **outro personagem** com painel aberto fecha o atual e abre o novo
- [ ] **Nao** abre painel para personagens com status `dead`

### Layout Aliado (Painel Completo)

- [ ] Exibe nome da classe em portugues (Guerreiro, Mago, etc.)
- [ ] Exibe **HP atual / HP maximo** numerico (ex: "HP: 45/85")
- [ ] Exibe **PA restante / 4** se o personagem e o ativo no turno atual (ex: "PA: 2/4"); caso contrario, nao exibe PA
- [ ] Exibe os **5 atributos finais** (base + alocacao) com modificador: "FOR: 13 (+8)", "DES: 6 (+1)", etc.
- [ ] Exibe lista de **efeitos ativos** com tag e duracao restante em turnos (ex: "Sangramento (2 turnos)")
- [ ] Se nao ha efeitos ativos, exibe "Nenhum" ou omite a secao
- [ ] Exibe lista de **5 habilidades** com estado de cooldown: "OK" se disponivel, "CD: N" se em cooldown
- [ ] Borda do painel em azul (`0x4488ff`)

### Layout Inimigo (Painel Reduzido)

- [ ] Exibe nome da classe em portugues
- [ ] Exibe **HP atual / HP maximo** numerico
- [ ] Exibe lista de **efeitos ativos** com tag e duracao
- [ ] **Nao** exibe PA, atributos ou habilidades
- [ ] Borda do painel em vermelho (`0xff4444`)

### Visual

- [ ] Painel usa depth 300+ (acima de todos os outros elementos)
- [ ] Background solido `0x1a1a2e`
- [ ] Texto monospace, cores claras legiveis
- [ ] Painel posicionado centralizado na tela ou proximo ao personagem clicado (nao pode sair da tela)

### Interacao com Gameplay

- [ ] O painel **nao bloqueia** acoes de jogo — o jogador pode fechar e continuar jogando
- [ ] Abrir o painel **nao** consome PA ou afeta o estado do jogo
- [ ] O painel e automaticamente fechado ao iniciar uma animacao (quando `isAnimating` se torna true)

### Cleanup

- [ ] O painel e destruido no `shutdown()` do BattleScene
- [ ] O painel e fechado/destruido no `handleBattleEnd`

---

## Fora do Escopo

- Exibir habilidades do inimigo (informacao estrategica limitada por design)
- Exibir atributos do inimigo
- Tooltip ao passar o mouse sobre habilidades no painel (nome, descricao, stats)
- Animacao de abertura/fechamento do painel
