#!/usr/bin/env python
"""V-WUP-* gates for tools/wu_packet.py: compile -> verify CURRENT; a changed claim, a moved HEAD -> STALE."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE / "wu_packet.py"
GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@t"}
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def run(*args):
    p = subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout.strip()


def git(repo, *args):
    subprocess.run([GIT, "-C", str(repo), "-c", "commit.gpgsign=false", *args], check=True,
                   capture_output=True, env=ENV)


IR = {"gates": [{"id": "G1", "text": "gate one"}, {"id": "G2", "text": "gate two"}],
      "units": [{"id": "U", "title": "unit u", "est_calls": 2, "reserve_calls": 1, "profile": "top-level-worker",
                 "ctx_tokens": 1000, "context": ["src/a.ts"], "acceptance": ["npm test"],
                 "capabilities": ["edit"]}],
      "claims": [{"id": "c1", "title": "first", "unit": "U", "gates": ["G1"]},
                 {"id": "c2", "title": "second", "unit": "U", "gates": ["G2"]},
                 {"id": "c3", "title": "other unit", "unit": "X", "gates": ["G1"]}]}


def main() -> int:
    d = Path(tempfile.mkdtemp(prefix="wup-test-"))
    repo = d / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    (repo / "f.txt").write_text("1", encoding="utf-8")
    git(repo, "add", "f.txt")
    git(repo, "commit", "-q", "-m", "one")
    ir = d / "ir.json"
    ir.write_text(json.dumps(IR), encoding="utf-8")
    pk = d / "packet.md"
    rc, _ = run("compile", "--claims", str(ir), "--unit", "U", "--repo", str(repo), "--out", str(pk))
    text = pk.read_text(encoding="utf-8") if pk.exists() else ""
    check("V-WUP-COMPILE", rc == 0 and "fingerprint:" in text and "- c1: first" in text and "- c3" not in text,
          f"rc={rc}")
    check("V-WUP-BUDGET-HARD-STOP-3X", "hard stop: 6 calls" in text and "reserve calls: 1" in text)
    check("V-WUP-SECTIONS", all(s in text for s in ("## Context", "- src/a.ts", "## Acceptance", "- npm test",
                                                      "## Capabilities", "## Progress rule")))
    rc, out = run("verify", str(pk))
    check("V-WUP-VERIFY-CURRENT", rc == 0 and out == "CURRENT", f"rc={rc} {out}")

    IR2 = json.loads(json.dumps(IR))
    IR2["claims"][0]["title"] = "first, changed"
    ir.write_text(json.dumps(IR2), encoding="utf-8")
    rc, out = run("verify", str(pk))
    check("V-WUP-CLAIM-CHANGE-STALE", rc == 3 and out == "STALE", f"rc={rc} {out}")
    ir.write_text(json.dumps(IR), encoding="utf-8")
    rc, out = run("verify", str(pk))
    check("V-WUP-RESTORED-CURRENT-CONTROL", rc == 0 and out == "CURRENT", f"rc={rc} {out}")

    (repo / "f.txt").write_text("2", encoding="utf-8")
    git(repo, "commit", "-q", "-am", "two")
    rc, out = run("verify", str(pk))
    check("V-WUP-HEAD-MOVE-STALE", rc == 3 and out == "STALE", f"rc={rc} {out}")

    rc, _ = run("compile", "--claims", str(ir), "--unit", "NOPE", "--repo", str(repo), "--out", str(d / "n.md"))
    check("V-WUP-UNKNOWN-UNIT-REFUSED", rc == 2 and not (d / "n.md").exists(), f"rc={rc}")

    print(f"WUP_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
