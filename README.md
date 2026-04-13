<div align="center">

# Ashborn Arena

Turn-based tactical RPG with multi-agent AI trained via reinforcement learning.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat&logo=pytorch&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white)
![Phaser](https://img.shields.io/badge/Phaser_3-8B5CF6?style=flat&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJMMiAyMmgyMEwxMiAyeiIgZmlsbD0id2hpdGUiLz48L3N2Zz4=&logoColor=white)

</div>

---

## Features

- **5 unique classes** — Warrior, Mage, Cleric, Archer, Assassin with 47 abilities and elemental combos
- **Deep build system** — 5 attributes, 10 distributable points, 11 abilities per class (pick 5)
- **Destructible environments** — throwable objects, fire spread, line-of-sight cover on a 10x8 grid
- **Multi-agent RL** — MAPPO-trained AI with per-class policies and curriculum learning (1v1 to 3v3)
- **3 difficulty levels** — Easy, Normal, Hard from different training checkpoints
- **Zero friction** — browser-based, no login, builds saved in localStorage

## Tech Stack

| Layer          | Technology                             |
| -------------- | -------------------------------------- |
| Game Engine    | Python (pure, no framework)            |
| ML / AI        | PyTorch, MAPPO (custom implementation) |
| RL Environment | PettingZoo                             |
| Backend API    | FastAPI (REST + WebSocket)             |
| Frontend       | Phaser 3 + TypeScript                  |
| Persistence    | localStorage (no database)             |

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd ashborn-arena

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install Python dependencies (engine + backend + training)
pip install -e ".[dev]"

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Running

```bash
# Start the backend
uvicorn backend.main:app --reload

# Start the frontend (in another terminal)
cd frontend
npm run dev
```

### Training the AI

```bash
# Run the full curriculum (this takes weeks on CPU)
python -m training.train

# Or run a specific phase
python -m training.train --phase 1  # 1v1 only
```

## Testing

```bash
# Engine + backend tests
pytest

# Frontend tests
cd frontend
npm test
```

## Project Structure

```
ashborn-arena/
├── engine/                 # Game engine (shared between backend and training)
│   ├── models/             # Domain models: Character, Ability, Map, Effect
│   ├── systems/            # Combat, movement, LoS, damage pipeline
│   └── generation/         # Procedural map generation
├── backend/                # FastAPI (REST + WebSocket)
│   ├── api/routes/         # Endpoints
│   ├── api/schemas/        # Pydantic request/response
│   └── inference/          # Loads .pt models, runs MAPPO inference
├── training/               # RL training (standalone)
│   ├── environment/        # PettingZoo wrapper
│   ├── agents/             # MAPPO networks + PPO update
│   └── curriculum/         # Training phases + self-play
├── frontend/               # Phaser 3 + TypeScript
│   └── src/
│       ├── scenes/         # Menu, preparation, battle, result
│       ├── ui/             # HUD, ability bar, HP bars
│       └── network/        # REST + WebSocket client
├── models/                 # Trained AI checkpoints (.pt)
│   ├── easy/
│   ├── normal/
│   └── hard/
└── .specs/                 # Game design documentation
    ├── prd.md              # Product requirements
    ├── design.md           # Technical design (formulas, ability specs)
    └── features/           # Per-feature specs and tasks
```

## Documentation

All game rules, formulas, and design decisions live in `.specs/`:

| Document                      | Contents                                                                        |
| ----------------------------- | ------------------------------------------------------------------------------- |
| [prd.md](.specs/prd.md)       | Game rules, classes, abilities, map, AI, interface                              |
| [design.md](.specs/design.md) | Damage formulas, numerical specs for 47 abilities, AI architecture, WS protocol |
| [state.md](.specs/state.md)   | Development status for all 24 features                                          |

## License

MIT
