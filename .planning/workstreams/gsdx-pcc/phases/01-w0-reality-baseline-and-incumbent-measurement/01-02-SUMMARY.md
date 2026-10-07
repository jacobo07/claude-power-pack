---
phase: 01-w0-reality-baseline-and-incumbent-measurement
plan: 02
subsystem: incumbent measurement instrument
tags: [measurement, hermetic, guard, jsonl, windows]

requires: []
provides:
  - tools/gsdx_reality_baseline.py (fingerprint, suites, unknown, table), the instrument plan 01-05 and Phase 9 consume
  - tools/test_gsdx_reality_baseline.py V-RB-* gates, GSDX_REALITY_BASELINE_PASS=16/16
affects: [01-05 incumbent table, Phase 9 X vs X' comparison]

actuals:
  tasks: 2
  commits: 2

key-files:
  created:
    - tools/gsdx_reality_baseline.py
  modified:
    - tools/test_gsdx_reality_baseline.py (RED Task-1 gates were committed by the previous worker in 903005c2; Task-2 gates added here)

key-decisions:
  - "Gate count is 16, not the plan's 15: the previous worker added V-RB-GUARD-EXCLUDES-ONLY-NAMED for the measured sweep_heartbeat.json confound (01-01 Task 1). The guard excludes only DEFAULT_GUARD_EXCLUDE=('sweep_heartbeat.json',), records a change to it as excluded_changed, and its control still trips on any other file."
  - "The fingerprint carries a sha256 digest over (path, size, mtime_ns) of non-excluded files; SAME/CHANGED is decided by the digest, and changed files are named by mtime above the recorded max."
  - "Executed inline in the main session (PowerShell). Subagent sessions have no PowerShell tool, and the Windows Bash guard blocks git and python."

requirements-completed: []
---

# 01-02 Summary: reality-baseline instrument

## Commits
- `a2bec412` feat(gsdx-pcc-01): reality-baseline instrument -- guarded hermetic suite timing
- `77fcf1e8` feat(gsdx-pcc-01): reality-baseline instrument -- in-copy runs, UNKNOWN rows, table

## RED evidence
- Task 1: the tool was absent at `903005c2`, so the committed suite printed `FAIL V-RB-TOOL-EXISTS` and `GSDX_REALITY_BASELINE_PASS=0/16`, with exit 1.
- Task 2: the run with only the `LIVE_MUTATING` constant present gave `GSDX_REALITY_BASELINE_PASS=12/16`, exit 1. It failed four gates: V-RB-LIVE-MUTATING-REFUSED (rc=0, 2 rows), V-RB-IN-COPY-ISOLATED (in_copy=False, live SHA changed), V-RB-UNKNOWN-ROW (rc=2) and V-RB-TABLE (rc=2). V-RB-TIMEOUT was already green, because Task 1's run loop already handled `TimeoutExpired`. That gate was never red, so it never failed against an absent implementation. It still asserts the timeout row's shape.

## GREEN evidence
- `python tools/test_gsdx_reality_baseline.py` printed `GSDX_REALITY_BASELINE_PASS=16/16  threshold=16/16` and exited 0.
- A real smoke run with the default guard (`~/.claude/state/gsd-x`) used `suites --suite tools/test_gsd_x_goal_convergence.py --runs 1`:
  - After Task 1: 3.628 s, rc=0, `GSDX_GOAL_CONV_PASS=29/29`, guard SAME, exit 0.
  - After Task 2: 3.287 s, rc=0, `GSDX_GOAL_CONV_PASS=29/29`, guard SAME, exit 0.

## Deviations
- The default suite glob drops LIVE_MUTATING names. As a result, a no-`--suite` run never refuses; it skips the mutation suite. Plan 01-05 must time that suite explicitly with `--in-copy`.
