"""`vre track <spec dir>`: fill `spec.json` rows from the video. Phase 1 = text tracks, per shot.

Tracking runs per shot (a cut ends every track: a re-entry after a cut is a new layer). Frames are decoded
once, streamed, and only one shot is held in memory. Re-running replaces the rows this stage owns
(`source == "text"`) and nothing else, so two runs on the same spec give the same file.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from . import flow, layers, media, text
from .deps import available

TEXT_SOURCE = "text"
LAYER_SOURCE = "layer"
OWNED_SOURCES = (TEXT_SOURCE, LAYER_SOURCE)


def _shot_ranges(spec: dict) -> list[tuple[int, int, int]]:
    return [(s["index"], s["start"], s["end"]) for s in spec["shots"]]


def track_text_spec(spec: dict, frames, fps: float, *, detector=None) -> dict:
    """Run text tracking shot by shot over an iterator of display-orientation RGB frames (decode order).
    Returns {engine, status, tracks, rows}; row frames are absolute, elements are `s<shot>.text#<id>`."""
    ranges = _shot_ranges(spec)
    words = spec.get("audio", {}).get("words") or {}
    asr = words.get("words") if words.get("status") == "OK" else None
    rows: list[dict] = []
    tracks: list[dict] = []
    engine, status = None, "OK"
    it = iter(frames)
    for shot, a, b in ranges:
        buf = [f for _, f in zip(range(b - a + 1), it)]
        if len(buf) != b - a + 1:
            status = "SHORT_DECODE"
        if not buf:
            break
        t0 = time.time()
        res = text.track_text(buf, fps, detector=detector)
        print(f"[vre track] text shot {shot} frames {a}-{b} tracks {len(res['tracks'])} {time.time() - t0:.0f}s",
              file=sys.stderr, flush=True)
        engine, status = res["engine"], res["status"] if status == "OK" else status
        for r in res["rows"]:
            r = {**r, "element": f"s{shot}.{r['element']}", "start": r["start"] + a, "shot": shot}
            rows.append(r)
        for t in res["tracks"]:
            tracks.append({"element": f"s{shot}.text#{t['id']}", "shot": shot, "first": t["first"] + a,
                           "last": t["last"] + a, "frames": t["frames"], "box": t.get("box")})
    if asr:
        rows = text.align_reveals_to_words(rows, asr, fps)
    rows.sort(key=lambda r: (r["start"], r["element"], r["property"]))
    return {"engine": engine, "status": status, "tracks": tracks, "rows": rows}


def track_layers_and_flow(spec: dict, frames, fps: float, *, provider=None, do_flow: bool = True,
                          flow_stride: int = 2, text_tracks: list[dict] | None = None) -> dict:
    """Per shot: prompt boxes from the shot-start frame -> masks -> layer rows, plus a flow summary.
    Returns {engine, status, objects, rows, flow:{shot: summary}}. Rows carry absolute frames."""
    provider = provider or layers.ColorProvider()
    rows: list[dict] = []
    objects: list[dict] = []
    flows: dict[str, dict] = {}
    it = iter(frames)
    for shot, a, b in _shot_ranges(spec):
        buf = np.stack([f for _, f in zip(range(b - a + 1), it)]) if b >= a else np.zeros((0,))
        if len(buf) < 3:
            continue
        boxes = [t["box"] for t in (text_tracks or []) if t["shot"] == shot and t.get("box")]
        prompts = layers.shot_prompts(buf[0], boxes)
        if prompts:
            res = layers.track_layers(buf, fps, prompts, provider)
            for o in res["objects"]:
                objects.append({**o, "element": f"s{shot}.{o['element']}", "shot": shot,
                                **({"first": o["first"] + a, "last": o["last"] + a} if "first" in o else {})})
            for r in res["rows"]:
                rows.append({**r, "element": f"s{shot}.{r['element']}", "start": r["start"] + a, "shot": shot})
        if do_flow:
            flows[str(shot)] = flow.shot_flow(buf, stride=flow_stride)
    rows.sort(key=lambda r: (r["start"], r["element"], r["property"]))
    return {"engine": provider.name, "status": "OK", "objects": objects, "rows": rows, "flow": flows}


def track(spec_dir: str, *, video: str | None = None, width: int = 360, detector=None, provider=None,
          layers_on: bool = True, flow_on: bool = True, text_on: bool = True) -> dict:
    """Read `<spec_dir>/spec.json`, track text, layers and flow over the video, write rows + blocks back.
    Each stage replaces only the rows it owns (`source` text / layer), so re-runs give the same file."""
    path = Path(spec_dir) / "spec.json"
    spec = json.loads(path.read_text(encoding="utf-8"))
    p = media.probe(video or spec["source"]["path"])
    if (p.width, p.height) != (spec["source"]["width"], spec["source"]["height"]):
        raise media.MediaError("video display size differs from the spec: wrong video for this spec dir")
    use_ocr = detector is None and available("paddleocr")
    kept = [r for r in spec.get("rows", []) if r.get("source") not in OWNED_SOURCES]
    new_rows: list[dict] = []
    if text_on:
        res = track_text_spec(spec, media.iter_frames(p, width), p.fps, detector=detector)
        new_rows += res["rows"]
        spec["text_tracks"] = {"engine": res["engine"], "status": res["status"], "width": width, "ocr": use_ocr,
                               "tracks": res["tracks"]}
    else:
        new_rows += [r for r in spec.get("rows", []) if r.get("source") == TEXT_SOURCE]
    if layers_on or flow_on:
        lres = track_layers_and_flow(spec, media.iter_frames(p, width), p.fps, provider=provider,
                                     do_flow=flow_on,
                                     text_tracks=spec.get("text_tracks", {}).get("tracks"))
        if layers_on:
            new_rows += lres["rows"]
            spec["layer_tracks"] = {"engine": lres["engine"], "status": lres["status"], "width": width,
                                    "objects": lres["objects"]}
        if flow_on:
            spec["flow_tracks"] = {"width": width, "shots": lres["flow"]}
    if not layers_on:
        new_rows += [r for r in spec.get("rows", []) if r.get("source") == LAYER_SOURCE]
    spec["rows"] = kept + new_rows
    path.write_text(json.dumps(spec, indent=2, ensure_ascii=False, sort_keys=False), encoding="utf-8")
    return spec["text_tracks"] if text_on else spec.get("text_tracks", {})
