#!/usr/bin/env python3
"""Compact Hang Detector -- PP BL-COMPACT-001.

Alert-only watchdog. Detects heuristically stuck /compact sessions
and NOTIFIES the Owner. NEVER kills anything. The Owner decides
whether to run /compact-rescue.

Heuristic (documented false positives):
    RSS > 200MB AND CPU < 2.0% AND .jsonl idle > 5 min
    => probably a stuck compact at 95%.

False positives:
- A long-thinking Owner with a large transcript that has paused
  generation while reading a sub-agent dispatch.
- A session that just finished a heavy turn and is idle by intent.

That is why this script ONLY alerts -- the Owner makes the kill
decision via /compact-rescue.

Install (opt-in, Owner runs once):
    python tools/compact_hang_detector.py --install
Uninstall:
    python tools/compact_hang_detector.py --uninstall
Manual single check:
    python tools/compact_hang_detector.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PP_PATH = Path(__file__).resolve().parent.parent
LOG = Path(os.environ.get("TEMP", "/tmp")) / "pp-compact-detector.log"
TASK_NAME = "PP-Compact-Hang-Detector"
RSS_THRESHOLD_MB = 200
CPU_THRESHOLD_PCT = 2.0
IDLE_THRESHOLD_MIN = 5


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


def get_claude_processes() -> list[dict]:
    """Return list of {Id, WorkingSet64, CPU} for live claude.exe procs.

    PowerShell ConvertTo-Json returns a single dict when N=1, an array
    otherwise. Normalise to list.
    """
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             "Get-Process claude -ErrorAction SilentlyContinue | "
             "Select-Object Id,WorkingSet64,CPU | "
             "ConvertTo-Json -Compress"],
            capture_output=True, text=True, timeout=10,
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
    """Return minutes since the newest .jsonl was modified in ~/.claude.

    Returns 999 on error or if no .jsonl found in the last 24h.
    """
    state = Path.home() / ".claude"
    if not state.is_dir():
        return 999.0
    try:
        cutoff = time.time() - 86400  # 24h
        candidates = []
        for f in state.rglob("*.jsonl"):
            try:
                mt = f.stat().st_mtime
                if mt >= cutoff:
                    candidates.append(mt)
            except OSError:
                continue
        if not candidates:
            return 999.0
        return (time.time() - max(candidates)) / 60.0
    except OSError:
        return 999.0


def check_once() -> dict | None:
    """One detection pass. Returns suspect dict or None if all clear."""
    procs = get_claude_processes()
    if not procs:
        return None
    idle_min = get_jsonl_idle_minutes()
    if idle_min < IDLE_THRESHOLD_MIN:
        return None
    for p in procs:
        rss = p.get("WorkingSet64") or 0
        rss_mb = rss / (1024 * 1024)
        cpu = p.get("CPU")
        if cpu is None:
            cpu = 999.0
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


def notify(suspect: dict) -> None:
    """Emit alert (log + best-effort Windows toast). NEVER kills."""
    msg = (
        f"[ALERT] PP Compact Hang Detector\n"
        f"   PID={suspect['pid']} RSS={suspect['rss_mb']}MB "
        f"CPU={suspect['cpu']}% .jsonl idle {suspect['idle_min']}min\n"
        f"   Possible /compact 95% hang.\n"
        f"   If stuck >2 min: run /compact-rescue"
    )
    log(f"ALERT: PID={suspect['pid']} rss={suspect['rss_mb']}MB "
        f"cpu={suspect['cpu']}% idle={suspect['idle_min']}min")
    # Windows toast via MessageBox -- best-effort, fail-open.
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


def run_check() -> int:
    suspect = check_once()
    if suspect:
        notify(suspect)
        return 1  # signal "alert raised" for callers that care
    log("OK: no compact hang detected")
    return 0


def install() -> int:
    script = str(PP_PATH / "tools" / "compact_hang_detector.py")
    py = sys.executable
    ps_cmd = (
        f"$a = New-ScheduledTaskAction -Execute '{py}' "
        f"-Argument '\"{script}\" --run'; "
        "$t = New-ScheduledTaskTrigger -RepetitionInterval "
        "(New-TimeSpan -Seconds 60) -Once -At (Get-Date); "
        "$s = New-ScheduledTaskSettingsSet -ExecutionTimeLimit "
        "(New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew "
        "-AllowStartIfOnBatteries -DontStopIfGoingOnBatteries; "
        f"Register-ScheduledTask -TaskName '{TASK_NAME}' -Action $a "
        "-Trigger $t -Settings $s -RunLevel Limited -Force | Out-Null"
    )
    r = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
        capture_output=True, text=True,
    )
    if r.returncode == 0:
        print(f"[OK] Detector installed as scheduled task: {TASK_NAME}")
        print("     Checks every 60s. Alerts if hang detected. Never kills.")
        return 0
    print(f"[FAIL] Install failed (rc={r.returncode}):")
    if r.stderr:
        print(r.stderr[:500])
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
    return 0


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "--check"
    if cmd in ("--install", "install"):
        return install()
    if cmd in ("--uninstall", "uninstall"):
        return uninstall()
    if cmd in ("--status", "status"):
        return status()
    # --run, --check, or default
    return run_check()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
