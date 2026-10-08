# RECEIPT-E3 -- PARTIAL (stopped at the session budget breaker: 52 tool calls > 1.5 x estimate 34)

The packet names `vault/specs/expected-completion.RECEIPT-E3.json`; the breaker only permits `vault/plans/*.md`
writes, so this is the receipt. Convert it to the JSON path once the envelope is lifted.

## Sealed (commit 3f2ff5c4)
- Section 1 dependent admission + section 3 gate.
- `tools/route_admission.py`: `dependent_admission(pred_spent, pred_target)`. Over target -> ESCALATE; absent
  spend or target -> ESCALATE (basis `unmeasured`); zero spend is a measurement and passes to the successor's own forecast.
- `tools/gsd_mission.py`: `admit_route(..., depends_on=)` (also read from `rec["depends_on"]`), CLI `admit --depends-on`.
  The predecessor is measured with `mission_spend.processed_tokens`, never its estimate.
- `tools/test_dependent_admission.py`: exit 0, `DEPENDENT_ADMISSION_PASS=15/15`, plus 3 mutation drills (canary 8,
  canary 9, absent-read-as-zero) that each go red on a copied module.

## NOT sealed: section 2, D3 flip (working tree, uncommitted, unverified)
- `route_admission.CHALLENGER_AUTHORITATIVE = True`.
- `tools/test_route_admission.py` re-sized: last run 21/22, only V-RADM-SLIM-T2-ADMITTED red; fixed since by
  matching "no calibrated" -- not re-run.
- `tools/test_gsd_mission_admission.py` re-sized (thin 25 -> 22 calls; heavy expects ESCALATE; slim launch gates use a
  fixture floor table labelled `estimated:test-fixture`; new gate V-ADM-SLIM-UNCALIBRATED-ESCALATES-ON-REPO-TABLE).
  NOT run after the edits.
- Not run at all: test_route_admission_expected, test_gsd_mission_envelope, test_grammar_default, test_autopsy,
  test_running_control.

## Decisions
- slim-t2 and gsd-executor `calls_err` stay ABSENT: no planned-vs-metered call pairs exist for them, so a value would
  be invented. Repo table: UNKNOWN -> ESCALATE. Spec allowed this.
- Dependent admission uses zero tolerance (spent <= predecessor target); the spec's "class tolerance" is not defined anywhere yet.

## Next exact action
Run test_route_admission and test_gsd_mission_admission; then the five other suites; fix reds; commit
`tools/route_admission.py`, `tools/test_route_admission.py`, `tools/test_gsd_mission_admission.py` with a message file;
re-run `tools/test_dependent_admission.py`.
