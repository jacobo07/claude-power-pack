---
phase: 00-spec-gen2-freeze-novelty-gate
plan: 03
subsystem: ic-gen2-ledger
tags: [ic-gen2, ledger, bound-context-manager, g2-rules, mutants, d-oq3, d-oq4]
requires: [00-01]
provides:
  - "vault/programs/incremental-cognition/gen2/ledger.json: IC-gen2 pre-registration DRAFT (pillars M reopened, O, P, Q, R), no FROZEN_AT"
  - "tools/ic_gen2.py: bound() over the seven CE globals, problems(led, res, final), six G2 rules, selftest with 29 mutants, main(status|final|selftest)"
  - "wrapper --generation 2 dispatch; gen2 folded into the wrapper --selftest and --final with a distinct ICP_GEN2_VERDICT line (D-OQ3)"
  - "AOP-M..AOP-R traceability rows read by the bound X2 clause"
affects: [00-04, 00-05]
tech-stack:
  added: []
  patterns: ["CE clauses reused under a restore-in-finally context manager, nothing rebound at import", "fixture resolver subclass: synthetic evidence first, real repo fallback, never writes", "every mutant behind a clean control; allowed-loss positive control"]
key-files:
  created:
    - vault/programs/incremental-cognition/gen2/ledger.json
    - tools/ic_gen2.py
  modified:
    - tools/test_incremental_cognition_program.py
    - .planning/workstreams/autonomous-optimization/REQUIREMENTS.md
key-decisions:
  - "HANDOFF_DIR for gen2 is vault/programs/incremental-cognition/gen2/handoffs/ (the plan named the constant without a value)"
  - "G2 rules read gen1 sources and the spec root from the resolver when it offers them (getattr with real-loader defaults), so the selftest drives them end to end through problems() instead of only as pure functions"
  - "Final-mode S0 line is computed after the ledger is read, so a missing or invalid ledger stays COULD_NOT_RUN (exit 2) and cannot recurse into the selftest"
requirements-completed: [AO-01, AO-02]
duration: 40min
completed: 2026-10-06
status: complete
commits: 2
plan_head_before: 70abb1c735035d4cdae1dc9bc1cb0ba86200b719
actuals:
  tokens: 9500
  tasks: 2
  commits: 2
---

# Phase 0 Plan 03: IC-gen2 ledger draft and judge Summary

**The IC-gen2 pre-registration (M reopened, O, P, Q, R, predicted IMPLEMENTED_AND_VERIFIED with P's allowed loss) is judged by CE's own L1-L9/X clauses rebound through `ic_gen2.bound()`, plus six G2 rules each killed by a mutant; the IC wrapper now judges gen2 in `--generation 2`, in its `--selftest` and in its `--final` with a separate `ICP_GEN2_VERDICT`. Plane: gex44.**

## Performance

- Tasks: 2 of 2 complete (task 1 tracer, task 2 auto/tdd); 2 task commits, the SUMMARY commit follows this file
- Files: 2 created, 2 modified; `git diff --stat 70abb1c7 HEAD` before this file: 703 insertions, 20 deletions

## Accomplishments

- `gen2/ledger.json` (draft, no `FROZEN_AT`): `frozen` keys `frozen_note, generation, spec, materiality, denominators, reopens.M, pillars`; materiality and denominators are the parsed gen1 values; `reopens.M` quotes gen1's predicted and rule verbatim plus gen1 FROZEN_AT `18e928af...`; the five rule texts are the plan's verbatim (no check proved one wrong, none changed). `opportunities` is empty for plan 00-04.
- `tools/ic_gen2.py`: `bound()` snapshots and restores `SELF_REL, LEDGER_REL, FROZEN_AT_REL, HANDOFF_DIR, PILLARS, REQS_REL, REQ_ROW` in a `finally`; `problems(led, res=None, final=False)` runs `ce.check_ledger` (+ `ce.check_disposition` when not final) then the G2 rules. G2-B1, G2-GEN1, G2-REOPEN, G2-DENOM, G2-PRED, G2-SPEC (`modules.sdd_os.readiness.assess(path, 3)` must be READY).
- Selftest: 5 controls (clean, final-with-FROZEN_AT-served has no L2, gen1 loaders read and equal, an unreadable pin is None, allowed loss accepted), 29 mutants each `killed by <label>`, `V-IC2-BINDING-RESTORED`, `V-IC2-COULD-NOT-RUN`. The CE clauses gen2 depends on are killed under the gen2 binding: L1 (extra pillar, predicted DONE, unknown owner), L2 (edited rule, no FROZEN_AT in final), L3, L4 (falsification naming another pillar, unpinned evidence), L6, L7, X2 (wrong row, absent row).
- Wrapper: `--generation N` parsed (absent or 1 is today's path; 2 lazy-imports `ic_gen2`; `--pillar` with 2 exits 2). gen1 `--selftest` also prints `ICP_GEN2_SELFTEST` and re-runs `check_binding`; gen1 `--final` is the extracted `_final_gen1()` (same lines, same `ICP_VERDICT`) followed by `ICP_GEN2_VERDICT`; exit 2 if either could not run, 0 only if both pass.

## Task Commits

| Task | Commit | Subject |
|---|---|---|
| 1 (tracer) | 2cefcfc3 | feat(00-03): IC-gen2 ledger draft + tools/ic_gen2.py judge + --generation 2 dispatch |
| 2 | ab096db5 | feat(00-03): IC-gen2 G2 rules + selftest (one mutant per rule) + AOP traceability rows |

Tracer gate: after task 1, `--generation 2 --status`, gen1 `--status` cmp and gen1 `--selftest` all passed (output below) before task 2 started. Tracer verified end-to-end, expanding.

## Verification Observed (plane: gex44, HEAD ab096db5)

- `--generation 2 --status` -> `{"open": ["M", "O", "P", "Q", "R"], "closed": [], "violations": []}`, exit 0.
- `--generation 2 --final` exit 1: exactly 10 FAIL lines (`L2 not frozen`, five `L3`, four `L8`) and `ICP_GEN2_VERDICT=FAIL failures=10`. Pre-freeze red, reported verbatim, never claimed green.
- `--generation 2 --pillar M` -> `ICP_GEN2_VERDICT=COULD_NOT_RUN --pillar applies to generation 1 only`, exit 2.
- `--generation 2 --selftest` exit 0, `ICP_GEN2_SELFTEST=PASS`, 29 `V-IC2-MUT-... killed by` lines (acceptance asks 15), plus `V-IC2-CLEAN`, `V-IC2-BINDING-RESTORED`, `V-IC2-ALLOWED-LOSS-ACCEPTED`.
- `--selftest` exit 0 with `CEP_SELFTEST=PASS`, `ICP_GEN2_SELFTEST=PASS`, `ICP_SELFTEST=PASS`.
- `--final` exit 1: `CEP_VERDICT=FAIL failures=12`, `ICP_VERDICT=FAIL failures=1`, `ICP_GEN2_VERDICT=FAIL failures=10`. `diff` of the pre-change gen1 `--final` output against the new one adds only the ten gen2 FAIL lines and the verdict line; every gen1 line is unchanged (inherited gen1 state per D-OQ3).
- gen1 `--status` output: `cmp` before/after exit 0 (byte-identical).
- Ledger python assertion from the acceptance criteria: passes; `gen2/FROZEN_AT` absent.
- `grep -c "^| AOP-[MOPQR] |"` on the workstream REQUIREMENTS.md prints 5.
- `git diff --name-only 3f48f2e3 HEAD` lists none of: both CE/SC program verifiers, gen1 `ledger.json` / `FROZEN_AT` of IC, CE or SC, root `.planning/STATE.md`, `tools/gsd_mission.py`; `git diff --name-only --diff-filter=A 3f48f2e3 HEAD -- modules` is empty.
- Leak drill (T-00-12): with `ic_gen2.bound` replaced by a version that sets `LEDGER_REL` and never restores it, the wrapper `--selftest` prints `FAIL V-IC2-BINDING-RESTORED`, `ICP_GEN2_SELFTEST=FAIL`, `FAIL B1 CE global LEDGER_REL rebound away from this program`, `ICP_SELFTEST=FAIL` and exits 1.

## TDD record (task 2)

RED run before the rules existed (stubs returning `[]`, committed nowhere): `--generation 2 --selftest` exit 1, the controls and the CE-clause mutants green, and 15 G2 mutants printed `SURVIVED (expected a G2-... line, got [])`: program-foreign, generation-1, gen1-frozen-drift, reopen-misquoted, reopen-predicted-misquoted, reopen-missing, reopen-wrong-gen1-sha, denominator-calls-changed, materiality-changed, Q-predicted-MERGED, P-rule-without-allowed-loss, roadmap-phases-missing, spec-missing, spec-key-absent, spec-not-ready. After the rules, 14 of those were killed; `gen1-frozen-drift` still survived, which was the fixture, not the rule.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Selftest fixture let the gen1 pin follow the mutated working-tree copy**
- **Found during:** Task 2, first green run (`gen1-frozen-drift SURVIVED` with the rule implemented)
- **Issue:** `Fx` defaulted the pinned gen1 frozen to the same object it served as the working-tree copy, so a drifted working tree was compared with itself and G2-GEN1 could never fire in that mutant.
- **Fix:** the pin defaults to an independent real read; only an explicit `gen1_pin=` argument changes it. All 29 mutants then killed.
- **Files modified:** tools/ic_gen2.py
- **Commit:** ab096db5

**2. [Rule 3 - Blocking] Gen1 `--final` body extracted into `_final_gen1()`**
- **Found during:** Task 2 wrapper wiring
- **Issue:** the plan keeps the gen1 verdict unchanged and adds gen2 after it, but the gen1 branch returned from inside `main`, so gen2 could not run after it nor could the exit codes be combined.
- **Fix:** moved the existing lines verbatim into `_final_gen1()`; `--final` calls it, then `ic_gen2.main("final")`, then re-checks the gen1 binding. gen1 output is unchanged (diff shown above).
- **Files modified:** tools/test_incremental_cognition_program.py
- **Commit:** ab096db5

**Total deviations:** 2 auto-fixed (1 bug in my fixture, 1 blocking refactor). **Impact:** none on scope; no rule text or plan-fixed output line changed.

## Authentication Gates

None.

## Known Stubs

None. The gen2 ledger `state`, `reviews`, `deltas` and `opportunities` are intentionally empty pre-registration content; plan 00-04 fills `opportunities`, and open pillars are the point of the draft (they are what the pre-freeze `--final` red lines report).

## Threat Flags

None. `ic_gen2` adds no endpoint or auth path; gate execution still goes through CE `gate_argv_problem` with `SELF_REL` bound to the wrapper under gen2 (T-00-14), and its only subprocess is the read-only `git show` of gen1's ledger at its FROZEN_AT.

## Issues Encountered

- `ENVPF`, `PFP`, `LG` baselines were not re-run: they belong to plan 00-02 and nothing in this plan touches them.
- Inherited reds are unchanged and reported verbatim: IC gen1 `--final` L3 for A, B, C, I, J, K, M, N and four L8 lines.

## Next Phase Readiness

Plan 00-04 can add `opportunities` rows (outside `frozen`, so the freeze does not cover them) and the champion numbers; plan 00-05 audits, writes `gen2/FROZEN_AT`, and calls `ic_gen2.problems(led, None, False)` for its post-freeze L2 drill. Rule texts become immutable at that freeze.

## Self-Check

- Created files exist: `tools/ic_gen2.py`, `vault/programs/incremental-cognition/gen2/ledger.json` (both present, 20966 and 10500 bytes).
- Commits `2cefcfc3` and `ab096db5` present on `mission/autonomous-optimization-gen2`; `git rev-list --count 70abb1c7..HEAD` = 2 before this file.
- All task acceptance criteria and plan-level verification commands re-run after the last commit (see Verification Observed).

## Self-Check: PASSED
