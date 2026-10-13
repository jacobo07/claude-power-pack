---
id: CDIO-11
name: Componentry Catalogue — the Measured Motion-Component Axis
type: dataset
domain: cdio
status: sealed
governs: [cdio-reviewer, cdio-core]
governed_by: CDIO-00
source: componentry.dev (MIT, github.com/harshjdhv/componentry @ b602c28), absorbed 2026-10-13
evidence: static scan of the vendored source, 54 of 54 published components (see sec. 6)
---

# CDIO-11 — Componentry Catalogue (the Measured Motion-Component Axis)

CDIO-07 decides how much a surface is allowed to move. CDIO-06 decides what it looks like.
Neither says anything about a third thing that arrives in every modern front-end project:
a ready-made animated component, copied in from a public library because it looks good in
a preview video. That component brings its own motion, its own input model and its own
accessibility posture, and those were decided by its author for a demo page, not by the
product that adopts it. The question this dataset answers is narrow and recurs constantly:
**before an off-the-shelf animated component lands on a surface, what does its source
actually do, which contract does it need, and what must be fixed before it may ship?**

CDIO-11 answers that question for one library, componentry.dev, in full: all 54 published
components, each measured from its own source, each turned into a motion pattern that the
existing contract-aware resolver serves or withholds. The library was chosen by the Owner.
The method is general, and sec. 10 records the parts of it that transfer to any other
component library absorbed later.

CDIO-11 adds criteria; it never relaxes a CDIO-00 floor. Where it and an older dataset
appear to disagree, CDIO-00 decides, and where a component and CDIO-07 disagree, CDIO-07
decides. A component is never a reason to raise a declared contract.

## 1. What was absorbed, and what kind of thing it is

componentry.dev describes itself as a component library for polished interfaces: animated
React components with editable source, installable through the shadcn command line or
through an editor's MCP integration. Upstream sorts its catalogue into five categories:
Hero Backgrounds (11), Visual Effects (10), ASCII Effects (1), Text Animations (7) and
Components (25). The categories are upstream's, and CDIO keeps them because they are the
best available statement of what the author meant each piece for.

It matters what this library is **not**. It is not an aesthetic family in the CDIO-06 sense:
its pieces do not share a palette, a type system or a spacing scale, and a page assembled
from several of them has no visual grammar unless the adopting product supplies one. It is
not a design system either: it has no tokens that bind a product, no form controls worth
standardising on, and no states for the hard parts of an interface (empty, error, loading,
disabled). It is a **catalogue of expressive moments**: hero backgrounds, image effects,
headline animations and a set of showcase widgets (a clock, a calendar heat map, a flight
card, a music player, a keyboard, several carousels). Every one of them exists to be looked
at. That fact decides almost everything below, because CDIO-07 already says where looking
is the point and where it competes with the task.

The absorption therefore does three things and no more. It vendors the source so that every
claim can be checked against a file. It measures the source with a fixed, inspectable
scanner. And it turns each measurement into a motion pattern with a minimum contract and a
list of things to fix before use. It does not rank the components by beauty, it does not
recommend any of them, and it does not make any of them a default.

## 2. Provenance, licence and the vendoring rules

The source is vendored byte-identical under `componentry/` at commit `b602c28` (main,
pushed 2026-10-12). The licence is MIT; the notice belongs to Harsh Jadhav and must travel
with every copy, including a copy pasted into a client project. The vendored set is the
whole `packages/ui` package (64 source files, of which 54 are the published components and
10 are support primitives that the published ones import or that upstream keeps for its own
site: autocomplete, command, two button and badge variants, input, kbd, scroll area,
spinner, tabs, and a WebGL error boundary), plus upstream's README and its registry file,
which is the catalogue the scanner reads. The directory's NOTICE carries the operating
rules; the short version is: never edit vendored files, re-vendor at a new commit to
update, and treat the generated catalogue as output, never as input.

The support primitives are vendored because the published components import them, not
because CDIO endorses them. They are not catalogued, they carry no motion entry, and a
request for a form control or a command palette is not routed here.

## 3. The pipeline: discover, measure, derive

The pipeline lives in `modules/cdio/componentry_catalog.py` and is the only producer of
the 54 entries in `visual-patterns/componentry-*.md` and of `componentry/catalog.json`.

**Discover.** The catalogue is read from upstream's own registry, never from a list kept by
hand. A component the registry lists whose source file is missing is an error. The
registry parse is cross-checked against the number of slug fields in the file, so an entry
written in a shape the parser does not understand fails loudly instead of disappearing
(sec. 10, first trap, is the incident that put this check here).

**Measure.** Each source file is scanned with a fixed set of regular expressions, listed in
sec. 4. Each signal records the first line where it appears, so every sentence an entry
says about a component points at a line a reviewer can open. A signal is a static fact
about the text of the file. It is never a claim about what the component does in a browser.

**Derive.** From the upstream category and the measured signals, the module derives the
`motion:` block that `modules/cdio/motion_patterns.py` consumes: the surfaces the component
applies to, the surfaces it is excluded from, the minimum expressiveness and motion budget
a contract must declare to receive it, and the reduced-motion requirement. Derivation only
narrows. A measured cost can raise a component's minimum contract; nothing a component
does can lower it, and no component can propose that a product raise its own contract.

Because the entries are ordinary motion patterns, they are live the moment they exist: the
resolver discovers every `*.md` with a `motion:` block, and the CDIO visual advisory hook
calls the resolver when a surface file is written. One change was made to that consumer.
The advisory line lists each applicable pattern by name, which is right for a corpus of a
dozen hand-written patterns and wrong for a catalogue of fifty-four: a landing page with a
high contract would have received one line naming every component. Catalogue families are
now summarised in that line as a count and a pointer to this dataset, while the resolver
itself still returns every entry individually to any caller that asks.

## 4. The signals, and what each one cannot see

| signal | what it matches | what it cannot see |
|---|---|---|
| `reduced_motion` | the reduced-motion media query, the framer-motion hook, the Tailwind variant, a reduced-motion prop | whether the reduced variant is equivalent |
| `webgl` | a WebGL context, three.js, react-three-fiber | whether WebGL is available on the target device |
| `canvas2d` | a 2D canvas context | what the canvas draws |
| `svg` | an inline SVG element | whether the SVG is decorative |
| `infinite` | infinite repeats, intervals, per-frame hooks, the GSAP ticker | when the animation stops |
| `raf` | any animation-frame request | whether it is a loop or one frame |
| `pauses_offscreen` | intersection observers, in-view hooks, page-visibility checks | whether the pause actually happens |
| `pointer` | mouse and pointer move or enter handlers, hover props | what the hover reveals |
| `keyboard` | key handlers, a tab index | whether the keyboard path reaches the same content |
| `touch` | touch and pointer-down handlers, drag and pan | gesture quality |
| `scroll` | scroll hooks and handlers, wheel handlers, smooth-scroll libraries | scroll hijacking |
| `aria_hidden` | the aria-hidden attribute anywhere | which element carries it |
| `accessible_name` | aria-label, aria-labelledby, a role, a screen-reader-only class | whether the name is accurate |
| `webgl_fallback` | the vendored error boundary, a null-context guard | whether the fallback renders anything |

Two calibration decisions are worth recording because they are where a naive scanner lies.
First, `matchMedia` alone is not a reduced-motion signal: in this library it is also used
to read the colour scheme (circuit board) and a viewport width (dithered logo). Matching it
would have credited two components with a floor they do not attempt. Second, an
animation-frame request is not proof of a loop: in this library it is also used for a
one-shot deferred measurement, a scroll throttle, and an animation that stops when a
target is reached. The scanner therefore keeps `infinite` and `raf` apart. On a canvas or
WebGL surface a frame request is treated as a per-frame renderer, which matches every such
component inspected. On the DOM, a frame request alone raises nothing; the entry says that
continuity is undecidable by reading and must be measured in a browser.

"Not detected" in an entry means that none of the expressions appears in the file. It does
not mean the property is absent at runtime. A component can honour reduced motion through
a parent `MotionConfig` the adopting product supplies, and a scanner of one file cannot see
that. The phrasing in every entry keeps that distinction.

## 5. The derivation rules

The starting contract comes from the upstream category:

| upstream category | applies to | minimum expressiveness | minimum motion budget |
|---|---|---|---|
| Hero Backgrounds | landing, hero | high | medium |
| Visual Effects | landing, hero, product tour | high | medium |
| ASCII Effects | landing, hero | high | medium |
| Text Animations | landing, hero, product tour | moderate | low |
| Components | landing, product tour | moderate | low |

Every component is excluded from checkout, auth, admin, settings, forms, dashboards,
destructive flows, documentation and list-detail surfaces. That is the same exclusion set
as the ambient grain texture pattern (VP-011), for the same reason: on a surface where the
user is doing a task, expressive motion competes with the task, and CDIO-07 sec. 5 already
names that collision. Onboarding and pricing are deliberately absent from the applies-to
lists: neither is excluded, but neither is a surface this library was designed for, and
the resolver only serves a pattern to a surface it applies to.

Then the measurements raise the minimum, never lower it:

- A component that renders per frame on canvas or WebGL needs `expressiveness: high`
  whatever its category, because a per-frame renderer is the most expressive and most
  expensive thing a surface can carry.
- If that renderer has a detectable off-screen pause, it needs `motion_budget: medium`; if
  it has none, it needs `high`, because it spends main-thread time, GPU time and battery
  for as long as the page is open, including while the user reads something else.
- A DOM component with an infinite animation needs at least `motion_budget: medium`.

Every entry states which of these rules raised it, with the line that triggered the rule,
under "Por que este contrato minimo". A component that nothing raised says so.

The reduced-motion requirement is `equivalent` for every entry without exception. That is
not a measurement; it is the CDIO-07 floor, restated where it will be tested most. A
contract that declares anything weaker receives none of these components.

## 6. What the catalogue measured

Produced by `python -m modules.cdio.componentry_catalog build` over the vendored source at
`b602c28` on 2026-10-13, and re-derivable at any time with `check`, which fails on drift.

- **54 of 54** published components catalogued, 0 registry errors, 10 support files.
- **Render technology:** 17 WebGL, 8 canvas 2D, 7 SVG, 22 DOM.
- **Minimum contracts:** 20 need high expressiveness and a high motion budget; 7 need high
  and medium; 7 need moderate and medium; 20 need moderate and low. 29 components were
  raised above their category's starting contract by a measurement.
- **Reduced motion:** 23 components read the preference somewhere in their source. **31 do
  not**, including most of the per-frame hero backgrounds and visual effects.
- **Pointer without a keyboard path:** 21 components respond to the pointer and have no
  detectable key handler or tab index.
- **Continuous work without an off-screen pause:** 27 components.
- **Animation-frame use whose continuity is undecidable by reading:** 6 components.
- **Canvas without an accessible name or aria-hidden:** 11 components.
- **WebGL without a detectable failure path:** 1 component (hero geometric).
- **Only the equivalence check remains:** 9 components read reduced motion and trip no
  other check (annotated text, grain gradient, hover transition, liquid glass carousel,
  magnetic dock, orbit card stack, spectral ribbon, spiral 3D slider, sticky scroll cards).
  These are the cheapest to adopt, and still not adoptable without a browser check.
- **Dependencies:** framer-motion in 24 components, three.js in 6 (react-three-fiber in 5),
  GSAP in 4, lenis in 2, next-themes in 2, opentype.js in 1. A component that pulls three.js
  into a page that had none adds the largest dependency in this list for one hero.

The numbers describe the source, and the source is upstream's. They are not a judgement of
the author's skill: a demo library optimises for the demo, and the floors below are the
floors of a product, which is a different job.

## 7. Where this catalogue collides with the floors

**(a) Reduced motion is the first collision, and the largest.** More than half of the
catalogue does not read the user's preference at all, and the components that do read it
have not been shown to make the reduced variant equivalent. CDIO-07 is explicit that
equivalent means the information and the state change still arrive by a non-motion
channel, not that the animation is shortened. For a purely ambient background the
equivalent is usually a static frame of the same field, which is cheap. For a text
animation that reveals a headline letter by letter, the equivalent is the headline,
present and readable at once. For a widget whose content changes over time (the split-flap
display, the flight card, the clock) the equivalent must still deliver the changing value.

**(b) Pointer-only content is the second.** A fifth of the catalogue responds to the
pointer and has no keyboard path. For an ambient effect that only tilts or ripples under
the cursor this is harmless, because nothing is withheld from a user without a mouse. It
becomes a failure the moment the pointer reveals content: an image that appears only on
hover, a label that appears only when the cursor approaches. The entry flags the pattern;
the reviewer decides which case applies by asking what the hover reveals.

**(c) Cost is the third.** A per-frame WebGL or canvas renderer without an off-screen pause
keeps working after the user has scrolled past it, and it competes for the same main
thread as the page's real interactions. CDIO-07 sec. 5 says a perceived-premium gain bought
with interaction latency is a net loss and is not arbitrable. CDIO-07 sec. 12 adds that the
motion budget is aggregate: two such components on one landing page are not two medium
budgets, they are one high budget.

**(d) Silent canvases are the fourth.** A canvas is opaque to assistive technology. If it is
decorative it should be hidden from the accessibility tree; if it carries the product's
name or a headline drawn as particles, that text must exist as text. Eleven components do
neither in their own source.

## 8. Review criteria (what CDIO-11 can fail)

`cdio-reviewer` applies these when a surface under review contains a component copied from
this library, identified by its slug, its vendored file name or its upstream import path.
Each criterion reports under an existing dimension, so the CDIO-05 score formula is
unchanged. Severity follows CDIO-05 sec. 3.

**`cmp-contract-cleared`** (conformance, reported with the experience contract; withholds
done, never moves the score — sec. 13). The surface's declared CDIO-07
contract meets the component's minimum in its entry, and the surface kind is one the entry
applies to. Observed-value form: "liquid chrome (needs high/high) on a landing page whose
contract declares moderate/medium". With no contract declared, this criterion is
unassessed, never failed.

**`cmp-reduced-motion-equivalent`** (dimension `ux`, severity critical). Under
`prefers-reduced-motion: reduce`, the component delivers the same information and state
change without movement. Observed-value form: "kinetic text reveal under reduced motion:
headline invisible for 1.2 s, then appears" or "matrix rain under reduced motion: still
animating". This is the CDIO-07 floor and is critical for the same reason there.

**`cmp-pointer-not-sole-channel`** (dimension `ux`, severity major). Nothing the component
reveals on hover or cursor proximity is unavailable to keyboard and touch users. Observed
form: "image trail: project thumbnails appear only under the cursor; no list of the same
projects exists on the page". An ambient tilt or ripple that reveals nothing passes.

**`cmp-offscreen-paused`** (dimension `visual`, severity major for per-frame renderers,
minor otherwise). The component stops per-frame work when it is out of the viewport or the
page is hidden. Observed form: "dither prism hero: 60 frames per second recorded with the
hero scrolled out of view".

**`cmp-canvas-accounted`** (dimension `visual`, severity major when the canvas carries
text, minor when decorative). A canvas is either hidden from assistive technology or its
content exists as text. Observed form: "particle typography draws the product name; the
accessibility tree has no heading with that name".

**`cmp-not-a-state-cue`** (dimension `trust`, severity major). No component from this
library is used as the acknowledgement, progress or success cue of a real operation.
Observed form: "the flight status card's animated 'landed' state reused as the order
confirmation". This is CDIO-07 sec. 12's rule that marketing motion never stands in for a
transactional state, applied to a catalogue whose widgets look like real status displays.

**`cmp-one-expressive-moment`** (dimension `visual`, severity minor). At most one
per-frame component from this library runs at the same time in one viewport. Observed
form: "aurora flow hero and matrix rain section both running at the fold".

**`cmp-licence-carried`** (dimension `trust`, severity minor). The MIT notice travels with
the copied source. Observed form: "aurora-flow.tsx copied into the project with no
licence header and no third-party notice".

## 9. What was deliberately not absorbed

- **Preview videos and the showroom order.** Upstream ranks its "strongest video-preview
  pieces" first. A preview is the component at its best on the author's machine; it is the
  wrong evidence for a product decision, and CDIO does not rank by it.
- **The install path.** The shadcn command line and the MCP install route are distribution
  mechanisms. A component installed from the live registry is whatever upstream ships that
  day; the vendored copy is pinned, and the entries describe the pinned copy only.
- **Upstream's blocks.** Two pricing blocks and a gradient hero block live outside the
  component package. Pricing is a conversion surface governed by CDIO-04, and absorbing a
  third party's pricing layout as a pattern would have imported a conversion opinion with
  no evidence behind it.
- **The support primitives as standards.** Autocomplete, command, input, tabs and the
  rest are vendored because published components import them. They are not CDIO's form
  controls and are not catalogued.
- **The word "polished".** Upstream's claim about its own components is the author's, and
  each entry quotes the upstream description as the author's text, unverified.
- **A visual ranking.** CDIO does not score which component is most beautiful. A design
  choice between two components that both clear a surface's contract belongs to the
  product's aesthetic family (CDIO-06), not to this catalogue.

## 10. Traps that transfer to any component library

- **A parser that knows one shape drops entries silently.** Upstream writes registry keys
  quoted when they contain a dash and bare otherwise. The first parser knew only the
  quoted form and produced 53 of 54 with no error. The fix was not the regex alone; it was
  the cross-check of the parsed count against a second, independent count of the same
  population. Any discovered catalogue needs that second count.
- **A scanner signal is only as honest as its calibration.** Both calibration errors in
  sec. 4 would have produced confident, wrong entries. Calibrate each signal against the
  real files before trusting it, and phrase every entry as a statement about the file.
- **A green structural check says nothing about the floors.** Every one of the 54 entries
  parses, every one carries a complete motion block, and 31 of them describe components
  that ignore reduced motion. Parsing proves the entry will load.
- **Absorbing a catalogue can flood its consumer.** The advisory hook printed one item per
  applicable pattern. Adding fifty-four patterns would have turned a proportional hint into
  a catalogue dump. Check every consumer of a corpus before multiplying its size.
- **A demo component that looks like a status display will be reused as one.** The flight
  card, the clock, the split-flap board and the music player look like product UI. That is
  exactly why `cmp-not-a-state-cue` exists.

## 11. Evidence, scope and what is still planned

Scope claimed: **a measured, per-component admission rule for the 54 published components
of one library, served through the existing CDIO-07 resolver.** Not claimed: that any of
them is good, that the reduced variants are equivalent, or that the derivation rules are
right for another library without recalibration.

| rung | status | evidence |
|---|---|---|
| local success | reached | 54 of 54 catalogued, 0 parse errors, drift-checked |
| repeated success | not reached | no Owner product has adopted a component from the catalogue yet |
| production reality | not reached | no entry has been checked in a browser; every entry says so |
| adversarial survival | partial | the gate drives the parser, the scanner and the resolver from both poles |
| transfer | not reached | one library absorbed |
| enforcement | gated structurally, judged on behaviour | gate described in sec. 12; criteria in sec. 8 are judged by the reviewer |

A browser lane that drives each component under reduced motion and records whether the
information still arrives is **planned**, not built. It becomes worth building when the
first Owner product adopts a component, because only then is there a surface to drive and a
contract to judge against.

## 12. Common false positives (what CDIO-11 does not flag)

- **A component with no reduced-motion signal whose product supplies one.** A product that
  wraps its tree in a reduced-motion configuration, or that removes the component under the
  media query in its own stylesheet, satisfies the floor. Judge the rendered surface, not
  the vendored file.
- **Hover effects that reveal nothing.** A ripple, a tilt or a magnetic pull is not content.
- **A canvas behind an element that already carries the text.** If the heading exists as
  text and the canvas only decorates it, the canvas being unnamed is not a finding beyond
  the minor decorative case.
- **A modified copy.** Once a product has changed a component, its entry describes the
  ancestor. Review the copy.
- **Absence of every component.** A surface that uses none of this library is never
  assessed under CDIO-11.

## 13. Contract with the review pipeline

`cdio-reviewer` applies sec. 8 whenever a surface contains a component from this library.
The floor and cost criteria run under CDIO-05 Lens 3, which carries the mechanical
accessibility checks; their findings report under the existing `ux`, `visual` and `trust`
dimensions, so the score formula is unchanged, and `cmp-reduced-motion-equivalent` is
critical because the floor it restates is. `cmp-contract-cleared` is the exception: it is
a conformance question, so it is reported with the reviewer's experience-contract lens,
withholds done when it fails, and never moves the score (CDIO-07, "three separate
answers"). `cdio-core`
routes a request that names componentry, a component slug from this library, or "an
animated hero background / text animation from a component library" here first, and to
CDIO-07 when the question is how much motion a surface should carry at all. The gate is
`tools/test_cdio_componentry.py` (V-CMP-*): it fails if the vendored source no longer
matches the catalogue, if any generated entry drifts, if the population falls below 54, if
the resolver stops serving or withholding these entries correctly, or if the advisory line
stops summarising the family.
