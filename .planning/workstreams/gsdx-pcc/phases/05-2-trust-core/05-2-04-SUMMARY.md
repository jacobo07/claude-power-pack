# 05-2-04 SUMMARY -- D11: non-AND claims are evaluated through the algebra

Plane for every gate below: `Windows laptop` (tmp git repos, real gate subprocess). Not observed on GEX44 or in a live run.

## Gates (verbatim)
- `GSDX_TRUST_ALGEBRA_PASS=7/7  threshold=7/7` (RED: 1/7, `logs/05-2-04-red.log`; GREEN: `logs/05-2-04-green.log`)
- `GSDX_INVALIDATION_PASS=26/26`, `GSDX_JUDGE_VALIDATE_PASS=11/11`, `GSDX_PCC_SEMANTICS_PASS=48/48`,
  `GSDX_TRUST_PASS=7/7`, `GSDX_TRUST_ENV_PASS=14/14`, `GSDX_TRUST_FORGERY_PASS=31/31`,
  `GSDX_CERTIFICATE_PASS=7/7`, `GSDX_FRONTIER_PASS=40/40`, `GSDX_PCC_REPLAY_PASS=28/28` (logs `05-2-04-reg-*.log`).

## What changed
- `proof.element_premises` + `certificate_payload.element_premises`: per-element fingerprint/environment/gate pin, written by one function and re-derived by the same one.
- `inherit.plan`: a non-AND claim's state is `combine_states(op, per-element states, k)`; INHERITED/FRESH goes through the eligibility check, STALE invalidates, anything else (incl. UNKNOWN) runs.
- `inherit.apply` writes `element_premises` on the event; `inherit.inherited_ids` re-derives element states from certificate vs event (`_agrees_nonand`); `verification_set` lists `elements: {oid: {run, inherit}}`.

## Deviations
1. A non-AND contract with < 2 elements, or a certificate with no `element_premises` (pre-05-2-04), always re-runs (keeps V-INV-NONAND-RUNS-FULL).
2. `proof.freshness_class` answers UNKNOWN for any non-AND contract; `inherit.ineligible` now takes the strictest element class instead (as if AND). `freshness_class` itself is unchanged.
3. Pre-existing test debt fixed: `test_gsd_x_goal_pcc_replay.py` lacked an `authority.revoked` sample payload (added by 05-2-01, never regressed in 5.2) and did not count `led.revoked`; it failed 26/28 before this change touched anything.

## Drills
Not run (05-2-05).
