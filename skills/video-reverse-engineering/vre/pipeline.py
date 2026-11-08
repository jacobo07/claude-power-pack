"""`analyze`: one video in, a reverse-engineering spec out (spec.json, REVERSE.md, contact sheet).

The spec format follows reanimate's rows (one row per element and property: start, duration,
from -> to, easing, stagger) with "?" wherever a value was not read, plus the HeyGen-style
REVERSE.md ledger of everything that is approximate or unavailable.
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from . import audio as audio_mod
from . import media, palette, shots
from .deps import status as deps_status

SPEC_VERSION = "vre-spec/1"


def _contact_sheet(thumbs: list[np.ndarray], shot_list: list[shots.Shot], out: Path, cols: int = 8) -> None:
    tiles = []
    for s in shot_list:
        for f in (s.start, (s.start + s.end) // 2, s.end):
            t = cv2.cvtColor(thumbs[f], cv2.COLOR_RGB2BGR).copy()
            t = cv2.resize(t, (t.shape[1] * 2, t.shape[0] * 2), interpolation=cv2.INTER_NEAREST)
            cv2.rectangle(t, (0, 0), (t.shape[1], 14), (0, 0, 0), -1)
            cv2.putText(t, f"S{s.index} f{f}", (2, 11), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
            tiles.append(t)
    if not tiles:
        return
    h, w = tiles[0].shape[:2]
    rows = (len(tiles) + cols - 1) // cols
    sheet = np.zeros((rows * h, cols * w, 3), np.uint8)
    for i, t in enumerate(tiles):
        r, c = divmod(i, cols)
        sheet[r * h:(r + 1) * h, c * w:c * w + t.shape[1]] = t[:h, :w]
    cv2.imwrite(str(out), sheet)


def analyze(video: str, out_dir: str, *, width: int = 144, words: bool = True, beats: bool = True,
            brand: dict | None = None) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    p = media.probe(video)
    acc = shots.FeatureAccumulator()
    for frame in media.iter_frames(p, width):
        acc.add(frame)
    hist, grid, luma = acc.arrays()
    decoded = len(luma)
    cuts, shot_list, candidates = shots.detect(hist, grid, luma, p.fps)
    shot_rows = []
    for s in shot_list:
        pal = palette.shot_palette(acc.thumbs[s.start:s.end + 1:max(1, s.length // 6)])
        row = {**s.to_dict(), "start_s": round(s.start / p.fps, 3), "palette": pal,
               "luma_mean": round(float(luma[s.start:s.end + 1].mean()), 1)}
        if brand:
            row["brand_roles"] = palette.map_to_brand(pal["roles"], pal["polarity"], brand)
        shot_rows.append(row)
    y = audio_mod.load_mono(video) if p.has_audio else None
    audio_block: dict = {"status": "NO_AUDIO_STREAM"} if y is None else {"status": "OK"}
    if y is not None:
        onset_times = audio_mod.onsets(y, 22050)
        audio_block.update({
            "loudness": audio_mod.loudness(y), "onsets_s": onset_times,
            "onsets_on_cuts": audio_mod.pair_with_frames(onset_times, [c.frame for c in cuts], p.fps),
            "words": audio_mod.words(video) if words else {"status": "SKIPPED"},
            "beats": audio_mod.beats(video) if beats else {"status": "SKIPPED"},
        })
    spec = {
        "spec_version": SPEC_VERSION,
        "source": {**p.to_dict(), "decoded_frames": decoded, "frame_count_agrees": decoded == p.packets},
        "analysis": {"width": width, "height": media.analysis_size(p, width)[1]},
        "cuts": [c.to_dict() for c in cuts],
        "cut_candidates": candidates,
        "shot_crosscheck": shots.cross_check(video, cuts),
        "shots": shot_rows,
        "audio": audio_block,
        "rows": [],  # element/property rows, filled by the tracking stage (vre track)
        "dependencies": deps_status(),
    }
    (out / "spec.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    np.savez_compressed(out / "features.npz", hist=hist, grid=grid, luma=luma)
    _contact_sheet(acc.thumbs, shot_list, out / "contact_sheet.png")
    (out / "REVERSE.md").write_text(reverse_ledger(spec), encoding="utf-8")
    return spec


def _q(v) -> str:
    return "?" if v is None else str(v)


def reverse_ledger(spec: dict) -> str:
    src = spec["source"]
    lines = [
        "# REVERSE.md: what was measured, what is approximate, what is missing", "",
        f"- Source: `{src['path']}`, display {src['width']}x{src['height']} (stored {src['stored_width']}x"
        f"{src['stored_height']}, rotation {src['rotation']}), {src['fps_exact']} fps.",
        f"- Frames: {src['decoded_frames']} decoded vs {src['packets']} packets"
        f" ({'agree' if src['frame_count_agrees'] else 'DISAGREE: trust decoded, investigate'}),"
        f" {src['decoded_frames'] / src['fps']:.3f} s of picture; audio {_q(src['audio_duration_s'])} s.",
        f"- Shots: {len(spec['shots'])}; cuts {len(spec['cuts'])}; near-threshold candidates"
        f" {len(spec['cut_candidates'])} (read those frames before trusting the cut list).",
        "", "## Rules for the rebuild", "",
        "- Research use only: never copy the source's audio, voice, logos, illustrations, fonts, numbers or text.",
        "- Source metrics shown on screen are the source's, never the rebuild's results.",
        "- Never claim pixel identity. Match levels: MOVES-SAME (cuts and key times within 80 ms, same easing"
        " family) and LOOKS-SAME (adds per-shot SSIM/VMAF and palette deltas within the frozen tolerance).",
        "", "## Approximate or unavailable", "",
    ]
    cc = spec["shot_crosscheck"]
    if cc.get("status") != "OK":
        lines.append(f"- Shot cross-check: {cc['status']} ({cc.get('reason', '')}).")
    elif cc["only_ours"] or cc["only_pyscenedetect"]:
        lines.append(f"- Shot detectors disagree: only ours {cc['only_ours']}, only PySceneDetect"
                     f" {cc['only_pyscenedetect']}.")
    au = spec["audio"]
    if au.get("status") == "OK":
        for key in ("words", "beats"):
            st = au[key].get("status")
            if st != "OK":
                lines.append(f"- Audio {key}: {st} ({au[key].get('reason', '')}).")
    else:
        lines.append(f"- Audio: {au.get('status')}.")
    for d in spec["dependencies"]:
        if d["state"] != "OK" and d["state"] != "EXCLUDED":
            lines.append(f"- Engine `{d['name']}` ({d.get('stage')}): {d['state']}.")
    if not spec["rows"]:
        lines.append("- Element/property rows: not yet tracked (run `vre track`); motion is unmeasured.")
    for r in spec["rows"]:
        if r.get("evidence") != "OBSERVED":
            lines.append(f"- {r.get('element')}.{r.get('property')} f{r.get('start')}: {r.get('evidence')}"
                         f" ({r.get('easing')}, rmse {_q(r.get('rmse'))}).")
    return "\n".join(lines) + "\n"
