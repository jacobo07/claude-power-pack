# BCAP-2 Phase 3 — CPP-AGSK-001 Reality Scan (IN PROGRESS, scan only, no implementation) — 2026-11-19, base 0855c18e

Upstream pin (read-only clone, shallow): https://github.com/addyosmani/agent-skills @ 8c99fa36d90068c82d547f7c12a9d67a3e95f4ee. Licence: MIT, (c) 2025 Addy Osmani (LICENSE read; NOTICE with attribution needed before any copy).
Clone lived in the job tmp dir (not durable): re-clone with `git clone --depth 1` and `git checkout 8c99fa36`.

Observed upstream at that pin: 23 skill dirs (backlog said 25; adds accessibility-engineering; verify the count against the backlog table before dispositions), 10 command TOMLs (backlog said nine: a11y, build, code-simplify, constraints, planning, review, ship, spec, test, webperf), evals/, hooks/ (sdd-cache, session-start, simplify-ignore), references/ (7 checklists), scripts/ (validators + floor-guard-reference-test.js + quality-gate-test.js).

CPP owners found so far: modules/skill_router, modules/pp_eval (common/floor/harvest/nightly/runner/verdict), modules/rule_compiler (detectors.py, counterfactual.py, effect_harness.py), modules/done_gate, modules/spec_gate, modules/liveness.
No disposition has been written yet. Nothing in the repo changed besides this file.

## Next exact steps
1. Write vault/programs/bcap-2/agsk/DISPOSITIONS.md: one row per upstream skill (23 observed) + 10 commands, each with exactly one of ALREADY OWNED/EXTEND/CONNECT/MERGE/CONDITIONAL/UPSTREAM-ONLY/REJECT/UNVERIFIED and a CPP owner path that exists.
2. Pick ONE pilot slice: AGSK-C constraint non-weakening. Read upstream skills/constraint-driven-development/SKILL.md (floor = no new suppressions, no stubs, no skipped/deleted tests, no weakened CONSTRAINTS) and scripts/floor-guard-reference-test.js; read modules/rule_compiler/detectors.py first to see whether a diff-weakening detector already exists (grep for ts-ignore/noqa found no obvious owner in modules/rule_compiler).
3. Gate tools/test_bcap2_agsk.py: both poles (clean diff passes; seeded weakening — deleted assertion, added noqa/skip, lowered threshold — each refused by code), disposition-ledger integrity (every upstream skill has one row, owner path exists, pin matches), routing recall/precision for the new card via classify_intent, liveness check.
4. Then deferred-backlog row + backlog Status line + STATE.md (spend, 5-line analysis); commit.
