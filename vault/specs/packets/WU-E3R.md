done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/test_route_admission.py
work_tree: C:\Users\User\Apps\pp-cost-collapse

# WU-E3R -- certify and commit the D3 flip, write the canonical E3 receipt (E3 recovery)

Plan (binding, Owner "y" 2026-10-08): `vault/plans/expected-completion-E3R-plan.md`.
Fresh worker, no parent transcript. This file is your scope, budget and done-gate. No Agents, no GSD commands.

## Frontier (all you need)
- E3-A is SEALED at 3f2ff5c4 (dependent admission). Do not edit `tools/gsd_mission.py` or `tools/test_dependent_admission.py`.
- D3 is in the working tree, UNCOMMITTED, status IMPLEMENTED_BUT_UNCERTIFIED: `tools/route_admission.py`
  (CHALLENGER_AUTHORITATIVE = True), `tools/test_route_admission.py`, `tools/test_gsd_mission_admission.py`.
  Snapshot: `vault/plans/expected-completion-E3-D3.patch` sha256 A354803E...27774. If the tree lost it: `git apply` it.
- Last known: test_route_admission 21/22 (V-RADM-SLIM-T2-ADMITTED), fixed since, not re-run; test_gsd_mission_admission
  not run since its edits. Fallback notes: `vault/plans/expected-completion.RECEIPT-E3.md`.
- UNKNOWN invariant: slim-t2 and gsd-executor have NO measured calls_err. `vault/config/route-floors.json` must not gain one.
  On the repo table they ESCALATE. Fixture values labelled `estimated:test-fixture` live only in a temp table.

## Steps (in order; Windows: PowerShell, git = C:\Program Files\Git\cmd\git.exe, python = done_gate path,
## $env:PYTHONIOENCODING='utf-8'; redirect each suite to a log, read only the _PASS= line and FAIL lines)
1. test_route_admission, test_gsd_mission_admission. Red -> fix ONLY causes from the D3 flip; re-run. Max 3 repair rounds;
   a 3rd red = stop, write the receipt with status BLOCKED.
2. In ONE PowerShell call, sequentially: test_route_admission_expected, test_gsd_mission_envelope, test_grammar_default,
   test_autopsy, test_running_control, test_dependent_admission (expect 15/15 + its 3 drills red-on-mutant).
3. `git diff --exit-code -- vault/config/route-floors.json` must be clean.
4. Commit the 3 D3 files by pathspec with a message file; verify `git log -1 --format=%s`. Never push.
5. Autopsy of the E3 worker: `python tools/mission_spend.py` autopsy/report for session b35651f5-4167-40cb-9596-624e90b58f48
   (use the subcommand its --help names). Record calls, processed tokens, first/mean/p90 ctx, g; classify each figure
   MEASURED / ESTIMATED / UNKNOWN. Forecasts to compare: spec 25 calls/4M, packet 32, route 34 calls / 6M target.
6. IMMEDIATELY write `vault/specs/expected-completion.RECEIPT-E3.json`, same shape as RECEIPT-E2.json, plus keys
   `economics` {forecast_calls, actual_calls, call_error, forecast_tokens, actual_tokens, token_error, basis per field},
   `authoritative_policy` "certified-in-worktree (ACTIVE only after E4 landing)", `unknown_telemetry` [slim-t2, gsd-executor
   calls_err], `incident` {receipt blocked by guard CLOSEOUT_PATH, call-ratio deny with no checkpoint tier, EAC forecast
   inert: gsd_mission.py:2778 passes no usage}. Commit it (pathspec) together with `vault/plans/expected-completion-E3*`.
7. Chain: arm WU-E3G exactly as `vault/plans/expected-completion-E3R-plan.md` section Chain says. Then stop.

## Budget
At most 22 model calls; the route is route-E3R.json. When the guard says checkpoint, go straight to step 6.
End with `HANDOFF NOTE:` and one line.
