"""One-Shot Compiler -- BL-ONESHOT-001.

Compile a task description into a frozen contract (scope, budget,
done-gate, out-of-scope). Fidelity lock detects scope deviation.
Escalation ladder (OD7): 2 fails -> Opus, 3 fails -> STOP.

Public API: compile_contract, OneShotContract, BUDGETS,
fidelity_score, is_deviated, SCOPE_DEVIATION_THRESHOLD,
should_escalate, should_stop, recommend_action.
"""
from .compiler import BUDGETS, OneShotContract, compile_contract
from .escalation import (
    ESCALATE_TO_OPUS_AT,
    STOP_AT,
    recommend_action,
    should_escalate,
    should_stop,
)
from .lock import SCOPE_DEVIATION_THRESHOLD, fidelity_score, is_deviated

__all__ = [
    "BUDGETS",
    "ESCALATE_TO_OPUS_AT",
    "OneShotContract",
    "SCOPE_DEVIATION_THRESHOLD",
    "STOP_AT",
    "compile_contract",
    "fidelity_score",
    "is_deviated",
    "recommend_action",
    "should_escalate",
    "should_stop",
]
