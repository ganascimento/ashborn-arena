# Feature 20 — Setup: Menu e Preparacao

## Objetivo

Implementar as duas primeiras telas do frontend (Phaser 3 + TypeScript): **Menu** (selecao de dificuldade) e **Preparacao** (montagem de time — selecao de classes, distribuicao de atributos, escolha de habilidades). Inclui o REST client para consumir os endpoints do backend (feature 17), persistencia em localStorage, e toda logica de validacao de builds. Esta feature entrega o fluxo completo pre-batalha: o jogador abre o jogo, escolhe dificuldade, monta seu time, confirma e recebe um session_id pronto para conectar ao WebSocket (feature 21).

---

## Referencia nos Specs

- prd.md: secoes 2.1 (composicao de times), 3.2 (sistema de habilidades), 5.1-5.5 (atributos, builds, fator de corte), 7.1-7.4 (interface, localStorage, fluxo do jogador, builds pre-definidos)
- design.md: secoes 3.2-3.3 (composicao de atributos, modificador), 3.8 (formula de HP), 6.1-6.2 (protocolo REST: GET /builds/defaults, POST /battle/start)

---

## Arquivos Envolvidos

### Criar

| Arquivo | Descricao |
|---|---|
| `frontend/src/network/types.ts` | Interfaces TypeScript correspondentes aos schemas da API (ClassInfo, DefaultBuild, AbilityOut, etc.) |
| `frontend/src/network/api-client.ts` | REST client: getDefaults(), startBattle() |
| `frontend/src/network/storage.ts` | localStorage manager: salvar/carregar builds customizados e preferencias |
| `frontend/src/scenes/MenuScene.ts` | Tela inicial: titulo do jogo + selecao de dificuldade |
| `frontend/src/scenes/PreparationScene.ts` | Tela de preparacao: selecao de classes, distribuicao de atributos, escolha de habilidades, confirmacao |

### Modificar

| Arquivo | Descricao |
|---|---|
| `frontend/src/main.ts` | Registrar novas scenes, ajustar config do Phaser (dimensoes, scene flow) |

---

## Criterios de Aceitacao

### Network

- [ ] `getDefaults()` faz GET /builds/defaults e retorna as 5 classes com: base_attributes, hp_base, lista de 11 abilities (com id, name, pa_cost, cooldown, max_range, target, damage_base, damage_type, heal_base, elemental_tag), e 5 default builds (attribute_points + ability_ids)
- [ ] `startBattle(difficulty, team)` faz POST /battle/start com body `{ difficulty, team: [{ class_id, attribute_points, ability_ids }] }` e retorna `{ session_id, initial_state }`
- [ ] API client configura base URL via constante (localhost:8000 em dev)
- [ ] Erros HTTP (4xx, 5xx) sao capturados e exibidos ao jogador como mensagem na tela (nao console.log silencioso)
- [ ] Interfaces TypeScript em types.ts correspondem exatamente aos schemas Pydantic do backend (ClassInfo, DefaultBuild, AbilityOut, BattleStartRequest, BattleStartResponse, CharacterOut, PositionOut, MapObjectOut, InitialBattleState)

### localStorage

- [ ] Salva builds customizados por classe: chave `build_{class_id}` com valor `{ attribute_points: number[], ability_ids: string[] }`
- [ ] Salva preferencia de dificuldade: chave `difficulty` com valor `"easy" | "normal" | "hard"`
- [ ] Salva ultima composicao de time: chave `last_team` com valor `string[]` (lista de class_ids)
- [ ] Ao abrir a tela de preparacao, carrega builds salvos se existirem; senao usa default builds da API
- [ ] Ao confirmar batalha, salva automaticamente os builds customizados e a composicao do time

### Menu (Tela Inicial)

- [ ] Exibe titulo "Ashborn Arena" centralizado
- [ ] Exibe 3 botoes de dificuldade: "Facil", "Normal", "Dificil" — com visual distinto (cor ou destaque)
- [ ] Botao de dificuldade previamente selecionada aparece destacado (carregado do localStorage, default "normal" se nenhum salvo)
- [ ] Ao clicar em uma dificuldade, transiciona para PreparationScene passando `{ difficulty }` como data

### Preparacao (Tela de Montagem de Time)

- [ ] Chama GET /builds/defaults ao entrar na cena e exibe loading enquanto aguarda resposta
- [ ] Painel de selecao de classes: mostra as 5 classes disponiveis com nome e arquetipo
- [ ] Jogador pode adicionar 1 a 3 personagens ao time; classes ja adicionadas ficam desabilitadas (sem duplicata)
- [ ] Jogador pode remover personagens do time antes de confirmar
- [ ] Para cada personagem no time, exibe:
  - Distribuicao de atributos: 5 atributos (FOR, DES, CON, INT, SAB) com controles +/- para alocar pontos
  - Pontos restantes visivel (10 - soma dos alocados)
  - Valores finais visiveis: `atributo_base + pontos_alocados` para cada atributo
  - HP calculado visivel: `hp_base + (modificador_CON * 5)` onde `modificador_CON = (CON_base + pontos_CON) - 5`
  - Controle +/- respeita limites: minimo 0, maximo 5 por atributo, soma total exatamente 10
  - Selecao de habilidades: lista de 11 habilidades disponiveis para a classe, jogador marca 5
  - Cada habilidade mostra: nome, custo PA, cooldown, alcance, tipo de dano, dano base, tag elemental (se houver)
  - Nao permite selecionar mais de 5 habilidades (sexta selecao bloqueada ou deseleciona a anterior)
- [ ] Ao selecionar uma classe, carrega build salvo no localStorage; se nao existir, usa default build da API
- [ ] Botao "Confirmar" habilitado apenas quando:
  - 1-3 personagens no time
  - Cada personagem tem exatamente 10 pontos distribuidos
  - Cada personagem tem exatamente 5 habilidades selecionadas
- [ ] Ao confirmar: salva builds no localStorage, chama POST /battle/start, armazena session_id
- [ ] Apos POST bem-sucedido, transiciona para a proxima cena passando `{ session_id, initial_state }` como data (cena de batalha — feature 21; por enquanto pode ser um placeholder que exibe o session_id)
- [ ] Erro no POST exibe mensagem na tela (ex: "Erro ao iniciar batalha") sem crashar
- [ ] Botao "Voltar" retorna ao MenuScene

---

## Fora do Escopo

- Renderizacao do grid de batalha e sprites dos personagens (feature 21)
- Comunicacao WebSocket (feature 18/21)
- Animacoes de habilidades e feedback visual de combate (feature 22)
- HUD de batalha, barras de HP, icones de status (feature 23)
- Tela de resultado (feature 24)
- Sprites, tilesets, spritesheets, assets visuais (features 21-24)
- Audio e efeitos sonoros
- Responsividade mobile — MVP e desktop/browser
