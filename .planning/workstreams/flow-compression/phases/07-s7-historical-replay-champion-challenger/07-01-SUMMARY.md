---
phase: 07-s7-historical-replay-champion-challenger
plan: 01
subsystem: mission-supervisor
tags: [replay, champion-challenger, ledger-pin, avoidable-idle, S7]
requires: [06-01]
provides:
  - tools/flow_replay.py (pin, replay, report; failure-kind table, real S1-S6 seams, time accounting, avoidable idle, S8 sentence)
  - tools/test_s7_replay.py (58 gates)
  - 07-PIN.json (hash-pinned ledger prefix)
key-files:
  created:
    - tools/flow_replay.py
    - tools/test_s7_replay.py
    - .planning/workstreams/flow-compression/phases/07-s7-historical-replay-champion-challenger/07-PIN.json
  modified: []
decisions:
  - Champion = six S1-S6 switches off, challenger = on; HELD group (CCR admission, mission renew, bounded renewal) equal in both arms
  - Real decision functions only; compile_blocker always cwd=None (no W2 dependence)
  - UNMEASURED is a closed-set verdict kept apart from totals, never prevented or zero
  - Renewal axis is a labelled sensitivity section outside S2-S6 totals
  - Rebuilt owner in idle gaps is a host-backgrounded worker, so plan_next answers none (host owns restarts); avoidable gaps are therefore few and inferred
requirements: [FC-01, FC-09, FC-10, FC-11]
completed: 2026-10-25
status: complete
commits: 3
actuals:
  tasks: 3
  commits: 3
---

# Summary 07-01

Commits: 6ba88a90 (tracer), 7062fa76 (full replay), 9bf8cd9a (time, idle, S8, report). Gate: S7_PASS=58/58.

Pin: 1740294 bytes, 6339 rows (plan text said 6333; harness wins), sha256 b47ff018fb44....
Replay: 266 incidents on the real host records: PREVENTED 2, MOVED_EARLIER 1, LEGITIMATE_STOP 125, UNCHANGED 121, UNMEASURED 17. Coverage: 3400 failure-class rows, 588 mapped to S1-S6, 2812 unmapped (mostly provider waits and supervise_error); census cross-check mission_blocked 55 = 55.
Time (separate): summed 27483.9 mission-h (148 missions, 92 open at pin), wall 715.1 h, critical path 516.8 h. Avoidable idle 0.728 h before and after (7 gaps; no S2 gap moved), 23 gaps unmeasured (1.276 h). S8: unmeasured form (0 recorded independent_work values; 55 pre-S6 rows).

## Baselines (foreground, CPP_RESOURCE_ADMISSION=off)
test_gsd_mission 234/234, s3_admission 11/11, s4_lease 14/14, s5_reconcile 44/44, s6_blockers 72/72, gsd_epoch 111/111, rotation_invariant 17/17, arm_preflight 16/16, mission_spend 44/45 and mission_continuity 37/38 (both known prior failures, untouched).

## Deviations and honest limits
- S1 verdicts are all UNMEASURED (no size evidence); S5 is UNCHANGED by construction (annotation only).
- Three S4 groups were UNMEASURED replay_unfaithful; one S5 record changed since pin.
- Renewal axis: all budget halts UNMEASURED on gsd_outcome (or lacking a renewal row).
- Idle gap start is inferred (no worker-end row). Challenger idle equals champion where no seam recomputed.
- Debt untouched: W2, W3, V-AMCR-ONE-RESOLVER-INVENTORY, V-MSPEND-HOLD-PLAN-NONE.
- Not merged or pushed; ROADMAP untouched. Committed report is for plan 07-02.
