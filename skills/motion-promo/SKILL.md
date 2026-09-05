---
name: motion-promo
description: Turn a written script, a product description, or a website into a finished promo film — a dark, neon, glass-and-light motion piece in the register of an Apple product reveal crossed with synthwave. Delivers a scrubbable .html player and an H.264 .mp4. Use when someone asks for a promo, launch film, product video, teaser, trailer, sizzle, animated ad, motion graphics piece, "a video for our landing page", "turn this script into a video", "make a 20 second promo, 9:16", or "turn acme.com into a launch film". Do not wait to be named — recognise the request.
origin: MOTION PROMPT Claude (User Guide), absorbed into Claude Power Pack 2026-09-05
---

# Motion Promo

Someone describes a product in plain words. They get back a film.

Two files, every time:

- **`.mp4`** — the finished film, ready to post.
- **`.html`** — the same film as an interactive player. Scrub it frame by
  frame, and edit it later: the whole animation is readable code with the
  timeline and brand settings in one block at the top.

The HTML is not a preview. It is a complete deliverable that plays in any
browser. If only one file can be produced, it is the HTML.

## What you need from them

Exactly two things you cannot decide for them:

| | |
|---|---|
| **Duration** | 15–20s for social · 30s for a launch or site hero · under 12s feels rushed · over 45s needs a real narrative |
| **Ratio** | `9:16` 1080×1920 TikTok/Reels/Shorts · `1:1` 1080×1080 feed/LinkedIn · `16:9` 1920×1080 site hero/YouTube/decks |

If they gave a script, that is the whole brief — start. If they gave a URL,
fetch it and pull the product story out of the page. If they gave neither
duration nor ratio, ask for those two and nothing else.

Never ask them to write a beat sheet. That is your job.

## The four stages

### 1. Write the beat sheet — and show it

Cut their material into **4–7 timed beats**. One idea per beat. Present it
in the reply as a short table (beat · shot · seconds · words on screen)
before building anything, and say plainly that this is the moment to
redirect the story.

The craft of the cut — how to pick which five ideas survive, how to get to
five-word lines, what makes a beat animate well — is in
`references/beat-sheet.md`. Read it before your first cut.

### 2. Build and preview stills

Write the beat sheet as JSON, then:

```bash
python scripts/new_film.py --spec beats.json --out <name>.html
python scripts/contact_sheet.py <name>.html --out <name>_sheet.png
```

`new_film.py` swaps only the FILM block into the engine template — never
hand-write the engine, and never paste it into a reply. It also validates
the spec and warns about beats that are too fast, too wordy, or too many.

Look at the contact sheet yourself before continuing. You are checking
composition and the colour travel, not spelling: one idea per frame, text
inside the safe area, nothing clipped.

### 3. Render

```bash
python scripts/render_film.py <name>.html --out <name>.mp4
```

A 20-second film is roughly 600 individually painted frames. Expect five to
fifteen minutes. That is normal, not stuck — say so, and do not background
a render you are about to report on.

For a fast rough cut while iterating: `--scale 0.5 --preset veryfast`.
To re-check one beat only: `--range 120:210`.

### 4. Hand over both files

Say what they are and what each is for. Name the duration, ratio and
resolution.

## The shot vocabulary

Ten shots. Each does one thing. Pick by what the line *is*, not by variety
— repeating a shot is better than reaching for a wrong one.

| Shot | Use it for |
|---|---|
| `title` | the opening claim, or any plain statement that should land big |
| `type-line` | a capability, typed out live; the last character flashes white and cools |
| `number-slam` | a concrete figure — put the figure in `value`, the unit in `text` |
| `ring-pulse` | a promise or an offer; concentric rings expanding through the words |
| `glass-tiles` | integrations, features, platforms — 2 to 6 dark glass tiles lighting in sequence |
| `shockwave` | speed, impact, a hard claim; two waves cross the frame |
| `orbit` | reach, coverage, "everywhere" — light points orbiting a dark sphere |
| `bar-rise` | growth or comparison; pass `items` as values 0–1 |
| `grid-sweep` | the open. A synthwave floor receding into black. Strongest first beat |
| `logo-lockup` | the close. Wordmark, hairline, domain |

Full parameters and composition notes: `references/shot-library.md`.

## The beat-sheet JSON

```json
{
  "title": "Meridian",
  "aspect": "9:16",
  "fps": 30,
  "brand": { "hero": "#00D4FF", "accent": null },
  "beats": [
    { "shot": "grid-sweep",  "dur": 2.6, "text": "Meetings nobody hates", "sub": "MERIDIAN" },
    { "shot": "type-line",   "dur": 3.2, "text": "Reads every calendar" },
    { "shot": "number-slam", "dur": 2.8, "value": "40%", "text": "fewer meetings" },
    { "shot": "glass-tiles", "dur": 3.0, "text": "Works where you work",
      "items": [{"glyph":"clock"},{"glyph":"check"},{"glyph":"bolt"},{"glyph":"lock"}] },
    { "shot": "logo-lockup", "dur": 3.0, "text": "MERIDIAN", "sub": "meridian.app" }
  ]
}
```

Glyphs available: `clock` `check` `bolt` `lock` `spark` `arrow` `grid` `globe`.

## Brand colour

If they give you a hex, put it in `brand.hero`. It is not pasted on top of
the palette — it *is* a point on the palette. The film's spectrum runs
cyan → blue → violet → magenta, and that band rotates so their colour lands
on it: a cyan brand opens the film, a violet brand owns the middle, a
magenta brand closes it. Everything else is built around that.

If they give two hexes, the second goes in `brand.accent`.

## Refining

After the first cut they will say what is wrong in plain language. Change
the JSON and rebuild — only re-render what changed.

| They say | You change |
|---|---|
| "beat three is too fast" | raise that beat's `dur`; leave the others |
| "make it pop more" | `number-slam` / `shockwave` in place of a flat beat |
| "too busy" | fewer `items`, fewer beats, longer `dur` |
| "colder" / "warmer" | move `brand.hero` along the band |
| "drop the search bar scene" | delete that beat, spread its seconds over the neighbours |
| "different opening" | swap beat one's shot — `grid-sweep` ↔ `title` ↔ `shockwave` |
| "use our purple #6633EE" | set `brand.hero`, rebuild; the structure holds |

Nothing is baked until they are happy.

## The look

Do not negotiate these — they are what makes a set of films look like a set.

- **Pure black backgrounds.** Never grey, never a dark wash.
- **Light is the subject.** Objects are dark matte glass; what you see is
  the light coming off and behind them.
- **A spectrum that travels** — cool at the open, warm at the close.
- **One idea per beat, big and centred.** Never a busy composite.
- **Hard cuts.** No crossfades between beats.

Why each of these, and the measured constants behind them:
`references/visual-language.md`.

## Setup

Needs `playwright` (with Chromium) and `imageio-ffmpeg`, which carries its
own H.264 encoder — no system ffmpeg required. Check before a first run:

```bash
python scripts/check_toolchain.py
```

## When it goes wrong

| Symptom | What it actually is |
|---|---|
| "It looks flat compared to the examples" | Almost always the model. Then the script — tighten it. |
| Only the HTML appeared | The HTML is finished work. Render the MP4 on request. |
| Rendering ten minutes | Normal. Hundreds of individual frames. |
| The MP4 won't play | It is H.264 in MP4. Try VLC, or open the HTML. |
| It picked the wrong parts of the script | It can only choose from what it was given. Ask which beats they wanted. |
| Text is clipped at the frame edge | Too many words. Five per line. |

## Done means

- `python tools/test_motion_promo.py` exits 0.
- The HTML opens in a browser and scrubs.
- The MP4 exists, is H.264, and plays.
- You looked at the contact sheet before rendering.
