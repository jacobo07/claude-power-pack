# gsdx-factory: failure knowledge (staged for UKDL at W8 closeout)

Each entry: symptom, root cause, chain, impact, proof, fix, prevention, applicability, invalidator.

## K1. A breaker compared tool calls with an estimate written in model calls (S1, 2026-10-09)
- Symptom: S1 halted by "calls" at 61 > 1.5 x 40 while its 40 model calls exactly matched the envelope.
- Root cause: `session_budget_guard.js` counts tool_use blocks (`st.calls`); the route envelope `calls` was authored
  in model calls. Ratio 64 tool / 40 model = 1.6 for implementation work.
- Impact: the unit stopped with green, uncommitted work; closeout had to be done by another pane.
- Proof: transcript e422223f, message.id dedup: 40 model calls, 64 tool_use (scratchpad rd_scan.py).
- Fix: ce-lifecycle-v3 WU-S4 prices admission in physical calls; gsdx W3 adds an explicit unit to every budget.
- Prevention / UKDL candidate: BUDGET UNITS MUST BE TYPE-SAFE (HR candidate; class CLASE 1, assumed unit).
- Invalidator: a guard that counts message ids would make the old envelope correct; check which unit the guard counts.

## K2. A flat cost-per-call estimate under growing context (S1, A-G1)
- Symptom: S1 2.71M vs admission 763K; A-G1 3.28M vs 1.5M.
- Root cause: admission = floor x calls x 1.2; context grew 18,742 -> 96,922 over 40 calls (+2,005/call).
- Proof: flat model 749,680 (28% of actual); n*F + g*n(n-1)/2 = 2,313,280 (85%).
- Fix: growth term (ce-lifecycle-v3 ea5cf9c8) + per-work-class g and r (W3).
- UKDL candidate: A FLAT CALL-COST MODEL IS INVALID WHEN CONTEXT GROWTH IS MATERIAL.

## K3. A test captured the hostile input and never used it (S1 test, 2026-10-09)
- Symptom: mutation "steward skips its re-read" SURVIVED on V-STEWARD-DUP-PASS-ONE-EFFECT.
- Root cause: the test built `stale = gm._scan()[0]` and then called `run(c)`, which rescans fresh state.
- Fix: 2a3c3bd0 feeds the stale list to steward_pass; the drill (re-reads return the stale copy) is KILLED.
- UKDL candidate (trap): a fixture variable that is assigned and never read is a gate that never ran; drill every
  idempotence gate with a stale-input mutant.

## K4. Closeout inside a grown worker is the most expensive work in the unit
- S1's tail (drills, 3 commits, receipt) would have run at ~95K context per call (~0.6M); done outside by a
  deterministic path it cost ~0 model tokens. UKDL candidate: GREEN IMPLEMENTATION SHOULD BECOME DURABLE BEFORE
  AVOIDABLE LEASE EXHAUSTION; closeout is a transaction, not a worker phase.

## K6. An unrecognised receipt status renewed a finished worker (L1, 2026-10-09)
- Symptom: L1 (m-4e161ffd6420) finished with everything committed and Status DONE_WITH_LIMITS; the supervisor renewed
  it as m-2c6cb462596f, which spent 98,070 tokens re-checking a clean tree.
- Root cause: receipt status is free text; anything not DONE reads as "work remains". The same free text stalled the
  chain (stopped_without_done) until the coordinator named the extra status per unit (chain `accept`).
- Fix (gsdx side): chain `accept` list per unit, V-CHAIN-ACCEPT-IS-PER-UNIT. Open: a closed receipt-status vocabulary
  (DONE / PARTIAL / BLOCKED / FAILED + `limits[]`) shared by packet template, supervisor and chain.
- Also: L1's GRAPH costs were placeholders (n = rows/6); a gate that checks disposition coverage says nothing about the
  quality of a forecast built beside it. PLAN-1 re-prices.

## K7. The live growth estimator charges context growth per TOOL call (ce-lifecycle-v3 L3, live 37a5f3c0)
- Symptom: PLAN-1 refused RECOMPILE at need 1,895,956 for a unit expected at ~0.4M.
- Root cause: route_admission.admit computes cp = calls*physical_ratio(2.4) and then n*F + g*cp(cp-1)/2 over cp.
  Context grows per model REQUEST; several tool_use blocks share one request (S1: 40 requests / 64 tool calls).
- Proof (backtest): S1 live formula 7.26M vs actual 2.71M; L1 5.26M vs 1.80M (both ~2.8x). It fit lc3's own
  units because they ran ~1 tool call per request (S3 9/9, S2 13/17).
- Workaround: routes in declared steps with targets >= live need (chain.json pricing_note).
- Fix owner: ce-lifecycle-v3 (owns route_admission growth); gsdx W3 proposes: price requests r_m = model calls,
  growth over r_m, physical calls only for the calls wall. Recurrence of K1 (unit mismatch) across programmes.
- Also fixed: a failed arm left a held PREPARED record the chain read as "running" (silent stall);
  V-CHAIN-ARM-REFUSED-SURFACED.

## K5. A successor arming step had no owner (programme level)
- Symptom: every unit end needed a coordinator pane to arm the next one (the 49% control-plane tax measured in
  cost-collapse). Fix: tools/gsdx_chain.py tick (85024700), CHAIN_PASS=9/9, envelope mutant KILLED.
- CBR candidate after a second programme uses it: steward R3 arms within the programme envelope.
