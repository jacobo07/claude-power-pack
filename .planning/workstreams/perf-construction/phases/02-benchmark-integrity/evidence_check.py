"""evidence_check.py - phase-local fixture: structural check of 02-EVIDENCE.md (read-only, stdlib only).

Usage: python3 -I evidence_check.py <02-EVIDENCE.md> [--repo DIR]
Checks: eight numbered level-2 headings ("## 1." to "## 8."); a table row for each of P01, P03, P04, P06
and P07; the P07 row says BLOCKED-ON-ORIGIN-AUDIT; the words UNJUDGED and LP-03 occur; every cited
`records/<file>` path exists next to the evidence file; every cited `tools/<file>` path exists under
--repo; every "commit <hex>" token resolves with `git cat-file -e`. It cannot judge whether the
evidence is TRUE, only that nothing it cites is missing. Exit 0 when no problem is found, 1 otherwise.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

HEADINGS = ["## %d." % i for i in range(1, 9)]
PIDS = ["P01", "P03", "P04", "P06", "P07"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("evidence")
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    ev = Path(a.evidence)
    repo = Path(a.repo)
    text = ev.read_text(encoding="utf-8")
    problems = []
    for h in HEADINGS:
        if not re.search(r"^" + re.escape(h), text, re.M):
            problems.append("missing heading starting with '%s'" % h)
    for pid in PIDS:
        rows = re.findall(r"^\|\s*" + pid + r"\s*\|.*$", text, re.M)
        if not rows:
            problems.append("no table row for %s" % pid)
        elif pid == "P07" and not any("BLOCKED-ON-ORIGIN-AUDIT" in r for r in rows):
            problems.append("P07 row does not say BLOCKED-ON-ORIGIN-AUDIT")
    for word in ("UNJUDGED", "LP-03"):
        if word not in text:
            problems.append("text lacks '%s'" % word)
    for rel in sorted(set(re.findall(r"records/[A-Za-z0-9_.\-]+", text))):
        if not (ev.parent / rel).is_file():
            problems.append("cited record not found: " + rel)
    for rel in sorted(set(re.findall(r"\btools/[A-Za-z0-9_./\-]+\.py", text))):
        if not (repo / rel).is_file():
            problems.append("cited tool not found: " + rel)
    for h in sorted(set(re.findall(r"\bcommit ([0-9a-f]{7,40})\b", text))):
        r = subprocess.run(["git", "cat-file", "-e", h + "^{commit}"], cwd=str(repo),
                           capture_output=True, text=True)
        if r.returncode != 0:
            problems.append("cited commit does not resolve: " + h)
    for p in problems:
        print("EVIDENCE_PROBLEM: " + p)
    print("EVIDENCE_CHECK problems=%d" % len(problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
