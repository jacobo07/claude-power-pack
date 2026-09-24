# Recordly: legal and technical disposition (2026-09-24)

Subject: github.com/webadderallorg/recordly (TypeScript, Electron desktop editor; ~31k stars; pushed 2026-09-23).

## License (OBSERVED from LICENSE.md, read via the GitHub API)
- GNU AGPL-3.0, with an added preamble: derived code must credit Recordly in the user-facing UI and the repo, and the
  "Recordly" name and branding may not be used. The file also notes the project began as a fork of OpenScreen.
- GitHub classifies the file as NOASSERTION because of the added terms. Do not read NOASSERTION as "unlicensed".

## Technical shape (OBSERVED)
- An interactive GUI editor: a human records, then edits zoom regions, cursor effects, speed regions, frames and exports.
- Its extension API runs inside the editor renderer (render hooks, cursor effects, playback and export events).
- It is not a headless library, so it cannot be driven as a CPP capture backend without a human in the loop.

## Disposition
| Use | Verdict | Reason |
|---|---|---|
| Study ideas (cursor smoothing, zoom/speed regions, render hooks, export parity) | ALLOWED | Ideas are not copyrightable; reimplement from principles |
| Owner using Recordly by hand as an external tool | ALLOWED | No distribution; output videos are the Owner's |
| Copy, vendor, fork or transplant its code into CPP or into generated software | PROHIBITED | AGPL reciprocity plus the added UI-attribution term would attach to QuickLease and every future product |
| Depend on it (npm, submodule, bundled binary) | PROHIBITED | Same; also an Electron GUI, the wrong substrate |
| Use its name or branding | PROHIBITED | Added term |

## Consequence
modules/product_demo is a clean-room implementation built on Playwright (Apache-2.0) and ffmpeg via imageio-ffmpeg.
Nothing in it was derived from Recordly source; the only input was the public README/EXTENSIONS description of features.
