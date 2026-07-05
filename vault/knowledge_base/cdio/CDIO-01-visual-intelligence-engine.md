---
id: CDIO-01
name: Visual Intelligence Engine
type: dataset
domain: cdio
status: sealed
parent: CDIO-00
---

# CDIO-01 — Visual Intelligence Engine

Owns the measurable evaluation of typography, color, spacing, and visual
hierarchy. Inherits the value hierarchy and the reality contract from CDIO-00.
Every rule here is expressed as a threshold with an observed value, never as an
adjective. When a reviewer says "the typography is off," CDIO-01 forces the
statement into "the type scale uses five distinct sizes where the system
declares three, and the two heading levels differ by 1.09×, below the 1.25
minimum ratio needed to read as distinct levels."

## 1. Typography

Typography is the single highest-leverage surface in visual design because it
carries most of the content and most of the hierarchy. CDIO-01 evaluates it on
five measurable axes.

**Type scale (levels).** A viewport should present at most three typographic
levels at once — a dominant level (hero or page title), a secondary level
(section headings), and a body level. A fourth or fifth competing size is the
"visual noise" anti-pattern from CDIO-00. Measurement: count the distinct
font-size values applied to text in a single viewport region; more than three is
a finding. A fourth size is permitted only if it is clearly subordinate (caption
or metadata) and set below the body size, not competing with it.

**Modular scale ratio.** Adjacent type levels must differ by a perceptible
ratio. The minimum is 1.25 (major third); common systems use 1.25, 1.333, or
1.5. Measurement: divide each heading size by the next smaller level; a ratio
below 1.2 fails because the two levels read as the same size with an accidental
difference, destroying hierarchy. A ratio above 2.0 between body and the next
level is permitted for a deliberate hero but should be checked for balance.

**Line length (measure).** Body text line length should fall between 45 and 75
characters, with 66 as the classic optimum. Measurement: at the target
breakpoint, count characters per line. Below 45 the eye returns too often and
reading fragments; above 75 the eye loses the start of the next line. A full-
width paragraph on a 1440px container with no max-width is the most common
failure and is detectable directly from the absence of a max-width constraint.

**Line height (leading).** Body copy needs a line-height of at least 1.4 (1.5 is
safer for long text); headings can go tighter, 1.1 to 1.25, because their lines
are short. Measurement: line-height below 1.3 on body text is a finding —
descenders and ascenders of adjacent lines begin to crowd and reading slows.

**Font pairing and weight.** A surface should use at most two font families
(one for display, one for text) and a bounded set of weights (typically 400,
500/600, 700). Measurement: more than two families or more than four weights is
a consistency finding. A single family with multiple weights is always safe; the
risk is uncontrolled mixing.

## 2. Color

Color in CDIO-01 is evaluated for contrast (accessibility floor), semantic
meaning, and restraint.

**Contrast (the floor).** This is non-negotiable and traces to CDIO-00's
accessibility floor. Body text must reach a contrast ratio of at least 4.5:1
against its background; large text (≥ 24px, or ≥ 18.66px bold) and meaningful UI
components (icons, borders that convey state) must reach at least 3:1. These are
WCAG 2.1 AA. Measurement: compute the relative-luminance ratio between the
foreground and background colors. A CTA with white text on a light-green button
at 2.8:1 is a critical finding regardless of how the button looks. The scorer
computes this ratio directly from the two color values, so it is a mechanical,
non-opinion check.

**Semantic color.** Color must carry meaning consistently. The accent/interactive
color should appear on interactive elements and (ideally) nowhere else, so that
"this color means you can act on it" holds. Status colors — success, warning,
danger, info — must be distinct hues used only for their status. Measurement: the
accent hue appearing on a non-interactive decorative element, or danger-red used
as a decorative accent, is a "color meaninglessness" finding. Relying on color
alone to convey state (red/green with no icon or label) fails accessibility for
color-blind users and is a finding on its own.

**Restraint.** A surface should resolve to a small, intentional palette:
typically one or two brand hues, a neutral ramp (4–8 grays), and the status
colors. Measurement: more than roughly a dozen distinct non-neutral colors on
one screen signals an unsystematic palette. Gradients count as their endpoints.

## 3. Spacing

Spacing is where amateur and professional design most visibly diverge, and it is
almost entirely measurable.

**Systematic spacing.** Every gap, padding, and margin should resolve to a base
unit — commonly 4px or 8px — so the system produces 4, 8, 12, 16, 24, 32, 48,
64. Measurement: collect the spacing values on a surface; any value that is not a
multiple of the base unit (a stray 13px or 17px or 25px) is a "cramping /
off-system" finding. Off-system spacing is the leading cause of a design feeling
"slightly wrong" without an obvious reason, which is exactly the felt-not-
measured reaction CDIO converts into a threshold.

**Density and breathing room.** Related elements should be closer to each other
than to unrelated elements (proximity = grouping). Measurement: when the gap
inside a group equals or exceeds the gap between groups, the grouping is broken
and the layout reads as an undifferentiated field. Section padding on a landing
page should be generous (commonly 64–128px vertical between major sections on
desktop); cramped sections (< 32px between distinct sections) read as crowded.

**Alignment.** Elements should align to a shared grid or a small set of edges.
Measurement: text and controls that start at three or four slightly different
left edges (e.g., 16px, 20px, 24px) with no reason is a misalignment finding;
professional layouts share edges.

## 4. Visual hierarchy

Hierarchy is the composed result of typography, color, size, and spacing
directing the eye. CDIO-01 evaluates whether the intended reading order is the
actual reading order.

**Single dominant element.** Each screen region should have exactly one element
that is visually strongest — the thing the eye lands on first. Measurement: if
two elements share the largest size, the strongest color, and the highest
contrast, there is no single landing point and the "visual noise" anti-pattern
applies. On a hero, the dominant element is normally the headline or the primary
CTA, never both at equal weight.

**Deliberate contrast of scale.** The most important element should be
meaningfully larger or higher-contrast than the rest. Measurement: a primary CTA
that is the same size and weight as secondary links has no hierarchy; the primary
action should be visually distinct (filled vs. outline, larger, higher contrast).

**Progressive disclosure.** Secondary and tertiary information should recede.
Measurement: metadata, legal text, and helper copy set at the same size and
contrast as primary content flattens the hierarchy; these should sit at a lower
level of the scale and lower contrast (while still clearing the 4.5:1 floor if
they are body-sized).

## 5. The CDIO-01 anti-pattern catalog (with detection rules)

- **Off-system spacing** — any spacing value not a multiple of the base unit.
- **Scale explosion** — more than three competing type sizes in a viewport.
- **Flat hierarchy** — no single dominant element; multiple equal-weight foci.
- **Contrast failure** — text below 4.5:1 (or 3:1 for large/UI). Critical.
- **Decorative color** — the interactive hue used on non-interactive elements.
- **Color-only signaling** — state conveyed by hue alone, no icon or label.
- **Runaway measure** — body line length above 75 characters (missing max-width).
- **Crowded leading** — body line-height below 1.3.
- **Font sprawl** — more than two families or more than four weights.

## 6. How CDIO-01 feeds the score

Each axis above yields a pass/fail (or a graded value) that the scorer consumes.
The mechanically computable checks — contrast ratio, spacing-multiple
conformance, type-level count, line-length, family/weight count — are computed
directly and are not subject to opinion. The judgment-adjacent checks — whether a
single dominant element exists, whether hierarchy matches intent — are supplied
by the reviewer but must still cite the measured values (sizes, contrasts) that
justify the verdict. In both cases the output is a criterion plus an observed
value, never a bare adjective. This is what lets two reviewers reach the same
CDIO-01 verdict on the same surface.

## 7. Worked examples (criterion, observed value, verdict, fix)

**Contrast.** A pricing card uses `#8A8A8A` gray text on a `#FFFFFF` background.
Observed contrast: 2.9:1. Body floor: 4.5:1. Verdict: fail, critical. Fix:
darken the text to at least `#767676` (4.54:1) or larger. This is a mechanical
computation, not a judgment — the same two colors always yield 2.9:1.

**Type scale.** A landing hero shows a 48px headline, a 32px subhead, a 20px
lede, an 18px body, and a 16px caption — five sizes competing in one viewport.
Observed: 5 type levels. Ceiling: 3. Verdict: fail, major. Fix: collapse the
lede and body into one level and demote the caption below body, leaving three
perceptible levels (48 / 24 / 16, ratios 2.0 and 1.5).

**Spacing.** A card's internal padding reads 12px top, 16px sides, 20px bottom;
the base grid is 8px. Observed: 12 and 20 are not multiples of 8. Verdict: fail,
minor. Fix: snap to 16px all around, or 16/16/24 if a deliberate asymmetry is
wanted. Off-system spacing is the single most common cause of a layout feeling
"slightly off" with no obvious reason — CDIO converts that feeling into the exact
two values at fault.

**Measure.** A blog post body spans the full 1200px content column at 18px,
producing ~140 characters per line. Observed: 140 chars. Ceiling: 75. Verdict:
fail, minor. Fix: constrain the text column to `max-width: 65ch` (~680px), which
lands the measure near the 66-character optimum.

**Hierarchy.** A hero places the headline and the primary CTA at the same visual
weight — both large, both the accent color, both high contrast. Observed: two
elements share the dominant role. Verdict: fail, major (flat hierarchy). Fix:
keep the headline as the type-dominant element and make the CTA the
interaction-dominant element (filled accent button) so each region has one clear
focus rather than two competing ones.

## 8. Dark mode and state coverage (measurable)

**Dual-theme contrast.** A surface that supports light and dark themes must clear
the contrast floor in BOTH. Observed failures are common in dark mode where a
mid-gray that passed on white fails on a near-black background. Measurement:
compute the ratio in each theme; a pass in one theme and a fail in the other is
still a critical finding for the failing theme.

**Interactive-state visibility.** Every interactive element needs a visible
hover, focus, active, and disabled state, and the focus state must be
keyboard-visible (not removed via an outline reset with no replacement).
Measurement: a control with no focus indicator is an accessibility finding
(keyboard users cannot see where they are); a button whose disabled state is
indistinguishable from its enabled state is a clarity finding. These are
presence checks — the state either exists and is visible, or it does not.

**Optical alignment.** Beyond grid alignment, some elements need optical
correction: an icon inside a circular button, a triangular play glyph, or text
next to an icon may be mathematically centered yet look off-center. Measurement
here is bounded — CDIO flags an optically ragged group as a finish finding
(CDIO-03) but treats the exact correction as a craft adjustment rather than a
hard threshold, and labels it as a convention per CDIO-00 §5.

These examples are the template for every CDIO-01 verdict: name the criterion,
state the observed value, give the threshold, assign the severity by rule, and
provide the concrete fix. A reviewer who cannot fill all five fields does not yet
have a finding — they have an impression, which CDIO does not record.

## 9. Common false positives (what CDIO-01 does NOT flag)

A review that over-flags is as useless as one that under-measures, because it
buries the real defects in noise and trains the team to ignore CDIO. These are
the visual patterns that look like defects but are not:

- **A deliberate large hero-to-body ratio.** A 64px headline over 16px body is a
  4× jump — far above the 1.25 minimum — but this is intentional dominance, not a
  scale error. The ratio ceiling is a floor on *distinction*, not a cap on
  contrast. Do not flag a big, deliberate hero.
- **Decorative low-contrast that carries no information.** A faint background
  texture, a subtle divider, or a watermark at 1.5:1 is not a contrast failure —
  the 4.5:1 floor applies to *text and meaningful UI*, not to purely decorative
  elements that convey nothing. Flagging decoration for contrast is a false
  positive.
- **Intentional asymmetry.** Padding of 24px top and 16px bottom on a card can be
  a deliberate optical balance (heavier content sits lower), not off-system
  spacing — as long as both values are on the grid. Off-system means off the base
  unit, not merely unequal.
- **A single accent on a non-interactive brand mark.** The brand logo rendered in
  the accent hue is identity, not a broken "color means clickable" contract. The
  rule targets the accent leaking onto *content* that looks interactive but is
  not, not the brand's own mark.
- **More than two families when one is an icon font.** An icon font plus a text
  family plus a display family is three "families" by a naive count but only two
  *typographic* families; icon fonts do not count toward font sprawl.
- **A short caption below body size.** A 13px caption under 16px body is not a
  scale-explosion level; subordinate metadata set deliberately smaller is correct
  hierarchy, not a fourth competing level.

Before recording a CDIO-01 finding, confirm it is not one of these. When a value
is technically off a threshold but clearly intentional and harmless, note it as an
observation with the reason, not as a defect. The goal is a review the team
trusts because every finding is real.
