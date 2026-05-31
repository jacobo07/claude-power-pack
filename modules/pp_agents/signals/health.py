"""pp-monitor signal -- Jobs gate on service DOWN.

Also exposes check_playwright_mcp_plugin() (BL-PLAYWRIGHT-001 sealed
2026-05-31) as a stand-alone callable for any pp-agent that wants to
surface stale-process risk for the Playwright MCP plugin.
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[3]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.pp_agents.proactive_core import ProactiveSignal


def evaluate(project: str = "global") -> ProactiveSignal | None:
    """Fire only when the project has a monitor state file marked DOWN.

    Silence when:
      - no monitor config for the project
      - no state file yet
      - state.status != DOWN
    """
    monitor_cfg = PP_ROOT / "vault" / "monitor" / f"{project}.json"
    if not monitor_cfg.is_file():
        return None
    state_file = PP_ROOT / "vault" / "monitor" / f"{project}_state.json"
    if not state_file.is_file():
        return None
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if state.get("status") != "DOWN":
        return None
    since = state.get("last_change_iso", "unknown")
    return ProactiveSignal(
        agent_name="pp-monitor",
        trigger="service_down",
        value=1.0,
        advisory=(
            f"{project.upper()} DOWN since {since}.\n"
            f"Jobs: users are living this right now."
        ),
        gate="jobs",
        actionable="python -m modules.monitoring.observe --once",
    )


def check_playwright_mcp_plugin() -> dict:
    """Health probe for the Playwright MCP plugin (BL-PLAYWRIGHT-001).

    Returns a dict with at least a ``status`` key:
      - ``ok``         : <=3 procs alive, no risk
      - ``stale_risk`` : >3 procs alive, possible transport stale -- advisory
      - ``skip``       : not Windows (PowerShell-based probe)
      - ``error``      : probe failed

    Counts live ``node.exe`` processes whose command line references
    ``@playwright/mcp`` or ``playwright/.../cli.js``. The plugin loader
    spawns one process per active client; >3 is an empirical signal that
    stale processes are accumulating and the transport may be at risk.
    """
    if platform.system() != "Windows":
        return {"status": "skip", "reason": "Windows-only probe"}
    ps_cmd = (
        "Get-CimInstance Win32_Process -Filter \"Name='node.exe'\" "
        "-ErrorAction SilentlyContinue | "
        "Where-Object { $_.CommandLine -and ("
        "$_.CommandLine -like '*@playwright/mcp*' -or "
        "$_.CommandLine -like '*playwright*cli.js*') } | "
        "Measure-Object | Select-Object -ExpandProperty Count"
    )
    try:
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive",
             "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=10,
        )
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
    raw = (r.stdout or "").strip()
    try:
        count = int(raw or "0")
    except ValueError:
        return {"status": "error", "error": f"non-int count: {raw!r}"}
    if count > 3:
        return {
            "status": "stale_risk",
            "count": count,
            "advisory": (
                f"{count} playwright node processes alive -- possible stale "
                "transport. Quick fix: powershell -File "
                "tools\\playwright_stale_killer.ps1"
            ),
        }
    return {"status": "ok", "count": count}
