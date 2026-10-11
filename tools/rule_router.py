#!/usr/bin/env python
"""Rule router: key a unit (goal / root / unit id) to the deferred-backlog D-rows that bind it.

    python tools/rule_router.py --goal cp50-c2 [--unit C2c] [--root <path>]

Why (plan cpx s2): the coordinator-cost rule is filed as prose inside other programmes' rows and no
code read deferred-backlog.md. Rows are found by streaming the file line by line and keeping only
the requested `## Dnn` sections, capped at MAX_LINES each -- the backlog is never materialized.
Fail soft: a missing backlog or row returns what was found and appends a line to the log.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BACKLOG = REPO / "vault" / "plans" / "deferred-backlog.md"
LOG = REPO / "vault" / "programs" / "cpx" / "rule_router.log"
MAX_LINES = 12

# (matcher over unit keys) -> rows. A unit is keyed by goal, root path or unit id.
ROUTES = [
    {"name": "cp50-c2", "goal": {"cp50-c2"}, "root": re.compile(r"wt_cp50_c2", re.I),
     "rows": ["D21", "D22", "D23", "D24", "D26"]},
]
_HEAD = re.compile(r"^## (D\d+)\b")


def _log(log: Path, msg: str) -> None:
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a", encoding="utf-8") as f:
            f.write(f"{_dt.datetime.now().isoformat(timespec='seconds')} rule_router {msg}\n")
    except OSError:
        pass


def wanted_rows(unit: dict) -> list[str]:
    out: list[str] = []
    for r in ROUTES:
        if str(unit.get("goal", "")) in r["goal"] or r["root"].search(str(unit.get("root", ""))):
            out += [x for x in r["rows"] if x not in out]
    return out


def route(unit: dict, backlog: Path = BACKLOG, log: Path = LOG) -> list[dict]:
    want = wanted_rows(unit)
    if not want:
        return []
    found: dict[str, dict] = {}
    try:
        with open(backlog, encoding="utf-8") as f:
            cur = None
            for n, line in enumerate(f, 1):
                m = _HEAD.match(line)
                if m:
                    cur = m.group(1) if m.group(1) in want else None
                    if cur:
                        found[cur] = {"id": cur, "line": n, "lines": [line.rstrip()]}
                elif cur and len(found[cur]["lines"]) < MAX_LINES:
                    found[cur]["lines"].append(line.rstrip())
    except OSError as e:
        _log(log, f"backlog missing/unreadable {backlog}: {e.__class__.__name__}")
        return []
    for w in want:
        if w not in found:
            _log(log, f"row {w} absent in {backlog}")
    return [{"id": i, "line": found[i]["line"], "text": "\n".join(found[i]["lines"]).rstrip()}
            for i in want if i in found]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--goal", default="")
    ap.add_argument("--root", default="")
    ap.add_argument("--unit", default="")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rows = route({"goal": a.goal, "root": a.root, "unit": a.unit})
    if a.json:
        print(json.dumps(rows))
    for r in rows:
        print(f"--- {r['id']} (deferred-backlog.md:{r['line']})\n{r['text']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
