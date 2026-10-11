Status: DONE
HEAD: see `git log -1` (commit "feat(evc-03): task 2 -- CTC as primary estimator, with confidence and the retained profile misses")
RED-FIRST: V-EVC-CTC-CONFIDENCE (confidence key absent), V-EVC-CTC-INVALIDATED-CANNOT-ADMIT (admit_large/fallback absent), V-EVC-MISS-KIND (TypeError: unexpected kwarg `kind`) all failed before the code.
VERIFY:
- python tools\test_evc_confidence.py: exit 0, 28 passed, 0 failed
- python tools\test_cost_to_completion.py: exit 0, CTC_PASS=18/18
- python tools\test_route_admission.py: exit 1, RADM_PASS=19/21. CAVEAT: the same 2 FAILs (V-RADM-SLIM-T2-ADMITTED "RECOMPILE floor 13507", V-RADM-SLIM-REPO-FILE-EXISTS) occur identically on a pristine `git archive HEAD` copy without my changes (19/21), so they are pre-existing and unrelated to `kind`; the miss-shape tests pass. Not fixed (out of task scope).
Notes: additive keys on compile_cost: confidence, admit_large, fallback, effective_tokens (ceiling when conservative).
