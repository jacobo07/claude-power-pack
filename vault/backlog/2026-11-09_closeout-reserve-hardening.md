# Closeout-reserve hardening (CPP lane, coordinator-owned)

Status: OPEN, operational backlog. Owner order 2026-11-09T19:36:54Z (laptop session ddf4990e, uuid e19e015a, S23
Checkpoint B opening): "incorpora al backlog operativo el refuerzo del closeout ... No confundas la ausencia de errores
en el sweep con la prueba de esa ruta específica."

## Context
S22 m-4a5a719551ae closed HALTED with its closeout reserve unreachable: the authority trip met an unlisted background
worker, so liveness was UNKNOWN and `worker_stopped_at` was never set. Fixed in laptop 02f9d5eb
(V-COST-CLOSEOUT-UNLISTED-BACKGROUND-LAUNCHES), deployed GEX44 4a992fc4 at 19:20Z.

What that deploy proved: the red->green suite case, and on GEX44 0 `supervise_error` over 9 sweep rows (control 527
historical). What it did NOT prove: that a real mission whose worker really disappears reaches its closeout reserve.
The sweep's clean rows never exercised that path. Their 0 is not evidence for it.

## Work items (each needs a red-first test and a real-host drill, not only a unit)
1. **Real worker-disappearance recovery.** Drill on a disposable mission on GEX44: launch a worker, kill it
   (SIGKILL, no settle row), let the authority trip fire, and observe that the closeout reserve is granted and a
   closeout worker runs. Done = ledger rows for trip -> worker_stopped_at -> closeout launch, from the real sweep.
2. **Incomplete-snapshot control.** The liveness/process snapshot the trip judges from can be partial (the listing
   tool fails, or times out, or a host is unreachable). A partial snapshot must read UNKNOWN, never "no worker". Fault-
   inject the snapshot and assert the verdict.
3. **Double-launch prevention.** The closeout launch and a sweep relaunch must not both fire for one mission epoch.
   An atomic claim per (mission, epoch). Test: two concurrent sweeps against one tripped mission yield exactly one launch.

## Gate
Each item lands as a test in tools/test_gsd_mission_*.py or its own V- suite, plus the real-host drill evidence.
Deploy to GEX44 live PP needs an Owner "y" (live-clone deploy), canary first, rollback line recorded.
