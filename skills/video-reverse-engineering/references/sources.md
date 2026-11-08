# Sources (research 2026-11-08)

No open-source pipeline or skill turns an existing video into Remotion code, and no repo named
"video-reverse-engineering" exists. This skill is assembled from the parts below. Star counts were read on each
repo's GitHub page on 2026-11-08; commit dates were not visible and are not claimed.

| Source | Licence | Taken how | What |
|---|---|---|---|
| heygen-com/hyperframes, skill `reverse-any-video` | Apache-2.0 | workflow ideas only | fps/size/duration from frames not audio; jump cuts and punch-ins count as cuts; read the frames at every entrance/exit/transition; rebuild text/cards/charts as code; diff reports missing/extra cuts, audio offset, worst moments; a REVERSE.md of approximations. Its CLI is not used (Pro login, telemetry). |
| NiazMorshed2007/reanimate | MIT | ideas, ported | spec rows (element x property: start, duration, from->to, easing, stagger, "?" when unread); named-easing fit, overshoot, spring estimate; MOVES-SAME (80 ms, same family) vs LOOKS-SAME; particles compared blurred; fix loop capped at 2-5 rounds. |
| lovisdotio/motion2code | MIT | ideas | dense frame study around cuts and a contact sheet; exact flat palette; frame-diff worst-5 moments; side-by-side proof video. |
| loadingio/easing-fit | MIT | idea, re-implemented | fit a free cubic-bezier to samples (here with scipy least squares). |
| easings.net cubic-bezier values | public reference | data | the named families are defined as Remotion `Easing.bezier` values so fit == codegen. |
| Breakthrough/PySceneDetect | BSD-3 | optional dependency | AdaptiveDetector as a second opinion on cuts (`shot_crosscheck`). |
| TransNetV2 (PyTorch port) | MIT | optional dependency (W2) | learned shot boundaries as a third opinion. |
| PaddlePaddle/PaddleOCR | Apache-2.0 | optional dependency (W2) | text boxes per frame, linked into one track per text layer. |
| facebookresearch/sam2 | Apache-2.0 | optional dependency (W2) | per-layer masks from a box/point prompt. |
| facebookresearch/sam3 | SAM License (custom) | GATED (W2) | text-prompted masks ("card", "number"); needs a human licence read: `VRE_ALLOW_SAM3=1`. |
| RAFT via torchvision | BSD-3 | optional dependency (W2) | optical flow for rotation and particle direction (replaces CoTracker). |
| m-bain/whisperX | BSD-2 | optional dependency | word timestamps by forced alignment (no diarization). |
| SYSTRAN/faster-whisper | MIT | optional dependency | word timestamps fallback. |
| CPJKU/beat_this | MIT | optional dependency | beat and downbeat grid, never `--dbn`. |
| librosa | ISC | optional dependency | onset cross-check. |
| Netflix/vmaf | BSD+Patent | optional dependency (W3) | per-shot VMAF / SSIM / CIEDE2000 in the judge. |
| remotion-dev/skills | not verified | companion skill | rebuild-side Remotion practice; no reverse capability. |
| a private frame-forensics harness (not in this repo) | private | the forensic tier | region grid with per-cell noise floor, golden benchmark lock, negative controls, slice harness. vre is the portable one-shot tier; use the creative-os judge when a frame-accurate benchmark is required. |

## Excluded

| Source | Why |
|---|---|
| facebookresearch/co-tracker | CC-BY-NC weights |
| madmom models | CC BY-NC-SA |
| mixfont/lens (font ID) | personal / academic / non-commercial only |
| HeyGen HyperFrames CLI | paid Pro login, usage telemetry |

## Looked for, not found

`llm-video-mcp` (GitHub 404), mblode `reverse-engineer-animation` (path 404), an open video-to-Lottie with
editable keyframes, a kinetic-typography detector, a Python easing-fit library.
