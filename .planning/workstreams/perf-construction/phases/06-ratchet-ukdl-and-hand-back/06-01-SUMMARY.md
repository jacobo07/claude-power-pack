---
phase: 06-ratchet-ukdl-and-hand-back
plan: 01
subsystem: inheritance-proof
tags: [perf-construction, inheritance, mutant-matrix, standing-gate, PERF-06]
requires:
  - phase: 05-critical-path-audit
    provides: final-gates record, reachability baseline, hook critical-path suite
provides:
  - phase-local checker (selftest, manifest, matrix) with a closed verdict set
  - recorded manifest of the Phase 2-5 standing gates
  - recorded mutant matrix and the inheritance map (06-INHERITANCE.md)
affects: [06-02, 06-03]
tech-stack:
  added: []
  patterns: [closed verdict set, control-first scratch mutant matrix, process-group timeout kill]
key-files:
  created:
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/inherit_check.py
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/06-INHERITANCE.md
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/records/06-01-T1.selftest.txt
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/records/06-01-T1.tracer.txt
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/records/06-01-T2.manifest.txt
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/records/06-01-T3.matrix.txt
  modified:
    - .planning/workstreams/perf-construction/STATE.md
key-decisions:
  - "Phase 3 and Phase 5 proofs are inherited only by their own suites (OWN_SUITE_ONLY); not wired (OWNER DECISION NEEDED (11))"
  - "Matrix scratch copy also archives hooks, tests, vault/specs and the Phase 5 inventory baseline (F2)"
requirements-completed: [PERF-06]
status: complete
duration: ~30 min
completed: 2026-11-23
commits: 3
plan_head_before: 5fecb5a28e0b7171a30e55f5b045e83ab0c53ec7
actuals:
  tokens: 11400
  tasks: 3
  commits: 3
---

# Phase 6 Plan 01: Inheritance proof Summary

A phase-local checker with a closed verdict set measured which Phase 2-5 proofs a standing gate defends: the Phase 2 and Phase 4 proofs are ENFORCED by the `bench-gate` row, the Phase 3 and Phase 5 proofs are OWN_SUITE_ONLY (no standing gate runs their suites).

## Results

- **Selftest** `INHERIT_SELFTEST=9/9`: PASS, exit-1 FAIL, silent UNPARSED, over-timeout TIMED_OUT (grandchild process gone), lower or higher count FAIL, missing executable NOT_RUN, baseline 6/7 BASELINE_MATCH and 5/7 FAIL, footer exit codes, and a mutant control (count comparison disabled in memory turns the lower-count case green).
- **Manifest** (`records/06-01-T2.manifest.txt`, one run, exit 0): `INHERIT_JUDGED=14/15`, `INHERIT_PASS=14/14`, `SKIPPED=1`, `NOT_JUDGED=0`. git_invocation 6/7 and reachability (56 offenders, equal by unit name) are BASELINE_MATCH, pre-existing debt, not passes. s9 red-team SKIPPED_BY_POLICY (UNJUDGED, no clean control run). Ledger and floors sha256 SAME.
- **Matrix** (`records/06-01-T3.matrix.txt`, verified by `matrix --verify-record`): control passed the standing gate and four owning suites; `MATRIX: ENFORCED=3 OWN_SUITE_ONLY=2 SURVIVED_ALL=0 NOT_DISCRIMINATING=0`. MX1 (Phase 4 pressure judge), MX2 (Phase 4 reader), MX3 (Phase 2 `verdicts_fail` met_target) ENFORCED; MX4 (Phase 3 `CENSORED_STATES` without FAILED) and MX5 (Phase 5 FLAG_WEAKENED condition inverted) OWN_SUITE_ONLY. Each target occurred once and compiled.
- **Scheduler grep**: `hooks/` 0, `scripts/` 0, `tools/` 33 files mention `verify_spp.py`; no scheduler found, UNKNOWN whether the laptop or any cron runs it.
- **Tree**: tools, modules, hooks, vault/config unchanged; ledger and floors hashes SAME; no host absolute path in the records.

## Task commits

1. Task 1 (tracer, TDD selftest controls): 088b0ce8
2. Task 2 (manifest record): aed9cb00
3. Task 3 (matrix, map): ae1b1c47

## Deviations from Plan

**1. [Rule 3 - Blocking] Scratch copy needed more paths for a passing control (F2)**
- **Found during:** Task 3, first matrix run (control failed on all but one suite, five NOT_DISCRIMINATING, not committed)
- **Issue:** the five archive paths of the plan omit `hooks/`, `tests/`, `vault/specs/` and the Phase 5 `05-01-inventory-baseline.json`, which the integrity, metrology and critical-path suites read.
- **Fix:** added those read-only inputs to the archive; the record prints them on `ADDED_PATHS`.
- **Files modified:** `inherit_check.py`
- **Commit:** ae1b1c47

**2. [Rule 2 - Missing] First-FAIL-line selection prefers real FAIL result lines** over PASS lines that merely carry the word FAIL, so a mutant's first failing line is the actual failing gate.

**3. [Rule 2 - Missing] `hook_boundary` runs with a fresh temporary HOME** (as the plan says) and the temp directory is removed after the row; the control rows print no host paths because all printed text is scrubbed.

TDD note: Task 1 is a tracer whose behaviours are the selftest gates; the RED shape is carried by the in-file mutant control (`V-INH-MUTANT-CONTROL`) rather than a separately committed red record, because the plan lists only the selftest and tracer records for T1.

## Known Stubs

None.

## Threat Flags

None. The matrix writes mutants only under a `tempfile.mkdtemp(prefix="p6-inherit-")` scratch directory (path asserted before removal); the repo tree check and hash check ran after.

## Issues / Gaps for the hand-back

- Two proofs (Phase 3, Phase 5) are defended by no standing gate: OWNER DECISION NEEDED (11), left unwired. Suite timings disagree between the planning session and this run (n=1 each), so budget fit is unsettled.
- The other manifest suites (a5_u6, arm_preflight, gsd_mission_*, hook_boundary) have no mutant: whether a standing gate defends them was not measured.
- Whether anything schedules the `bench-gate` row: UNKNOWN. Laptop behaviour: untouched, zero laptop-judged items.

## Self-Check: PASSED

- Files exist: inherit_check.py, 06-INHERITANCE.md, four records.
- Commits found: 088b0ce8, aed9cb00, ae1b1c47.
