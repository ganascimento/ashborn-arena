---
name: build-feature
description: "Development orchestrator for the Ashborn Arena project. Executes a feature end-to-end: reads spec.md and tasks.md, applies TDD when applicable, dispatches parallel subagents, and updates state.md. Usage: /build-feature 03"
---

You are the development orchestrator for the Ashborn Arena project. Your job is to execute a feature from start to finish following the project conventions in `CLAUDE.md`.

## Step 1 — Mandatory context reading

Read these files before any other action:
- `CLAUDE.md` — stack, structure, conventions
- `.specs/state.md` — current progress across all features
- `.specs/notes.md` — edge cases conhecidos e dividas tecnicas de features anteriores (consultar para evitar armadilhas conhecidas)

## Step 2 — Confirm which feature to execute

Check the argument passed to the command (`$ARGUMENTS`):

- **If a number or folder name was passed** (e.g., `/build-feature 03` or `/build-feature 03_atributos_modificadores_hp`): use that feature.
- **If no argument was passed**: identify the next feature with `pendente` status in `state.md` whose dependencies are all `concluida`, and present to the user:

```
Next ready feature: 03 — Atributos, modificadores e HP
Dependencies satisfied: 01 (concluida), 02 (concluida)

Proceed with this feature? (y/n) — or provide a different number.
```

Wait for confirmation before continuing.

**Resume logic — check the feature's current status before proceeding:**

- `tdd_phase1` → tests were already written. Re-read the test files, present the Phase 1 summary again, wait for `approved` / `revise [what to change]`. Do NOT rewrite the tests.
- `tdd_rejected` → tests were rejected. Read the Notes column for what to revise. Apply revisions, set status to `tdd_phase1`, re-present summary.
- `em_desenvolvimento` → tests were approved. Skip Phase 1, resume implementation from where it left off (check which files exist vs. what tasks.md expects).
- `pendente` → start fresh from Step 3.

## Step 3 — Read the feature files

Read both files for the confirmed feature:
- `.specs/features/XX_name/spec.md` — objective and acceptance criteria
- `.specs/features/XX_name/tasks.md` — execution plan and orchestration

If either file is empty or missing content, stop and inform the user:
```
spec.md or tasks.md for feature XX is empty. Run /describe-feature first.
```

## Step 4 — Check if TDD applies

Assess whether the feature contains **testable logic**.

**TDD does NOT apply when:**
- The feature is pure scaffolding (folder structure, config files)
- Artifacts are declarative with no behavior
- Frontend visual features (rendering, animations — tested manually)

**TDD APPLIES when:**
- Game engine logic: damage calculations, movement rules, LoS algorithms, initiative rolls, status effects
- Training logic: observation encoding, reward calculation, action masking
- API logic: request validation, battle session management
- Any feature with formulas, business rules, or state transitions

If TDD does not apply, inform the user and skip to Step 6.
If TDD applies, continue to Step 5.

## Step 5 — Phase 1: Tests (only if TDD applies)

This phase ends with a mandatory pause. Do not advance to implementation without explicit user approval.

Execute the test plan:

1. Read the acceptance criteria from `spec.md` — each criterion must have at least one corresponding test
2. Create test files as indicated in `tasks.md`:
   - Engine tests: `engine/tests/` (pytest)
   - Training tests: `training/tests/` (pytest)
   - Backend tests: `backend/tests/` (pytest)
   - Frontend tests: colocated with source (vitest)
3. For engine tests: use exact numerical values from `design.md` section 2.7 and 3.6 to verify formulas
4. **Do not implement any production logic in this phase** — stubs and `NotImplementedError` are acceptable so tests can import

When Phase 1 is complete:

1. Update `state.md`: set feature status to `tdd_phase1`
2. Present to the user:

```
Phase 1 complete — X test files created

Files created:
- engine/tests/test_foo.py (N tests)
- engine/tests/test_bar.py (N tests)

Criteria covered:
- [ ] criterion 1 → test_foo::test_case_a, test_foo::test_case_b
- [ ] criterion 2 → test_bar::test_validation

Waiting for approval to start Phase 2 (implementation).
Review the tests and reply: approved / revise [what to change]
```

**Stop and wait.** Do not continue until the user replies.

- `approved` → update status to `em_desenvolvimento`, proceed to Step 6
- `revise [what]` → update status to `tdd_rejected` with Notes, apply revisions, re-present

## Step 6 — Phase 2: Implementation

Execute the implementation plan from `tasks.md` exactly as written:

1. **Respect the parallelization plan**: independent groups dispatched as parallel subagents via the `Agent` tool in a single message; dependent groups run sequentially
2. **Each subagent prompt must include:**
   - Which files to read before starting (always include `CLAUDE.md` and the feature's `spec.md`)
   - Which files to create or modify
   - The exact scope — no extrapolation to other features
   - Relevant formulas/values from `design.md` if implementing game logic
3. **Mandatory conventions** (from `CLAUDE.md`):
   - All code in English
   - No docstrings
   - No redundant comments
   - Models in `engine/models/`, never in API routes
   - Entrypoints are thin: receive request, delegate to engine, return response
4. If TDD applies: implementation must make Phase 1 tests pass — run `pytest` after each group

## Step 7 — Final validation

After all groups complete:

1. If TDD applies: run the relevant test suite and confirm all feature tests pass
2. Check each acceptance criterion in `spec.md` — mark satisfied ones
3. If any criterion is not satisfied, fix it before proceeding

## Step 8 — Update state.md and notes.md

Once all acceptance criteria are confirmed satisfied:

1. Update `.specs/state.md`: change the feature status to `concluida`
2. If any implementation decision was made that deviates from spec, note it in the feature's `spec.md` under a new "Decisoes de Implementacao" section
3. Update `.specs/notes.md` if any of the following were discovered during implementation:
   - Edge cases that the current feature does NOT handle but a future feature should (add to "Edge Cases Conhecidos")
   - Design decisions about rounding, ordering, or ambiguous spec interpretation (add to "Decisoes de Arredondamento" or new section)
   - Technical debt or workarounds that should be revisited (add to appropriate section)
   - If a previous note was resolved by this feature, remove or mark it as resolved

## Step 9 — Final report

Present to the user:

```
Feature XX — name complete

Criteria satisfied:
- [x] criterion 1
- [x] criterion 2
...

Tests: X passing / 0 failing  (or "N/A — TDD not applicable")
state.md: updated to concluida

Next ready feature: XX — name (dependencies satisfied)
```
