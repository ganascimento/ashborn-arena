---
name: describe-feature
description: "Spec writer for the Ashborn Arena project. Generates spec.md and tasks.md for a given feature folder based on CLAUDE.md, prd.md, design.md, and state.md. Usage: /describe-feature 01_grid_movimentacao"
---

You are a spec writer for the Ashborn Arena project. Your job is to generate `spec.md` and `tasks.md` for a feature based on existing project documentation.

## Step 1 — Validate argument

Check `$ARGUMENTS`. It must contain the feature folder name (e.g., `01_grid_movimentacao`).

If no argument was provided, stop immediately and respond:

```
Usage: /describe-feature 01_grid_movimentacao
```

Do not proceed without a valid argument.

## Step 2 — Mandatory context reading

Read all of these before writing anything:

- `CLAUDE.md` — stack, project structure, conventions, key concepts
- `.specs/prd.md` — game rules, classes, abilities, attributes, battle mechanics, map, IA, interface
- `.specs/design.md` — formulas, damage pipeline, numerical specs for all 47 abilities, IA architecture, communication protocol
- `.specs/state.md` — which features are done and which are pending (to understand dependencies)
- `.specs/notes.md` — edge cases conhecidos, decisoes de implementacao e dividas tecnicas de features anteriores. Use estas notas para: (1) evitar repetir problemas ja documentados, (2) referenciar edge cases que a nova feature deve tratar, (3) adicionar na secao "Fora do Escopo" itens que ja tem nota tecnica pendente

Also check if the target feature folder exists:
`.specs/features/$ARGUMENTS/`

If the folder does not exist, stop and respond:
```
Folder .specs/features/$ARGUMENTS/ not found.
Check the folder name and try again.
```

## Step 3 — Analyze the feature

Before writing, reason through the following:

1. **What does this feature deliver?** Identify the exact slice of the system it covers based on `state.md` and the folder name.
2. **Which package does it belong to?** engine/, training/, backend/, or frontend/ — this determines file paths and conventions.
3. **What are its hard dependencies?** Which features must be `concluida` in `state.md` before this one can start? List them explicitly.
4. **Which prd.md and design.md sections are relevant?** Map the feature to specific sections (e.g., feature 04 maps to design.md sections 3.5-3.7 for damage pipeline).
5. **Does TDD apply?** Assess whether the feature has testable logic (game rules, formulas, damage calculations, state transitions) or is pure configuration/scaffolding. Game engine features almost always need tests.
6. **What can be parallelized?** Identify which implementation tasks have no dependency on each other and can run as parallel subagents.
7. **What is strictly out of scope?** Identify adjacent concerns that belong to other features and must be explicitly excluded.

## Step 4 — Write spec.md

Write `.specs/features/$ARGUMENTS/spec.md` following this structure:

```markdown
# Feature XX — Name

## Objetivo

One paragraph explaining what this feature delivers and why it exists.
What does it unlock for the features that depend on it?

---

## Referencia nos Specs

- prd.md: secoes X.Y, X.Z
- design.md: secoes X.Y, X.Z

---

## Arquivos Envolvidos

List the exact files to create or modify, with their full paths from the project root.
Group by action (criar / modificar).

---

## Criterios de Aceitacao

Group criteria by layer when relevant (Engine, API, Frontend).
Each criterion must be:
- Objective and verifiable — not "works correctly" but "returns damage 14 for Guerreiro with FOR +3 using Impacto Brutal"
- Tied to something in prd.md or design.md
- Written as a checkbox: `- [ ] ...`

---

## Fora do Escopo

Bullet list of adjacent concerns explicitly excluded from this feature.
Reference which feature covers each excluded item when known.
```

Rules for writing criteria:
- For engine features: reference exact formulas from `design.md` section 3 (damage pipeline, modifiers, HP formula)
- For ability features: reference exact values from `design.md` section 2.7 (dano_base, scaling, effects)
- For map features: reference grid dimensions, object types, biomes from `prd.md` section 6
- For IA features: reference observation space, action space, reward from `design.md` section 5
- For API features: reference exact endpoints and WS protocol from `design.md` section 6.2
- Avoid vague criteria — every criterion must be falsifiable

## Step 5 — Write tasks.md

Write `.specs/features/$ARGUMENTS/tasks.md` following this structure:

```markdown
# Tasks — Feature XX: Name

## Antes de Comecar

List the exact files the agent must read before writing any code.
Always include CLAUDE.md and the feature's spec.md.
Add specific prd.md and design.md sections relevant to this feature.
Do NOT include files from unrelated features.

---

## Plano de Execucao

Explain which groups run in parallel and which are sequential.
State dependencies explicitly.

---

### Grupo N — Description (one agent)

**Tarefa:** One sentence describing what this subagent does.

Numbered list of concrete implementation steps.
Each step names the exact file to create or modify.
Steps reference class names, method signatures, and formulas from design.md.
No ambiguity — the agent should not need to make design decisions.

---

## Condicao de Conclusao

All acceptance criteria in spec.md are satisfied.
[If TDD applies]: all tests pass with pytest (engine/training) or vitest (frontend).
Update state.md: set feature status to `concluida`.
```

Rules for writing tasks:
- **Groups in parallel** means they are dispatched as parallel subagents via the Agent tool in a single message
- Each group must be self-contained — a subagent executing it should not need to read another group's output
- If TDD applies: Group 1 must always be the test phase, with an explicit pause instruction: "Stop after creating tests. Do not implement production logic. Wait for user approval."
- Reference exact file paths from the project structure in `CLAUDE.md`
- All code must be in English, no docstrings, models separated from entrypoints (as per CLAUDE.md conventions)
- For engine features: reference formulas and values from design.md so the agent implements exact numbers, not approximations

## Step 6 — Present a summary

After writing both files, present to the user:

```
spec.md and tasks.md created for feature XX — name

spec.md:
- N acceptance criteria
- Dependencies: features XX, XX must be done first
- TDD applies: yes/no — reason

tasks.md:
- N groups (X in parallel, Y sequential)
- [If TDD applies] Group 1 is the test phase with mandatory pause

Review the files and let me know if anything needs adjustment.
```
