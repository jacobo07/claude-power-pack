"""Spec Gate -- PP BL-SPEC-GATE-001.

Public API: check_spec_gate, SpecGateResult, classify_tier, TierResult.
"""
from .gate import (
    SpecGateResult,
    TierResult,
    check_spec_gate,
    classify_tier,
)

__all__ = [
    "SpecGateResult",
    "TierResult",
    "check_spec_gate",
    "classify_tier",
]
