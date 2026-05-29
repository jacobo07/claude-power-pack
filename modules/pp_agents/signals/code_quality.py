"""pp-code-reviewer signal -- Jobs gate on anti-pattern hits."""
from __future__ import annotations

import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[3]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.pp_agents.proactive_core import ProactiveSignal


def evaluate(last_written_code: str = "",
             project: str = "global") -> ProactiveSignal | None:
    """Fire when newly-written code carries detectable anti-patterns.

    Silence (None) when no code was written or no anti-pattern hits --
    silence is implicit Jobs approval.
    """
    if not last_written_code or len(last_written_code) < 50:
        return None
    try:
        from modules.uqf.anti_patterns import run_all
    except Exception:
        return None
    try:
        results = run_all(last_written_code)
    except Exception:
        return None
    hits = {k: v for k, v in results.items() if v}
    if not hits:
        return None
    worst_name, worst_hits = sorted(
        hits.items(), key=lambda item: -len(item[1]))[0]
    detector = worst_name.replace("detect_", "").replace("_", " ")
    count = len(worst_hits)
    return ProactiveSignal(
        agent_name="pp-code-reviewer",
        trigger="anti_pattern_in_new_code",
        value=min(1.0, count * 0.25),
        advisory=(
            f"{count} instance(s) of '{detector}' in newly-written code.\n"
            f"Jobs standard: fix before shipping."
        ),
        gate="jobs",
        actionable="python tools/uqf_audit.py --scan-all",
    )
