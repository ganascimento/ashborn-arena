# Feature 21 — Batalha: Grid e Rendering

## Objetivo

Implementar a cena de batalha com renderizacao do grid 10x8, posicionamento visual de personagens e objetos de mapa, cliente WebSocket para comunicacao com o servidor, e fluxo basico de turnos (receber/enviar mensagens, alternar entre turno do jogador e turno da IA). Esta feature substitui o BattlePlaceholderScene da feature 20 e entrega o esqueleto funcional da batalha: o jogador ve o campo, pode mover personagens, fazer ataque basico, encerrar turno, e observar a IA jogar. Features 22 (acoes e animacoes) e 23 (HUD e feedback) adicionam polish sobre esta base.

---

## Referencia nos Specs

- prd.md: secoes 6.1-6.6 (grid, movimentacao, spawn zones, objetos, LoS), 7.3 (fluxo do jogador — tela de batalha), 7.5 (feedback visual basico)
- design.md: secoes 4.1-4.2 (grid, objetos interativos), 6.2 (protocolo WebSocket — mensagens, ready/next, fluxo de turno da IA)
- notes.md: "WebSocket — protocolo ready/next", "WebSocket — extensoes ao protocolo de design.md 6.2", "Frontend — BattlePlaceholderScene com key BattleScene"

---

## Arquivos Envolvidos

### Criar

| Arquivo | Descricao |
|---|---|
| `frontend/src/network/ws-client.ts` | Cliente WebSocket: conecta, envia acoes, recebe mensagens, protocolo ready |
| `frontend/src/network/__tests__/ws-client.test.ts` | Testes unitarios do WS client |
| `frontend/src/scenes/BattleScene.ts` | Cena principal de batalha: grid, entidades, turnos, integracao WS |
| `frontend/src/scenes/ResultPlaceholderScene.ts` | Placeholder para tela de resultado (substituido pela feature 24) |

### Modificar

| Arquivo | Descricao |
|---|---|
| `frontend/src/network/types.ts` | Adicionar interfaces para mensagens WS (server→client e client→server) |
| `frontend/src/main.ts` | Substituir import de BattlePlaceholderScene por BattleScene, adicionar ResultPlaceholderScene |

### Remover

| Arquivo | Descricao |
|---|---|
| `frontend/src/scenes/BattlePlaceholderScene.ts` | Substituido por BattleScene |

---

## Criterios de Aceitacao

### WebSocket Client

- [ ] Conecta a `ws://localhost:8000/battle/{session_id}` ao iniciar a cena
- [ ] Parseia todas as mensagens do servidor: `turn_start`, `action_result`, `ai_action`, `turn_end`, `skip_event`, `battle_end`, `error`
- [ ] Envia mensagens de acao do jogador no formato correto: `{ type: "action", character, action: "move", target: [x, y] }` para movimento, `{ type: "action", character, action: "basic_attack", target: [x, y] }` para ataque basico, `{ type: "action", character, action: "end_turn" }` para encerrar turno
- [ ] Envia `{ type: "ready" }` apos processar cada mensagem `ai_action` recebida (protocolo ready/next — notes.md)
- [ ] Exibe mensagem de erro na tela se a conexao WS falhar ou cair (nao crashar)
- [ ] Fecha a conexao WS ao sair da cena (cleanup)
- [ ] Interfaces TypeScript adicionadas em types.ts para todas as mensagens WS (ServerMessage, ClientMessage)
- [ ] Usa `readyState === 1` (nao `WebSocket.OPEN`) para verificar conexao aberta (happy-dom compat — notes.md)

### Grid

- [ ] Grid 10x8 renderizado com tiles coloridos em padrao alternado (claro/escuro) — tile size 64px, area do grid 640x512px
- [ ] Grid posicionado no lado esquerdo do canvas (x=32, y=104), reservando ~600px de largura a direita para HUD (feature 23)
- [ ] Clique em um tile retorna as coordenadas (x, y) corretas do grid (0-indexed: x 0-9, y 0-7)
- [ ] Tiles fora do grid nao respondem a clique

### Entidades — Personagens

- [ ] Personagens renderizados como circulos coloridos no centro do tile correspondente: time do jogador em azul (#4488ff), time da IA em vermelho (#ff4444)
- [ ] Cada personagem exibe abreviacao da classe dentro do circulo (G/M/C/A/As para Guerreiro/Mago/Clerigo/Arqueiro/Assassino)
- [ ] Personagens caidos (knocked_out) exibidos com opacidade reduzida (alpha 0.4)
- [ ] Personagens mortos removidos do grid
- [ ] Posicao do personagem atualiza no grid quando o servidor envia evento de movimento (action_result ou ai_action com action "move")

### Entidades — Objetos de Mapa

- [ ] Objetos de mapa renderizados como retangulos coloridos no tile correspondente: crate/barrel (marrom #8B4513), tree (verde escuro #228B22), rock (cinza #808080), bush (verde claro #90EE90), puddle (azul claro #87CEEB)
- [ ] Objetos que bloqueiam movimento (blocks_movement=true) tem borda branca fina para distinguir de objetos nao-bloqueantes
- [ ] Objetos destruidos (HP chega a 0 em eventos) sao removidos do grid

### Fluxo de Turnos

- [ ] Indicador de turno no topo exibe: "Turno de: {entity_id}" com cor azul (jogador) ou vermelha (IA)
- [ ] No turno do jogador: exibe texto "Seu turno" e botao "Encerrar Turno"
- [ ] Botao "Encerrar Turno" envia `{ type: "action", character: current, action: "end_turn" }` via WS
- [ ] No turno do jogador: clicar em tile vazio envia acao de movimento `{ type: "action", character: current, action: "move", target: [x, y] }`
- [ ] No turno do jogador: clicar em tile com inimigo envia acao de ataque basico `{ type: "action", character: current, action: "basic_attack", target: [x, y] }`
- [ ] No turno da IA: recebe ai_action, atualiza estado visual, envia ready, repete ate turn_end
- [ ] Ao receber turn_end: atualiza indicador de turno para o proximo personagem (`next` field)
- [ ] Ao receber skip_event: pula personagens inativos sem intervencao do jogador
- [ ] Ao receber battle_end: transiciona para cena de resultado passando `{ result }` (ResultScene — feature 24; por enquanto placeholder que exibe "Vitoria!" ou "Derrota!")

### Gerenciamento de Estado

- [ ] Cena rastreia posicoes dos personagens a partir do initial_state e atualiza com eventos de movimento
- [ ] Cena rastreia HP dos personagens a partir do initial_state (atualizacao de HP sera integrada com eventos na feature 22/23 — por enquanto exibe HP inicial)
- [ ] Cena rastreia status de personagens: ativo, knocked_out, dead (a partir de eventos recebidos)
- [ ] Cena rastreia objetos de mapa e remove destruidos
- [ ] processEvents aceita field names flexiveis do backend: entity/character, to/position, amount/damage; posicoes como [x,y] ou {x,y} (notes.md)

---

## Fora do Escopo

- Selecao de habilidades pelo jogador e UI de targeting completo (feature 22)
- Animacoes de ataque, projeteis e efeitos visuais de habilidades (feature 22)
- Barras de HP sobre personagens (feature 23)
- Icones de status ativos (feature 23)
- Numeros flutuantes de dano/cura (feature 23)
- Highlight de tiles de alcance ao selecionar habilidade (feature 23)
- Preview de area de efeito (feature 23)
- Indicador de LoS bloqueada (feature 23)
- Barra de habilidades e contador de PA (feature 23)
- Tela de resultado completa (feature 24)
- Sprites, tilesets e assets visuais — MVP usa formas geometricas coloridas
- Audio e efeitos sonoros
