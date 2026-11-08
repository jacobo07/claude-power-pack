"""Synthetic flow clips with KNOWN truth: a smooth random texture that translates, rotates or zooms by a
constant amount per frame (display 192x320, no audio)."""

from __future__ import annotations

import cv2
import numpy as np

W, H, N = 192, 320, 8


def texture(seed: int = 3) -> np.ndarray:
    rng = np.random.default_rng(seed)
    big = rng.random((H + 160, W + 160, 3)).astype(np.float32)
    big = cv2.GaussianBlur(big, (0, 0), 3.0)
    big = (big - big.min()) / (big.max() - big.min())
    return (big * 255).astype(np.uint8)


def clip(kind: str, amount: float, seed: int = 3) -> np.ndarray:
    """kind: translate (content moves by -amount px/frame in x, -0.5*amount in y), rotate (deg/frame), zoom (scale/frame)."""
    tex = texture(seed)
    out = []
    for f in range(N):
        if kind == "translate":
            m = np.float32([[1, 0, 80 - amount * f], [0, 1, 80 - 0.5 * amount * f]])
        elif kind == "rotate":
            m = cv2.getRotationMatrix2D((W / 2 + 80, H / 2 + 80), -amount * f, 1.0)
            m[:, 2] -= (80, 80)
        elif kind == "zoom":
            m = cv2.getRotationMatrix2D((W / 2 + 80, H / 2 + 80), 0, 1.0 + amount * f)
            m[:, 2] -= (80, 80)
        else:
            raise ValueError(kind)
        out.append(cv2.warpAffine(tex, m, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT))
    return np.stack(out)
