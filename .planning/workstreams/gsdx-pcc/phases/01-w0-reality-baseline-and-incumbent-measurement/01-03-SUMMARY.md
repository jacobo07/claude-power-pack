---
phase: 01-w0-reality-baseline-and-incumbent-measurement
plan: 03
subsystem: goal timeline instrument
tags: [measurement, goal-log, hermetic, cli]

requires: []
provides:
  - tools/gsdx_goal_timeline.py (recorded, fixture, pure timeline()) for plan 01-05, Phase 3 and Phase 9
  - tools/test_gsdx_goal_timeline.py V-TL-* gates, GSDX_GOAL_TIMELINE_PASS=8/8
affects: [01-05 recorded and fixture timelines, judge replay figures]

actuals:
  tasks: 2
  commits: 2

key-files:
  created:
    - tools/gsdx_goal_timeline.py
    - tools/test_gsdx_goal_timeline.py

key-decisions:
  - "Event types are imported from the goal package (DECLARED, DISPATCHING, RUNNING, ENDED, RECEIPT, JUDGED); none are re-typed."
  - "The oblige step carries `--text \"prove it\"`, as the proven sequence at test_gsd_x_goal_cli.py:196-198 does. The plan's step list omitted it."
  - "Executed inline in the main session (PowerShell), as in 01-01 and 01-02."

requirements-completed: []
---

# 01-03 Summary: goal timeline instrument

## Commits
- `8aedb547` feat(gsdx-pcc-01): goal timeline instrument -- recorded goal over a verified copy
- `e9a61556` feat(gsdx-pcc-01): goal timeline instrument -- hermetic fixture goal through the real CLI

## RED evidence
- Task 1 (tool absent): `FAIL V-TL-TOOL-EXISTS`, `GSDX_GOAL_TIMELINE_PASS=0/8  threshold=8/8`, exit 1.
- Task 2: `FAIL V-TL-FIXTURE-CONVERGES: rc=2 ... usage: gsdx_goal_timeline.py [-h] {recorded}` and
  `FAIL V-TL-FIXTURE-HERMETIC: store= goals_root=`, giving `GSDX_GOAL_TIMELINE_PASS=6/8`, exit 1.

## GREEN evidence
- `python tools/test_gsdx_goal_timeline.py` printed `GSDX_GOAL_TIMELINE_PASS=8/8  threshold=8/8` and exited 0.
- Cross-check on the live recorded goal `g-002-router-surface`, read through a copy:
  - Result: 6 judged gates, verdict PASS, judge replay 2.9 s, declared to judged 155.755 s, exit 0. This equals the hand reading in 01-RESEARCH 4.5 (0.7+0.8+0.5+0.1+0.4+0.4).
  - Hermeticity: fingerprint of `~/.claude/state/gsd-x` taken by `tools/gsdx_reality_baseline.py fingerprint` was SAME before and after, 253 -> 253 files (sweep_heartbeat.json excluded by name).
- Fixture through the real CLI, as gate V-TL-FIXTURE-CONVERGES ran it:
  - Steps: declare, 10 plane calls, 4 oblige calls, then reconcile --apply/status passes until `CLOSURE  : CLEAR`, judge --record, and a final reconcile.
  - Result: closure cleared after 8 passes, CONVERGED, four epochs ended, and every receipt `observed` = `['2 passed']`.
  - Hermeticity: the store lies under the fixture's temp goals root, and the test's HOME has no `.claude/state/gsd-x`.
