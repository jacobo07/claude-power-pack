#!/usr/bin/env python3
"""measure_hook_event.py -- empirical, shell-free timing of the hooks that
fire for ONE Claude Code event in ~/.claude/settings.json.

Why a new tool (not measure_session_start.py): that tool runs each hook via
``subprocess.run(cmd, shell=True)``. On Windows shell=True is cmd.exe, which
CANNOT resolve the Git-Bash-style interpreter path the hooks are registered
with (``"/c/Program Files/nodejs/node.exe"``). So 9/10 hooks *fast-fail*
(rc=1, ~16 ms) and the recorded "timing" is cmd.exe's failure latency, not
the hook. This tool parses the SCRIPT path out of each command and runs it
with the correct interpreter directly (shell=False) -- the same model
hook-dispatcher.js runChain() uses -- so the timing is real.

Headline metric for the hub-fold task: ``entry_count`` = the number of
top-level settings.json entries Claude Code spawns for the event (each is a
separate process). Folding standalone hooks into hook-dispatcher.js reduces
this. ``dispatcher_entries`` / ``standalone_entries`` split shows how much
fold headroom remains.

Usage:
    python tools/measure_hook_event.py --event PreToolUse --tool Bash
    python tools/measure_hook_event.py --event Stop --json
    python tools/measure_hook_event.py --event UserPromptSubmit --json
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
PER_HOOK_TIMEOUT_S = 20
SLOW_INDIVIDUAL_MS = 300

# Interpreter resolution (absolute, no PATH guessing failures).
_NODE = (shutil.which("node")
         or r"C:\Program Files\nodejs\node.exe")
_PY = sys.executable
_PS = shutil.which("powershell") or "powershell.exe"

# Script-path extractor: a Windows abs path OR an msys /c/... path ending in
# a known hook extension. Quotes are stripped by the capture bounds.
_SCRIPT_RE = re.compile(
    r"""(?:["']?)(
        (?:[A-Za-z]:[\\/]|/[A-Za-z]/)   # C:\ or C:/ or /c/
        [^"']*?
        \.(?:js|cjs|mjs|py|ps1)
    )(?:["']?)""",
    re.VERBOSE,
)
_EVENT_ARG_RE = re.compile(r"--event=(\S+)")


def _msys_to_win(p: str) -> str:
    """/c/Program Files/x -> C:\\Program Files\\x ; leave Windows paths as-is."""
    m = re.match(r"^/([A-Za-z])/(.*)$", p)
    if m:
        return f"{m.group(1).upper()}:\\" + m.group(2).replace("/", "\\")
    return p


def _interp_for(script: str):
    s = script.lower()
    if s.endswith((".js", ".cjs", ".mjs")):
        return _NODE
    if s.endswith(".py"):
        return _PY
    if s.endswith(".ps1"):
        return _PS
    return None


def parse_command(cmd: str):
    """Return (interp, [args...], kind) or None if not a runnable hook cmd.

    A ``test -f "X" || exit 0; node "X"`` guard is a real conditional spawn;
    the guard's path IS the hook script, so the script regex finds it and we
    time the hook body directly (the shell guard itself is sub-ms)."""
    if not cmd:
        return None
    m = _SCRIPT_RE.search(cmd)
    if not m:
        return None
    script = _msys_to_win(m.group(1))
    interp = _interp_for(script)
    if not interp:
        return None
    args = [script]
    ev = _EVENT_ARG_RE.search(cmd)
    if ev:
        args.append("--event=" + ev.group(1))
    kind = "dispatcher" if "hook-dispatcher" in script.lower() else "standalone"
    if interp.lower().endswith("powershell.exe") or interp == _PS:
        if script.lower().endswith(".ps1"):
            args = ["-NoProfile", "-NonInteractive", "-ExecutionPolicy",
                    "Bypass", "-File", script]
    return (interp, args, kind)


def _matcher_matches(matcher: str, tool: str | None) -> bool:
    if not matcher:                 # empty/absent matcher = all tools
        return True
    if tool is None:                # event has no tool dimension (Stop, UPS)
        return True
    parts = [p.strip() for p in matcher.split("|") if p.strip()]
    if "*" in parts:
        return True
    return tool in parts


def _enumerate(event: str, tool: str | None):
    raw = SETTINGS_PATH.read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    groups = data.get("hooks", {}).get(event, [])
    out = []
    for entry in groups:
        if not _matcher_matches(entry.get("matcher", ""), tool):
            continue
        for hh in entry.get("hooks", []):
            cmd = hh.get("command", "")
            parsed = parse_command(cmd)
            if parsed:
                out.append((cmd, parsed))
    return out


def _payload(event: str, tool: str | None) -> str:
    if event == "PreToolUse":
        if tool == "Bash":
            return json.dumps({"tool_name": "Bash",
                               "tool_input": {"command": "ls"}})
        return json.dumps({"tool_name": tool or "Edit", "tool_input": {
            "file_path": str(SETTINGS_PATH.parent / "_measure_probe.tmp"),
            "old_string": "a", "new_string": "b"}})
    if event == "PostToolUse":
        return json.dumps({"tool_name": tool or "Bash",
                           "tool_input": {"command": "ls"},
                           "tool_response": {"success": True}})
    if event == "UserPromptSubmit":
        return json.dumps({"prompt": "measurement probe"})
    return "{}"


def _time_one(interp: str, args: list[str], stdin: str):
    t0 = time.perf_counter()
    try:
        r = subprocess.run([interp, *args], input=stdin,
                           capture_output=True, text=True,
                           timeout=PER_HOOK_TIMEOUT_S)
        rc = r.returncode
    except subprocess.TimeoutExpired:
        rc = -1
    except Exception:  # noqa: BLE001
        rc = -2
    return ((time.perf_counter() - t0) * 1000, rc)


def measure(event: str, tool: str | None) -> dict:
    entries = _enumerate(event, tool)
    stdin = _payload(event, tool)
    results = []
    for cmd, (interp, args, kind) in entries:
        ms, rc = _time_one(interp, args, stdin)
        results.append({"script": Path(args[-1]).name if args else cmd[:40],
                        "kind": kind, "ms": round(ms, 1), "rc": rc})
    disp = sum(1 for r in results if r["kind"] == "dispatcher")
    return {
        "event": event,
        "tool": tool,
        "entry_count": len(results),
        "dispatcher_entries": disp,
        "standalone_entries": len(results) - disp,
        "individual_max_ms": round(max((r["ms"] for r in results),
                                       default=0.0), 1),
        "total_serial_ms": round(sum(r["ms"] for r in results), 1),
        "slow_hooks": [r["script"] for r in results
                       if r["ms"] > SLOW_INDIVIDUAL_MS],
        "results": results,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--event", required=True,
                    help="PreToolUse | PostToolUse | Stop | "
                         "UserPromptSubmit | SessionStart")
    ap.add_argument("--tool", default=None,
                    help="tool_name for matcher filtering (e.g. Bash, Edit)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    payload = measure(args.event, args.tool)

    if args.json:
        sys.stdout.write(json.dumps(payload, indent=2))
        return 0

    print("=" * 72)
    print(f"Hook timing: {args.event}"
          + (f" / tool={args.tool}" if args.tool else ""))
    print("=" * 72)
    print(f"Top-level entries (process spawns): {payload['entry_count']}"
          f"  (dispatcher={payload['dispatcher_entries']} "
          f"standalone={payload['standalone_entries']})")
    print()
    for r in payload["results"]:
        tag = "SLOW" if r["ms"] > SLOW_INDIVIDUAL_MS else "ok  "
        print(f"  [{tag}] {r['ms']:8.1f} ms rc={r['rc']:<3} "
              f"{r['kind']:<10} {r['script']}")
    print()
    print(f"individual_max_ms : {payload['individual_max_ms']}")
    print(f"total_serial_ms   : {payload['total_serial_ms']}")
    print(f"slow (>{SLOW_INDIVIDUAL_MS}ms)     : {payload['slow_hooks']}")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
