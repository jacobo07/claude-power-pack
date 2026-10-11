Status: DONE
HEAD: see `git log -1` (commit "feat(evc-03): task 3 -- Demote the auto envelope to a labelled emergency fallback")
RED-FIRST: V-AUTO-ASSIGNED (src "auto"), V-EVC-ENV-LABEL, V-AUTO-SUPERVISE-ASSIGNS, V-EVC-ENV-CTC-FIRST, V-EVC-ENV-CTC-FIRST-NO-CLAIMS, V-EVC-ENV-CTC-REFUSED-FALLS-THROUGH failed before the code (54/60).
VERIFY:
- test_gsd_mission_envelope.py: exit 0, ENVELOPE_PASS=60/60
- test_evc_confidence.py: exit 0, 28 passed, 0 failed
- test_cost_to_completion.py: exit 0, CTC_PASS=18/18
- test_evc_usage_truth.py: exit 0, 30/30
- test_evc_gsdx_reforecast.py: absent, skipped
- test_route_admission.py: exit 1, RADM_PASS=19/21 -- V-RADM-SLIM-T2-ADMITTED (floor 13507 expected, RECOMPILE) and V-RADM-SLIM-REPO-FILE-EXISTS. NOT caused by this unit: route_admission.py / route-floors.json / the test are untouched here and the test never imports gsd_mission. Needs a separate look (live profile floor vs the 13507 literal).
V-EVC-ENV-GREP: the only writer of token_estimate_src="auto" was gsd_mission.py:1387 (now "auto-fallback"/"ctc"); no non-test reader compared == "auto". Test lines asserting "auto" (V-AUTO-ASSIGNED, V-AUTO-SUPERVISE-ASSIGNS) updated to "auto-fallback".
