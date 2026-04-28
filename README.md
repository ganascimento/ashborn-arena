<div align="center">

# <img src="https://em-content.zobj.net/source/apple/391/crossed-swords_2694-fe0f.png" width="32" /> Ashborn Arena

**Turn-based tactical RPG with multi-agent AI trained via reinforcement learning**

<!-- TODO: replace with actual gameplay GIF -->
<!-- ![Gameplay](docs/gameplay.gif) -->

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5+-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Phaser](https://img.shields.io/badge/Phaser-3.80+-8B5CF6?style=flat-square&logoColor=white)](https://phaser.io)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)]()
[![Tests](https://img.shields.io/badge/Tests-878_passing-44cc11?style=flat-square&logo=testinglibrary&logoColor=white)]()
[![Features](https://img.shields.io/badge/Features-29%2F29_done-44cc11?style=flat-square)]()
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

</div>

---

## <img src="https://em-content.zobj.net/source/apple/391/scroll_1f4dc.png" width="20" /> About

Ashborn Arena is a browser-based tactical RPG where you assemble a team of up to 3 characters and battle against an AI opponent trained entirely through self-play reinforcement learning. No scripted behaviors, no hardcoded heuristics for difficulty — the AI learned to play the game from scratch using **MAPPO** (Multi-Agent Proximal Policy Optimization).

The game features 5 unique classes, 47 abilities with elemental combos, destructible environments, and a deep build system — all on a 10x8 grid with line-of-sight mechanics and projectile interception.

---

## <img src="https://em-content.zobj.net/source/apple/391/sparkles_2728.png" width="20" /> Features

| | Feature | Details |
|:---:|---|---|
| <img src="https://em-content.zobj.net/source/apple/391/person-fencing_1f93a.png" width="18" /> | **5 unique classes** | Warrior, Mage, Cleric, Archer, Assassin — each with distinct identity and 11 abilities |
| <img src="https://em-content.zobj.net/source/apple/391/fire_1f525.png" width="18" /> | **47 abilities** | 8 shared across classes, elemental combos (Fire, Ice, Electric, Poison), AoE with friendly fire |
| <img src="https://em-content.zobj.net/source/apple/391/bar-chart_1f4ca.png" width="18" /> | **Deep build system** | 5 attributes (STR, DEX, CON, INT, WIS), 10 distributable points, pick 5 of 11 abilities per class |
| <img src="https://em-content.zobj.net/source/apple/391/dagger_1f5e1-fe0f.png" width="18" /> | **Tactical combat** | 4 action points per turn, cooldown management, knockout/revival system, opportunity attacks |
| <img src="https://em-content.zobj.net/source/apple/391/collision_1f4a5.png" width="18" /> | **Destructible map** | Throwable objects, fire mechanics, line-of-sight cover, projectile interception on blocking objects |
| <img src="https://em-content.zobj.net/source/apple/391/robot_1f916.png" width="18" /> | **Multi-agent RL** | MAPPO-trained AI with per-class policy networks, 3 difficulty levels from training checkpoints |
| <img src="https://em-content.zobj.net/source/apple/391/globe-with-meridians_1f310.png" width="18" /> | **Zero friction** | Browser-based, no login, builds saved in localStorage, auto-battle mode (AI vs AI) |

---

## <img src="https://em-content.zobj.net/source/apple/391/hammer-and-wrench_1f6e0-fe0f.png" width="20" /> Tech Stack

### <img src="https://em-content.zobj.net/source/apple/391/gear_2699-fe0f.png" width="16" /> Backend

| Technology | Role |
|---|---|
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" width="16" /> **Python 3.11+** | Game engine, API, training pipeline |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/fastapi/fastapi-original.svg" width="16" /> **FastAPI** | REST API (menu, builds) + WebSocket (real-time battle) |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/pytorch/pytorch-original.svg" width="16" /> **PyTorch** | MAPPO neural networks — training and inference |
| <img src="https://em-content.zobj.net/source/apple/391/parrot_1f99c.png" width="16" /> **PettingZoo** | Multi-agent RL environment wrapper |

### <img src="https://em-content.zobj.net/source/apple/391/desktop-computer_1f5a5-fe0f.png" width="16" /> Frontend

| Technology | Role |
|---|---|
| <img src="https://em-content.zobj.net/source/apple/391/joystick_1f579-fe0f.png" width="16" /> **Phaser 3** | 2D game rendering, animations, input handling |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/typescript/typescript-original.svg" width="16" /> **TypeScript** | Type-safe frontend code |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/vitejs/vitejs-original.svg" width="16" /> **Vite** | Build tool and dev server |

### <img src="https://em-content.zobj.net/source/apple/391/package_1f4e6.png" width="16" /> Infrastructure

| Technology | Role |
|---|---|
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/docker/docker-original.svg" width="16" /> **Docker + Compose** | Containerized deployment (backend + frontend) |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/nginx/nginx-original.svg" width="16" /> **Nginx** | Static file serving for production frontend |
| <img src="https://em-content.zobj.net/source/apple/391/floppy-disk_1f4be.png" width="16" /> **localStorage** | Client-side persistence (no database) |

---

## <img src="https://em-content.zobj.net/source/apple/391/brain_1f9e0.png" width="20" /> AI System — MAPPO

The AI uses **Multi-Agent Proximal Policy Optimization (MAPPO)**, a state-of-the-art multi-agent reinforcement learning algorithm built on the **Centralized Training, Decentralized Execution (CTDE)** paradigm.

### <img src="https://em-content.zobj.net/source/apple/391/thinking-face_1f914.png" width="16" /> Why MAPPO?

- **Multi-agent by design** — handles team coordination natively (up to 3v3)
- **Shared critic** — a centralized value function sees global state during training, while individual policies only see local observations at execution time
- **Per-class policies** — 5 separate neural networks (one per class), enabling the same Warrior policy to function in any team composition
- **Self-play** — trains against copies of itself from a policy pool, preventing overfitting to a single strategy

### <img src="https://em-content.zobj.net/source/apple/391/building-construction_1f3d7-fe0f.png" width="16" /> Architecture

```
Policy Network (per class):                    Centralized Critic (shared):
  Input: local observation (~160 values)         Input: global state (all agents + full map)
  → MLP: 2 hidden layers, 128 neurons, ReLU     → MLP: 2 hidden layers, 256 neurons, ReLU
  → Output: action distribution (masked)         → Output: V(s) state value estimate
```

### <img src="https://em-content.zobj.net/source/apple/391/graduation-cap_1f393.png" width="16" /> Curriculum Learning

Training follows a **4-phase progressive curriculum** where each phase loads weights from the previous one:

```
Phase 1 (1v1)  ──weights──▸  Phase 2 (2v2)  ──weights──▸  Phase 3 (3v3)  ──weights──▸  Phase 4 (mixed)
  └─ saves easy/                                             └─ saves normal/             └─ saves hard/
```

| Phase | Composition | Episodes | Focus | Checkpoint |
|:---:|---|:---:|---|:---:|
| **1** | 1v1 (all classes) | 2,000 | Basic mechanics, abilities, positioning | `easy/` |
| **2** | 2v2 | 2,000 | Team coordination, healer/tank roles | — |
| **3** | 3v3 | 2,000 | Full coordination, combos, friendly fire | `normal/` |
| **4** | Mixed (1v1, 2v2, 3v3) | 2,000 | Asymmetric adaptation | `hard/` |

### <img src="https://em-content.zobj.net/source/apple/391/chart-increasing_1f4c8.png" width="16" /> Difficulty Levels

Difficulty comes directly from different training checkpoints — **no artificial handicaps**:

| Level | Source | Behavior |
|---|---|---|
| <img src="https://em-content.zobj.net/source/apple/391/green-circle_1f7e2.png" width="12" /> **Easy** | Phase 1 checkpoint | Plays individually, no team coordination |
| <img src="https://em-content.zobj.net/source/apple/391/yellow-circle_1f7e1.png" width="12" /> **Normal** | Phase 3 checkpoint | Reasonable coordination, basic combos |
| <img src="https://em-content.zobj.net/source/apple/391/red-circle_1f534.png" width="12" /> **Hard** | Phase 4 checkpoint | Exploits synergies, focuses priority targets |

### <img src="https://em-content.zobj.net/source/apple/391/control-knobs_1f39b-fe0f.png" width="16" /> Training Hyperparameters

| Parameter | Value |
|---|---|
| Learning rate | `3e-4` |
| PPO clip range | `0.2` |
| Discount (gamma) | `0.99` |
| GAE lambda | `0.95` |
| Batch size | `64` |
| Epochs per update | `4` |
| Self-play pool size | `10` |
| Pool update interval | Every `50` episodes |

---

## <img src="https://em-content.zobj.net/source/apple/391/rocket_1f680.png" width="20" /> Getting Started

### Prerequisites

| Requirement | Version |
|---|---|
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" width="14" /> Python | 3.11+ |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/nodejs/nodejs-original.svg" width="14" /> Node.js | 18+ |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/docker/docker-original.svg" width="14" /> Docker *(optional)* | 20+ |

### <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/docker/docker-original.svg" width="16" /> Option 1 — Docker (recommended)

The fastest way to get everything running:

```bash
git clone <repo-url>
cd ashborn-arena

docker compose up --build
```

| Service | URL |
|---|---|
| <img src="https://em-content.zobj.net/source/apple/391/desktop-computer_1f5a5-fe0f.png" width="14" /> Frontend | [http://localhost:3000](http://localhost:3000) |
| <img src="https://em-content.zobj.net/source/apple/391/gear_2699-fe0f.png" width="14" /> Backend API | [http://localhost:8000](http://localhost:8000) |
| <img src="https://em-content.zobj.net/source/apple/391/stethoscope_1fa7a.png" width="14" /> Health check | [http://localhost:8000/health](http://localhost:8000/health) |

To stop:

```bash
docker compose down
```

### <img src="https://em-content.zobj.net/source/apple/391/wrench_1f527.png" width="16" /> Option 2 — Manual Setup

#### 1. Install dependencies

```bash
git clone <repo-url>
cd ashborn-arena

# Python — create venv and install
python -m venv .venv
source .venv/bin/activate    # Linux / macOS
# .venv\Scripts\activate     # Windows
pip install -e ".[dev]"

# Frontend
cd frontend && npm install && cd ..
```

#### 2. Start the backend

```bash
source .venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Check `http://localhost:8000/health` to verify.

#### 3. Start the frontend

In a separate terminal:

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173` and connects to the backend at `localhost:8000`.

#### 4. Play

Open [http://localhost:5173](http://localhost:5173) in the browser. Choose difficulty, build your team, and start a battle.

---

## <img src="https://em-content.zobj.net/source/apple/391/mechanical-arm_1f9be.png" width="20" /> Training the AI

> **Note:** Training runs on CPU and takes a long time. GPU is not required but is supported by PyTorch if available.

### Full curriculum (all 4 phases)

```bash
source .venv/bin/activate
python -m training.train
```

This runs all phases sequentially (1v1 → 2v2 → 3v3 → mixed), saving checkpoints to `models/{easy,normal,hard}/`.

### Single phase

```bash
# Run only phase 1 (1v1)
python -m training.train --phase 1

# Run phase 3 with custom episode count
python -m training.train --phase 3 --episodes 500
```

### CLI options

| Flag | Default | Description |
|---|---|---|
| `--phase N` | `0` (all) | Run only phase N (1-4) |
| `--episodes N` | `0` (use defaults) | Override episodes per phase |
| `--seed N` | `42` | Random seed for reproducibility |
| `--log-dir PATH` | `logs` | Directory for training logs |

### Output

```
models/
├── easy/            Phase 1 checkpoint (1v1)
│   ├── warrior.pt
│   ├── mage.pt
│   ├── cleric.pt
│   ├── archer.pt
│   └── assassin.pt
├── normal/          Phase 3 checkpoint (3v3)
│   └── ...
└── hard/            Phase 4 checkpoint (mixed)
    └── ...
```

5 `.pt` files per difficulty level (one per class), **15 files total**.

### <img src="https://em-content.zobj.net/source/apple/391/hourglass-not-done_23f3.png" width="16" /> Running training in the background

For long runs on a VPS (or any remote machine where you want to disconnect and come back later), use the helper script:

```bash
./scripts/train_background.sh
```

It launches `python -m training.train` detached via `nohup`, writes stdout/stderr to `logs/train.out` and the process ID to `logs/train.pid`. Any extra args are forwarded to the training CLI:

```bash
./scripts/train_background.sh --phase 3 --episodes 5000 --log-dir logs/runs/2026-04-28_baseline
```

| Action | Command |
|---|---|
| <img src="https://em-content.zobj.net/source/apple/391/eyes_1f440.png" width="14" /> Follow logs live | `tail -f logs/train.out` |
| <img src="https://em-content.zobj.net/source/apple/391/magnifying-glass-tilted-left_1f50d.png" width="14" /> Check if running | `ps -p $(cat logs/train.pid)` |
| <img src="https://em-content.zobj.net/source/apple/391/octagonal-sign_1f6d1.png" width="14" /> Stop the run | `kill $(cat logs/train.pid)` |

Both `logs/train.out` and `logs/train.pid` are gitignored.

### <img src="https://em-content.zobj.net/source/apple/391/chart-increasing_1f4c8.png" width="16" /> Visualizing training

The `TrainingLogger` writes metrics to two parallel channels:

| Channel | Path | Format |
|---|---|---|
| <img src="https://em-content.zobj.net/source/apple/391/page-facing-up_1f4c4.png" width="14" /> Structured log (source of truth) | `<log-dir>/training.jsonl` | JSON-Lines, diff-friendly |
| <img src="https://em-content.zobj.net/source/apple/391/bar-chart_1f4ca.png" width="14" /> TensorBoard event files | `<log-dir>/tb/events.out.tfevents.*` | Binary, for visualization |

**Folder convention:**

| Path | Status | Use case |
|---|---|---|
| `logs/runs/<descriptive-name>/` | Versioned in git | Milestone runs (worth comparing later) |
| `logs/scratch/<id>/` | Ignored by git | Smoke tests, throwaway experiments |

**Example — milestone run:**

```bash
python -m training.train --log-dir logs/runs/2026-04-28_baseline
```

**Example — throwaway experiment:**

```bash
python -m training.train --log-dir logs/scratch/$(date +%s)
```

**View dashboards (compares all milestone runs side-by-side):**

```bash
tensorboard --logdir logs/runs/
```

Open [http://localhost:6006](http://localhost:6006) in the browser.

**Available metrics:**

| Group | Tag | Source |
|---|---|---|
| Loss | `loss/policy`, `loss/value` | per update |
| Policy | `policy/entropy`, `policy/entropy_coeff` | per update |
| Train | `train/avg_reward_50`, `train/avg_steps_50`, `train/win_rate_50` | per update (50-ep window) |
| Eval | `eval/win_rate`, `eval/loss_rate`, `eval/draw_rate`, `eval/avg_steps` | every `eval_interval` episodes |

All metrics use `episode` as the X axis, allowing direct alignment between training and eval curves.

---

## <img src="https://em-content.zobj.net/source/apple/391/test-tube_1f9ea.png" width="20" /> Testing

The project has **878 test cases** covering the game engine, backend API, training pipeline, and frontend.

### <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" width="14" /> Python tests (pytest) — 774 tests

```bash
source .venv/bin/activate

# Run all tests
pytest

# Verbose output
pytest -v

# Specific module
pytest engine/tests/test_combat.py
```

| Directory | Coverage |
|---|---|
| `engine/tests/` | Combat, movement, abilities, LoS, map generation, effects |
| `backend/tests/` | API endpoints, schemas, sessions |
| `training/tests/` | MAPPO agent, curriculum, self-play, PettingZoo environment |

### <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/vitejs/vitejs-original.svg" width="14" /> Frontend tests (vitest) — 104 tests

```bash
cd frontend

# Run all tests once
npx vitest run

# Watch mode
npm test

# Specific file
npx vitest run src/network/__tests__/ws-client.test.ts
```

### <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/typescript/typescript-original.svg" width="14" /> Type checking

```bash
cd frontend
npx tsc --noEmit
```

---

## <img src="https://em-content.zobj.net/source/apple/391/file-folder_1f4c1.png" width="20" /> Project Structure

```
ashborn-arena/
│
├── engine/                  # Game engine — pure Python, no framework
│   ├── models/              #   Domain models (Character, Ability, Map, Effect)
│   ├── systems/             #   Combat, movement, LoS, damage pipeline, effects
│   ├── generation/          #   Procedural map generation
│   └── tests/               #   Engine test suite
│
├── backend/                 # FastAPI server
│   ├── api/
│   │   ├── routes/          #   REST + WebSocket endpoints
│   │   └── schemas/         #   Pydantic request/response models
│   ├── inference/           #   Loads .pt models, runs MAPPO at runtime
│   └── main.py              #   FastAPI entrypoint
│
├── training/                # RL training pipeline (standalone)
│   ├── environment/         #   PettingZoo wrapper over the engine
│   ├── agents/              #   MAPPO: policy networks, critic, PPO update
│   ├── curriculum/          #   4-phase training, self-play pool
│   └── train.py             #   Training CLI entrypoint
│
├── frontend/                # Phaser 3 + TypeScript
│   ├── public/assets/       #   Spritesheets and visual assets
│   └── src/
│       ├── scenes/          #   Menu, Preparation, Battle, Result
│       └── network/         #   REST client, WebSocket client, validation
│
├── models/                  # Trained AI checkpoints (.pt files)
│   ├── easy/                #   5 policy networks (1v1)
│   ├── normal/              #   5 policy networks (3v3)
│   └── hard/                #   5 policy networks (mixed)
│
├── .specs/                  # Game design documentation
│   ├── prd.md               #   Product requirements
│   ├── design.md            #   Technical design (formulas, numerical specs)
│   ├── state.md             #   Feature development status
│   └── features/            #   Per-feature specs and task breakdowns
│
├── Dockerfile               # Multi-stage build (backend + frontend)
├── docker-compose.yml       # Orchestration (backend + nginx frontend)
├── nginx.conf               # Static file serving for production
└── pyproject.toml           # Python project configuration
```

### Package Dependencies

```
engine         ← pure domain, zero external deps
backend        ← imports engine + models/
training       ← imports engine, produces models/
frontend       ← independent (communicates via REST / WebSocket)
```

---

## <img src="https://em-content.zobj.net/source/apple/391/books_1f4da.png" width="20" /> Documentation

All game rules, formulas, and design decisions live in `.specs/`:

| Document | Contents |
|---|---|
| <img src="https://em-content.zobj.net/source/apple/391/clipboard_1f4cb.png" width="14" /> [prd.md](.specs/prd.md) | Game mechanics, 5 classes, 47 abilities, map rules, AI design |
| <img src="https://em-content.zobj.net/source/apple/391/nut-and-bolt_1f529.png" width="14" /> [design.md](.specs/design.md) | Damage formulas, ability numerical specs, WS protocol, AI architecture |
| <img src="https://em-content.zobj.net/source/apple/391/bar-chart_1f4ca.png" width="14" /> [state.md](.specs/state.md) | Development status — 29 features tracked |

---

<div align="center">

## <img src="https://em-content.zobj.net/source/apple/391/page-facing-up_1f4c4.png" width="18" /> License

MIT

<br/>

Made with <img src="https://em-content.zobj.net/source/apple/391/heart-on-fire_2764-fe0f-200d-1f525.png" width="16" /> and reinforcement learning

</div>
