"""Synthetic text clip with KNOWN ground truth (display 360x640, 30 fps, 90 frames, no rotation, no audio).

Dark navy background. Three invented text layers (all invented neutral words):
  L0 "ORBIT"   x moves 20 -> 160 over frames 10..40 with easeOutCubic, constant size
  L1 "LAUNCH PLAN NOW" at fixed position, words revealed one by one at frames 20, 35, 50
  L2 "SCALE"   fixed position, height grows 1.0 -> 1.6 over frames 30..60 (linear)
Truth is exposed as plain numbers so a test can compare a measured track against it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vre.easing import NAMED, bezier  # noqa: E402

W, H, FPS, N = 360, 640, 30, 90
BG = (11, 31, 58)
FG = (245, 245, 240)
L0_X = (20.0, 160.0, 10, 40)  # from, to, start frame, end frame
L1_WORDS = ["LAUNCH", "PLAN", "NOW"]
L1_REVEAL = [20, 35, 50]
L2_SCALE = (1.0, 1.6, 30, 60)
FONT = cv2.FONT_HERSHEY_DUPLEX


def l0_x(f: int, family: str = "easeOutCubic") -> float:
    a, b, f0, f1 = L0_X
    if f <= f0:
        return a
    if f >= f1:
        return b
    return a + (b - a) * float(bezier(np.array([(f - f0) / (f1 - f0)]), *NAMED[family])[0])


def l2_scale(f: int) -> float:
    a, b, f0, f1 = L2_SCALE
    return a + (b - a) * min(1.0, max(0.0, (f - f0) / (f1 - f0)))


def _put(img: np.ndarray, text: str, x: float, y_base: int, scale: float, thick: int = 2) -> None:
    cv2.putText(img, text, (int(round(x)), y_base), FONT, scale, FG, thick, cv2.LINE_AA)


def frame(f: int, reveal: list[int] | None = None, l0_family: str = "easeOutCubic",
          with_text: bool = True) -> np.ndarray:
    img = np.empty((H, W, 3), np.uint8)
    img[:] = BG
    if not with_text:
        return img
    _put(img, "ORBIT", l0_x(f, l0_family), 120, 1.4)
    shown = sum(1 for r in (reveal or L1_REVEAL) if f >= r)
    if shown:
        _put(img, " ".join(L1_WORDS[:shown]), 20, 300, 1.0)
    _put(img, "SCALE", 20, 520, 1.0 * l2_scale(f))
    return img


def frames(**kw) -> list[np.ndarray]:
    return [frame(f, **kw) for f in range(N)]
