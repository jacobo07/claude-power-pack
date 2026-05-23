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
| 05-23 | PRE-1 | DONE | spec 223 lines, plan 105 lines, dirs scaffolded, 0 trigger tokens |
| 05-23 | A1    | DONE+ITER | 5/5 cwds correctly classified; convention rule iterated to require test_*.py>=3 AND *.py>=3 (TEMP false-positive caught) |
| 05-23 | A2    | DONE | HELLO returns 16.1 s via STDIN; CLAUDEPP_AUTOTEST_RUNNING=1 propagation verified |
| 05-23 | B1    | DONE | 30-line .py diff -> import calc + def test_add + assert add(2,3)==5 in 15.4 s; 3 PP style refs |
| 05-23 | B2    | DONE | 30-line .ts diff -> 3 vitest it() blocks with expect().toBe() in 20.2 s; framework correctly inferred from InfinityOps UI deps |
| 05-23 | B3    | DONE | KobiCraft -> CEILING (no build system); synthetic Maven /tmp project -> JUnit 5 @Test assertEquals scaffold in 16.1 s |
| 05-23 | C1    | DONE | 5 s pytest run passes; infinite-loop test killed at exactly 5 s timeout (exit 124 + TIMEOUT marker) |
| 05-23 | C2    | DONE | 4/4 vault IO round-trips (log_auto_spawn / write_result_artifact / write_failure + history / 100 KB rotation) |
| 05-23 | D1    | DONE | dual-regex 9/9 positive + 9/9 negative; integration 150 ms on no-diff cwd; recursion + opt-out guards exit 0 |
| 05-23 | D2    | DONE | 35 s fake-sleep killed at exactly 28 s, verdict=timeout, exit 0, warn-log row written |
| 05-23 | D3    | DONE | register-auto-test-gate consolidator added; --dry-run prints valid wiring; --help lists subcommand; Mirror-Sync-Direction respected |
| 05-23 | E1    | DONE | commands/auto-test.md skill manifest; args + examples + 4 opt-out env vars + 5 verdict table |
| 05-23 | E2    | DONE+ITER | deep mode wired; first run pytest-rejected filename (digit-start + dot); fix: test_auto_<slug>_<ts>.py; re-run: 3 tests generated, all passed in 0.57 s, 22.9 s total |
| 05-23 | F1    | DONE | AVOID clause 227-char with prior test_text fires at Jaccard>=0.30; empty history -> 0-len clause |
| 05-23 | V-DET | PASS | byte-identical scaffold on consecutive runs (`import pytest; from calc import add; def test_add_returns_sum...; assert add(2,3)==5`) |
| 05-23 | V-PYTHON-FAIL | PASS | broken add(a,b)=a-b staged -> hook exit 2 BLOCKED, verdict=fail, visible "[auto-test-gate] BLOCKED:" message, 21.55 s |
| 05-23 | V-PYTHON-PASS | PASS | correct add(a,b)=a+b staged -> hook exit 0, verdict=pass, vault/test-results/<ts>_pass_*.md artifact written, 19.11 s |
| 05-23 | V-CEILING-JAVA | PASS | .java in no-pom.xml project -> exit 0, verdict=ceiling, reason cites "no build manifest", 0.41 s |
| 05-23 | V-CEILING-NODE | PASS | .ts in node-no-test-script project -> exit 0, verdict=ceiling, reason cites "framework binary missing", 0.30 s |
| 05-23 | V-TIMING | PASS | 10 hook fires: p05=0.22 s, median=0.27 s, p95=23.48 s — within the 5 s / 30 s bounds |
| 05-23 | V-CLOSED-LOOP | PASS | planted sha 7a1bd6 -> AVOID clause fires -> new test sha f691d4 (parametrize-based, different name) |
| 05-23 | POST-1 | DONE | apex-completion-standard.md gains "Testing Gate Axis" section (5 components + 5-check DONE-gate + empirical proofs); PP source + live mirror sha256-identical (63bdfca46f83e8cd...) |
| 05-23 | POST-2 | DONE+ITER | session_lessons.md L1-L6 rows + ukdl-universal.md cross-ref; bash heredoc clobbered head of session_lessons.md (BOM interaction), recovered via `git checkout HEAD -- <file>` + Python read_bytes+write_bytes; new lesson sealed at vault/lessons/bash-heredoc-bom-clobber.md |

## Final commits (this plan)

- `3efe960` PRE-1
- `a5c1468` A1 (with iteration: Python-by-convention rule tightened)
- `1eabc2d` A2
- `ceb0b56` B1
- `3839983` B2
- `50d4e4c` B3
- `3ebbe77` C1 + C2
- `7801235` D1 + D2 + D3
- `a266cff` E1 + E2 (with iteration: filename starts with `test_`)
- `f7a8948` F1
- (this commit) POST-1 + POST-2 + BOM lesson

## Iterations sealed as PP-wide lessons

- `vault/lessons/bash-heredoc-bom-clobber.md` — Python read_bytes +
  write_bytes is the safe append pattern; bash `>>` heredoc on
  BOM-prefixed files on Windows can clobber the head of the file.

## Cross-axis pattern

The Auto-Testing Skill completes the third PP axis built on the
"sleepy auto-spawn + ceiling-honest gate" pattern:
- Research Axis (cpp-deep-research, sealed 2026-05-23)
- Testing Gate Axis (auto-test-gate, this plan)
- Session-Safety Axis (session-file-guard, sealed 2026-05-22)

All three share: PreToolUse-or-Stop hook + subprocess-spawn-with-
recursion-guard-env-var + Mirror-Sync-Direction consolidator in
settings_merger.py + apex DONE-gate section.
