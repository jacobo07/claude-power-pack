"""pp-ceps-analyst signal -- Woz gate on recurring errors."""
from __future__ import annotations

import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[3]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.pp_agents.proactive_core import ProactiveSignal


def evaluate(current_error: str = "",
             project: str = "global") -> ProactiveSignal | None:
    """Fire when the current error matches a known lesson >=2 times.

    First-time errors stay silent -- they are learning opportunities,
    not interruption opportunities.
    """
    if not current_error:
        return None
    try:
        from modules.osa.never_again import query
    except Exception:
        return None
    try:
        results = query(current_error[:50])
    except Exception:
        return None
    if not results:
        return None
    top = results[0]
    recurrence = int(getattr(top, "recurrence", 0))
    if recurrence < 2:
        return None
    fix_text = str(getattr(top, "fix", "") or "")[:80]
    return ProactiveSignal(
        agent_name="pp-ceps-analyst",
        trigger="recurring_error",
        value=min(1.0, recurrence * 0.2),
        advisory=(
            f"This error has occurred {recurrence}x before.\n"
            f"Woz asks: why are we still here?"
        ),
        gate="woz",
        actionable=f"Known fix: {fix_text}" if fix_text else
                   "Inspect modules/osa/never_again history",
    )
