# EWC knowledge log (E6 promotes; append one entry per bug/failure)

## K0 -- Evaluation Without Closure, the seed incident (Owner report, 2026-10-11)
- Symptom: an asset-iteration session reported several objective failures, several actionable warnings, an unwritten
  evidence artifact, uncommitted work and an explicit known next iteration, then stopped and recommended doing that
  iteration later.
- Epistemic status: OWNER REPORT. The transcript was not located by the planning pane (a vault-wide search timed out);
  E1 searches for it and records the session id here if found.
- Why it stopped (planning-pane hypothesis, E1 confirms with a fixture): no Stop member evaluates unresolved work in an
  interactive session -- closer-guard judges closer shape only and its hasResult() reads any digit as a result;
  gsd_stop_continuation exits without an autorun marker; findings live only in prose, never in Goal Spine.
- Impact: the Owner had to re-prompt for work the agent had already diagnosed and was authorized to do.

## K1 -- my own plan priced the programme at 5M; the estimator said ~22M (2026-10-11, arming)
- Symptom: the approved plan carried "mission cap 5M"; `tools/route_admission.py admit` priced slim-t2 units at
  1.27M (S/12 calls), 2.88M (M/20), 5.26M (L/28) before margin.
- Root cause: the plan's budget table was estimated from intuition, not from the route estimator (the same lesson as
  tennis-rf K2, which was already on disk).
- Fix: Owner re-decided the cap (22M) before any unit launched. Prevention: run the estimator BEFORE writing a plan's
  TOKEN BUDGET section; E5's plan-template change should say so.

## K0 addendum (E1) -- seed incident NOT_FOUND
- 2 bounded transcript searches returned nothing; the report stays OWNER REPORT. Generic fixture used instead.

## K2 -- WU-E1 step 1b conflated two Obligation nouns (E1)
- Symptom: brief pointed at mission/obligation.py for the Goal Spine obligation. Root cause: same noun, two models; Goal Spine one is modules/gsd_x/goal/convergence.py GoalObligation. Prevention: name file:class in briefs.

## K3 -- WU-E1 priced at 12 calls, needed >20 (E1)
- Symptom: breaker tripped at 21 calls; first attempt left nothing committed. Fix: continue from fault capsule. Prevention: S-route for premises+fixtures+test is underestimated.

## K4 -- RED proof (E1)
- tools/test_ewc.py today: V-EWC-1 FAIL (incident neither blocked nor CONTINUE_* receipt), 2b/3b FAIL (no receipts exist); 2a/3a PASS. Root cause confirmed: no Stop member evaluates unresolved work interactively.

## K5 -- E2 finished its work but its receipt had no `Status:` line; the chain halted (coordinator, 2026-10-11)
- Symptom: tick 11:14 `stopped_without_done receipt=UNREADABLE` (max_residuals 0) although every E2 step was PROVEN and
  committed (25f83975). The worker evaluated, wrote the evidence, then stopped without the one line that closes the unit:
  a live instance of EWC itself, at the programme level.
- Fix: coordinator re-ran test_ewc_obligations.py 56/56 + test_ewc.py 2/5, added `Status: DONE`, ticked; E3 armed
  m-6e6382f12f90. Prevention: the receipt's line 2 is `Status: DONE` -- E3+ check it before ending; E6 may wire the
  receipt status as an obligation the EWC gate sees.

## K6 -- receiptless endings are the pattern, not an accident (coordinator, 2026-10-11 16:40)
- E2 1st attempt, E3 x2 and E4 1st attempt all ended `slim worker finished ... no receipt`; E1 1st attempt tripped the
  breaker. 5 of 8 worker runs closed without the line that closes the unit -- after evaluating and often committing.
- E3's latency step was skipped silently (NOT_PROVEN). The receipt is written last, so the breaker's closeout calls
  eat exactly it. Prevention for E6/UKDL: write the receipt skeleton FIRST (Status: IN_PROGRESS) and flip it at the end;
  this is the programme-level form of "evaluation without closure".


Pointer (APR-6): K5 root cause, fix and production proof -> vault/programs/apr/KNOWLEDGE.md A1 and PRODUCTION-REALITY.md.
