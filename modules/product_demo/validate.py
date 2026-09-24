"""Validator: is the rendered demo a truthful, well-formed artifact?

Four outcomes, never collapsed:
    VALID             every check ran and passed
    SUBJECT_INVALID   the demo is wrong (defects listed, each with a class)
    VERIFIER_FAILED   a check could not run; outranks subject defects, because a
                      run that died part-way says nothing about what it skipped
    UNREADABLE_INPUT  the artifact is missing, empty or undecodable

A process that exited 0 and an MP4 that exists prove nothing; this is the gate.
"""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

VALID, SUBJECT_INVALID, VERIFIER_FAILED, UNREADABLE = (
    "VALID", "SUBJECT_INVALID", "VERIFIER_FAILED", "UNREADABLE_INPUT")
SAMPLE_FRAMES = 8
UNIFORM_STD = 2.0      # a frame with luminance stddev below this carries no picture
BLACK_MEAN = 8.0


@dataclass
class Verdict:
    outcome: str
    defects: list = field(default_factory=list)     # {class, detail}
    checks: dict = field(default_factory=dict)      # name -> observed value
    verifier_errors: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def ffmpeg_exe() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def probe(path: Path) -> dict:
    """Duration / geometry / codec / fps from ffmpeg's own stream report."""
    r = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", str(path)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60)
    txt = r.stderr
    info: dict = {}
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", txt)
    if m:
        info["duration_s"] = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
    m = re.search(r"Video: (\w+).*?, (\d{2,5})x(\d{2,5})", txt)
    if m:
        info["codec"], info["w"], info["h"] = m[1], int(m[2]), int(m[3])
    m = re.search(r"([\d.]+) fps", txt)
    if m:
        info["fps"] = float(m[1])
    return info


def frame_stats(path: Path, duration_s: float, n: int = SAMPLE_FRAMES) -> list:
    """Decode n evenly spaced frames (first and last included) -> luminance mean/std."""
    from PIL import Image, ImageStat
    stats = []
    with tempfile.TemporaryDirectory() as td:
        times = [min(duration_s - 0.05, max(0.0, duration_s * k / (n - 1))) for k in range(n)]
        for k, t in enumerate(times):
            out = Path(td) / f"s{k}.png"
            subprocess.run([ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.3f}",
                            "-i", str(path), "-frames:v", "1", str(out)], capture_output=True, timeout=60)
            if not out.is_file():
                stats.append({"t": round(t, 2), "decoded": False})
                continue
            st = ImageStat.Stat(Image.open(out).convert("L"))
            stats.append({"t": round(t, 2), "decoded": True, "mean": round(st.mean[0], 1),
                          "std": round(st.stddev[0], 1)})
    return stats


def check_layout(layout: dict) -> list:
    """Every callout inside the product screen, pointed at its own target, hiding no text."""
    defects = []
    scr = layout["screen"]
    for c in layout["callouts"]:
        inside = (c["x"] >= scr["x"] - 0.5 and c["y"] >= scr["y"] - 0.5
                  and c["x"] + c["w"] <= scr["x"] + scr["w"] + 0.5 and c["y"] + c["h"] <= scr["y"] + scr["h"] + 0.5)
        if not inside:
            defects.append({"class": "CLIPPED_CALLOUT", "detail": f"callout {c['n']} '{c['text']}' leaves the screen"})
        g, a = c["target"], c["anchor"]
        on_target = g["x"] - 0.5 <= a["x"] <= g["x"] + g["w"] + 0.5 and g["y"] - 0.5 <= a["y"] <= g["y"] + g["h"] + 0.5
        if not on_target:
            defects.append({"class": "MISPOINTED_CALLOUT",
                            "detail": f"callout {c['n']} points at ({a['x']},{a['y']}), outside its target"})
        if c.get("hidden_text_px") is None:
            defects.append({"class": "OCCLUSION", "detail": f"callout {c['n']} found no clean spot"})
        elif c["hidden_text_px"] > 0:
            defects.append({"class": "OCCLUSION",
                            "detail": f"callout {c['n']} hides {c['hidden_text_px']} px^2 of product text"})
    return defects


def validate(video: Path, *, layout: dict, timeline: dict, telemetry: dict, output: dict,
             canvas: tuple) -> Verdict:
    v = Verdict(outcome=VALID)
    if not video.is_file() or video.stat().st_size == 0:
        return Verdict(outcome=UNREADABLE, defects=[{"class": "MISSING", "detail": f"{video} missing or empty"}])
    try:
        info = probe(video)
        v.checks["probe"] = info
        if "duration_s" not in info or "w" not in info:
            return Verdict(outcome=UNREADABLE, checks=v.checks,
                           defects=[{"class": "UNDECODABLE", "detail": "ffmpeg reports no video stream"}])
        size = video.stat().st_size
        v.checks["bytes"] = size
        if size > int(output.get("max_bytes", 12_000_000)):
            v.defects.append({"class": "OVERSIZE", "detail": f"{size} bytes > budget {output['max_bytes']}"})
        want = timeline["duration_ms"] / 1000
        fps = int(output.get("fps", 30))
        if abs(info["duration_s"] - want) > 1.5 / fps + 0.05:
            v.defects.append({"class": "DURATION_MISMATCH",
                              "detail": f"video {info['duration_s']:.3f}s vs timeline {want:.3f}s"})
        if (info["w"], info["h"]) != tuple(canvas):
            v.defects.append({"class": "GEOMETRY", "detail": f"{info['w']}x{info['h']} vs stage {canvas[0]}x{canvas[1]}"})
        stats = frame_stats(video, info["duration_s"])
        v.checks["frames"] = stats
        for s in stats:
            if not s["decoded"]:
                v.defects.append({"class": "UNDECODABLE_FRAME", "detail": f"t={s['t']}s"})
            elif s["std"] < UNIFORM_STD:
                v.defects.append({"class": "DEGENERATE_FRAME", "detail": f"t={s['t']}s uniform (std {s['std']})"})
            elif s["mean"] < BLACK_MEAN:
                v.defects.append({"class": "BLACK_FRAME", "detail": f"t={s['t']}s mean {s['mean']}"})
        v.defects += check_layout(layout)
        v.defects += [{"class": d["class"], "detail": d["detail"]} for d in timeline.get("defects", [])]
        if telemetry.get("outcome") != "ok":
            v.defects.append({"class": "CAPTURE_REFUSED", "detail": json.dumps(telemetry.get("refusal"))})
        if telemetry.get("console_errors") or telemetry.get("http_errors"):
            v.defects.append({"class": "PRODUCT_ERROR", "detail": "capture recorded console/HTTP errors"})
        v.checks["compressions"] = len(timeline.get("compressions", []))
    except Exception as exc:   # the verifier broke: say so, and outrank everything
        v.verifier_errors.append(f"{type(exc).__name__}: {exc}")
        v.outcome = VERIFIER_FAILED
        return v
    v.outcome = SUBJECT_INVALID if v.defects else VALID
    return v
