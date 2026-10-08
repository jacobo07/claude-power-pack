done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/test_running_control.py
work_tree: C:\Users\User\Apps\pp-cost-collapse

# WU-E3C -- the running forecast runs live, and E3's miss recalibrates the next admission

Plan (binding, Owner "y" 2026-10-08): `vault/plans/expected-completion-E3R-plan.md`. Inputs: RECEIPT-E3.json,
RECEIPT-E3G.json, `vault/specs/expected-completion.CALIBRATION.json`. Fresh worker; no Agents, no GSD commands; this
worktree only; pathspec commits with a message file; never push.

## 1. Wire the EAC forecast (configured != runtime)
`gsd_mission.py` supervise calls `_cost_breaker(rec, now)` (one call site, ~line 2778) with NO `usage`, so E2's EAC
reforecast has never run live (RECEIPT-E2 decisions). Supply the worker usage reader -> (ctx_now, calls_done) from the
owner session transcript (mission_spend already reads transcripts; reuse, do not re-implement). Absent/unreadable usage
stays None (forecast None, legacy behaviour) -- never zero. Pin it with a test that drives the real call site.

## 2. Recalibrate from E3 truth
Add the E3 planned-vs-metered pair (planned 32 worker calls / 34 envelope, actual from RECEIPT-E3 economics; tokens
6,000,000 target vs 7,622,341 metered) to top-level-worker calls_err with provenance, via the E1 calibration path
(commit ce433d17), not by hand. n stays small: confidence LOW, the band widens; do not fit to one sample.
slim-t2 / gsd-executor calls_err stay ABSENT (UNKNOWN -> ESCALATE).

## 3. Promotion gate (Cognitive CI)
A check that fails when route_admission.CHALLENGER_AUTHORITATIVE is True and RECEIPT-E3.json does not record all seven
suites + test_dependent_admission green. Mutation: flip on with one suite missing from the receipt -> red.

## 4. Gate + chain
Green: test_running_control, test_route_admission_expected, test_route_admission, test_gsd_mission_admission,
test_gsd_mission_envelope, test_autopsy, test_session_budget_guard, plus the new checks. Write RECEIPT-E3C.json.
Compute route-E4.json with route_admission on the recalibrated table (WU-E4.md budget section as input; RECOMPILE ->
split E4 into E4a land / E4b ratchet and write both). Arm E4 per the plan's Chain section. Stop.

## Budget
At most 26 model calls (route-E3C.json). On checkpoint: go to section 4.
End with `HANDOFF NOTE:` and one line.
