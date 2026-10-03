---
phase: 03
checker: gsd-plan-checker (sonnet), read-only; persisted by the orchestrator (epoch 3)
pass: 1
verdict: ISSUES_FOUND
blockers: 0
warnings: 5
revision: requested from the planner, all five warnings
---

# Phase 3 plan check, pass 1

## The six requested checks

1. Each roadmap criterion maps to a verify command: **PASS.** SC1: gates 2, 3, 7-14. SC2: gates 16-19.
   SC3: gates 2, 22, 26. SC4: gates 28-29. SC5: gates 3, 10, 18, 22, with gate 2 as the positive control.
2. `legacy=` cannot switch admission off for the real tree: **PASS, with gap W1.** `check_legacy`
   refuses root=None and any path ending `vault/tower/baselines`, and runs first in `judge`. Gates 20 and
   21 drive it, with controls. `BASELINES_DIR` has no environment override.
3. The grandfathered table comes from 03-F0-REFERENCE.md and is checked against a fresh measurement:
   **PASS.** The seven hashes match character for character, and 03-04 T3 checks them three ways
   (`F0_THREE_WAY=EQUAL rows=7`).
4. RED-first ordering: **PASS.** 03-01 T1 records `TOWER_ADMISSION_PASS=1/6` before the module exists.
   03-03 T3 records 21/25 before UNADMITTED is emitted.
5. Every refusal has a control, and the suite floors are named: **PASS.** All 15 Phase 1 and 2 floors are
   named.
6. Size, order, forward dependencies: **PASS.** Tasks per plan are 2, 2, 3 and 3. The dependency chain is
   linear, with no forward file dependency.

## Findings

- **W1 (03-03 T1, gate 20).** The real-tree refusal is tested in one spelling only. Add refusal arms
  for a trailing `\`, a relative path, an `x\..\baselines` form, and a junction or symlink if cheap.
  Require realpath, normcase and separator stripping in `check_legacy`.
- **W2 (03-02 T1, gate 15).** The named-constant check sees only the tokens from gates 1-14. Collect
  every `admit` token at module level, and assert membership in `REASONS` after all gates have run.
- **W3 (D4 and the phase gate).** The offender-set comparison and the EVIDENCE checks run from a
  throwaway script, with no `<verify>` pass/fail line. Add committed verify commands for: offender names
  against `03-liveness-before.json` (non-zero exit on growth), the `tower/admission` registry row, and the
  empty git log/diff over `vault/tower/baselines`. Add 03-04-SUMMARY.md to the files of 03-04 T3.
- **W4 (all verify blocks).** Floors are checked only through the exit code, so lowering `EXPECTED` in a
  suite would pass. Compare each `_PASS=n/m` against the floor table, and set the hermetic temp HOME,
  USERPROFILE and CLAUDE_STATE_DIR in every regression loop, not only in 03-03 T3 and 03-04 T3.
- **W5 (03-01 T1).** The task is oversized (nine paths, two commits, an estimated 95k tokens). Split
  Step 0 (start state, F0 table, floors, liveness JSON) into its own task.

## Info (no revision)

- The LF/CRLF identity design and `is_grandfathered` failing closed on OSError are sound.
- The `legacy=(0,)` migrations keep every gate name and `EXPECTED` value.
- Gate 24 relies on `would_block_on_violated`, and nobody has verified that it exists in `donegate.judge`. The
  executor reads `donegate.py` before writing that predicate.
