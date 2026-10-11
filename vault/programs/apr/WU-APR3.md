# WU-APR3 -- Event-driven advance, single-arm fencing, health, bounded silence, budget reforecast

Common brief: `PROGRAMME.md`. Read `WU-APR2-receipt.md` first. Route L. cwd `C:\Users\User\Apps\wt_apr`.
Files you own: `tools/gsdx_chain.py`, `tools/gsd_mission.py` (the supervise hook point only), their tests.

Steps:
1. Tick lock: every `tick` (watchdog task, event call, manual) runs under one per-goal exclusive lock
   (`modules/lease/store.py` `Exclusive` already exists -- reuse it; `mission_spend.goal_declare` shows the usage).
   A tick that cannot take the lock within a few seconds returns `{"action":"skipped_locked"}` and logs it; it never
   waits minutes. Test: two ticks in two processes on the same chain with an injected slow armer -> exactly one arm.
2. Idempotent arm: before calling arm-chain, re-read missions under the lock and refuse if any non-terminal mission
   already carries the unit's packet (or its residual packet). Test: event tick + watchdog tick; recovery residual +
   normal finalizer; a crash between arm-chain returning and the row being logged (simulate: armer succeeds, then
   raise) -> the next tick sees the mission and says `running`, never arms twice.
3. Event path: in `gsd_mission.supervise`, after a mission carrying a `wu_packet` transitions to COMPLETED or HALTED,
   call a new `gsdx_chain.tick_for_packet(packet)` that DISCOVERS the owning chain(s) by scanning
   `<live checkout>/vault/programs/*/chain.json` for that packet (or its `.residual.md`), and ticks each. It must be
   fail-isolated (an exception is a row, never a supervise failure), bounded (the sweep stage has 600 s), and off
   with `CPP_GSDX_CHAIN_EVENT=off`. Record `"trigger":"event"` vs `"watchdog"` on the chain row. Test with injected
   state: a COMPLETED transition ticks the chain once; kill switch -> no tick; chain.json unreadable -> row, no raise.
   Cheapest repair first: in `halt_continue`, when the stop reason is "receipt not closed", call APR-2's
   `gsdx_chain.try_seal(packet)` (fail-isolated) BEFORE renewing; sealed -> no renewal, row `"renewal": "not renewed:
   sealed by finalizer"`. A worker relaunch costs ~100k+ tokens; a seal costs zero model calls. Test both poles
   (evidence passes -> sealed, no successor; evidence fails -> renewed as today).
4. Health: `python tools/gsdx_chain.py status --chain <path>` (and `--all` over the discovered chains): per programme
   current unit, mission + state, last semantic progress (latest of: seal/receipt write, arm row, commit in root),
   last chain action and since when, recovery state (residual n/max, class), human gate if any, envelope used /
   forecast / remaining, next expected event. Plain JSON; no model.
5. Bounded silence: a chain whose last action is one of {stopped_without_done, residual_exhausted, arm_refused,
   refuse_envelope, human_gate, pause_budget, wait_steward} for longer than `silence_s` (chain field, default 1800)
   writes ONE alert per (goal, action, unit) to the existing alert sink (find it: `vault/alerts/`,
   `steward-incidents.jsonl`, or pp-monitor's sink -- reuse, do not invent) and marks the row `alerted`. A chain whose
   only wait reason is a running mission is not silent; `wait_event` is silent once older than `wait_timeout_s`
   (chain field, default 21600) -- an awaited event that never comes must not hold a programme forever (APR-6 waits
   on the canary). Test both poles.
6. Budget reforecast: before an `arm`, compute forecast = sum over not-done units of route target x overrun, where
   overrun = (measured spend of sealed/done units) / (their route targets), floor 1.0, from data the ledger already
   has (steward `settled.measured`, slim_result tokens, or goal-ledger leases -- read what exists, cite it). If
   used + forecast > envelope -> `{"action":"pause_budget", ...}` instead of arming (explicit, alerted by step 5).
   Absent measurements -> overrun 1.0 and say "unmeasured". Test: an overspent first unit makes a too-big remainder
   pause; a cheap first unit arms.
7. Coordinator attribution: `status` lists sessions holding reservations on the goal that are not owners of the
   chain's missions ("foreign_bindings"), so an accidental cwd bind is visible. Read-only; no hook changes.
8. Run every suite named in WU-APR2 plus `tools/test_gsd_mission.py`, `tools/test_gsd_epoch.py`,
   `tools/test_gsd_sweep_pass.py`.
Receipt: race tests and their counts; the event latency measured in a test; status JSON sample; forecast formula.
