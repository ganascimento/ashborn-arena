# Tasks — Feature 20: Setup — Menu e Preparacao

## Antes de Comecar

Ler obrigatoriamente antes de escrever qualquer codigo:

- `CLAUDE.md` — stack, estrutura, convencoes (ingles, sem docstrings, models separadas)
- `.specs/features/20_setup_menu_preparacao/spec.md` — criterios de aceitacao desta feature
- `.specs/prd.md` secoes 2.1, 3.2, 5.1-5.5, 7.1-7.4 — composicao de times, habilidades, atributos, builds, fluxo do jogador
- `.specs/design.md` secoes 3.2-3.3, 3.8, 6.1-6.2 — formulas de atributo/HP, endpoints REST
- `backend/api/schemas/` — schemas Pydantic para mapear os tipos TypeScript
- `frontend/src/main.ts` — setup atual do Phaser
- `frontend/package.json` — dependencias e scripts disponiveis

---

## Plano de Execucao

```
Grupo 1 (TDD)           — testes primeiro, pausa obrigatoria
         |
Grupo 2 + Grupo 3       — paralelos (network client e storage sao independentes)
         |
Grupo 4 + Grupo 5       — paralelos (MenuScene e PreparationScene sao independentes)
         |
Grupo 6                  — wiring: registrar scenes no main.ts, testar fluxo completo
```

Grupos 2 e 3 nao dependem entre si. Grupos 4 e 5 nao dependem entre si, mas dependem de 2 e 3. Grupo 6 depende de todos.

---

### Grupo 1 — Testes (TDD)

**Tarefa:** Escrever testes unitarios para logica de validacao, API client e localStorage manager. Nao implementar producao.

1. Criar `frontend/src/network/__tests__/api-client.test.ts`:
   - Testar `getDefaults()`: mock fetch, verificar que faz GET para `/builds/defaults`, retorna dados tipados
   - Testar `startBattle()`: mock fetch, verificar que faz POST para `/battle/start` com body correto `{ difficulty, team }`, retorna `{ session_id, initial_state }`
   - Testar tratamento de erro: response 400/500 lanca erro com mensagem legivel

2. Criar `frontend/src/network/__tests__/storage.test.ts`:
   - Testar `saveBuild(classId, build)` e `loadBuild(classId)`: salva/carrega de localStorage com chave `build_{classId}`
   - Testar `saveDifficulty(difficulty)` e `loadDifficulty()`: salva/carrega com chave `difficulty`, default `"normal"`
   - Testar `saveLastTeam(classIds)` e `loadLastTeam()`: salva/carrega com chave `last_team`
   - Testar `loadBuild` retorna `null` quando nao ha build salvo

3. Criar `frontend/src/network/__tests__/validation.test.ts`:
   - Testar `validateAttributePoints(points: number[])`: retorna true se length=5, cada valor 0-5, soma=10; false caso contrario
   - Testar `validateAbilitySelection(abilityIds: string[], availableIds: string[])`: retorna true se length=5, sem duplicatas, todos em availableIds
   - Testar `validateTeam(classIds: string[])`: retorna true se 1-3 classes, sem duplicatas; false caso contrario

**Parar apos criar os testes. Nao implementar logica de producao. Aguardar aprovacao do usuario.**

---

### Grupo 2 — REST Client + Types (um agente)

**Tarefa:** Criar o network layer com tipos TypeScript e cliente REST.

1. Criar `frontend/src/network/types.ts` com interfaces mapeando os schemas do backend:
   - `AbilityOut`: `{ id: string, name: string, pa_cost: number, cooldown: number, max_range: number, target: string, damage_base: number, damage_type: string, heal_base: number, elemental_tag: string }`
   - `ClassInfo`: `{ class_id: string, base_attributes: Record<string, number>, hp_base: number, abilities: AbilityOut[] }`
   - `DefaultBuild`: `{ class_id: string, attribute_points: number[], ability_ids: string[] }`
   - `BuildsDefaultsResponse`: `{ classes: ClassInfo[], default_builds: DefaultBuild[] }`
   - `CharacterRequest`: `{ class_id: string, attribute_points: number[], ability_ids: string[] }`
   - `BattleStartRequest`: `{ difficulty: string, team: CharacterRequest[] }`
   - `PositionOut`: `{ x: number, y: number }`
   - `CharacterOut`: `{ entity_id: string, team: string, class_id: string, attributes: Record<string, number>, current_hp: number, max_hp: number, position: PositionOut, abilities: AbilityOut[] }`
   - `MapObjectOut`: `{ entity_id: string, object_type: string, position: PositionOut, hp: number | null, max_hp: number | null, blocks_movement: boolean, blocks_los: boolean }`
   - `InitialBattleState`: `{ grid_size: { width: number, height: number }, map_objects: MapObjectOut[], characters: CharacterOut[], turn_order: string[], current_character: string }`
   - `BattleStartResponse`: `{ session_id: string, initial_state: InitialBattleState }`
   - Chave de atributos no backend usa `"str"`, `"dex"`, `"con"`, `"int_"`, `"wis"` — manter as mesmas chaves no frontend para consistencia com a API

2. Criar `frontend/src/network/api-client.ts`:
   - Constante `API_BASE_URL = "http://localhost:8000"` no topo do arquivo
   - Funcao `async getDefaults(): Promise<BuildsDefaultsResponse>` — GET `${API_BASE_URL}/builds/defaults`
   - Funcao `async startBattle(difficulty: string, team: CharacterRequest[]): Promise<BattleStartResponse>` — POST `${API_BASE_URL}/battle/start` com body JSON
   - Em caso de erro HTTP (status >= 400): ler body da response, lancar Error com mensagem descritiva (incluir status code)
   - Usar `fetch` nativo (sem axios ou bibliotecas extras)

3. Criar `frontend/src/network/validation.ts`:
   - Funcao `validateAttributePoints(points: number[]): boolean` — length 5, cada 0-5, soma 10
   - Funcao `validateAbilitySelection(abilityIds: string[], availableIds: string[]): boolean` — length 5, sem duplicata, todos em availableIds
   - Funcao `validateTeam(classIds: string[]): boolean` — length 1-3, sem duplicata

---

### Grupo 3 — localStorage Manager (um agente)

**Tarefa:** Criar o modulo de persistencia em localStorage.

1. Criar `frontend/src/network/storage.ts`:
   - Interface `SavedBuild`: `{ attribute_points: number[], ability_ids: string[] }`
   - Funcao `saveBuild(classId: string, build: SavedBuild): void` — salva em `build_{classId}`
   - Funcao `loadBuild(classId: string): SavedBuild | null` — carrega de `build_{classId}`, retorna null se nao existir
   - Funcao `saveDifficulty(difficulty: string): void` — salva em chave `difficulty`
   - Funcao `loadDifficulty(): string` — carrega de chave `difficulty`, retorna `"normal"` se nao existir
   - Funcao `saveLastTeam(classIds: string[]): void` — salva em chave `last_team`
   - Funcao `loadLastTeam(): string[]` — carrega de chave `last_team`, retorna `[]` se nao existir
   - Todas as funcoes usam `JSON.stringify`/`JSON.parse` para serializar
   - Tratar `JSON.parse` com try/catch: se o valor salvo for invalido, retornar o default

---

### Grupo 4 — MenuScene (um agente)

**Tarefa:** Implementar a tela inicial com selecao de dificuldade.

1. Criar `frontend/src/scenes/MenuScene.ts`:
   - Classe `MenuScene extends Phaser.Scene` com key `"MenuScene"`
   - Metodo `create()`:
     - Exibir titulo "Ashborn Arena" centralizado no topo (Phaser.GameObjects.Text, fonte grande, cor clara)
     - Carregar dificuldade salva via `loadDifficulty()` de `network/storage.ts`
     - Criar 3 botoes de texto interativos: "Facil", "Normal", "Dificil", centralizados verticalmente com espacamento
     - Botao da dificuldade salva aparece com cor diferente (ex: amarelo vs branco)
     - Cada botao ao clicar:
       - Salva a dificuldade via `saveDifficulty()`
       - Chama `this.scene.start("PreparationScene", { difficulty })` para transicionar
     - Efeito hover nos botoes: mudar cor ou escala ao passar o mouse (setInteractive + pointerover/pointerout)

2. O visual e funcional, nao precisa ser bonito — texto com interatividade basica. Sprites e polimento sao features futuras.

---

### Grupo 5 — PreparationScene (um agente)

**Tarefa:** Implementar a tela de montagem de time com selecao de classes, atributos e habilidades.

1. Criar `frontend/src/scenes/PreparationScene.ts`:
   - Classe `PreparationScene extends Phaser.Scene` com key `"PreparationScene"`
   - Recebe `{ difficulty: string }` do MenuScene via `this.scene.settings.data`

2. Metodo `create()` — fluxo principal:
   - Exibir "Carregando..." enquanto chama `getDefaults()` de `network/api-client.ts`
   - Ao receber resposta, renderizar a interface de montagem

3. Painel de selecao de classes (lado esquerdo ou topo):
   - Exibir 5 botoes de classe: "Guerreiro", "Mago", "Clerigo", "Arqueiro", "Assassino"
   - Clicar em classe adiciona ao time (maximo 3)
   - Classe ja no time fica desabilitada (cor escura, nao clicavel)
   - Exibir time atual como lista com botao "X" para remover

4. Painel de build do personagem selecionado (centro/direita):
   - Aparece ao clicar em um personagem da lista do time
   - **Atributos**: 5 linhas, uma por atributo (FOR, DES, CON, INT, SAB):
     - Label do atributo
     - Valor base da classe (readonly, vem de `ClassInfo.base_attributes`)
     - Botao "-" e "+" para ajustar pontos alocados (0 a 5)
     - Valor final: `base + alocado`
     - Modificador: `final - 5` (exibir com +/-)
   - Exibir "Pontos restantes: X" (10 - soma dos alocados)
   - Botao "+" desabilitado se alocado = 5 ou pontos restantes = 0
   - Botao "-" desabilitado se alocado = 0
   - **HP calculado**: exibir `hp_base + (modificador_CON * 5)` atualizado em tempo real
     - `modificador_CON = (CON_base + pontos_CON) - 5`
   - **Habilidades**: lista de 11 habilidades da classe:
     - Cada habilidade mostra: nome, PA, CD, alcance, tipo dano, dano base, tag elemental
     - Checkbox ou toggle para selecionar/deselecionar
     - Maximo 5 selecionadas — se ja tem 5, bloquear selecao adicional
     - Exibir contador "X/5 selecionadas"

5. Carregar build inicial ao selecionar classe:
   - Primeiro tenta `loadBuild(classId)` do localStorage
   - Se nao existir, usa o `DefaultBuild` correspondente da resposta da API
   - Preenche atributos e habilidades com o build carregado

6. Botao "Confirmar" (parte inferior):
   - Habilitado apenas se `validateTeam` + `validateAttributePoints` + `validateAbilitySelection` passam para todos personagens do time
   - Ao clicar:
     - Salva cada build via `saveBuild(classId, { attribute_points, ability_ids })` no localStorage
     - Salva composicao via `saveLastTeam(classIds)`
     - Chama `startBattle(difficulty, team)` da api-client
     - Se sucesso: `this.scene.start("BattleScene", { session_id, initial_state })` (BattleScene sera criada na feature 21; por enquanto criar um placeholder que exibe o session_id)
     - Se erro: exibe mensagem de erro na tela (texto vermelho), nao crashar

7. Botao "Voltar" (canto superior):
   - `this.scene.start("MenuScene")` para retornar ao menu

---

### Grupo 6 — Wiring e Placeholder (um agente)

**Tarefa:** Registrar todas as scenes no Phaser, criar placeholder para BattleScene, e validar o fluxo completo.

1. Modificar `frontend/src/main.ts`:
   - Remover a `BootScene` placeholder existente
   - Importar `MenuScene`, `PreparationScene`, e `BattlePlaceholderScene`
   - Registrar as 3 scenes na config do Phaser: `scene: [MenuScene, PreparationScene, BattlePlaceholderScene]`
   - Ajustar dimensoes do game se necessario (800x600 pode ser pequeno para a interface de preparacao — considerar 1024x768 ou 1280x720)
   - Manter background escuro (#1a1a2e)

2. Criar `frontend/src/scenes/BattlePlaceholderScene.ts`:
   - Classe `BattlePlaceholderScene extends Phaser.Scene` com key `"BattleScene"`
   - Recebe `{ session_id, initial_state }` do PreparationScene
   - Exibe: "Batalha iniciada! Session: {session_id}" + lista de personagens do initial_state
   - Botao "Voltar ao Menu" que chama `this.scene.start("MenuScene")`
   - Este arquivo sera substituido pela feature 21

3. Iniciar o dev server (`npm run dev` no frontend) e verificar:
   - Menu carrega, 3 botoes de dificuldade funcionam
   - Preparacao carrega dados da API (backend precisa estar rodando)
   - Selecao de classes, atributos e habilidades funciona
   - Confirmar cria batalha e transiciona para placeholder
   - Voltar retorna ao menu
   - localStorage persiste entre recarregamentos

---

## Condicao de Conclusao

- Todos os criterios de aceitacao em spec.md estao satisfeitos
- Todos os testes passam com `npm run test` (vitest)
- Fluxo completo funciona no browser: Menu → Preparacao → Placeholder (com backend rodando)
- localStorage persiste builds e preferencias entre sessoes
- Atualizar `.specs/state.md`: status da feature 20 para `concluida`
