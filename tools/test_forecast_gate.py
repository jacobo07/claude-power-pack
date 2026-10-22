#!/usr/bin/env python
"""V-FG-* / V-CMAP-* / V-CANARY-* gates for CCR v5 E3: the physical forecast gate
(route_admission.forecast_gate), the code-map page (tools/code_map.py) and the canary (tools/ccr_canary.py).
Each refusal is paired with a control that is admitted; the canary is driven red by a mutant."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import code_map  # noqa: E402
import route_admission as ra  # noqa: E402

passes = fails = 0
FLOORS = {"profiles": {"top-level-worker": {"floor": 110835}, "slim-t2": {"floor": 13507}}}
SAMPLE = '''"""module doc"""
import os


def alpha(x):
    """Add one.

    More text."""
    return x + 1


class Box:
    """A box."""

    def put(self, v):
        return v

    async def get(self):
        return 1


def beta():
    return 2
'''


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def canary(env_extra=None):
    env = {**os.environ, **(env_extra or {})}
    p = subprocess.run([sys.executable, "-I", str(HERE / "ccr_canary.py")], capture_output=True, text=True,
                       env=env, timeout=240)
    return p.returncode, p.stdout


def main():
    # --- forecast gate
    g = ra.forecast_gate
    bound = 6 * 110835
    check("V-FG-AT-BOUND-OK", g(bound, 6, "top-level-worker", FLOORS)["verdict"] == "OK", f"{bound:,}")
    r = g(bound - 1, 6, "top-level-worker", FLOORS)
    check("V-FG-BELOW-BOUND-UNDERPRICED", r["verdict"] == "UNDERPRICED" and r["need"] == bound
          and "6 calls x top-level-worker floor 110,835" in r["reason"], r["reason"])
    check("V-FG-SLIM-FLOOR-IS-LOWER", g(6 * 13507, 6, "slim-t2", FLOORS)["verdict"] == "OK", "same calls, slim profile")
    check("V-FG-NO-FLOOR-UNKNOWN", g(10**9, 6, "ghost", FLOORS)["verdict"] == "UNKNOWN", "absent floor is not OK")
    for label, args in (("zero-calls", (bound, 0)), ("bool-forecast", (True, 6)), ("float-calls", (bound, 6.0))):
        check(f"V-FG-BAD-INPUT-{label}", g(*args, "top-level-worker", FLOORS)["verdict"] == "UNKNOWN", str(args))

    # --- code map
    with tempfile.TemporaryDirectory(prefix="cmap-test-") as d:
        f = Path(d) / "s.py"
        f.write_text(SAMPLE, encoding="utf-8")
        m = code_map.build_map(f)
        check("V-CMAP-SYMBOLS-WITH-RANGES", "L5-9 (5) def alpha - Add one." in m and "L12-19 (8) class Box - A box." in m, m.splitlines()[2])
        check("V-CMAP-METHODS-NESTED", "  def put" in m and "  async def get" in m and "L22-23 (2) def beta" in m, "methods indented under the class")
        check("V-CMAP-HEADER-COUNTS", "23 lines  5 symbols" in m.splitlines()[0], m.splitlines()[0])
        js = Path(d) / "x.js"
        js.write_text("function a(){}\n", encoding="utf-8")
        try:
            code_map.build_map(js)
            check("V-CMAP-REFUSES-NON-PYTHON", False, "mapped a .js file")
        except code_map.MapError as exc:
            check("V-CMAP-REFUSES-NON-PYTHON", "guess" in str(exc), str(exc)[:70])
        bad = Path(d) / "b.py"
        bad.write_text("def (:\n", encoding="utf-8")
        try:
            code_map.build_map(bad)
            check("V-CMAP-REFUSES-UNPARSEABLE", False, "mapped a broken file")
        except code_map.MapError as exc:
            check("V-CMAP-REFUSES-UNPARSEABLE", "cannot parse" in str(exc), str(exc)[:70])
        store = Path(d) / "st"
        a, b = code_map.page(f, store), code_map.page(f, store)
        check("V-CMAP-PAGE-MISS-THEN-HIT", (a["hit"], b["hit"]) == (False, True) and a["map"] == b["map"], a["sha256"][:12])
        f.write_text(SAMPLE + "\ndef gamma():\n    return 3\n", encoding="utf-8")
        c = code_map.page(f, store)
        check("V-CMAP-EDIT-NEVER-STALE", c["hit"] is False and "def gamma" in c["map"] and "def gamma" not in a["map"],
              "an edited file gets a new page")
        check("V-CMAP-REAL-FILE-IS-SMALLER", code_map.page(HERE / "gsd_mission.py", store)["bytes_map"] * 10
              < (HERE / "gsd_mission.py").stat().st_size, "gsd_mission.py map is under 10% of the file")

    # --- canary: green, and red when the gate it checks is turned off
    rc, out = canary()
    check("V-CANARY-GREEN", rc == 0 and "CANARY_RESULT=PASS 8/8" in out, out.strip().splitlines()[-1] if out.strip() else "no output")
    rc2, out2 = canary({"CPP_FORECAST_GATE": "off"})
    check("V-CANARY-RED-WHEN-GATE-OFF", rc2 == 1 and "FAIL forecast-gate-refuses" in out2,
          "mutant: CPP_FORECAST_GATE=off must turn the canary red")

    print(f"FORECAST_GATE_PASS={passes}/{passes + fails}  threshold=all")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
