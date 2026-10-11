# WU-APR5 -- Build the no-user canary programme (Production Reality, part 1)

Common brief: `PROGRAMME.md`. Read `WU-APR4-receipt.md` first (APR-2/3 must be LIVE, or stop BLOCKED_HUMAN with why).
Route S. cwd `C:\Users\User\Apps\wt_apr`.

The canary proves, with real workers and the real sweep/tick, that recoverable unit-closure faults recover with NO
message from any pane. You build it and END; it runs after you (your mission holds the root, so it cannot start
while you live). APR-6 judges it.

Steps:
1. Create `vault/programs/apr-canary/` in the live checkout: `chain.json` (goal `apr`, root
   `C:\Users\User\Apps\wt_apr`, envelope 20000000 -- the goal's whole cap, because envelope arithmetic is goal-wide --,
   `max_residuals` 1, route_ladder [route-XS.json, route-S.json]), and three units, each with `acceptance`:
   - C1 UNCLOSED_RECEIPT: create `canary/c1.txt` = `ok`, commit it, then write `WU-C1-receipt.md` with a heading
     and one PROVEN line and NO Status line, ever, including on any renewal. Acceptance: file exists with `ok`,
     require_commit. Expected: sealed by the finalizer (try_seal), no renewal, C2 armed.
   - C2 FALSE_DONE: first attempt (packet has NO `## Residual` section) writes `Status: DONE` and creates nothing.
     If the packet HAS a `## Residual` section: create `canary/c2.txt` = `ok`, commit, `Status: DONE`. Acceptance:
     file exists, require_commit. Expected: refusal, finalizer-written residual, one residual arm, then sealed DONE.
   - C3 CONTROL: create `canary/c3.txt`, commit, `Status: DONE`. Expected: armed by the EVENT path (row
     `trigger: event`), advanced, chain `complete`.
   Packets tiny (<= 15 lines), each stating "this is a canary; do exactly this and nothing else".
2. Routes: price with `tools/route_admission.py admit` -- an XS route (calls 6) and the S route; write the
   estimator's envelope into the route files (K1). Record the prices.
3. `chain_tick.ps1` for the canary (clone of `vault/programs/apr/chain_tick.ps1`) and register `PP-AprCanary-Tick`
   (10 min, same pattern) -- the watchdog. Event-driven progression must not need it; it is there to repair.
4. Write `vault/programs/apr-canary/EXPECTED.md`: the row sequence above, the max wall time (bounded-silence window),
   and the forbidden events (any coordinator message, any duplicate arm, any human_gate).
5. Commit everything (pathspec, live checkout), receipt `Status: DONE`, end. Do NOT tick the canary yourself.
Receipt: route prices, files, task registered (Get-ScheduledTask output line).
