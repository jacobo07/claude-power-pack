"""Per-shot palette in CIELAB with roles (background, surface, accent, text) and brand mapping.

Idea absorbed from motion2code's palette.py (exact flat colours) and extended with role assignment so
a rebrand maps colours by FUNCTION, not by hue: the source's accent becomes the brand's accent.
"""

from __future__ import annotations

import cv2
import numpy as np


def _hex(rgb: np.ndarray) -> str:
    r, g, b = (int(v) for v in rgb)
    return f"#{r:02X}{g:02X}{b:02X}"


def _rel_luminance(rgb: np.ndarray) -> float:
    c = rgb.astype(np.float64) / 255.0
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return float(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])


def contrast(a: np.ndarray, b: np.ndarray) -> float:
    la, lb = sorted((_rel_luminance(a), _rel_luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def shot_palette(thumbs: list[np.ndarray], k: int = 5, max_pixels: int = 40000, seed: int = 7,
                 min_share: float = 0.004) -> dict:
    """min_share: a small accent (a 16 px badge is ~1 % of a reel frame) must still count as a colour."""
    pixels = np.concatenate([t.reshape(-1, 3) for t in thumbs], axis=0)
    rng = np.random.default_rng(seed)
    if len(pixels) > max_pixels:
        pixels = pixels[rng.choice(len(pixels), max_pixels, replace=False)]
    lab = cv2.cvtColor(pixels.reshape(-1, 1, 3), cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)
    k = int(min(k, max(1, len(np.unique(lab, axis=0)))))
    cv2.setRNGSeed(seed)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    _, labels, centers = cv2.kmeans(lab, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    shares = np.bincount(labels.ravel(), minlength=k) / len(labels)
    rgb = cv2.cvtColor(np.clip(centers, 0, 255).astype(np.uint8).reshape(-1, 1, 3), cv2.COLOR_LAB2RGB).reshape(-1, 3)
    chroma = np.hypot(centers[:, 1] - 128.0, centers[:, 2] - 128.0)
    order = np.argsort(-shares)
    colours = [{"hex": _hex(rgb[i]), "share": round(float(shares[i]), 4), "chroma": round(float(chroma[i]), 1)}
               for i in order]
    bg = int(order[0])
    rest = [int(i) for i in order[1:] if shares[i] >= min_share]
    roles: dict[str, str | None] = {"background": _hex(rgb[bg]), "surface": None, "accent": None, "text": None}
    # accent = the most saturated colour; text = the most contrasting NEAR-NEUTRAL colour (a saturated
    # high-contrast colour is an accent, not body text); surface = the largest remaining colour.
    used: set[int] = set()
    vivid = [i for i in rest if chroma[i] >= 25]
    if vivid:
        accent = max(vivid, key=lambda i: chroma[i] * np.sqrt(shares[i]))
        roles["accent"], _ = _hex(rgb[accent]), used.add(accent)
    neutral = [i for i in rest if i not in used and chroma[i] < 25 and contrast(rgb[i], rgb[bg]) >= 3.0]
    if neutral:
        text = max(neutral, key=lambda i: contrast(rgb[i], rgb[bg]))
        roles["text"], _ = _hex(rgb[text]), used.add(text)
    surface = [i for i in rest if i not in used]
    if surface:
        roles["surface"] = _hex(rgb[surface[0]])
    return {"colours": colours, "roles": roles, "background_luma": round(_rel_luminance(rgb[bg]), 4),
            "polarity": "light" if _rel_luminance(rgb[bg]) > 0.4 else "dark"}


def map_to_brand(roles: dict, polarity: str, brand: dict) -> dict:
    """brand = {"light": {background, surface, accent, text}, "dark": {...}}; unknown roles stay None."""
    target = brand.get(polarity) or {}
    return {role: (target.get(role) if src is not None else None) for role, src in roles.items()}
