---
name: video-reverse-engineering
description: Reverse-engineer a reference video (a reel, explainer, ad, motion-graphics short) into a measured rebuild spec, then rebuild it for another brand and judge the rebuild. Use when the user shows a video and asks for "one like this", "the same but for <brand>", "clone / copy / recreate this video", "how was this animated", "what easing / timing / cuts / palette does this use", or wants a frame-accurate reconstruction. Measures in display orientation with a counted frame total, finds cuts and fades, palettes by role, audio onsets / words / beats, and fits easing curves and springs into Remotion code. Never copies the source's audio, voice, logos, illustrations, fonts, numbers or text.
---

# Video Reverse Engineering (vre)

One reference video in; out come a spec of what it does frame by frame, a ledger of what is only approximate,
and (W3) a Remotion composition for the target brand plus a judge report. "One-shot" means one command
produces a judged first draft, never a claimed copy: the judge says where it differs, and the fix loop is capped
at 2-5 rounds.

## Run it

From this skill directory (`~/.claude/skills/video-reverse-engineering`):

```
python -m vre deps                                   # which optional engines are installed, licences, gates
python -m vre analyze <video> --out <dir> [--brand brand.json] [--no-words] [--no-beats]
```

`analyze` writes `<dir>/spec.json`, `<dir>/REVERSE.md`, `<dir>/contact_sheet.png` and `<dir>/features.npz`.
Read REVERSE.md first: it lists every stage that ran degraded or not at all.
Heavy engines (SAM 2, whisperX, PaddleOCR on GPU) belong on a GPU host. Everything in W1 runs on CPU.

## The workflow (do it in this order)

1. **Source truth.** fps, size and duration come from the video stream and the COUNTED frames, never from
   audio length. Rotation is applied once at decode; a portrait reel stored landscape is read portrait.
   `spec.source.frame_count_agrees` false means: trust decoded frames and say why they differ.
2. **Cuts.** Adaptive change score (a cut must stand out against its neighbourhood), plus fades through black
   or white as their own boundaries. Near-threshold frames go to `cut_candidates`: **read those frames** (and
   every PySceneDetect disagreement in `shot_crosscheck`) before trusting the cut list. Jump cuts and punch-ins
   are cuts.
3. **Palette by role.** Per shot: background (largest), accent (most saturated), text (most contrasting
   near-neutral), surface. A rebrand maps colours by ROLE (`--brand`), never by hue.
4. **Audio as timing only.** Onsets (SFX hits) always; words (whisperX, else faster-whisper) and beats
   (beat_this) when installed. `onsets_on_cuts` pairs hits with cuts within +-2 frames: that is the AV-sync
   grammar to rebuild with NEW sound.
5. **Motion.** For each tracked element/property, split where it holds still, then `easing.fit_segment` fits
   the Remotion `Easing.bezier` families, a free bezier, and a spring when it overshoots (giving
   `spring({mass, damping, stiffness})`). Fewer than 8 samples or rmse above 0.03 is ESTIMATED, never OBSERVED.
6. **Spec rows.** One row per element and property: start, duration, from -> to, easing, stagger, evidence.
   Unread values are `"?"`. Text, cards and charts are rebuilt as code; photos and footage are replaced with
   the target brand's own assets, never cut from the source.
7. **Rebuild, then judge** (W3): per-shot comparison, cut-list diff, AV offset, two match levels, side by side.

## Match levels (never claim pixel identity)

- **MOVES-SAME**: every cut and key time within 80 ms (about 2 frames at 30 fps) and the same easing family.
- **LOOKS-SAME**: MOVES-SAME plus per-shot structural similarity and palette deltas within frozen tolerances.
  A rebrand is judged on MOVES-SAME and layout, never on pixels.
- Tolerances come from the measured noise floor and negative controls, frozen BEFORE the first candidate.
  The generator never edits the judge's benchmark.

## Hard rules

- Research use of the reference only: no audio, voice, logos, illustrations, fonts, numbers or text in a
  deliverable. Numbers on screen in the source are the source's; they never become the target's results.
- New claims for a real brand are pending its legal or owner approval; nothing is published by this skill.
- Licence wall (`vre/deps.py`): CoTracker, madmom models and mixfont/lens are EXCLUDED (non-commercial).
  SAM 3 is GATED behind `VRE_ALLOW_SAM3=1` after a human reads its licence. whisperX diarization stays off.
- A missing engine is UNAVAILABLE in the spec and REVERSE.md, never an empty result read as "nothing there".

## Status

| Wave | Content | State |
|---|---|---|
| W1 | probe/orientation, cuts/fades, palette roles, audio onsets/words/beats, easing+spring fit, spec, ledger | built, 16 tests on a synthetic clip with known truth |
| W2 | text tracks (PaddleOCR), layer tracks (SAM 2 / gated SAM 3), flow (RAFT), rows from tracks (`vre track`) | built, synthetic-proven with negative controls; real-footage gate in progress |
| W3 | spec -> Remotion TSX codegen (`vre generate`) | built, 4 tests, tsc-checked when `VRE_TSC_DIR` is set; render round trip not yet run |
| W3 | judge (`vre/judge.py`: frozen tolerances, 8 dimensions, A/A + negative controls) | built, 13 tests |
| W3 | fix loop (`vre oneshot`: render, judge, shift row starts, capped 2-5 rounds, stops and reports on unfixable defects) | built, 3 tests with an injected pure-Python renderer; real Remotion render check pending |

Tests: `python -m pytest tests -q` (set `VRE_TEST_CACHE=<dir>` to reuse the synthetic clip).
Sources, licences and what was absorbed from each: `references/sources.md`.
