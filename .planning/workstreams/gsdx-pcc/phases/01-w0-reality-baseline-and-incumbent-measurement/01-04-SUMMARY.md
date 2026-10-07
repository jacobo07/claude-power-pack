---
phase: 01-w0-reality-baseline-and-incumbent-measurement
plan: 04
subsystem: repository reality (premises, liveness, denominator)
tags: [hr-premise-001, liveness, denominator]

requires: []
provides:
  - 01-PREMISES.md with 54 real signatures and file:line, plus a known-false control
  - liveness gate green (gate offenders 0) with the inherited debt frozen by name
  - DENOMINATOR row R10
affects: [Phase 3 imports decide from modules.cognitive_os.scheduler, every phase-end liveness gate, Phase 10]

actuals:
  tasks: 3
  commits: 3

key-decisions:
  - "The liveness freeze was applied as an order-preserving rewrite of known_orphans only. `reachability.py --baseline` writes with sort_keys=True and re-sorted the whole `modules` map, which put hunks outside known_orphans (the data was identical). Per plan step 4, that write was restored. The same 65-name list the tool produced was then re-applied with a rewrite that refuses unless it round-trips the original bytes and finds every other key equal. The diff has 3 hunks, all inside known_orphans."
  - "backup/test_v_block left known_orphans because the gate no longer lists it as unreachable. known_orphans = 8 previous names + 57 offenders = 65."

requirements-completed: []
---

# 01-04 Summary: premises, liveness freeze, R10

## Commits
- `ed0d833d` docs(gsdx-pcc-01): HR-PREMISE-001 premise record for the spec's APIs (control included)
- `96bdb8b1` chore(gsdx-pcc-01): freeze inherited liveness debt by name (65 standing, 57 new at fbca24fc)
- `f83c2a61` docs(gsdx-pcc-01): DENOMINATOR R10 -- gsd_x/goal liveness debt tracked to Phase 10

## Evidence
- Premises: 62 premises (8 files, 54 attrs).
  - Real set: `EXIT=0`.
  - Control: `[FAIL] decide in modules.parallel_mesh.pm_02_intent`, `EXIT=1`.
  - No corrections were needed. `decide` is at `modules/cognitive_os/scheduler.py:94`.
- Liveness before the freeze: `modules: 490 | REACHABLE: 312 | ORPHAN: 178 | UNKNOWN: 0 | gate offenders: 57`, `EXIT=1`.
  - Since fbca24fc, this mission has changed only `modules/gsd_x/goal/providers/gate.py` under modules/, and added no new module.
- Freeze: `baseline written: ... (65 modules of standing debt)`, `EXIT=0`.
- Liveness after the freeze: `gate offenders: 0`, `EXIT=0`.
- R10: one row added after R09, `git show --numstat` = `1 0`. It counts 17 gsd_x/goal units among the 57 offenders.
