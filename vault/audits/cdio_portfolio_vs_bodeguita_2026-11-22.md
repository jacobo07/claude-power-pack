# CDIO live observation: portfolio vs Bodeguita (2026-11-22)

Mission: CDIO autonomous-design, tranche 1, slice S4. **Observation only**: no edit, no deploy to either site.
Captured 2026-11-22T17:14:06+0100 by headless Chromium through the S1 render-facts collector
(`tools/design_review_record.py::_observe`, commit b1403659), desktop 1440x900 and phone 390x844.
Script and raw output: session scratchpad `live_capture.py`, `live/facts.json`, eight PNGs (fold + full page).
Not durable: anything in this file that matters is copied here.

The four layers stay separate, as the mission requires. Nothing below is a conversion claim.

## 1. Deterministic measurements (browser observed)

| | portfolio desktop | portfolio phone | Bodeguita desktop | Bodeguita phone |
|---|---|---|---|---|
| load to idle (s) | 6.62 | 2.43 | 1.44 | 1.49 |
| horizontal overflow (px) | 0 | 0 | 0 | 0 |
| broken images / console errors / dead links | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| failed requests | 2 (see 1.1) | 0 | 0 | 0 |
| repeated large image | none | none | `art/strip/plate.svg` x2 | none |
| H1 size | 109.44px | 44px | 92px | 49.94px |
| words above the fold | 58 | 58 | 76 | 76 |
| whole page words / height | 1173 / 7565px | 1173 / 10942px | 400 / 4900px | 400 / 6288px |
| body background | rgb(10,10,10) | same | rgb(248,240,226) | same |
| in-hero action buttons | none (only nav "Hablemos") | none (only nav "Hablemos") | Ver la carta, Cómo llegar, Llamar, phone | same |

### 1.1 Collector false positive found by this live run
The two portfolio "failed requests" are `…/contact?tipo=…&_rsc=…  (net::ERR_ABORTED)`: Next.js cancelling its
own route prefetches. A cancelled request is not a failed asset. The S1 collector counted it, so a correct
Next.js site would have been marked `RENDER-ASSET-FAILED` (major). No fixture could have shown this; only the
live site did. Fixed in the S1 follow-up commit (cancelled requests are excluded and pinned by a test).

## 2. Reproducible visual observations (same PNGs, anyone can check)
- **Portfolio**: the protagonist is a real, authorised portrait with an ASCII-texture treatment, centred under a
  very large name. On **phone the portrait starts at ~640px and only the hair and eyes are above 844px**: the
  protagonist that makes the desktop hero is mostly lost on mobile. The phone secondary nav is cut off at the right
  edge ("PR…") inside its own scroller (not page overflow: measured 0).
- **Bodeguita**: the hero visual is an original illustrated jug and plate, captioned *"Ilustración original.
  Fotografía real pendiente de autorización."* A dark top banner declares the site a private demo with unconfirmed
  data, and the phone number carries "Pendiente de validar". On **phone the illustration starts below the fold**: the
  first screen is typography and buttons only.

## 3. Multimodal judgment (mine, one reviewer: a hypothesis, not a score)
- The initial hypothesis "Bodeguita lacks a gastronomic protagonist" is **confirmed for the observation and wrong
  about the cause**. The site already knows real photography is the right protagonist and **abstains** because
  none is authorised. That abstention is what mission section XIII requires. Generating food photography would
  break the authenticity rules. The fix is an input (authorised photos), not a design move.
- The portfolio's strength (a real person as protagonist, contrast, a treatment no one else has) holds on
  desktop. Its weaknesses are the ones the brief suspected: dense fold copy (58 words under a 109px name), no
  action inside the hero, and on phone the protagonist pushed out of the first screen.
- **Shared pattern, both sites:** on a 390x844 phone the hero's visual protagonist is not in the first screen.
  Measured on 2 of 2 sites from one author. It is a candidate check, **not a rule**: a text-led B2B page or a
  deliberately typographic hero can be correct without an image above the fold (kill switch 14).

## 4. User behaviour / commercial results
None measured. No analytics were read. Nothing here supports a conversion claim either way.

## Consequences for CDIO (what this run changed)
1. Collector false positive fixed (1.1): a real-site run is now part of the render-facts gate evidence.
2. "Phone protagonist below the fold" is logged as a **candidate** criterion for a later tranche. Before any
   promotion it needs evidence from a third site, a sector that is not food or personal, and a counterexample review.
3. Bodeguita's next visual step is blocked on the Owner, not on CDIO: authorised photography of the venue and dishes.
