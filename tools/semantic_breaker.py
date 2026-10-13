"""Semantic breaker calibration (CDC C4): calls-between-progress distribution over historical transcripts.

`calibrate <transcript>...` -> prints the distribution and, with --write, vault/config/semantic-breaker.json
(calls_p95, and trip_calls = max(p95, 25): the p95 of a streaky edit loop is tighter than a legit exploration, so 25 is a floor) which hooks/semantic_breaker.js reads. Progress mirrors the hook: Edit/Write/MultiEdit/NotebookEdit,
a commit command, a proof run turning red -> green. (A moved git HEAD is not derivable from a transcript.)
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import session_autopsy as sa  # noqa: E402

EDITS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
COMMIT = re.compile(r"\bcommit\b")
PROOF = re.compile(r"\b(pytest|unittest)\b|\btest[_-]\w*\.(py|js)\b|\bnode\s+--test\b|\bnpm\s+(run\s+)?test\b", re.I)
CONFIG = HERE.parent / "vault" / "config" / "semantic-breaker.json"
DEFAULT = 25


def gaps(path: Path) -> list[int]:
    """Calls between consecutive progress events (and the trailing run, which is censored, kept out)."""
    out, run, red = [], 0, False
    for c in sa._scan(Path(path), "main"):
        if c.get("epoch"):
            continue
        for uid, name, inp in c["uses"]:
            res = c["results"].get(uid)
            cmd = inp.get("command", "") if isinstance(inp.get("command"), str) else ""
            prog = False
            if name in EDITS:
                prog = True
            elif name in ("Bash", "PowerShell") and cmd:
                if COMMIT.search(cmd) and res is not None and not sa._is_fail(res):
                    prog = True
                elif PROOF.search(cmd) and res is not None:
                    bad = sa._is_fail(res)
                    if red and not bad:
                        prog = True
                    red = bad
            run += 1
            if prog:
                out.append(run - 1)       # calls strictly between two progress events
                run = 0
    return out


def pctl(xs: list[int], p: float) -> int:
    s = sorted(xs)
    return s[min(len(s) - 1, max(0, math.ceil(p * len(s)) - 1))]


def calibrate(paths: list[str]) -> dict:
    per, allg = {}, []
    for p in paths:
        g = gaps(Path(p))
        per[Path(p).stem] = {"events": len(g), "max": max(g) if g else None}
        allg += g
    ok = len([v for v in per.values() if v["events"]]) >= 5 and allg
    return {"transcripts": len(paths), "usable": len([v for v in per.values() if v["events"]]),
            "gaps": len(allg), "p50": pctl(allg, .5) if allg else None, "p95": pctl(allg, .95) if allg else None,
            "max": max(allg) if allg else None, "calls_p95": pctl(allg, .95) if ok else None,
            "default_used": not ok, "default": DEFAULT, "per_transcript": per}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=["calibrate"])
    ap.add_argument("transcripts", nargs="+")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    r = calibrate(a.transcripts)
    print(json.dumps(r, indent=2))
    if a.write and r["calls_p95"]:
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(json.dumps({"calls_p95": r["calls_p95"], "trip_calls": max(r["calls_p95"], DEFAULT), "gaps": r["gaps"], "usable": r["usable"],
                                      "p50": r["p50"], "max": r["max"]}, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
