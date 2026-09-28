"""V-CIMPACT-*: tools/change_impact.py -- which suites a change reaches, from the code's own edges.

Hermetic: a synthetic tree whose true dependencies are known. Every edge kind the graph claims to
see is driven (plain import, sys.path-style tools import, package import, relative import, a
subprocess path literal, a transitive chain); a non-Python change must be a gap, and a sweep that
found too little must refuse rather than answer.
    python tools/test_change_impact.py
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import change_impact as ci  # noqa: E402

passes = fails = 0


def check(gate: str, cond: bool, ev: object = "") -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {ev}")


def w(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="cimpact_t_"))
    saved_floor = ci.FLOOR
    try:
        w(tmp, "tools/core.py", "X = 1\n")
        w(tmp, "tools/mid.py", "import core\n")                                   # sys.path style
        w(tmp, "tools/test_core.py", "import core as c\n")
        w(tmp, "tools/test_mid.py", "import mid\n")                               # transitive to core
        w(tmp, "tools/test_cli.py", "import subprocess\nsubprocess.run(['python', 'tools/cli.py'])\n")
        w(tmp, "tools/cli.py", "print('hi')\n")
        w(tmp, "modules/__init__.py", "")
        w(tmp, "modules/pkg/__init__.py", "")
        w(tmp, "modules/pkg/a.py", "from . import b\n")                           # relative
        w(tmp, "modules/pkg/b.py", "Y = 2\n")
        w(tmp, "tools/test_pkg.py", "from modules.pkg import a\n")                 # package import
        w(tmp, "tools/test_unrelated.py", "import json\n")
        w(tmp, "hooks/guard.js", "// not python\n")
        ci.FLOOR = 5

        def suites(*changed):
            r = ci.analyze(tmp, list(changed))
            return r, set(r.get("affected", {}).get("test", []))

        r, s = suites("tools/core.py")
        check("V-CIMPACT-DIRECT-AND-TRANSITIVE", s == {"tools/test_core.py", "tools/test_mid.py"}, sorted(s))
        check("V-CIMPACT-UNRELATED-NOT-RUN", "tools/test_unrelated.py" not in s, sorted(s))
        r, s = suites("tools/cli.py")
        check("V-CIMPACT-SUBPROCESS-PATH-EDGE", s == {"tools/test_cli.py"}, sorted(s))
        r, s = suites("modules/pkg/b.py")
        check("V-CIMPACT-RELATIVE-THEN-PACKAGE", s == {"tools/test_pkg.py"}, sorted(s))
        r, s = suites("hooks/guard.js", "tools/core.py")
        check("V-CIMPACT-NON-PYTHON-IS-A-GAP", r["coverageComplete"] is False
              and {"type": "unmatched-change", "path": "hooks/guard.js"} in r["gaps"]
              and "tools/test_core.py" in s, r["gaps"])
        r, s = suites("tools/core.py")
        check("V-CIMPACT-COMPLETE-WHEN-MAPPED", r["coverageComplete"] is True and not r["gaps"], r["gaps"])

        ci.FLOOR = 10_000
        r = ci.analyze(tmp, ["tools/core.py"])
        check("V-CIMPACT-FLOOR-REFUSES", r.get("unjudged") is True and r["gaps"][0]["type"] == "sweep-floor", r)
        ci.FLOOR = 5
        saved = os.environ.get("CPP_NODE_EXE")
        os.environ["CPP_NODE_EXE"] = str(tmp / "no-node.exe")
        try:
            r = ci.analyze(tmp, ["tools/core.py"])
        finally:
            if saved is None:
                os.environ.pop("CPP_NODE_EXE", None)
            else:
                os.environ["CPP_NODE_EXE"] = saved
        check("V-CIMPACT-BRIDGE-DOWN-UNJUDGED", r.get("unjudged") is True, r.get("gaps"))

        print("the real tree: a change to rollover.py reaches its own suites")
        ci.FLOOR = saved_floor
        real = ci.analyze(ROOT, ["tools/rollover.py"])
        rs = set(real.get("affected", {}).get("test", []))
        check("V-CIMPACT-REAL-ROLLOVER", {"tools/test_rollover.py", "tools/test_rollover_active_path.py"} <= rs,
              sorted(rs))
    finally:
        ci.FLOOR = saved_floor
        shutil.rmtree(tmp, ignore_errors=True)
    total = passes + fails
    print(f"CIMPACT_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
