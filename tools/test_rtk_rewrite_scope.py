#!/usr/bin/env python3
"""V-RTKSCOPE gates: rtk-rewrite.js rewrites Bash commands only.

Measured 2026-09-30: both dispatchers route PowerShell through the same chain, and the hook never read
tool_name, so a PowerShell `gh pr list` became `"...\\rtk.exe" gh pr list` -- a string followed by stray
tokens -- and failed with ParserError (Token 'gh' inesperado). A POSIX rewrite is only valid for the
POSIX shell. The positive controls (Bash, and a payload with no tool_name) prove the hook still rewrites,
so the scope gate cannot pass by the hook doing nothing. Needs the real rtk binary; without it: SKIP.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "modules" / "rtk-core" / "rtk-rewrite.js"
RTK = Path(os.environ.get("RTK_BIN") or Path.home() / ".claude" / "bin" / "rtk.exe")
NODE = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
passes = fails = skips = 0


def check(gate, cond, ev):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"  [{'PASS' if cond else 'FAIL'}] {gate}: {ev}")


def hook(payload: dict) -> str:
    r = subprocess.run([NODE, str(HOOK)], input=json.dumps(payload), capture_output=True, text=True,
                       encoding="utf-8", timeout=30, env={**os.environ, "RTK_BIN": str(RTK)})
    return r.stdout.strip()


def rewritten(out: str) -> str | None:
    if not out:
        return None
    return ((json.loads(out).get("hookSpecificOutput") or {}).get("updatedInput") or {}).get("command")


def main() -> int:
    global skips
    if not RTK.is_file():
        skips += 1
        print(f"  [SKIP] V-RTKSCOPE-*: rtk binary absent at {RTK}")
        print(f"RTKSCOPE_PASS={passes}/{passes + fails}  skipped={skips}")
        return 0
    cmd = "gh pr list --limit 1"
    bash = rewritten(hook({"tool_name": "Bash", "session_id": "t", "tool_input": {"command": cmd}}))
    check("V-RTKSCOPE-BASH-REWRITES", bool(bash) and "rtk" in bash and bash != cmd, bash)
    legacy = rewritten(hook({"session_id": "t", "tool_input": {"command": cmd}}))
    check("V-RTKSCOPE-NO-TOOLNAME-REWRITES", bool(legacy) and legacy != cmd, legacy)
    ps = hook({"tool_name": "PowerShell", "session_id": "t", "tool_input": {"command": cmd}})
    check("V-RTKSCOPE-POWERSHELL-UNTOUCHED", ps == "", ps or "(pass-through)")
    other = hook({"tool_name": "Monitor", "session_id": "t", "tool_input": {"command": cmd}})
    check("V-RTKSCOPE-OTHER-TOOL-UNTOUCHED", other == "", other or "(pass-through)")
    print(f"RTKSCOPE_PASS={passes}/{passes + fails}  skipped={skips}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
