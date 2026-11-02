#!/usr/bin/env python
"""V-HOLDOUT-* gates for tools/heldout_release.py (Held-out Consumption Law, Tennis S11 A3).

The S10b replay (positive controls 0/3) must refuse; a request meeting every condition must release (control);
each condition removed on its own must refuse with its own reason. --drills: each mutant of heldout_release.py must
turn its named gate red.
"""
from __future__ import annotations

import copy
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.environ.get("HOLDOUT_DRILL_DIR") or str(Path(__file__).resolve().parent))
import heldout_release as hr  # noqa: E402

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        man = Path(td) / "manifest.json"
        man.write_text('{"h2": "frozen"}\n', encoding="utf-8")
        seal = Path(td) / "h2"
        good = {"manifest": str(man), "manifest_sha256": hashlib.sha256(man.read_bytes()).hexdigest(),
                "method_frozen": {"commit": "c0ffee1", "entrypoint": "tools/run.py"},
                "controls": {"positive": {"pass": 3, "total": 3}, "negative": {"refused": 3, "total": 3}},
                "dev_minimum": {"required": 3, "observed": 4}, "blindness": [], "seal_dir": str(seal)}
        r = hr.release(good)
        check("V-HOLDOUT-RELEASE-CONTROL", r["verdict"] == "RELEASE", str(r))

        s10b = copy.deepcopy(good)
        s10b["controls"]["positive"] = {"pass": 0, "total": 3}
        s10b["dev_minimum"]["observed"] = 0
        s10b["blindness"] = ["operator returns None on raw m2c for the 3 known CXX"]
        r = hr.release(s10b)
        check("V-HOLDOUT-S10B-REFUSED", r["verdict"] == "REFUSE" and any("positive controls 0/3" in x for x in r["reasons"]),
              str(r["reasons"]))

        cases = {
            "V-HOLDOUT-POSITIVE": (("controls", "positive"), {"pass": 2, "total": 3}, "positive controls"),
            "V-HOLDOUT-POSITIVE-EMPTY": (("controls", "positive"), {"pass": 0, "total": 0}, "positive controls"),
            "V-HOLDOUT-NEGATIVE": (("controls", "negative"), {"refused": 2, "total": 3}, "negative controls"),
            "V-HOLDOUT-DEV-MIN": (("dev_minimum",), {"required": 3, "observed": 2}, "development minimum"),
            "V-HOLDOUT-BLINDNESS": (("blindness",), ["x"], "blindness"),
            "V-HOLDOUT-UNFROZEN": (("method_frozen",), {}, "not frozen"),
            "V-HOLDOUT-MANIFEST-SHA": (("manifest_sha256",), "0" * 64, "sha256 differs"),
        }
        for gate, (path, val, needle) in cases.items():
            req = copy.deepcopy(good)
            node = req
            for k in path[:-1]:
                node = node[k]
            node[path[-1]] = val
            r = hr.release(req)
            check(gate, r["verdict"] == "REFUSE" and any(needle in x for x in r["reasons"]), str(r["reasons"]))

        seal.mkdir()
        (seal / "SEAL").write_text("x", encoding="utf-8")
        r = hr.release(good)
        check("V-HOLDOUT-ALREADY-SEALED", r["verdict"] == "REFUSE" and any("SEAL already" in x for x in r["reasons"]),
              str(r["reasons"]))
    print(f"HOLDOUT_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


DRILLS = (
    ("H1 positive check removed", 'int(pos.get("pass") or 0) != int(pos.get("total") or 0)', "False",
     "V-HOLDOUT-S10B-REFUSED"),
    ("H2 negative check removed", 'int(neg.get("refused") or 0) != int(neg.get("total") or 0)', "False",
     "V-HOLDOUT-NEGATIVE"),
    ("H3 seal check removed", '(Path(str(seal)) / "SEAL").exists()', "False", "V-HOLDOUT-ALREADY-SEALED"),
)


def drills() -> int:
    src = (Path(__file__).resolve().parent / "heldout_release.py").read_text(encoding="utf-8")
    ok = 0
    for name, needle, repl, gate in DRILLS:
        if needle not in src:
            print(f"DRILL-FAIL {name}: needle absent")
            continue
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "heldout_release.py").write_text(src.replace(needle, repl, 1), encoding="utf-8")
            r = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve())], capture_output=True, text=True,
                               env={**os.environ, "HOLDOUT_DRILL_DIR": td}, timeout=120)
        red = f"FAIL {gate}" in r.stdout
        ok += red
        print(f"{'DRILL-PASS' if red else 'DRILL-FAIL'} {name}: {gate} {'red' if red else 'NOT red'}")
    print(f"HOLDOUT_DRILLS_PASS={ok}/{len(DRILLS)}")
    return 0 if ok == len(DRILLS) else 1


if __name__ == "__main__":
    sys.exit(drills() if "--drills" in sys.argv[1:] else main())
