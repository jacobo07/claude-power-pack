"""V-ACPS-* gates: per-session auto-compact flags + daemon window routing.

Spec: vault/specs/autocompact-per-session-flags.md

The daemon is driven in DRY-RUN (AC_DAEMON_DRYRUN=1): it logs WOULD-SEND and
never calls SendKeys, so this suite cannot press Enter into a live pane.
Foreground window and the list of open Cursor windows are injected through
AC_DAEMON_FAKE_FG / AC_DAEMON_FAKE_WINDOWS; flags live in a temp dir.

AC_TEST_DAEMON overrides the daemon path (used by mutation drills).
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

HOME = Path.home()
DAEMON = Path(os.environ.get("AC_TEST_DAEMON")
              or HOME / ".claude" / "hooks" / "auto-compact-sendkeys-daemon.ps1")
WATCHDOG = Path(__file__).resolve().parents[1] / "modules" / "zero-crash" / "hooks" / "context-watchdog.py"

passes = fails = 0


def _ok(gate, ev):
    global passes
    passes += 1
    print(f"PASS {gate}: {ev}")


def _fail(gate, ev):
    global fails
    fails += 1
    print(f"FAIL {gate}: {ev}")


def check(gate, cond, ev):
    (_ok if cond else _fail)(gate, ev)


def write_flag(d: Path, name: str, cwd: str, age_s: float = 0.0):
    p = d / name
    p.write_text(json.dumps({"ts": "x", "session_id": name, "used_pct": 71, "cwd": cwd}) + "\n",
                 encoding="utf-8")
    if age_s:
        t = time.time() - age_s
        os.utime(p, (t, t))
    return p


def fg(name="Cursor", title="", hwnd="1"):
    return json.dumps({"name": name, "title": title, "hwnd": hwnd})


def run_daemon(d: Path, fg_src: str, windows: list, ttl: int = 3, script=None):
    """Run the daemon to TTL; fg_src is JSON or a path re-read every tick.
    `script` is an optional callable run in a thread while the daemon lives."""
    env = dict(os.environ)
    env.update({
        "AC_DAEMON_DIR": str(d),
        "AC_DAEMON_DRYRUN": "1",
        "AC_DAEMON_FAKE_FG": fg_src,
        "AC_DAEMON_FAKE_WINDOWS": json.dumps(windows),
        "AC_DAEMON_TTL": str(ttl),
    })
    th = threading.Thread(target=script) if script else None
    if th:
        th.start()
    r = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(DAEMON)],
        env=env, capture_output=True, text=True, timeout=ttl + 60)
    if th:
        th.join()
    log = (d / "auto-compact-daemon.log")
    text = log.read_text(encoding="utf-8-sig") if log.exists() else ""
    sent = re.findall(r"WOULD-SEND flag=(\S+)", text)
    start = "daemon start" in text
    return sent, text, start, r.returncode


def remaining(d: Path):
    return sorted(p.name for p in d.glob("auto-compact-*.flag"))


def fresh():
    return Path(tempfile.mkdtemp(prefix="acps_"))


def main() -> int:
    # --- watchdog: one flag per session ------------------------------------
    spec = importlib.util.spec_from_file_location("_acps_wd", WATCHDOG)
    wd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wd)
    home = fresh()

    class AW:
        @staticmethod
        def atomic_write_bytes(path, data):
            Path(path).write_bytes(data)

    old_home = Path.home
    Path.home = staticmethod(lambda: home)
    try:
        a = wd._write_trigger_flag(AW, "aaaa-1111", 71, r"C:\p\ProjA")
        b = wd._write_trigger_flag(AW, "bbbb-2222", 72, r"C:\p\ProjB")
        evil = wd._write_trigger_flag(AW, "..\\..\\x", 73, r"C:\p\ProjC")
    finally:
        Path.home = old_home
    names = sorted(p.name for p in (home / ".claude" / "hooks").glob("*.flag"))
    check("V-ACPS-WD-PER-SESSION",
          "auto-compact-trigger-aaaa-1111.flag" in names and "auto-compact-trigger-bbbb-2222.flag" in names,
          f"files={names}")
    check("V-ACPS-WD-NO-SINGLE-NAME", "auto-compact-trigger.flag" not in names, f"files={names}")
    check("V-ACPS-WD-SID-SANITISED", evil and Path(evil).parent == home / ".claude" / "hooks"
          and Path(evil).name == "auto-compact-trigger-x.flag", f"evil={evil}")

    # --- preflight: the daemon runs at all ----------------------------------
    d = fresh()
    write_flag(d, "auto-compact-trigger-s1.flag", r"C:\p\ProjA")
    sent, log, started, rc = run_daemon(d, fg(title="ProjA - Cursor"), ["ProjA - Cursor"])
    if not started:
        print(f"HARNESS-FAILED: daemon did not start (rc={rc}) log={log!r}")
        return 2
    check("V-ACPS-D-TITLE-MATCH", sent == ["auto-compact-trigger-s1.flag"], f"sent={sent}")

    # --- two runs, two windows: only the focused one is sent ----------------
    d = fresh()
    write_flag(d, "auto-compact-trigger-A.flag", r"C:\p\ProjA", age_s=5)
    write_flag(d, "auto-compact-trigger-B.flag", r"C:\p\ProjB")
    sent, log, _, _ = run_daemon(d, fg(title="ProjA - Cursor"), ["ProjA - Cursor", "ProjB - Cursor"])
    check("V-ACPS-D-ROUTE-FOCUSED", sent == ["auto-compact-trigger-A.flag"], f"sent={sent}")
    check("V-ACPS-D-OTHER-WAITS", remaining(d) == ["auto-compact-trigger-B.flag"],
          f"left={remaining(d)}")
    # ...and B is delivered when its own window comes forward.
    (d / "auto-compact-daemon.log").unlink()
    sent2, _, _, _ = run_daemon(d, fg(title="ProjB - Cursor", hwnd="2"), ["ProjA - Cursor", "ProjB - Cursor"])
    check("V-ACPS-D-OTHER-DELIVERED", sent2 == ["auto-compact-trigger-B.flag"], f"sent={sent2}")

    # --- a lone flag whose project has its own window is NOT sent elsewhere --
    d = fresh()
    write_flag(d, "auto-compact-trigger-B.flag", r"C:\p\ProjB")
    sent, _, _, _ = run_daemon(d, fg(title="ProjA - Cursor"), ["ProjA - Cursor", "ProjB - Cursor"])
    check("V-ACPS-D-NO-STEAL", sent == [] and remaining(d) == ["auto-compact-trigger-B.flag"],
          f"sent={sent} left={remaining(d)}")

    # --- newest-first focus: the non-focused OLDER flag is not stolen --------
    d = fresh()
    write_flag(d, "auto-compact-trigger-B.flag", r"C:\p\ProjB", age_s=9)
    write_flag(d, "auto-compact-trigger-A.flag", r"C:\p\ProjA")
    sent, _, _, _ = run_daemon(d, fg(title="notes.md - ProjA - Cursor"), ["notes.md - ProjA - Cursor", "ProjB - Cursor"])
    check("V-ACPS-D-EDITOR-TITLE", sent == ["auto-compact-trigger-A.flag"], f"sent={sent}")

    # --- legacy: one flag, project has no window -> sent as before -----------
    d = fresh()
    write_flag(d, "auto-compact-trigger-C.flag", r"C:\p\ProjC")
    sent, _, _, _ = run_daemon(d, fg(title="ProjA - Cursor"), ["ProjA - Cursor"])
    check("V-ACPS-D-NO-OWN-WINDOW-SENDS", sent == ["auto-compact-trigger-C.flag"], f"sent={sent}")

    # --- legacy single name still consumed ----------------------------------
    d = fresh()
    write_flag(d, "auto-compact-trigger.flag", r"C:\p\ProjA")
    sent, _, _, _ = run_daemon(d, fg(title="ProjA - Cursor"), ["ProjA - Cursor"])
    check("V-ACPS-D-LEGACY-NAME", sent == ["auto-compact-trigger.flag"], f"sent={sent}")

    # --- not Cursor: every trigger demoted, none discarded, none sent -------
    d = fresh()
    write_flag(d, "auto-compact-trigger-A.flag", r"C:\p\ProjA")
    write_flag(d, "auto-compact-trigger-B.flag", r"C:\p\ProjB")
    write_flag(d, "auto-compact-pending-Z.flag", r"C:\p\ProjZ")
    sent, _, _, _ = run_daemon(d, fg(name="chrome", title="x"), ["ProjA - Cursor"])
    check("V-ACPS-D-NOT-CURSOR-NOSEND", sent == [], f"sent={sent}")
    check("V-ACPS-D-DEMOTE-ALL-KEPT",
          remaining(d) == ["auto-compact-pending-A.flag", "auto-compact-pending-B.flag", "auto-compact-pending-Z.flag"],
          f"left={remaining(d)}")

    # --- same window: one Enter per focus episode ----------------------------
    d = fresh()
    write_flag(d, "auto-compact-trigger-A1.flag", r"C:\p\ProjA", age_s=5)
    write_flag(d, "auto-compact-trigger-A2.flag", r"C:\p\ProjA")
    sent, _, _, _ = run_daemon(d, fg(title="ProjA - Cursor"), ["ProjA - Cursor"])
    check("V-ACPS-D-ONE-PER-EPISODE", sent == ["auto-compact-trigger-A1.flag"], f"sent={sent}")
    # focus leaves and returns -> the second one is delivered
    fgfile = d / "fg.json"
    fgfile.write_text(fg(title="ProjA - Cursor", hwnd="1"), encoding="utf-8")
    (d / "auto-compact-daemon.log").unlink()

    def flip():
        time.sleep(2.0)
        fgfile.write_text(fg(name="explorer", title="x", hwnd="9"), encoding="utf-8")
        time.sleep(1.5)
        fgfile.write_text(fg(title="ProjA - Cursor", hwnd="1"), encoding="utf-8")

    write_flag(d, "auto-compact-trigger-A3.flag", r"C:\p\ProjA")  # A2 still pending + A3 = 2 to deliver
    sent, _, _, _ = run_daemon(d, str(fgfile), ["ProjA - Cursor"], ttl=7, script=flip)
    check("V-ACPS-D-REFOCUS-DELIVERS", len(sent) == 2 and remaining(d) == [], f"sent={sent} left={remaining(d)}")

    total = passes + fails
    print(f"ACPS_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
