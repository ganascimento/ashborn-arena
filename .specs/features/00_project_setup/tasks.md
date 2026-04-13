# Tasks — Feature 00: Project Setup e Scaffolding

## Antes de Comecar

Ler antes de escrever qualquer codigo:
- `CLAUDE.md` — estrutura do projeto, stack, convencoes
- `.specs/features/00_project_setup/spec.md` — criterios de aceitacao

---

## Plano de Execucao

3 grupos. Grupos 1 e 2 rodam **em paralelo** (Python e Frontend sao independentes). Grupo 3 roda **apos ambos** (validacao).

TDD nao se aplica — feature e scaffolding puro sem logica de negocio.

---

### Grupo 1 — Python scaffolding (um agente)

**Tarefa:** Criar toda a estrutura Python (engine, backend, training) com pyproject.toml e arquivos de configuracao.

1. Criar `pyproject.toml` na raiz com:
   - `[project]` name = "ashborn-arena", requires-python = ">=3.11"
   - `[project.dependencies]`: fastapi, uvicorn[standard], pettingzoo, torch (cpu)
   - `[project.optional-dependencies]` dev = ["pytest", "httpx"] 
   - `[tool.pytest.ini_options]` testpaths = ["engine/tests", "backend/tests", "training/tests"]
   - Packages: engine, backend, training como find packages

2. Criar estrutura engine/:
   - `engine/__init__.py` (vazio)
   - `engine/models/__init__.py` (vazio)
   - `engine/systems/__init__.py` (vazio)
   - `engine/generation/__init__.py` (vazio)
   - `engine/tests/__init__.py` (vazio)

3. Criar estrutura backend/:
   - `backend/__init__.py` (vazio)
   - `backend/api/__init__.py` (vazio)
   - `backend/api/routes/__init__.py` (vazio)
   - `backend/api/schemas/__init__.py` (vazio)
   - `backend/inference/__init__.py` (vazio)
   - `backend/tests/__init__.py` (vazio)
   - `backend/main.py`:
     ```python
     from fastapi import FastAPI

     app = FastAPI(title="Ashborn Arena")

     @app.get("/health")
     def health():
         return {"status": "ok"}
     ```

4. Criar estrutura training/:
   - `training/__init__.py` (vazio)
   - `training/environment/__init__.py` (vazio)
   - `training/agents/__init__.py` (vazio)
   - `training/curriculum/__init__.py` (vazio)
   - `training/tests/__init__.py` (vazio)
   - `training/train.py`:
     ```python
     if __name__ == "__main__":
         pass
     ```

5. Criar estrutura models/:
   - `models/easy/.gitkeep`
   - `models/normal/.gitkeep`
   - `models/hard/.gitkeep`

6. Criar `.gitignore`:
   ```
   .venv/
   __pycache__/
   *.pyc
   *.egg-info/
   dist/
   build/
   node_modules/
   models/**/*.pt
   .env
   ```

---

### Grupo 2 — Frontend scaffolding (um agente)

**Tarefa:** Criar toda a estrutura frontend com Phaser 3, TypeScript e configuracao de build.

1. Criar `frontend/package.json`:
   - name: "ashborn-arena-frontend"
   - scripts: dev (vite), build (vite build), test (vitest)
   - dependencies: phaser@^3
   - devDependencies: typescript, vite, vitest, @types/node

2. Criar `frontend/tsconfig.json`:
   - target: ES2020, module: ESNext, strict: true
   - include: ["src"]

3. Criar `frontend/vite.config.ts`:
   - Plugin: nenhum necessario para Phaser
   - Configurar base para desenvolvimento

4. Criar `frontend/index.html`:
   ```html
   <!DOCTYPE html>
   <html lang="en">
   <head>
     <meta charset="UTF-8">
     <meta name="viewport" content="width=device-width, initial-scale=1.0">
     <title>Ashborn Arena</title>
     <style>body { margin: 0; background: #000; }</style>
   </head>
   <body>
     <script type="module" src="/src/main.ts"></script>
   </body>
   </html>
   ```

5. Criar `frontend/src/main.ts`:
   - Configurar Phaser.Game com config minima (800x600, scene com texto "Ashborn Arena")
   - Apenas o suficiente para confirmar que Phaser funciona

6. Criar pastas com .gitkeep:
   - `frontend/src/scenes/.gitkeep`
   - `frontend/src/ui/.gitkeep`
   - `frontend/src/network/.gitkeep`

---

### Grupo 3 — Validacao (sequencial, apos grupos 1 e 2)

**Tarefa:** Validar que toda a estrutura funciona conforme os criterios de aceitacao.

1. Validar Python:
   ```bash
   cd <project_root>
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   python -c "import engine; import backend; import training"
   pytest
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
   sleep 2
   curl http://localhost:8000/health
   kill %1
   ```

2. Validar Frontend:
   ```bash
   cd frontend
   npm install
   npm run build
   ```

3. Validar estrutura:
   - Conferir que todas as pastas de CLAUDE.md existem
   - Conferir que todos os __init__.py existem
   - Conferir .gitignore

4. Se alguma validacao falhar, corrigir antes de concluir.

---

## Condicao de Conclusao

Todos os criterios de aceitacao em spec.md satisfeitos.
TDD nao se aplica — validacao e estrutural.
Update state.md: set feature 00 status para `concluida`.
