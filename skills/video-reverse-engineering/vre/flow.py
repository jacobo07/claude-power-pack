"""Flow summaries (W2 phase 2): RAFT optical flow (torchvision, BSD-3) reduced to a few numbers per shot.

Particle fields, drifting backgrounds and spinning objects are not worth tracking one by one. A shot's flow
is summarised as a mean translation, a speed spread, a dominant direction, a rotation rate (curl) and a zoom
rate (divergence), per frame pair and as a shot median. The model is loaded for the call and freed after it
(the GPU is shared). CoTracker is excluded (non-commercial weights); see deps.py.
"""

from __future__ import annotations

import gc

import numpy as np


def compute(frames: np.ndarray, *, stride: int = 1, batch: int = 4, device: str | None = None) -> np.ndarray:
    """Flow (T-1, 2, H, W) in pixels per `stride` frames between consecutive sampled frames (dx, dy)."""
    import torch
    from torchvision.models.optical_flow import Raft_Small_Weights, raft_small

    dev = device or ("cuda" if torch.cuda.is_available() else "cpu")
    model = raft_small(weights=Raft_Small_Weights.DEFAULT).to(dev).eval()
    h, w = frames.shape[1:3]
    hh, ww = h - h % 8, w - w % 8
    x = torch.from_numpy(np.ascontiguousarray(frames[::stride, :hh, :ww])).permute(0, 3, 1, 2).float() / 255.0
    x = x * 2 - 1
    out = []
    try:
        with torch.inference_mode():
            for i in range(0, len(x) - 1, batch):
                a, b = x[i:i + batch], x[i + 1:i + 1 + batch]
                n = min(len(a), len(b))
                out.append(model(a[:n].to(dev), b[:n].to(dev))[-1].float().cpu())
    finally:
        del model
        gc.collect()
        if dev == "cuda":
            torch.cuda.empty_cache()
    return torch.cat(out).numpy() if out else np.zeros((0, 2, hh, ww), np.float32)


def summarize(flow: np.ndarray, *, still_px: float = 0.15) -> dict:
    """Per-pair numbers, then the shot median. Units: px per sampled frame, degrees per sampled frame."""
    pairs = []
    for fl in flow:
        dx, dy = fl[0], fl[1]
        mag = np.hypot(dx, dy)
        gy, gx = np.gradient(dy, axis=0), np.gradient(dx, axis=1)  # dvy/dy, dvx/dx
        dydx, dxdy = np.gradient(dy, axis=1), np.gradient(dx, axis=0)
        curl = float(np.median(dydx - dxdy) / 2)  # rad per frame (solid-body rotation: curl/2)
        div = float(np.median(gx + gy) / 2)
        mx, my = float(np.median(dx)), float(np.median(dy))
        pairs.append({"mean_dx": mx, "mean_dy": my, "speed_p50": float(np.median(mag)),
                      "speed_p90": float(np.percentile(mag, 90)), "rotation_deg": float(np.degrees(curl)),
                      "zoom_rate": div, "moving_frac": float((mag > still_px).mean())})
    if not pairs:
        return {"pairs": 0}
    med = {k: round(float(np.median([p[k] for p in pairs])), 4) for k in pairs[0]}
    direction = float(np.degrees(np.arctan2(med["mean_dy"], med["mean_dx"])))
    return {"pairs": len(pairs), "median": med, "direction_deg": round(direction, 1),
            "per_pair": [{k: round(v, 4) for k, v in p.items()} for p in pairs]}


def shot_flow(frames: np.ndarray, **kw) -> dict:
    """Flow summary for a shot's frames; `status` is explicit when torch/torchvision are missing."""
    try:
        fl = compute(frames, **kw)
    except ImportError as e:
        return {"status": "UNAVAILABLE", "reason": str(e)}
    return {"status": "OK", "engine": "raft_small", **summarize(fl)}
