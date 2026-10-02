---
id: CDIO-09
name: Focused Decision Surface — the One-Decision Axis
type: dataset
domain: cdio
status: sealed
governs: [cdio-reviewer, cdio-core]
governed_by: CDIO-00
source: InfinityOps Focused Monochrome UI (Owner reference "Dataset InfinityOps Focused Monochrome UI 1.md" + STANDARD-113, PR #467, distilled 2026-10-01)
evidence: one product, two consumers, production build in a real browser (see sec. 8)
---

# CDIO-09 — Focused Decision Surface (the One-Decision Axis)

CDIO-02 already says a screen should carry one primary action, and CDIO-04 already says the
value must arrive before the ask. Neither answers a narrower question that comes up every time a
product needs the user to commit to something: **when should the product stop showing everything
else, put one question in front of the user, and refuse to move on until that question is
answered or dismissed?** That interaction has a recognisable shape — a centred surface, the
product behind it blurred and dimmed, one high-contrast action, a quiet way out, a visible
position in the flow — and it has failure modes that the evaluative datasets do not name,
because they judge a page at rest and this is a surface that interrupts one.

CDIO-09 is that axis. It was distilled from an Owner-supplied reference and from what
InfinityOps learned building the pattern twice in its own product. The reference named the
style "Monochrome Premium SaaS / Linear-style Enterprise Minimalism" and then said the part that
matters: the defining characteristic is not the blur and not the rounded corners, it is the rule
of **one dominant decision at a time**. Everything secondary loses contrast so that the
interface concentrates the user on a single choice. That sentence is the dataset; everything
below is what it takes to execute it without breaking a floor.

CDIO-09 adds criteria; it never relaxes a CDIO-00 floor. Where it and an older dataset appear to
disagree, CDIO-00 decides.

## 1. Scope and the four conditions

A focused decision surface is justified only when **all four** of these hold. A surface that
meets three is a page, a panel, or an inline control, and building it as a focus surface is a
defect in its own right (criterion `focus-applicability`).

1. **Consequence.** The answer changes what the product does next, or cannot be undone from the
   interface. Creating a project, completing a step that unlocks the next, approving, connecting
   an automation, choosing a plan of execution. A preference toggle with no downstream effect
   does not qualify.
2. **Sufficiency.** Everything the user needs in order to decide fits on the surface. The
   product behind it is deliberately illegible; if the decision requires reading that page, the
   focus surface has taken information away from the user at the exact moment they need it.
3. **One question.** There is one principal decision. Several independent decisions are a form
   or a page. Several decisions in sequence are steps of one flow, each of which is itself one
   question — which is how a five-step onboarding stays inside this dataset.
4. **Justified interruption.** Interrupting is better than leaving the action inline, because
   inline the action would be easy to press without understanding its effect.

The exclusions are as important as the conditions, and each one was observed rather than
reasoned:

- **Comparison surfaces.** Dashboards, analytics, monitoring and any council-style view whose
  purpose is to hold several things side by side. Focus removes exactly what they exist to show.
  This is the same mismatch CDIO-06 sec. 6 records for Calm Utility on a comparison task, one
  level down: the family is fine, the interaction is wrong.
- **Multi-object management.** Dense lists, bulk edits, continuous navigation.
- **Informational notices with no decision.** An announcement does not earn the right to block
  the screen. A toast or an inline banner is the honest form.
- **Anything that must be read beside the page behind it.** The backdrop is unreadable by
  design.
- **Blur is not privacy.** The content behind the surface is still in the document and still in
  the accessibility tree unless it has been made inert, and it is always still in the DOM. A
  focus surface must never be the mechanism that "hides" data the user is not entitled to see.

## 2. Anatomy (what the surface is made of)

The anatomy is stated as roles, not components, so that it survives a change of framework. In
the order a screen reader meets them:

1. **The dialog host.** A modal layer that makes the rest of the document inert (not merely
   covered), locks background scroll, traps focus inside, and on close returns focus to the
   control that opened it.
2. **The header.** Product identity at low weight, and the position in the flow when there is
   one ("4 / 5", or a segmented bar with the same information in its accessible name).
3. **The question.** One heading, and it is the dialog's accessible name. If the heading and the
   accessible name differ, the user of assistive technology is answering a different question.
4. **One line of context.** The dialog's accessible description: why this is being asked, or
   what the answer changes.
5. **The decision content.** A choice group built on native radio semantics, a single field, or
   a summary card of what is about to happen. Never a mixture of all three.
6. **A status line.** Validation, in-flight and outcome messages, announced politely, in product
   language.
7. **The footer.** The secondary action on the leading side, restrained (text or outline). The
   primary action on the trailing side, filled with the strongest ink on the surface.

The visual weight follows the anatomy: the question and the primary action carry the only full
contrast on the surface; identity, position, context and the secondary action recede; the
backdrop recedes furthest.

## 3. The criteria (what CDIO-09 can fail)

Each criterion names the dimension it reports under, so the deterministic scorer in CDIO-05 sec.
4 weighs it without any change to the formula. Severity follows CDIO-05 sec. 3. None of these is
critical by itself; a genuine keyboard trap, a dead end, or an accessibility-floor failure on the
surface is already critical under the general rule and is reported as such.

**`focus-applicability`** (dimension `ux`, severity major). The surface meets all four
conditions of sec. 1 and none of its exclusions. Observed-value form: "settings toggle with no
downstream effect presented as a blocking modal (condition 1 fails)", or "analytics drill-down
opened in a focus surface; the user must compare against the table behind it (condition 2
fails)". The reviewer names the condition that fails; "this feels like too many modals" is not a
finding.

**`one-filled-action`** (dimension `visual`, severity major). Exactly one action on the surface
carries the filled, highest-contrast treatment, and it is the action that answers the question.
The secondary action is visibly subordinate — text or outline, lower weight — and is never a
second filled button. Observed-value form: "two filled buttons in the footer, 'Skip' and
'Continue', both #030305". This is CDIO-02's single primary action, made strict, because on a
surface whose whole purpose is one decision a tie is a contradiction rather than a weakness.

**`backdrop-inert`** (dimension `ux`, severity major). While the surface is open, nothing behind
it can receive focus, pointer input or scroll. Observed-value form: "Tab from the last footer
button reaches the sidebar link behind the dialog", or "mouse wheel over the backdrop scrolls
the page behind". Covering the page is not the same as disabling it; a visual overlay over a
live page is the commonest failure and is invisible in a screenshot.

**`initial-focus-intent`** (dimension `ux`, severity major). When the surface opens, focus lands
where the decision begins: on the first field when the surface collects data, and on the least
destructive action when it confirms something that cannot be undone. Observed-value form:
"irreversible completion dialog opens with focus on the filled 'Complete' button; Enter commits".
Focus on the close icon, or on the container with nothing focused inside, is also a fail.

**`focus-restored`** (dimension `ux`, severity minor, major when the surface sits inside a
keyboard-driven workflow). On close, focus returns to the control that opened the surface, unless
that control no longer exists, in which case it goes to the nearest meaningful successor. The
observed failure that put this criterion here was subtle: the restore decision changed in the
same render that closed the dialog, and the old cleanup moved focus to the opener behind a
dialog that was, from the user's side, still closing. Observed-value form: "after Cancel, focus
is on the document body; the opener was the 'Complete step' button".

**`single-effect-in-flight`** (dimension `ux`, severity major). Once the primary action has
fired, a second press, Enter, or Escape does not fire a second effect or abandon the first. The
primary action stays focusable (so the screen reader does not lose its place) but inert, and the
in-flight state is visible. Observed-value form: "double click on 'Create project' sent two
POSTs", or "Escape during submission closed the dialog; the effect completed unseen".

**`retry-only-if-nothing-changed`** (dimension `trust`, severity major). After a failure, a
retry affordance appears only for outcomes where nothing was committed, and every outcome has its
own product-language sentence. Raw transport text — a status code, an exception name, "Failed to
fetch" — never reaches the surface. Observed-value form: "session-expired failure shows 'Try
again'; retrying cannot succeed and the user is not told to sign in". This is the
technical-failure-to-product-state rule applied to the one surface where a wrong retry is most
likely to commit something twice.

**`selected-state-non-color`** (dimension `visual`, severity major). On a monochrome surface,
selected, unselected, hover, disabled and focused states of a choice must be distinguishable
without hue and without relying on a shade difference below 3:1. The selected state carries a
change of shape or weight — a thicker border, a filled radio dot, a check — and the unselected
control's own boundary clears the WCAG 2.1 non-text contrast threshold of 3:1 against its
surroundings. Observed-value form: "unselected radio ring #C3C9D5 on card #F6F8FC = 1.56:1".
Monochrome removes the channel most designs use for state, which is why this criterion lives
here rather than in CDIO-01.

**`progress-is-announced`** (dimension `ux`, severity minor). A multi-step flow shows the current
position and the total, and the same information is available to assistive technology — a
progress bar's accessible name or value, or the visible "4 / 5" text inside the dialog's labelled
region. Observed-value form: "segmented bar of five spans with no role, no name; position not
announced". A single-step confirmation is not assessed.

**`backdrop-not-privacy`** (dimension `trust`, severity major). Data the current user is not
entitled to see is not rendered behind the surface on the assumption that blur hides it.
Observed-value form: "other tenants' names present in the DOM and the accessibility tree behind
the onboarding blur". If the data is genuinely unauthorised, this is also a security finding
outside CDIO and is escalated as one; the CDIO verdict records only the trust failure.

## 4. The monochrome variant and where it collides with the floors

The reference's aesthetic is CDIO-06 F1 Editorial Minimalism with **zero accent hue**: near-black
ink is the only state colour, so progress, selection and the primary action all share it, and
nothing else on the surface competes. CDIO-06 records this as F1's zero-accent variant rather than
as an eleventh family, because it changes one F1 commitment (the indigo accent) and keeps every
other; a family that differs from an existing one by a single token is a variant, and splitting it
would have created two authorities over the same palette.

The variant should be **scoped**. In InfinityOps the monochrome palette lives on the focus surface
only, under a data attribute, and the rest of the product keeps its own family. That scoping is
the recommended default for any product adopting this pattern: the monochrome surface reads as
"this is the moment that matters" precisely because the product around it is not monochrome. A
whole application in the focus palette loses the contrast between the decision and everything
else, which was the point.

Removing hue moves the variant's failures onto two axes, and both were measured on the exemplar.

**(a) Quiet chrome below the non-text floor.** With no colour to separate controls from their
ground, designers reach for whisper-grey borders, and the controls stop being identifiable. In
the InfinityOps tokens as distilled, the unselected radio ring sits at 1.56:1 against its card,
the text-field border at 1.23:1 against the surface, and the unselected card border at 1.18:1.
The selected state is excellent (the selected border is 11.7:1); the problem is entirely the
resting state, which is the state the user meets first. WCAG 2.1 asks 3:1 for the visual
information required to identify a control. A slightly different fill helps the eye and does not
count, because the fill difference is itself below 1.1:1.

**(b) Hint text treated as decoration.** An example answer shown inside an empty field is still
text. The exemplar renders its example line at 2.76:1, which reads as appropriately quiet and
fails the 4.5:1 text floor. If the hint carries information — and an example of a good answer
does — it must be readable; if it does not, delete it. This is the same trap CDIO-06 sec. 5 names
for F1 and F10: restraint governs the quantity of elements, never the contrast of text.

What the variant gets right, and should be kept: body ink at 7.5:1, muted ink at 5.8:1, the
primary action's label at 20.6:1, and a five-step progress bar whose completed and remaining
segments differ by 10.5:1 against each other.

## 5. Motion and the backdrop

The backdrop's job is to say "the product is still here, and it is not the subject now". Blur and
dim do that together; either alone is weaker. Blur without dim leaves the backdrop competing on
luminance, and dim without blur leaves it legible enough to read, which invites the user to try.

Motion belongs to CDIO-07, and this dataset adds only what the focus surface specifically needs:
the surface enters as one unit, the backdrop and the card do not animate independently in a way
that makes the card arrive before the page behind it has gone quiet, and under reduced motion the
transition collapses to opacity with no movement and no blur animation. A surface that blocks its
own primary action until an animation finishes is a CDIO-07 floor breach (blocking animation), not
a CDIO-09 finding, and is reported under CDIO-07.

## 6. What was deliberately not universalised

InfinityOps built this in one stack and learned things that are true there and nowhere else.
Recording them here would have taught every other product a constraint it does not have. They are
listed so that nobody re-imports them as doctrine:

- **The exact hex values.** They are measured from one Owner-designated anchor image. Another
  product's monochrome ink is its own decision; only the ratios in sec. 4 transfer.
- **The blur radius, dim alpha and shadow.** Instance values. The transferable rule is
  "blur and dim together".
- **Five steps.** The reference showed "4 / 5". Step count is the product's.
- **A transport helper's name, a BFF route shape, an id validator.** These were real bugs and
  real fixes in that codebase (an effect whose HTTP status was flattened, a path parameter that
  survived URL encoding as "..") and they are captured in the InfinityOps UKDL and in Power Pack's
  `web_surface` B1 baseline, which is where a transport rule belongs. CDIO judges the surface.
- **A global CSS reset that removed every radius.** A trap of that product's stylesheet, not of
  the pattern.
- **Spanish copy, sounds, and the specific onboarding questions.** Content.

The test applied to every item was the one CDIO-06 sec. 9 used for the F10 reference bank:
does the trait survive a change of brand, platform or domain? Everything on this list fails it.

## 7. Traps that transfer

These did survive the change-of-domain test, because they are about the pattern rather than the
stack:

- **A portal escapes token scope.** A modal rendered into a portal is no longer inside the subtree
  that defines its tokens. Scoped tokens must be applied to the portal root as well, or the surface
  silently renders with the product's default family.
- **Remounting the surface between steps destroys state and focus.** A multi-step focus flow must
  keep one surface mounted and swap its content; remounting per step resets scroll lock, focus and
  any in-progress input, and looks identical in a screenshot.
- **A test that finds no population passes green.** A reduced-motion assertion that first filtered
  out the reduced variants and then asserted "opacity only" over zero animations was green for the
  wrong reason. Every sweep over states or variants needs a floor on how many it found.
- **The restore decision and the close can land in one render.** If the restore flag is read
  through a stale closure, the cleanup acts on the old value. Read it through a reference that is
  committed before the passive cleanup runs.
- **A screenshot cannot show inertness.** Backdrop inertness, scroll lock and focus containment
  are behaviours. They need a real browser, a real wheel event and a real Tab key, with a control
  run in which the lock is deliberately lifted so the test is shown to be able to fail.

## 8. Evidence, scope and what is still planned

Scope claimed: **interaction-class doctrine for any product with consequential single decisions**,
judged by `cdio-reviewer`. Not claimed: that every product should adopt the monochrome variant, or
that the pattern belongs in places sec. 1 excludes.

The evidence ladder as of 2026-10-01:

| rung | status | evidence |
|---|---|---|
| local success | reached | InfinityOps onboarding, five steps, creates the project |
| repeated success | reached | a second consumer, roadmap step completion, built on the same primitives |
| production reality | reached | production build, real browser, three viewports and reduced motion; 16 of 16 twice, the second run against reviewed reference captures |
| adversarial survival | partial | mutation drills went red on remount and scroll lock; the restore-focus race was found by review, not by a drill |
| transfer | not reached | no second product has adopted the pattern |
| enforcement | judged, not gated | reviewer criteria above; no deterministic gate |

Because transfer is not reached, a mechanical check in `design_gate` (for example, refusing a
raw colour inside a declared focus surface, or requiring each focus surface to cite which
condition of sec. 1 it meets) is **PLANNED**, not built. It becomes worth building when a second
product adopts the pattern, because only then is there evidence that the declaration format is
stable. Until then these criteria are judged by the reviewer with an observed value per finding,
exactly as CDIO-08's are.

## 9. Common false positives (what CDIO-09 does not flag)

- **A non-modal focus mode.** A full-page step in a wizard, without a backdrop, can satisfy the
  one-decision rule perfectly well. CDIO-09 judges the interruption pattern; it does not require
  that every decision be a modal.
- **A dense confirmation.** A confirmation that must show a twelve-line summary of what will be
  committed is still one question. Length is not multiple decisions.
- **Colour on the surface.** A product may adopt the focus pattern without the monochrome variant.
  `selected-state-non-color` still applies (state must not depend on hue alone), but the absence
  of monochrome is never a finding.
- **A destructive confirmation focusing Cancel.** That is `initial-focus-intent` passing, not a
  usability defect, even though it adds a keystroke for the user who meant to confirm.
- **System dialogs.** The platform's own permission and file dialogs are out of scope.

## 10. Contract with the review pipeline

`cdio-reviewer` applies sec. 3 under CDIO-05 Lens 5 (conversion path) whenever the surface under
review is a modal or focus-mode decision; the verdicts report under the existing `ux`, `visual`
and `trust` dimensions, so the score formula is unchanged. `cdio-core` routes a request that
mentions an onboarding modal, an approval or confirmation dialog, a "focus mode", or "one decision
at a time" here first, and to CDIO-06 F1's zero-accent variant when the request is about the look
rather than the behaviour. The criteria grammar is parsed by `tools/test_cdio_focus.py`, which
fails if a criterion loses its dimension or severity, if the population falls below the one sealed
here, or if any wiring point named in this section disappears.
