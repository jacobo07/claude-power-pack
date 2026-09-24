"""Timeline: capture telemetry -> presentation time, cursor path, callouts.

Pure and deterministic: same telemetry + same Output settings = same timeline.

Temporal honesty, stated as rules the code enforces:
- Presentation may COMPRESS real time; it records every compression per segment
  (real_ms vs presented_ms) so the manifest can say exactly what was sped up.
- System work (frames captured while the product was working) is never shown
  faster than MAX_WORK_COMPRESSION x real time. Showing a 6 s generation as
  instantaneous would misrepresent the product.
- The synthetic cursor ends every move at the centre of the element the real
  interaction targeted, measured at capture time, and the click emphasis sits at
  the recorded click point -- the cursor cannot point somewhere the event did not go.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

MAX_WORK_COMPRESSION = 3.0      # system-work segments: at most 3x faster than real
CURSOR_TRAVEL_MS = 650
CLICK_DWELL_MS = 180
AFTER_MS = 420
MIN_FRAME_MS = 140
READ_MS_BASE, READ_MS_PER_CHAR = 600, 45   # callout legibility floor


@dataclass
class Segment:
    frame: str
    step: str
    kind: str
    start_ms: int
    dur_ms: int
    real_ms: int | None          # real time this frame stood for (None = not measured)


@dataclass
class Timeline:
    viewport: dict
    segments: list = field(default_factory=list)
    cursor: list = field(default_factory=list)      # {t_ms, x, y, click}
    callouts: list = field(default_factory=list)    # {n, step, text, start_ms, end_ms, box}
    duration_ms: int = 0
    compressions: list = field(default_factory=list)
    defects: list = field(default_factory=list)     # {class, detail, step}

    def to_dict(self) -> dict:
        d = asdict(self)
        d["segments"] = [asdict(s) for s in self.segments]
        return d


def read_ms(text: str) -> int:
    return READ_MS_BASE + READ_MS_PER_CHAR * len(text)


def build(telemetry: dict, output: dict, hold_overrides: dict | None = None) -> Timeline:
    """hold_overrides: {step_id: extra_ms}, applied by the bounded revision loop."""
    if telemetry.get("outcome") != "ok":
        raise ValueError(f"cannot build a timeline from a {telemetry.get('outcome')} capture: "
                         f"{telemetry.get('refusal')}")
    extra = hold_overrides or {}
    default_hold = int(output.get("default_hold_ms", 1400))
    per_char = int(output.get("typing_ms_per_char", 45))
    vp = telemetry["viewport"]
    tl = Timeline(viewport=vp)
    t = 0
    cursor_xy = (vp["width"] * 0.62, vp["height"] * 0.72)   # rest position, lower right of centre
    tl.cursor.append({"t_ms": 0, "x": round(cursor_xy[0], 1), "y": round(cursor_xy[1], 1), "click": False})
    n_callout = 0

    filmed = [s for s in telemetry["steps"] if s["film"] and s["frames"]]
    for si, step in enumerate(filmed):
        frames = step["frames"]
        tgt = step.get("target")
        centre = None
        if tgt:
            b = tgt["box"]
            centre = (b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
        step_start = t
        prev_chars = 0
        # A click/press can change the page: its "after" frame may show a different
        # screen where the measured target no longer is. A callout for it must end
        # at the click. Measured on the first real product demo: the callout stayed
        # into the next page and outlined an empty area -- a wrong-target callout.
        navigating_callout = bool(step.get("callout") and tgt) and step["do"] in ("click", "press")
        before_end = None
        for fi, fr in enumerate(frames):
            nxt = frames[fi + 1]["t_ms"] if fi + 1 < len(frames) else step.get("t_end_ms", fr["t_ms"])
            real = max(0, nxt - fr["t_ms"])
            kind = fr["kind"]
            if kind == "arrive":
                dur = default_hold
            elif kind == "before":
                dur = CURSOR_TRAVEL_MS + CLICK_DWELL_MS if centre else MIN_FRAME_MS
            elif kind.startswith("typing"):
                upto = int(kind[len("typing"):] or 0)
                dur = max(MIN_FRAME_MS, (upto - prev_chars) * per_char)
                prev_chars = upto
            elif kind == "working":
                dur = max(MIN_FRAME_MS * 2, int(real / 2))
            elif kind == "result":
                dur = int(default_hold * 1.5)
            else:   # "after"
                dur = AFTER_MS
            last = fi == len(frames) - 1
            if last and step.get("hold_ms"):
                dur = max(dur, int(step["hold_ms"]))
            # Revision time goes on the frame the callout is actually shown on: for a
            # navigating step that is the pre-click frame, not the next page.
            if (kind == "before") if navigating_callout else last:
                dur += int(extra.get(step["id"], 0))
            if kind == "working" and real and dur * MAX_WORK_COMPRESSION < real:
                dur = int(real / MAX_WORK_COMPRESSION)
            tl.segments.append(Segment(fr["file"], step["id"], kind, t, dur, real or None))
            if real and real > dur:
                tl.compressions.append({"step": step["id"], "frame": fr["file"], "kind": kind,
                                        "real_ms": real, "presented_ms": dur,
                                        "ratio": round(real / dur, 2)})

            # Cursor: travel during the "before" frame, arrive, then click on the transition.
            if kind == "before" and centre:
                tl.cursor.append({"t_ms": t, "x": round(cursor_xy[0], 1), "y": round(cursor_xy[1], 1),
                                  "click": False})
                arrive = t + CURSOR_TRAVEL_MS
                cursor_xy = centre
                tl.cursor.append({"t_ms": arrive, "x": round(centre[0], 1), "y": round(centre[1], 1),
                                  "click": False})
                if step["do"] in ("click", "check", "select", "fill"):
                    cp = step.get("click_point") or {"x": centre[0], "y": centre[1]}
                    tl.cursor.append({"t_ms": t + dur - 60, "x": round(cp["x"], 1), "y": round(cp["y"], 1),
                                      "click": True})
            if kind == "before":
                before_end = t + dur
            t += dur

        if step.get("callout") and tgt:
            n_callout += 1
            start = step_start
            end = before_end if (navigating_callout and before_end is not None) else t
            text = step["callout"]
            need = read_ms(text)
            if end - start < need:
                tl.defects.append({"class": "TIMING", "step": step["id"],
                                   "detail": f"callout '{text}' visible {end - start} ms, needs {need} ms",
                                   "short_ms": need - (end - start)})
            tl.callouts.append({"n": n_callout, "step": step["id"], "text": text,
                                "start_ms": start, "end_ms": end, "box": tgt["box"],
                                "avoid": step.get("text_boxes", [])})

    tl.duration_ms = t
    max_ms = int(float(output.get("max_seconds", 40)) * 1000)
    if t > max_ms:
        tl.defects.append({"class": "DURATION", "step": None,
                           "detail": f"timeline {t} ms exceeds max_seconds budget {max_ms} ms"})
    if not tl.segments:
        tl.defects.append({"class": "EMPTY", "step": None, "detail": "no filmed frames"})
    return tl


def cursor_at(tl: Timeline | dict, t_ms: float) -> tuple:
    """Eased cursor position at t (the stage's JS implements the same function)."""
    pts = tl["cursor"] if isinstance(tl, dict) else tl.cursor
    if t_ms <= pts[0]["t_ms"]:
        return pts[0]["x"], pts[0]["y"]
    for a, b in zip(pts, pts[1:]):
        if a["t_ms"] <= t_ms <= b["t_ms"]:
            span = max(1, b["t_ms"] - a["t_ms"])
            u = (t_ms - a["t_ms"]) / span
            e = u * u * (3 - 2 * u)          # smoothstep: no robotic constant velocity
            return a["x"] + (b["x"] - a["x"]) * e, a["y"] + (b["y"] - a["y"]) * e
    return pts[-1]["x"], pts[-1]["y"]
