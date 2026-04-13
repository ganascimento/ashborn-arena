# Ashborn Arena

Jogo de arena tatico por turnos com IA multi-agente treinada via aprendizado por reforco.

## Stack

### Backend
- **Linguagem**: Python
- **API**: FastAPI
- **ML Framework**: PyTorch
- **Algoritmo IA**: MAPPO (implementacao propria)
- **Ambiente RL**: PettingZoo (API multi-agente)
- **Game Engine**: Python puro (turn-based)

### Frontend
- **Framework**: Phaser 3
- **Linguagem**: TypeScript
- **Persistencia**: localStorage (sem auth, sem banco de dados de usuario)

### Comunicacao
- **REST** (FastAPI): menu, setup de time, builds
- **WebSocket** (FastAPI): batalha — servidor envia acoes da IA uma a uma, frontend anima cada uma antes de receber a proxima

## Estrutura do Projeto

```
ashborn-arena/
├── CLAUDE.md
├── .specs/
│   ├── prd.md                  # O QUE o jogo faz
│   ├── design.md               # COMO funciona (formulas, numeros, arquitetura)
│   └── state.md                # Estado de desenvolvimento
│
├── engine/                     # Game engine (compartilhado entre backend e training)
│   ├── __init__.py
│   ├── models/                 # Domain models: Character, Ability, Map, Effect, Status
│   ├── systems/                # Combat, movement, LoS, initiative, damage pipeline, status
│   └── generation/             # Procedural map generation, biomes
│
├── backend/                    # API (consome engine + inference)
│   ├── api/
│   │   ├── routes/             # REST + WebSocket endpoints
│   │   └── schemas/            # Pydantic request/response schemas
│   ├── inference/              # Carrega .pt files, roda MAPPO inference
│   └── main.py                 # FastAPI entrypoint
│
├── training/                   # RL training (consome engine, roda standalone)
│   ├── environment/            # PettingZoo wrapper sobre engine
│   ├── agents/                 # MAPPO: policy networks, critic, PPO update
│   ├── curriculum/             # Fases de treinamento, self-play pool
│   └── train.py                # Training entrypoint
│
├── frontend/                   # Phaser 3 + TypeScript
│   ├── src/
│   │   ├── scenes/             # Menu, preparation, battle, result
│   │   ├── ui/                 # HUD, ability bar, HP bars, status icons
│   │   └── network/            # REST client + WebSocket client
│   ├── package.json
│   └── index.html
│
└── models/                     # Checkpoints treinados (output de training, input de backend)
    ├── easy/                   # 5 .pt files (1 por classe)
    ├── normal/
    └── hard/
```

**Dependencias entre pacotes:**
- `engine` nao depende de nada (pacote puro de dominio)
- `backend` importa `engine` + `models/`
- `training` importa `engine`, gera `models/`
- `frontend` e independente (se comunica via REST/WS)

## Regras de Negocio

Todas as regras de negocio, formulas, balanceamento e decisoes de design estao em `.specs/`:

- **prd.md**: define o produto (classes, habilidades, atributos, mapa, IA)
- **design.md**: detalha implementacao (formulas de dano, pipeline de resolucao, spec numerica das 47 habilidades, arquitetura da IA)

Nao duplicar regras de negocio no codigo. O codigo deve implementar o que esta nos specs.

## Conceitos-Chave

- **5 classes**: Guerreiro, Mago, Clerigo, Arqueiro, Assassino
- **5 atributos**: FOR, DES, CON, INT, SAB (fator de corte = 5, modificador = atributo - 5)
- **4 PA por turno**, custos inteiros (1-3), cooldown em turnos, sem mana
- **Grid 10x8**, 2D top-down, 2 tiles por PA de movimento
- **47 habilidades** (11 por classe, jogador escolhe 5), spec completa em design.md secao 2.7
- **Cenario destrutivel**: objetos com HP, fogo, arremesso, LoS
- **AoE causa friendly fire**
- **Sistema elemental**: Molhado (gelo) + Eletrico (+50%), Fogo (-30%), Gelo (congela)
- **Knockout**: 0 a -10 HP = caido (revivivel), abaixo de -10 = morto permanente
- **IA**: MAPPO, 1 policy por classe, curriculum learning (1v1 → 3v3), self-play

## Convencoes

- Todo codigo em ingles (variaveis, funcoes, classes, commits)
- Sem docstrings — codigo deve ser autoexplicativo, nao adicionar comentarios de documentacao em metodos
- Comentarios apenas quando a logica nao e obvia
- Documentos em `.specs/` usam portugues sem acentos
- **Models separadas de entrypoints** — domain models ficam em `engine/models/`, API schemas ficam em `backend/api/schemas/`, nunca definir models dentro de routes
- Entrypoints sao finos: recebem request, delegam pra engine/inference, retornam response
