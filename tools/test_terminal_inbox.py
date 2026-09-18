#!/usr/bin/env python3
"""V-INBOX gate: runs extension/src/terminal_inbox.js --selftest under node.

The module decides whether a Cursor window may type a resume line into one of its
terminals for a Claude Code session (auto-compact / long-run resume without the
foreground window). Typing into the wrong terminal submits a command in another
session, so the self-test drives every refusal: other window, ambiguous match,
dialog open (status "waiting"), busy, expired, reused pid, other session, no
session file, multi-line text.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "extension" / "src" / "terminal_inbox.js"
EXPECTED_OK = 12  # population floor: a self-test that silently lost cases is not green


def main() -> int:
    node = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
    r = subprocess.run([node, str(MODULE), "--selftest"], capture_output=True, text=True, timeout=60)
    print(r.stdout.strip())
    ok = r.returncode == 0 and f"TERMINAL_INBOX_SELFTEST=PASS ok={EXPECTED_OK}" in r.stdout
    print(f"TERMINAL_INBOX_PASS={'1/1' if ok else '0/1'}  threshold=1/1")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
