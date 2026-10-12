# 04-02 SUMMARY -- certificate producer and candidate-moved-under-verification

Plane: laptop (Windows, Python 3.12). Plan: `proof.produced` is written when, and only when, `cv.satisfy` allows.

## Changed
- `modules/gsd_x/goal/proof.py`: `certificate_id`, `live_certificates`, `certificate_payload` (pure builder).
- `modules/gsd_x/goal/sweep.py`: `_apply_verdicts(..., root=None)`, `_moved_under_verification`, `_certify`; the harvest call site passes `root`.
- `tools/test_gsd_x_goal_certificate.py` (new, 7 gates).

## Gates (laptop plane)
- RED first: `logs/04-02-red.log` (1/7, TypeError on the new `root` keyword).
- `GSDX_CERTIFICATE_PASS=7/7  threshold=7/7`
- `GSDX_PCC_REPLAY_PASS=28/28  threshold=28/28`
- `GSDX_PCC_SEMANTICS_PASS=48/48  threshold=48/48`
- `GSDX_INVALIDATION_PASS=10/10  threshold=10/10`
- `GSDX_GOAL_SWEEP_PASS=14/14  threshold=14/14`
- Frontier suite 40/40: 30 gates in a full run cut at the wall bound while in `V-FRONTIER-SWEEP-N` (host loaded; each real-subprocess sweep gate takes 2-5 min), then the 10 remaining gates each run to PASS in `logs/04-02-frontier-sweep-*.log`. Not one uninterrupted run.

## Deviations
- The dispatch-time causal fingerprint is NOT stored in the epoch spec (that spec stays byte-identical). "Moved under verification" = `receipt.tree_before`/`tree_after` not `tree_equal` (unequal or either unknown); the causal fingerprint is computed at harvest.
- `candidate.py` is not imported by `sweep.py` in this plan; no real call site needs it yet. Wiring is deferred to 04-03/04-04 and checked by liveness in 04-05.
- Re-harvesting a claim already holding a live certificate at the same binding writes nothing (idempotent), so `law_proof_conservation` stays clean.
