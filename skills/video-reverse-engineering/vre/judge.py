"""Independent judge: a candidate render against the reference spec, with FROZEN tolerances.

The judge reads the reference spec and the candidate's own measured spec (the same `vre analyze` + `vre track`
run on the candidate video), never the generator's intent, so a generator cannot grade itself. Tolerances live
in a frozen file (`tolerances.json`, sha256 over its values) that is loaded read-only: `load_tolerances` refuses
a file whose hash no longer matches, and `freeze` refuses to freeze unless the A/A floor and the negative
controls are separable. Verdicts: FAIL, MOVES-SAME, LOOKS-SAME. Pixel identity is never claimed.

Dimensions (status PASS / FAIL / UNMEASURED; `critical` dimensions fail the whole verdict):
  orientation, frame_count, cuts, blank_frames  (critical)
  rows (timing + easing direction + missing objects), av_offset
  shot_ssim (LOOKS-SAME only)
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

from . import media

CRITICAL = ("orientation", "frame_count", "cuts", "blank_frames", "missing_objects")
MOVES_REQUIRED = CRITICAL + ("row_timing", "row_easing")
ENCODER_FLOOR_NOTE = "tolerances measured on synthetic A/A + negative controls; re-freeze on real footage"


def _hash(values: dict) -> str:
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def load_tolerances(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if _hash(data["values"]) != data["frozen"]["sha256"]:
        raise ValueError(f"tolerances file {path} no longer matches its frozen hash: refusing to judge")
    return data


def write_frozen(path: str | Path, values: dict, evidence: dict) -> dict:
    data = {"frozen": {"sha256": _hash(values), "note": ENCODER_FLOOR_NOTE}, "values": values,
            "evidence": evidence}
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return data


# ---------------------------------------------------------------- SSIM

def _gauss_blur(a: np.ndarray) -> np.ndarray:
    return cv2.GaussianBlur(a, (11, 11), 1.5)


def ssim(a: np.ndarray, b: np.ndarray) -> float:
    """Mean structural similarity of two gray float32 images in 0..255 (Wang et al., gaussian window)."""
    a, b = a.astype(np.float32), b.astype(np.float32)
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    mu_a, mu_b = _gauss_blur(a), _gauss_blur(b)
    saa = _gauss_blur(a * a) - mu_a * mu_a
    sbb = _gauss_blur(b * b) - mu_b * mu_b
    sab = _gauss_blur(a * b) - mu_a * mu_b
    m = ((2 * mu_a * mu_b + c1) * (2 * sab + c2)) / ((mu_a ** 2 + mu_b ** 2 + c1) * (saa + sbb + c2))
    return float(m.mean())


def gray_frames(video: str, width: int = 96) -> tuple[media.Probe, np.ndarray]:
    p = media.probe(video)
    out = [cv2.cvtColor(f, cv2.COLOR_RGB2GRAY) for f in media.iter_frames(p, width)]
    if not out:
        raise media.MediaError(f"no frames decoded from {video}")
    return p, np.stack(out)


# ---------------------------------------------------------------- dimensions

def _dim(status: str, **kw) -> dict:
    return {"status": status, **kw}


def d_orientation(ref: dict, cand: dict) -> dict:
    rs, cs = ref["source"], cand["source"]
    same = (rs["width"] < rs["height"]) == (cs["width"] < cs["height"]) and \
        abs(rs["width"] / rs["height"] - cs["width"] / cs["height"]) < 0.02
    return _dim("PASS" if same else "FAIL", ref=[rs["width"], rs["height"]], cand=[cs["width"], cs["height"]])


def d_frame_count(ref: dict, cand: dict, tol: dict) -> dict:
    r, c = ref["source"]["decoded_frames"], cand["source"]["decoded_frames"]
    ok = abs(r - c) <= tol["frame_count_frames"] and abs(ref["source"]["fps"] - cand["source"]["fps"]) < 0.01
    return _dim("PASS" if ok else "FAIL", ref=r, cand=c, fps=[ref["source"]["fps"], cand["source"]["fps"]],
                tol=tol["frame_count_frames"])


def d_cuts(ref: dict, cand: dict, tol: dict) -> dict:
    rc = sorted(c["frame"] for c in ref["cuts"])
    cc = sorted(c["frame"] for c in cand["cuts"])
    used: set[int] = set()
    missing, offsets = [], []
    for f in rc:
        best = min((j for j in range(len(cc)) if j not in used), key=lambda j: abs(cc[j] - f), default=None)
        if best is not None and abs(cc[best] - f) <= tol["cut_frames"]:
            used.add(best)
            offsets.append(cc[best] - f)
        else:
            missing.append(f)
    extra = [cc[j] for j in range(len(cc)) if j not in used]
    ok = not missing and not extra
    return _dim("PASS" if ok else "FAIL", missing=missing, extra=extra, offsets=offsets, tol=tol["cut_frames"])


def d_blank(ref_gray: np.ndarray, cand_gray: np.ndarray, tol: dict) -> dict:
    n = min(len(ref_gray), len(cand_gray))
    rs = ref_gray[:n].reshape(n, -1).std(axis=1)
    cs = cand_gray[:n].reshape(n, -1).std(axis=1)
    thr = tol["blank_std"]
    bad = [int(i) for i in np.nonzero((cs < thr) & (rs >= thr))[0]]
    return _dim("PASS" if not bad else "FAIL", frames=bad[:20], count=len(bad), tol=thr)


def family_class(name: str) -> str:
    n = (name or "").lower()
    if n in ("linear", "step", "spring", "bezier"):
        return n
    if n.startswith("easeinout"):
        return "inout"
    if n.startswith("easein"):
        return "in"
    if n.startswith("easeout"):
        return "out"
    return "unknown"


def _shot_of(ref: dict, frame: int) -> int:
    for s in ref["shots"]:
        if s["start"] <= frame <= s["end"]:
            return s["index"]
    return -1


def match_rows(ref_rows: list[dict], cand_rows: list[dict], shots: list[dict], window: int) -> tuple:
    """Pair reference rows with candidate rows by (shot, property), nearest start inside `window` frames."""
    def shot(frame):
        for s in shots:
            if s["start"] <= frame <= s["end"]:
                return s["index"]
        return -1

    free = list(range(len(cand_rows)))
    pairs, missing = [], []
    for r in sorted(ref_rows, key=lambda x: x["start"]):
        opts = [j for j in free if cand_rows[j].get("property") == r.get("property")
                and shot(cand_rows[j]["start"]) == shot(r["start"])
                and abs(cand_rows[j]["start"] - r["start"]) <= window]
        if not opts:
            missing.append(r)
            continue
        j = min(opts, key=lambda j: abs(cand_rows[j]["start"] - r["start"]))
        free.remove(j)
        pairs.append((r, cand_rows[j]))
    return pairs, missing


def d_rows(ref: dict, cand: dict, tol: dict) -> dict[str, dict]:
    ref_rows = [r for r in ref.get("rows", []) if r.get("evidence") == "OBSERVED"]
    if not ref_rows:
        un = _dim("UNMEASURED", reason="reference has no OBSERVED rows (run vre track)")
        return {"row_timing": un, "row_easing": un, "missing_objects": un}
    pairs, missing = match_rows(ref_rows, cand.get("rows", []), ref["shots"], tol["row_match_window_frames"])
    late = [{"element": r["element"], "property": r["property"], "ref": r["start"], "cand": c["start"]}
            for r, c in pairs if abs(r["start"] - c["start"]) > tol["row_start_frames"]]
    badease = [{"element": r["element"], "ref": r["easing"], "cand": c["easing"]}
               for r, c in pairs if r.get("easing") not in (None, "?") and c.get("easing") not in (None, "?")
               and family_class(r["easing"]) != family_class(c["easing"])]
    return {
        "row_timing": _dim("PASS" if not late else "FAIL", matched=len(pairs), off=late, tol=tol["row_start_frames"]),
        "row_easing": _dim("PASS" if not badease else "FAIL", compared=len(pairs), off=badease,
                           rule="same direction class (in / out / inout / linear / spring / step)"),
        "missing_objects": _dim("PASS" if not missing else "FAIL", count=len(missing),
                                rows=[{"element": m["element"], "property": m["property"], "start": m["start"]}
                                      for m in missing[:20]]),
    }


def d_av(ref: dict, cand: dict, tol: dict) -> dict:
    ra = ref.get("audio", {})
    ca = cand.get("audio", {})
    if ra.get("status") != "OK" or not ra.get("onsets_on_cuts"):
        return _dim("UNMEASURED", reason="reference has no onsets paired with cuts")
    if ca.get("status") != "OK":
        return _dim("FAIL", reason="candidate has no audio stream")
    cand_on = np.asarray(ca.get("onsets_s", []), dtype=float)
    offs = []
    for pair in ra["onsets_on_cuts"]:
        t = pair.get("time_s") if isinstance(pair, dict) else None
        if t is None or not len(cand_on):
            continue
        offs.append(float(cand_on[np.argmin(np.abs(cand_on - t))] - t))
    if not offs:
        return _dim("FAIL", reason="candidate has no onsets near the reference hits")
    worst = max(abs(o) for o in offs)
    return _dim("PASS" if worst <= tol["av_offset_s"] else "FAIL", worst_s=round(worst, 4), n=len(offs),
                tol=tol["av_offset_s"])


def d_shot_ssim(ref: dict, ref_gray: np.ndarray, cand_gray: np.ndarray, tol: dict) -> dict:
    n = min(len(ref_gray), len(cand_gray))
    per = []
    for s in ref["shots"]:
        a, b = s["start"], min(s["end"], n - 1)
        if a > b:
            continue
        vals = [ssim(ref_gray[i], cand_gray[i]) for i in range(a, b + 1)]
        per.append({"shot": s["index"], "mean": round(float(np.mean(vals)), 4), "min": round(float(np.min(vals)), 4)})
    worst = min((p["mean"] for p in per), default=0.0)
    return _dim("PASS" if per and worst >= tol["shot_ssim_min"] else "FAIL", per_shot=per, worst_mean=worst,
                tol=tol["shot_ssim_min"])


# ---------------------------------------------------------------- verdict

def judge(ref_spec: dict, cand_spec: dict, ref_gray: np.ndarray, cand_gray: np.ndarray, tolerances: dict,
          *, rebrand: bool = False) -> dict:
    tol = tolerances["values"]
    dims: dict[str, dict] = {
        "orientation": d_orientation(ref_spec, cand_spec),
        "frame_count": d_frame_count(ref_spec, cand_spec, tol),
        "cuts": d_cuts(ref_spec, cand_spec, tol),
        "blank_frames": d_blank(ref_gray, cand_gray, tol),
        **d_rows(ref_spec, cand_spec, tol),
        "av_offset": d_av(ref_spec, cand_spec, tol),
    }
    dims["shot_ssim"] = (_dim("UNMEASURED", reason="rebrand: judged on MOVES-SAME and layout, not pixels")
                         if rebrand else d_shot_ssim(ref_spec, ref_gray, cand_gray, tol))
    critical = [k for k in CRITICAL if dims[k]["status"] == "FAIL"]
    unmeasured = [k for k, v in dims.items() if v["status"] == "UNMEASURED"]
    moves = all(dims[k]["status"] == "PASS" for k in MOVES_REQUIRED) and dims["av_offset"]["status"] != "FAIL"
    level = "FAIL"
    if moves:
        level = "MOVES-SAME"
        if dims["shot_ssim"]["status"] == "PASS":
            level = "LOOKS-SAME"
    return {"level": level, "critical_failures": critical, "unmeasured": unmeasured, "dimensions": dims,
            "tolerances_sha256": tolerances["frozen"]["sha256"],
            "claim": "MOVES-SAME means timings and easing families are within frozen tolerances; never pixel identity"}


# ---------------------------------------------------------------- freeze

def freeze(path: str | Path, aa: list[float], controls: dict[str, float], base: dict) -> dict:
    """Freeze `shot_ssim_min` between the A/A floor (lowest shot SSIM of a benign re-encode) and the best
    negative control. Refuses when they overlap: an instrument that cannot tell them apart is not a judge."""
    floor, ceiling = min(aa), max(controls.values())
    if floor <= ceiling:
        raise ValueError(f"A/A floor {floor:.4f} <= best negative control {ceiling:.4f}: ssim cannot separate them")
    values = {**base, "shot_ssim_min": round((floor + ceiling) / 2, 4)}
    return write_frozen(path, values, {"aa_floor": round(floor, 4), "negative_controls": controls})
