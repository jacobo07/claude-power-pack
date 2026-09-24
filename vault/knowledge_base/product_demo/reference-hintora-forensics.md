# Reference demo forensics: Hintora landing demo (measured 2026-09-24)

Purpose: extract a reusable motion grammar for product demos. Not a clone brief.
Status of every claim is marked OBSERVED, INFERENCE or UNKNOWN.

## Source and instrument
- Source: an Owner-supplied phone screen recording (Brave, Android) of the hintora.ai landing page. Identified by metadata
  (duration + geometry), not by name; the file is kept out of the repo.
- Instruments: imageio-ffmpeg 7.1 (probe, scene select, crops), visual inspection of a 1 fps sheet, a 2 fps crop sheet of
  the demo region, and one full-resolution frame at t=20 s.

## Container (OBSERVED)
- 26.26 s, 1080x2340, H.264 Main, ~52.44 fps variable, AAC 48 kHz stereo.
- The recording medium is inside the evidence: Android status bar, Brave URL bar and nav bar are NOT part of the demo.
  The demo is an embedded video on the page, roughly y=900..1800 of the recording.

## Composition (OBSERVED)
- Stage: laptop mockup (bezel + base), macOS-style menu bar, landscape wallpaper, dock.
- App window: a fictional spreadsheet with Overdue / Paid status pills.
- Notch pill, dynamic-island style, narrates system phase: listening (waveform) -> understanding -> guiding step by step.
- Query card under the pill: shortcut hint, query text typed progressively.
- Numbered callouts in brand blue, anchored to real menu targets, one at a time, with an arrow.
- Cursor travels to the target; the menu opens; the item highlights.
- The first seconds show the payoff state, then the scene resets: the loop closes cleanly.
- A page-level toggle under the stage switches between two demo variants.

## Camera (OBSERVED at 2 fps over 12-26 s)
- Stage and camera are static. No zoom, no pan. All motion is inside the stage.
- UNKNOWN: sub-0.5 s micro-zoom.

## Rhythm (OBSERVED; 10 fps sampling, scene threshold 0.004 on the demo crop)
- 37 of ~262 samples change: about 86% of the runtime is holds (upper bound; small typing may fall under the threshold).
- About 11 bursts, mean spacing ~2.4 s; longest holds ~3.1 s.

## Production method (INFERENCE)
- Very likely a coded HTML/CSS animation of a mocked desktop rather than a screen capture: vector-crisp text in every state,
  a fictional app, the conventional 9:41 clock, no capture artifacts.
- Consequence for CPP: the reference's look comes from a coded STAGE. Our demos put REAL captured product inside that stage,
  and every overlay is anchored to a recorded element, never drawn as if it were product UI.

## Motion grammar (reusable)
1. Static stage; attention is directed by product state and overlays, not by camera pumping. Zoom is opt-in.
2. A state pill may narrate the system phase, and only when the product really is in that phase.
3. Callouts are numbered, one at a time, and anchored to the element the real interaction targets.
4. A beat every ~2-3 s, with long holds for reading.
5. Put the payoff first or last so the loop closes.
