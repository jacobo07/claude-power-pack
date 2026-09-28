"""Night Research runner (T10 item 34) -- the Sovereign VPS only.

Owner decision (2026-09-28): night research runs on the VPS (204.168.166.63, user kobicraft),
never on the workstation. This runner REFUSES anywhere else, before touching state. On the VPS it
hands one gated pass to tools/night_research.cjs, whose vendored core enforces the night window,
pause flag, pass budget and single-flight lock and writes a bounded report with every source
marked unverified, reward 0, promotion none. Findings are CANDIDATES; nothing here promotes them.

    python tools/night_research_runner.py status   (no model call, no state written)
    python tools/night_research_runner.py run      (one gated pass; the systemd timer calls this)
exit: 0 ran or correctly idle · 2 could not run (node/bridge) · 3 refused (wrong host)

Budget: 2 passes per night (vendor default 6) and 180 s per pass -- a research candidate is not
worth an unattended night of quota. Pause: `touch <state>/paused.flag`.
"""
from __future__ import annotations

import getpass
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "tools" / "night_research.cjs"
QUESTIONS = ROOT / "vault" / "night_research" / "questions.json"
TIMEZONE = "Europe/Madrid"          # the Owner's night, not the server's (the VPS clock is UTC)
PASSES_PER_NIGHT = 2
PASS_TIMEOUT_MS = 180_000
ENGINE_MIN = (22, 23, 2)            # vendored genesis-suite engines range: ^22.23.2 || ^24.14


def state_dir() -> Path:
    return Path(os.environ.get("CPP_NIGHT_RESEARCH_DIR") or (Path.home() / ".claude" / "state" / "night-research"))


def host_ok() -> tuple[bool, str]:
    if os.environ.get("CPP_NIGHT_RESEARCH_FIXTURE") == "1":
        return True, "fixture"
    system, user = platform.system(), getpass.getuser()
    if system != "Linux" or user != "kobicraft":
        return False, f"night research runs only on the Sovereign VPS (Linux, user kobicraft); this is {system}/{user}"
    return True, "vps"


def _version(node: str) -> tuple[int, ...] | None:
    try:
        out = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=20).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return None
    m = re.match(r"^v(\d+)\.(\d+)\.(\d+)", out)
    return tuple(int(x) for x in m.groups()) if m else None


def engine_ok(v: tuple[int, ...]) -> bool:
    return (v[0] == 22 and v >= ENGINE_MIN) or (v[0] == 24 and v >= (24, 14, 0))


def find_node() -> tuple[str | None, str]:
    cands = [os.environ.get("CPP_NIGHT_NODE"), str(Path.home() / ".local" / "node24" / "bin" / "node"), shutil.which("node")]
    seen = []
    for c in cands:
        if not c or not Path(c).exists():
            continue
        v = _version(c)
        seen.append(f"{c}={'.'.join(map(str, v)) if v else '?'}")
        if v and engine_ok(v):
            return c, ""
    return None, f"no node inside the vendored engines range (^22.23.2 || ^24.14): {', '.join(seen) or 'none found'}"


def theme() -> dict:
    qs = json.loads(QUESTIONS.read_text(encoding="utf-8"))["questions"]
    done = 0
    try:
        st = json.loads((state_dir() / "state.json").read_text(encoding="utf-8"))
        done = sum(int(n.get("attempts") or 0) for n in (st.get("nights") or {}).values())
    except (OSError, ValueError):
        pass
    return qs[done % len(qs)]


def call(mode: str, fixture: bool = False, now: int | None = None) -> dict:
    node, why = find_node()
    if node is None:
        return {"outcome": "NO_ENGINE", "error": why}
    req = {"mode": mode, "stateDir": str(state_dir()), "timezone": TIMEZONE, "maxPassesPerNight": PASSES_PER_NIGHT,
           "timeoutMs": PASS_TIMEOUT_MS, "theme": theme(), "claude": os.environ.get("CPP_CLAUDE_EXE") or "claude",
           "fixture": fixture}
    if now is not None:
        req["now"] = now
    try:
        p = subprocess.run([node, str(CORE)], input=json.dumps(req), capture_output=True, text=True,
                           encoding="utf-8", timeout=PASS_TIMEOUT_MS / 1000 + 60)
    except subprocess.TimeoutExpired:
        return {"outcome": "TIMEOUT", "error": "the core did not return"}
    try:
        return json.loads(p.stdout)
    except ValueError:
        return {"outcome": "UNREADABLE", "error": f"rc={p.returncode} {(p.stdout or p.stderr)[:300]}"}


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    mode = argv[0] if argv else ""
    if mode not in ("status", "run"):
        print(__doc__)
        return 2
    ok, why = host_ok()
    if not ok:
        print(f"REFUSED: {why}")
        return 3
    r = call(mode, fixture=os.environ.get("CPP_NIGHT_RESEARCH_FIXTURE") == "1")
    print(json.dumps(r, indent=1))
    return 0 if r.get("outcome") == "OK" else 2


if __name__ == "__main__":
    sys.exit(main())
