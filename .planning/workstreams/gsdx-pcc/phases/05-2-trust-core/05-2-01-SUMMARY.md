# 05-2-01 SUMMARY -- trust substrate (N01 N02 N05 N23)

Plane for every line below: `Windows laptop`. Logs: `logs/05-2-01-*.log`.

## Gates (verbatim)
- RED (before implementation): `GSDX_TRUST_PASS=0/7  threshold=7/7` (`logs/05-2-01-trust-RED.log`; each gate failed because the feature was absent: no `AUTHORITY_REVOKED`, no `authority`/`lineage` field, certificate still inherited).
- GREEN: `GSDX_TRUST_PASS=7/7  threshold=7/7` (plane Windows laptop)
- Regress: `GSDX_JUDGE_VALIDATE_PASS=11/11  threshold=11/11`; `GSDX_INVALIDATION_PASS=26/26  threshold=26/26`; `GSDX_CERTIFICATE_PASS=7/7  threshold=7/7`; `GSDX_PCC_SEMANTICS_PASS=48/48  threshold=48/48` (after the deliberate vocabulary edit below).
- Liveness: `python modules/liveness/reachability.py` exit 0, `gate offenders: 0` (`gsd_x/goal/trust` declared PLANNED like its siblings; same entrance, `tools/gsd_x_goal.py`).

## What changed
- NEW `modules/gsd_x/goal/trust.py` (AUTHORITIES registry `gsdx-sweep` v1,v2; `stamp`, `is_trusted`, `revoked_set`, `dead_certificates`, `inherited_event_ok`, `strength_ok`, `revoke`, `ledger`).
- `proof.py`: `authority.revoked` joins `NEW_TYPES` / `REQUIRED_FIELDS` / `ProofLedger.revoked`; `live_certificates` also drops revoked-authority and dead-lineage certificates; `append_pcc` refuses a `proof.inherited` whose authority strength is above its certificate.
- `inherit.py`: `_latest_live` never returns a certificate without authority+lineage (legacy: RUN, never raises); `inherited_ids` ignores an inflated event; `apply` stamps the original's authority on the event it writes (plan-check (a): an event with no authority is admitted, claims nothing above original).
- `sweep._certify` stamps authority + depth-0 lineage on every new certificate.

## Deviations
- Authority id is `gsdx-sweep`, not dotted: `test_gsd_x_goal_pcc_semantics.py` (V-PCC-VOCAB-DECLARED) discovers dotted lowercase strings as event types.
- Deliberate vocabulary landing, edited in the Phase 2 pins: spec S7 table row for `authority.revoked` (`vault/specs/gsdx-proof-conserving-convergence.md`), a sample payload and `len(new_types) == 7` in `test_gsd_x_goal_pcc_semantics.py`. All 48 gates pass again.
- Not run this unit (belongs to 05-2-05): replay 28/28, frontier 40/40, hermetic 5/5, drills t1..t7. Drills UNRUN.
- `inherit.ineligible` / D11 untouched (05-2-04).