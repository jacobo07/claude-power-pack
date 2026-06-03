"""pp-premise-guardian signal -- Woz gate on unverified-premise risk.

Fires when the session has hit errors AND a CLASE 1 pattern (an assumed
API / function / attribute / import / signature that does not exist) is
present in the current error text or in a recurring NEVER_AGAIN entry.
Surfaces the risk so the agent verifies the REAL public API before
writing more code against an assumed signature.

Sleepy-by-default: returns None on a clean session (session_had_errors
False) -- a first observation teaches, it is not yet a premise failure.

Sealed BL-SPEC-DEPT-001 (2026-06-03).
"""
from __future__ import annotations

import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[3]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.pp_agents.proactive_core import ProactiveSignal

# CLASE 1 markers: an assumed-but-nonexistent API surface.
CLASE1_KEYWORDS = (
    "no attribute", "does not exist", "has no attribute",
    "cannot import", "no module named", "is not defined",
    "unexpected keyword argument", "takes no arguments",
    "missing 1 required", "object is not callable",
    "attributeerror", "importerror", "modulenotfounderror",
    "typeerror",
)


def _is_clase1(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in CLASE1_KEYWORDS)


def _recurring_clase1() -> tuple[str, int] | None:
    """Return (issue, recurrence) of the top recurring CLASE 1 entry."""
    try:
        from modules.osa.never_again import top_recurring
    except Exception:
        return None
    try:
        for entry in top_recurring(20):
            # NeverAgainEntry is a dataclass -- attribute access, not .get.
            if int(entry.recurrence) >= 2 and _is_clase1(entry.issue):
                return (entry.issue, int(entry.recurrence))
    except Exception:
        return None
    return None


def evaluate(current_error: str = "",
             session_had_errors: bool = False,
             project: str = "global") -> ProactiveSignal | None:
    """Fire on a CLASE 1 pattern when the session has actually erred."""
    if not session_had_errors:
        return None

    if _is_clase1(current_error):
        issue = current_error.strip()[:60]
        recurrence = 1
    else:
        hit = _recurring_clase1()
        if hit is None:
            return None
        issue, recurrence = hit[0][:60], hit[1]

    return ProactiveSignal(
        agent_name="pp-premise-guardian",
        trigger="premise_risk_clase1",
        value=0.65,
        advisory=(
            f"CLASE 1 pattern ({recurrence}x): {issue}. "
            "Verify the REAL public API before writing more code against "
            "an assumed signature."
        ),
        gate="woz",
        actionable=(
            "python modules/error_prevention/premise_verifier.py "
            "--self-test  (or assert_premises([...]) in-process)."
        ),
    )


__all__ = ["CLASE1_KEYWORDS", "evaluate"]
