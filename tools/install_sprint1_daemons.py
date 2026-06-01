#!/usr/bin/env python3
"""install_sprint1_daemons.py -- register PP Mechanism-F maintenance daemons.

Sealed BL-TOOL-AUTO-001 (2026-06-01). The manual-tools audit + PASO 0 timing
reclassified the slow (>1 s), genuinely-periodic maintenance tools to Windows
Task Scheduler. This installer registers them as nightly tasks.

Scope is deliberately conservative -- ONLY tools whose semantics are periodic
maintenance. Event-scoped tools (jit_ref_correlate, session-snapshot) are NOT
here; they are Stop hooks. Live-target probes (oracle_heartbeat) and
session-scoped consumers (cache_hint_apply) are excluded too.

Idempotent: Register-ScheduledTask -Force overwrites an existing task of the
same name. Use --dry-run to preview without touching the scheduler.

Usage:
    python tools/install_sprint1_daemons.py --dry-run
    python tools/install_sprint1_daemons.py
    python tools/install_sprint1_daemons.py --uninstall
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional

PP_PATH = Path(__file__).resolve().parent.parent
PYTHON_EXE = sys.executable

# name, tool (relative to PP), args, daily time HH:MM, description
DAEMONS: list[dict[str, str]] = [
    {
        "name": "PP-Vault-Summarize",
        "tool": "tools/vault_summarize.py",
        "args": "--check",
        "time": "02:00",
        "desc": "PP Knowledge Vault self-optimization health check",
    },
    {
        "name": "PP-Sovereign-Miner",
        "tool": "tools/sovereign_miner.py",
        "args": "",
        "time": "03:00",
        "desc": "PP 4-pillar repo/transcript distillation",
    },
    {
        "name": "PP-Miner-V2",
        "tool": "tools/miner_v2.py",
        "args": "",
        "time": "03:30",
        "desc": "PP Total Recall: jsonl + Cursor SQLite mining",
    },
    {
        "name": "PP-Normalize-Paths",
        "tool": "tools/normalize_paths.py",
        "args": "--check",
        "time": "04:00",
        "desc": "PP path + secret-scan hygiene audit",
    },
]


def _run_ps(script: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive",
         "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True, text=True, timeout=timeout,
    )


def _register_script(daemon: dict[str, str]) -> str:
    tool_abs = str(PP_PATH / daemon["tool"])
    args = daemon.get("args", "")
    argument = tool_abs + (f" {args}" if args else "")
    # single-quoted PS literals -- none of our paths contain a single quote
    return (
        "$ErrorActionPreference='Stop'; "
        f"$a=New-ScheduledTaskAction -Execute '{PYTHON_EXE}' "
        f"-Argument '{argument}' -WorkingDirectory '{PP_PATH}'; "
        f"$t=New-ScheduledTaskTrigger -Daily -At '{daemon['time']}'; "
        "$s=New-ScheduledTaskSettingsSet "
        "-ExecutionTimeLimit (New-TimeSpan -Minutes 30) "
        "-MultipleInstances IgnoreNew -StartWhenAvailable; "
        f"Register-ScheduledTask -TaskName '{daemon['name']}' "
        f"-Description '{daemon['desc']}' -Action $a -Trigger $t "
        "-Settings $s -Force | Out-Null; Write-Output 'OK'"
    )


def install(daemon: dict[str, str], dry_run: bool) -> bool:
    arg = daemon.get("args", "")
    preview = f'python "{PP_PATH / daemon["tool"]}" {arg}'.strip()
    if dry_run:
        print(f"[DRYRUN] {daemon['name']}  (daily {daemon['time']})")
        print(f"         {preview}")
        return True
    try:
        r = _run_ps(_register_script(daemon))
    except subprocess.TimeoutExpired:
        print(f"[FAIL]   {daemon['name']}: powershell timeout")
        return False
    if r.returncode == 0 and "OK" in (r.stdout or ""):
        print(f"[OK]     {daemon['name']}  (daily {daemon['time']})")
        return True
    print(f"[FAIL]   {daemon['name']}: {(r.stderr or r.stdout or '').strip()[:160]}")
    return False


def uninstall(daemon: dict[str, str]) -> bool:
    script = (
        f"Unregister-ScheduledTask -TaskName '{daemon['name']}' "
        "-Confirm:$false -ErrorAction SilentlyContinue; Write-Output 'OK'"
    )
    try:
        r = _run_ps(script)
    except subprocess.TimeoutExpired:
        return False
    ok = r.returncode == 0
    print(f"[{'OK' if ok else 'FAIL'}]   removed {daemon['name']}")
    return ok


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Install PP Sprint 1 F-daemons")
    ap.add_argument("--dry-run", action="store_true",
                    help="preview without touching Task Scheduler")
    ap.add_argument("--uninstall", action="store_true",
                    help="remove the PP-* scheduled tasks")
    ns = ap.parse_args(argv)

    if ns.uninstall:
        print("=== Uninstalling PP Sprint 1 daemons ===")
        results = [uninstall(d) for d in DAEMONS]
    else:
        mode = "DRY RUN -- no changes" if ns.dry_run else "Installing"
        print(f"=== {mode}: PP Sprint 1 F-daemons ===")
        results = [install(d, ns.dry_run) for d in DAEMONS]

    passed = sum(1 for ok in results if ok)
    verb = "would be set" if ns.dry_run else "set"
    print(f"\n{passed}/{len(DAEMONS)} daemons {verb}")
    return 0 if passed == len(DAEMONS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
