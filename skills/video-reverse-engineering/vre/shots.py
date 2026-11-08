"""Shot boundaries, fades and flashes from one streaming pass of per-frame features.

The detector is adaptive (a cut must stand out against its own neighbourhood, the idea behind
PySceneDetect's AdaptiveDetector), so fast motion inside a shot does not read as a cut. Near-threshold
frames are returned as CANDIDATES: the workflow says to read those frames before trusting the list.
When PySceneDetect is installed, `cross_check` reports where the two detectors disagree.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class Cut:
    frame: int  # first frame of the new shot
    kind: str  # hard | fade_black | fade_white
    score: float
    ratio: float
    confidence: str  # high | medium
    luma_before: float
    luma_after: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Shot:
    index: int
    start: int
    end: int  # inclusive

    @property
    def length(self) -> int:
        return self.end - self.start + 1

    def to_dict(self) -> dict:
        return {"index": self.index, "start": self.start, "end": self.end, "length": self.length}


class FeatureAccumulator:
    """Collects the small per-frame features every later stage needs (one decode pass)."""

    def __init__(self, thumb_width: int = 72) -> None:
        self.thumb_width = thumb_width
        self.hist: list[np.ndarray] = []
        self.grid: list[np.ndarray] = []
        self.luma: list[float] = []
        self.thumbs: list[np.ndarray] = []

    def add(self, rgb: np.ndarray) -> None:
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
        hist = cv2.calcHist([hsv], [0, 1, 2], None, [12, 4, 4], [0, 180, 0, 256, 0, 256]).ravel()
        self.hist.append(hist / max(hist.sum(), 1.0))
        y = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        self.grid.append(cv2.resize(y, (8, 8), interpolation=cv2.INTER_AREA).astype(np.float32).ravel())
        self.luma.append(float(y.mean()))
        h = max(2, int(round(self.thumb_width * rgb.shape[0] / rgb.shape[1])))
        self.thumbs.append(cv2.resize(rgb, (self.thumb_width, h), interpolation=cv2.INTER_AREA))

    def arrays(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        return np.asarray(self.hist), np.asarray(self.grid), np.asarray(self.luma)


def frame_scores(hist: np.ndarray, grid: np.ndarray) -> np.ndarray:
    """Change score in [0, 1] between each frame and the previous one (frame 0 scores 0)."""
    d_hist = 0.5 * np.abs(np.diff(hist, axis=0)).sum(axis=1)  # total-variation distance
    d_grid = np.minimum(1.0, np.abs(np.diff(grid, axis=0)).mean(axis=1) / 64.0)
    return np.concatenate([[0.0], 0.5 * d_hist + 0.5 * d_grid])


def _runs(mask: np.ndarray, min_len: int) -> list[tuple[int, int]]:
    runs, start = [], None
    for i, flag in enumerate(mask):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            if i - start >= min_len:
                runs.append((start, i - 1))
            start = None
    if start is not None and len(mask) - start >= min_len:
        runs.append((start, len(mask) - 1))
    return runs


FADE_RAMP = 6.0  # luma levels between the 4 frames before and after a fade edge


def detect(hist: np.ndarray, grid: np.ndarray, luma: np.ndarray, fps: float, *, ratio: float = 3.0,
           floor: float = 0.12, min_shot: int = 4, black: float = 14.0, white: float = 242.0
           ) -> tuple[list[Cut], list[Shot], list[dict]]:
    n = len(luma)
    score = frame_scores(hist, grid)
    half = max(2, int(round(fps / 3)))
    cuts: list[Cut] = []
    candidates: list[dict] = []
    for i in range(1, n):
        lo, hi = max(1, i - half), min(n, i + half + 1)
        neigh = np.concatenate([score[lo:i], score[i + 1:hi]])
        local = float(np.median(neigh)) if neigh.size else 0.0
        r = score[i] / (local + 1e-3)
        if score[i] >= floor and r >= ratio:
            conf = "high" if (r >= 2 * ratio and score[i] >= 2 * floor) else "medium"
            cuts.append(Cut(i, "hard", round(float(score[i]), 4), round(float(r), 2), conf,
                            round(float(luma[i - 1]), 1), round(float(luma[i]), 1)))
        elif score[i] >= 0.6 * floor and r >= 0.6 * ratio:
            candidates.append({"frame": i, "score": round(float(score[i]), 4), "ratio": round(float(r), 2),
                               "why": "near threshold: read frames before trusting the cut list"})
    # fades through black / white: the run becomes its own boundary at both ends
    for kind, mask in (("fade_black", luma <= black), ("fade_white", luma >= white)):
        for a, b in _runs(mask, 2):
            for edge in (a, b + 1):
                # a real fade has a luma ramp at its edge; a bright shot whose mean hovers at the threshold does not
                ramp = abs(float(luma[max(0, edge - 4):edge].mean()) - float(luma[edge:edge + 4].mean()))
                if 0 < edge < n and ramp >= FADE_RAMP and not any(abs(c.frame - edge) <= 2 for c in cuts):
                    cuts.append(Cut(edge, kind, round(float(score[edge]), 4), 0.0, "medium",
                                    round(float(luma[edge - 1]), 1), round(float(luma[edge]), 1)))
    cuts.sort(key=lambda c: c.frame)
    kept: list[Cut] = []
    for c in cuts:  # enforce a minimum shot length, keeping the stronger boundary
        if kept and c.frame - kept[-1].frame < min_shot:
            if c.score > kept[-1].score:
                kept[-1] = c
            continue
        kept.append(c)
    bounds = [0] + [c.frame for c in kept] + [n]
    shots = [Shot(k, bounds[k], bounds[k + 1] - 1) for k in range(len(bounds) - 1) if bounds[k + 1] > bounds[k]]
    return kept, shots, candidates


def cross_check(path: str, cuts: list[Cut], tolerance: int = 2) -> dict:
    """Compare with PySceneDetect's AdaptiveDetector when it is installed."""
    try:
        from scenedetect import AdaptiveDetector, detect as sd_detect  # type: ignore
    except ImportError:
        return {"status": "UNAVAILABLE", "reason": "scenedetect not installed (pip install scenedetect)"}
    scenes = sd_detect(path, AdaptiveDetector())
    theirs = sorted(s[0].get_frames() for s in scenes[1:])
    ours = [c.frame for c in cuts]
    only_ours = [f for f in ours if not any(abs(f - t) <= tolerance for t in theirs)]
    only_theirs = [t for t in theirs if not any(abs(f - t) <= tolerance for f in ours)]
    return {"status": "OK", "pyscenedetect_cuts": theirs, "only_ours": only_ours, "only_pyscenedetect": only_theirs,
            "note": "read the frames at every disagreement before choosing"}
