---
phase: 07-s7-historical-replay-champion-challenger
plan: 02
subsystem: mission-supervisor
tags: [replay, fc-06, mutants, mutation-drills, committed-report, S7]
requires: [07-01]
provides:
  - FC-06 replay assertions (capital_ceiling, packet_digest, done_proof, protections) judged with snapshotted originals
  - six policy mutants run as challenger variants with HARNESS_DEFECT detection (exit 4) and FC-06 hard fail (exit 3)
  - 19 seeded scenarios reported apart from host verdict counts
  - 78 mutation drills, no-op drill control, real-file-untouched gate, negative controls, strict mutant map
  - 07-REPLAY.json and 07-REPLAY.md (committed report)
key-files:
  created:
    - .planning/workstreams/flow-compression/phases/07-s7-historical-replay-champion-challenger/07-REPLAY.json
    - .planning/workstreams/flow-compression/phases/07-s7-historical-replay-champion-challenger/07-REPLAY.md
  modified:
    - tools/flow_replay.py
    - tools/test_s7_replay.py
    - .planning/workstreams/flow-compression/STATE.md
decisions:
  - A mutant is caught when its (scenario, effect_digest) set differs from the challenger's or its FC-06 breaches exceed the challenger's; an identical replay is a harness defect
  - Each drill maps a gate to the mutations that turn it red by its own check; crash-absence never counts as red
  - Two gates stay UNMUTATED with a stated reason, listed in STATE.md
requirements: [FC-06, FC-09, FC-10, FC-12]
completed: 2026-10-25
status: executed, phase close pending verifier
commits: 3
actuals:
  tasks: 3
  commits: 3
---

# Summary 07-02

Gate: S7_PASS=164/164 (83 behaviour and control gates plus 78 drills, the no-op control, real-file-untouched, mutant map). Suite runs in about 170 s.

Mutants: always-admit, never-rotate, always-renew, drop-blocker-class, expand-authority differ on host and seeded sets; terminal-without-proof differs on the seeded set only. Challenger: 0 FC-06 breaches on 266 host incidents and 19 seeded scenarios; each assertion breaches under at least one mutant.

Report: PREVENTED 2, MOVED_EARLIER 1, LEGITIMATE_STOP 125, UNCHANGED 121, UNMEASURED 17 apart. Independently recomputed from the raw pinned bytes: sha256 b47ff018..., 6339 rows, relay_held 59, cost_breaker_tripped 288, mission_blocked 55; all equal the report. Two report runs are identical once the output path in the command tag is normalised.

Regression (baseline 07-01 -> now): test_gsd_mission 234/234, s3 11/11, s4 14/14, s5 44/44, s6 72/72, gsd_epoch 111/111, rotation_invariant 17/17, arm_preflight 16/16, mission_recovery 69/69, blocked_intent 16/16, owner_boundary_delivery 14/14 unchanged; mission_spend 44/45 and mission_continuity 37/38 unchanged, failing by exactly V-MSPEND-HOLD-PLAN-NONE and V-AMCR-ONE-RESOLVER-INVENTORY.

Isolation: the host ledger prefix still hashes to the pin; no write to the host ledger, queue or mission records; git diff vs the plan base touches only tools/flow_replay.py, tools/test_s7_replay.py and phase/state artifacts; no push. decisions compile: measured true, 0 items.

## Deviations and honest limits
- Test-run replay sees 215 incidents versus 266 in the CLI (S5 slice absent; import-order cause, not a host leak, not repaired).
- Report idle figures (66 gaps, 22 avoidable, 1.353 h) differ from the 07-01 summary (7 avoidable, 0.728 h); cause not isolated, carried to Phase 8.
- Two gates UNMUTATED (V-S7-HELD-RESTORED, V-S7-READONLY-COPY-IDENTICAL) with reasons in STATE.md.
- Phase close pending verifier: counters, ROADMAP and RESUMPTION_FILE.md untouched.
