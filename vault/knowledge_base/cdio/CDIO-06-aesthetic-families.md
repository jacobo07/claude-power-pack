---
id: CDIO-06
name: Aesthetic Families — the Generative Axis
type: dataset
domain: cdio
status: sealed
governs: [design-md, design_gate]
governed_by: CDIO-00
source: github.com/rohitg00/awesome-claude-design (absorbed 2026-07-12) + Anthropic Anti-Slop Kit
---

# CDIO-06 — Aesthetic Families (the Generative Axis)

CDIO-00 through CDIO-05 are **evaluative**: they judge a surface against thresholds
(does it contrast, does it hierarchize, does it convert). None of them answers the
question that comes *first*: **which aesthetic family should this product inhabit,
and why?** CDIO-06 is that missing axis. It is the vocabulary a PP agent commits to
*before* writing a single token, and the vocabulary the design gate reads to decide
whether a font or a palette was *chosen* or merely *defaulted into*.

The distinction this dataset exists to enforce:

> A default is not slop. A default **without a declared intent** is slop.

Four of the ten families below use a default-tier stack deliberately, as a considered
choice with a stated reason. The Power Pack's own token template used Inter with no
reason at all. The first is design; the second is the absence of design. The gate
(`modules/cdio/scorer.py`, `check_font_stack`) draws exactly this line: a default-tier
font passes only when the declared family sanctions it.

## 1. The ten families

Each family is a *commitment*: a palette, a type strategy, a context where it earns
its keep, and real products that prove it works. A DESIGN.md declares exactly one
family in its `aesthetic_family` field. That declaration is load-bearing — it is what
`check_family_declared` verifies and what `check_font_stack` consults.

### F1 — Editorial Minimalism
- **Palette:** `#fff` / `#0f0f14` / `#5e6ad2`
- **Typography:** Inter, Söhne (narrow grotesque), generous line-height
- **Use when:** reading-heavy surfaces, pricing pages, documentation
- **Proof:** Linear, Stripe, Vercel
- **Sanctions default-tier fonts:** yes (Inter, deliberately — the restraint *is* the point)
- **Zero-accent variant (added 2026-10-01):** near-black ink is the only state colour —
  progress, selection and the primary action share it, and no hue competes. Distilled from
  the InfinityOps Focused Monochrome UI, where it is scoped to focused decision surfaces
  and the rest of the product keeps its own family. A variant, not an eleventh family: it
  changes one F1 commitment (the accent) and keeps every other. Its behaviour, criteria and
  measured floor collisions live in CDIO-09.

### F2 — Terminal-Core
- **Palette:** `#000` / `#fff` / no accent (or phosphor-green, amber)
- **Typography:** monospace everywhere
- **Use when:** CLI metaphors, developer tools
- **Proof:** Ollama, Warp, Raycast
- **Sanctions default-tier fonts:** no (monospace is the commitment)

### F3 — Warm Editorial
- **Palette:** `#f4f3ee` / `#c96442` / `#191817` (cream, terracotta, clay)
- **Typography:** serif body, approachable
- **Use when:** humanized prosumer products
- **Proof:** Claude/Anthropic, Notion, Resend
- **Sanctions default-tier fonts:** no (a serif body is the commitment)

### F4 — Data-Dense Pro
- **Palette:** `#181818` / `#faff69` / magenta (saturated categorical)
- **Typography:** Inter tabular, fixed-width numerals
- **Use when:** charts are the hero; scan-heavy dashboards
- **Proof:** ClickHouse, PostHog, MongoDB
- **Sanctions default-tier fonts:** yes (Inter, for its tabular numerals specifically)

### F5 — Cinematic Dark
- **Palette:** `#000` / saturated magenta + cyan (film-grade gradients)
- **Typography:** oversized, custom grotesque
- **Use when:** AI products, creator tools, motion-forward surfaces
- **Proof:** RunwayML, NVIDIA, BMW, Ferrari
- **Sanctions default-tier fonts:** no

### F6 — Playful Color
- **Palette:** `#0acf83` / `#f24e1e` / `#a259ff` (high-saturation multi-hue)
- **Typography:** Inter + Whyte, rounded corners
- **Use when:** consumer-friendly products with illustrated accents
- **Proof:** Figma, Duolingo, Toss
- **Sanctions default-tier fonts:** yes (Inter, paired against a characterful display face)

### F7 — Glass / Soft-Futurism
- **Palette:** `#fff` / radial pastel (frosted blur, translucency)
- **Typography:** SF Pro or an editorial serif
- **Use when:** premium consumer, Apple-adjacent
- **Proof:** Apple, Arc Browser, Spotify
- **Sanctions default-tier fonts:** no

### F8 — Neon Brutalist
- **Palette:** `#ff6600` / `#000` / `#fff` (hard edges, deliberate ugliness)
- **Typography:** type mixing, oversized numerals
- **Use when:** statement pieces that require courage
- **Proof:** The Verge, Pitchfork, PlayStation
- **Sanctions default-tier fonts:** no

### F9 — Cult / Indie
- **Character:** research-publication, crypto-minimal, film-archive aesthetics
- **Use when:** differentiation is itself the primary goal
- **Proof:** A24, Criterion, Granola, Superhuman
- **Sanctions default-tier fonts:** no

### F10 — Calm Utility (Minimal iOS / Clean SaaS)
- **Palette:** opaque `#fff`–`#f7f8fa` ground / near-black ink (`#141a2e`-class) / at most
  one saturated accent, carried by a small fraction of the surface
- **Typography:** the platform's own sans at a short scale — four levels, not nine
- **Use when:** mobile-first consumer utilities where the user has one task per screen:
  weather, habit, transit, personal finance, scheduling, lightweight consumer SaaS
- **Proof:** the CDIO-06 reference bank (sec. 9), distilled 2026-09-14
- **Sanctions default-tier fonts:** yes — and this is the family's most abusable licence,
  see below

F10 is the family the other nine kept almost-covering. F7 Glass is Apple-adjacent but its
defining commitment is *translucency*; F1 Editorial Minimalism is restraint but for
read-heavy web. F10 is neither: **opaque flat surfaces, scan-heavy, one task per screen,
thumb-operated.** No existing family's proof set contained a bottom-tab mobile app, which
is what made the gap real rather than a naming preference.

**The font sanction is deliberate and narrow.** F10 defers to the platform's own text
rendering because deference to the platform *is* the commitment — the same logic that lets
F1 keep Inter. It is not a licence to skip the type decision: the short scale, the weight
discipline and the ink colour are still choices, and a surface that declared F10 purely to
escape `check_font_stack` has declared the wrong family. The mismatch in sec. 6 is the
check on that.

#### Invariants — break one and it is not this family
- **Surfaces are opaque.** Contrast must be computable from the surface's own tokens. A
  frosted or gradient-backed panel makes it depend on what sits behind, which is F7's
  problem to own, not this one's.
- **At most one hue carries emphasis.** Two accents is not richness; it is the absence of
  a hierarchy decision.
- **The accent is scarce.** It earns its emphasis from how little of the surface it
  occupies. An interface that is mostly accent has no accent.
- **Exactly one dominant action per screen.** Scarcity of emphasis is the whole mechanism.
- **One radius family**, ordered with surface size — larger surfaces may carry a larger
  radius, never the reverse.
- **Depth is information.** Elevation says "this layer is above that one" or "this is
  interactive". Decorative shadow is noise wearing depth's clothes.

#### Strong preferences — adapt to brand and platform
White or near-white ground; a large hero surface carrying the screen's primary fact;
bottom tab navigation on mobile (on desktop the same philosophy becomes a restrained
sidebar or top nav with few persistent destinations — never a transplanted tab bar);
generous outer gutters; metadata quieter than content.

#### Optional motifs — present in the references, required by nothing
A **blue** accent specifically; a centred floating action; a gradient on the hero surface;
rounded photo cards; pill-shaped status chips. Every one of these is a choice the
reference bank happened to make. None is the family.

#### Anti-patterns
Card soup — a rounded rectangle around every heading, metric and row, so that containment
stops meaning grouping. Several equally-weighted accent buttons competing for one
decision. Accent gradient on every surface rather than on the one that leads. Whitespace
standing in for functionality that was never built. Slot names surviving into the shipped
screen — a tile labelled `Primary`, a venue labelled `Place Name` — which is the reference
bank's own most common defect and is a Contract of Reality breach, not a style note.

## 2. The picker (three questions, one family)

Answer in order. The first two narrow; the third can override into F8/F9; the fourth
fires only where the first three left a real choice.

1. **Is the product read-heavy or scan-heavy?**
   - Read → F1 Editorial Minimalism, or F3 Warm Editorial
   - Scan → F4 Data-Dense Pro, F2 Terminal-Core, or F10 Calm Utility
2. **Who is the user?**
   - Developer → F2 or F4
   - Designer / creator → F5 or F6
   - Consumer → F7, F6, or F10
   - Prosumer → F3
3. **Does the brand need to feel courageous?**
   - Yes → F8 Neon Brutalist, or F9 Cult/Indie
   - No → stay within F1–F7, F10
4. **What does the user hold, and how many decisions does one screen carry?**
   - A phone, one decision per screen → **F10 Calm Utility**
   - A phone, premium/immersive, translucency is part of the brand → F7
   - A desktop, many simultaneous decisions → F4
   - Form factor does not discriminate here → the sec. 2 answer above stands

Question 4 was added 2026-09-14 and is the reason F10 exists. The first three questions
route on *content* and *audience* and never on **form factor**, so a consumer mobile
utility and a premium desktop consumer surface arrived at the same pair — and the mobile
answer was always slightly wrong. A picker that cannot ask what the user is holding
cannot choose between a tab bar and a sidebar, and that difference is structural rather
than stylistic.

Do not read question 4 as "mobile means F10". A phone running a dense trading terminal is
still F4; a phone running a film-archive brand is still F9. Question 4 discriminates only
when questions 1–3 have already landed on the calm, consumer, scan-heavy branch.

A family reached by this tree is a *hypothesis*, not a verdict: it must still clear
the CDIO-01..04 thresholds. A beautiful family that fails legibility is a defect
(CDIO-00 sec. 2). The picker chooses the direction; the scorer decides whether the
execution earned it.

## 3. Remix recipes and token arbitration

A remix is two families in tension. The tension is the product — but only if the
conflicts are *arbitrated*, not averaged. Averaging two palettes yields mud.

The eight canonical remixes:

| Remix | Result |
|---|---|
| Linear × Claude | Linear typography + Claude terracotta + warm neutrals → editorial SaaS with a soul |
| Warp × Sentry | Warp mono grid + Sentry lilac→purple → developer dashboard without coldness |
| Stripe × A24 | Stripe layout discipline + A24 poster boldness → fintech pitch with personality |
| Vercel × Pitchfork | Vercel grayscale + Pitchfork orange → editorial docs site |
| Granola × Criterion | Granola warmth + Criterion editorial rigor → premium note app with gravitas |
| Ollama × ElevenLabs | Terminal mono + cinematic dark gradients → CLI landing page |
| Notion × Duolingo | Notion neutrals + Duolingo greens → friendly education SaaS |
| Mercury × Linear | Mercury cream + indigo + Linear surgical density → fintech dashboard, editorial warmth |

### Arbitration rules (which family wins a conflicting token)

Every remix names a **base** family and a **voice** family. The base is the family
that governs the surface the user must *operate*; the voice is the family that gives
it character. When a token conflicts:

1. **Structure goes to the base.** Spacing scale, grid, density, nesting depth, and
   component geometry are the base family's, without exception. Structure is where
   usability lives, and a remixed structure is an unusable structure.
2. **Accent goes to the voice.** Exactly one accent hue survives the remix, and it
   comes from the voice family. Two accents is not a remix; it is indecision.
3. **Body type goes to the base; display type goes to the voice.** The reader spends
   their attention on the body — it inherits the family optimized for reading. The
   headline is where the voice is allowed to be loud.
4. **Neutrals go to the voice.** Neutrals carry temperature (cream versus slate), and
   temperature is character. This is the rule that makes "Linear × Claude" read as
   warm rather than as Linear-with-an-orange-button.
5. **Accessibility floors are not arbitrable.** Contrast, tap target, and mobile body
   size are CDIO-00 floors. A remix that breaks a floor is rejected outright — no
   family, base or voice, can trade an accessibility floor for character.

Rule 5 is the one that makes the other four safe. Without it, "deliberate ugliness"
(F8) becomes an excuse for 3:1 body contrast.

## 4. The Anti-Slop Kit (Anthropic; verbatim intent)

**NEVER:**
- Generic AI-generated aesthetics
- Overused fonts (Inter, Roboto, Arial) *as defaults without intent*
- Clichéd gradients — purple on white or dark, teal accents everywhere
- Predictable cookie-cutter layouts
- Stacked padding with no semantic purpose

**ALWAYS:**
- Fonts chosen for the brand story, not inherited from a framework
- Colors grounded in the product's narrative
- Animation used for effect and micro-interaction
- Context-specific character in every component
- Semantic nesting, capped at two levels

### Default fingerprints (the tells, and their counters)

These are the specific artifacts that mark an interface as machine-defaulted. Each
is a detectable symptom, in the CDIO tradition of naming mediocrity by measurement
rather than by vibe (CDIO-00 sec. 3).

| Fingerprint | Counter |
|---|---|
| Teal `#16d5e6` accent everywhere | Declare a brand-specific accent in DESIGN.md first |
| Blinking status dot, top-right of the nav | Brief explicitly: no animated status indicators |
| Container soup — 24/24/24 padding stacking | Cap nesting depth; use semantic spacing |
| Default serif headline (Tiempos-adjacent) | State an explicit weight and tracking, not a vibe |
| Left accent bar on every card | Reserve it for exactly one semantic role |
| Three-column feature grid | Use a marquee, alternating rows, or a single column |
| Default icon-library stack | Commit to one icon family, or go type-only |
| Hero that ignores the DESIGN.md tokens | Regenerate constrained to `--bg`, `--accent`, `--text` |

## 5. Where each family collides with the CDIO floors

A family is a set of commitments, and some of those commitments pull directly against
the accessibility and hierarchy floors that CDIO-00 declares non-negotiable. Naming
the collision in advance is what stops a designer from discovering it as a BLOCK at
the end. Each family below carries its characteristic failure — the specific way that
executing it *well* still lands you outside a floor if you are not deliberate.

- **F1 Editorial Minimalism** — its restraint tempts a low-contrast grey-on-white body
  (the "timid palette" symptom). Restraint is about *quantity* of elements, never about
  contrast of text. Body copy still clears 4.5:1. The zero-accent variant meets a second
  collision sooner: with no hue to separate a control from its ground, the resting borders
  and radio rings that identify controls drift to whisper grey and fall under the 3:1
  non-text floor (measured 1.23–1.51:1 on the distilled exemplar, then fixed; CDIO-09 sec. 4).
- **F2 Terminal-Core** — monospace at a small size wrecks the line-measure ceiling: a
  mono face at 14px in a full-width container routinely exceeds 100 characters per
  line, well past the 75-character readability ceiling. Constrain the measure, or the
  aesthetic is bought with the reader's comprehension.
- **F3 Warm Editorial** — a serif body at a low weight on cream can dip under 4.5:1
  because the cream ground raises the floor's numerator. Warmth is not an excuse for a
  washed-out body; darken the ink, not the intent.
- **F4 Data-Dense Pro** — density is its purpose, so it collides with the tap-target
  floor first. A 32px row in a dense table is still an accessibility failure on touch.
  Density belongs to information, not to hit areas.
- **F5 Cinematic Dark** — oversized type plus film-grade gradients invites text laid
  over a gradient, where contrast varies across the glyph run. Contrast must hold at
  the *worst* point of the gradient, not the average.
- **F6 Playful Color** — high-saturation multi-hue palettes routinely produce accents
  that are vivid but low-contrast against white (saturated yellow-greens especially).
  Vividness and contrast are independent axes; check the ratio, do not trust the eye.
- **F7 Glass / Soft-Futurism** — translucency makes contrast *non-deterministic*: the
  effective background depends on what is behind the panel. A frosted surface must
  guarantee the floor against the worst-case backdrop it can ever sit on, not against
  the mockup's backdrop.
- **F8 Neon Brutalist** — "deliberate ugliness" is the single most abused licence in
  this dataset. It licenses hard edges, type mixing, and clashing hues. It does **not**
  licence 3:1 body text. CDIO-06 sec. 3 rule 5 exists primarily to hold this line.
- **F9 Cult / Indie** — differentiation as a goal tends to produce novel navigation,
  which collides with the Flow dimension (CDIO-00 sec. 2.5). Being memorable and being
  operable are not in tension unless you let them be.
- **F10 Calm Utility** — two collisions, and the first is the family's signature move.
  **(a) The accent hero that cannot carry its own text.** F10's characteristic gesture is
  the screen's primary fact set in white on a large surface filled with the one saturated
  accent. Whether that clears 4.5:1 is decided entirely by the accent's luminance, and the
  friendly blues this family reaches for sit right on the line: white text stops clearing
  the floor somewhere around `#3b82f6`, and every blue lighter than that fails while
  looking perfectly pleasant. Choose the accent against the contrast it must carry *in the
  hero*, not against how it looks as a button, and darken the accent rather than greying
  the text. **(b) Quiet metadata dropping under the floor.** Restraint governs the
  quantity of elements, never the contrast of text — the trap F1 also carries, but F10
  meets it sooner because its whole vocabulary is secondary labels: timestamps, distances,
  unit suffixes, "see all" affordances. A label being unimportant is not a licence for it
  to be unreadable. If it may not be read, delete it.

## 6. Family mismatch is a structural defect, not a taste dispute

Choosing the wrong family is not a stylistic misstep that a later component tweak can
absorb. The family governs type, color, density, and motion simultaneously, so a wrong
family produces *systematic* incoherence — every component is individually defensible
and the whole is incoherent. This is why the picker runs before the tokens, and why the
gate refuses to review a surface that has not declared one.

Three mismatches recur often enough to name:

- **Calm Utility (F10) on a product whose task is comparison.** F10 buys its calm by
  putting one fact per screen and paying in density. A user comparing eleven rows, or
  reading a column against another column, needs them simultaneously present — and F10's
  answer is to give each its own generous surface and make the user scroll. The symptom is
  a product where every individual screen reviews well and the *task* takes nine taps.
  This is also the shape of the family's font licence being abused: F10 declared on a
  desktop data-dense surface reads, from the gate's side, as a family that sanctions a
  default font stack — so the wrong declaration buys a pass on the very check that would
  have asked whether the type was chosen. F4 is the family; density is not a failure of
  restraint.
- **Terminal-Core (F2) on a consumer product.** The mono grid signals "you are expected
  to already know what this does". Consumers read that as coldness, and no amount of
  friendly copy inside a mono grid undoes it — the type *is* the message. The symptom
  is a product whose onboarding keeps getting rewritten and never gets warmer.
- **Playful Color (F6) on a technical dashboard.** High-saturation multi-hue accents
  compete with the categorical colors the data itself needs. When the chrome and the
  data both shout in saturated hues, the chart loses its categorical channel — the
  design has consumed the very signal the product exists to show.

The general form: a family that fights the user's *task* will lose, and the loss shows
up as a product that is endlessly "polished" without ever feeling right. Fix the
family, and most of the component-level debt resolves itself.

## 7. What this gate cannot see (honest limits)

`design_gate.py` reads a DESIGN.md. It therefore knows what a project *declared*, and
knows nothing about what it *rendered*. Three consequences, stated plainly so no one
mistakes an APPROVE here for a design review:

1. **A passing DESIGN.md does not mean a passing surface.** The most common fingerprint
   in CDIO-06 sec. 4 is a hero that ignores its own tokens. The gate cannot detect this;
   only a rendered-pixel review can. A declared value is a hypothesis until it is
   validated against rendered pixels.
2. **The gate checks tokens, not composition.** Hierarchy, rhythm, depth, and grid
   discipline are judgments against CDIO-01..04, made by the cdio-reviewer agent with an
   observed value per finding. The gate is a floor beneath that review, not a substitute
   for it.
3. **APPROVE means "no slop detected in the declared system".** It is a necessary
   condition for shipping a visual surface, never a sufficient one. The sufficient
   condition remains PR-CDIO-REVIEW-GATE-001: a Design Quality Score of at least 80 with
   zero critical issues, on the surface as rendered.

Stating the limit is what keeps the gate honest. A gate that oversells its coverage
becomes a rubber stamp, and a rubber stamp is worse than no gate at all — it launders a
bad surface with the authority of a green check.

## 8. Contract with the gate

This dataset is not advisory prose. Three of its structures are read by code:

- `aesthetic_family` — a required field in the DESIGN.md front-matter. Absent →
  `check_family_declared` fails. This is what makes
  `PR-DESIGN-FAMILY-BEFORE-BUILD-001` enforceable rather than aspirational.
- **Sanctions default-tier fonts** — the per-family flag above. `check_font_stack`
  fails a default-tier font stack *only* when the declared family does not sanction
  it, so F1/F4/F6/F10 keep their system stacks and everyone else must earn their typeface.
- **Clichéd gradients** — `check_palette_cliche` fails a purple-family gradient over
  a white or black ground, and flags the teal `#16d5e6` fingerprint.

A rule that no gate can refuse is a preference. These three are refusable, and the
gate has been observed refusing them (`tools/test_cdio.py`).

## 9. The F10 reference bank — evidence, and what it refused to support

F10 was distilled on 2026-09-14 from a bank of seven supplied images. The distillation is
recorded here rather than summarised, because **what the bank refused to support shaped
the family more than what it confirmed.**

The brief described the bank as three mobile weather screens: white canvas, vivid blue
accent, large rounded hero cards, bottom navigation. Measured, the bank was not that.

| source | classification |
|---|---|
| an iOS screen-kit sheet, a travel app, a home-automation kit | **exemplar** — the described family |
| a fourth image | **duplicate** — the same home-automation kit, re-rendered as a marketplace advert |
| a dark neon-mint VPN concept, neumorphic dial over a world map | **contrast case** — competent, and outside F10 entirely |
| a monochrome iOS home screen, light and dark | **contrast case** — minimal with *no* accent hue |
| a monochrome line-art habit tracker | **contrast case** — minimal with *no* accent hue |

Six distinct sources, not seven. Three exemplars, three outside the family, and none of
them a weather app.

**What the bank refused to support.** Had the family been written from the brief's prose,
"a vivid accent, scarce against white" would have been an invariant — and *half the
supplied evidence would have violated it*. The two monochrome references are arguably the
most minimal artefacts in the bank and carry no accent at all. So accent *hue* dropped to
an optional motif and accent *scarcity* survived as the invariant, because scarcity is the
mechanism and blue was only ever the instance. The dark neumorphic reference did the same
work from the other side: it is the one image the brief's own anti-pattern list would
reject, and it is not bad design — it is a different family, executed competently.

**The exemplars carry their own defects, and this is why a reference is evidence rather
than authority.** The travel app's search field asks *"Where shalud we go?"* — misspelled,
in the shipped asset. The home-automation kit ships tiles reading `Primary`, `Secondary`,
`Tertiary` and a venue card reading `Place Name` / `Location, Country`: slot names that
survived into the screen, presented as product state. Both are marketplace template
assets, which is to say they are instances of the cookie-cutter layout sec. 4 names as a
default fingerprint. **The family's best available exemplars are also carriers of the slop
the family must refuse.** A distillation that copied them would have encoded both.

**What was deliberately not universalised**: the blue; the centred floating action; the
gradient hero; the pill status chips; the photo-card treatment; the tab-bar item count.
Each is present in a majority of the exemplars and none of them is a principle. The test
is whether the trait survives a change of brand, platform or domain — and every item on
that list is an artefact of three template kits sold in the same year.
