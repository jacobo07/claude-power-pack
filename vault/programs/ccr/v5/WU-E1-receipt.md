# E1 receipt
Status: DONE_WITH_LIMITS
Limits: (1) measured-ctx1.json not created: GEX44 receipts carry no profile label, so the context check reports UNMEASURED for every profile and enforce has no data to act on; (2) slim-t2 floor rests on n=2 sessions, no fresh parity run; (3) four decomposition rows are candidates without a parity run.
Done: decomposition (E1-floor-decomposition.md, 41 GEX44 sessions, REDUCIBLE rows 60,902, call-1 median 82,298); lean profile = existing slim-t2, flag-to-component map and predicted 68,791-token call-1 saving in evidence-E1.md; context admission at arm = route_admission.context_check wired into gsd_mission.admit_route (observe by default, CPP_CONTEXT_ADMISSION=enforce refuses UNDERSTATED). Tests: CTX_PASS=10/10, ADM_PASS=43/43, EST_PASS=9/9.
Reforecast: E0 actual ~110,000 vs target 2,500,000 (0.04x), eligible. RAM_HOLD from the first session is cleared (7.7 GB free measured later).
K7: estimate 1,500,000; actual not summed across the unit's sessions (the 13-call breaker session, the rollover session and this one); the breaker session and this one are each far below the estimate.
Evidence: vault/programs/ccr/v5/evidence-E1.md
