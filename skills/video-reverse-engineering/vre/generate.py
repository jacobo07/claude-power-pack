"""`generate`: a spec plus a brand plus a copy file becomes a Remotion composition (TSX).

Every row is emitted as data and played by a small runtime in the generated file: `interpolate` with
`Easing.bezier(...)` for named and free beziers, `spring(...)` for spring rows, a step for `reveal` rows. Colours come
from brand roles (never from the reference); text comes ONLY from the copy file (keys are element ids such as
`s3.text#0`); a text slot with no copy is reported UNFILLED and renders nothing. One `Sequence` per shot.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

DEFAULT_BRAND = {
    "font": "Inter, Helvetica, Arial, sans-serif",
    "light": {"background": "#F5F5F5", "surface": "#E4E7EB", "accent": "#2563EB", "text": "#111827"},
    "dark": {"background": "#0B1220", "surface": "#1B2433", "accent": "#2EC4B6", "text": "#F3F4F6"},
}

RUNTIME = """
type Row = {p: string; s: number; d: number; a: number; b: number; e: string; bz: number[] | null;
  sp: {mass: number; damping: number; stiffness: number} | null};
type El = {id: string; kind: 'text' | 'layer'; t0: number; t1: number; x: number; y: number; w: number; h: number;
  fill: string; text: string | null; rows: Row[]};
type ShotData = {index: number; from: number; frames: number; bg: string; ink: string; els: El[]};

const evalRow = (r: Row, f: number, fps: number): number => {
  if (r.e === 'step') return f >= r.s ? r.b : r.a;
  if (f <= r.s) return r.a;
  if (r.e === 'spring' && r.sp) {
    return r.a + (r.b - r.a) * spring({frame: f - r.s, fps, config: r.sp});
  }
  if (f >= r.s + r.d) return r.b;
  const easing = r.bz ? Easing.bezier(r.bz[0], r.bz[1], r.bz[2], r.bz[3]) : Easing.linear;
  return interpolate(f, [r.s, r.s + r.d], [r.a, r.b], {easing});
};

const prop = (el: El, name: string, f: number, fps: number, dflt: number): number => {
  const rows = el.rows.filter((r) => r.p === name).sort((p, q) => p.s - q.s);
  let v = dflt;
  for (const r of rows) {
    if (f >= r.s) v = evalRow(r, f, fps);
    else if (rows.indexOf(r) === 0) v = r.a;
  }
  return v;
};

const Layer: React.FC<{el: El; frame: number; fps: number}> = ({el, frame, fps}) => {
  if (frame < el.t0 || frame > el.t1) return null;
  const x = prop(el, 'x', frame, fps, el.x);
  const y = prop(el, 'y', frame, fps, el.y);
  const sc = prop(el, 'scale', frame, fps, 1);
  const rot = prop(el, 'rotation', frame, fps, 0);
  const op = prop(el, 'opacity', frame, fps, 1);
  if (el.kind === 'layer') {
    return <div style={{position: 'absolute', left: x - el.w / 2, top: y - el.h / 2, width: el.w, height: el.h,
      background: el.fill, opacity: op, transform: `rotate(${rot}deg) scale(${sc})`}} />;
  }
  if (el.text === null) return null;
  const words = el.text.split(/\\s+/).filter(Boolean);
  const reveals = el.rows.filter((r) => r.p === 'reveal').map((r) => r.s).sort((a, b) => a - b);
  const at = (k: number) => reveals[Math.min(reveals.length - 1, Math.floor((k * reveals.length) / words.length))];
  const shown = reveals.length ? words.filter((_, k) => frame >= at(k)) : words;
  return <div style={{position: 'absolute', left: x, top: y, whiteSpace: 'nowrap', color: el.fill, opacity: op,
    fontSize: el.h * 0.8, lineHeight: `${el.h}px`, fontWeight: 700, fontFamily: BRAND_FONT,
    transformOrigin: 'left top', transform: `rotate(${rot}deg) scale(${sc})`}}>{shown.join(' ')}</div>;
};

const Shot: React.FC<{data: ShotData}> = ({data}) => {
  const frame = useCurrentFrame() + data.from;
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{background: data.bg}}>
      {data.els.map((el) => <Layer key={el.id} el={el} frame={frame} fps={fps} />)}
    </AbsoluteFill>
  );
};
"""


def _round(v, n=3):
    return None if v is None else round(float(v), n)


def _row(r: dict, k: float) -> dict:
    prop = r["property"]
    a, b = r.get("from"), r.get("to")
    if prop in ("x", "y"):
        a, b = a * k, b * k
    sp = r.get("spring")
    return {"p": prop, "s": int(r["start"]), "d": int(r.get("duration") or 0), "a": _round(a), "b": _round(b),
            "e": r.get("easing") or "linear", "bz": [round(float(v), 4) for v in r["bezier"]] if r.get("bezier")
            else None, "sp": ({"mass": sp["mass"], "damping": sp["damping"], "stiffness": sp["stiffness"]}
                              if sp else None)}


def _nearest_role(rgb: list[int], roles: dict[str, str | None]) -> str:
    best, name = 1e18, "accent"
    for role, hexv in roles.items():
        if not hexv:
            continue
        c = np.array([int(hexv[i:i + 2], 16) for i in (1, 3, 5)])
        d = float(((c - np.array(rgb)) ** 2).sum())
        if d < best:
            best, name = d, role
    return name


def build(spec: dict, brand: dict | None, copy: dict[str, str]) -> tuple[dict, dict]:
    """Composition data + a report. Pure function of its inputs (two runs give the same bytes)."""
    brand = {**DEFAULT_BRAND, **(brand or {})}
    src = spec["source"]
    W, H, fps = int(src["width"]), int(src["height"]), float(src["fps"])
    tracked_w = (spec.get("layer_tracks") or spec.get("text_tracks") or {}).get("width") or spec["analysis"]["width"]
    k = W / float(tracked_w)
    by_el: dict[str, list[dict]] = {}
    for r in spec.get("rows", []):
        by_el.setdefault(r["element"], []).append(r)
    text_info = {t["element"]: t for t in (spec.get("text_tracks") or {}).get("tracks", [])}
    layer_info = {o["element"]: o for o in (spec.get("layer_tracks") or {}).get("objects", []) if o["status"] == "OK"}
    shots_out, unfilled, used = [], [], []
    for sh in spec["shots"]:
        pal = sh.get("palette") or {}
        pol = pal.get("polarity", "dark")
        colours = brand.get(pol) or brand["dark"]
        els = []
        for eid in sorted(set(text_info) | set(layer_info)):
            info = text_info.get(eid) or layer_info.get(eid)
            if info["shot"] != sh["index"] and not eid.startswith(f"s{sh['index']}."):
                continue
            rows = [_row(r, k) for r in by_el.get(eid, [])]
            if eid in text_info:
                t = text_info[eid]
                box = t.get("box") or [0, 0, 0, 0]
                txt = copy.get(eid)
                if txt is None:
                    unfilled.append(eid)
                else:
                    used.append(eid)
                els.append({"id": eid, "kind": "text", "t0": t["first"], "t1": t["last"], "x": _round(box[0] * k, 1),
                            "y": _round(box[1] * k, 1), "w": _round((box[2] - box[0]) * k, 1),
                            "h": _round((box[3] - box[1]) * k, 1), "fill": colours["text"], "text": txt, "rows": rows})
            else:
                o = layer_info[eid]
                box = o.get("box") or [0, 0, 0, 0]
                role = _nearest_role(o.get("rgb", [0, 0, 0]), pal.get("roles") or {})
                els.append({"id": eid, "kind": "layer", "t0": o["first"], "t1": o["last"],
                            "x": _round((box[0] + box[2]) / 2 * k, 1), "y": _round((box[1] + box[3]) / 2 * k, 1),
                            "w": _round((box[2] - box[0]) * k, 1), "h": _round((box[3] - box[1]) * k, 1),
                            "fill": colours.get(role) or colours["accent"], "text": None, "rows": rows})
        shots_out.append({"index": sh["index"], "from": int(sh["start"]), "frames": int(sh["end"] - sh["start"] + 1),
                          "bg": colours["background"], "ink": colours["text"], "els": els})
    data = {"width": W, "height": H, "fps": fps, "frames": int(shots_out[-1]["from"] + shots_out[-1]["frames"]),
            "font": brand["font"], "shots": shots_out}
    report = {"unfilled_text": unfilled, "used_copy": used,
              "unused_copy": sorted(set(copy) - set(used)), "shots": len(shots_out),
              "rows": sum(len(e["rows"]) for s in shots_out for e in s["els"])}
    return data, report


def render_tsx(data: dict) -> str:
    head = ("// Generated by vre generate. Do not edit by hand: change the spec, the brand or the copy file.\n"
            "import React from 'react';\n"
            "import {AbsoluteFill, Easing, Sequence, interpolate, spring, useCurrentFrame, useVideoConfig}"
            " from 'remotion';\n\n"
            f"export const VRE = {json.dumps({k: v for k, v in data.items() if k != 'shots'}, sort_keys=True)}"
            " as const;\n"
            f"const BRAND_FONT = {json.dumps(data['font'])};\n"
            f"const SHOTS: ShotData[] = {json.dumps(data['shots'], indent=1, sort_keys=True)};\n")
    body = RUNTIME + """
export const VreComposition: React.FC = () => (
  <AbsoluteFill>
    {SHOTS.map((s) => (
      <Sequence key={s.index} from={s.from} durationInFrames={s.frames}>
        <Shot data={s} />
      </Sequence>
    ))}
  </AbsoluteFill>
);
"""
    return head + body


def generate(spec_dir: str, out_dir: str, *, brand: str | None = None, copy: str | None = None,
             strict: bool = False) -> dict:
    spec = json.loads((Path(spec_dir) / "spec.json").read_text(encoding="utf-8"))
    b = json.loads(Path(brand).read_text(encoding="utf-8")) if brand else None
    c = json.loads(Path(copy).read_text(encoding="utf-8")) if copy else {}
    data, report = build(spec, b, c)
    if strict and report["unfilled_text"]:
        raise ValueError(f"copy file has no text for: {', '.join(report['unfilled_text'])}")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "VreComposition.tsx").write_text(render_tsx(data), encoding="utf-8")
    (out / "vre-generate-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report

