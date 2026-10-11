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
