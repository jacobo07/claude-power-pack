# Shot library

Ten shots. Each is a pure function of `(ctx, beat, p, hue, rng)` where `p`
runs 0→1 through the beat. All sizes are in `u` = 1% of the frame's short
edge, so every shot composes correctly at 9:16, 1:1 and 16:9 unchanged.

Common fields: `shot`, `dur` (seconds), `text`. Extra fields per shot below.

---

## `title`
The opening claim, or any plain statement that should land big.

`text` (up to 3 words per line, wrapped) · `sub` optional, set in small caps
under a hairline that draws itself in.

Lines stagger in 0.07s apart on ease-out-expo, each rising 3.2u as it
arrives. Use when there is no better picture for the line than the line.

## `type-line`
A capability, typed live. 26 characters per second; each character flashes
near-white and cools to the palette hue over 0.20s; a caret blinks at 2.4Hz
and stops at the end.

`text` only. **Give it 3.0s or more** — at 26 cps, "Reads every calendar" is
0.8s of typing plus the time to read it.

## `number-slam`
A concrete figure. The number enters at 1.34× and settles on ease-out-back,
a bloom swells and decays over 0.34 of the beat, and a ring is knocked out
to 74u.

`value` the figure ("40%", "9s", "3×") · `text` the unit beneath it.

Put the figure in `value`. If you put it in `text` it renders at label size
and the whole point is lost.

## `ring-pulse`
A promise or an offer. Three concentric rings expand to 56u on
ease-out-quint, 0.17 of the beat apart, thinning as they go, with the words
held in the middle.

`text` only. 56u is chosen so a whole ring stays inside a 9:16 frame —
wider and the rings only ever read as stray arcs across the corners.

## `glass-tiles`
Integrations, features, platforms. Dark matte glass tiles, edge-lit, each
lighting 0.10 of the beat after the last, with a stroked glyph inside.

`items` 2–6 of `{"glyph": "..."}` · `text` sits above the grid.

Glyphs: `clock` `check` `bolt` `lock` `spark` `arrow` `grid` `globe`.
Layout: 2 columns up to 4 items, 3 columns above that.

## `shockwave`
Speed, impact, a hard claim. Two waves cross the frame to 95u — the second
trailing at 45% strength, because one wave alone leaves the middle of the
beat empty. The text holds through both.

`text` only.

## `orbit`
Reach, coverage, "everywhere". Seven points of light orbit a dark glass
sphere on a 0.42 tilt, dimming to 30% as they pass behind it. The sphere's
highlight stays under 5% — any brighter and it reads as a grey ball rather
than black glass.

`text` sits below the system.

## `bar-rise`
Growth or comparison. Bars rise on ease-out-expo, 0.07 of the beat apart,
each with a hot cap and a gradient falling to near-black at the base.

`items` as `[{"value": 0.34}, {"value": 0.52}, ...]`, values 0–1 · `text`
above. Four to six bars. It is a gesture at a shape, not a chart — no axes,
no labels, no legend.

## `grid-sweep`
The open. A synthwave floor recedes into black under a horizon glow that
falls off on both sides. Horizontals drift toward the camera; alpha peaks
just past the horizon and fades again at the bottom edge so the floor
recedes rather than stopping at the frame.

`text` above the horizon · `sub` in small caps above that.

The strongest first beat in the set. Costs the most attention, so it earns
its place only at the open.

## `logo-lockup`
The close. Wordmark at 900 weight with wide tracking, a hairline that draws
in, and the domain beneath. The glow breathes on a 1.6π sine across the
beat.

`text` the wordmark (caps read best) · `sub` the domain or the CTA.

Always the last beat. The palette arrives at its warm end here.

---

## Choosing

Pick by what the line *is*. Repeating a shot beats reaching for a wrong one
— a film with two `type-line` beats is fine; a film that uses `bar-rise`
because nothing else was left is not.

| The line is… | Shot |
|---|---|
| a claim | `title` `grid-sweep` `shockwave` |
| a capability | `type-line` |
| a figure | `number-slam` |
| a list | `glass-tiles` |
| a shape or trend | `bar-rise` |
| coverage or reach | `orbit` |
| an offer | `ring-pulse` |
| the name | `logo-lockup` |

## Adding a shot

Add `SHOTS["name"] = (ctx, b, p, hue, rng) => { … }` to the template. Two
rules: size everything in `S.u`, and take colour from `PAL.css(hue, L, C, a)`
rather than a literal — the hue is handed to you already positioned on the
film's arc, and a hardcoded colour breaks the travel.

`new_film.py` reads the shot list out of the template, so a new shot is
accepted by the validator the moment it exists. Nothing to register.
