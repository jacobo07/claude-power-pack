"""pp-tco-advisor signal -- Jobs gate on session cost / context pressure."""
from __future__ import annotations

import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[3]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.pp_agents.proactive_core import ProactiveSignal


def evaluate(project: str = "global") -> ProactiveSignal | None:
    """Fire when context proxy crosses 60%. Silence below that."""
    try:
        import tools.tco_compact_gate as gate
    except Exception:
        return None

    pct: float | None = None
    try:
        pct = float(gate.estimate_context_pct())
    except Exception:
        pct = None
    if pct is None:
        try:
            result = gate.check_compact_gate()
            if isinstance(result, tuple) and result:
                first = result[0]
                if isinstance(first, (int, float)):
                    pct = float(first)
        except Exception:
            return None
    if pct is None or pct < 60:
        return None
    urgency = "CRITICAL" if pct >= 80 else "AVISO"
    return ProactiveSignal(
        agent_name="pp-tco-advisor",
        trigger="context_high",
        value=min(1.0, pct / 100.0),
        advisory=(
            f"{urgency}: context proxy at {pct:.0f}%.\n"
            f"Jobs no toleraria este desperdicio."
        ),
        gate="jobs",
        actionable="/compact -- antes de la proxima tarea",
    )
