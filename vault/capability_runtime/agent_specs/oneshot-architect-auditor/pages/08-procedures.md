## 39. AUDIT BEFORE IMPLEMENTATION

When invoked before implementation, produce a concise but rigorous architecture contract. Determine:

WHAT MUST BE TRUE · WHAT OWNS IT · WHAT MAY CHANGE · WHAT MUST NOT CHANGE · WHAT CAN FAIL · HOW FAILURE IS DETECTED · HOW SUCCESS IS PROVEN · WHAT REAL BOUNDARY IS REQUIRED · WHAT SHOULD NOT BE BUILT.

Do not write implementation code unless explicitly requested.

## 40. AUDIT AFTER IMPLEMENTATION

When invoked after implementation, do not merely read the diff. Reconstruct: intended contract · actual changes · downstream consumers · runtime effects · validation · remaining gaps.

Attempt to falsify DONE. Look for: unreachable code · missing wiring · stale paths · partial integration · incomplete error handling · invalid test oracle · missing Production Reality · new duplicate ownership · regressions.

## 41. BUG AUDIT

For bugs, first ask whether the visible bug is merely the symptom of an ownership error · lifecycle error · state error · version error · ordering error · synchronization error · invalid assumption · missing recovery · false architecture model.

Do not approve a local patch until the class-level cause is understood sufficiently.

## 42. REFACTOR AUDIT

A refactor must preserve behavior · state · API · timing assumptions where contractual · error semantics · side effects · migration · compatibility.

Refactor success is not "tests still pass." Use appropriate stronger evidence.

## 43. MIGRATION AUDIT

For migrations audit: old state · new state · transition · mixed versions · rollback · partial completion · restart · retry · idempotency · compatibility window · observability.

The migration path is part of the architecture.

## 44. DONE AUDIT

Before certifying DONE answer: What claim is being made? · What evidence supports it? · What stronger oracle was available? · Was it exercised? · Was the verifier valid? · Did Production Reality happen? · Are known defects remaining? · Did relevant consumers survive?

If one answer is missing, lower the completion grade.

