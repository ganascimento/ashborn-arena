# Feature 00 — Project Setup e Scaffolding

## Objetivo

Criar toda a estrutura de pastas, arquivos de configuracao e dependencias do projeto Ashborn Arena. Ao final, todos os pacotes Python sao importaveis, pytest roda (com 0 testes), o frontend compila, e qualquer feature subsequente pode comecar a escrever codigo sem se preocupar com setup.

---

## Referencia nos Specs

- CLAUDE.md: secao "Estrutura do Projeto" (arvore de pastas completa)
- CLAUDE.md: secao "Stack" (dependencias Python e frontend)
- CLAUDE.md: secao "Convencoes" (ingles, sem docstrings)

---

## Arquivos Envolvidos

### Criar

**Raiz:**
- `.gitignore`
- `pyproject.toml` (define engine, backend, training como pacotes, dependencias, pytest config)

**Engine (engine/):**
- `engine/__init__.py`
- `engine/models/__init__.py`
- `engine/systems/__init__.py`
- `engine/generation/__init__.py`

**Backend (backend/):**
- `backend/__init__.py`
- `backend/main.py` (FastAPI app minimo — healthcheck apenas)
- `backend/api/__init__.py`
- `backend/api/routes/__init__.py`
- `backend/api/schemas/__init__.py`
- `backend/inference/__init__.py`

**Training (training/):**
- `training/__init__.py`
- `training/train.py` (placeholder com `if __name__ == "__main__": pass`)
- `training/environment/__init__.py`
- `training/agents/__init__.py`
- `training/curriculum/__init__.py`

**Frontend (frontend/):**
- `frontend/package.json`
- `frontend/tsconfig.json`
- `frontend/index.html`
- `frontend/src/main.ts` (Phaser 3 bootstrap minimo — tela preta com texto "Ashborn Arena")
- `frontend/src/scenes/.gitkeep`
- `frontend/src/ui/.gitkeep`
- `frontend/src/network/.gitkeep`

**Models (checkpoints):**
- `models/easy/.gitkeep`
- `models/normal/.gitkeep`
- `models/hard/.gitkeep`

---

## Criterios de Aceitacao

### Python

- [ ] `pyproject.toml` existe na raiz com dependencias: fastapi, uvicorn, torch, pettingzoo, pytest
- [ ] `pip install -e ".[dev]"` executa sem erro dentro do venv
- [ ] `python -c "import engine; import backend; import training"` executa sem erro
- [ ] `pytest` roda e retorna 0 testes coletados, exit code 0
- [ ] `uvicorn backend.main:app` inicia e `GET /health` retorna `{"status": "ok"}`

### Frontend

- [ ] `cd frontend && npm install` executa sem erro
- [ ] `cd frontend && npm run dev` inicia o servidor de desenvolvimento Phaser 3
- [ ] `cd frontend && npm run build` compila sem erro TypeScript

### Estrutura

- [ ] Todas as pastas de CLAUDE.md existem: engine/{models,systems,generation}, backend/{api/routes,api/schemas,inference}, training/{environment,agents,curriculum}, frontend/src/{scenes,ui,network}, models/{easy,normal,hard}
- [ ] Todos os `__init__.py` existem nos pacotes Python
- [ ] `.gitignore` cobre: .venv/, __pycache__/, node_modules/, models/**/*.pt, .env, dist/

---

## Fora do Escopo

- Qualquer domain model (Character, Ability, etc.) — feature 03+
- Qualquer rota REST ou WebSocket alem do healthcheck — features 16, 17
- Qualquer logica de game engine — features 01-12
- Qualquer codigo de treinamento — features 13-15
- Qualquer cena Phaser alem do bootstrap minimo — features 19-23
- README.md — ja existe
