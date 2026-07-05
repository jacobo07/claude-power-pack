---
id: CDIO-05
name: Design Review Pipeline
type: dataset
domain: cdio
status: sealed
parent: CDIO-00
implements: [CDIO-01, CDIO-02, CDIO-03, CDIO-04]
---

# CDIO-05 — Design Review Pipeline

Owns the process by which CDIO evaluates any visual surface and the exact,
reproducible way it computes the Design Quality Score. This dataset is the
contract between the reviewer (the cdio-reviewer agent) and the scorer (the
deterministic `modules/cdio/scorer.py`): the score formula defined here is
implemented verbatim in code, so the number is never the agent's opinion — it is
a function of the per-criterion verdicts the agent supplies plus the mechanical
checks the code computes. Same inputs, same score, every time.

## 1. The six review lenses (the evaluation order)

CDIO reviews a surface through six lenses, in this order, because the order
mirrors how a real user encounters the surface. Each lens draws its criteria from
the dimension datasets (CDIO-01 through CDIO-04).

**Lens 1 — First impression (the three-second test).** Before analyzing
anything, the reviewer asks: in three seconds, is it clear what this is, what it
does for the user, and what to do next (CDIO-03 §1)? A failure here is weighted
heavily because it precedes everything.

**Lens 2 — Above the fold.** What is present in the first viewport without
scrolling: value proposition, primary CTA, at least one trust signal (CDIO-03
§1, §2; CDIO-04 §1). Missing primary action or missing value above the fold are
findings.

**Lens 3 — Visual hierarchy.** Does the eye land on the intended element first;
are there at most three type levels; is spacing systematic; does contrast clear
the floor (CDIO-01)? This lens carries the mechanical accessibility checks.

**Lens 4 — Trust signals.** Are trust signals present, specific, honest, and
placed where the undecided user reaches them; are the finish details present;
is the surface free of trust leaks (CDIO-03)?

**Lens 5 — Conversion path.** Is there one clear primary action; is the value
before the friction; is the structure value-then-proof-then-ask; are there no
dark patterns (CDIO-02 §4; CDIO-04)?

**Lens 6 — Mobile-first check.** Does the surface hold at a 320–390px width:
body text ≥ 16px, tap targets ≥ 44×44px, no horizontal scroll, the primary CTA
still reachable and prominent, content reflowed rather than shrunk (CDIO-01 +
CDIO-02 applied at the small breakpoint). Mobile is checked explicitly because a
desktop-only review misses where most users actually are.

## 2. What a criterion verdict is

Every lens produces zero or more **criterion verdicts**. A verdict is a
structured record, never prose:

- **criterion** — the named rule (e.g., `contrast-body`, `single-primary-cta`,
  `trust-signal-above-fold`, `type-levels`, `tap-target-size`).
- **dimension** — one of `visual` (CDIO-01), `ux` (CDIO-02), `trust` (CDIO-03),
  `conversion` (CDIO-04).
- **status** — `pass` or `fail`.
- **severity** — `critical`, `major`, or `minor` (only meaningful on `fail`).
- **observed** — the measured value or concrete instance ("body text 13px",
  "CTA contrast 2.8:1", "two primary CTAs in hero"). A verdict with no observed
  value is invalid and is dropped, per CDIO-00's reality contract.
- **recommendation** — the concrete fix, tied to the criterion.

## 3. Severity assignment (fixed rules)

Severity is not a feeling; it is assigned by rule so it is reproducible:

- **Critical** — any accessibility-floor failure (contrast below the AA
  threshold, tap target below 44px, keyboard trap), any broken/dead-end state,
  a buried or absent primary action, a fabricated trust signal, or a dark
  pattern. Criticals block a "done" verdict by themselves (CDIO-00 §4).
- **Major** — a defect that clearly harms the experience but does not block a
  provisional ship: scale explosion (>3 type levels), no proof section on a
  landing page, field bloat, mental-model-mismatched navigation, value framed as
  features, missing hover/focus states across interactive elements.
- **Minor** — a polish defect: a few off-system spacing values, a slightly long
  measure, one inconsistent casing, a weak-but-present CTA label.

## 4. The Design Quality Score (the exact formula)

The score is computed deterministically from the verdicts. The reviewer supplies
verdicts; the scorer computes the number. The formula, implemented verbatim in
`modules/cdio/scorer.py`:

1. Start at **100**.
2. For each failing verdict, subtract by severity:
   - **critical**: −25
   - **major**: −8
   - **minor**: −2
3. Clamp the result to the range **0 to 100**.

The score is a single integer. Because the deductions and severities are fixed
and the mechanical checks are computed (not judged), the same set of verdicts
always yields the same score. Two reviewers who record the same verdicts get the
same number; a disagreement in the number always reduces to a disagreement in
the verdicts, which is resolvable by re-checking the observed values.

## 5. The verdict / gate (PR-CDIO-REVIEW-GATE-001)

From the score and the critical count, the pipeline emits one verdict:

- **APPROVE** — score **≥ 80 AND zero critical** issues. The surface may be
  declared done.
- **REVISE (warning)** — score **60–79 and zero critical**. Shippable only as a
  draft; the major issues must be resolved before "done."
- **BLOCK** — score **< 60, OR one or more critical issues at any score**. Not
  shippable. A single critical issue forces BLOCK even if the arithmetic score is
  high, because the accessibility/trust floor is not tradeable.

This is the PP completion standard for visual output: a surface that is BLOCK or
REVISE is **not done**. "Score ≥ 80 and zero critical" is the done-gate.

## 6. The review output (the report shape)

A CDIO review returns a structured report, never a paragraph of impressions:

1. **Design Quality Score** — the integer 0–100.
2. **Verdict** — APPROVE / REVISE / BLOCK, with the deciding reason.
3. **Critical issues** — each with criterion, observed value, and fix. Empty is
   valid and expected on a clean surface.
4. **Major issues** — same structure.
5. **Minor issues** — same structure.
6. **Recommendations** — the prioritized, concrete fixes (criticals first).
7. **What passed** — the lenses and criteria that cleared, so the report is
   honest about strengths, not only defects.

A report with a score but no per-criterion breakdown is rejected — the number
must be reconstructable from the listed verdicts. A report that lists issues but
no observed values is rejected — every issue carries its measurement.

## 7. Interaction with the rest of CDIO and the PP

- The verdicts and the score are published to the **PM-03 Findings Bus** as
  design findings (`topic="design:<criterion>"`), so another agent working the
  same repo consults them before repeating the same defect.
- The review counts and average score feed **CO-12 telemetry**, so CDIO's own
  catch rate is measured.
- The datasets consulted (CDIO-00..04) are ordinary **Graphify** nodes, so the
  reviewer navigates to the relevant standard rather than re-deriving it.
- The gate (PR-CDIO-REVIEW-GATE-001) is invoked at the point any agent is about
  to declare a visual surface done; the advisory hook surfaces the reminder.

## 8. Honesty boundary of the pipeline

CDIO-05 measures what a structured review can measure: the presence, values, and
structure that the dimension datasets define. It does not claim to measure taste,
predict a conversion rate, or replace a real user test. Where a criterion is a
convention rather than a first-principle threshold (CDIO-00 §5), the verdict
labels it as such, and the reviewer may accept a stated override. The pipeline's
promise is narrow and kept: a reproducible score, a defensible verdict, and every
finding carrying a criterion and an observed value.

## 9. A full worked review (verdicts to score)

Consider a SaaS landing page reviewed through the six lenses. The reviewer
records these verdicts, each with an observed value:

- Lens 1 (first impression): `value-proposition-3s` — pass (concrete value stated
  in viewport 1).
- Lens 2 (above the fold): `primary-cta-above-fold` — pass (one filled CTA in the
  hero).
- Lens 3 (hierarchy): `contrast-body` — **fail, critical** (hero subtext at
  `#9B9B9B` on white = 2.6:1, below 4.5:1). `type-levels` — **fail, major** (5
  competing sizes in the hero). `spacing-system` — **fail, minor** (three values
  off the 8px grid).
- Lens 4 (trust): `trust-signal-above-fold` — pass (named testimonial present).
  `finish-hover-states` — **fail, major** (buttons have no hover or focus state).
- Lens 5 (conversion): `single-primary-cta` — pass. `no-proof-section` — pass
  (results section present).
- Lens 6 (mobile): `mobile-body-font` — **fail, major** (body 14px on mobile).
  `tap-target-size` — pass (48px targets).

Now the deterministic scorer applies the formula: start 100; one critical (−25),
three majors (−24), one minor (−2) → 100 − 25 − 24 − 2 = **49**. Because a
critical is present, the verdict is **BLOCK** regardless of the arithmetic. The
report lists the one critical first (the contrast failure, with its fix: darken
the subtext to at least `#767676`), then the three majors, then the minor, then
what passed (value clarity, CTA placement, trust signal, proof section, tap
targets). The number 49 is fully reconstructable from the six failing verdicts —
any reviewer recording the same verdicts computes the same 49 and the same BLOCK.

## 10. Scoring edge cases (defined, not improvised)

- **A clean surface.** Zero failing verdicts → score 100 → APPROVE. This is a
  valid, expected outcome; the report still lists what passed. The reviewer never
  invents a defect to avoid a perfect score.
- **High score, one critical.** Score 85 with a single critical (e.g., a keyboard
  trap) → BLOCK, not APPROVE. The floor is not tradeable; the arithmetic does not
  override a critical.
- **Many minors, no criticals or majors.** Twenty minor findings → 100 − 40 = 60
  → REVISE (a wall of small issues is itself a quality signal). The score floor
  clamps at 0; it never goes negative.
- **A verdict with no observed value.** Dropped by the scorer before it counts,
  and reported in the dropped list so the omission is visible, not silent. A
  reviewer cannot lower a score with an unmeasured claim.
- **A convention-level finding the owner overrides.** Recorded as a pass with an
  override note rather than deleted, so the report remains honest about what was
  waived and why.

These rules make the score a contract, not a negotiation. The scorer's constants
(deductions, thresholds, severity rules) are mirrored in `modules/cdio/scorer.py`;
if the two ever diverge, the standards librarian flags it as the highest-severity
proposal, because a score whose formula and code disagree is no longer
reproducible — and reproducibility is the whole reason CDIO scores instead of
opining.

## 11. The pre-report gate (four questions before any finding)

Before the reviewer records ANY verdict, it passes the finding through four
questions, inherited from the PP code-review doctrine and adapted to design:

1. **Exact location** — can you point to the specific element, color pair, field,
   or step where the issue lives? A finding with no locus is an impression.
2. **Concrete observed value** — do you have the measurement or the concrete
   instance (the ratio, the count, the px value, the missing state)? Without it,
   the finding is dropped by the scorer and should be dropped by you.
3. **Context read** — have you looked at enough of the surface to rule out that
   the "defect" is intentional and serving the design (a false positive from each
   dataset's §9/§10)?
4. **Severity defensible** — can you justify critical / major / minor against the
   fixed severity rules in §3, not by how strongly you feel about it?

If any answer is no, the finding is not recorded. This gate is what keeps a CDIO
review honest under the pressure to "find something."

## 12. Zero Findings Is Valid

A clean surface returns a score of 100 and an APPROVE verdict with an empty
critical/major/minor set and a populated "what passed" section. This is a
complete, valid review — not a failure of the reviewer to look hard enough. The
pipeline never manufactures a finding to justify having run, and a reviewer who
reports "no defects found; here is what passed and why" has done the job
correctly. Equally, a surface riddled with real defects returns a low score and a
BLOCK, and that too is the pipeline working. The measure of a good review is not
how many findings it produced but whether every finding it produced is real,
located, measured, and reproducible — and whether every clean pass is honestly a
clean pass. This is the discipline that lets the rest of the Power Pack trust a
CDIO verdict the way it trusts a test result: as evidence, not as an opinion with
a number attached.
