"""pp-monitor signal -- Jobs gate on service DOWN."""
from __future__ import annotations

import json
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
