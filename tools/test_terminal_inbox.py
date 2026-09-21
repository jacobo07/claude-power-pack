#!/usr/bin/env python3
"""V-INBOX gate: runs extension/src/terminal_inbox.js --selftest under node.

The module decides whether a Cursor window may type a resume line into one of its
terminals for a Claude Code session (auto-compact / long-run resume without the
foreground window). Typing into the wrong terminal submits a command in another
session, so the self-test drives every refusal: other window, ambiguous match,
dialog open (status "waiting"), busy, expired, reused pid, other session, no
session file, multi-line text. Since 2026-09-21 it also drives both poles of
`argumentTail`, the /compact argument-submission rule that used to live inline in
extension.js where no gate could reach it.

A floor, not an equality (repaired 2026-09-21). The count was compared with `==`
against a number that the very next added case invalidates, so this gate had been
RED purely because the self-test grew -- and a gate that goes red for growing
teaches the next reader to re-baseline it without looking, which is how a real
loss gets waved through. The load-bearing half is unchanged and must stay: a
self-test that silently LOST cases is not green.

The comparison is also parsed rather than matched as a substring. `ok=12` is
contained in `ok=120`, so the old form would have accepted a count it never meant
to accept.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "extension" / "src" / "terminal_inbox.js"

# Population floor. Raise it deliberately when cases are added; never lower it to
# make a run pass. 30 as of 2026-09-21 (23 + 7 argumentTail cases).
EXPECTED_OK = 30

SUMMARY = re.compile(r"TERMINAL_INBOX_SELFTEST=PASS ok=(\d+)\s*$", re.MULTILINE)


def main() -> int:
    node = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
    if not Path(node).is_file():
        # The verifier could not run. That is NOT a verdict about the subject,
        # and reporting it as one sends the reader to fix code that is fine.
        print(f"TERMINAL_INBOX_PASS=0/1  threshold=1/1  HARNESS-FAILED: node not found at {node}")
        return 2
    try:
        r = subprocess.run([node, str(MODULE), "--selftest"],
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"TERMINAL_INBOX_PASS=0/1  threshold=1/1  HARNESS-FAILED: {exc}")
        return 2

    print(r.stdout.strip())
    m = SUMMARY.search(r.stdout)
    if r.returncode != 0 or m is None:
        # Subject invalid: the self-test ran and reported failing cases (or died
        # before printing its summary, which is the same thing from here).
        print(f"TERMINAL_INBOX_PASS=0/1  threshold=1/1  "
              f"(exit={r.returncode}, summary={'absent' if m is None else 'present'})")
        return 1

    count = int(m.group(1))
    ok = count >= EXPECTED_OK
    if not ok:
        print(f"  LOST CASES: self-test reported ok={count}, floor is {EXPECTED_OK}. "
              f"A self-test that silently lost cases is not green.")
    print(f"TERMINAL_INBOX_PASS={'1/1' if ok else '0/1'}  threshold=1/1  ok={count}/{EXPECTED_OK}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
