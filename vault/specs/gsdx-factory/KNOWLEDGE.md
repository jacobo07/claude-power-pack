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

## K5. A successor arming step had no owner (programme level)
- Symptom: every unit end needed a coordinator pane to arm the next one (the 49% control-plane tax measured in
  cost-collapse). Fix: tools/gsdx_chain.py tick (85024700), CHAIN_PASS=9/9, envelope mutant KILLED.
- CBR candidate after a second programme uses it: steward R3 arms within the programme envelope.
