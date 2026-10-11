Status: DONE
Unit: WU-P04-T3
HEAD: 5a854fb5

HEAD: 5a854fb5 (parent of the task commit)
RED-FIRST: tools/test_evc_draining_wire.py failed before the code with TypeError (_cost_breaker had no forecast= argument); after wiring, first run failed 3 gates on the fixture ratio (default 2.0 gave authority 2M), fixed by token_trip_ratio=1.0 in the fixture.
VERIFY: test_evc_draining_wire exit 0 (8 pass, 0 fail); test_evc_draining exit 0 (ALL PASS); test_evc_distribution exit 0 (ALL PASS); test_gsdx_reforecast exit 0 (ALL PASS); test_mission_spend exit 0 (30/30); test_gsd_mission_owner_hold exit 0 (32/32); test_goal_lease exit 0 (10/10).
DECISION: transition() accepts arbitrary record fields, so no whitelist change. The single lease_draining ledger row comes from transition itself (ledger_extra carries spent, p95_remaining, authority); a separate ledger_append would have doubled the row.
DECISION: gsdx_reforecast --mission-record flag SKIPPED. The only write helper (_write) is raw with no lock or CAS and would race the supervisor. forecast_p95_remaining is left to the supervisor to write via transition.
