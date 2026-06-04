#!/usr/bin/env python3
"""verify_mcp_health.py -- MCP-Stability done-gate (BL-MCP-STABILITY-001).

A verify_spp row. Asserts the PP-CONTROLLABLE machinery for MCP stability
is present and active. It deliberately does NOT fail on a stdio server that
happens to be disconnected right now: a stdio mcpServer (-32000) is recovered
only Claude-side, never by the PP (T-MCP-RECONNECT-001), so its live state is
an OPERATIONAL condition, surfaced as ADVISORY, captured by telemetry for
death-mode classification -- not a gate failure (no-classified-FAILs doctrine).

STRICT V-gates (PP-controllable):
  V-MCP-HEALTHTOOL          mcp_health_check.py present + importable
  V-MCP-DETECTION           it classifies every configured server (no UNKNOWN)
  V-MCP-PW-SCRIPTS          stale_killer + watchdog scripts present
  V-MCP-PW-WATCHDOG-TASK    Playwright watchdog scheduled task installed
                            (the real auto-recovery; install via
                             playwright_watchdog.ps1 -Action start)
  V-MCP-TELEMETRY           telemetry log writable + >=1 classified row

ADVISORY (printed, non-failing):
  per-stdio-server liveness (e.g. magic-ui DEAD == client-side reconnect)

ASCII-only. Exit 0 iff every STRICT gate passes.
"""
from __future__ import annotations

import platform
import sys
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
TOOLS = PP / "tools"
sys.path.insert(0, str(TOOLS))

passes = 0
fails = 0


def _ok(gate: str, evidence: str) -> None:
    global passes
    passes += 1
    print(f"  OK   {gate:<26s} {evidence}")


def _fail(gate: str, diag: str) -> None:
    global fails
    fails += 1
    print(f"  FAIL {gate:<26s} {diag}")


def _adv(gate: str, note: str) -> None:
    print(f"  ADV  {gate:<26s} {note}")


def main() -> int:
    print("=" * 60)
    print("verify_mcp_health -- MCP-Stability machinery gate")
    print("=" * 60)

    # --- import the health tool -------------------------------------
    try:
        import mcp_health_check as mh  # type: ignore
    except Exception as e:
        _fail("V-MCP-HEALTHTOOL", f"import failed: {e}")
        print(f"\nMCP_HEALTH_PASS={passes}/{passes + fails}  threshold=strict")
        return 1

    tool = TOOLS / "mcp_health_check.py"
    if tool.is_file():
        _ok("V-MCP-HEALTHTOOL", f"{tool.name} present + importable")
    else:
        _fail("V-MCP-HEALTHTOOL", "mcp_health_check.py missing")

    # --- run the probes ---------------------------------------------
    servers = mh.load_stdio_servers()
    procs = mh.get_running_cmdlines()
    stdio = mh.probe_stdio(servers, procs)
    playwright = mh.probe_playwright()

    # V-MCP-DETECTION: every stdio server classified (no UNKNOWN)
    unknown = [n for n, e in stdio.items() if e["status"] == "UNKNOWN"]
    if servers and not unknown:
        _ok("V-MCP-DETECTION",
            f"{len(stdio)} stdio server(s) classified, plugin={playwright['status']}")
    elif not servers:
        _ok("V-MCP-DETECTION", "no stdio servers configured (vacuously ok)")
    else:
        _fail("V-MCP-DETECTION", f"UNKNOWN status for: {unknown}")

    # V-MCP-PW-SCRIPTS
    killer = TOOLS / "playwright_stale_killer.ps1"
    wd = TOOLS / "playwright_watchdog.ps1"
    if killer.is_file() and wd.is_file():
        _ok("V-MCP-PW-SCRIPTS", "stale_killer + watchdog scripts present")
    else:
        missing = [p.name for p in (killer, wd) if not p.is_file()]
        _fail("V-MCP-PW-SCRIPTS", f"missing: {missing}")

    # V-MCP-PW-WATCHDOG-TASK (the real auto-recovery contract)
    if platform.system() != "Windows":
        _adv("V-MCP-PW-WATCHDOG-TASK", "non-Windows host -- watchdog n/a")
        _ok("V-MCP-PW-WATCHDOG-TASK", "skipped on non-Windows (vacuously ok)")
    else:
        installed = bool(playwright.get("watchdog_installed"))
        state = playwright.get("watchdog_state", "unknown")
        if installed:
            _ok("V-MCP-PW-WATCHDOG-TASK", f"scheduled task state={state}")
        else:
            _fail("V-MCP-PW-WATCHDOG-TASK",
                  "NOT installed -- run: "
                  "powershell -File tools\\playwright_watchdog.ps1 -Action start")

    # V-MCP-TELEMETRY: write one row (also logs this verify event), assert it landed
    merged = dict(stdio)
    merged["playwright"] = playwright
    mh.append_telemetry("verify", merged)
    log = PP / "vault" / "telemetry" / "mcp_health" / "mcp_state.jsonl"
    if log.is_file() and log.stat().st_size > 0:
        rows = sum(1 for _ in log.open(encoding="utf-8"))
        _ok("V-MCP-TELEMETRY", f"{rows} classified row(s) in {log.name}")
    else:
        _fail("V-MCP-TELEMETRY", "telemetry log absent or empty after append")

    # --- advisory: live stdio liveness (operational, never a gate) ---
    for n, e in stdio.items():
        if e["status"] == "DEAD":
            _adv("V-MCP-STDIO-LIVENESS",
                 f"{n} DEAD -> reconnect in Claude Code via /mcp (T-MCP-RECONNECT-001)")

    print("-" * 60)
    print(f"MCP_HEALTH_PASS={passes}/{passes + fails}  threshold=strict (all OK)")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
