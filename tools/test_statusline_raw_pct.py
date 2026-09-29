"""V-SL-* gates: the statusline context meter shows the RAW used percentage.

Owner 2026-09-29: the GSD statusline (~/.claude/hooks/gsd-statusline.js, gsd-hook-version
1.14.0) subtracted a 16.5% autocompact buffer from remaining_percentage and rescaled the
rest, so the bar read 48% at a real 40% and 99% at a real 83% -- ~20 points above the
context watchdog and the rollover wall, which both judge 100 - remaining. The file is
GSD-owned and lives outside every git repo, so a `/gsd-update` can silently put the
buffer back. This drives the LIVE script with real stdin payloads and fails if it does.

SL_TEST_SCRIPT points it at another copy (mutation drill). A copy must sit next to the
live one: the script requires ./lib/hook-exit.js relative to itself.
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

SCRIPT = Path(os.environ.get("SL_TEST_SCRIPT")
              or Path.home() / ".claude" / "hooks" / "gsd-statusline.js")
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


def render(remaining, session):
    """Run the statusline once; return (percent shown or None, return code)."""
    ctx = {} if remaining is None else {"remaining_percentage": remaining,
                                        "total_tokens": 1_000_000}
    payload = {"model": {"display_name": "Opus"},
               "workspace": {"current_dir": tempfile.gettempdir()},
               "session_id": session, "context_window": ctx}
    # Bytes, not text: no BOM, no newline translation -- the script JSON.parses stdin.
    r = subprocess.run([NODE, str(SCRIPT)], input=json.dumps(payload).encode("utf-8"),
                       capture_output=True, timeout=30)
    out = ANSI.sub("", r.stdout.decode("utf-8", "replace"))
    m = METER.search(out)
    return (int(m.group(1)) if m else None), r.returncode


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
            print(f"HARNESS-FAILED: no meter rendered (rc={rc}); check {SCRIPT} runs in place")
            return 2

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
    finally:
        try:
            bridge.unlink()
        except OSError:
            pass  # never written, or already gone
    print(f"SL_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
