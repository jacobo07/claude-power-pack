"""Layer tracks (W2 phase 2): per-element masks -> position, scale, rotation, opacity series -> spec rows.

One contract, two mask engines. A `MaskProvider` takes display-orientation RGB frames plus prompts (an object id,
a frame, a box) and returns one boolean mask stack per object:

- `ColorProvider`: model-free, for flat graphics (cards, bars, dots). Follows a colour from the prompt box and keeps the
  connected component that continues the previous one. This is what the synthetic gates run on.
- `Sam2Provider`: SAM 2 video predictor (Apache-2.0), prompted with the same boxes. Needs a GPU; the model is loaded
  for the call and freed after it. SAM 3 is not used here (GATED, see deps.py).

Everything after the masks (measurement, easing fit, rows) is engine-independent, so a gate proves it once.
An object the engine loses gives status LOST and NO rows: a missing object is never turned into a flat track.
"""

from __future__ import annotations

import gc
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import cv2
import numpy as np

from . import text
from .deps import available


# mask edges jitter by ~1-2 px (SAM 2 measured on the synthetic clip), so smaller moves are noise, not motion
LAYER_MIN_AMP = {"x": 2.5, "y": 2.5}


@dataclass(frozen=True)
class Prompt:
    obj: int
    frame: int
    box: tuple[float, float, float, float]  # x0, y0, x1, y1 in frame pixels


class MaskProvider(Protocol):
    name: str

    def __call__(self, frames: np.ndarray, prompts: list[Prompt]) -> dict[int, np.ndarray]: ...


# ---------------------------------------------------------------- engines

class ColorProvider:
    name = "color"

    def __init__(self, tol: float = 60.0, grow: int = 9):
        self.tol, self.grow = tol, grow

    def _one(self, frames: np.ndarray, p: Prompt, bg: np.ndarray) -> np.ndarray:
        T = len(frames)
        x0, y0, x1, y1 = (int(round(v)) for v in p.box)
        crop = frames[p.frame, max(0, y0):y1, max(0, x0):x1].reshape(-1, 3).astype(np.float32)
        far = np.linalg.norm(crop - bg, axis=1) > self.tol
        if not far.any():
            return np.zeros(frames.shape[:3], bool)
        color = np.median(crop[far], axis=0)
        out = np.zeros(frames.shape[:3], bool)
        k = cv2.getStructuringElement(cv2.MORPH_RECT, (self.grow, self.grow))
        for order in (range(p.frame, T), range(p.frame - 1, -1, -1)):
            prev = None
            for t in order:
                cand = (np.linalg.norm(frames[t].astype(np.float32) - color, axis=2) < self.tol).astype(np.uint8)
                if prev is None:  # seed: the component under the prompt box
                    box_mask = np.zeros_like(cand)
                    box_mask[max(0, y0):y1, max(0, x0):x1] = 1
                    anchor = cand & box_mask
                else:
                    anchor = cand & cv2.dilate(prev.astype(np.uint8), k)
                if not anchor.any():
                    break  # lost / not on screen yet (backward) / gone (forward)
                n, lab = cv2.connectedComponents(cand, connectivity=8)
                keep = np.unique(lab[anchor.astype(bool)])
                m = np.isin(lab, keep[keep > 0])
                out[t], prev = m, m
        return out

    def __call__(self, frames: np.ndarray, prompts: list[Prompt]) -> dict[int, np.ndarray]:
        bg = text._bg_color(frames[0]).astype(np.float32)
        return {p.obj: self._one(frames, p, bg) for p in prompts}


class Sam2Provider:
    name = "sam2"

    def __init__(self, checkpoint: str, config: str = "configs/sam2.1/sam2.1_hiera_s.yaml", device: str = "cuda"):
        self.checkpoint, self.config, self.device = checkpoint, config, device

    def __call__(self, frames: np.ndarray, prompts: list[Prompt]) -> dict[int, np.ndarray]:
        import torch
        from sam2.build_sam import build_sam2_video_predictor  # type: ignore

        out = {p.obj: np.zeros(frames.shape[:3], bool) for p in prompts}
        predictor = build_sam2_video_predictor(self.config, self.checkpoint, device=self.device)
        try:
            with tempfile.TemporaryDirectory() as d:
                for i, f in enumerate(frames):
                    cv2.imwrite(str(Path(d) / f"{i:05d}.jpg"), cv2.cvtColor(f, cv2.COLOR_RGB2BGR),
                                [cv2.IMWRITE_JPEG_QUALITY, 98])
                with torch.inference_mode(), torch.autocast(self.device, dtype=torch.bfloat16):
                    state = predictor.init_state(video_path=d)
                    for p in prompts:
                        predictor.add_new_points_or_box(state, frame_idx=p.frame, obj_id=p.obj,
                                                        box=np.array(p.box, dtype=np.float32))
                    for reverse in (False, True):
                        for fi, ids, logits in predictor.propagate_in_video(state, reverse=reverse):
                            for j, oid in enumerate(ids):
                                out[int(oid)][fi] |= (logits[j, 0] > 0).cpu().numpy()
        finally:
            del predictor
            gc.collect()
            torch.cuda.empty_cache()
        return out


def default_provider(checkpoint: str | None = None) -> MaskProvider:
    """SAM 2 when installed and a checkpoint is given, else the colour follower (explicit via `.name`)."""
    if checkpoint and available("sam2"):
        return Sam2Provider(checkpoint)
    return ColorProvider()


def shot_prompts(frame: np.ndarray, text_boxes: list[tuple[float, float, float, float]] | None = None, *,
                 min_area_frac: float = 0.002, max_frac: float = 0.6, limit: int = 8,
                 first_obj: int = 0) -> list[Prompt]:
    """Prompt boxes from a shot-start frame: connected non-background components that are not text and not the
    backdrop. Components inside an OCR/ink text box are skipped (text is tracked by its own stage)."""
    d, _ = text.coverage(frame)
    mask = (d > 40.0).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)))
    n, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    h, w = mask.shape
    out = []
    for i in range(1, n):
        x, y, bw, bh, area = (int(v) for v in stats[i])
        if area < min_area_frac * h * w or bw * bh > max_frac * h * w:
            continue
        box = (float(x), float(y), float(x + bw), float(y + bh))
        if any(_contains(tb, box) for tb in (text_boxes or [])):
            continue
        out.append((area, box))
    out.sort(key=lambda t: -t[0])
    return [Prompt(first_obj + k, 0, b) for k, (_, b) in enumerate(out[:limit])]


def _contains(outer, inner, frac: float = 0.7) -> bool:
    ix0, iy0 = max(outer[0], inner[0]), max(outer[1], inner[1])
    ix1, iy1 = min(outer[2], inner[2]), min(outer[3], inner[3])
    inter = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
    return inter >= frac * max(1e-6, (inner[2] - inner[0]) * (inner[3] - inner[1]))


# ---------------------------------------------------------------- measurement

def _orientation(mask: np.ndarray) -> tuple[float, float] | None:
    """(angle in degrees mod 180, eccentricity 0..1) from second moments, or None for a speck."""
    m = cv2.moments(mask.astype(np.uint8), binaryImage=True)
    if m["m00"] < 12:
        return None
    mu20, mu02, mu11 = m["mu20"] / m["m00"], m["mu02"] / m["m00"], m["mu11"] / m["m00"]
    ang = 0.5 * np.degrees(np.arctan2(2 * mu11, mu20 - mu02))
    l1 = (mu20 + mu02) / 2 + np.sqrt(((mu20 - mu02) / 2) ** 2 + mu11 ** 2)
    l2 = (mu20 + mu02) / 2 - np.sqrt(((mu20 - mu02) / 2) ** 2 + mu11 ** 2)
    return float(ang % 180.0), float((l1 - l2) / max(l1 + l2, 1e-9))


def measure(frames: np.ndarray, masks: np.ndarray, bg: np.ndarray, *, min_ecc: float = 0.2):
    """Series for one object: {x, y (centroid), scale (sqrt area ratio to the first fully visible size),
    rotation (deg, unwrapped, only for elongated shapes), opacity (ink contrast, relative to the strongest)}."""
    fr, cx, cy, area, ang, contrast = [], [], [], [], [], []
    for t in range(len(masks)):
        if masks[t].sum() < 12:
            continue
        m = masks[t].astype(np.uint8)
        mom = cv2.moments(m, binaryImage=True)
        fr.append(t)
        cx.append(mom["m10"] / mom["m00"])
        cy.append(mom["m01"] / mom["m00"])
        area.append(mom["m00"])
        o = _orientation(m)
        ang.append(o if o and o[1] >= min_ecc else None)
        core = cv2.erode(m, np.ones((3, 3), np.uint8)).astype(bool)
        core = core if core.any() else m.astype(bool)
        contrast.append(float(np.linalg.norm(frames[t][core].astype(np.float32) - bg, axis=1).mean()))
    if len(fr) < 3:
        return {}
    f = np.array(fr, dtype=np.float64)
    a = np.array(area)
    ref = a[0]
    out = {"x": (f, np.array(cx)), "y": (f, np.array(cy)), "scale": (f, np.sqrt(a / ref))}
    ok = [i for i, v in enumerate(ang) if v is not None]
    if len(ok) >= 3 and len(ok) == len(ang):
        deg = np.degrees(np.unwrap(np.radians([2 * ang[i][0] for i in ok]))) / 2  # period 180 -> unwrap on doubled
        out["rotation"] = (f[ok], deg - deg[0])
    c = np.array(contrast)
    if c.max() > 0:
        out["opacity"] = (f, c / c.max())
    return out


def track_layers(frames: np.ndarray, fps: float, prompts: list[Prompt], provider: MaskProvider | None = None) -> dict:
    """Masks -> series -> rows for each prompted object. Returns {engine, status, objects, rows}.
    Object status: OK, or LOST when the engine returned (almost) no mask for it (no rows are invented)."""
    provider = provider or ColorProvider()
    masks = provider(frames, prompts)
    bg = text._bg_color(frames[0]).astype(np.float32)
    rows, objects = [], []
    for p in prompts:
        m = masks[p.obj]
        n_on = int((m.reshape(len(m), -1).sum(axis=1) >= 12).sum())
        if n_on < 3:
            objects.append({"element": f"layer#{p.obj}", "status": "LOST", "frames": n_on})
            continue
        ser = measure(frames, m, bg)
        el = f"layer#{p.obj}"
        first = int(np.nonzero(m.reshape(len(m), -1).sum(axis=1) >= 12)[0][0])
        last = int(np.nonzero(m.reshape(len(m), -1).sum(axis=1) >= 12)[0][-1])
        objects.append({"element": el, "status": "OK", "frames": n_on, "first": first, "last": last})
        rows += text.rows_from_series(el, ser, fps, "layer", LAYER_MIN_AMP)
    return {"engine": provider.name, "status": "OK", "objects": objects, "rows": rows}
