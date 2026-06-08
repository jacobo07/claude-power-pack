"""pp-setup-scan signal -- nudge /scan-repo on an un-profiled repo.

Fires once per repo (24h throttle via the dispatcher) when the active repo has
no persisted ProjectProfile in the Setup-OS registry. A scan is the Setup-OS
Pillar 1 prerequisite for any ROI / install recommendation. Silent once the
repo has been scanned (registry hit) -- silence = approval.

Cross-repo: the registry lives in the PP repo (absolute path), keyed by the
active cwd, so the check works from ANY repo. Composes setup_os.registry
(SCS C28). Sealed BL-GOV-PROP-001 (2026-06-08, SCS C43).
"""
from __future__ import annotations

import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[3]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.pp_agents.proactive_core import ProactiveSignal


def evaluate(cwd: str = "",
             project: str = "global") -> ProactiveSignal | None:
    """Fire when the active repo has no persisted ProjectProfile."""
    if not cwd:
        return None  # no repo context (empty cwd) -> nothing to nag about
    try:
        from modules.setup_os.registry import has_profile
    except Exception:
        return None
    try:
        root = Path(cwd)
        if has_profile(root):
            return None  # already scanned -> silent
    except Exception:
        return None
    return ProactiveSignal(
        agent_name="pp-setup-scan",
        trigger="repo_unscanned",
        value=0.6,
        advisory=(
            "This repo has no Setup-OS ProjectProfile yet. A read-only scan "
            "maps its language / framework / CI / secrets / Claude-config "
            "before any automation is recommended (the repo on disk is the "
            "source of truth)."
        ),
        gate="woz",
        actionable=(
            "Run /scan-repo (python -m modules.setup_os.scanner --path . "
            "--save) to profile this repo once."
        ),
    )


__all__ = ["evaluate"]
