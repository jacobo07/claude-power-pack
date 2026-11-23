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

The protagonist in the first phone screen (promoted 2026-11-23 by the Owner).
Judge it on the phone render, 390x844, first screen without scrolling. The rule
depends on the surface:
- `hero-protagonist-first-phone-screen` applies to marketing and landing surfaces.
  The protagonist is the one thing the page sells or shows: the offer, the product,
  the dish, the person or the place. Absent from the first phone screen is major.
  Present but cut by the fold, so that it cannot be recognized, is minor.
- `urgent-info-first-screen` applies to data and app screens (dashboard, list,
  detail). "Hero" does not apply there. The test is that the most urgent
  information (what needs action now) is in the first screen. Absent is major.
  Partly cut is minor.
- Brand sheets and legal pages: not applicable. Report `unassessed`, never fail.

Evidence and limits: E2. The criterion was found on 2 of 2 live sites (portfolio,
Bodeguita). It was then confirmed across a third and fourth sector: a professional
service, where the baseline had no protagonist and the CDIO final put the offer in
screen one, and a mobile app and a brand kit. A blind A/B judge preferred the
version that met it in both pairs. That judge is one LLM, and the fixtures are from
one author. The dashboard was the counterexample, which is why data screens get
`urgent-info-first-screen` instead. Sources:
`vault/audits/cdio_portfolio_vs_bodeguita_2026-11-22.md` and
`vault/audits/cdio_cross_sector_benchmark_2026-11-22.md` (Item 4). If live reviews
find a counterexample on a marketing surface, re-scope before trusting the major.

**Lens 3 — Visual hierarchy.** Does the eye land on the intended element first;
are there at most three type levels; is spacing systematic; does contrast clear
the floor (CDIO-01)? This lens carries the mechanical accessibility checks.

**Lens 4 — Trust signals.** Are trust signals present, specific, honest, and
placed where the undecided user reaches them; are the finish details present;
is the surface free of trust leaks (CDIO-03)? For any public website or web app,
this lens also applies the CDIO-10 legal-surface criteria (required legal pages
present, filled from facts, linked, matched to the jurisdiction, consent before
tracking); the mechanical half is emitted by `modules/cdio/legal_surface.py` and
every verdict reports under `trust`, `ux` or `visual`, so the score formula is
unchanged.

**Lens 5 — Conversion path.** Is there one clear primary action; is the value
before the friction; is the structure value-then-proof-then-ask; are there no
dark patterns (CDIO-02 §4; CDIO-04)? When the surface is a modal or focus-mode
decision (onboarding step, approval, irreversible confirmation), this lens also
applies the CDIO-09 criteria (applicability, one filled action, inert backdrop,
initial focus, single effect in flight, retry only if nothing changed, non-colour
selected state); they report under `ux`, `visual` and `trust`, so the score
formula is unchanged.

**Lens 6 — Mobile-first check.** Does the surface hold at a 320–390px width:
body text ≥ 16px, tap targets ≥ 44×44px, no horizontal scroll, the primary CTA
still reachable and prominent, content reflowed rather than shrunk (CDIO-01 +
CDIO-02 applied at the small breakpoint). Mobile is checked explicitly because a
desktop-only review misses where most users actually are. When the surface is an
app screen built for the hand rather than a page that must survive a phone, this
lens also applies the CDIO-08 criteria (thumb-zone primary action, value over
label, search zero state, input-method fit, bottom navigation count, tabular
figures); they report under the existing `ux` and `visual` dimensions, so the
score formula is unchanged.

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
  a buried or absent primary action, a fabricated trust signal, a dark
  pattern, or a legal-floor failure (a required legal page missing, or published
  with unfilled template fields — CDIO-10 §3). Criticals block a "done" verdict
  by themselves (CDIO-00 §4).
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

**A reference is evidence of intent, not of production truth.** When a surface
is built from an approved image (a mockup, a generated render, a competitor
screenshot), the review scores the rendered product, and it reports two things
separately: fidelity to the reference (composition, hierarchy, warmth, rhythm)
and fitness for the product (truthful routes, brand tokens, accessibility,
performance, every layout state). Affordances drawn in a reference, such as a
mock navigation, a "view sample report" card or a dashboard button, are not
requirements until the product can keep them; replacing one with a truthful
equivalent is an adaptation, recorded as such, not a fidelity defect. The
reverse holds as well: a polished render is no evidence that its links lead
anywhere. Neither score may be borrowed to excuse the other.

**An observation must be able to see what it claims.** A finding, or a pass,
about what a person sees needs a rendered observation of that state. Text
present in the page source or in a serialized payload is not rendered text:
some frameworks embed the not-found tree in the payload of every page, so a
source search "finds" an error page on every healthy page. A check at one width
says nothing about a layout state that exists only at another: a tablet width
where the header has already stacked while a card grid has not is its own
state, not a scaled desktop. Every piece of review evidence names the viewport
and theme it observed, and a layout state with no observation is reported as
unobserved, never as passing.

**`unobserved-layout-state`** (dimension `visual`, severity major). A review
that declares a surface complete while one of its materially different layout
or theme states (a breakpoint where the arrangement changes, a dark theme) has
no rendered observation.

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

## Taste pre-flight lens (render) — absorbed design-taste-frontend, 2026-11-16

Applies to landing pages, portfolios and redesigns (the skill's own scope; dashboards, data tables, wizards,
editors, native and realtime collab are out of scope). Source: `vendor/skills/design-taste-frontend/SKILL.md` (MIT,
Leonxlnx). Every item of that skill has a destination in `vault/knowledge_base/cdio/taste-absorption.json`; the
STATIC half is code (`modules/cdio/taste.py`, done-gate kind `taste:<file>`), and is NOT re-judged here. This lens is
the half that needs the rendered page: open it at desktop (1280+) and phone (390) widths, in light AND dark scheme,
and judge each item below as a finding with an observed value (a screenshot region, a measured line count, a
contrast ratio). A failing item is a `major` finding; a contrast failure is `critical` (an accessibility floor).

| Pre-Flight item (skill §14) | What to observe on the render |
|---|---|
| Page Theme Lock | one theme across all sections; no section flips light/dark mid-page |
| Color Consistency Lock | one accent colour, identical in every section |
| Shape Consistency Lock | one corner-radius system, or a documented per-component rule followed everywhere |
| Button Contrast Check | every CTA label ≥ 4.5:1 (≥ 3:1 at 18px+) against its own background, both schemes |
| CTA Button Wrap | no CTA label wraps to 2+ lines at desktop |
| Form Contrast Check | inputs, hint text, focus rings, labels, errors ≥ AA against the section |
| Italic descender clearance | italic display words with y g j p q are not clipped (leading ≥ 1.1 plus reserve) |
| Hero fits the viewport | headline ≤ 2 lines, subtext ≤ 20 words and ≤ 4 lines, CTA visible without scroll |
| Hero top padding | hero content does not float halfway down the viewport (≤ ~6rem top padding) |
| Hero stack discipline | ≤ 4 text elements; no tagline under CTAs, no trust micro-strip inside the hero |
| Split-Header Ban | no "big headline left + small explainer right" section headers |
| Zigzag Alternation Cap | no 3+ consecutive image/text split sections |
| Logo wall = logo only | no category labels under logos (and the logos are REAL customers: CONFLICT rule) |
| Bento Background Diversity | ≥ 2-3 cells carry real visual variation |
| Navigation on ONE line | desktop nav on one line, height ≤ 80px |
| Section-Layout-Repetition | no layout family used twice; ≥ 4 families over 8 sections |
| Bento has rhythm AND exact cell count | N items → N cells, no empty cell |
| Long lists use the right UI component | no > 5-item default bullet / divide-y list |
| No pills/labels overlaid on images | no tags printed over photos |
| No photo-credit captions as decoration | credits only for real photographers |
| No micro-meta-sentences | no clutter sentence under section eyebrows |
| No decoration text strip at hero bottom | no `BRAND. MOTION. SPATIAL.`-style strip |
| No floating top-right sub-text | no orphan corner paragraph in section headers |
| No scoring/progress bars with filled background tracks | no dashboard-style comparison bars on a landing |
| No locale / city-name / time / weather strips | unless the brief is genuinely place/time-zone driven |
| No decorative dots | coloured dots only for real semantic state |
| No `border-t` + `border-b` on every row | long lists/spec tables are not hairlined on every row |
| Quotes ≤ 3 lines | quote bodies ≤ 3 lines with name + role attribution |
| Mobile collapse | every multi-column layout collapses explicitly under 768px |
| Cards omitted | cards only where elevation carries hierarchy |
| Core Web Vitals | LCP < 2.5s, INP < 200ms, CLS < 0.1 measured (Lighthouse), not assumed |
