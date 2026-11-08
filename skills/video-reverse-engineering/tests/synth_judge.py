"""Synthetic reference + candidate variants for the judge, with KNOWN truth (display 108x192, 30 fps, no audio).

Three shots (cuts at 30 and 60), each a flat background with one coloured square sliding right over `dur` frames
from frame `start` of the shot with a named easing. The reference uses easeOutCubic starting at shot frame 5.
Variants are built by changing exactly one thing, so each judge dimension has a control that moves only it.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vre.easing import NAMED, bezier  # noqa: E402

W, H, FPS, N = 108, 192, 30, 90
BGS = [(14, 22, 40), (236, 232, 222), (20, 90, 100)]
FGS = [(245, 183, 0), (200, 40, 60), (250, 240, 220)]


def ease(name: str, u: float) -> float:
    return float(bezier(np.array([min(1.0, max(0.0, u))]), *NAMED[name])[0])


def frame(f: int, *, cuts=(30, 60), easing="easeOutCubic", start=5, dur=15, missing_shot=None,
          n_blank=()) -> np.ndarray:
    shot = sum(f >= c for c in cuts)
    t = f - ([0, *cuts][shot])
    img = np.zeros((H, W, 3), np.uint8)
    img[:] = BGS[shot]
    if f in n_blank:
        img[:] = 0
        return img
    if shot != missing_shot:
        x = 10 + 60 * ease(easing, (t - start) / dur)
        x0 = int(round(x))
        img[88:108, x0:x0 + 20] = FGS[shot]
    return img


def encode(path: Path, frames, size=(W, H), crf: int | None = None) -> Path:
    w, h = size
    codec = ["-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv444p"] if crf is None else \
        ["-c:v", "libx264", "-crf", str(crf), "-pix_fmt", "yuv420p"]
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                            "-r", str(FPS), "-i", "-", *codec, str(path)], stdin=subprocess.PIPE)
    for f in frames:
        enc.stdin.write(np.ascontiguousarray(f).tobytes())
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError("ffmpeg encode failed")
    return path


def variant(path: Path, n: int = N, **kw) -> Path:
    return encode(path, (frame(f, **kw) for f in range(n)))
