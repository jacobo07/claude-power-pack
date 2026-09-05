# The visual language

Every film is composed from the same elements, so a set of them reads as a
set. These are constants, not preferences. The numbers below are the ones
in the engine.

## Pure black

`#000000`. Never grey, never a dark wash. The frame ends in a radial
falloff to `rgba(0,0,0,0.72)` at the corners, so the edges go to true black
and everything that glows is the only thing there is.

## Light is the subject

Objects are dark matte glass — fill from `rgba(255,255,255,0.055)` at the
top to `0.012` at the bottom, edge-lit with a 1-pixel stroke at the beat's
hue. What you see is not the object. It is the light coming off and behind
it.

Every luminous element draws with `globalCompositeOperation = "lighter"`.
That is what makes light *add* rather than paint over.

### Bloom

Two octaves, composited additively over the scene:

| Pass | Blur | Alpha |
|---|---|---|
| tight | `0.9u` | 0.52 |
| wide | `2.8u` | 0.34 |

Highlights are isolated by drawing the scene into a quarter-size buffer
twice — the second time with `multiply`, which squares the values so
midtones fall away and only the bright parts survive to be blurred.

Kept deliberately under 0.6 combined. Bloom here lands on an already
glowing scene; past about 0.6 it starts eating the crisp glyph edges.

### Why type stays readable

Text draws in three passes: a wide halo at 26 × 0.34u blur, a tight halo at
8 × 0.34u, then **the core with `shadowBlur = 0`**. Blurring the core is
what turns a wordmark into a white splat — it was doing exactly that until
the core pass was separated out. Halos may run as hot as a shot wants; the
glyphs stay sharp.

## The spectrum travels

Measured OKLCH hues of the anchors:

| | H |
|---|---|
| cyan | 195–220 |
| blue | 264 |
| violet | 290 |
| purple-magenta | 323 |
| magenta | 349 |

The house band is **195 → 350**, a 155° span, traversed linearly across the
whole film. Cool at the open, warm at the close, always.

### Where the brand colour goes

The brand colour is not laid on top of the band. It *is* a point on it, and
the band rotates so the colour lands on it:

- **On the band already** (195–350) → the band is used unchanged, and the
  brand sits wherever it naturally falls. A cyan brand opens the film. A
  violet brand owns the middle. A magenta brand closes it.
- **Green side** (120–195) → the brand becomes the open; the band runs from
  it to +155.
- **Warm side** (350–360, 0–120) → the brand becomes the close; the band
  runs from −155 to it.

The span is 155° in every case, so the travel never flattens or reverses.
`V-MOTION-PALETTE-HERO` checks all of this against the real engine for six
brand hues, including the two edge cases.

Neon is `L≈0.78, C≈0.19`. White-hot centres are `L≈0.99, C≈0.02`.

## One idea per beat

Big and centred. Never a busy composite. Text stays inside 84% of the frame
width and shrinks to fit rather than wrapping past it.

Type is a system sans at 700–900 weight, sized in `u` so it holds at every
ratio. No webfonts: they would have to load before a frame could be
captured, and a missing one would change the film silently.

## Motion

| | |
|---|---|
| Frame rate | 30fps — a 20s film is 600 painted frames |
| Beat entrance | ease-out-expo, roughly 0.3 of the beat |
| Camera | push-in 1.000 → 1.055 across every beat, ease-out-cubic |
| Between beats | **hard cut.** No crossfade, ever |
| Typing | 26 characters/sec, 0.20s cool from white to hue |
| Number slam | 1.34× → 1.0, ease-out-back (c=1.70158) |
| Ring expansion | ease-out-quint, alpha falling with `(1−p)²` |
| Grain | 128px tile, `overlay` at 0.055, panned per frame |

The hard cut is the one that matters most. Crossfades are what make motion
graphics look like a slideshow; the cut is what makes them look cut.

## Determinism

Every pixel is a pure function of the frame index. No `requestAnimationFrame`
accumulation, no unseeded randomness — the per-beat RNG is a mulberry32
seeded from the beat index and shot name, and the grain is seeded from the
frame number.

This is not a stylistic point. It is what lets a headless browser step the
film frame by frame and get the same picture the browser scrubber shows,
and it is what makes a re-render of one changed beat match the frames
around it. `V-MOTION-DETERMINISM` renders a frame, moves away, comes back,
and requires the two PNGs to be byte-identical.
