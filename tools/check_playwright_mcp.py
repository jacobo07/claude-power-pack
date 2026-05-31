#!/usr/bin/env python3
"""
Playwright MCP Plugin Health Check -- PP BL-PLAYWRIGHT-001 (Option A).

Verifies the state of the Playwright MCP plugin in Claude Code.
Adapted for `enabledPlugins` (NOT `mcpServers`).

ASCII-only output to survive Windows cp1252 console encoding.
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path

PP_PATH = Path(__file__).resolve().parent.parent
SETTINGS = Path.home() / ".claude" / "settings.json"
KILLER = PP_PATH / "tools" / "playwright_stale_killer.ps1"
WATCHDOG = PP_PATH / "tools" / "playwright_watchdog.ps1"
WATCHDOG_TASK = "PP-Playwright-MCP-Watchdog"


def find_plugin_config() -> tuple[Path | None, bool]:
    """Return (settings_path, playwright_enabled)."""
    if not SETTINGS.exists():
        return None, False
    try:
        # utf-8-sig handles BOM if any tooling wrote one
        d = json.loads(SETTINGS.read_text(encoding="utf-8-sig"))
    except Exception:
        return SETTINGS, False
    plugins = d.get("enabledPlugins", {}) or {}
    pw_enabled = any(
        "playwright" in k.lower() and bool(v)
        for k, v in plugins.items()
    )
    return SETTINGS, pw_enabled


def get_playwright_processes() -> list[dict]:
    """Return [{pid, age_minutes}] for every node.exe @playwright/mcp proc."""
    if platform.system() != "Windows":
        return []
    ps_cmd = (
        "Get-CimInstance Win32_Process -Filter \"Name='node.exe'\" "
        "-ErrorAction SilentlyContinue | "
        "Where-Object { $_.CommandLine -and ("
        "$_.CommandLine -like '*@playwright/mcp*' -or "
        "$_.CommandLine -like '*playwright*cli.js*') } | "
        "ForEach-Object { "
        "$age = if ($_.CreationDate) { "
        "[int][Math]::Round((New-TimeSpan -Start $_.CreationDate -End (Get-Date)).TotalMinutes) "
        "} else { 0 }; "
        "Write-Output ('PID=' + $_.ProcessId + ' AGE=' + $age) }"
    )
    try:
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive",
             "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=15,
        )
    except Exception:
        return []
    procs: list[dict] = []
    for line in (r.stdout or "").splitlines():
        line = line.strip()
        if not line.startswith("PID="):
            continue
        try:
            parts = dict(p.split("=", 1) for p in line.split() if "=" in p)
            procs.append({
                "pid": int(parts["PID"]),
                "age_minutes": int(parts.get("AGE", 0)),
            })
        except Exception:
            continue
    return procs


def check_watchdog() -> tuple[bool, str]:
    """Return (installed, state_string)."""
    if platform.system() != "Windows":
        return False, "n/a"
    try:
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             f"$t = Get-ScheduledTask -TaskName '{WATCHDOG_TASK}' "
             "-ErrorAction SilentlyContinue; "
             "if ($t) { $t.State } else { 'NotInstalled' }"],
            capture_output=True, text=True, timeout=10,
        )
        state = (r.stdout or "").strip()
        if state and state != "NotInstalled":
            return True, state
        return False, "NotInstalled"
    except Exception as e:
        return False, f"error: {e}"


def main() -> int:
    cfg_path, pw_enabled = find_plugin_config()
    procs = get_playwright_processes()
    wd_installed, wd_state = check_watchdog()

    killer_exists = KILLER.exists()
    wd_script_exists = WATCHDOG.exists()

    print("=" * 56)
    print("PLAYWRIGHT MCP PLUGIN STATUS")
    print("=" * 56)
    print(f"Plugin enabled : {'OK YES (enabledPlugins)' if pw_enabled else 'FAIL NOT FOUND'}")
    print(f"Settings file  : {cfg_path if cfg_path else 'FAIL NOT FOUND'}")
    print(f"Node procs     : {len(procs)} alive"
          + (f" (max age {max(p['age_minutes'] for p in procs)}min)" if procs else " (will start on next use)"))
    if procs:
        for p in procs[:5]:
            print(f"                 PID={p['pid']} age={p['age_minutes']}min")
    print(f"Stale killer   : {'OK EXISTS' if killer_exists else 'FAIL MISSING'}  ({KILLER.name})")
    print(f"Watchdog script: {'OK EXISTS' if wd_script_exists else 'FAIL MISSING'}  ({WATCHDOG.name})")
    print(f"Watchdog task  : {'OK ' + wd_state if wd_installed else 'WARN NOT INSTALLED (' + wd_state + ')'}")
    print()

    resilient = killer_exists and wd_script_exists and wd_installed
    if pw_enabled and resilient:
        print("OK PLAYWRIGHT MCP: PLUGIN READY + RESILIENT")
        print("   Transport disconnects will auto-resolve via watchdog cycles.")
    elif pw_enabled and killer_exists and wd_script_exists:
        print("WARN PLUGIN ENABLED, scripts present, but watchdog NOT INSTALLED")
        print("   Install: powershell -File tools\\playwright_watchdog.ps1 -Action start")
    elif pw_enabled:
        print("WARN PLUGIN ENABLED but resilience scripts missing")
    else:
        print("FAIL PLAYWRIGHT PLUGIN NOT ENABLED in ~/.claude/settings.json")

    print()
    print("QUICK FIX (if disconnected right now):")
    print("  powershell -File tools\\playwright_stale_killer.ps1")
    print("  Then retry your Playwright command in Claude Code.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
