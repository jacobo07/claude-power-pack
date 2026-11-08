"""`vre track <spec dir>`: fill `spec.json` rows from the video. Phase 1 = text tracks, per shot.

Tracking runs per shot (a cut ends every track: a re-entry after a cut is a new layer). Frames are decoded
once, streamed, and only one shot is held in memory. Re-running replaces the rows this stage owns
(`source == "text"`) and nothing else, so two runs on the same spec give the same file.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import media, text
from .deps import available

TEXT_SOURCE = "text"


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
        res = text.track_text(buf, fps, detector=detector)
        engine, status = res["engine"], res["status"] if status == "OK" else status
        for r in res["rows"]:
            r = {**r, "element": f"s{shot}.{r['element']}", "start": r["start"] + a, "shot": shot}
            rows.append(r)
        for t in res["tracks"]:
            tracks.append({"element": f"s{shot}.text#{t['id']}", "shot": shot, "first": t["first"] + a,
                           "last": t["last"] + a, "frames": t["frames"]})
    if asr:
        rows = text.align_reveals_to_words(rows, asr, fps)
    rows.sort(key=lambda r: (r["start"], r["element"], r["property"]))
    return {"engine": engine, "status": status, "tracks": tracks, "rows": rows}


def track(spec_dir: str, *, video: str | None = None, width: int = 360, detector=None) -> dict:
    """Read `<spec_dir>/spec.json`, track text over the video, write rows + a `text_tracks` block back."""
    path = Path(spec_dir) / "spec.json"
    spec = json.loads(path.read_text(encoding="utf-8"))
    p = media.probe(video or spec["source"]["path"])
    if (p.width, p.height) != (spec["source"]["width"], spec["source"]["height"]):
        raise media.MediaError("video display size differs from the spec: wrong video for this spec dir")
    use_ocr = detector is None and available("paddleocr")
    res = track_text_spec(spec, media.iter_frames(p, width), p.fps, detector=detector)
    spec["rows"] = [r for r in spec.get("rows", []) if r.get("source") != TEXT_SOURCE] + res["rows"]
    spec["text_tracks"] = {"engine": res["engine"], "status": res["status"], "width": width, "ocr": use_ocr,
                           "tracks": res["tracks"]}
    path.write_text(json.dumps(spec, indent=2, ensure_ascii=False, sort_keys=False), encoding="utf-8")
    return spec["text_tracks"]
