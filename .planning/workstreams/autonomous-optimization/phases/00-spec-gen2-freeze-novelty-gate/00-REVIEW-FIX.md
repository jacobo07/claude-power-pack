---
phase: 00-spec-gen2-freeze-novelty-gate
fixed_at: 2026-10-06T00:00:00Z
review_path: .planning/workstreams/autonomous-optimization/phases/00-spec-gen2-freeze-novelty-gate/00-REVIEW.md
iteration: 2
findings_in_scope: 1
fixed: 1
skipped: 0
status: all_fixed
---

# Phase 0: Code Review Fix Report

**Fixed at:** 2026-10-06
**Source review:** .planning/workstreams/autonomous-optimization/phases/00-spec-gen2-freeze-novelty-gate/00-REVIEW.md
**Iteration:** 2

**Summary:**
- Findings in scope: 1 (WR-05; fix_scope critical_warning, 0 critical). IN-06 was also fixed because it sat on the same lines.
- Fixed: 1
- Skipped: 0

Plane: gex44. Edits and verification ran in the main checkout of the already-isolated worktree
`.claude/worktrees/ao-gen2` (the executor brief forbids creating a further worktree), so the numbers below are
reproducible from the tree the reader is looking at. No immutable object was touched (gen2 ledger `frozen`,
`gen2/FROZEN_AT`, gen1 ledgers, `test_cognitive_economy_program.py`, `test_skill_capability_program.py`).
`vault/progress.md` is hook output and was not committed.

## Fixed Issues

### WR-05: generation-1 `--selftest` (including explicit `--generation 1`) still imported ic_gen2 unguarded

**Files modified:** `tools/test_incremental_cognition_program.py`
**Commit:** 52e7b3b0
**Status:** fixed: requires human verification (control flow of a gate that decides when other gates run)
**Applied fix:**
- `selftest(verbose=True, gen2_gates=True)` and `_final_gen1(gen2_gates=True)` take a flag; `main` passes
  `gen2_gates=companion`, so an explicit `--generation 1 ...` run never reaches the gen2 gates and never attempts the
  import. It prints a visible `SKIP V-ICP-GEN2-LEDGER-ABSENT-DEGRADES / V-ICP-GEN2-PRESENT-CONTROL / V-ICP-GEN1-SELFTEST-NO-GEN2
  (--generation 1: ic_gen2 is not loaded; not counted as a pass)` line instead.
- On a bare run, `_import_gen2()` inside `selftest()` is wrapped: `ImportError` prints
  `SKIP V-ICP-GEN2-LEDGER-ABSENT-DEGRADES / V-ICP-GEN2-PRESENT-CONTROL (ic_gen2 not importable: ...); not counted as a pass`
  and both gates are skipped. A SKIP never calls `say`, so it is neither a pass nor a fail and cannot hide behind a count.
- Two new gates drive the script in a child process in which a meta-path finder blocks `ic_gen2` and prints
  `IC_GEN2_IMPORT_ATTEMPTED` on every attempt (so "never imported" is observed, not inferred):
  `V-ICP-GEN1-SELFTEST-NO-GEN2` (`--generation 1 --selftest` exits 0, `ICP_SELFTEST=PASS`, no import attempt, no
  `ICP_GEN2_*` line) and its positive control `V-ICP-GEN2-BLOCKED-CONTROL` (the same blocker on a bare `--selftest` does
  record the attempt, prints `ICP_GEN2_SELFTEST=COULD_NOT_RUN` and still exits 0). The children set
  `ICP_SELFTEST_NO_SUBPROCESS=1` so they do not recurse.
- The `_final_gen1` stub in `V-ICP-GEN1-FLAG-HONOURED` became `lambda *a, **k: 0` to accept the new keyword. Module
  docstring updated to describe the SKIP behaviour.
- IN-06: the unused `saved_import = _import_gen2` line is deleted.

Red first: before the wiring, `--generation 1 --selftest` printed `FAIL V-ICP-GEN1-SELFTEST-NO-GEN2` and exited with
`ICP_SELFTEST=FAIL` (the import was attempted). The first draft of the gate also mis-matched `ICP_GEN2` inside the `ok` label
text of other gates; it now matches only lines that start with `ICP_GEN2_`. After: `--generation 1 --selftest` rc 0 with the
SKIP line; bare `--selftest` rc 0 with both new gates `ok`; `--generation 1 --final` with ic_gen2 blocked prints no import
attempt and no `ICP_GEN2` line.

## Skipped Issues

None. Info findings IN-01, IN-02, IN-04 and IN-05 are outside `fix_scope: critical_warning` and were not attempted.

## Verification (run after the commit, plane gex44, main checkout of worktree ao-gen2)

| Command | Result |
|---|---|
| `python3 tools/test_incremental_cognition_program.py --selftest` | rc 0, `CEP_SELFTEST=PASS`, `ICP_GEN2_SELFTEST=PASS`, `ICP_SELFTEST=PASS` |
| `python3 tools/test_incremental_cognition_program.py --generation 1 --selftest` | rc 0, `CEP_SELFTEST=PASS`, `ICP_SELFTEST=PASS` (gen2 gates SKIPped, visible) |
| `python3 tools/test_incremental_cognition_program.py --generation 2 --selftest` | rc 0, `ICP_GEN2_SELFTEST=PASS` |
| `python3 tools/test_incremental_cognition_program.py --generation 2 --audit` | rc 0, `ICP_GEN2_AUDIT=PASS frozen_sha256=a8ac15d894a72c74eb71901b3081c7a6a20a0ee2d9da085a270dd015a204d39e` (unchanged) |
| `python3 tools/test_gex44_env_preflight.py --drill` | rc 0, `DRILL killed=11/11`, clean-after 65/65 |
| `python3 tools/test_ao_p0.py` | rc 0, `AOP0_PASS=22/22 threshold=22/22` |

## History

### Iteration 1 (fixed 4 of 4: WR-01..WR-04, all_fixed)

- WR-01 (e3064323, `tools/gex44_env_preflight.py`, `tools/test_gex44_env_preflight.py`): the cherry-pick trailer match is
  anchored to a whole line; new gate `V-ENVPF-PP-TRAILER-MIDLINE-STALE` and drill mutant M11 (drill 11/11, preflight 65/65).
- WR-02 (c1800d57, `tools/ic_gen2.py`; requires human verification): `g2_champ` judges a malformed champion number
  instead of raising; the `audit_rules` A4 mixed-type sort is a mismatch line. Residual: the `owner` list guard is
  unreachable from here (crashes earlier in the never-edit CE verifier).
- WR-03 (c90fe222, `tools/test_incremental_cognition_program.py`; requires human verification): `--generation 1` is
  generation 1 only (no ic_gen2 import, gen1's own exit code); a bare `--selftest`/`--final` keeps the gen2 companion and
  degrades to `COULD_NOT_RUN` lines through `_gen2_companion`; IN-03 (trailing `--generation`) fixed with it. WR-05 above
  closed the part of this that still imported ic_gen2 from inside `selftest()`.
- WR-04 (bd0516cc, `tools/ic_gen2.py`): G2-CHAMP evidence refs are confined against `..` traversal, with two mutant gates
  and fixture controls.

---

_Fixed: 2026-10-06_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 2_
