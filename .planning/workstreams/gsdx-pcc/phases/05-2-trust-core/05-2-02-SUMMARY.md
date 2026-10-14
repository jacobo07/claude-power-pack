# 05-2-02 SUMMARY -- certificate forgery (N16) through the real judge

Plane for every line below: `Windows laptop`. Logs: `logs/05-2-02-*.log`.

## Gates (verbatim)
- RED (before `verify_certificate`): `GSDX_TRUST_FORGERY_PASS=18/31  threshold=31/31` (`logs/05-2-02-forgery-RED.log`). The certificate attacks F3 F4 F5a F5b F6a F6b F8 F11a F11b F11c were all VALIDATEd by the judge (`mode=VALIDATE runs=0`), i.e. the gate was skipped on a forged certificate. F2's first draft raised `ProofRefused` (the writer already refuses an inherited event naming no certificate); rewritten to hand-write the event file.
- GREEN: `GSDX_TRUST_FORGERY_PASS=31/31  threshold=31/31` (`logs/05-2-02-forgery-GREEN.log`), `V-FORGERY-COUNT 16 distinct attacks refused` (>= 8 required).
- Regress: `GSDX_TRUST_PASS=7/7  threshold=7/7`; `GSDX_JUDGE_VALIDATE_PASS=11/11  threshold=11/11`. Invalidation and certificate suites: see 05-2-03-SUMMARY (run once, after both plans).

## What changed
- `trust.py`: `contract_hashes`, `plane_ok` (N19 predicate), `verify_certificate(ledger, cert_event, claim_id, obligation, contract_hashes) -> (ok, reason)`.
- `inherit.py`: `_latest_live` takes the obligation and returns only a certificate `verify_certificate` admits; a forged newer certificate is skipped, the older legitimate one still serves (the judge validates on it).
- NEW `tools/test_gsd_x_goal_trust_forgery.py`: forged `proof.produced` events on a real tmp git repo, outcome observed by a marker file the gate drops. Every attack has a control on the same fixture where the legitimate certificate is admitted (`mode=VALIDATE runs=0`).

## Attack table (what was RED and what was already refused)
| attack | result before | refused by |
|---|---|---|
| F1 edited premises | baseline green | `_agrees` |
| F2 inherited names unproduced certificate | baseline green | `certificate == live cert` match in `inherited_ids` |
| F3 unit claim stamped live | RED | `verify_certificate` strength |
| F4 parent of another claim | RED | lineage |
| F5a self-parent cycle, F5b depth disagrees | RED | lineage (parent must precede and match depth/root) |
| F6a/F6b unregistered authority id / version | RED | registry |
| F7 revoked authority signs again | baseline green (05-2-01 `dead_certificates`) | revocation |
| F8 contract hash | RED | `contract_hashes` |
| F9 premises.claim of another claim | baseline green | premise comparison reads CHANGED -> STALE -> gate runs; also refused by the verifier |
| F10 inherited authority above original | baseline green | `inherited_event_ok`, driven with the writer bypassed |
| F11a/b/c PORTABILITY one plane / different trees / unknown tree | RED | `plane_ok` |
| F12 future `ts` | baseline green | `observe_premises` |

## Deviations / decisions
- F3's control with an obligation whose accepted class really is `live` cannot go through the judge: a live-class claim's freshness class is never inherited. The strength rule is therefore controlled by calling `verify_certificate` directly (live cert on a live claim admitted; unit claim stamped live refused).
- F5b's predecessor carries an unregistered authority, otherwise the judge would legitimately validate on the older certificate and the depth forgery would not be observable.
- N19 field shape (fixed here, 05-2-03 stamps it): `plane = {claim: PLATFORM|PORTABILITY, planes: [ids], modules_tree}`. `modules_tree` is a string or a per-plane dict for PLATFORM, and a dict `{plane id: tree}` for PORTABILITY (identical, known, clean). An absent `plane` is admitted until 05-2-03 stamps it.
- Not run this unit: replay 28/28, semantics 48/48, frontier, hermetic, drills (05-2-05).
