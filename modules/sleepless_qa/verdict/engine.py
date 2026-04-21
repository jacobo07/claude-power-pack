"""
Verdict engine — aggregates log_pattern + contract + visual strategies.

Strategy order:
  1. log_pattern (cheap, no API) → if confident FAIL, return immediately
  2. contract (structural asserts) → if FAIL, return
  3. visual (Claude Vision) → if screenshots exist

Aggregation rules:
  - Any strategy returning FAIL with confidence >= threshold → final FAIL
  - All returning PASS → final PASS (max confidence across strategies)
  - Any UNCERTAIN → final UNCERTAIN (do not auto-heal)
"""

from __future__ import annotations

import logging
from typing import Any

from ..dumpers.base import ActionScript, EvidenceBundle
from . import contract as contract_strategy
from . import log_pattern as log_strategy
from . import visual as visual_strategy
from .schema import Verdict, VerdictStatus

logger = logging.getLogger(__name__)


def judge(
    bundle: EvidenceBundle,
    action: ActionScript,
    uncertain_threshold: float = 0.7,
) -> Verdict:
    """Main entry point. Returns a single aggregated Verdict."""

    collected: list[Verdict] = []
    total_cost = 0.0

    # 1. log_pattern
    log_verdict = log_strategy.evaluate(bundle)
    collected.append(log_verdict)
    if log_verdict.status == VerdictStatus.FAIL and log_verdict.confidence >= uncertain_threshold:
        log_verdict.strategy = "aggregate"
        log_verdict.metadata["aggregated_from"] = ["log_pattern"]
        return log_verdict

    # 2. contract
    contract_verdict = contract_strategy.evaluate(bundle, action)
    if contract_verdict is not None:
        collected.append(contract_verdict)
        if contract_verdict.status == VerdictStatus.FAIL and contract_verdict.confidence >= uncertain_threshold:
            contract_verdict.strategy = "aggregate"
            contract_verdict.metadata["aggregated_from"] = ["log_pattern", "contract"]
            return contract_verdict

    # 3. visual
    visual_verdict = visual_strategy.evaluate(bundle, uncertain_threshold=uncertain_threshold)
    if visual_verdict is not None:
        collected.append(visual_verdict)
        total_cost += visual_verdict.api_cost_estimate_usd

    # Aggregate
    strategies_used = [v.strategy for v in collected]
    any_uncertain = any(v.status == VerdictStatus.UNCERTAIN for v in collected)
    all_pass = all(v.status == VerdictStatus.PASS for v in collected)
    any_fail = any(v.status == VerdictStatus.FAIL for v in collected)

    if any_fail:
        worst = min(
            (v for v in collected if v.status == VerdictStatus.FAIL),
            key=lambda v: v.confidence,
        )
        worst.strategy = "aggregate"
        worst.metadata["aggregated_from"] = strategies_used
        worst.api_cost_estimate_usd = total_cost
        return worst

    if all_pass:
        best_pass = max(collected, key=lambda v: v.confidence)
        return Verdict(
            status=VerdictStatus.PASS,
            confidence=best_pass.confidence,
            reason=f"All strategies PASS ({len(collected)}): {best_pass.reason}",
            strategy="aggregate",
            evidence_refs=best_pass.evidence_refs,
            priority_level=min(v.priority_level for v in collected),
            api_cost_estimate_usd=total_cost,
            metadata={"aggregated_from": strategies_used},
        )

    if any_uncertain:
        ref_verdict = next(v for v in collected if v.status == VerdictStatus.UNCERTAIN)
        return Verdict(
            status=VerdictStatus.UNCERTAIN,
            confidence=ref_verdict.confidence,
            reason=f"At least one strategy UNCERTAIN: {ref_verdict.reason}",
            strategy="aggregate",
            evidence_refs=ref_verdict.evidence_refs,
            priority_level=2,
            api_cost_estimate_usd=total_cost,
            metadata={"aggregated_from": strategies_used},
        )

    # Fallback — should not reach here
    return Verdict(
        status=VerdictStatus.UNCERTAIN,
        confidence=0.0,
        reason="No strategies produced a verdict",
        strategy="aggregate",
        evidence_refs=[],
        priority_level=2,
        api_cost_estimate_usd=total_cost,
        metadata={"aggregated_from": strategies_used},
    )
