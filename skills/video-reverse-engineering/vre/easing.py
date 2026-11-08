"""Fit easing curves, overshoot, settle and springs to tracked property samples.

Absorbed ideas (MIT): reanimate's easing.ts (fit named easings, detect overshoot, estimate a spring
from it) and loadingio/easing-fit (fit a free cubic-bezier). The named families are DEFINED as the
cubic-bezier values Remotion's `Easing.bezier` takes, so what is fitted is exactly what is generated.
No Python library did this (research 2026-11-08), hence this module.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from scipy.optimize import least_squares

# easings.net cubic-bezier values (the CSS forms of the Penner families)
NAMED: dict[str, tuple[float, float, float, float]] = {
    "linear": (0.0, 0.0, 1.0, 1.0),
    "easeInSine": (0.12, 0, 0.39, 0), "easeOutSine": (0.61, 1, 0.88, 1), "easeInOutSine": (0.37, 0, 0.63, 1),
    "easeInQuad": (0.11, 0, 0.5, 0), "easeOutQuad": (0.5, 1, 0.89, 1), "easeInOutQuad": (0.45, 0, 0.55, 1),
    "easeInCubic": (0.32, 0, 0.67, 0), "easeOutCubic": (0.33, 1, 0.68, 1), "easeInOutCubic": (0.65, 0, 0.35, 1),
    "easeInQuart": (0.5, 0, 0.75, 0), "easeOutQuart": (0.25, 1, 0.5, 1), "easeInOutQuart": (0.76, 0, 0.24, 1),
    "easeInQuint": (0.64, 0, 0.78, 0), "easeOutQuint": (0.22, 1, 0.36, 1), "easeInOutQuint": (0.83, 0, 0.17, 1),
    "easeInExpo": (0.7, 0, 0.84, 0), "easeOutExpo": (0.16, 1, 0.3, 1), "easeInOutExpo": (0.87, 0, 0.13, 1),
    "easeInCirc": (0.55, 0, 1, 0.45), "easeOutCirc": (0, 0.55, 0.45, 1), "easeInOutCirc": (0.85, 0, 0.15, 1),
    "easeInBack": (0.36, 0, 0.66, -0.56), "easeOutBack": (0.34, 1.56, 0.64, 1), "easeInOutBack": (0.68, -0.6, 0.32, 1.6),
}


def bezier(u: np.ndarray, x1: float, y1: float, x2: float, y2: float) -> np.ndarray:
    """y for each progress u in [0, 1] of the CSS cubic-bezier (0,0)-(x1,y1)-(x2,y2)-(1,1)."""
    u = np.clip(np.asarray(u, dtype=np.float64), 0.0, 1.0)
    lo, hi = np.zeros_like(u), np.ones_like(u)
    for _ in range(50):  # x(t) is monotonic for x1, x2 in [0, 1]
        t = 0.5 * (lo + hi)
        x = 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t ** 2 * x2 + t ** 3
        lo, hi = np.where(x < u, t, lo), np.where(x < u, hi, t)
    t = 0.5 * (lo + hi)
    return 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t ** 2 * y2 + t ** 3


def spring_curve(t_s: np.ndarray, zeta: float, omega: float) -> np.ndarray:
    """Unit step response of a damped spring (mass 1), t in seconds, starting at 0 and settling at 1."""
    t = np.asarray(t_s, dtype=np.float64)
    if zeta < 1.0:
        wd = omega * np.sqrt(1 - zeta ** 2)
        return 1 - np.exp(-zeta * omega * t) * (np.cos(wd * t) + zeta * omega / wd * np.sin(wd * t))
    if zeta == 1.0:
        return 1 - np.exp(-omega * t) * (1 + omega * t)
    r = np.sqrt(zeta ** 2 - 1)
    s1, s2 = -omega * (zeta - r), -omega * (zeta + r)
    return 1 + (s2 * np.exp(s1 * t) - s1 * np.exp(s2 * t)) / (s1 - s2)


@dataclass
class EasingFit:
    start_frame: int
    end_frame: int
    from_value: float
    to_value: float
    family: str  # a NAMED key, "bezier" or "spring"
    bezier: tuple[float, float, float, float] | None
    spring: dict | None  # Remotion spring config {mass, damping, stiffness}
    rmse: float
    overshoot: float  # fraction past the end value (0.08 = 8 %)
    settle_frame: int | None
    samples: int
    evidence: str  # OBSERVED | ESTIMATED
    candidates: list[dict]

    def to_dict(self) -> dict:
        return asdict(self)

    def remotion(self) -> str:
        if self.family == "spring" and self.spring:
            s = self.spring
            return f"spring({{frame, fps, config: {{mass: {s['mass']}, damping: {s['damping']}, stiffness: {s['stiffness']}}}}})"
        x1, y1, x2, y2 = self.bezier or NAMED["linear"]
        return f"Easing.bezier({x1:.3f}, {y1:.3f}, {x2:.3f}, {y2:.3f})"


def _rmse(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.sqrt(np.mean((a - b) ** 2)))


def fit_segment(frames: np.ndarray, values: np.ndarray, fps: float, settle_tol: float = 0.02) -> EasingFit | None:
    frames = np.asarray(frames, dtype=np.float64)
    values = np.asarray(values, dtype=np.float64)
    if len(frames) < 3:
        return None
    v0, v1 = float(values[0]), float(values[-1])
    if abs(v1 - v0) < 1e-9:
        return None
    f0, f1 = float(frames[0]), float(frames[-1])
    u = (frames - f0) / (f1 - f0)
    p = (values - v0) / (v1 - v0)
    overshoot = max(0.0, float(p.max()) - 1.0)
    outside = np.nonzero(np.abs(p - 1.0) > settle_tol)[0]
    settle = int(frames[outside[-1] + 1]) if len(outside) and outside[-1] + 1 < len(frames) else (
        int(frames[0]) if not len(outside) else None)
    scored = sorted(((_rmse(bezier(u, *bz), p), name) for name, bz in NAMED.items()))
    best_rmse, best_name = scored[0]
    candidates = [{"family": n, "rmse": round(r, 4)} for r, n in scored[:3]]
    free = least_squares(lambda q: bezier(u, *q) - p, x0=np.array(NAMED[best_name], dtype=float),
                         bounds=([0, -1, 0, -1], [1, 2, 1, 2]))
    free_q = tuple(round(float(v), 4) for v in free.x)
    free_rmse = _rmse(bezier(u, *free_q), p)
    family, bz, rmse, spring_cfg = best_name, NAMED[best_name], best_rmse, None
    if free_rmse < 0.9 * best_rmse:  # a named family is preferred unless clearly worse
        family, bz, rmse = "bezier", free_q, free_rmse
    if overshoot > 0.02:  # a visible overshoot: test a spring against the best curve
        t_s = (frames - f0) / fps
        sp = least_squares(lambda q: spring_curve(t_s, q[0], q[1]) - p, x0=[0.5, 12.0],
                           bounds=([0.05, 1.0], [1.5, 200.0]))
        sp_rmse = _rmse(spring_curve(t_s, *sp.x), p)
        candidates.append({"family": "spring", "rmse": round(sp_rmse, 4)})
        if sp_rmse < rmse:
            zeta, omega = float(sp.x[0]), float(sp.x[1])
            family, bz, rmse = "spring", None, sp_rmse
            spring_cfg = {"mass": 1, "stiffness": round(omega ** 2, 2), "damping": round(2 * zeta * omega, 2)}
    evidence = "OBSERVED" if len(frames) >= 8 and rmse <= 0.03 else "ESTIMATED"
    return EasingFit(int(f0), int(f1), v0, v1, family, bz, spring_cfg, round(rmse, 4), round(overshoot, 4),
                     settle, len(frames), evidence, candidates)


def split_motion(frames: np.ndarray, values: np.ndarray, eps: float, min_hold: int = 2) -> list[tuple[int, int]]:
    """Index ranges [a, b] of moving segments, each starting at the last still sample before motion
    and ending at the first sample of the next hold (where the property is settled)."""
    v = np.asarray(values, dtype=np.float64)
    moving = np.abs(np.diff(v)) > eps
    segs, i, n = [], 0, len(moving)
    while i < n:
        if not moving[i]:
            i += 1
            continue
        a, j, still = i, i, 0
        while j < n:
            still = still + 1 if not moving[j] else 0
            if still >= min_hold:
                break
            j += 1
        b = min(len(v) - 1, j - still + 1)
        if b - a >= 2:
            segs.append((a, b))
        i = j + 1
    return segs
