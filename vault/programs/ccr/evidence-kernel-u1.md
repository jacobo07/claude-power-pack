# evidence-kernel-u1 — PARTIAL, no code changed

Session stopped by the session budget guard after 16 read-only calls (limit 14 without an edit/commit). Tasks 1-3 and 7 not done.

Findings for the next worker (do not re-derive):
- Packet file lists tasks 1-6, but the latest commit 3414540c cut the route to 20 calls and scoped u1 to Env 0 (tasks 1-3, 7). Tasks 4-6 belong to kernel-u2.
- `hooks/lib/mission_gate.js` `decide(event)` (line 116): add the next-call check after the cost-hold block. Inputs are the record `phase_lease` {forecast, hard, base} and the worker transcript `event.transcript_path`. `agentTokens(file)` already sums processed tokens for one transcript. Last-call context = last assistant usage (input + cache_creation + cache_read).
- Phase hard cap = `int(forecast*hard) + base`, as in `tools/phase_lease.py` `judge`. Mission-wide spend is `mission_spend.processed_tokens(rec)` (Python); in JS, only the worker transcript is cheaply measurable. Decide: use the worker transcript sum plus a `spent_hint` written by the supervisor, or deny on the worker transcript alone.
- State-dir override already exists: `GSD_LONG_RUN_STATE_DIR` and `GSD_AUTORUN_MARKER_DIR`. Task 2 needs no gate change.
- Tests live in `tools/test_mission_gate.py` (not tests/).
- Sweep breaker hook point: `_phase_breaker` / `_cost_breaker` in `tools/gsd_mission.py` (~1594-1660); `supervise` call site ~4208.

Verdicts: tasks 1,2,3 NOT DONE; task 7 booking and kernel-u2 not done. No commits, nothing landed.

## kernel-u0 recalibration (2026-10-16)
- Session a7e006a1 curve (10 distinct calls): 18917, 21905, 23952, 28634, 30074, 33705, 34644, 35245, 37308, 38485; first 18917, mean +2174/call.
- slim-t2 growth 1725 (n=4) -> 1815 (n=5); physical_ratio 2.4 unchanged (censored). PP main commit 367df32c (also test fixture 25->20 calls; RADM 21/21).
- Admitted calls for kernel-u1b at target 6M/stop 8M: 26 (27 refused).
- Armed mission: m-48214fe73487
