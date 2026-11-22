"""V-SL-* gates: the PP statusline context meter shows the RAW used percentage.

Owner 2026-09-29: the GSD statusline (~/.claude/hooks/gsd-statusline.js) subtracted a
16.5% autocompact buffer from remaining_percentage and rescaled the rest, so the bar read
48% at a real 40% and 99% at a real 83% -- ~20 points above the context watchdog and the
rollover wall, which both judge 100 - remaining. A `/gsd-update` put the buffer back once
(found 2026-11-09). Owner 2026-11-09: build it inside PP instead of depending on GSD, so
the statusline is now hooks/pp-statusline.js, PP-owned and standalone.

This drives the LIVE copy (~/.claude/hooks/pp-statusline.js) with real stdin payloads, and
checks the live copy has not drifted from the repo copy. SL_TEST_SCRIPT points it at
another copy (mutation drill); the drift gate is skipped then.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_SCRIPT = Path(__file__).resolve().parent.parent / "hooks" / "pp-statusline.js"
LIVE_SCRIPT = Path.home() / ".claude" / "hooks" / "pp-statusline.js"
OVERRIDE = os.environ.get("SL_TEST_SCRIPT")
SCRIPT = Path(OVERRIDE) if OVERRIDE else LIVE_SCRIPT
NODE = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
ANSI = re.compile(r"\x1b\[[0-9;]*m")
METER = re.compile(r"[\u2588\u2591]{10} (\d+)%")

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def run(script, remaining, session, env=None):
    """Run a statusline once; return (percent shown or None, return code, plain stdout)."""
    ctx = {} if remaining is None else {"remaining_percentage": remaining,
                                        "total_tokens": 1_000_000}
    payload = {"model": {"display_name": "Opus"},
               "workspace": {"current_dir": tempfile.gettempdir()},
               "session_id": session, "context_window": ctx}
    # Bytes, not text: no BOM, no newline translation -- the script JSON.parses stdin.
    r = subprocess.run([NODE, str(script)], input=json.dumps(payload).encode("utf-8"),
                       capture_output=True, timeout=30, env=env)
    out = ANSI.sub("", r.stdout.decode("utf-8", "replace"))
    m = METER.search(out)
    return (int(m.group(1)) if m else None), r.returncode, out


def render(remaining, session):
    shown, rc, _ = run(SCRIPT, remaining, session)
    return shown, rc


def gate_standalone(session):
    """A copy alone in an empty directory must still render: no GSD, no ./lib."""
    with tempfile.TemporaryDirectory() as d:
        lone = Path(d) / "pp-statusline.js"
        shutil.copyfile(SCRIPT, lone)
        shown, rc, _ = run(lone, 60, session)
    check("V-SL-STANDALONE", shown == 40 and rc == 0, f"isolated copy shown={shown} rc={rc}")


def gate_orca_forward(session):
    """When Orca's hook exists under HOME, it receives the exact payload."""
    with tempfile.TemporaryDirectory() as home:
        hooks = Path(home) / ".orca" / "agent-hooks"
        hooks.mkdir(parents=True)
        sink = Path(home) / "received.json"
        if os.name == "nt":
            (hooks / "claude-statusline.cmd").write_text(
                f'@echo off\r\n"%SystemRoot%\\System32\\more.com" > "{sink}"\r\n', encoding="ascii")
        else:
            hook = hooks / "claude-statusline.sh"
            hook.write_text(f'#!/bin/sh\ncat > "{sink}"\n', encoding="ascii")
            hook.chmod(0o755)
        env = dict(os.environ, HOME=home, USERPROFILE=home)
        shown, rc, _ = run(SCRIPT, 60, session, env=env)
        try:
            got = json.loads(sink.read_text(encoding="utf-8", errors="replace").strip())
            ok = got.get("session_id") == session
            ev = f"orca got session_id={got.get('session_id')}"
        except (OSError, ValueError) as exc:
            ok, ev = False, f"orca received nothing usable: {exc}"
    check("V-SL-ORCA-FORWARD", ok and shown == 40 and rc == 0, f"{ev}; bar={shown} rc={rc}")


def main():
    if not SCRIPT.exists():
        print(f"HARNESS-FAILED: statusline not found at {SCRIPT}")
        return 2
    session = f"sltest-{os.getpid()}"
    bridge = Path(tempfile.gettempdir()) / f"claude-ctx-{session}.json"
    try:
        # Precondition: the script renders a meter at all. Without it every
        # percentage gate below would be judging a crash, not a formula.
        shown, rc = render(50, session)
        if shown is None:
            print(f"HARNESS-FAILED: no meter rendered (rc={rc}); check {SCRIPT} runs")
            return 2

        if not OVERRIDE:
            same = REPO_SCRIPT.exists() and REPO_SCRIPT.read_bytes() == LIVE_SCRIPT.read_bytes()
            check("V-SL-LIVE-MATCHES-REPO", same,
                  f"live={LIVE_SCRIPT} repo={REPO_SCRIPT} identical={same}")

        for remaining, want in ((60, 40), (17.4, 83), (100, 0), (0, 100)):
            shown, rc = render(remaining, session)
            check(f"V-SL-RAW-PCT remaining={remaining}", shown == want and rc == 0,
                  f"want={want}% shown={shown} rc={rc}")

        # The monitor's bridge file and the bar must carry the same number.
        shown, _ = render(17.4, session)
        try:
            used = json.loads(bridge.read_text(encoding="utf-8")).get("used_pct")
        except (OSError, ValueError) as exc:
            used = f"unreadable: {exc}"
        check("V-SL-BRIDGE-MATCHES-BAR", used == shown == 83, f"bar={shown} bridge={used}")

        shown, rc = render(None, session)
        check("V-SL-NO-DATA-NO-METER", shown is None and rc == 0, f"shown={shown} rc={rc}")

        gate_standalone(session)
        gate_orca_forward(session)
    finally:
        try:
            bridge.unlink()
        except OSError:
            pass  # never written, or already gone
    print(f"SL_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
