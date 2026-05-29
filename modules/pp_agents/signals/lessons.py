"""pp-never-again signal -- Jobs gate on errors-fixed-without-lesson."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[3]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.pp_agents.proactive_core import ProactiveSignal


def evaluate(session_had_errors: bool = False,
             errors_fixed: int = 0,
             project: str = "global") -> ProactiveSignal | None:
    """Fire once per day when errors were fixed without recording lesson."""
    if not session_had_errors or errors_fixed <= 0:
        return None
    try:
        from modules.osa.never_again import top_recurring
    except Exception:
        return None
    try:
        recent = top_recurring(1)
    except Exception:
        recent = []
    last_iso = ""
    if recent:
        last_iso = str(getattr(recent[0], "iso", "") or "")[:10]
    if last_iso == str(date.today()):
        return None
    return ProactiveSignal(
        agent_name="pp-never-again",
        trigger="errors_fixed_without_lesson",
        value=0.8,
        advisory=(
            f"Fixed {errors_fixed} error(s) without recording a lesson.\n"
            f"Jobs: learning is the only output that compounds."
        ),
        gate="jobs",
        actionable="Invoke pp-never-again to register the lesson",
    )
