#!/usr/bin/env python3
"""Compact Hang Detector -- PP BL-COMPACT-001.

Alert-only watchdog. Detects heuristically stuck /compact sessions
and notifies the Owner. NEVER kills on its own. The Owner makes the
kill decision -- either by running /compact-rescue manually, or by
clicking Yes on the interactive prompt (--interactive opt-in).

Heuristic (documented false positives):
    RSS > 200MB AND CPU < 2.0% AND .jsonl idle > 5 min
    => probably a stuck compact at 95%.

False positives:
- A long-thinking Owner with a large transcript that has paused
  generation while reading a sub-agent dispatch.
- A session that just finished a heavy turn and is idle by intent.

Doctrine: per apex v13 (Slash-Recovery axis), the kill decision is
ALWAYS Owner-driven. The interactive mode just lowers the friction
of that decision from "go to a terminal and type a command" to
"click Yes" -- but the click is still required. No auto-kill.

Install (opt-in, Owner runs once):
    python tools/compact_hang_detector.py --install
    python tools/compact_hang_detector.py --install --interactive
Uninstall:
    python tools/compact_hang_detector.py --uninstall
Manual single check:
    python tools/compact_hang_detector.py
    python tools/compact_hang_detector.py --interactive
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PP_PATH = Path(__file__).resolve().parent.parent
LOG = Path(os.environ.get("TEMP", "/tmp")) / "pp-compact-detector.log"
SNOOZE_FILE = Path.home() / ".claude" / "state" / "compact_snooze_until.txt"
TASK_NAME = "PP-Compact-Hang-Detector"

# Detection heuristic thresholds
RSS_THRESHOLD_MB = 200
CPU_THRESHOLD_PCT = 2.0
IDLE_THRESHOLD_MIN = 5

# Unit conversions and sentinels
BYTES_PER_MB = 1024 * 1024
IDLE_MISS_SENTINEL_MIN = 999.0
SECONDS_PER_DAY = 86400

# Subprocess and popup timeouts
PROC_QUERY_TIMEOUT_S = 10
INTERACTIVE_POPUP_TIMEOUT_S = 300  # 5min Owner-click window
STDERR_TRUNC_CHARS = 500

# Scheduled-task wiring
TASK_POLL_INTERVAL_S = 60
TASK_EXEC_LIMIT_MIN = 6  # > popup timeout so interactive prompt fits

# Defaults
DEFAULT_SNOOZE_SECONDS = 60

# CLI flags set in main() -- consumed by check_once() + notify()
INTERACTIVE = False
SNOOZE_SECONDS = DEFAULT_SNOOZE_SECONDS
DRY_NOTIFY = False  # testing-only: log the action instead of popping


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{ts} {msg}"
    print(line)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def snoozed() -> bool:
    """True if the snooze file points to a future epoch timestamp."""
    if not SNOOZE_FILE.is_file():
        return False
    try:
        until = float(SNOOZE_FILE.read_text(encoding="utf-8").strip())
        return time.time() < until
    except (ValueError, OSError):
        return False


def write_snooze(seconds: int) -> None:
    try:
        SNOOZE_FILE.parent.mkdir(parents=True, exist_ok=True)
        SNOOZE_FILE.write_text(str(time.time() + seconds), encoding="utf-8")
    except OSError as exc:
        log(f"snooze write failed: {exc}", )


def clear_snooze() -> None:
    try:
        if SNOOZE_FILE.is_file():
            SNOOZE_FILE.unlink()
    except OSError:
        pass


def get_claude_processes() -> list[dict]:
    """Return list of {Id, WorkingSet64, CPU} for live claude.exe procs."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             "Get-Process claude -ErrorAction SilentlyContinue | "
             "Select-Object Id,WorkingSet64,CPU | "
             "ConvertTo-Json -Compress"],
            capture_output=True, text=True, timeout=PROC_QUERY_TIMEOUT_S,
        )
        if not r.stdout.strip():
            return []
        data = json.loads(r.stdout)
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            return data
        return []
    except (subprocess.TimeoutExpired, subprocess.SubprocessError,
            json.JSONDecodeError, OSError):
        return []


def get_jsonl_idle_minutes() -> float:
    """Minutes since newest .jsonl in ~/.claude was written; 999 on miss."""
    state = Path.home() / ".claude"
    if not state.is_dir():
        return IDLE_MISS_SENTINEL_MIN
    try:
        cutoff = time.time() - SECONDS_PER_DAY
        candidates = []
        for f in state.rglob("*.jsonl"):
            try:
                mt = f.stat().st_mtime
                if mt >= cutoff:
                    candidates.append(mt)
            except OSError:
                continue
        if not candidates:
            return IDLE_MISS_SENTINEL_MIN
        return (time.time() - max(candidates)) / 60.0
    except OSError:
        return IDLE_MISS_SENTINEL_MIN


def check_once() -> dict | None:
    """One detection pass. Returns suspect dict or None if all clear."""
    if snoozed():
        return None
    procs = get_claude_processes()
    if not procs:
        return None
    idle_min = get_jsonl_idle_minutes()
    if idle_min < IDLE_THRESHOLD_MIN:
        return None
    for p in procs:
        rss = p.get("WorkingSet64") or 0
        rss_mb = rss / BYTES_PER_MB
        cpu = p.get("CPU")
        if cpu is None:
            cpu = IDLE_MISS_SENTINEL_MIN
        if rss_mb < RSS_THRESHOLD_MB:
            continue
        if cpu > CPU_THRESHOLD_PCT:
            continue
        return {
            "pid": p.get("Id"),
            "rss_mb": round(rss_mb, 1),
            "cpu": round(float(cpu), 2),
            "idle_min": round(idle_min, 1),
        }
    return None


def notify_passive(suspect: dict) -> None:
    """Old behaviour: fire-and-forget OK-only MessageBox toast."""
    msg = (
        f"[ALERT] PP Compact Hang Detector\n"
        f"   PID={suspect['pid']} RSS={suspect['rss_mb']}MB "
        f"CPU={suspect['cpu']}% .jsonl idle {suspect['idle_min']}min\n"
        f"   Possible /compact 95% hang.\n"
        f"   If stuck >2 min: run /compact-rescue"
    )
    try:
        flat = msg.replace("\n", " ").replace('"', "'")
        ps_cmd = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "[System.Windows.Forms.MessageBox]::Show("
            f"\"{flat}\",\"PP Compact Alert\","
            "[System.Windows.Forms.MessageBoxButtons]::OK,"
            "[System.Windows.Forms.MessageBoxIcon]::Warning) | Out-Null"
        )
        subprocess.Popen(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except OSError:
        pass


def notify_interactive(suspect: dict) -> str:
    """Blocking 5-min Yes/No/Cancel dialog. Returns one of:
        'rescue'  -- Owner clicked Yes -> caller should spawn rescue
        'snooze'  -- Owner clicked No  -> caller should write snooze
        'dismiss' -- Owner clicked Cancel or closed dialog
        'timeout' -- 5 min elapsed without click
        'error'   -- popup spawn failed (degrade to passive)
    """
    flat = (
        f"claude.exe PID={suspect['pid']} appears stuck. "
        f"RSS={suspect['rss_mb']}MB, CPU={suspect['cpu']}%, "
        f".jsonl idle {suspect['idle_min']} min. "
        f"This matches the /compact 95% hang signature. "
        f"\\n\\nYES = run /compact-rescue now (kills the stuck "
        f"claude.exe; kclaude.bat resumes from pre-compact state). "
        f"\\nNO = snooze alerts for {SNOOZE_SECONDS}s. "
        f"\\nCANCEL = dismiss this alert only."
    )
    title = "PP Compact Hang Detected"
    ps_cmd = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$r = [System.Windows.Forms.MessageBox]::Show("
        f"\"{flat}\",\"{title}\","
        "[System.Windows.Forms.MessageBoxButtons]::YesNoCancel,"
        "[System.Windows.Forms.MessageBoxIcon]::Warning); "
        "Write-Output $r"
    )
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            capture_output=True, text=True,
            timeout=INTERACTIVE_POPUP_TIMEOUT_S,
        )
        out = (r.stdout or "").strip()
        if out == "Yes":
            return "rescue"
        if out == "No":
            return "snooze"
        return "dismiss"
    except subprocess.TimeoutExpired:
        return "timeout"
    except (OSError, subprocess.SubprocessError):
        return "error"


def spawn_rescue() -> None:
    """Fire-and-forget: spawn compact_rescue.ps1 with guard bypass.

    The detector already confirmed .jsonl idle >= 5min AND the Owner
    explicitly clicked Yes -- the rescue's recency guard would be
    redundant and could spuriously block this Owner-authorised kill.
    """
    rescue = PP_PATH / "tools" / "compact_rescue.ps1"
    if not rescue.is_file():
        log(f"rescue script missing: {rescue}")
        return
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-ExecutionPolicy", "Bypass", "-File", str(rescue),
             "-IdleThresholdSeconds", "0"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        log("Owner clicked Yes -- rescue spawned")
    except OSError as exc:
        log(f"rescue spawn failed: {exc}")


def notify(suspect: dict) -> None:
    """Top-level notification dispatcher.

    INTERACTIVE off (default): fire-and-forget OK-only popup. Owner
    must still run /compact-rescue manually -- this is the legacy
    behaviour preserved for users who do not want clickable kills.

    INTERACTIVE on (opt-in): blocking Yes/No/Cancel popup. Yes runs
    the rescue inline; No snoozes; Cancel/timeout no-ops. Owner
    decision required for every kill -- no auto-kill.
    """
    log(f"ALERT: PID={suspect['pid']} rss={suspect['rss_mb']}MB "
        f"cpu={suspect['cpu']}% idle={suspect['idle_min']}min "
        f"interactive={INTERACTIVE} dry_notify={DRY_NOTIFY}")
    if DRY_NOTIFY:
        log("dry_notify ON -- would prompt but not spawning popup")
        return
    if not INTERACTIVE:
        notify_passive(suspect)
        return
    action = notify_interactive(suspect)
    log(f"interactive action: {action}")
    if action == "rescue":
        spawn_rescue()
    elif action == "snooze":
        write_snooze(SNOOZE_SECONDS)
        log(f"snoozed alerts for {SNOOZE_SECONDS}s")
    elif action == "error":
        # Degrade to passive popup so the Owner still gets a signal.
        notify_passive(suspect)


def run_check() -> int:
    suspect = check_once()
    if suspect:
        notify(suspect)
        return 1
    log("OK: no compact hang detected")
    return 0


def install(interactive: bool = False, snooze_seconds: int = 60) -> int:
    script = str(PP_PATH / "tools" / "compact_hang_detector.py")
    py = sys.executable
    args = f'"{script}" --run'
    if interactive:
        args += f' --interactive --snooze-seconds {snooze_seconds}'
    ps_cmd = (
        f"$a = New-ScheduledTaskAction -Execute '{py}' "
        f"-Argument '{args}'; "
        "$t = New-ScheduledTaskTrigger -RepetitionInterval "
        f"(New-TimeSpan -Seconds {TASK_POLL_INTERVAL_S}) "
        "-Once -At (Get-Date); "
        "$s = New-ScheduledTaskSettingsSet -ExecutionTimeLimit "
        f"(New-TimeSpan -Minutes {TASK_EXEC_LIMIT_MIN}) "
        "-MultipleInstances IgnoreNew "
        "-AllowStartIfOnBatteries -DontStopIfGoingOnBatteries; "
        f"Register-ScheduledTask -TaskName '{TASK_NAME}' -Action $a "
        "-Trigger $t -Settings $s -RunLevel Limited -Force | Out-Null"
    )
    r = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
        capture_output=True, text=True,
    )
    if r.returncode == 0:
        mode = "interactive (Yes/No/Cancel popup)" if interactive else "passive (OK-only popup)"
        print(f"[OK] Detector installed as scheduled task: {TASK_NAME}")
        print(f"     Mode: {mode}. Checks every 60s. NEVER auto-kills.")
        return 0
    print(f"[FAIL] Install failed (rc={r.returncode}):")
    if r.stderr:
        print(r.stderr[:STDERR_TRUNC_CHARS])
    return 1


def uninstall() -> int:
    r = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command",
         f"Unregister-ScheduledTask -TaskName '{TASK_NAME}' "
         "-Confirm:$false -ErrorAction SilentlyContinue"],
        capture_output=True, text=True,
    )
    print(f"[OK] Detector removed: {TASK_NAME} (rc={r.returncode})")
    return 0


def status() -> int:
    r = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command",
         f"$t = Get-ScheduledTask -TaskName '{TASK_NAME}' "
         "-ErrorAction SilentlyContinue; "
         "if ($t) { $t.State } else { 'NOT_INSTALLED' }"],
        capture_output=True, text=True,
    )
    out = (r.stdout or "").strip()
    print(f"Detector task: {out or 'NOT_INSTALLED'}")
    snooze_str = "no" if not snoozed() else "yes (active)"
    print(f"Snooze active: {snooze_str}")
    return 0


def main(argv: list[str]) -> int:
    global INTERACTIVE, SNOOZE_SECONDS, DRY_NOTIFY
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("action", nargs="?", default="check",
                        choices=["check", "run", "install", "uninstall",
                                 "status", "clear-snooze"],
                        help="default: check")
    parser.add_argument("--interactive", action="store_true",
                        help="opt-in: blocking Yes/No/Cancel popup")
    parser.add_argument("--snooze-seconds", type=int,
                        default=DEFAULT_SNOOZE_SECONDS,
                        help="seconds to suppress alerts after Owner clicks No")
    parser.add_argument("--dry-notify", action="store_true",
                        help="testing: log the action; do NOT show popup")
    # Tolerate the old --run / --check / --install / etc. dash form.
    norm_argv = [a.lstrip("-") if a.startswith("--") and a[2:] in
                 {"check", "run", "install", "uninstall", "status",
                  "clear-snooze"} else a for a in argv]
    args = parser.parse_args(norm_argv)

    INTERACTIVE = bool(args.interactive)
    SNOOZE_SECONDS = max(0, int(args.snooze_seconds))
    DRY_NOTIFY = bool(args.dry_notify)

    if args.action == "install":
        return install(interactive=INTERACTIVE,
                       snooze_seconds=SNOOZE_SECONDS)
    if args.action == "uninstall":
        return uninstall()
    if args.action == "status":
        return status()
    if args.action == "clear-snooze":
        clear_snooze()
        print("[OK] Snooze cleared")
        return 0
    return run_check()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
