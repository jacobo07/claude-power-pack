"""pp-backlog-autopilot signal -- proactive P0 surfacing.

Fires when the active project's backlog (vault/backlog.json) has an
actionable P0 item. Wires modules.backlog_autopilot into the live
proactive-dispatch path. Silence (None) when there is no backlog, no
actionable item, or the top recommendation is not P0.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[3]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.pp_agents.proactive_core import ProactiveSignal

# Signal strength when an actionable P0 is found. Above the
# pp-backlog-autopilot AgentConfig.min_signal_strength (0.7) so it
# fires; below 1.0 so a future "P0 + blocked-dependency" variant can
# rank higher.
P0_SIGNAL_STRENGTH = 0.9


def _backlog_path(project: str) -> Path:
    # Per-project backlog file if present, else the repo-level default.
    per_project = PP_ROOT / "vault" / f"backlog_{project}.json"
    if per_project.is_file():
        return per_project
    return PP_ROOT / "vault" / "backlog.json"


def evaluate(project: str = "global") -> ProactiveSignal | None:
    backlog_file = _backlog_path(project)
    if not backlog_file.is_file():
        return None
    try:
        raw = json.loads(backlog_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(raw, list) or not raw:
        return None

    try:
        from modules.backlog_autopilot.engine import BacklogItem, what_now
    except (ImportError, ModuleNotFoundError):
        return None

    try:
        backlog = [
            BacklogItem(
                id=str(item.get("id", "?")),
                title=str(item.get("title", "?")),
                priority=int(item.get("priority", 2)),
                effort=str(item.get("effort", "M")),
                impact=str(item.get("impact", "Medium")),
                blockers=tuple(item.get("blockers", []) or []),
                done=bool(item.get("done", False)),
            )
            for item in raw
            if isinstance(item, dict)
        ]
    except (TypeError, ValueError):
        return None

    result = what_now(backlog)
    rec = result.recommended
    if rec is None or rec.priority != 0:
        return None

    return ProactiveSignal(
        agent_name="pp-backlog-autopilot",
        trigger="actionable_p0",
        value=P0_SIGNAL_STRENGTH,
        advisory=(
            f"/what-now -> P0: {rec.title} "
            f"({rec.effort} effort, {rec.impact} impact).\n"
            f"Highest-ROI actionable item right now."
        ),
        gate="jobs",
        actionable="python -c \"from modules.backlog_autopilot import "
                   "what_now; ...\"  (or /what-now)",
    )
