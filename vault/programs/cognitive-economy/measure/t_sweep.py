#!/usr/bin/env python
"""t_sweep.py -- pillar T (institutional GC). Read-only, zero model calls.

1. Modules: `modules/liveness/reachability.gate()` (imported, never edited). Every gate OFFENDER (unreachable,
   undeclared, not standing debt) gets two facts that decide whether it may be PROPOSED for retirement:
     age      days since the last commit touching its file (git log -1, this checkout's history)
     tested   some test file names it (dotted import or path): tools/*.py, tests/**/*.py, modules/**/test_*.py
   Disposition (rule written before running; the test aperture was widened after run 1 read tools/ only):
     ACTIVE            touched within 14 days -- someone is building it; never proposed
     DORMANT_TESTED    older, a test file names it -- declare (LIBRARY/PLANNED) or wire; Owner decides
     RETIRE_CANDIDATE  older, no test file names it -- proposed for deletion; Owner decides
2. Skills: every skill directory installed under ~/.claude/skills (SKILL.md present) and the number of times it was
   invoked in D-W7 transcripts (Skill tool_use `skill` input, or a `<command-name>/x` slash invocation). Zero is
   reported as "not invoked in D-W7", which is a fact about one week, not a verdict of uselessness.

    python t_sweep.py [--json OUT]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))
from modules.liveness import reachability as rb  # noqa: E402
import turns  # noqa: E402  (W_START, W_END, DB access)

GIT = r"C:\Program Files\Git\cmd\git.exe"
NOW = datetime(2026, 10, 3, tzinfo=timezone.utc).timestamp()
ACTIVE_DAYS = 14
SKILLS = Path.home() / ".claude" / "skills"
CMD = re.compile(r"<command-name>/?([A-Za-z0-9:_-]+)</command-name>")


def last_commit_ts(path: Path) -> float | None:
    r = subprocess.run([GIT, "-C", str(REPO), "log", "-1", "--format=%ct", "--", str(path)],
                       capture_output=True, text=True, timeout=60)
    return float(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None


def modules_part() -> dict:
    passed, offs, rows = rb.gate(REPO)
    # Where tests live in this repo: tools/*.py (V-gates), tests/**, and module-local test_*.py. An earlier
    # version read tools/ only and proposed a package with five tests under tests/ as untested.
    test_files = [*(REPO / "tools").glob("*.py"), *(REPO / "tests").rglob("*.py"),
                  *(REPO / "modules").rglob("test_*.py")]
    tools_text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in test_files)
    out = []
    for r in offs:
        path = rb._unit_path(REPO, r["unit"])
        ts = last_commit_ts(path)
        age = None if ts is None else round((NOW - ts) / 86400, 1)
        dotted = "modules." + r["unit"].replace("/", ".")
        tested = dotted in tools_text or f"modules/{r['unit']}" in tools_text
        if age is not None and age <= ACTIVE_DAYS:
            disp = "ACTIVE"
        elif age is None:
            disp = "ACTIVE"            # never committed: work in progress in this tree
        elif tested:
            disp = "DORMANT_TESTED"
        else:
            disp = "RETIRE_CANDIDATE"
        out.append({"unit": r["unit"], "age_days": age, "tested_in_tools": tested, "disposition": disp})
    stat = Counter(r["status"] for r in rows)
    return {"gate_passed": passed, "modules": len(rows), "status": dict(stat), "offenders": len(offs),
            "dispositions": dict(Counter(o["disposition"] for o in out)), "rows": out}


def skills_part() -> dict:
    installed = sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md"))
    con = turns.ro_connect()
    files = [r[0] for r in con.execute("SELECT DISTINCT file FROM calls WHERE ts > ? AND ts <= ?",
                                       (turns.W_START, turns.W_END))]
    con.close()
    used = Counter()
    for fp in files:
        try:
            fh = open(fp, encoding="utf-8", errors="replace")
        except OSError:
            continue
        with fh:
            for line in fh:
                if '"Skill"' in line:
                    try:
                        o = json.loads(line)
                    except ValueError:
                        continue
                    m = o.get("message") if isinstance(o.get("message"), dict) else {}
                    for c in m.get("content") or []:
                        if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Skill":
                            s = str((c.get("input") or {}).get("skill", ""))
                            used[s.split(":")[-1]] += 1
                if "<command-name>" in line:
                    for name in CMD.findall(line):
                        used[name.split(":")[-1]] += 1
    rows = [{"skill": s, "invocations_DW7": used.get(s, 0)} for s in installed]
    return {"installed": len(installed), "invoked_in_DW7": sum(1 for r in rows if r["invocations_DW7"]),
            "not_invoked_in_DW7": [r["skill"] for r in rows if not r["invocations_DW7"]],
            "rows": rows, "transcripts_scanned": len(files)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    res = {"modules": modules_part(), "skills": skills_part()}
    blob = json.dumps(res, indent=1, sort_keys=True)
    if a.json:
        Path(a.json).write_text(blob, encoding="utf-8", newline="\n")
    m, s = res["modules"], res["skills"]
    print(json.dumps({"modules": {k: v for k, v in m.items() if k != "rows"},
                      "skills": {"installed": s["installed"], "invoked_in_DW7": s["invoked_in_DW7"],
                                 "not_invoked": len(s["not_invoked_in_DW7"])}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
