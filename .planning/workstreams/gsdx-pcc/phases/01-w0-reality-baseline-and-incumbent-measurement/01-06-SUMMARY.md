---
phase: 01-w0-reality-baseline-and-incumbent-measurement
plan: 06
subsystem: phase-end evidence
tags: [evidence, production-reality, denominator]

requires: [01-01, 01-02, 01-03, 01-04, 01-05]
provides:
  - 01-EVIDENCE.md (10 sections, incumbent table verbatim, Production Reality verdicts)
  - fresh phase-end gate logs
  - DENOMINATOR R01 DONE with evidence
affects: [Phase 2 ULTRA-PLAN starts from 01-EVIDENCE.md]

actuals:
  tasks: 2
  commits: 2

key-decisions:
  - "01-EVIDENCE.md was assembled by a script. The prose is written once, and the incumbent table, wall, Timelines, UNKNOWN and the offender list are inserted verbatim from the committed files. 0 table lines are missing (checked line by line)."

requirements-completed: [R01]
---

# 01-06 Summary: Phase 1 evidence

## Commits
- `f83f5973` docs(gsdx-pcc-01): Phase 1 evidence -- R01 fixed red-first, premises, incumbent baseline
- `8c997884` docs(gsdx-pcc-01): DENOMINATOR R01 dispositioned with evidence

## Evidence
- Phase end, fresh:
  - `GSDX_GATE_PROVIDER_PASS=18/18  threshold=18/18`, `EXIT=0`.
  - Liveness: `gate offenders: 0`, `EXIT=0`.
- 01-EVIDENCE.md:
  - It has 10 `## ` sections.
  - It contains 57, 61, the UKDL id, CLASE 4, CLASE 2 and `modules/cognitive_os/scheduler.py:94`.
  - Every line of `01-incumbent-suites-table.md` is present.
- R01 is DONE. Its evidence is the fix 58934936, the phase-end 18/18, the drill KILLED exit 0, the UKDL id and 01-EVIDENCE.md. `git show --numstat` = `1 1`.
- `git status --porcelain` was empty after the R01 commit. Nothing was pushed.

## Production Reality (from 01-EVIDENCE.md)
- R01 is PROVEN on Windows and UNJUDGED on POSIX.
- The premises are PROVEN.
- Liveness is OBSERVED: the debt is frozen, not cleared.
- The suite times and timelines are OBSERVED.
- The incumbent mutation-suite timing is UNJUDGED (memory-pressure reaper).
