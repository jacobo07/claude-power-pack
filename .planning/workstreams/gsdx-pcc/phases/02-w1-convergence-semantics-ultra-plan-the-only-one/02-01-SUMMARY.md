# 02-01 SUMMARY -- W1 semantics resolved, audited

PLAN_BASE = 7a3223a1

## Done
- Spec `vault/specs/gsdx-proof-conserving-convergence.md`: Semantics S1-S16 resolved, each with Resolved/Gates/Sources lines (fabe7c88, a223b337, 86c3e628).
- ULTRA Q&A Q1-Q6 answered by the worker and recorded in STATE.md Decisions.
- HR-PREMISE-001: 28 premises EXIT=0 (`02-premises.log`), failing control EXIT=1 (`02-premises-control.log`).
- Audit: `oneshot-architect-auditor` returned 6 gaps; all injected, none deferred or rejected (f14420a0, `02-AUDIT.md`).

## Deviations
- None to the plan. Audit gaps 1-6 become CODE rows for 02-02, 02-04 and 02-06; each of those plans records the fix as a deviation in its own SUMMARY.

## Open
- DENOMINATOR unchanged (no deferred gaps, so no R13+ rows).
