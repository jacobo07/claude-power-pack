"""pp-uqf-auditor signal -- Woz gate on UQF score under threshold."""
from __future__ import annotations

import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[3]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.pp_agents.proactive_core import ProactiveSignal


def evaluate(file_path: str = "",
             project: str = "global") -> ProactiveSignal | None:
    """Fire when UQF score < 70% for the last-touched Python file."""
    if not file_path or not file_path.endswith(".py"):
        return None
    target = Path(file_path)
    if not target.is_file():
        return None
    try:
        from modules.uqf.auditor import UQFAuditor
    except Exception:
        return None
    try:
        report = UQFAuditor().audit_file(str(target))
    except Exception:
        return None
    score = float(getattr(report, "score_pct", 0.0) or 0.0)
    if score >= 70.0:
        return None
    hints = list(getattr(report, "fix_hints", []) or [])
    top_hint = hints[0][:100] if hints else ""
    actionable = top_hint or f"python tools/uqf_audit.py {file_path}"
    return ProactiveSignal(
        agent_name="pp-uqf-auditor",
        trigger="quality_below_threshold",
        value=1.0 - (score / 100.0),
        advisory=(
            f"UQF score: {score:.0f}% (S+++ floor = 70%).\n"
            f"Woz: there is a more elegant solution."
        ),
        gate="woz",
        actionable=actionable,
    )
