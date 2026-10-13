"""Visual residual compiler: deterministic region-grid diff, failure mask, frozen regions, residual packet.

Extends the numeric-gate idea of image-calco (gate_boxes.py: measure, tolerance, a gate that can fail)
from named boxes to a full R x C grid. Standalone copy; the original is untouched. Uses Pillow + numpy.

usage: visual_residual.py CAND REF [--grid R,C] [--tol N] [--frozen F.json] [--mask M.png]
                          [--packet P.json --crops DIR]
Exit 0 only when every region is PASS or FROZEN_OK. Different sizes: refused (exit 2), never resized.
"""
import hashlib
import json
import os
import sys
import numpy as np
from PIL import Image


class SizeMismatch(Exception):
    pass


def region_verdict(max_diff, tol):
    return "PASS" if max_diff <= tol else "FAIL"


def _load(p):
    return np.asarray(Image.open(p).convert("RGB"), dtype=np.int16)


def _edges(n, k):
    return [round(i * n / k) for i in range(k + 1)]


def compare(candidate, reference, grid=(4, 4), tol=0, frozen_path=None, mask_path=None):
    c, r = _load(candidate), _load(reference)
    if c.shape != r.shape:
        raise SizeMismatch("size mismatch: candidate %dx%d vs reference %dx%d; refusing, no resize"
                           % (c.shape[1], c.shape[0], r.shape[1], r.shape[0]))
    H, W = r.shape[:2]
    R, C = grid
    ys, xs = _edges(H, R), _edges(W, C)
    frozen = {}
    if frozen_path and os.path.exists(frozen_path):
        frozen = json.load(open(frozen_path))
    diff = np.abs(c - r).max(axis=2)
    mask = np.zeros((H, W), dtype=np.uint8)
    regions, new_frozen = [], dict(frozen)
    for i in range(R):
        for j in range(C):
            y0, y1, x0, x1 = ys[i], ys[i + 1], xs[j], xs[j + 1]
            d = diff[y0:y1, x0:x1]
            rid = "r%dc%d" % (i, j)
            mx = int(d.max()) if d.size else 0
            ch = np.argwhere(d > tol)
            bbox = None
            if len(ch):
                bbox = [int(ch[:, 1].min()) + x0, int(ch[:, 0].min()) + y0,
                        int(ch[:, 1].max()) + x0 + 1, int(ch[:, 0].max()) + y0 + 1]
            rhash = hashlib.sha256(r[y0:y1, x0:x1].astype(np.uint8).tobytes()).hexdigest()
            v = region_verdict(mx, tol)
            if rid in frozen and frozen[rid] == rhash:
                v = "FROZEN_OK" if v == "PASS" else "FROZEN_REGRESSED"
            elif v == "PASS":
                new_frozen[rid] = rhash
            if v in ("FAIL", "FROZEN_REGRESSED"):
                mask[y0:y1, x0:x1] = (d > tol) * 255
            regions.append({"region": rid, "rect": [x0, y0, x1, y1], "verdict": v,
                            "mean_abs_diff": round(float(d.mean()), 4) if d.size else 0.0,
                            "max_diff": mx, "changed_bbox": bbox})
    if mask_path:
        Image.fromarray(mask).save(mask_path)
    if frozen_path:
        json.dump(new_frozen, open(frozen_path, "w"), indent=1, sort_keys=True)
    ok = all(x["verdict"] in ("PASS", "FROZEN_OK") for x in regions)
    return {"size": [W, H], "grid": [R, C], "tol": tol, "regions": regions, "gate": "PASS" if ok else "FAIL"}


def write_residual_packet(result, candidate, reference, crops_dir, packet_path, pad=0):
    """Compact JSON for FAIL / FROZEN_REGRESSED regions only, with crop paths (cand + ref)."""
    os.makedirs(crops_dir, exist_ok=True)
    ci, ri = Image.open(candidate).convert("RGB"), Image.open(reference).convert("RGB")
    items = []
    for g in result["regions"]:
        if g["verdict"] not in ("FAIL", "FROZEN_REGRESSED"):
            continue
        box = tuple(g["rect"])
        cp = os.path.join(crops_dir, g["region"] + "_cand.png")
        rp = os.path.join(crops_dir, g["region"] + "_ref.png")
        ci.crop(box).save(cp)
        ri.crop(box).save(rp)
        items.append({"region": g["region"], "verdict": g["verdict"], "metric": {
            "mean_abs_diff": g["mean_abs_diff"], "max_diff": g["max_diff"], "bbox": g["changed_bbox"]},
            "crops": {"candidate": cp, "reference": rp}})
    pkt = {"tol": result["tol"], "fail_regions": items}
    with open(packet_path, "w") as f:
        json.dump(pkt, f, separators=(",", ":"))
    return pkt


def main(argv):
    def arg(n, d=None):
        return argv[argv.index(n) + 1] if n in argv else d
    cand, ref = argv[1], argv[2]
    grid = tuple(int(x) for x in arg("--grid", "4,4").split(","))
    try:
        res = compare(cand, ref, grid, int(arg("--tol", "0")), arg("--frozen"), arg("--mask"))
    except SizeMismatch as e:
        print("REFUSED:", e)
        return 2
    for g in res["regions"]:
        print(g["region"], g["verdict"], "mean=%s max=%s bbox=%s" % (g["mean_abs_diff"], g["max_diff"], g["changed_bbox"]))
    if arg("--packet"):
        write_residual_packet(res, cand, ref, arg("--crops", "crops"), arg("--packet"))
    print("GATE", res["gate"])
    return 0 if res["gate"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
