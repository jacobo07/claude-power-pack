# REF-KITCHEN-001 — dqnamo "The Kitchen" (15 interaction studies)

- Source: https://www.dqnamo.com/kitchen and its 15 `/experiments/*` pages.
- Read: 2026-10-08, page text and the visible source panels, one fetch per page (15/15 read).
- Author shown: "dqnamo" (studio interface.london). No license or copyright notice on any page.
- Spec: `vault/specs/cdio-kitchen-absorption.md`.

## Labels

- **OBSERVED**: stated on the page or in its visible source panel.
- **INFERRED**: deduced from observed values (for example a total duration computed from a tick
  and a step cap). The inference is stated.
- **UNKNOWN**: the page does not state it. UNKNOWN is never read as "absent" or "handled".

## License disposition

**Principles only.** The code is publicly visible, but visible is not licensed. Nothing from the
source panels is copied into this repo. The entries restate behaviour, numbers and contracts in
our own words, which is the same disposition `product_demo/recordly-disposition.md` applies to an
AGPL source. Libraries the source imports (motion/react, react-parallax-tilt, Phosphor) are named
so a reader can choose them; none becomes a dependency of Power Pack through this absorption.

## Stack (OBSERVED)

React client components in TSX, `motion/react` for springs and presence, Tailwind-style utilities,
`@phosphor-icons/react`, `react-parallax-tilt` (Ticket only). Next.js is INFERRED from
`/_next/image` paths.

## Per component

| # | Component | OBSERVED (key facts) | UNKNOWN | Absorbed as |
|---|---|---|---|---|
| 1 | Tactile Button | a face, firm edge and compressible depth built in layers; `size` prop; icon `aria-hidden` | press/hover/disabled values, keyboard, reduced motion | VP-027 |
| 2 | Scramble Text | 32 ms tick; reveal capped at 48 steps; grapheme segmentation; whitespace never scrambled; deterministic scramble on first render; animated span `aria-hidden` + `sr-only` polite atomic final text; reduced motion shows the final text | keyboard (not interactive) | VP-022 |
| 3 | Receipt Printer | stage `processing/printing/complete` owned by the parent; stepped feed 20 steps over 1.75 s (default) or smooth; `role=status` polite; output hidden from AT until complete; reduced motion or `animate=false` sets durations to 0 | sound, what triggers Replay | VP-023 |
| 4 | Cassette Audio Player | audio source + title + WebVTT caption track (default English); elapsed/total time readout | play/pause/seek semantics, keyboard, reel motion under reduced motion | VP-027 |
| 5 | Hold to Confirm | 1600 ms linear fill; early release rolls back in 180 ms; pointer drifting >8 px outside cancels; primary button only; Enter/Space hold, key repeat ignored, keyup cancels; blur, lost capture and `disabled` cancel; `aria-busy`; `onConfirm` receives the input mode; resets after 1800 ms; reduced motion = no fill transition | undo window length, modal close timing | VP-019 |
| 6 | Magnetic Drop Zone | window `dragover` only for file drags; 180 px pull radius from the edge; max 10 px offset; spring stiffness 280 / damping 24 / mass 0.65; copy per state (idle / near / over); native button opens the picker; validation errors polite with the file name; Replace / Remove; window `drop`/`dragend` reset; reduced motion zeroes offset and glow | keyboard alternative beyond the native button | VP-020 |
| 7 | Dynamic Button | width animates to a measured label width (spring, no bounce, 0.26 s); text and icon crossfade with 8 px travel in 0.18 s; hidden measuring span + ResizeObserver; `width=full` skips the animation; press scale 0.97 | announcement of label changes | VP-021 |
| 8 | Playing Cards | 5:7 ratio, type scaled from width; corner indices carry rank + suit so court art is `alt=""`; hover thumbs the fan, click or upward flick plays | keyboard path to play a card, reduced motion | VP-027 |
| 9 | Ticket | notched outline via clip-path; dashed tear line `aria-hidden`; tilt max 6 deg, perspective 1100, scale 1.018, 220 ms; tilt enabled only under `(hover: hover) and (pointer: fine) and (prefers-reduced-motion: no-preference)`; `touch-pan-y`; tilt off during SSR; `article` + label | focus behaviour, contrast | VP-026 |
| 10 | Stamp | perforations as a generated polygon clip-path with clamped depth and counts; label omitted when `aria-hidden` | none relevant (static) | VP-026 |
| 11 | Scroll Fade List | each fade's height equals the remaining scroll distance on that side, capped at 76 px; zero at the end and when nothing overflows; overlays ignore the pointer; passive scroll + rAF + ResizeObserver; `ul/li`; stable scrollbar gutter; overscroll contained | keyboard scroll focus | VP-025 |
| 12 | Advanced Model Selector | described as "benchmark informed"; a model picker and a prompt composer | every benchmark value, every source, accessibility | **rejected** |
| 13 | Animated Signature | `pathLength=1`, dash offset 1 to 0, 2.8 s; `role=img` + label; reduced motion collapses to ~1 ms | per-stroke timing | VP-024 |
| 14 | Logo Trace Loader | phases loop / closing outline / fading fill / done; resolves on completion by closing the loop, not by cutting it; width and height stable from the first render; `role=status` + label; reduced motion shows the filled mark and fires done once | default durations | VP-024 |
| 15 | Iridescent Foil | layered decorative spans (`aria-hidden`); scroll progress (element or document) and pointer (clamped 0.08..0.92) written as CSS variables in a rAF-batched passive listener | reduced motion, text contrast over the foil | VP-007 (extended) |

## Rejected: Advanced Model Selector

The page claims the picker is "benchmark informed" and shows no benchmark value and no source.
A picker that recommends on numbers nobody can see is the claim shape that
`generated-content-needs-an-evidence-gate` refuses: an assertive statement with no backing fact.
Its accessibility is also UNKNOWN. Nothing transferable remains once those two are removed. It
can be reopened if a version appears that cites its benchmark sources on the surface.

## Cross-cutting doctrine (OBSERVED in several components, restated)

1. **One ease-out token.** Five components share one ease-out curve, `cubic-bezier(0.23, 1, 0.32, 1)`,
   for short state changes (receipt, hold, drop zone, dynamic button, ticket). A project should have
   one such token, not a curve per component.
2. **Reduced motion means the final state, not a frozen middle.** Scramble shows the final text,
   the loader shows the filled mark and fires `done`, the receipt jumps to its stage. This matches
   CDIO-07's "equivalent, not absent" floor.
3. **Animated text is hidden from assistive technology; the final value is announced once.** The
   scramble keeps a visually hidden, polite, atomic copy of the final string.
4. **Motion never owns state.** The receipt animates a stage its parent decides; the loader resolves
   only on a real completion signal. A purely decorative "processing" animation would fabricate a
   state (CDIO-07 trust collision).
5. **Gate pointer effects by capability, not by device sniffing.** Tilt runs only on hover-capable,
   fine pointers with no reduced-motion preference; touch keeps vertical panning.
6. **Pointer and scroll effects write CSS variables from one passive, rAF-batched listener** and
   clean up on unmount. No per-event React state.
7. **Destructive actions get friction proportional to the cost, then an undo.** The hold is the
   friction; the timed undo is the recovery.

## Evidence level

Every absorbed entry is `research`: verified against a real published source, never built in an
Owner project. One source cannot promote anything beyond `local` even once built
(`V-MGRAM-NO-SINGLE-REF-PROMOTION`).
