"""Synthetic layers clip with KNOWN truth (display 360x640, 30 fps, 90 frames, no audio, flat dark background).

Invented flat shapes, no text:
  CARD   teal rectangle 90x60, x springs 40 -> 220 from frame 10 (zeta 0.35, omega 18 rad/s), y fixed
  BAR    amber bar 120x24 at (180, 330), rotates 0 -> 60 degrees over frames 20..60 (easeInOutCubic)
  DOT0-2 three coral squares, y moves 560 -> 500 with easeOutCubic over 18 frames, starting at 12, 18, 24
         (a stagger of 6 frames), scale 0.6 -> 1.0 on the same curve
Truth is plain numbers so a test can compare a recovered track against it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vre.easing import NAMED, bezier, spring_curve  # noqa: E402

W, H, FPS, N = 360, 640, 30, 90
BG = (14, 22, 40)
TEAL, AMBER, CORAL = (20, 184, 166), (245, 170, 20), (240, 90, 80)
CARD_X = (40.0, 220.0, 10)  # from, to, start frame
CARD_ZETA, CARD_OMEGA, CARD_Y, CARD_WH = 0.35, 18.0, 150.0, (90.0, 60.0)
BAR_ANGLE = (0.0, 60.0, 20, 60)
BAR_C, BAR_WH = (180.0, 330.0), (120.0, 24.0)
DOT_STARTS, DOT_X, DOT_Y, DOT_DUR, DOT_SIZE = [12, 18, 24], [60.0, 160.0, 260.0], (560.0, 500.0), 18, 40.0
DOT_SCALE = (0.6, 1.0)


def _ease(family: str, u: float) -> float:
    return float(bezier(np.array([min(1.0, max(0.0, u))]), *NAMED[family])[0])


def card_x(f: int) -> float:
    a, b, f0 = CARD_X
    if f < f0:
        return a
    return a + (b - a) * float(spring_curve(np.array([(f - f0) / FPS]), CARD_ZETA, CARD_OMEGA)[0])


def bar_angle(f: int, family: str = "easeInOutCubic") -> float:
    a, b, f0, f1 = BAR_ANGLE
    return a + (b - a) * _ease(family, (f - f0) / (f1 - f0))


def dot_u(f: int, k: int) -> float:
    return _ease("easeOutCubic", (f - DOT_STARTS[k]) / DOT_DUR)


def _poly(img, pts, color) -> None:
    cv2.fillConvexPoly(img, np.round(np.asarray(pts) * 16).astype(np.int32), color, cv2.LINE_AA, 4)


def _rect(cx, cy, w, h, deg):
    t = np.deg2rad(deg)
    c, s = np.cos(t), np.sin(t)
    return [(cx + sx * w / 2 * c - sy * h / 2 * s, cy + sx * w / 2 * s + sy * h / 2 * c)
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def frame(f: int, *, bar_family: str = "easeInOutCubic", with_bar: bool = True, with_card: bool = True,
          dot_starts: list[int] | None = None) -> np.ndarray:
    img = np.empty((H, W, 3), np.uint8)
    img[:] = BG
    if with_card:
        _poly(img, _rect(card_x(f) + CARD_WH[0] / 2, CARD_Y, *CARD_WH, 0), TEAL)
    if with_bar:
        _poly(img, _rect(*BAR_C, *BAR_WH, bar_angle(f, bar_family)), AMBER)
    for k in range(3):
        st = (dot_starts or DOT_STARTS)[k]
        if f >= st:
            u = _ease("easeOutCubic", (f - st) / DOT_DUR)
            s = DOT_SCALE[0] + (DOT_SCALE[1] - DOT_SCALE[0]) * u
            y = DOT_Y[0] + (DOT_Y[1] - DOT_Y[0]) * u
            _poly(img, _rect(DOT_X[k] + DOT_SIZE / 2, y, DOT_SIZE * s, DOT_SIZE * s, 0), CORAL)
    return img


def frames(**kw) -> np.ndarray:
    return np.stack([frame(f, **kw) for f in range(N)])
