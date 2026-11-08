"""Text tracks (W2 phase 1): per-frame text boxes linked into one track per text layer, then spec rows.

Two detectors, one contract (`Detection`): PaddleOCR (boxes + text, when installed) and an ink-box
fallback that needs no model (boxes only, text None). The track linker, the sub-pixel measurements and
the row builder do not care which one produced the boxes.

The recognised text is used for ALIGNMENT only (word counts, ASR matching). It never reaches the spec:
rows name a layer `text#N` and carry numbers, never the words (the reference's text is not copy).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

from . import easing
from .deps import available

# "still" thresholds per property
EPS = {"x": 0.4, "y": 0.4, "scale": 0.008, "opacity": 0.01, "rotation": 0.25}
MIN_AMP = {"x": 1.0, "y": 1.0, "scale": 0.03, "opacity": 0.05, "rotation": 1.5}  # smaller total change is jitter


@dataclass
class Detection:
    frame: int
    box: tuple[float, float, float, float]  # x0, y0, x1, y1 in analysis pixels (sub-pixel)
    text: str | None = None
    conf: float = 1.0

    @property
    def h(self) -> float:
        return self.box[3] - self.box[1]


@dataclass
class Track:
    id: int
    dets: list[Detection] = field(default_factory=list)
    opacity: dict[int, float] = field(default_factory=dict)

    @property
    def frames(self) -> list[int]:
        return [d.frame for d in self.dets]


# ---------------------------------------------------------------- detection

def _bg_color(rgb: np.ndarray) -> np.ndarray:
    q = (rgb // 16).reshape(-1, 3)
    key = (q[:, 0].astype(np.int32) << 8) | (q[:, 1].astype(np.int32) << 4) | q[:, 2]
    top = np.bincount(key).argmax()
    sel = rgb.reshape(-1, 3)[key == top]
    return np.median(sel, axis=0)


def _extent(profile: np.ndarray, floor: float = 0.04) -> tuple[float, float] | None:
    """Sub-pixel [start, end) of a coverage profile in [0, 1]: edge pixels count by their coverage."""
    idx = np.nonzero(profile > floor)[0]
    if not len(idx):
        return None
    i0, i1 = int(idx[0]), int(idx[-1])
    return i0 + (1.0 - min(1.0, float(profile[i0]) / max(float(profile[i0:i0 + 3].max()), 1e-6))), \
        i1 + min(1.0, float(profile[i1]) / max(float(profile[max(0, i1 - 2):i1 + 1].max()), 1e-6))


def coverage(rgb: np.ndarray, bg: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """(coverage in [0,1] per pixel, bg colour): colour distance from the background, normalised."""
    bg = _bg_color(rgb) if bg is None else bg
    d = np.sqrt(((rgb.astype(np.float32) - bg.astype(np.float32)) ** 2).sum(axis=2))
    return d, bg


def detect_ink(rgb: np.ndarray, frame: int, *, min_ink: float = 40.0) -> list[Detection]:
    """Model-free text-box detector: ink = colour far from the dominant background; letters are merged
    into lines by a horizontal close sized to the frame. Boxes only (text None). Sub-pixel edges."""
    d, _ = coverage(rgb)
    if d.max() < min_ink:
        return []
    cov = np.clip(d / max(float(d.max()), 1.0), 0, 1)
    ink = (d > min_ink * 0.5).astype(np.uint8)
    n0, _, st0, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    heights = [int(st0[i][3]) for i in range(1, n0) if st0[i][3] >= 6]
    k = max(5, int(1.2 * float(np.median(heights))) | 1) if heights else 5  # bridge gaps up to ~a letter height
    merged = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (k, 3)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(merged, connectivity=8)
    out = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if h < 6 or w < 6 or area < 30 or w < h * 0.9:  # text lines are wider than tall
            continue
        pad = 2
        y0, y1 = max(0, y - pad), min(rgb.shape[0], y + h + pad)
        x0, x1 = max(0, x - pad), min(rgb.shape[1], x + w + pad)
        sub = cov[y0:y1, x0:x1] * (ink[y0:y1, x0:x1] | (lab[y0:y1, x0:x1] == i))
        ex, ey = _extent(sub.max(axis=0)), _extent(sub.max(axis=1))
        if ex is None or ey is None:
            continue
        out.append(Detection(frame, (x0 + ex[0], y0 + ey[0], x0 + ex[1], y0 + ey[1])))
    return sorted(out, key=lambda t: (t.box[1], t.box[0]))


Box = tuple[float, float, float, float]


def refine_box(rgb: np.ndarray, box: Box, pad: int = 6) -> Box:
    """Snap a coarse OCR box to the ink inside it with sub-pixel edges (OCR boxes are padded and quantised;
    that quantisation would read as jitter in a scale or position track). Falls back to the input box."""
    H, W = rgb.shape[:2]
    x0, y0, x1, y1 = (int(max(0, box[0] - pad)), int(max(0, box[1] - pad)),
                      int(min(W, box[2] + pad)), int(min(H, box[3] + pad)))
    d, _ = coverage(rgb)
    sub = d[y0:y1, x0:x1]
    if sub.size == 0 or sub.max() < 40.0:
        return box
    cov = np.clip(sub / float(sub.max()), 0, 1)
    ex, ey = _extent(cov.max(axis=0)), _extent(cov.max(axis=1))
    if ex is None or ey is None:
        return box
    return (x0 + ex[0], y0 + ey[0], x0 + ex[1], y0 + ey[1])


def is_readable(text_: str | None) -> bool:
    """OCR also "reads" solid shapes as block glyphs (a filled square comes back as a full-block character).
    A detection with no letter or digit is a shape, not text, and must not become a text track."""
    return bool(text_) and any(ch.isalnum() for ch in text_)


MAX_TEXT_HEIGHT_FRAC = 0.35


def is_text_sized(box: Box, frame_h: float, max_frac: float = MAX_TEXT_HEIGHT_FRAC) -> bool:
    """A text line is never a third of the frame tall; OCR boxes that large sit on artwork, not on text."""
    return (box[3] - box[1]) <= max_frac * frame_h


def make_ocr_detector(lang: str = "en"):
    """PaddleOCR detector (boxes + text). Raises if the engine is missing: callers check `available`."""
    from paddleocr import PaddleOCR  # type: ignore

    ocr = PaddleOCR(lang=lang, use_textline_orientation=False, use_doc_orientation_classify=False,
                    use_doc_unwarping=False, enable_mkldnn=False)  # oneDNN path crashes on paddle 3.x CPU

    def detect(rgb: np.ndarray, frame: int) -> list[Detection]:
        res = ocr.predict(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        out = []
        for r in res:
            for poly, text, conf in zip(r["rec_polys"], r["rec_texts"], r["rec_scores"]):
                if not is_readable(str(text)):
                    continue
                pts = np.asarray(poly, dtype=np.float32)
                lo, hi = pts.min(axis=0), pts.max(axis=0)
                coarse = (float(lo[0]), float(lo[1]), float(hi[0]), float(hi[1]))
                if not is_text_sized(coarse, rgb.shape[0]):
                    continue
                out.append(Detection(frame, refine_box(rgb, coarse), str(text), float(conf)))
        return sorted(out, key=lambda t: (t.box[1], t.box[0]))

    return detect


def ocr_available() -> bool:
    return available("paddleocr")


# ---------------------------------------------------------------- linking

def _center(b):
    return (b[0] + b[2]) / 2, (b[1] + b[3]) / 2


def _compatible(a: str | None, b: str | None) -> bool:
    if a is None or b is None:
        return True
    a, b = a.strip().lower(), b.strip().lower()
    return a.startswith(b) or b.startswith(a) or a in b or b in a or _sim(a, b) >= 0.6


def _sim(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    common = sum(1 for x, y in zip(a, b) if x == y)
    return common / max(len(a), len(b))


def link(per_frame: list[list[Detection]], *, max_gap: int = 3, max_move_frac: float = 0.35) -> list[Track]:
    """Greedy nearest-box association. A detection joins the open track whose last box is closest (left edge
    or centre) when the height ratio stays within 0.5..2.0, the move is bounded, and the text is compatible.
    A track survives `max_gap` missed frames; a closed track never reopens (a re-entry is a new layer)."""
    tracks: list[Track] = []
    open_: list[Track] = []
    for f, dets in enumerate(per_frame):
        open_ = [t for t in open_ if f - t.dets[-1].frame <= max_gap + 1]
        used: set[int] = set()
        pairs = []
        for ti, t in enumerate(open_):
            last = t.dets[-1]
            for di, d in enumerate(dets):
                (cx, cy), (lx, ly) = _center(d.box), _center(last.box)
                dist = min(np.hypot(cx - lx, cy - ly), np.hypot(d.box[0] - last.box[0], d.box[1] - last.box[1]))
                lim = max(12.0, max_move_frac * max(last.h, 1.0) * 8)
                hr = d.h / max(last.h, 1e-6)
                if dist <= lim and 0.5 <= hr <= 2.0 and _compatible(d.text, last.text):
                    pairs.append((dist, ti, di))
        taken_t: set[int] = set()
        for dist, ti, di in sorted(pairs):
            if ti in taken_t or di in used:
                continue
            taken_t.add(ti)
            used.add(di)
            open_[ti].dets.append(dets[di])
        for di, d in enumerate(dets):
            if di not in used:
                t = Track(len(tracks), [d])
                tracks.append(t)
                open_.append(t)
    return tracks


# ---------------------------------------------------------------- measurements

def measure_opacity(track: Track, frames_rgb) -> None:
    """Opacity per frame = ink strength inside the box relative to the track's strongest frame (0..1).
    `frames_rgb[f]` is the RGB frame. The first frames of a fade-in read low, the held frames read 1."""
    raw = {}
    for d in track.dets:
        rgb = frames_rgb[d.frame]
        x0, y0, x1, y1 = (int(max(0, v)) for v in (d.box[0] - 1, d.box[1] - 1, d.box[2] + 2, d.box[3] + 2))
        reg = rgb[y0:y1, x0:x1]
        if reg.size == 0:
            continue
        bg = _bg_color(rgb)
        dist = np.sqrt(((reg.astype(np.float32) - bg.astype(np.float32)) ** 2).sum(axis=2))
        raw[d.frame] = float(np.percentile(dist, 98))
    top = max(raw.values(), default=0.0)
    track.opacity = {f: (v / top if top > 0 else 0.0) for f, v in raw.items()}


def series(track: Track) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Per-property (frames, values): x (left edge), y (top), scale (height / first height), opacity."""
    fr = np.array([d.frame for d in track.dets], dtype=np.float64)
    h0 = track.dets[0].h
    out = {
        "x": (fr, np.array([d.box[0] for d in track.dets])),
        "y": (fr, np.array([d.box[1] for d in track.dets])),
        "scale": (fr, np.array([d.h / h0 for d in track.dets])),
    }
    if track.opacity:
        f2 = np.array(sorted(track.opacity), dtype=np.float64)
        out["opacity"] = (f2, np.array([track.opacity[int(f)] for f in f2]))
    return out


def reveal_events(track: Track, *, min_step_frac: float = 0.12) -> list[dict]:
    """Frames where the line gets longer while its left edge holds: one event per word (or chunk) revealed.
    With OCR text the count of words is used; without, width steps of at least `min_step_frac` of the final
    width. Returns [{frame, words, width_px}] (words is the cumulative count, None without OCR)."""
    dets = track.dets
    if len(dets) < 2:
        return []
    w = np.array([d.box[2] - d.box[0] for d in dets])
    left = np.array([d.box[0] for d in dets])
    texts = [d.text for d in dets]
    events = []
    if all(t is not None for t in texts):
        prev = len(texts[0].split())
        for d, t in zip(dets[1:], texts[1:]):
            n = len(t.split())
            if n > prev:
                events.append({"frame": d.frame, "words": n, "width_px": round(d.box[2] - d.box[0], 2)})
            prev = max(prev, n)
        return ([{"frame": dets[0].frame, "words": len(texts[0].split()), "width_px": round(float(w[0]), 2)}]
                + events) if events else []
    thr = max(5.0, min_step_frac * float(w.max()))
    for i in range(1, len(dets)):
        if w[i] - w[i - 1] >= thr and abs(left[i] - left[i - 1]) <= 1.5:
            events.append({"frame": dets[i].frame, "words": None, "width_px": round(float(w[i]), 2)})
    if events:  # the first appearance is the first word of the reveal
        events.insert(0, {"frame": dets[0].frame, "words": None, "width_px": round(float(w[0]), 2)})
    return events


# ---------------------------------------------------------------- rows

def _fit_extended(fr: np.ndarray, val: np.ndarray, a: int, b: int, fps: float, eps: float, limit: int,
                  floor: int = 0):
    """split_motion ends a segment where the change drops below `eps`, which truncates the slow tail of an
    ease-out and the slow start of an ease-in. Try starting up to 12 samples earlier and ending up to 12 later
    (while the series stays inside the hold) and keep the best named/spring fit, so a truncated tail does not
    turn a standard family into a free bezier."""
    best = None
    starts = [a]
    for s in range(a - 1, max(floor, a - 12) - 1, -1):
        if abs(val[s] - val[a]) > 3 * eps * (a - s) + 4 * eps:
            break
        starts.append(s)
    for s in starts:
        for e in range(b, min(limit, b + 12) + 1):
            if e > b and abs(val[e] - val[b]) > 3 * eps * (e - b) + 4 * eps:
                break
            fit = easing.fit_segment(fr[s:e + 1], val[s:e + 1], fps)
            if fit is None:
                continue
            named = fit.family != "bezier"
            score = fit.rmse - (0.004 if named else 0.0)
            if best is None or score < best[0]:
                best = (score, fit)
    return best[1] if best else None


def rows_from_series(el: str, ser: dict[str, tuple[np.ndarray, np.ndarray]], fps: float, source: str,
                     min_amp: dict[str, float] | None = None) -> list[dict]:
    """Spec rows from per-property (frames, values) series: one row per moving segment."""
    amp = {**MIN_AMP, **(min_amp or {})}
    rows: list[dict] = []
    for prop, (fr, val) in ser.items():
        if len(fr) != int(fr[-1] - fr[0]) + 1:  # gaps: interpolate to the frame grid for the fit
            grid = np.arange(int(fr[0]), int(fr[-1]) + 1, dtype=np.float64)
            val, fr = np.interp(grid, fr, val), grid
        segs = easing.split_motion(fr, val, EPS[prop])
        for i, (a, b) in enumerate(segs):
            limit = segs[i + 1][0] - 1 if i + 1 < len(segs) else len(fr) - 1
            floor = segs[i - 1][1] + 1 if i else 0
            fit = _fit_extended(fr, val, a, b, fps, EPS[prop], max(b, limit), floor)
            if fit is None or abs(fit.to_value - fit.from_value) < amp[prop]:
                continue
            rows.append({"element": el, "property": prop, "start": fit.start_frame,
                         "duration": fit.end_frame - fit.start_frame, "from": round(fit.from_value, 3),
                         "to": round(fit.to_value, 3), "easing": fit.family,
                         "bezier": list(fit.bezier) if fit.bezier else None, "spring": fit.spring,
                         "rmse": fit.rmse, "overshoot": fit.overshoot, "evidence": fit.evidence,
                         "source": source})
    return rows


def track_rows(track: Track, fps: float, element: str | None = None) -> list[dict]:
    """Spec rows for one track: a row per moving segment of x/y/scale/opacity, plus reveal rows."""
    el = element or f"text#{track.id}"
    rows = rows_from_series(el, series(track), fps, "text")
    for i, ev in enumerate(reveal_events(track)):
        rows.append({"element": el, "property": "reveal", "start": ev["frame"], "duration": 0, "from": i,
                     "to": i + 1, "easing": "step", "bezier": None, "spring": None, "rmse": 0.0,
                     "overshoot": 0.0, "evidence": "OBSERVED", "source": "text", "width_px": ev["width_px"]})
    return rows


def align_reveals_to_words(rows: list[dict], asr_words: list[dict], fps: float, tol_s: float = 0.15) -> list[dict]:
    """Attach `asr_delta_ms` to each reveal row whose time lands within `tol_s` of an ASR word start.
    Only times are used; the words themselves are not copied. Unmatched reveals stay unmatched."""
    starts = np.array([w["start"] for w in asr_words if w.get("start") is not None], dtype=np.float64)
    out = []
    for r in rows:
        r = dict(r)
        if r["property"] == "reveal" and len(starts):
            t = r["start"] / fps
            j = int(np.abs(starts - t).argmin())
            delta = float(starts[j] - t)
            r["asr_aligned"] = abs(delta) <= tol_s
            r["asr_delta_ms"] = round(delta * 1000, 1) if r["asr_aligned"] else None
        out.append(r)
    return out


def track_text(frames_rgb, fps: float, *, detector=None, stride: int = 1) -> dict:
    """Detect -> link -> measure -> rows over decoded display-orientation RGB frames.
    `stride` > 1 runs the detector on every stride-th frame only (slow OCR); timing then resolves to `stride`
    frames, and the result says so. Returns {engine, status, stride, tracks, rows}."""
    engine = "paddleocr" if detector is None and ocr_available() else "ink"
    det = detector or (make_ocr_detector() if engine == "paddleocr" else detect_ink)
    n = len(frames_rgb)
    per_frame = [det(f, i) if i % stride == 0 or i == n - 1 else [] for i, f in enumerate(frames_rgb)]
    tracks = [t for t in link(per_frame, max_gap=max(3, stride)) if len(t.dets) >= 3]
    rows = []
    for t in tracks:
        measure_opacity(t, frames_rgb)
        rows += track_rows(t, fps)
    return {"engine": engine, "status": "OK" if engine == "paddleocr" else "DEGRADED_NO_OCR", "stride": stride,
            "tracks": [{"id": t.id, "first": t.dets[0].frame, "last": t.dets[-1].frame, "frames": len(t.dets),
                        "box": [round(float(v), 1) for v in t.dets[0].box]} for t in tracks], "rows": rows}
