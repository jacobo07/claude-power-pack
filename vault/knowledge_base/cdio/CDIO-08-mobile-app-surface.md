---
id: CDIO-08
name: Mobile App Surface — the Hand-Held Axis
type: dataset
domain: cdio
status: sealed
governs: [cdio-reviewer, mobile-app-ui-design]
governed_by: CDIO-00
source: github.com/ceorkm/mobile-app-ui-design (SKILL.md + references/industry-conventions.md, absorbed 2026-09-18; README declares MIT, no licence file was retrievable, so the content is restated with attribution rather than copied)
---

# CDIO-08 — Mobile App Surface (the Hand-Held Axis)

CDIO-05 Lens 6 already asks whether a surface *survives* a narrow viewport: body
text at 16px or more, tap targets at 44×44 or more, no horizontal scroll, the
primary action still reachable. That lens was written for the responsive web
page that must also work on a phone. It does not ask the questions that belong to
a surface **designed for the hand from the start** — a native or native-style app
screen that is held, operated by a thumb, returned to daily, and judged in a few
seconds between other things. CDIO-08 is that axis.

The scope is precise: an app screen, flow, or component whose primary form factor
is a phone held in portrait, at a logical width of roughly 320 to 430 points. A
marketing landing page viewed on a phone stays under Lens 6 alone. A dense trading
terminal that happens to run on a phone stays under CDIO-06 F4 and CDIO-01; the
form factor does not override the content, which is the lesson CDIO-06 already
records about family routing. CDIO-08 adds criteria; it never relaxes a CDIO-00
floor, and where it and an older dataset appear to disagree, CDIO-00 decides.

## 1. How this dataset was absorbed (the classification contract)

The source is a community skill that teaches mobile UI design by principle and by
example. It is a good skill, and it is also a skill written for generation rather
than for judgment: it tells an author what to reach for, and several of its
instructions, applied as rules, would make CDIO issue verdicts it cannot defend.
So every claim in the source was classified before any of it entered the
knowledge base, and each class has a fixed consequence:

- **Already owned.** The claim is true and an existing dataset already carries it,
  usually with a stricter threshold. It is not duplicated here, because two
  authorities over one property drift apart. The pointer is recorded instead.
- **First-principle criterion.** The claim traces to a human constraint — reach,
  acuity, memory, error cost — and admits a threshold. It becomes a criterion in
  section 3 and may fail a review.
- **Convention.** The claim describes what users of a category have come to
  expect. It is recorded, and a reviewer may cite it, but it never produces a
  failing verdict on its own; CDIO-00 §5 says a convention can be overridden with
  a stated reason and a first-principle threshold cannot.
- **Unverified.** The claim is a number or an outcome the source asserts without a
  citation that CDIO can check. It is recorded so nobody re-imports it as fact,
  and it is never used as evidence.
- **Rejected.** The claim, applied as written, contradicts a sealed CDIO rule or
  a measured constraint. It is recorded with the reason, so the next absorption of
  a similar skill does not re-argue it.

The classification is the absorption. A skill whose every sentence entered CDIO
unchanged would have made the knowledge base louder and less consistent; the
value is in which sentences survived, and in what form.

## 2. What was already owned

The following source claims are correct and are already governed elsewhere. They
are listed so that a reviewer reaching for them lands on the owner rather than on
this file.

- **The 8-point spacing grid** ("all spacing divisible by 8 or 4") is CDIO-01's
  base-unit rule, and CDIO-00 names off-system spacing as the Cramping class.
- **Tap targets of at least 44×44** are CDIO-05 Lens 6 and a critical-severity
  floor in CDIO-05 §3. The source says 44pt, which is Apple's figure; Android's
  Material guidance is 48dp. CDIO keeps 44 as the floor that fails a review and
  records 48dp as the platform target an Android surface should meet. A 46dp
  target on Android is therefore a pass against the floor with a minor note, never
  a critical.
- **Designed empty, loading, error and success states** are CDIO-03 §7, where a
  truly blank state is a trust leak and a designed one is not.
- **Contrast checking** is the CDIO-00 legibility floor at WCAG 2.1 AA.
- **Soft rather than harsh decoration** and the warning against competing
  shadows, gradients and borders is CDIO-03's over-decoration rule.
- **"Keep text containers under 600px"** is a desktop proxy for line length. On a
  phone the container is always narrower; the governing rule is CDIO-01's 45 to 75
  character measure, which is what the 600px figure was approximating.
- **"Maximum four font sizes"** overlaps CDIO-01's three-level ceiling. They are
  not the same rule, and the resolution matters: a *level* is a role in the
  hierarchy, and a screen may carry a fourth *size* when that size is a caption or
  metadata line that sits below the body and competes with nothing. CDIO-01's
  three competing levels per viewport remains the failing threshold.

## 3. The criteria (what CDIO-08 can fail)

Each criterion names the dimension it reports under, so the deterministic scorer
in CDIO-05 §4 weighs it without any change to the formula. Severity follows
CDIO-05 §3; none of these is critical by itself, because a critical in CDIO is
reserved for floors, dead ends, buried primary actions, fabricated trust and dark
patterns, and a genuinely buried primary action is already critical under that
rule.

**`thumb-zone-primary-action`** (dimension `ux`, severity major). On a screen
operated one-handed, the primary action sits in the lower third of the viewport or
is docked to the bottom edge. The constraint is reach geometry: a phone held in
one hand is operated by a thumb pivoting from the lower corner, and the top of a
modern phone is outside comfortable reach for most hands. Observed-value form:
"primary CTA centred at 18% of viewport height on a 844pt screen". The threshold
of one third is a convention layered on a first-principle constraint, so a
reviewer must also observe that the screen is one-handed in use; a tablet-first or
two-handed media screen is not assessed.

**`value-over-label`** (dimension `visual`, severity major). In a label and value
pair — a statistic, a balance, a metric card — the value is the larger or heavier
element. The source's example is exact: making "Sales" bigger than "591" inverts
the hierarchy, because the user already knows which card they are looking at and
came for the number. Observed-value form: "label 17pt semibold, value 15pt regular".
This is the Hierarchy dimension of CDIO-00 applied to the commonest mobile
component.

**`search-zero-state`** (dimension `ux`, severity major). A search screen, before
the user has typed, shows at least one of: recent searches, popular or trending
items, or suggestions. A blank field over a blank screen is the CDIO-03 blank-state
leak in the place users visit most with the least intent. Observed-value form:
"search opened: field only, no content below".

**`selection-over-typing`** (dimension `ux`, severity minor, major when the field
is in onboarding). When the answer to a field comes from a small, known set — the
source's examples are job titles and preferences — the field offers tappable
choices, with an "other" escape that opens free input. Typing on a phone keyboard
costs more time and produces more errors than a tap, and onboarding is where the
cost is paid before any value has been delivered, which is CDIO-00's
Friction-before-value class. Observed-value form: "role field is a free-text input;
84% of expected answers fall in 8 known titles".

**`input-method-fit`** (dimension `ux`, severity major). Sliders, wheels and
steppers are for a coarse value set once; a value that is entered often or must
be exact is a text or numeric field. A slider for a transfer amount fails; a
slider for an initial goal set during onboarding passes. The constraint is motor
precision: a thumb dragging a slider cannot reliably land on one unit out of
hundreds. Observed-value form: "amount entered by slider, step 1, range 0 to 5000".

**`status-as-timeline`** (dimension `ux`, severity minor). A multi-step status —
an order, a delivery, an application, a refund — is shown as an ordered visual
sequence with the current step marked, not as a list of dated lines the user must
parse to find where things stand. The source adds opening with a confident status
sentence and humanising with a name or photo; those are recommendations attached
to this criterion, not separate criteria.

**`bottom-nav-destinations`** (dimension `ux`, severity major above five). A
bottom tab bar carries three to five destinations. Fewer than three is a sign the
bar is decoration; more than five shrinks each target and label below what a thumb
and an eye resolve, and both platform guidelines set five as the ceiling.
Observed-value form: "tab bar with 6 items, labels truncated".

**`first-run-differs`** (dimension `ux`, severity minor, only when assessed). The
source's "adapt to user stage" becomes testable in one narrow form: when a screen
serves both a user who has no data yet and one who has, the first-run state
explains what to do and the returning state shows the user's own content and
progress. It is assessed only when both states exist; a single-purpose screen with
no history is not failed for lacking stages.

**`tabular-figures`** (dimension `visual`, severity minor). Numbers that update in
place or align in a column — balances, timers, prices, statistics — use tabular
figures, so the digits do not jitter as they change and columns stay aligned. The
source said to use a monospace variant for large numbers; the correct instrument is
the tabular-figures feature of the text face, which keeps the family and fixes the
width. Observed-value form: "balance counter uses proportional figures; the value
shifts 3pt as 1 becomes 8".

**`shadow-tint-on-colour`** (dimension `visual`, severity minor, convention). A
shadow cast on a coloured surface is tinted toward that surface's hue rather than
drawn in neutral grey or black, which reads as dirt on colour. This is a convention
about perceived finish, so it fails only when the grey shadow is observed on a
saturated surface; on a white or neutral canvas a neutral shadow is correct.

## 4. The 60/30/10 proportion is a heuristic, not a criterion

The source teaches colour as 60 percent neutral base, 30 percent complementary
and 10 percent accent. It is a useful starting proportion and a poor rule: no
reviewer can measure a screen's colour area to the percent, and screens that work
break it constantly — a full-bleed brand onboarding screen is mostly accent, a
settings page is almost all neutral. CDIO therefore records it as authoring
guidance for the generative skill and never as a verdict.

What the heuristic is reaching for is already measurable in CDIO-00: the accent
colour appears on interactive elements and meaningful indicators and not on
decoration, which is the Colour-meaninglessness class. A reviewer who sees accent
overuse cites that class with the observed element, not a percentage. The source's
companion advice — text hierarchy through opacity steps of the neutral (roughly
100, 80 and 60 to 70 percent), and the accent at about 5 percent opacity for
secondary fills — is likewise authoring guidance, and every opacity step still has
to clear the contrast floor after blending; a 60 percent grey that falls below
4.5:1 on its background fails CDIO-01 regardless of what the heuristic suggested.

## 5. Industry conventions (recorded as conventions)

The source lists what users in each category expect. These are conventions in the
CDIO-00 §5 sense: they explain a choice and they can be broken for a stated
reason, and the reason to break one is usually differentiation. They inform the
CDIO-06 family choice and the CDIO-07 contract; they do not fail a review.

- **AI and technology.** Soft gradients, depth, a sense of motion suggesting
  intelligence. Natural CDIO-06 neighbours: F5 Cinematic Dark, F7 Glass.
  Colliding floor: motion without a reduced-motion equivalent (CDIO-07 §5).
- **Crypto and web3.** Dark canvases, bold type, high contrast, futuristic
  geometry. The source's lesson from a well-known wallet — that polish builds
  trust in a category where users fear losing money — is the CDIO-03 premium
  argument and is recorded as such.
- **Finance and banking.** Blue-leaning palettes, generous space, conservative
  type, a feeling of safety. The CDIO-07 picker already routes here to
  `trust_posture: critical` for irreversible operations. The source's praise of
  tactile touches — draggable charts, card flips — is compatible only inside that
  contract's motion budget.
- **Health and wellness.** Bright, approachable colour, friendly illustration,
  onboarding that does not intimidate. CDIO-07 picker question three: an
  intimidating task spends the budget on calm.
- **Sleep and meditation.** Deep blues and purples, minimal interface, soft
  transitions, low-contrast ambience. Colliding floor: "low contrast" is a mood,
  not a licence — body text still clears 4.5:1.
- **Education and learning.** Bright, playful colour and character-led
  feedback. CDIO-06 F6 Playful Color; CDIO-07 `character_policy` must be declared,
  because a persistent character is exactly the field that can be turned against
  the user through shame.
- **Fitness.** Energetic colour, bold type, progress made visible, complexity
  scaled to the user's stage (see `first-run-differs`).
- **Productivity.** Clean, dense, organised, strong grid. CDIO-06 F1 or F10,
  and F4 when data leads.
- **E-commerce and food.** Photography carries the product; the call to action is
  prominent; checkout is short; reviews, ratings and delivery estimates are the
  trust signals, which CDIO-03 already requires to be specific and honest.

## 6. Emotional design: where the Peak-End material went

The source's strongest section is emotional design: users remember the most intense
moment of an experience and its ending, so a product should design one peak and a
deliberate ending, remove negative peaks, and give emotional rather than purely
functional feedback. The research behind the peak-end effect is real — Kahneman and
colleagues' work on retrospective evaluation — and it is useful.

Absorbed as written, though, it becomes an instruction to add celebration, and
CDIO-07 exists precisely because celebration is a claim that can be false and a
behaviour that can be used against the user. So the material entered CDIO-07 as
section 11, as a method for *choosing* where a declared `celebration_policy`
spends itself, and for finding negative peaks to remove — never as a reason to
raise `expressiveness` or `celebration_policy`. The source's three strategic
principles (hide complex technology behind a familiar interface; make shared
insights about the user's identity rather than the app; make consistency a habit)
are recorded there too, with the note that the second one is a sharing mechanic
and must clear CDIO-02 §4 on manipulation.

## 7. What was rejected, and why

- **"Celebrate small wins; success states should bounce, glow and sparkle."**
  Rejected as a rule. It contradicts CDIO-07, where `success_posture` and
  `celebration_policy` are declared per surface, `celebrate` collides with the
  trust floor when the operation is queued or reversible, and a finance surface
  declares `celebration_policy: never`. A reviewer who applied the source's rule
  would fail correct, calm surfaces for under-delivery.
- **"Add subtle glow behind key elements; use backdrop blur."** Rejected as
  default polish. Glow and blur are family commitments (CDIO-06 F5, F7), not
  finish that every surface should carry, and applied everywhere they are the
  CDIO-03 over-decoration class. The source itself warns against flashy gradients
  and blur "unless you can pull it off", which is a family choice stated as taste.
- **"Section vertical padding at least 80 to 96px."** Rejected for phones. That
  range comes from desktop landing pages, where CDIO-01 records 64 to 128px
  between major sections. On a 667pt phone, 96px above and below a section spends
  nearly a third of the viewport on space, which buries content — the opposite of
  the source's own "reduce interaction cost". Mobile section spacing follows the
  relationship rule instead: related items close, the gap between groups roughly
  double the gap within them, all on the 8-point grid.
- **"Two font weights maximum"** in one part of the source and **"three"** in its
  anti-pattern list. The source contradicts itself; CDIO does not adopt either
  number. Weight is one of the channels CDIO-01 uses to build its three levels,
  and the failing threshold is the level count, not the weight count.
- **"Use monospace for large numbers."** Replaced by `tabular-figures`, which
  fixes the digit-width problem without importing a second typeface.
- **Default stack prescriptions** (a specific CSS utility framework, a specific
  icon set, a specific chart library, 375pt as the only baseline). These are the
  source's implementation choices for its own artifacts. CDIO judges rendered
  surfaces, not their toolchain, and CDIO-05 Lens 6 tests from 320pt precisely
  because 375pt is not the smallest phone in use.

## 8. What was recorded as unverified

- The claim that character animation and emotional feedback lifted a language
  app's daily active users from 14.2 million to more than 34 million in two years.
  The user numbers may be public; the causal attribution to animation is not
  something CDIO can check, and a design review must never cite a growth figure as
  evidence that a pattern works.
- The claim that 70 percent of theme-park visitors return because of remembered
  moments. No source is given.
- Case-study lessons attributed to named companies (a wallet, a neobank, an
  award-winning health app). They are recorded as illustrations of the conventions
  in section 5 and carry no evidential weight.

## 9. The authoring process the skill keeps

The Power Pack skill that ships beside this dataset keeps the source's five-step
process, because it is sound as a way to *produce* a screen: understand the
context and the one thing the user should notice first; structure the flow before
styling it; apply the visual system; design the emotional arc under the declared
CDIO-07 contract; then design every state. It also keeps the source's separation
of lenses — gather and judge visual direction and structural flow separately,
because mixing them in research produces screens that are pretty and lost, or
navigable and dead.

The skill generates. CDIO-08 judges. The skill cites these criteria as the checks
its output will meet, and the verdict belongs to `cdio-reviewer`, whose score comes
from the deterministic scorer and not from the author that built the screen.

## 10. Common false positives (what CDIO-08 does not flag)

- A primary action at the top of a screen that is read, not operated — an article,
  a receipt, a settings detail. `thumb-zone-primary-action` applies to screens
  whose job is an action.
- A two-item bottom bar on a product that genuinely has two destinations. The
  lower bound is a signal to look, not a failure; only above five fails.
- A label larger than its value when the label is the content — a category tile
  whose count is secondary metadata.
- A blank search screen in a product whose search is scoped to the user's own
  empty data on first run; the designed empty state of CDIO-03 governs instead.
- Free-text input for a genuinely open answer: names, messages, addresses.
- Neutral shadows on a neutral canvas.

## 11. Worked example

A savings app's home screen is reviewed at 390 by 844 points. Observed: the
"Add money" button is centred at 21 percent of viewport height beneath the header;
the balance card shows "Total balance" at 18pt semibold above the amount at 16pt
regular, in proportional figures; the goal-setup flow asks for a monthly amount
with a slider from 0 to 2000 in steps of 1; the bottom bar holds six tabs with
labels truncated to "Invest…" and "Insigh…"; a transfer completion plays a
full-screen confetti burst.

Verdicts: `thumb-zone-primary-action` fail, major ("primary action at 21% on a
one-handed home screen"); `value-over-label` fail, major ("label 18pt semibold,
value 16pt regular"); `tabular-figures` fail, minor; `input-method-fit` fail, major
("exact monthly amount by 1-step slider over 2000 values"); `bottom-nav-destinations`
fail, major ("6 destinations, 2 labels truncated"). The confetti is not a CDIO-08
verdict at all: it is judged under CDIO-07, where a finance surface that declared
`celebration_policy: never` and `trust_posture: critical` makes it a finding, and
a critical one if the transfer is queued rather than settled.

The fixes are each tied to their criterion: dock "Add money" to the bottom edge;
set the amount at the dominant size with tabular figures and demote the label to a
caption; replace the slider with a numeric field and a few preset chips; fold two
destinations into a "More" tab or the home screen. None of the fixes asks the
screen to look different for its own sake, which is the point of the axis.

## 12. Honest limits

CDIO-08 is measured from what a reviewer can observe in a rendered screen or a
recording. It cannot see how the phone is actually held by this product's users,
so the thumb-zone criterion rests on the reviewer confirming one-handed use and
remains a convention-weighted threshold. It cannot measure the colour proportion,
so 60/30/10 stays guidance. It has no platform-specific motion or haptics
criteria; those belong to CDIO-07's contract. And it has not yet been calibrated
against a corpus of real app reviews — the thresholds are the source's and the
platforms', checked against CDIO-00's constraints, and the first real reviews that
cite them are the evidence that will confirm or move them.
