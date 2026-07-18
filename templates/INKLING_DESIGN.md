# INKLING_DESIGN.md — Atmospheric Dark Editorial

> **Reusable aesthetic template for the Claude Power Pack.**
> Aesthetic family: **F7 "Atmospheric Editorial"** (distinct from F4 "Data-Dense Pro").
> Distilled from the Inkling / Thinking Machines Lab landing aesthetic — **principles, not a copy**.
> Read this file in full before building any Inkling surface (`PR-TEMPLATE-INKLING-BEFORE-BUILD-001`).
> The tokens here are the source of truth; do not invent colour or type outside them.

---

## 1. Philosophy & atmosphere

**The governing principle: the screen is a space you are inside, not a page you look at.**

Inkling is *deep* rather than *dark*. A flat `#000` background is an absence; an Inkling
background is a presence — layered, faintly luminous, with the sense of looking through
something. Cosmic and submarine at once: mystery and calm held together. Content floats in
that space with generous room to breathe, and typography — not chrome — carries the hierarchy.

The emotional target is **quiet authority**. Nothing shouts. The restraint *is* the statement.

### Use Inkling when
- The surface is **narrative or presentational**: landing pages, manifestos, long-form reading,
  a product story, a report cover, an onboarding sequence, a magazine-style index.
- The visitor's job is to **absorb**, and you can afford generous negative space.
- The brand moment matters more than task throughput.

### Do NOT use Inkling when
- The surface is an **operations instrument** — dense tables, resource meters, log streams,
  admin queues. Scanning speed and tabular numerals beat atmosphere every time; use a
  data-dense family (e.g. F4) with a neutral grotesk instead.
- The screen must render **hundreds of rows** or be read under time pressure.
- The host app already has a ratified, conflicting design system. **An aesthetic family is an
  app-level decision, not a page-level one.** Introducing Inkling into one screen of an app
  governed by another family fragments the product — get that ratified first
  (see §7 anti-pattern 6).

---

## 2. Colour palette

Near-monochrome, cool-deep, with **exactly one** action colour per screen. Greys carry
temperature — they are never neutral `#808080`.

```css
:root {
  /* --- Background: three layers of depth (never a flat fill) --- */
  --ink-abyss:      #06070A;   /* page base, deepest */
  --ink-base:       #0A0C11;   /* primary content field */
  --ink-surface:    #10131A;   /* card / raised panel */
  --ink-raised:     #161A23;   /* modal, popover, top of stack */

  /* --- Atmosphere: the background "breathes" (see §7 anti-pattern 2) --- */
  --ink-glow-cool:  radial-gradient(120% 80% at 50% -10%, #16202E 0%, transparent 60%);
  --ink-glow-warm:  radial-gradient(90% 60% at 80% 110%, #1E1A16 0%, transparent 55%);
  --ink-noise-opacity: 0.025;  /* grain overlay; never above 0.04 */

  /* --- Text: cream, not white. Warm text on cool dark = the core tension --- */
  --ink-text:       #EDE8DF;   /* primary — cream, NOT #FFFFFF */
  --ink-text-2:     #A6A49C;   /* secondary — warm grey */
  --ink-text-3:     #6C6F76;   /* tertiary/meta — cool grey (temperature shift) */
  --ink-text-off:   #42454B;   /* disabled, and empty-prompt text inside inputs */

  /* --- Accent: ONE per screen. Pick warm OR cool, never both --- */
  --ink-accent:      #D8A657;  /* warm amber (default) */
  --ink-accent-cool: #6BA8B8;  /* cool teal (alternate) */
  --ink-accent-soft: rgba(216, 166, 87, 0.12);  /* wash for active/selected */

  /* --- Borders: thresholds of visibility --- */
  --ink-hairline:  rgba(237, 232, 223, 0.06);  /* separators — barely there */
  --ink-border:    rgba(237, 232, 223, 0.10);  /* card edge */
  --ink-border-hi: rgba(237, 232, 223, 0.18);  /* hover / focus edge */

  /* --- Semantic (status only; exempt from the one-accent rule) --- */
  --ink-ok:   #7FA87F;
  --ink-warn: #C9A227;
  --ink-err:  #B4685E;
}
```

**Rules.** The page background is `--ink-abyss` **plus** at least one glow layer — a flat fill
is a failed Inkling. Cards sit one step up (`--ink-surface`), never lighter than `--ink-raised`.
Text never uses pure `#FFFFFF`. The accent appears on **one** element class per screen (the
primary action) — everything else is text tiers and hairlines.

---

## 3. Typography

Dramatic hierarchy: a high-contrast serif display against a light, quiet sans body.

```css
:root {
  --ink-display: 'Cormorant Garamond', 'Newsreader', Georgia, 'Times New Roman', serif;
  --ink-body:    'Geist Sans', 'Inter', ui-sans-serif, system-ui, sans-serif;
  --ink-mono:    'Geist Mono', 'JetBrains Mono', ui-monospace, SFMono-Regular, monospace;

  /* Scale */
  --ink-t-xs:      11px;
  --ink-t-sm:      12px;
  --ink-t-base:    14px;
  --ink-t-md:      16px;   /* body floor on mobile */
  --ink-t-lg:      18px;
  --ink-t-xl:      24px;
  --ink-t-2xl:     32px;
  --ink-t-display: 44px;   /* clamp to 56px on wide viewports */

  /* Weight */
  --ink-w-light:  300;   /* long-form body */
  --ink-w-normal: 400;
  --ink-w-label:  600;   /* labels, meta, small caps */
  --ink-w-display:700;   /* serif display only */

  /* Letter-spacing — the tell of an editorial system */
  --ink-ls-display: -0.02em;  /* tight: high-contrast serif at large size */
  --ink-ls-body:     0;
  --ink-ls-label:    0.12em;  /* generous: uppercase labels & metadata */
  --ink-ls-mono:     0.05em;  /* keys, IDs, masked values */
}
```

**Rules.**
- **Exactly one serif.** Mixing two serifs is the fastest way to look accidental.
- Display is `--ink-display` at `--ink-t-2xl`+ / `--ink-w-display` / `--ink-ls-display`.
- Long body copy is `--ink-w-light` — lightness is what makes the display feel heavy.
- Labels and metadata are uppercase, `--ink-t-xs`, `--ink-w-label`, `--ink-ls-label`, `--ink-text-3`.
- **Numbers and data are expressive typography**, not chrome: set figures in the display serif
  or in mono with generous tracking; never in default body weight.
- Minimum three distinct roles per screen (display / body / meta) or the hierarchy has failed.
- Any non-system face **must be self-hosted** (woff2, `font-display: swap`). Declaring a font
  you have not shipped renders a silent fallback and voids the design.

---

## 4. Spacing & layout

Base unit **4px**. Inkling reads as expensive because of negative space — when unsure, add room.

```css
:root {
  --ink-s1: 4px;    --ink-s2: 8px;    --ink-s3: 12px;   --ink-s4: 16px;
  --ink-s5: 24px;   --ink-s6: 32px;   --ink-s7: 48px;   --ink-s8: 64px;
  --ink-s9: 96px;   --ink-s10: 128px;

  --ink-card-pad:    var(--ink-s5);   /* 24px; 32px on wide */
  --ink-gap-tight:   var(--ink-s2);
  --ink-gap:         var(--ink-s4);
  --ink-gap-section: var(--ink-s8);   /* between major blocks */
  --ink-measure:     68ch;            /* max reading width */
  --ink-radius:      10px;
  --ink-radius-sm:   6px;
}
```

Section rhythm is `--ink-gap-section` minimum. Text blocks cap at `--ink-measure`. Prefer an
asymmetric or offset column over a dead-centre stack for hero/editorial moments.

---

## 5. Components

**Input** — minimal but tactile. Prefer an underline over a boxed field. The empty-prompt text
inside the field takes `--ink-text-off`.
```css
.ink-input {
  background: transparent;
  border: 0; border-bottom: 1px solid var(--ink-border);
  padding: var(--ink-s3) 0;
  color: var(--ink-text);
  font: var(--ink-w-normal) var(--ink-t-md)/1.4 var(--ink-body);
  transition: border-color .22s ease, background-color .22s ease;
}
.ink-input:hover { border-bottom-color: var(--ink-border-hi); }
/* the accent underline IS the focus signal — a valid visible replacement for the ring */
.ink-input:focus { outline: none; border-bottom-color: var(--ink-accent); }
```

**Button** — three tiers; only `primary` may carry the accent.
```css
.ink-btn { font: var(--ink-w-label) var(--ink-t-base)/1 var(--ink-body);
           letter-spacing: .04em; padding: var(--ink-s3) var(--ink-s5);
           border-radius: var(--ink-radius-sm); transition: all .22s ease; }
.ink-btn--primary   { background: var(--ink-accent); color: var(--ink-abyss); border: 0; }
.ink-btn--primary:hover { filter: brightness(1.08); }
.ink-btn--secondary { background: var(--ink-surface); color: var(--ink-text);
                      border: 1px solid var(--ink-border); }
.ink-btn--ghost     { background: transparent; color: var(--ink-text-2);
                      border: 1px solid var(--ink-border); }
.ink-btn--ghost:hover { color: var(--ink-text); border-color: var(--ink-border-hi); }
```

**Card** — the edge should be *almost* indistinguishable from the field.
```css
.ink-card { background: var(--ink-surface); border: 1px solid var(--ink-border);
            border-radius: var(--ink-radius); padding: var(--ink-card-pad); }
```
No cast shadows — depth comes from the layer stack and the hairline, never `box-shadow`.

**Separator** — the workhorse of Inkling lists.
```css
.ink-sep { height: 1px; background: var(--ink-hairline); border: 0; }
```
A list of hairline-separated rows with typographic rhythm beats a stack of bordered cards.

**Icon** — stroke only, never filled.
`16px` (inline) / `20px` (standalone), `stroke-width: 1.5`, `stroke: currentColor`,
colour `--ink-text-3` at rest → `--ink-text` on hover. Filled icons are reserved for a single
*active* state.

**Badge** — uppercase micro-label.
```css
.ink-badge { font: var(--ink-w-label) var(--ink-t-xs)/1 var(--ink-body);
             letter-spacing: var(--ink-ls-label); text-transform: uppercase;
             color: var(--ink-text-3); padding: var(--ink-s1) var(--ink-s2);
             border: 1px solid var(--ink-hairline); border-radius: var(--ink-radius-sm); }
```

**Mono value field** (keys, IDs, hashes) — treat the string as typography.
```css
.ink-mono { font-family: var(--ink-mono); font-size: var(--ink-t-base);
            letter-spacing: var(--ink-ls-mono); color: var(--ink-text-2); }
```
Mask with the bullet `•` (U+2022), never `*`.

---

## 6. Interaction & state

Contained, never showy. Motion exists to confirm, not to entertain.

- **Hover** — a *subtle illumination*: text `--ink-text-2` → `--ink-text`, border
  `--ink-border` → `--ink-border-hi`, or a ≤4% background lift. Never a jump, scale, or colour flip.
- **Focus** — always visible, always elegant: `outline: 1px solid var(--ink-accent);
  outline-offset: 2px`, or an equivalent explicit accent edge (see `.ink-input:focus`). Never
  remove the ring without a visible replacement. Keyboard focus must be as legible as hover.
- **Active/selected** — `--ink-accent-soft` wash plus an accent hairline; not a solid fill.
- **Disabled** — `opacity: .38`, `cursor: not-allowed`, and **no hue change**. Dimming is the
  only signal; recolouring reads as a new state.
- **Loading** — a slow skeleton pulse between `--ink-surface` and `--ink-raised`, ~1.8s
  ease-in-out. No spinners on editorial surfaces.
- **Timing** — `.22s ease` default; `.4s` for entrances. One orchestrated staggered reveal on
  load beats many scattered micro-interactions.
- **Reduced motion** — honour `@media (prefers-reduced-motion: reduce)`: drop transforms and
  the grain animation, keep opacity/colour transitions.

---

## 7. Inkling anti-patterns (prohibited)

1. **More than one accent per screen.** Two action colours means neither is the action.
   (Semantic status colours are exempt.)
2. **Atmosphere as the feature.** The background is a *layer*, not the design. Stacking
   competing gradients, animated particles, or glows turns context into protagonist and steals
   attention from the content (`T-INKLING-ATMOSPHERIC-OVERDONE-001`). One base + at most two
   glow layers + optional grain ≤0.04. If the background is the most interesting thing on the
   screen, it has failed.
3. **Two serifs.** One display serif, one sans body, one mono. Never a second serif.
4. **Competing background gradients.** Multiple full-bleed gradients fighting for the same
   canvas produce mud, not depth.
5. **Pure `#FFFFFF` text or a flat `#000000` page.** Both collapse the temperature that makes
   Inkling read as a space.
6. **Retro-fitting Inkling onto one screen of an app governed by another aesthetic family.**
   The family is an app-level, ratified decision. A single Inkling page inside a data-dense
   admin fragments the product and violates that app's design source of truth.
7. **Cast shadows for depth.** Depth is the layer stack + hairline. `box-shadow` on cards or
   buttons is out of system.
8. **Decorative iconography at display scale.** The title *is* the presence; a big glyph above
   it is filler.

---

## 8. Done-gate

An Inkling surface ships only when all hold:
- Background = base + ≥1 glow layer (not a flat fill); grain ≤ 0.04.
- Exactly one accent colour on action; status colours excepted.
- Three distinct type roles present (display / body / meta); display is the single serif.
- Every declared font is self-hosted and actually loading (verify rendered, not declared).
- Focus visible on every interactive element; disabled dims without recolouring.
- No `box-shadow` on cards/buttons; separators are `--ink-hairline`.
- Verified by **render, not curl** — screenshot the built surface and look at it (VQ-8).
