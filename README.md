<div align="center">

# ⚔️ Ashborn Arena

**Turn-based tactical RPG with multi-agent AI trained via reinforcement learning.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Phaser](https://img.shields.io/badge/Phaser_3-8B5CF6?style=for-the-badge&logoColor=white)](https://phaser.io)
[![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev)

</div>

<br/>

## 🎮 Features

| | Feature | Description |
|---|---|---|
| 🗡️ | **5 unique classes** | Warrior, Mage, Cleric, Archer, Assassin with 47 abilities and elemental combos |
| 📊 | **Deep build system** | 5 attributes, 10 distributable points, 11 abilities per class (pick 5) |
| 💥 | **Destructible environments** | Throwable objects, fire spread, line-of-sight cover on a 10x8 grid |
| 🤖 | **Multi-agent RL** | MAPPO-trained AI with per-class policies and curriculum learning (1v1 to 3v3) |
| 🎯 | **3 difficulty levels** | Easy, Normal, Hard from different training checkpoints |
| 🌐 | **Zero friction** | Browser-based, no login, builds saved in localStorage |

<br/>

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| 🎲 Game Engine | Python (pure, no framework) |
| 🧠 ML / AI | PyTorch, MAPPO (custom implementation) |
| 🏋️ RL Environment | PettingZoo |
| ⚡ Backend API | FastAPI (REST + WebSocket) |
| 🖥️ Frontend | Phaser 3 + TypeScript + Vite |
| 💾 Persistence | localStorage (no database) |

<br/>

## 🚀 Getting Started

### Prerequisites

| Requirement | Version |
|---|---|
| 🐍 Python | 3.11+ |
| 📦 Node.js | 18+ |

### Installation

```bash
git clone <repo-url>
cd ashborn-arena

# Python — create venv and install all packages
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
pip install -e ".[dev]"

# Frontend
cd frontend && npm install && cd ..
```

### ▶️ Running the App

You need two terminals — one for the backend, one for the frontend.

**⚡ Backend** (REST + WebSocket on port 8000):

```bash
source .venv/bin/activate
uvicorn backend.main:app --reload
```

**🖥️ Frontend** (Vite dev server, default port 5173):

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173` in the browser. The frontend connects to the backend at `localhost:8000`.

### 🧠 Training the AI

```bash
# Full curriculum (1v1 → 2v2 → 3v3, takes a long time on CPU)
python -m training.train

# Single phase
python -m training.train --phase 1  # 1v1 only
```

Trained checkpoints are saved to `models/{easy,normal,hard}/` and loaded by the backend at inference time.

<br/>

## 🧪 Testing

### 🐍 Backend + Engine

Uses **pytest**. Test paths: `engine/tests/`, `backend/tests/`, `training/tests/`.

```bash
# Run all Python tests
pytest

# Run with verbose output
pytest -v

# Run a specific module
pytest engine/tests/test_combat.py
```

### 🖥️ Frontend

Uses **Vitest** with happy-dom. Tests live in `__tests__/` folders next to the source.

```bash
cd frontend

# Run all tests once
npx vitest run

# Run in watch mode (re-runs on file changes)
npm test

# Run a specific test file
npx vitest run src/network/__tests__/ws-client.test.ts
```

### ✅ Build Check

```bash
# TypeScript type-check (no emit)
cd frontend && npx tsc --noEmit
```

<br/>

## 📁 Project Structure

```
ashborn-arena/
├── engine/                 # 🎲 Game engine (shared between backend and training)
│   ├── models/             #    Domain models: Character, Ability, Map, Effect
│   ├── systems/            #    Combat, movement, LoS, damage pipeline
│   └── generation/         #    Procedural map generation
├── backend/                # ⚡ FastAPI (REST + WebSocket)
│   ├── api/routes/         #    Endpoints
│   ├── api/schemas/        #    Pydantic request/response
│   └── inference/          #    Loads .pt models, runs MAPPO inference
├── training/               # 🧠 RL training (standalone)
│   ├── environment/        #    PettingZoo wrapper
│   ├── agents/             #    MAPPO networks + PPO update
│   └── curriculum/         #    Training phases + self-play
├── frontend/               # 🖥️ Phaser 3 + TypeScript
│   └── src/
│       ├── scenes/         #    Menu, Preparation, Battle, Result
│       └── network/        #    REST client, WebSocket client, validation
├── models/                 # 📦 Trained AI checkpoints (.pt)
│   ├── easy/
│   ├── normal/
│   └── hard/
└── .specs/                 # 📝 Game design documentation
    ├── prd.md              #    Product requirements
    ├── design.md           #    Technical design (formulas, ability specs)
    ├── state.md            #    Development status for all 24 features
    └── features/           #    Per-feature specs and tasks
```

### 🔗 Package Dependencies

```
engine         ← pure domain, no external deps
backend        ← imports engine + models/
training       ← imports engine, produces models/
frontend       ← independent (communicates via REST/WS)
```

<br/>

## 📖 Documentation

All game rules, formulas, and design decisions live in `.specs/`:

| Document | Contents |
|---|---|
| 📋 [prd.md](.specs/prd.md) | Game rules, classes, abilities, map, AI, interface |
| 🔧 [design.md](.specs/design.md) | Damage formulas, numerical specs for 47 abilities, AI architecture, WS protocol |
| 📊 [state.md](.specs/state.md) | Development status for all 24 features |

<br/>

## 📄 License

MIT
