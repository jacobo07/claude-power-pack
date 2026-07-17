# DESIGN_GOVERNANCE.md — Visual quality is a done-gate

> Normative. Any project using Claude Power Pack that ships a user-facing visual
> surface obeys this from its first commit. Domain: dashboards, admin panels, landing
> pages, product UI, onboarding, any rendered surface. Origin: `kobicraft-panel`
> (dash.kobicraft.net) design-system work, 2026-07-14 → 2026-07-17.
> Companion to `COPY_GOVERNANCE.md`. The CDIO scorer
> (`modules/cdio/scorer.py`) makes most of these mechanically refusable; where a
> criterion is mechanical, that is stated and the check is named.

## The rule (imperative)
A visual surface that builds and returns HTTP 200 is NOT done. Done requires the CDIO
gate: a Design Quality Score ≥ 80 (project pane-gates may set ≥ 85) AND zero critical.
A surface MAY ship with a log warning. A surface MUST NOT ship failing VQ-1 (material),
VQ-4 (colour), or VQ-6 (identity). "It looks fine" is not a verdict — every judgment
names a criterion and an OBSERVED value (`T-DESIGN-OPINION-VS-CRITERIA-001`).

## Section 1 — Design System Authority
`DESIGN.md` at the repo root is the single source of visual truth. Read it before
building or restyling any surface (`PR-DASH-DESIGN-MD-FIRST-001`).
- Every colour, spacing, radius, type-size, and material value a component declares
  comes from a token `DESIGN.md` defines. A raw literal where a token exists is how a
  design system silently dies — not in one bad screen, but in a hundred harmless-looking
  literals (`HR-DASH-DESIGN-TOKEN-FIRST-001`; mechanical proxy: VQ-7).
- A legitimate literal is a value with **no** token equivalent, shipped with a one-line
  comment naming why. "No token existed" is a reason; "it was faster" is not.
- No aesthetic family declared in `DESIGN.md` front-matter ⇒ the surface is unreviewable.
  `check_family_declared` returns CRITICAL (forces BLOCK) — `PR-DESIGN-FAMILY-BEFORE-BUILD-001`.

## Section 2 — Colour Discipline (VQ-4, mechanical)
Maximum **2** tint fills above 10% opacity active in any one card / container. The
dominant fill communicates the most urgent datum; everything else subordinates to an
**outline** (transparent background) or **text-only** tint.
- Mechanical check: `check_color_discipline(fill_opacities)` — counts fills > 10% in one
  card; > 2 ⇒ MAJOR. Outline chips and text tints are 0-fill and do not count.
- The exemption is for a **hue** reused as a state signal (a red left-border echoing a red
  status). It is NOT a licence to stack N filled tint surfaces. Measure fills, not hues.
- Watch the cascade: an "outline" chip that also carries a `.badge.{color}` class can be
  out-specified and render as a FILL. Verify specificity, not just the intended class
  (`kobicraft-panel` shipped filled "outline" chips for weeks behind a 0,1,0-vs-0,2,0 bug).
- Rule of thumb: if 3+ colours compete, one is redundant — find it and remove it. More
  colours hide information, they do not add it (`T-DESIGN-MORE-COLORS-MORE-INFORMATION-001`).

## Section 3 — Logo Swap Test (VQ-6, identity)
Every new page passes the logo swap test before merge: replace the brand logo with another
company's — if the surface still looks completely natural, it is generic (FAIL).
- PASS = ≥ 3 of 4 KobiiCraft-specific tells actually **rendered** (not present only in code
  comments): operator-language vocabulary · role-separated state system · product-logic-bound
  affordance · a named institutional surface.
- Identity lives in the information system — WHAT the surface says, HOW (operator idiom),
  and WHICH decisions it encodes — not in the material. **Glass cannot fix an identity
  fault** (`HR-DASH-VOCABULARY-KOBIICRAFT-001`, `PR-DASH-LOGO-SWAP-ON-NEW-PAGES-001`).
- Fix a VQ-6 miss with copy revision and by wiring the REAL existing systems, never with
  more glass, and never by inventing a name to pad the count (the manufactured-finding
  anti-pattern in reverse). A tell a surface structurally cannot carry (a login form has no
  per-item lifecycle) is documented N/A, never fabricated.

## Section 4 — Material System (VQ-1, BLOCK-tier)
Elevated surfaces the user acts on (cards, modals, panels) use the glass material
(`backdrop-filter` via the `.kc-glass*` helpers / `--kc-mat-*` tokens) with the mandatory
`@supports` fallback to a **translucent** fill — never a flat hex. The only legitimate solid
fill is the page base and the surfaces a `DESIGN.md` explicitly ratifies flat (tables,
sidebar, topbar, console). Two physics laws, learned via CDIO BLOCK and verified by
computation, not by eye:
- Glass needs a backdrop with non-zero alpha AND spatial variation across the surface's own
  footprint — blurring a flat field returns a flat field (a declared material at 0.0000
  effective alpha is fake frost).
- Never nest `backdrop-filter` inside `backdrop-filter` — the frost compounds to muddy grey
  at double the cost; nested wells get a translucent recess, no blur of their own.
`HR-DASH... material` rules; VQ-1 is the only BLOCK-tier VQ criterion.

## Section 5 — CDIO Gate Requirements
Any PR that touches a visual component runs `cdio-reviewer` before it is called done
(`PR-CDIO-REVIEW-GATE-001`). The score is computed by `modules.cdio.scorer.score_review`,
not by the reviewer's opinion. Required outcomes:
- **VQ-1** material — no solid fill on an elevated surface (BLOCK).
- **VQ-4** colour discipline — `check_color_discipline` ≤ 2 fills/card (MAJOR).
- **VQ-6** logo swap — ≥ 3/4 rendered tells before merge (MAJOR; a done-gate by doctrine).
- **VQ-7** token consumption — every value from a token, or a commented legitimate literal (MAJOR).
- Verdict math: any critical ⇒ BLOCK; score < 60 ⇒ BLOCK; 60–79 ⇒ REVISE; ≥ 80 (≥ 85 on
  pane-gated repos) and zero critical ⇒ APPROVE. Zero Findings Is Valid — never manufacture
  a finding to justify the review.

## Section 6 — Permanently prohibited anti-patterns
1. Copying Linear / Vercel / GitHub / Stripe / Notion wholesale without reconstructing from
   the product's own `DESIGN.md` and tokens.
2. Glassmorphism as a trend — glass only where it earns real depth on a surface the user
   acts on; never as decoration, never nested, never over a backdrop that can't refract it.
3. 3+ tint fills competing in one card / container.
4. Generic vocabulary on command surfaces — stock SaaS/AIOps/ITSM labels that pass under any
   logo.
5. Declaring a surface done from material alone. Material (VQ-1) and identity (VQ-6) are
   orthogonal gates — passing one says nothing about the other
   (`T-DASH-GLASS-FIXES-EVERYTHING-001`).

## Applies to
Any pull request or deploy that adds or restyles a user-facing visual surface.
