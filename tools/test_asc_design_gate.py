#!/usr/bin/env python3
"""V-ASC-DG-* -- the paired design-gate measurement (tools/asc_design_gate_run.py), driven offline.

A stand-in `claude` (tools/fixtures/fake_claude.py) writes a slop page on the first call, a clean page plus three
Skill loads on a --resume, and always answers the judge with "B". Proves, with no model: the treated arm gets the kit,
the REAL Stop gate blocks it, the resume happens and is re-judged, the Taste counts separate the arms, and a judge that
always picks one position never yields a winner (position bias is detected, not counted).
Run: python tools/test_asc_design_gate.py   (exit 0 = all gates pass)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS: list = []


def ok(name: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(cond)))
    print("  %s %-34s %s" % ("PASS" if cond else "FAIL", name, "" if cond else str(detail)[:300]))


def main() -> int:
    out = tempfile.mkdtemp(prefix="v-asc-dg-")
    try:
        env = dict(os.environ, PYTHONIOENCODING="utf-8",
                   CPP_CLAUDE_EXE=json.dumps([sys.executable, str(ROOT / "tools" / "fixtures" / "fake_claude.py")]))
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "asc_design_gate_run.py"), "--out", out,
                            "--tasks", "saas"], capture_output=True, text=True, env=env, timeout=600, encoding="utf-8")
        ok("V-ASC-DG-RUN-RC0", r.returncode == 0, r.stderr[-400:])
        rec = json.loads(Path(out, "design_gate_run.json").read_text(encoding="utf-8"))
        t = rec["tasks"]["saas"]
        tr = t["treated"]
        ok("V-ASC-DG-KIT", {"design-md", "design-taste-frontend", "frontend-design", "agent:cdio-reviewer"}
           <= set(tr.get("kit", [])), tr.get("kit"))
        ok("V-ASC-DG-CONTROL-NO-KIT", not Path(out, "saas", "control", ".claude").exists())
        ok("V-ASC-DG-REAL-STOP-BLOCKS", tr["stop_round"]["blocked"] and "TASTE-EMDASH" in tr["stop_round"]["reason"],
           tr["stop_round"])
        ok("V-ASC-DG-RESUMED-ONCE", len(tr["calls"]) == 2 and len(t["control"]["calls"]) == 1,
           [len(tr["calls"]), len(t["control"]["calls"])])
        left = {p[0] for p in tr["after_round"]["problems_left"]}
        ok("V-ASC-DG-REJUDGED-AFTER-ROUND", left == {"design-review"}, tr["after_round"])
        ok("V-ASC-DG-TASTE-SEPARATES", t["taste"]["control"]["critical"] == 1 and t["taste"]["treated"]["critical"] == 0,
           t["taste"])
        ok("V-ASC-DG-POSITION-BIAS-NO-WINNER", t["judge"]["consistent_winner"] == "none"
           and {v["winner"] for v in t["judge"]["votes"]} == {"control", "treated"}, t["judge"])
    finally:
        shutil.rmtree(out, ignore_errors=True)
    passed = sum(1 for _, c in RESULTS if c)
    print("V-ASC-DG: %d passed, %d failed" % (passed, len(RESULTS) - passed))
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
