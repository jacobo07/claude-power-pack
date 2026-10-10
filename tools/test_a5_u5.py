"""A5-U5 tests: visual residual compiler. Hermetic (temp dirs), synthetic PNGs."""
import os
import sys
import json
import tempfile
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import visual_residual as vr

RESULTS = []


def check(name, cond):
    RESULTS.append(bool(cond))
    print(("ok   " if cond else "FAIL ") + name)


def card(w=400, h=300, shift=0):
    a = np.full((h, w, 3), 240, dtype=np.uint8)
    a[20:60, 20:180] = (30, 60, 200)
    a[20 + shift:60 + shift, 220 + shift:380 + shift] = (200, 40, 40)  # region r0c2/r0c3 area
    a[150:250, 20:380] = (20, 140, 70)
    return a


def save(a, p):
    Image.fromarray(a).save(p)
    return p


def failing(res):
    return sorted(g["region"] for g in res["regions"] if g["verdict"] != "PASS")


def main():
    with tempfile.TemporaryDirectory() as d:
        P = lambda n: os.path.join(d, n)
        ref = save(card(), P("ref.png"))
        same = save(card(), P("same.png"))
        G = (3, 4)
        # identical -> PASS
        r = vr.compare(same, ref, G, 0)
        check("identical -> gate PASS", r["gate"] == "PASS" and all(g["verdict"] == "PASS" for g in r["regions"]))
        # one region changed -> mask names only it
        a = card(); a[110:140, 110:140] = (0, 0, 0)  # inside r1c1 (y100-200, x100-200)
        shifted = save(a, P("shift.png"))
        mp = P("mask.png")
        r = vr.compare(shifted, ref, G, 0, mask_path=mp)
        m = np.asarray(Image.open(mp))
        rect = {g["region"]: g["rect"] for g in r["regions"]}
        outside = sum(int(m[y0:y1, x0:x1].any()) for k, (x0, y0, x1, y1) in rect.items() if k != "r1c1")
        x0, y0, x1, y1 = rect["r1c1"]
        check("changed region -> only r1c1 FAIL", failing(r) == ["r1c1"] and r["gate"] == "FAIL")
        check("mask lit in r1c1 only", m[y0:y1, x0:x1].any() and outside == 0)
        # size mismatch refused; control same size admitted
        big = save(np.zeros((301, 400, 3), np.uint8), P("big.png"))
        try:
            vr.compare(big, ref, G, 0)
            refused = False
        except vr.SizeMismatch as e:
            refused = "no resize" in str(e)
        check("size mismatch refused", refused)
        check("control: same size admitted", vr.compare(same, ref, G, 0)["gate"] == "PASS")
        # tolerance: small noise within tol passes, beyond tol fails
        n = card().astype(np.int16); n[110:140, 110:140] += 3
        noisy = save(n.astype(np.uint8), P("noisy.png"))
        check("noise within tol -> PASS", vr.compare(noisy, ref, G, 3)["gate"] == "PASS")
        check("noise beyond tol -> FAIL", vr.compare(noisy, ref, G, 2)["gate"] == "FAIL")
        # frozen
        fz = P("frozen.json")
        vr.compare(same, ref, G, 0, frozen_path=fz)
        check("frozen file records passed regions", len(json.load(open(fz))) == 12)
        r = vr.compare(same, ref, G, 0, frozen_path=fz)
        check("later run: FROZEN_OK", all(g["verdict"] == "FROZEN_OK" for g in r["regions"]) and r["gate"] == "PASS")
        r = vr.compare(shifted, ref, G, 0, frozen_path=fz)
        reg = [g["region"] for g in r["regions"] if g["verdict"] == "FROZEN_REGRESSED"]
        check("frozen region changed -> FROZEN_REGRESSED (only r1c1)", reg == ["r1c1"] and r["gate"] == "FAIL")
        # residual packet: fail regions only, smaller than the full image
        pk = P("packet.json")
        pkt = vr.write_residual_packet(r, shifted, ref, P("crops"), pk)
        check("packet names only failing region + crops exist",
              [i["region"] for i in pkt["fail_regions"]] == ["r1c1"]
              and all(os.path.exists(v) for i in pkt["fail_regions"] for v in i["crops"].values()))
        full = os.path.getsize(shifted) + os.path.getsize(ref)
        print("PACKET_BYTES=%d FULL_IMAGE_BYTES=%d" % (os.path.getsize(pk), full))
        check("packet smaller than full images", os.path.getsize(pk) < full)
        # mutant: tolerance ignored -> the tolerance test must go red
        orig = vr.region_verdict
        vr.region_verdict = lambda mx, tol: "PASS" if mx <= 0 else "FAIL"
        try:
            mut_red = vr.compare(noisy, ref, G, 3)["gate"] != "PASS"
        finally:
            vr.region_verdict = orig
        check("mutant (tol ignored) detected red", mut_red)
    n, ok = len(RESULTS), sum(RESULTS)
    print("A5_U5_PASS=%d/%d" % (ok, n))
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(main())
