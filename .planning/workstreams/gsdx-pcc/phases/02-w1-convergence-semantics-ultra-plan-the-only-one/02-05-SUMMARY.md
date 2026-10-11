# 02-05 SUMMARY -- five laws and D44 invariants

PLAN_BASE = 340c792d (02-04 summary commit)

## Done
- Task 1 (dfc87abc range): `law_semantic_conservation` and `law_work_conservation` in `proof.py`. Measured on the recorded and synthetic corpus: 26 epochs and 2 `goal.revised` events, 0 violations, so `WORK_CONSERVATION_LEGACY_EXCEPTIONS` and `SEMANTIC_CONSERVATION_LEGACY_EXCEPTIONS` stay empty (a stale exception also fails the gate). Gates `V-PCC-LAW-WORK-CONSERVATION`, `V-PCC-LAW-SEMANTIC-CORPUS` (replay) and `V-PCC-LAW-WORK-CONSERVATION-SYNTHETIC`, `V-PCC-LAW-SEMANTIC` (semantics, each with a passing control).
- Task 2: `law_proof_conservation`, `independent`, `law_unknown_escalates` (2916 cells, 0 violations, in-process mutant "unknown treated as equal" gives 63). `binding(t, "unknown:x")` now collapses to the tree scheme (spec S4). Gates `V-PCC-LAW-PROOF-CONSERVATION-LEDGER`, `V-PCC-LAW-CONCURRENCY-DEF`, `V-PCC-LAW-UNKNOWN-ESCALATES`, `V-PCC-ONE-OPEN-EPOCH-PINNED`.
- Task 3 (a353fb7b): `V-PCC-NO-SECOND-STORE`, `V-PCC-PROJECTION-PURE`, `V-PCC-ADDITIVE-ONLY` (`legacy=22 new=4`, only `proof.py` new, no legacy file hash moved), `V-PCC-VOCAB-DECLARED`, `V-PCC-SPEC-RESOLVED`.
- Final: `GSDX_PCC_REPLAY_PASS=28/28`, `GSDX_PCC_SEMANTICS_PASS=48/48`, liveness `gate offenders: 0`; incumbents RECONCILE 22/22, CONV 29/29, EPOCH 19/19, JUDGE 11/11. Logs `02-05-red.log`, `02-05-green.log`.
- DENOMINATOR D44 -> DONE. D03 stays OPEN (baseline entries are Phase 10).

## Deviations
- `V-PCC-ONE-OPEN-EPOCH-PINNED` was green at RED: it pins existing `epoch.begin` behaviour (a pin, not new behaviour). Vacuity is covered by the begin-after-end control.
- Task 3 had no module-absent RED; its RED is the seeded controls (scanner finds 3 / 1 / `sneaky.event` / `S1` / fake gate tokens). The first run found one real defect in the gate itself: the spec cites `V-PCC-NO-LEGACY-EDIT` (a phase-scoped git-diff evidence command run in 02-06) and the prefix family `V-PCC-REPLAY-*`. Handled by an explicit `PHASE_SCOPED_EVIDENCE` map that requires the named plan to mention the gate, and by prefix matching, not by dropping the cross-check.
- Spec S12 names the proof detector `duplicate_payment(ledger)` and counts 729 combinations; the plan (followed) names it `law_proof_conservation` and enumerates 2916 cells (729 premise combinations x event x switch). Spec wording left as is; the gate names match.
- Suite gate names are collected from quoted tokens in the two suite sources, so a quoted token in a message would count as a gate; the fake controls are built by concatenation for that reason.

## Open
- D03 and D43 stay OPEN until the 02-06 evidence.
