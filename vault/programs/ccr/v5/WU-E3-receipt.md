# E3 receipt
Status: DONE_WITH_LIMITS
Limits: (1) the code-map page is built and keyed by sha but no worker or hook reads it yet; (2) the canary uses injected meters, not a live mission; (3) the forecast gate covers phase leases with max_calls only; (4) measured-ctx1.json and PGO data still empty (1 real transcript); (5) test_mission_spend.py 40/41 predates this work.
Done: route_admission.forecast_gate wired into set_envelope (CPP_FORECAST_GATE=off kills it); tools/code_map.py (sha-keyed page, gsd_mission.py 351,130 B -> 21,917 B); fresh epoch when a lease moves to another phase; tools/ccr_canary.py (8/8, red when the gate is off). FORECAST_GATE_PASS=17/17; boundary 22/22, phase_lease 23/23 + 15/15, admission 43/43, envelope 67/67, epoch 92/92.
Returns to Owner: Envelope 4+ (not started); the code-map serve path; populating measured-ctx1.json.
K7: estimate 2,800,000; actual not summed from the transcript meter (one session, in this pane).
Evidence: vault/programs/ccr/v5/evidence-E3.md
