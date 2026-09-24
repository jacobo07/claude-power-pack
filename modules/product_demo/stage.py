"""Stage: compose captured product frames into a presentation, as an HTML page
that implements the motion-promo film contract (window.__ready, window.__meta,
async window.__renderFrame(i)). skills/motion-promo/scripts/render_film.py then
renders it unchanged -- one encoder, one frame-stepping harness, no fork.

Layout (screen rect, frame chrome, callout rects) is computed HERE, in Python, so
the validator can check it without a browser: a callout must sit inside the
screen and its pointer must land inside the element it names.
"""
from __future__ import annotations

import json
from pathlib import Path

ASSET = Path(__file__).with_name("assets") / "stage.template.html"

# Output canvas per stage; the product screen is fitted inside with its own aspect.
CANVAS = {"laptop": (1920, 1080), "browser": (1920, 1080), "raw": (1920, 1080), "phone": (1080, 1920)}
SCREEN_BOX = {   # max area the product screen may occupy, as (x, y, w, h) fractions of the canvas
    "laptop": (0.13, 0.07, 0.74, 0.76),
    "browser": (0.08, 0.12, 0.84, 0.80),
    "raw": (0.0, 0.0, 1.0, 1.0),
    "phone": (0.12, 0.08, 0.76, 0.84),
}
CALLOUT_FONT_PX = 26
CALLOUT_PAD, CALLOUT_GAP = 18, 16


def screen_rect(stage: str, vp_w: int, vp_h: int) -> dict:
    cw, ch = CANVAS[stage]
    fx, fy, fw, fh = SCREEN_BOX[stage]
    bx, by, bw, bh = fx * cw, fy * ch, fw * cw, fh * ch
    scale = min(bw / vp_w, bh / vp_h)
    w, h = vp_w * scale, vp_h * scale
    return {"x": round(bx + (bw - w) / 2, 2), "y": round(by + (bh - h) / 2, 2),
            "w": round(w, 2), "h": round(h, 2), "scale": scale}


def _overlap(a: tuple, b: tuple) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return max(0.0, min(ax + aw, bx + bw) - max(ax, bx)) * max(0.0, min(ay + ah, by + bh) - max(ay, by))


def callout_rect(box: dict, text: str, n: int, scr: dict, avoid: list | None = None) -> dict:
    """Place a numbered callout next to its target, clamped to the screen, choosing
    among above / below / right / left the spot that hides the least REAL product
    text (avoid = text boxes measured at capture). A spot covering the target
    itself is never chosen. Returns the rect plus the pointer, which must land on
    the target."""
    s = scr["scale"]
    tx, ty = scr["x"] + box["x"] * s, scr["y"] + box["y"] * s
    tw, th = box["width"] * s, box["height"] * s
    # Width estimate: ~0.56 em per glyph + badge + padding; the stage JS renders at
    # this exact width, so Python and the render agree on geometry.
    w = min(scr["w"] - 16, len(text) * CALLOUT_FONT_PX * 0.56 + 2 * CALLOUT_PAD + 44)
    h = CALLOUT_FONT_PX + 2 * CALLOUT_PAD - 4
    lo_x, hi_x = scr["x"] + 8, scr["x"] + scr["w"] - 8 - w
    lo_y, hi_y = scr["y"] + 8, scr["y"] + scr["h"] - 8 - h
    clamp = lambda v, lo, hi: max(lo, min(v, hi))  # noqa: E731
    cx = clamp(tx + tw / 2 - w / 2, lo_x, hi_x)
    cands = [("right", tx + tw + CALLOUT_GAP, clamp(ty + th / 2 - h / 2, lo_y, hi_y), 0.0),
             ("left", tx - CALLOUT_GAP - w, clamp(ty + th / 2 - h / 2, lo_y, hi_y), 0.0)]
    # Above/below may step away in half-height increments (joined to the target by a
    # leader line) until they stop covering real product text.
    for k in range(5):
        off = k * h * 0.6
        cands.append(("above", cx, ty - CALLOUT_GAP - h - off, off))
        cands.append(("below", cx, ty + th + CALLOUT_GAP + off, off))
    texts = [(scr["x"] + b["x"] * s, scr["y"] + b["y"] * s, b["width"] * s, b["height"] * s)
             for b in (avoid or [])]
    target = (tx, ty, tw, th)
    best = None
    for order, (side, x, y, off) in enumerate(cands):
        fits = lo_x <= x <= hi_x and lo_y <= y <= hi_y
        rect = (x, y, w, h)
        if not fits or _overlap(rect, target) > 0:
            continue
        hidden = sum(_overlap(rect, t) for t in texts)
        key = (round(hidden), off, order)
        if best is None or key < best[0]:
            best = (key, side, x, y, hidden)
    if best is None:   # nothing fits cleanly: fall back to a clamped spot above, and say so
        side, x, y, hidden = "above", cx, clamp(ty - CALLOUT_GAP - h, lo_y, hi_y), None
    else:
        _, side, x, y, hidden = best
    if side in ("above", "below"):
        ptr = {"x": round(max(x + 22, min(tx + tw / 2, x + w - 22)), 1),
               "y": round(y + h if side == "above" else y, 1)}
    else:
        ptr = {"x": round(x if side == "right" else x + w, 1),
               "y": round(max(y + 14, min(ty + th / 2, y + h - 14)), 1)}
    anchor = {"above": {"x": ptr["x"], "y": round(ty, 1)}, "below": {"x": ptr["x"], "y": round(ty + th, 1)},
              "right": {"x": round(tx + tw, 1), "y": ptr["y"]}, "left": {"x": round(tx, 1), "y": ptr["y"]}}[side]
    return {"n": n, "x": round(x, 1), "y": round(y, 1), "w": round(w, 1), "h": round(h, 1),
            "side": side, "pointer": ptr, "anchor": anchor,
            "hidden_text_px": None if hidden is None else round(hidden, 1),
            "target": {"x": round(tx, 1), "y": round(ty, 1), "w": round(tw, 1), "h": round(th, 1)}}


def compose(timeline: dict, capture_dir: Path, *, stage: str, fps: int, title: str,
            accent: str, host: str = "") -> Path:
    """Write <capture_dir>/stage_<viewport>.html next to its frames/ and return it."""
    vp = timeline["viewport"]
    scr = screen_rect(stage, vp["width"], vp["height"])
    cw, ch = CANVAS[stage]
    callouts = []
    for c in timeline["callouts"]:
        r = callout_rect(c["box"], c["text"], c["n"], scr, c.get("avoid"))
        r.update(text=c["text"], start_ms=c["start_ms"], end_ms=c["end_ms"], step=c["step"])
        callouts.append(r)
    frames = int(round(timeline["duration_ms"] / 1000 * fps))
    data = {
        "title": title, "stage": stage, "w": cw, "h": ch, "fps": fps, "frames": frames,
        "duration": timeline["duration_ms"] / 1000, "screen": scr, "accent": accent, "host": host,
        "segments": timeline["segments"], "cursor": timeline["cursor"], "callouts": callouts,
        "dsf": vp.get("dsf", 1),
    }
    html = ASSET.read_text(encoding="utf-8").replace("/*__DATA__*/null", json.dumps(data))
    out = capture_dir / f"stage_{vp['name']}.html"
    out.write_text(html, encoding="utf-8")
    (capture_dir / f"stage_{vp['name']}.layout.json").write_text(
        json.dumps({"screen": scr, "canvas": [cw, ch], "callouts": callouts}, indent=2), encoding="utf-8")
    return out
