---
phase: 01-w0-reality-baseline-and-incumbent-measurement
plan: 05
subsystem: incumbent measurement
tags: [measurement, baseline, timelines, r01]

requires: [01-01, 01-02, 01-03]
provides:
  - 01-INCUMBENT.md (method, provider sandboxes, suites, findings, wall, timelines, UNKNOWN)
  - 01-incumbent-suites.jsonl + incumbent-logs/ + generated table
  - 01-timeline-{g002,g001,fixture}.json/.log and 01-guard-timeline.json/.log
affects: [Phase 3 priors, Phase 6 mutant farm (no incumbent mutation timing yet), Phase 9 X vs X']

actuals:
  tasks: 3
  commits: 4 (incl. the instrument fix c75dc3cc)

key-decisions:
  - "The 16 remaining suites were timed by one background driver: one guarded `suites --runs 3 --timeout 540` call per suite, serial, stopping on a guard trip. This replaced the plan's 1+2 call pattern so no tool call hits the 600 s cap. The rows are identical in shape."
  - "The mutation suite's first in-copy run measured an instrument gap: the suite needs a clean git checkout, and the copy had no .git. Fixed in the instrument (c75dc3cc, V-RB-IN-COPY-CLEAN-GIT, 17/17). This is a tool change in 01-02's file, not an engine change."
  - "The second in-copy run was stopped by the Claude Code memory-pressure reaper. Per the harness notice it was NOT restarted unattended. It is recorded UNKNOWN with the reason, and no orphan or live mutation was left."

requirements-completed: [R01]
---

# 01-05 Summary: incumbent measurement

## Commits
- `02032644` gate_provider timed through the instrument
- `c75dc3cc` fix: in-copy runs get a clean one-commit git checkout
- `8b83216c` all goal suites (mutation suite in a copy)
- `46af64c6` sweep->judge timelines and judge replay

## Results
- **Suites:** 17 suites x 3 runs, rc 0 on every run, and all 8 spec baselines matched (gate_provider `= 18/18`). Every guard row was SAME.
  - Full goal-suite wall: sum cold 154.096 s, sum min 146.680 s. This is a **lower bound**, because 1 suite is UNKNOWN (`test_gsd_x_goal_mutation.py`).
  - The cli suite alone takes 53.4 s, about 36 % of the min sum.
- **Timelines:**
  - g-002: 6 gates, PASS, judge replay 2.9 s.
  - g-001: 6 gates, PASS, judge replay 32.3 s.
  - Fixture at the current engine: CONVERGED after 8 passes, 4 epochs, every receipt `observed` = `['2 passed']`. So R01 is observed fixed through the real CLI. Judge replay 0.4 s, judge CLI wall 1.558 s.
  - Timeline guard: SAME 253 -> 253, `EXIT=0`.
- **Live tree:** `git status --porcelain -- modules tools` was empty after the mutation attempts.

## Owner-actionable
- To obtain the incumbent mutation-suite number, relaunch Claude Code with `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1` (or free RAM). Then run:
  `python tools/gsdx_reality_baseline.py suites --suite tools/test_gsd_x_goal_mutation.py --in-copy --runs 1 --timeout 3600 --out <PHASE_DIR>/01-incumbent-suites.jsonl --log-dir <PHASE_DIR>/incumbent-logs --label "W0 incumbent 2026-10-07"`
