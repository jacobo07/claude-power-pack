---
covers: [ucr_cif, disposition_consumer, applicability, selector, precision, W8,
         MIN_DISTINCTIVE_OVERLAP, evidence_strength, saturation]
tier: T2
opened: 2026-09-21
---

# Spec: UCR-CIF W8 — applicability precision at real prompt length

Supersedes nothing. Extends the single selector sealed by W5 (`bc260cb`) and
consumed by two doors since W6 (`aace845`). The decision this spec acts on was
recorded at W7 close in `vault/audits/ucr_cif/05_W7_REACH.md` §9 as the exact
condition that reopens the widening question.

## 1. The defect, as measured

W7 measured the selector against 2,350 derived cases of real `UserPromptSubmit`
history and found the door is doing the selector's job:

| prompt length | n | routes >=1 owner | mean owners (cap 5) |
|---|---|---|---|
| m | 72 | 45.8 % | 2.73 |
| l | 74 | 89.2 % | 4.18 |
| **xl (>5 000 chars)** | **1061** | **99.4 %** | **4.74** |

85 % of real Tier >= 2 prompts are `xl`. Holdout precision of `P1-ANY-OWNER`
is **23.5 %** at **100 % recall** and an **86.7 % false-activation rate**.
The three most-routed owners are the three largest by unit count
(`governance-overlay` 1128, `knowledge_acquisition` 1123, `deep-research`
1087) — W3's vocabulary-volume bias, `spearman = +0.756`.

Two independent causes, both in `modules/ucr_cif/disposition_consumer.py`:

**D1 — the applicability bars are absolute, so they are length-blind.**
`MIN_TERM_OVERLAP = 2` and `MIN_DISTINCTIVE_OVERLAP = 1` are constants. The
expected coincidental overlap between a unit's evidence terms and a prompt
grows with the number of terms the prompt contains, so at `xl` length a unit
clears a fixed bar by chance. The clause was proven on short synthetic
W5/W6 fixtures, which never reach that length.

**D2 — owners are ranked by raw unit count, which IS the volume bias.**
`owners.sort(key=lambda o: (-o.units, o.owner))` followed by `[:MAX_OWNERS]`.
With a mean of 4.74 owners against a cap of 5 the cap is nearly always
binding, so the selector is choosing *which five* far more often than it is
choosing *whether any*, and it chooses the biggest.

## 2. What may not change

- **`DISTINCTIVE_MAX_HOLDERS` is frozen at 3.** It is the measured median of
  the held-term distribution. W7's finding is that the clause is too WEAK at
  length; loosening it moves the defect in the wrong direction and buys reach
  with false certainty. This spec tightens by adding a clause, never by
  editing that constant.
- **One authority, one selector.** Both consumers (the novelty gate and the
  L/XL spec gate) read the same `select_for`. No fork, no consumer-specific
  copy, no second applicability engine.
- **The four refusals stay distinct** and keep their order: authority ->
  semantics -> lifecycle -> applicability, with UNREADABLE / SCHEMA /
  POPULATION / (none) separately observable.
- **Bounded materialization** holds: no unit bodies travel; caps unchanged.
- **No third consumption boundary** and no revisiting the `create_spec`
  trigger. Both are measured, holdout-validated decisions.

## 3. Mechanisms

Stated before any confusion matrix was recomputed.

**M1 — distinctiveness proportional to input length.** The number of
distinctive overlapping terms a unit must show scales with the prompt's term
count, because the null expectation does. A short proposal keeps today's bar
of one; a long one must clear more than coincidence supplies. The scaling is
declared as a decision with its own constant so it can be argued with, and it
is monotone: a longer prompt never requires less.

**M2 — rank by evidence strength, not by volume.** An owner's strength is the
sum over its distinctive matched terms of an inverse-holder weight, so a term
held by one owner counts fully and a term held by three counts a third. This
answers "which owner is this about" rather than "which owner is largest", and
it is the mechanism W7 named as *rank and cap by evidence strength rather than
accepting the first five*. Unit count remains a reported field and stops being
the sort key.

Each mechanism is measurable alone; the wave attributes the gain by ablation
rather than asserting which one worked.

## 4. Oracle, and the instrument defect this spec fixes first

`tools/ucr_cif_shadow.py` reads `owners_routed` from the persisted control
report. **It never calls `select_for`.** Re-running shadow after a selector
change therefore returns byte-identical numbers — an instrument that can only
return the pre-change answer. The resumption's one-line instruction ("re-run
shadow and watch P1's precision") is incomplete in exactly that way, and is
corrected by this wave.

The correct protocol is paired, and both halves come from one replay
population so history drift cannot be read as effect:

1. derive control with the current selector -> `before`
2. change the selector
3. derive control again, same session bound -> `after`
4. score both with `ucr_cif_shadow.py --report <each>`

`tools/ucr_cif_reach.py --funnel` drives the live chain
(`sdd_tier` -> `check_spec_gate` -> `select_for`) and is what re-derives
`owners_routed`.

## 5. Acceptance

- `P1-ANY-OWNER` holdout precision rises from 23.5 %.
- A **true-positive retention floor**: the repair may not reach its precision
  by routing nothing. Recall and TP count are reported beside precision, and a
  collapse of true positives fails the gate however high precision goes.
- `PR-W7-X1-SELECTOR-SATURATION-ON-LONG-PROMPTS` goes red and is **inverted in
  place**, never deleted, carrying the old figure in its message.
- Both doors' suites stay green: `tools/test_disposition_selection.py`,
  `tools/test_disposition_consumption.py`,
  `tools/test_disposition_spec_boundary.py`, `tools/test_ucr_cif_reach.py`.
- Directed mutations for M1 and M2 are added to the existing plan family and
  caught, with runtime-safe restore (source bytes alone are not restore).
- The labelled holdout is 57 cases, so precision moves in ~2-point steps.
  Any claim states the sample size beside the number and does not report a
  difference smaller than one case as an effect.

## 6. Out of scope

The 503 ABSTAIN, the 218 UNRESOLVED, corpus growth, `spec_depth_selection`
(stays honest UNKNOWN), the FIOS live-deployment debt, and any third door.
