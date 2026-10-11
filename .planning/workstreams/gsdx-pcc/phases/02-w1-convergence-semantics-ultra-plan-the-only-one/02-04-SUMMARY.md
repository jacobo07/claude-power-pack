# 02-04 SUMMARY -- proof states, certificates, fingerprints, typed contract

PLAN_BASE = 63db7439 (the 02-03 summary commit, HEAD before this plan's first commit)

## Done
- ec1c1b82 (Task 1): `claim_id`, `legacy_contract`, `binding`, `proof_states` and the state vocabulary. `V-PCC-STATE-LEGACY-MAP` checked 1632 (prefix, context, obligation) cases over g-002, g-001 and the four synthetic scenarios with 0 excluded `unknown:` prefixes and 0 disagreements (FRESH 368, STALE 512, NOT_APPLICABLE 752); `V-PCC-CONTRACT-LEGACY-ONE-ELEMENT` 16 obligations. RED log shows `AttributeError` reported as FAIL, EXIT=1.
- ecdc8d1b (Task 2): `observe_premises`, `state_from_premises`, `supersedes`, `requires_full`, `causal_fingerprint` (`cf1:`), `environment_fingerprint` (`env1:`), the certificate path in `proof_states` (produced event binds candidate and revision -> FRESH; else observed premises; switch off ignores every PCC event). `V-PCC-STATE-TRUTH-TABLE cells=2916 INHERITED=1`. Audit rows 4 and 6 closed by `V-PCC-STATE-PRODUCED-UNKNOWN-BINDING`, `V-PCC-STATE-PRODUCED-WITHOUT-SATISFIED` and `V-PCC-STATE-OLD-REVISION-UNKNOWN` (raw `obligation.accepted` under an older revision -> UNKNOWN).
- Task 3 commit: `freshness_class` (second axis), `RISK_TAGS`, `RISK_KEYWORDS`, `effective_contract` (a weakening is ignored and its seq reported), `legacy_contract` now carries `freshness_class`. `GATE_CLASSES` pinned by `V-PCC-GATE-CLASSES-PINNED`.
- Final: `GSDX_PCC_SEMANTICS_PASS=37/37`, `GSDX_PCC_REPLAY_PASS=26/26`. Liveness `gate offenders: 0`. `git diff --name-only 63db7439..HEAD -- modules/gsd_x/goal` lists only `proof.py`.

## Deviations
- `V-PCC-STATE-UNKNOWN-TREE` control: a verdict at an `unknown:` tree judged against a KNOWN candidate is UNKNOWN too (the verdict cannot be compared), so the positive control is a known-tree goal that reads FRESH, not a STALE one. Fixed in the gate before its first green.
- A contract element may name its `freshness_class` by class name or by the legacy gate-class word (the sample payload uses `unit`); both map to the same class.
- `supersedes` orders identical bindings only; a differing binding is incomparable in Phase 2 (trees cannot be ordered).

## Open
- Audit row 4 also asks `law_unknown_escalates` to cover both cases: that law does not exist yet, it is created in 02-05, which must include the produced-unknown-binding and old-revision cases.
- D01/D10 stay OPEN until 02-06 evidence.