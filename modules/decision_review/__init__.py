"""Decision Review Kernel (DRK) — the executable Decision axis of the Claude Power Pack.

The doctrine lives in vault/knowledge_base/decision_review/ (DRK-00..07) and
vault/knowledge_base/sdd_os/sdd_os_06_* (accountability). This package is the
runtime SDD-OS Parte V never had: it instantiates a Decision Object, classifies
reversibility + blast radius, routes review depth (L0-Ln), emits one of ten
verdicts, and writes an append-only Decision Record. Composes the sealed families
(arch-decision, one_shot, spec_gate, d2a, acis, cost_collapse, owner_queue);
forks none. Fail-open: pathological input yields DEFER, never a raise.
"""
from __future__ import annotations

from .decision_record import (
    DecisionObject,
    DecisionRecord,
    Evidence,
    EvidenceType,
    Reversibility,
    Verdict,
    ReviewTier,
    Registry,
)

__all__ = [
    "DecisionObject",
    "DecisionRecord",
    "Evidence",
    "EvidenceType",
    "Reversibility",
    "Verdict",
    "ReviewTier",
    "Registry",
]
