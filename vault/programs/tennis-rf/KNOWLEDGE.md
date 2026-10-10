# TRF knowledge log (W9 promotes; append one entry per bug/failure)

## K1 -- C2b: one shared failure read as fifty (2026-10-11, W0 scan)
- Symptom: CP50 C2b reported "50 STALE_INPUT environment", zero measurements, one Phase-7 job spent.
- Root cause: ONE job; the judge had no CURRENT_CAPSULE for the rebuilt capsule cap1-ba8a3cfe2822 and failed closed
  after the remote run; candidate.py:486 copies the job verdict onto every unit with miss_class "environment".
  Hidden behind it: all 50 compiles aborted (raw m2c with unresolved `?` types, CXX built with `-lang c`), and the job
  contained no model step, so it could not have measured tokens per function.
- Economic impact: 1 of 4 Phase-7 jobs + the C2b worker session; the Tennis forecast was built on a number that
  never existed.
- Fix / prevention: W1 (CURRENT registration or pinned judge, zero-compile source lint, full stderr, reason classes),
  W2 (Fan-Out Readiness Certificate). Proof: W1/W2 receipts.

## K2 -- planned unit targets below measured physics (2026-10-11, arming)
- Symptom: the first chain tick's arm-chain for W1 refused `route RECOMPILE: floor 4,223,670 x 1.2 = 5,068,404 >
  target 2,500,000`.
- Root cause: the plan priced units at ~C1's per-call figure; route_admission's growth estimator (declared calls x
  2.4 physical, rising context) prices 25 declared calls at 4.22M. The admission was right; the plan was optimistic.
- Fix: routes resized from the estimator (S 1.6M/12, M 3.5M/20, L 6.4M/28; PP 5983db9d). Unit sum 36.1M: the
  programme's honest P50 is ~38M with W0, not 28M. Still inside the 55M hard stop.
- Prevention: size routes with `route_admission.py admit` BEFORE writing a plan's budget table.

## K3 -- a refused arm-chain deadlocks the chain when the goal has no GSD workstream (2026-10-11, arming)
- Symptom: after a RECOMPILE refusal the held PREPARED record makes gsdx_chain read the unit as `arm_refused`
  forever; it also counts as a live writer in the root (`wait_writer`), and if closed it reads as
  `stopped_without_done`.
- Root cause: `gsd_mission.arm --supersedes` requires a goal key (`goal_key(cwd, workstream)`); a mission armed without
  a GSD workstream has key None, so no supported path retires the refused record.
- Repair used: transition the never-launched record to HALTED keeping its owner_hold, then arm_chain again in the same
  script (scratch `rearm_w1.py`; old m-ea05f64a68b3, new m-3b3632860a22 RUNNING, worker 29a0ae3e read WU-W1).
- Prevention candidate (not this programme's scope): gsdx_chain re-arms a unit whose only record is a never-launched
  `arm-chain failed` hold once its route admits, retiring the old record itself.
