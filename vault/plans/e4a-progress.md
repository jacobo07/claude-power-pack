# E4a progress (stopped by session budget breaker at 14 calls > 1.5 x 8; no code edited)

## Finding (evidence so far)
- goal_authority (tools/gsd_mission.py:5011) is consistent with the ledger: reserve = recovery.reserve - recovery.used, from
  GoalLedger._recovery_view (modules/provider_routing/ledger.py:328), which reads the LATEST lease's reserves.
- The test arrange (tools/test_accounting_authority.py ~line 205) calls `tled.lease_open("s-lease", 2_000_000, prev_lease="L1", reserves={...})`
  on a goal made only by ms.goal_declare("tight", 8M, ...). ledger.py:493 `_open_locked` returns ok=False
  "UNKNOWN: no programme envelope declared" when g["programme"] is None, so no lease is opened and reserve stays 0.
  Observed FAIL (remaining 8M/open 0/reserve 0) matches. Probable root cause: the TEST ARRANGE is wrong (no programme, and possibly no
  initial lease L1), not goal_authority nor the fold.
- Note the assertion's own `and lo.get("ok")` would also have caught it.

## Next exact action
1. See how tools/test_goal_lease.py (lines ~60-100, helper around line 223 `_walled`) sets the programme/L1 (likely led.set_programme or goal-programme CLI) and
   copy that arrange into the test (declare programme >= 2.5M, ensure L1 exists), keep the assertion unchanged.
2. Run test_accounting_authority (expect 18/18); the control V-ACC-CONTROL-AT-AUTHORITY-ADMITTED already exists.
3. Run regressions: test_phase_lease, test_gsd_mission_phase_lease, test_boundary_authority, test_forecast_gate, test_gsd_mission_admission.
4. Write vault/programs/ccr/v5/evidence-E4a.md and WU-E4a-receipt.md ('# E4a receipt' / 'Status: DONE'). Stage only own hunks (tools/gsd_mission.py has others' hunks).
5. Commit pathspec-only, with the Co-Authored-By trailer.

## Open points
- E3 K7 actual was "not summed" in WU-E3-receipt.md, so the 1.3x reforecast check cannot be evaluated; treated as not exceeded.
- RAM free ~6.2 GB (>= 4 GB, ok).
