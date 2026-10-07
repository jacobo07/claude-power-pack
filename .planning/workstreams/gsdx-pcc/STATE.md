---
gsd_state_version: "1.0"
current_phase: 1
status: executing
last_updated: "2026-10-07T13:18:31.534Z"
last_activity: 2026-10-07
last_activity_desc: Phase 1 execution started
state_head: dc2ab789eff955117b11cef2ef4f5b75d228472a
progress:
  total_phases: 10
  completed_phases: 0
  total_plans: 6
  completed_plans: 0
  percent: 0
workstream: gsdx-pcc
created: 2026-10-07
current_phase_name: W0 Reality, baseline and incumbent measurement
current_plan: Not started
stopped_at: Owner approved the plan (2026-10-07); workstream created; ready to plan Phase 1
---

# Project State

## Current Position

**Status:** Executing Phase 1
**Current Phase:** 1
**Last Activity:** 2026-10-07 — Phase 1 execution started

## Session Continuity

Fresh context: read, in order, `vault/specs/gsdx-proof-conserving-convergence.md`, this workstream's `ROADMAP.md`
(operating constraints first), `DENOMINATOR.md`, then the latest phase `EVIDENCE.md`. Do not reread the
2111-line dataset end to end: open only the § numbers a denominator row cites.

## Decisions

- D-O1..D-O4 recorded in the spec (worktree, software_construction family, io-chatgpt-plugin pilot, PROBATION ceiling).
- 2026-10-07 (worker epoch 2): Phase 1 plans run inline in the main session with PowerShell. Reason: subagents have no PowerShell tool, and the Windows Bash guard blocks git and python there. Safe: execution order only; the artifacts are unchanged.
- 2026-10-07: V-RB is 16 gates, not the plan's 15. The added gate is V-RB-GUARD-EXCLUDES-ONLY-NAMED, for the sweep_heartbeat.json confound measured in 01-01. Safe: one more gate, and its control still trips.
- 2026-10-07: The 01-04 liveness freeze was re-applied as an order-preserving known_orphans-only rewrite. Reason: `--baseline` re-sorts the whole registry (sort_keys), which puts hunks outside known_orphans, and the plan forbids those. Safe: the list is identical to the tool's own output, every other key is checked equal, and it is reversible by git.
- 2026-10-07: The 01-05 suites were measured by one background driver script (one guarded `suites` call per suite, `--runs 3`). Reason: it stays serial and avoids the 600 s cap per tool call. Safe: same instrument, same rows; a guard trip stops the driver.

- 2026-10-07: `.gsd/`, the workstream `config.json` and `milestone.lock` (gsd-tools runtime state) are excluded through the common `.git/info/exclude` and are neither committed nor added to `.gitignore`. Safe: local only, reversible, and names only gsdx-pcc paths.
- 2026-10-07: The in-copy run of the mutation suite was killed by the memory-pressure reaper and NOT restarted (harness policy). It is recorded UNKNOWN in 01-INCUMBENT.md. Re-run when RAM allows (command in 01-05-SUMMARY.md).

## Blockers

None. Open measurement gap: incumbent `test_gsd_x_goal_mutation.py` is UNKNOWN (memory-pressure reaper; see 01-05-SUMMARY.md).
</content>
</invoke>
