---
id: REF-MOTION-001
type: motion-reference-observation
domain: visual-patterns
status: sealed
observed: 2026-09-30
source_file: coltonholland.ai_fc7fbac9b18f4d438a7932f276d3ec9d_1.mp4 (Owner's Downloads; not redistributed)
source_sha256: C8C017BF94243960F5A6E8136E4600210009C72BA191FA1A89087360C5D97287
feeds: [VP-016, VP-017, VP-018]
---

# REF-MOTION-001 — Device-frame product demo on an onboarding page

Epistemic labels: **OBSERVED** (visible in frames), **INFERRED** (follows from
several observations), **HYPOTHESIZED** (one reading of ambiguous frames),
**UNKNOWN** (the instrument cannot resolve it). Nothing here is KNOWN/PROVEN:
there is one reference.

## 1. What the instrument is

- 5.72 s, 720x1280, 30.08 fps, 172 frames, H.264 + AAC (audio not analysed).
- **It is not a screen recording.** It is a handheld phone filming a laptop
  showing a web page, with a hand pointing, a tissue in frame and a baked-in
  social caption. Consequences, all measured:
  - Whole-frame difference (`diff.tsv`) is dominated by camera shake and the
    hand: the three largest spikes (1.66-1.93 s, 3.06-3.72 s) coincide with
    the hand crossing the device, not with app transitions.
  - The variance map (`variance.png`) is bright everywhere; it cannot separate
    a stable shell from changing content in THIS capture. Stability of the
    outer shell is established by reading the crops, not by the variance map.
  - Timing resolution is +/-1 frame (33 ms) at best, worse where motion blur
    or occlusion intervenes. Easing curves are **UNKNOWN**.

Reproduce: `python decompose.py` and `python crop.py` (edit `SRC`); outputs
were recompressed to JPEG for the vault. `crop_a.jpg` / `crop_b.jpg` are the
readable evidence (device region, every 4th frame).

## 2. State sequence (device-region crops)

| # | State (inner app screen) | Window (s) | Label |
|---|---|---|---|
| shell | Landing/onboarding page: brand mark, headline "The first fitness coach in your pocket", primary CTA "Build my plan", secondary "Log in". Identical in every frame | 0 - 5.72 | OBSERVED |
| S1 | Plan overview list | 0 - ~0.30 (clip starts mid-state) | OBSERVED |
| S2 | Meal plan: row of coloured macro chips + Breakfast list | ~0.35 - 1.20 | OBSERVED |
| T2 | Chips smear horizontally while the device chrome and page text stay comparatively sharp; ~100-150 ms | 1.20 - 1.33 | INFERRED: in-screen horizontal slide or blur-crossfade; camera blur cannot be fully excluded |
| S3 | AI Coach chat, empty with input bar | ~1.33 - 1.90 | OBSERVED |
| S4 | Same chat **accumulates**: user bubble ~2.0 s, reply ~2.2 s, second reply ~3.2 s, suggestion chip ~3.7 s | 1.90 - ~4.40 | OBSERVED (hand occludes 1.6-1.9 s) |
| S5 | Nutrition Tracker: calorie ring + macros | ~4.65 - 5.20 | OBSERVED |
| S6 | Photo Analysis: the food photo appears inside the tracker layout (f160, 5.32 s) and is the hero of the next screen by f164 (5.45 s) | 5.30 - 5.72 | HYPOTHESIZED: shared-element expansion |
| loop | Whether S6 wraps to S1, and how | — | UNKNOWN (clip ends in S6) |

Derived rhythm (INFERRED, coarse): transitions ~100-250 ms against holds of
~0.5-2.5 s, i.e. roughly 1:5 to 1:10 transition:hold. The camera drifts and
zooms in over the clip; that is the filmer, not the design.

## 3. Grammar (transferable) vs source detail (not transferable)

Transferable candidates, each a VP entry:

- **VP-016 Stable shell, rotating proof** — the conversion frame (headline +
  CTA) never moves while an embedded device cycles one product capability per
  state, in narrative order (plan -> food -> coach -> tracking -> vision).
- **VP-017 Intra-state progressive build** — within one state the content
  assembles itself (chat messages arriving), which reads as a live product
  rather than a screenshot, and gives each state its own causality.
- **VP-018 Shared-element continuity** — an element present in state N
  becomes the hero of state N+1 instead of the screen being replaced
  (HYPOTHESIZED from two frames; kept at hypothesis level).

Source-specific, deliberately NOT transferred: the phone bezel, the fitness
domain, chip colours, the exact state count, the caption, the laptop framing.

## 4. Defects the reference itself carries

- Auto-advancing content with no visible pause/stop control. For content that
  moves for more than 5 s alongside other content this fails WCAG 2.2.2
  (Pause, Stop, Hide). The grammar entries require the control; copying the
  reference literally would not.
- No observable reduced-motion behaviour (cannot be observed in a capture).

## 5. What would upgrade these entries

A second independent reference exhibiting the same grammar, and a transfer to
a different surface that passes `tools/test_motion_grammar.py` Production
Reality lane. Until then every entry is `evidence_level: local` or
`hypothesis`, and the baseline entry is a candidate only.
