# Evidence E4a
Root cause: the TEST ARRANGE was wrong, not goal_authority (tools/gsd_mission.py:5011) nor the fold (modules/provider_routing/ledger.py:328 _recovery_view).
Proof: ledger.py:493 `_open_locked` returns ok=False "UNKNOWN: no programme envelope declared" when g["programme"] is None; the test declared goal "tight" with no programme, so lease_open opened nothing and reserve stayed 0 (observed remaining 8M/open 0/reserve 0). Fix: tled.set_programme(8_000_000, "test", inside_agent=False) before lease_open (as tools/test_goal_lease.py:76). Assertion unchanged.
Control: V-ACC-CONTROL-AT-AUTHORITY-ADMITTED admits estimate == available (1,500,000); over by 1 refused.
Result: ACCOUNTING_PASS=18/18
Regressions: test_phase_lease 23/23, test_gsd_mission_phase_lease 15/15, test_boundary_authority 22/22, test_forecast_gate 17/17, test_gsd_mission_admission 43/43.
