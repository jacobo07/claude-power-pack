#!/usr/bin/env python
"""CDC C5b: run every tools/test_*.py under --root serially (cap per suite), record rc/secs/checks.
rc != 0 -> red; timeout -> recorded as 'timeout' (NOT red). Every subprocess is awaited (subprocess.run).
    python tools/c5b_baseline.py --root R --out base.json [--cap 300] [--only a.py b.py]
Writes {"root","cap","suites":{path:{status,rc,secs,checks}},"red":[...],"timeout":[...]} ."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path


def run_one(root: Path, t: str, cap: int) -> dict:
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, t], cwd=root, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=cap)
        out = p.stdout + p.stderr
        st, rc = ("green" if p.returncode == 0 else "red"), p.returncode
    except subprocess.TimeoutExpired as e:
        out = ((e.stdout or b"") if isinstance(e.stdout, bytes) else (e.stdout or "")) and ""
        st, rc = "timeout", None
    except Exception as e:  # cannot start = red
        out, st, rc = repr(e), "red", 99
    n = len(re.findall(r"\bPASS\b", out)) + len(re.findall(r"\bFAIL\b", out))
    return {"status": st, "rc": rc, "secs": round(time.time() - t0, 2), "checks": n}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cap", type=int, default=300)
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    suites = a.only or sorted(p.relative_to(root).as_posix() for p in (root / "tools").glob("test_*.py"))
    res = {}
    for i, t in enumerate(suites):
        res[t] = run_one(root, t, a.cap)
        print(f"[{i + 1}/{len(suites)}] {t} {res[t]['status']} {res[t]['secs']}s", flush=True)
    out = {"root": str(root), "cap": a.cap, "suites": res,
           "red": sorted(k for k, v in res.items() if v["status"] == "red"),
           "timeout": sorted(k for k, v in res.items() if v["status"] == "timeout")}
    Path(a.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"suites={len(res)} red={len(out['red'])} timeout={len(out['timeout'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
