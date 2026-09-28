"""V-REGMEM-*: tools/regression_memory.py -- V-gate runs as regression evidence, vendored lifecycle.

Hermetic: a temporary root with its own vault/regressions store, a synthetic V-gate suite whose
behaviour a flag file selects, and an artifact the suite covers.
    python tools/test_regression_memory.py
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import regression_memory as rm  # noqa: E402

passes = fails = 0
SUITE = """import sys, pathlib
mode = pathlib.Path('mode.txt').read_text().strip()
if mode == 'crash':
    raise SystemExit(1)
print('PASS V-DEMO-B: stable')
if mode == 'fail':
    print('FAIL V-DEMO-A: broken')
else:
    print('PASS V-DEMO-A: fixed')
if mode == 'extra':
    print('PASS V-DEMO-C: new identity')
raise SystemExit(1 if mode == 'fail' else 0)
"""


def check(gate: str, cond: bool, ev: object = "") -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {ev}")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="regmem_t_"))
    try:
        (tmp / "suite.py").write_text(SUITE, encoding="utf-8")
        (tmp / "art.py").write_text("x = 1\n", encoding="utf-8")
        mode = lambda m: (tmp / "mode.txt").write_text(m, encoding="utf-8")  # noqa: E731
        run = lambda: rm.run(tmp, "demo", "suite.py", ["art.py"])  # noqa: E731

        print("the conversion is the suite's own lines")
        tap, p, f = rm.to_tap("PASS V-X: a\nnoise\nFAIL V-Y: b\n")
        check("V-REGMEM-TAP-COUNTS", (p, f) == (1, 1) and "not ok 2 - V-Y" in tap and "# tests 2" in tap, (p, f))

        print("lifecycle: fail -> open -> independent pass -> resolved")
        mode("pass")
        passing_first = run()
        ok, msg = rm.create(tmp, "demo", "V-DEMO-A broke", passing_first["runId"])
        check("V-REGMEM-CREATE-NEEDS-FAILURE", not ok and "failing" in msg.lower(), msg)
        mode("fail")
        failing = run()
        check("V-REGMEM-FAILING-RUN", failing["exitCode"] == 1 and failing["failedCount"] == 1, failing["checkedCount"])
        ok, msg = rm.create(tmp, "demo", "V-DEMO-A broke", failing["runId"])
        check("V-REGMEM-CREATED-OPEN", ok and msg == "open", msg)
        ok, msg = rm.resolve(tmp, "demo", failing["runId"])
        check("V-REGMEM-RESOLVE-NEEDS-PASS", not ok, msg)
        mode("extra")
        changed = run()
        ok, msg = rm.resolve(tmp, "demo", changed["runId"])
        check("V-REGMEM-CHECK-IDENTITY-CHANGE-REFUSED", not ok and "identit" in msg, msg)
        mode("pass")
        fixed = run()
        ok, msg = rm.resolve(tmp, "demo", fixed["runId"])
        check("V-REGMEM-RESOLVED", ok and msg == "resolved", msg)

        print("reopen: a control, then a moved byte")
        rows = rm.reopen_all(tmp)
        check("V-REGMEM-UNCHANGED-STAYS-RESOLVED", rows == [{"id": "demo", "status": "resolved", "reason": ""}], rows)
        (tmp / "art.py").write_text("x = 2\n", encoding="utf-8")
        rows = rm.reopen_all(tmp)
        check("V-REGMEM-MOVED-BYTE-REOPENS", rows and rows[0]["status"] == "REOPENED" and "Stale" in rows[0]["reason"], rows)
        rec = json.loads((tmp / "vault" / "regressions" / "demo" / "record.json").read_text(encoding="utf-8"))
        check("V-REGMEM-REOPENING-RECORDED", rec["status"] == "open" and len(rec["reopenings"]) == 1, rec["reopenings"])

        print("a suite that judged nothing cannot become a record")
        mode("crash")
        crashed = rm.run(tmp, "crash", "suite.py", ["art.py"])
        ok, msg = rm.create(tmp, "crash", "crashed", crashed["runId"])
        check("V-REGMEM-CRASH-REFUSED", not ok and crashed["checkedCount"] == 0, msg)

        saved = os.environ.get("CPP_NODE_EXE")
        os.environ["CPP_NODE_EXE"] = str(tmp / "no-node.exe")
        try:
            rows = rm.reopen_all(tmp)
        finally:
            if saved is None:
                os.environ.pop("CPP_NODE_EXE", None)
            else:
                os.environ["CPP_NODE_EXE"] = saved
        check("V-REGMEM-BRIDGE-DOWN-UNJUDGED", rows and all(x["status"] == "UNJUDGED" for x in rows), rows)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    total = passes + fails
    print(f"REGMEM_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
