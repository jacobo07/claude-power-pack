---
phase: 02-quick-ccr-residuals-route-2-0m
plan: 01
subsystem: ccr-stage3-gex44-driver
tags: [ccr, gex44, breaker, fail-closed, regression-test, provenance]
requires: []
provides:
  - "GEX44 driver drive3.sh v3 versioned byte-exact with provenance"
  - "V-DRV-* regression gates proving the breaker measurement and over() fail closed"
affects: [02-04 evidence, Phase 11 knowledge]
tech-stack:
  added: []
  patterns: ["read shell driver as text, extract pure functions, source only those into real bash with a python3 shim", "mutants whose replacement is asserted to change the text"]
key-files:
  created:
    - vault/programs/ccr/stage3/driver/drive3.sh
    - vault/programs/ccr/stage3/driver/MANIFEST.json
    - vault/programs/ccr/stage3/driver/.gitattributes
    - vault/programs/ccr/stage3/driver/README.md
    - tools/test_ccr_driver_breaker.py
  modified: []
key-decisions:
  - "Driver bytes NOT edited: v3 is proven, not re-fixed; the missing-stream-measures-0 observation is an open residual"
  - "One commit for both tasks, as the plan's Task 2 specifies (Task 1 'not yet committed')"
requirements-completed: [REQ-2]
status: complete
duration: ~25 min
completed: 2026-10-15
commits: 1
plan_head_before: 0316acff464e22eb7670aad9739ff3769298bbc8
actuals:
  tasks: 2
  commits: 1
---

# Phase 2 Plan 01: GEX44 driver versioned, breaker fail-closed proven Summary

The v3 GEX44 Stage 3 driver (`drive3.sh`, 3,882 bytes, sha256 `9f74c589...1dd7`, equal to the host's `sha256sum`) is in git unmodified with a manifest and an LF pin, and `tools/test_ccr_driver_breaker.py` drives its real `spent()` and `over()` through bash to prove the breaker fails closed, with three mutants that make the test go red.

## Result

- `DRV_PASS=14/14`, exit 0 (3 tracer gates + 11 expansion gates; INFO lines not counted).
- `CCRPGO_PASS=16/16` (`tools/test_ccr_pgo.py`, regression guard) exit 0.
- Commit `6376f589` (`ccr-v5 p2: version GEX44 drive3.sh v3 + breaker fail-closed regression test`): exactly the five planned paths, no deletions.
- `git check-attr eol text` on `drive3.sh`: `eol: lf`, `text: set`; 0 CR bytes; working tree == HEAD blob after commit.

## Tasks

| # | Task | Outcome |
|---|------|---------|
| 1 | Tracer: fetch byte-exact, drive `over ERR` through bash | DRV_PASS=3/3 first run; fetched bytes matched plan-time observation (3,882 bytes, "(v3)") |
| 2 | Full gate set, 3 mutants, README, commit | DRV_PASS=14/14; mutants detected; committed |

Gates: V-DRV-FILE-VERBATIM, EXTRACT, OVER-ERR-TRIPS, EXTRACT-IS-PURE, HARNESS-POSITIVE-CONTROL (python3 resolved to the shim; duplicate id counted once, sum 1010), STRING-MESSAGE-MEASURED (5000000, tripped), OVER-EMPTY-TRIPS, OVER-NUMERIC-CONTROLS (0 and 4499999 not tripped, 4500000 tripped), CRASHED-MEASUREMENT-IS-ERR, FAILED-INTERPRETER-IS-ERR, OUTPUT-DOMAIN (8 corruption variants all `^(\d+|ERR)$`), MUTANT-OVER-DROPS-ERR, MUTANT-OVER-DROPS-EMPTY, MUTANT-A4-SHAPE (string-message stream yields an empty measurement and over() does not trip).

## Open residual (recorded, not patched)

A unit whose stream file is missing or misnamed makes `spent()` print `0` (a measured zero, not `ERR`), so it is never over the stop; the same holds for a stream whose every line is a string-`message` line. Observed by the INFO characterization lines. Carry to 02-EVIDENCE.md and Phase 11 knowledge. Not covered by this plan: the pkill path, RAM hold, phase cap arithmetic, a live host run.

## Deviations from Plan

### Auto-fixed / environmental

**1. [Rule 3 - Blocking] Fetch quoting**
- **Found during:** Task 1 step 1
- **Issue:** the first fetch attempt (an inline `cmd /c "...> `"$out`""` from a PowerShell script) wrote no file and returned no exit code (quote mangling).
- **Fix:** changed approach (not a retry of the same shape): a `.cmd` batch file in `%TEMP%` performing `ssh ... cat ... < NUL > file` and `sha256sum`, run through `cmd.exe`. The redirect is still cmd-level, so bytes are not re-encoded; local sha256 equals the remote one.
- **Files modified:** none in the repo.

**2. [Tooling] No PowerShell tool in this run**
- The agent had only the Bash tool; the Windows Bash Bridge Guard blocked a direct `git`/`ssh` Bash call. I did not use the guard's escape markers; every shell action ran as `powershell.exe -File <ps1 in %TEMP%>` (and one `cmd.exe //c <cmd file>`), which the guard allowed. All file edits used Write/Edit.

**3. [Branch namespace] Commit on `ccr/v5`**
- The executor's worktree-branch allow-list expects `agent-*` names; the orchestrator explicitly designated `ccr/v5` as the branch for this worktree. `ccr/v5` is not a protected/default branch (main), so I committed there as instructed.

No stubs, no threat flags. Nothing was written on GEX44 (only `true`, `cat` and `sha256sum` were issued).

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: drive3.sh, MANIFEST.json, .gitattributes, README.md, tools/test_ccr_driver_breaker.py
- FOUND: commit 6376f589 on ccr/v5; `git log -1 --format=%s` matched the message file's first line
- Secret scan (`sk-ant-`, `ghp_`, `AKIA`, `BEGIN .*PRIVATE KEY`, `password\s*=`): 0 matches in all five files
