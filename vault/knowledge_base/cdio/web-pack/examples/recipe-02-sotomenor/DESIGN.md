---
name: Sotomenor (demo)
aesthetic_family: F1
voice: brand-own (lichen neutrals, sloe accent, Bodoni Moda display)
colors:
  neutral: "#C9CDB8"
  ink: "#3B2A20"
  secondary: "#3F5240"
  primary: "#4B3A5A"
  surface: "#E4E6DA"
typography:
  display:
    fontFamily: Bodoni Moda, Georgia, serif
  body:
    fontFamily: Figtree, system-ui, sans-serif
experience:
  expressiveness: restrained
  motion_budget: low
  reduced_motion: equivalent
  feedback_latency_ms: 100
  progress_threshold_ms: 1000
  waiting: none
  progress_language: none
  success_posture: confirm
  error_posture: explain
  celebration_policy: never
  character_policy: none
  trust_posture: standard
---

# Sotomenor — demo site for CDIO-13 recipe 02 (ERA style, editorial luxury)

Sotomenor is an invented guesthouse. This site exists to run CDIO-13 recipe 02 end to end
through the CDIO-12 sequence and score its criteria. It is not a real business and is never
published.

## Experience contract (CDIO-07 picker)

- Q1, cost of a mistake: recoverable (an enquiry email, no payment) -> continue.
- Q2, habit or task: "visitors arrive to decide whether to ask about dates, then leave" -> task
  -> `expressiveness: restrained`, `success_posture: confirm`.
- Q3, intimidating or the interface is the product: neither -> no extra latitude.
- Latitude: `motion_budget`. `none` was defensible; `low` buys the one arch reveal recipe 02 asks
  for ("one restrained scroll sequence"), traded against the calm a still page has.
- Floor collision (CDIO-07 sec. 5): reveal motion vs reduced motion. Guard: content is visible
  without JS and with reduced motion; the arch is open from the start in both cases.
- Abstention test: `none` would be correct if the page had no image sequence at all.
- Over-delivery falsifier: any second scroll-driven effect (parallax, word reveals, cursor
  effects), or any loop that runs without the visitor scrolling, breaches this contract.
- Coherence: restrained ceiling with `reduced_motion: equivalent`; celebration `never`;
  `motion_budget: low` within `restrained`. Cleared.

## Tokens

| Token | Value | Role |
|---|---|---|
| lichen | #C9CDB8 | page background |
| bark | #3B2A20 | text |
| moss | #3F5240 | secondary surfaces, illustration |
| sloe | #4B3A5A | accent, links, the one call to action |
| mist | #E4E6DA | raised surface |

Type: Bodoni Moda (display, 400/500) and Figtree (body, 400/600). Scale 1.333 from 18px body.

## Fact sheet (Step 1)

- Name: Sotomenor (invented). Place: an invented hamlet in a chestnut valley.
- Rooms: 4. Open: March to November. Arrival: by car; the last 3 km are a track.
- Contact: hola@sotomenor.example (reserved demo domain; no real inbox).
- Proof: none. No reviews, ratings, counts or years appear on the site, because none exist.
- Imagery: original inline SVG illustrations drawn for this demo; no photographs.
