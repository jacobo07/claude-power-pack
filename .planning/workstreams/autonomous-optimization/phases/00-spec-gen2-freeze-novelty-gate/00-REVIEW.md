---
phase: 00-spec-gen2-freeze-novelty-gate
reviewed: 2026-10-06T00:00:00Z
depth: quick
iteration: 3
files_reviewed: 5
files_reviewed_list:
  - tools/gex44_env_preflight.py
  - tools/ic_gen2.py
  - tools/test_ao_p0.py
  - tools/test_gex44_env_preflight.py
  - tools/test_incremental_cognition_program.py
findings:
  critical: 0
  warning: 0
  info: 5
  total: 5
status: clean
---

# Phase 00: Code Review Report (iteration 3, converged)

**Reviewed:** 2026-10-06
**Depth:** quick (iteration 3 re-review of commit 52e7b3b0; iterations 1 and 2 were standard)
**Files Reviewed:** 5
**Status:** clean (no Critical or Warning remains; four Info items carried forward plus one new)

## Summary

Final re-review of commit 52e7b3b0 (`fix(00): WR-05 keep generation-1 selftest independent of ic_gen2`). I read the
whole diff and the surrounding `selftest()`, `_final_gen1()`, `main()`, `_companion_wanted()` and `_gen2_companion()` code in
`tools/test_incremental_cognition_program.py`, and re-ran the two selftest modes myself:

- `--selftest` (bare): rc 0, `ICP_GEN2_SELFTEST=PASS`, `ICP_SELFTEST=PASS`. `V-ICP-GEN1-SELFTEST-NO-GEN2` and
  `V-ICP-GEN2-BLOCKED-CONTROL` both print `ok`.
- `--generation 1 --selftest`: rc 0, `ICP_SELFTEST=PASS`, a visible `SKIP` line for the three gen2-dependent gates ("not
  counted as a pass"), and no `ICP_GEN2_*` line.

## Resolved findings

| ID | Commit | State |
|----|--------|-------|
| WR-01 | e3064323 | Resolved (iteration 2 verified) |
| WR-02 | c1800d57 | Resolved (iteration 2 verified; the `audit_rules` owner-list residual is acknowledged in 00-REVIEW-FIX.md) |
| WR-03 | c90fe222 | Resolved: completed by WR-05 below |
| WR-04 | bd0516cc | Resolved (iteration 2 verified) |
| WR-05 | 52e7b3b0 | Resolved (verified this iteration) |
| IN-06 | 52e7b3b0 | Resolved: `saved_import` is gone (grep finds no reference) |

### WR-05 verification (52e7b3b0)

- The unguarded `_import_gen2()` inside `selftest()` is now behind `gen2_gates`. With `--generation 1` (`companion` is
  False) `selftest(gen2_gates=False)` prints the SKIP and returns before any import. `_final_gen1(gen2_gates=companion)` and
  the `--selftest` branch of `main` thread the flag through. The `final_with` stub was updated to `lambda *a, **k: 0` to
  match the new signature.
- A bare run guards the import with `except ImportError`. `ModuleNotFoundError` is a subclass, so the blocked case is
  covered. It prints a SKIP that is not counted as a pass and sets `g2mod = None`, so the ledger-patch gate and
  `V-ICP-GEN2-PRESENT-CONTROL` are skipped as a unit.
- The new gates observe the import instead of inferring it. The child runs the script under a meta-path finder that prints
  `IC_GEN2_IMPORT_ATTEMPTED` and raises. `V-ICP-GEN1-SELFTEST-NO-GEN2` asserts rc 0, `ICP_SELFTEST=PASS`, no attempt marker
  and no `ICP_GEN2_` line. `V-ICP-GEN2-BLOCKED-CONTROL` runs the same blocker on a bare `--selftest` and requires the
  attempt marker and `ICP_GEN2_SELFTEST=COULD_NOT_RUN`. The control proves the blocker can detect an import, so the first
  gate can fail.
- Recursion is bounded: the children run with `ICP_SELFTEST_NO_SUBPROCESS=1` and print a SKIP instead of spawning again.
  `runpy.run_path(..., run_name='__main__')` keeps `__file__` set, so `Path(__file__).resolve().parent` still resolves the
  tools directory in the child.
- Docstring (lines 68-75) now matches the behavior: gen2 gates run only on a bare invocation and are skipped without
  importing ic_gen2 under `--generation 1`.

No regression found. Exit-code contracts (`--generation 1 --final` returns gen1's own code; bare `--final` folds gen2's 0/1
and ignores a gen2 answer of 2) are unchanged by this commit.

## Info

### IN-01: Literal invisible BOM character in source (carried forward)

**File:** `tools/ic_gen2.py` (re-locate by the `lstrip` call near the git-stdout parse; about line 563)
**Issue:** `r.stdout.lstrip("<U+FEFF>")` embeds a raw U+FEFF in the literal. It is invisible in review, trips injection
scanners, and would silently become `lstrip("")` after an editor round-trip. The same pattern (`lstrip("﻿")` with a raw
U+FEFF, line 174) also appears in `tools/test_incremental_cognition_program.py`, and the injection scanner flagged that
file on read.
**Fix:** Use the escape `lstrip("﻿")`, as `front_matter_fields` already does in this file.

### IN-02: Temp directories are never removed (carried forward)

**File:** `tools/test_ao_p0.py:31, 190, 387`
**Issue:** `_STATE_DIR`, each `make_temp_repo` directory and the `aop0-novrepo-` repo are created with `mkdtemp` and never
deleted, so each run leaks several directories.
**Fix:** `atexit.register(shutil.rmtree, path, ignore_errors=True)` for each, or one module-level `TemporaryDirectory`.

### IN-04: Remaining test gaps around the pp_install accept paths (carried forward)

**File:** `tools/test_gex44_env_preflight.py:431-445`
**Issue:** No case asserts that the ancestry path emits no `floor_by_pick` finding, and no case covers a right-floor trailer
with the required file dropped while the floor object is absent (`V-ENVPF-PP-PICK-REQUIRED-FILE` covers the floor-present
variant only).
**Fix:** Add `expect_no_finding` on the ancestry path, and a `make_pick_install(floor_absent=True, drop_required=True)` case.

### IN-05: Evidence files keyed by basename in `g2_champ`; `population` check optional (carried forward)

**File:** `tools/ic_gen2.py:257-262, 290` (approximate)
**Issue:** `texts[ref.rsplit("/", 1)[-1]]` keys by basename, so two evidence entries with the same basename overwrite each
other, and `summ` is picked by `k.endswith("summary.txt")`. `if "population" in r:` makes the population check optional, so
dropping the key skips it with no failure line.
**Fix:** Key by the full `ref`, select by exact expected names, and treat a missing `population` as a failure.

### IN-07: Child-process timeout in the new WR-05 gates is uncaught (new, low impact)

**File:** `tools/test_incremental_cognition_program.py:1403-1412` (helper at `_selftest_with_gen2_blocked`)
**Issue:** `subprocess.run(..., timeout=120)` raises `subprocess.TimeoutExpired` on a hung child. Nothing catches it, so a
slow or hung child crashes the whole selftest with a traceback instead of printing a `FAIL V-ICP-GEN1-SELFTEST-NO-GEN2`
line. The exit code is still non-zero, so this is a diagnostics defect, not a missed failure. Measured child time is well
under 3 s.
**Fix:** Catch `subprocess.TimeoutExpired` in the helper and return `(124, "")` so the gate reports FAIL with its own label.

---

_Reviewed: 2026-10-06_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: quick (iteration 3)_
