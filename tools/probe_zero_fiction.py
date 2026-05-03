#!/usr/bin/env python
"""BL-0048 — Empirical probe: zero-fiction-gate.js actually blocks
literal placeholder copy on Edit|Write|MultiEdit.

Sends 4 synthetic PreToolUse events to the gate (via stdin) and
asserts:

  case 1 — clean code            -> {} (no advisory, no block)
  case 2 — literal soft-launch   -> permissionDecision="ask"
  case 3 — TO+DO comment         -> additionalContext (soft advisory)
  case 4 — NotImpl raise         -> permissionDecision="ask"

Anti-quine: every literal placeholder string is built at runtime via
concatenation so this probe file ITSELF does not contain the lexical
patterns the gate scans for. Same trick zero-fiction-gate.js uses on
its own pattern table.
"""
from __future__ import annotations

import datetime as _dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "modules" / "zero-crash" / "hooks" / "zero-fiction-gate.js"
OUT = ROOT / "vault" / "audits" / "probe_zero_fiction.json"

# --- anti-quine literals (do NOT inline these as plain strings) ---
_S = chr(83)
COMING_SOON = "Com" + "ing " + "Soon"
TODO_TAG = "TO" + "DO"
NOT_IMPL = "NotImple" + "mentedError"
# -------------------------------------------------------------------

CASES = [
    {
        "name": "clean_js",
        "tool_name": "Write",
        "content": "console.log('hello world');",
        "expect": "clean",
    },
    {
        "name": "literal_soft_launch",
        "tool_name": "Write",
        "content": f"<button>{COMING_SOON}</button>",
        "expect": "hard",
    },
    {
        "name": "todo_comment_line_leading",
        "tool_name": "Edit",
        "content": f"function foo() {{\n  // {TODO_TAG}: implement\n  return 1;\n}}",
        "expect": "soft",
    },
    {
        "name": "todo_comment_inline_should_pass",
        "tool_name": "Edit",
        "content": f"function bar() {{ /* {TODO_TAG}: inline */ return 2; }}",
        "expect": "clean",
    },
    {
        "name": "not_implemented_raise",
        "tool_name": "Write",
        "content": f"def bar():\n    raise {NOT_IMPL}('soon')\n",
        "expect": "hard",
    },
]


def _node() -> str | None:
    return shutil.which("node")


def _run_gate(case: dict) -> dict:
    payload = {
        "tool_name": case["tool_name"],
        "tool_input": {
            "file_path": "C:/tmp/probe_target.txt",
            "content": case["content"],
            "new_string": case["content"],
            "old_string": "x",
        },
        "session_id": "probe-bl48-" + case["name"],
    }
    proc = subprocess.run(
        [_node(), str(GATE)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=8,
    )
    raw = (proc.stdout or "").strip()
    try:
        out = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {"_raw_stdout": raw, "_stderr": proc.stderr}
    return out


def _classify(out: dict) -> str:
    hso = out.get("hookSpecificOutput") or {}
    if hso.get("permissionDecision") == "ask":
        return "hard"
    if "additionalContext" in hso:
        return "soft"
    if not out:
        return "clean"
    return "unknown"


def main() -> int:
    if not GATE.exists():
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"error": f"gate not found at {GATE}"}, indent=2))
        print(f"FAIL: gate absent at {GATE}", file=sys.stderr)
        return 2
    if not _node():
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"error": "node not on PATH"}, indent=2))
        print("FAIL: node missing", file=sys.stderr)
        return 2

    results = []
    for c in CASES:
        out = _run_gate(c)
        actual = _classify(out)
        results.append(
            {
                "case": c["name"],
                "tool": c["tool_name"],
                "expect": c["expect"],
                "actual": actual,
                "raw_output": out,
                "pass": actual == c["expect"],
            }
        )

    verdict = {
        "probe": "BL-0048 / MC-SYS-94 — zero-fiction-gate enforcement",
        "iso_ts": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "gate_path": str(GATE),
        "cases": results,
        "all_pass": all(r["pass"] for r in results),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    print(json.dumps({"all_pass": verdict["all_pass"], "out": str(OUT)}))
    return 0 if verdict["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
