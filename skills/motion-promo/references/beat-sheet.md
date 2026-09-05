# Writing a beat sheet

This decides whether the film is good. The renderer is the same either way.

A beat sheet is 4–7 rows. Each row is one idea, one shot, one duration, and
the words that will be on screen. Nothing else.

## The cut

**Five ideas, not twelve.** A 20-second film holds about five beats. If the
material has twelve points, five survive. Choosing which five is the work —
do not let the count decide it by taking the first five in order.

**Lead with the sharpest line.** The first beat is the one people actually
watch. Whatever in their material is most concrete, most surprising, or most
specific goes first. Not the company name. Not "introducing".

**Five words a line.** Longer lines shrink to fit and stop reading as a
statement. If a line will not go under six words, it is two beats or it is
the wrong line.

**Kill the adjectives.** "Powerful, intuitive, best-in-class platform" gives
nothing to animate — there is no picture in it and no rhythm. "Deploy in
nine seconds" gives both.

**Numbers are gold.** A concrete figure gets its own shot: the figure slams
in at 1.34× and settles, with a bloom swell and a ring knocked out of the
frame. `"40% fewer meetings"` will beat any adjective in the language. Put
the figure in `value` and the unit in `text`, so they get separate type.

**Write for the ear.** Say it the way you would say it to a friend who
asked what the product does.

## Weak and strong, from the same product

> **Weak** — Meridian is a comprehensive, enterprise-grade scheduling
> solution that leverages intelligent algorithms to optimise calendar
> management across your organisation.

One sentence, no beats in it. Nothing to put on screen, no number, no verb
anyone does.

> **Strong** — Meridian finds meeting times nobody hates. It reads every
> calendar in your team and picks the slot that costs the least. Cut 40% of
> your meetings. Free under ten people.

Four clean beats, already almost in order:

| # | Shot | Sec | On screen |
|---|---|---|---|
| 1 | `grid-sweep` | 2.6 | Meetings nobody hates |
| 2 | `type-line` | 3.2 | Reads every calendar |
| 3 | `number-slam` | 2.8 | **40%** / fewer meetings |
| 4 | `ring-pulse` | 2.4 | Free under ten people |
| 5 | `logo-lockup` | 3.0 | MERIDIAN / meridian.app |

## Shape

An open, a middle that earns it, a close.

- **Open** (1 beat) — the claim. `grid-sweep`, `title` or `shockwave`.
- **Middle** (2–4 beats) — why it is true. Capabilities as `type-line`,
  figures as `number-slam`, integrations as `glass-tiles`, reach as `orbit`,
  growth as `bar-rise`.
- **Close** (1 beat) — `logo-lockup`. Always. It is where the name goes and
  where the palette arrives at its warm end.

Do not put the product name in beat one *and* beat five. Once, at the close.

## Timing

| | |
|---|---|
| Under 1.2s | reads as a flicker; the eye has not landed before it cuts |
| 2.4–3.2s | a line of text, read comfortably, with a beat to spare |
| 3.0–3.6s | `type-line`, which needs time to actually type — 26 chars/sec |
| Over 6s | a single idea starts to sit |

Total should match what they asked for, within about half a second. Spend
the extra on the open and the close, not the middle.

`new_film.py` warns on every one of these. Read the warnings.

## Show it before you build it

Put the table in the reply and say that this is the moment to change the
story. A beat sheet costs seconds to redo. A render costs ten minutes.

## From a website

Fetch the page and pull out, in this order: the one-line claim in the hero,
any hard number anywhere on the page, the integration logos, the pricing
line. That is usually four of your five beats already, in the order they
should run.

Ignore the testimonials and the feature grid — a feature grid is twelve
ideas, and you need five.
