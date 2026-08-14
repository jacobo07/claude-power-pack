"""Intent-Verified Done -- close the gate at the end, not only at the start.

`spec_gate` and `sdd_os.pre_exec_gate` ask whether an intent artifact EXISTS
before coding. Nothing asked whether the output SATISFIES it afterwards: of 58
executable gate surfaces measured 2026-08-14, zero read an intent artifact at
close (`vault/audits/DONE_GATE_AUDIT.md`). This module is the other half of
that loop, over the artifact that already exists -- it defines no second
schema.

    from modules.intent_verified import verify_task
    v = verify_task("wire the ledger discovery gate", cwd, observe=True)
    v.verdict      # DONE_VERIFIED / PARTIAL_VERIFIED / BLOCKED / ...
    v.passed       # a done claim is admissible

Plan: vault/plans/intent-verified-done-2026-08-14.md
"""
from __future__ import annotations

from pathlib import Path

from .criteria import (
    Criterion, acceptance_section, criteria_for_task, iter_specs,
    parse_criteria, read_criteria, spec_label,
)
from .join import (
    CriterionResult, Observed, Reach, emitters, observe, parse_results,
    resolve, standing_gate_targets,
)
from .ratchet import RatchetReport, check as ratchet_check, save as ratchet_save
from .verdict import IntentVerification, Verdict, blocking_count, decide


def verify_task(task_description: str, cwd: Path | str | None = None,
                observe_tier: bool = True) -> IntentVerification:
    """Verify one task's output against the criteria its spec declares."""
    root = Path(cwd) if cwd else Path.cwd()
    criteria, spec, reason = criteria_for_task(task_description, root)
    if spec is None:
        return decide([], "", reason, bound=False)
    results = resolve(criteria, root)
    if observe_tier:
        results = observe(results, root)
    return decide(results, spec_label(spec, root), reason)


__all__ = [
    "Criterion", "CriterionResult", "IntentVerification", "Observed", "Reach",
    "RatchetReport", "Verdict", "acceptance_section", "blocking_count",
    "criteria_for_task", "decide", "emitters", "iter_specs", "observe",
    "parse_criteria", "parse_results", "ratchet_check", "ratchet_save",
    "read_criteria", "resolve", "spec_label", "standing_gate_targets",
    "verify_task",
]
