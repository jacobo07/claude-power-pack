---
title: Auto-Testing Skill — ULTRA PLAN
date_started: 2026-05-23
status: ACCEPTED — execution in progress
branch: feat/rtk-compressor-fusion
spec: vault/specs/auto-testing-gate.md
forbidden_runtimes: n8n
defaults_at_accept:
  diff_scope: staged-only
  llm_call_budget_per_gate: 1
  test_placement: project/tests/auto-generated (gitignored)
  ceiling_definition: no manifest OR framework binary missing on PATH
  failure_ledger: every failure recorded
  java_generator: shipped (ceiling-honest)
---

# Auto-Testing Skill — Execution Plan

## Objective

Build a PP-native quality gate that automatically generates relevant
tests for the staged diff, runs them in <=30 seconds, and blocks the
commit if any fail. Cross-language: Python (pytest), Node
(vitest/jest), Java (JUnit 5 with build-system honesty). Cross-
project: KobiCraft (Java, CEILING), InfinityOps UI (Node, SOFT-
CEILING), TUA-X (Python, READY), PP (Python, READY).

## PASO 0 — Floor (read-only, 2026-05-23)

| Project | Build | Framework | Existing | Verdict |
|---|---|---|---|---|
| KobiCraft (`Minecraft Projects/KobiiCraft Workspace/KobiCraft`) | none | n/a | 0 / 136 .java | HARD-CEILING |
| InfinityOps/UI (`13_UI_Product_Layer/infinity_ui`) | npm | none configured | 0 | SOFT-CEILING |
| TUA-X | pyproject.toml | pytest 8.0 (+asyncio +cov +httpx) | 6+ across tests/ + tuax_core/tests/ | READY |
| PP (this repo) | none at root | pytest convention | 3 in tests/, 4 in tools/, 1 .test.js, 1 .test.sh | READY-UNCONFIGURED |

Gate must honor this floor: cannot fabricate a test execution path
for KobiCraft.

## Reality contract (the hard floor)

A test exists on disk or it does not. `vault/test-results/` carries
real timestamps or it carries none. A commit blocked by the gate is
evidence; a commit allowed against passing tests is evidence. Honest
CEILING ("no build system") is correct posture, not an excuse.

## The 23 Pasos

| # | Paso | Component |
|---|---|---|
| PRE-1 | Spec + plan + dirs | scaffold |
| A1 | detectors.py | core |
| A2 | llm_bridge.py | core |
| B1 | python_gen.py | gen |
| B2 | node_gen.py | gen |
| B3 | java_gen.py | gen |
| C1 | auto_test.py runner + 30s kill | core |
| C2 | vault_io.py atomic + JSONL | core |
| D1 | hooks/auto-test-gate.js | gate |
| D2 | budget guard + WARN-TIMEOUT | gate |
| D3 | register-auto-test-gate consolidator | install |
| E1 | commands/auto-test.md | skill |
| E2 | auto_test.py --deep mode | skill |
| F1 | closed-loop failure replay | learn |
| V-DET | determinism x2 | verify |
| V-PYTHON-FAIL | real BLOCK on broken .py | verify |
| V-PYTHON-PASS | real ALLOW on passing .py | verify |
| V-CEILING-JAVA | KobiCraft honest CEILING | verify |
| V-CEILING-NODE | InfinityOps UI soft CEILING | verify |
| V-TIMING | 10-run 95-pct <=30s | verify |
| V-CLOSED-LOOP | AVOID clause empirical | verify |
| POST-1 | apex Testing Gate Axis | seal |
| POST-2 | session_lessons + ukdl-universal | seal |

## Iteration loop

Per Owner template
(`Downloads/Promptsss/Prompts pa iterar/Universal/iteracion-avanzada-universal.txt`):
each done-gate failure adds a row to
`vault/knowledge_base/session_lessons.md` and a cross-ref in
`vault/knowledge_base/ukdl-universal.md`. POST-2 enforces this.

## Restrictions (hard invariants)

1. Fast gate budget: 30 seconds total wall-clock. Exceeding this is
   the bug, not the test.
2. CEILING never blocks. A gate that blocks for reasons it cannot
   verify is worse than no gate.
3. Generator output is real test code (callable, executable). If the
   generator cannot produce a real test for the diff, it returns
   `Skip("reason")` — never an inert shell.
4. Generator reads up to 3 existing tests from the project before
   prompting the LLM. Style adapts to the project (JUnit 5 vs JUnit 4,
   pytest vs unittest, vitest vs jest).

## Status log

| Date  | Paso | Result | Notes |
|-------|------|--------|-------|

(filled in as each Paso closes)

## Final commits (this plan)

(filled in as commits land)
