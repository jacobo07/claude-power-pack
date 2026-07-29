"""Alert escalation -- promote a repeat finding nobody resolved, then go quiet.

Consumed by `tools/background_verifier_run.py` (Zero-Command Component C).
"""
from .policy import (  # noqa: F401
    ESCALATE,
    ROUTINE,
    SUPPRESS,
    Decision,
    Entry,
    Policy,
    count_prior_occurrences,
    finding_key,
    handoff_timestamp,
    load_ledger,
    load_policy,
    note_resolved,
    observe,
    open_escalations,
    render_standing_report,
    save_ledger,
    write_standing_report,
)

__all__ = [
    "ESCALATE", "ROUTINE", "SUPPRESS", "Decision", "Entry", "Policy",
    "count_prior_occurrences", "finding_key", "handoff_timestamp",
    "load_ledger", "load_policy", "note_resolved", "observe",
    "open_escalations", "render_standing_report", "save_ledger",
    "write_standing_report",
]
