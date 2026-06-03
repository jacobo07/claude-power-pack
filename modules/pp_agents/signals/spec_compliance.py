"""pp-spec-guardian signal -- Jobs gate on missing specs for L/XL tasks.

Fires when the current prompt looks like a large/complex build AND the
active repo has no spec file (check_spec_gate -> action=create_spec).
Surfaces the gap BEFORE coding so CLASE 1 (API assumptions) and CLASE 2
(false premises) cannot accrue.

Sleepy-by-default: returns None (silence = approval) for S/M tasks, for
prompts with no large-task signal, and when a spec already exists.

Sealed BL-SPEC-DEPT-001 (2026-06-03).
"""
from __future__ import annotations

import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[3]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.pp_agents.proactive_core import ProactiveSignal

# Keywords that mark a prompt as a large/complex build worth a spec.
# Word-boundary-ish: matched as lowercase substrings, kept specific so
# "fix" / "rename" / "typo" prompts never trip the gate.
LARGE_SIGNALS = (
    "build a complete", "build the complete", "implement a complete",
    "implement the complete", "create a complete", "from scratch",
    "build a full", "implement a full", "entire system", "whole system",
    "design the architecture", "migrate", "rewrite", "end-to-end",
    "build a new", "implement a new feature", "complete auth",
)


def _looks_large(prompt: str) -> bool:
    p = (prompt or "").lower()
    return any(sig in p for sig in LARGE_SIGNALS)


def evaluate(prompt: str = "",
             cwd: str = "",
             project: str = "global") -> ProactiveSignal | None:
    """Fire when a large-task prompt starts in a repo with no spec."""
    if not prompt or not _looks_large(prompt):
        return None
    try:
        from modules.spec_gate.gate import check_spec_gate
    except Exception:
        return None
    try:
        root = Path(cwd) if cwd else Path.cwd()
        result = check_spec_gate(prompt, cwd=root, task_size="L")
    except Exception:
        return None
    # gate_passed is True both for S/M (n/a) and when a spec already
    # exists -> stay silent. Only the create_spec action is actionable.
    if result.gate_passed or result.action != "create_spec":
        return None
    return ProactiveSignal(
        agent_name="pp-spec-guardian",
        trigger="spec_gate_create",
        value=0.7,
        advisory=(
            "L/XL task with no spec in this repo. Establish one before "
            "coding -- the scope and done-gate belong in the spec, not "
            "in the agent's head."
        ),
        gate="jobs",
        actionable=(
            "Use the auto-injected One-Shot contract, or run "
            "python modules/karimo-harness/prd_parser.py <prd>."
        ),
    )


__all__ = ["LARGE_SIGNALS", "evaluate"]
