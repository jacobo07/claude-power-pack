"""pp-error-analyst signal -- Woz gate on uncovered recurring errors.

Fires when the session has hit errors AND the NEVER_AGAIN log holds an
entry that has recurred 3+ times without a covering Hard Rule in
CLAUDE.md. Surfaces the recurring class so the Owner converts it into a
structural stop via bug_to_hardrule.

Hot-path safe: reads the installed-HR text in-process (a single file
read), never spawns a subprocess on UserPromptSubmit. The HR-coverage
check is a cheap keyword overlap, not an LLM call.

Sleepy-by-default: returns None on a clean session and when every
recurring error is already HR-covered.

Sealed BL-SPEC-DEPT-001 (2026-06-03).
"""
from __future__ import annotations

import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[3]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.pp_agents.proactive_core import ProactiveSignal

RECURRENCE_THRESHOLD = 3
# CLAUDE.md is the operative source of installed Hard Rules (the inline
# mirror); HARD_RULES.md is a partial archive. Read the live block.
_CLAUDE_MD = PP_ROOT / "CLAUDE.md"


def _installed_hr_text() -> str:
    try:
        return _CLAUDE_MD.read_text(encoding="utf-8-sig").lower()
    except OSError:
        return ""


def _has_hr_coverage(issue: str, hr_text: str) -> bool:
    """Cheap overlap: an HR covers the issue if it mentions >=2 of the
    issue's distinctive (len>4) words. Conservative -- a false 'covered'
    only silences the nudge, never blocks anything."""
    if not hr_text:
        return False
    words = [w for w in "".join(
        c if c.isalnum() else " " for c in issue.lower()).split()
        if len(w) > 4]
    hits = sum(1 for w in words[:6] if w in hr_text)
    return hits >= 2


def _top_uncovered() -> tuple[str, int] | None:
    try:
        from modules.osa.never_again import top_recurring
    except Exception:
        return None
    try:
        hr_text = _installed_hr_text()
        for entry in top_recurring(10):
            # NeverAgainEntry is a dataclass -- attribute access.
            if int(entry.recurrence) >= RECURRENCE_THRESHOLD:
                if not _has_hr_coverage(entry.issue, hr_text):
                    return (entry.issue[:60], int(entry.recurrence))
    except Exception:
        return None
    return None


def evaluate(session_had_errors: bool = False,
             project: str = "global") -> ProactiveSignal | None:
    """Fire on an uncovered recurring error when the session has erred."""
    if not session_had_errors:
        return None
    hit = _top_uncovered()
    if hit is None:
        return None
    issue, recurrence = hit
    return ProactiveSignal(
        agent_name="pp-error-analyst",
        trigger="recurring_error_no_hr",
        value=0.7,
        advisory=(
            f"Recurring error without a Hard Rule ({recurrence}x): "
            f"{issue}. A bug seen {recurrence} times is broken "
            "architecture, not bad luck."
        ),
        gate="woz",
        actionable=(
            f'python tools/bug_to_hardrule.py --propose "{issue}"'
        ),
    )


__all__ = ["RECURRENCE_THRESHOLD", "evaluate"]
