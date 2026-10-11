"""EVC confidence state machine and miss taxonomy for work-class profiles. Pure: no IO, no clock.

States, from the sample count n and the profile's misses (the {"need","actual"[,"kind"]} dicts
route_admission.record_actual stores):
  UNKNOWN (n=0) < EXPLORATORY (1-2) < PROVISIONAL (3-4) < CALIBRATED (5+, no material miss)
  DEGRADED     one or more material misses (actual > MISS_FACTOR x need)
  INVALIDATED  three comparable material misses (same kind), or one miss >= 10x need without an
               isolated-anomaly proof string
"""
from __future__ import annotations

import route_admission as ra

STATES = ("UNKNOWN", "EXPLORATORY", "PROVISIONAL", "CALIBRATED", "DEGRADED", "INVALIDATED")
TAXONOMY = ("CALL_COUNT", "CONTEXT_GROWTH", "WORK_CLASS_MISCLASSIFICATION", "PROOF_TAIL", "CLOSEOUT_TAIL",
            "REPAIR", "CONTROL_PLANE_LEAK", "SEMANTIC_SCOPE", "STALE_USAGE_TRUTH", "RESOURCE_ANOMALY",
            "PROVIDER_BEHAVIOR_CHANGE", "PROFILE_TRANSFER", "UNKNOWN")
FIOS_MAP = {
    "CALL_COUNT": "route-shape",
    "CONTEXT_GROWTH": "context-rent",
    "WORK_CLASS_MISCLASSIFICATION": "classification",
    "PROOF_TAIL": "proof-cost",
    "CLOSEOUT_TAIL": "closeout-cost",
    "REPAIR": "rework",
    "CONTROL_PLANE_LEAK": "control-plane",
    "SEMANTIC_SCOPE": "scope",
    "STALE_USAGE_TRUTH": "usage-truth",
    "RESOURCE_ANOMALY": "host-resource",
    "PROVIDER_BEHAVIOR_CHANGE": "provider",
    "PROFILE_TRANSFER": "profile-transfer",
    "UNKNOWN": "unclassified",
}
LARGE_TOKENS = 1_000_000
OOM_FACTOR = 10


def _material(m: dict) -> bool:
    return m["actual"] > ra.MISS_FACTOR * m["need"]


def classify_miss(need: int, actual: int, evidence: dict) -> str:
    """One taxonomy name from evidence; never guesses (no evidence -> UNKNOWN)."""
    ev = evidence or {}
    k = ev.get("kind")
    if k in TAXONOMY:
        return k
    if (ev.get("calls_ratio") or 0) > ra.MISS_FACTOR:
        return "CALL_COUNT"
    if (ev.get("ctx_ratio") or 0) > ra.MISS_FACTOR:
        return "CONTEXT_GROWTH"
    return "UNKNOWN"


def _kind(m: dict) -> str:
    k = m.get("kind")
    return k if k in TAXONOMY else classify_miss(m["need"], m["actual"], {})


def state(n: int, misses: list, isolated_anomaly: str = "") -> str:
    mat = [m for m in (misses or []) if _material(m)]
    if mat:
        if any(m["actual"] >= OOM_FACTOR * m["need"] for m in mat) and not (isolated_anomaly or "").strip():
            return "INVALIDATED"
        by_kind: dict = {}
        for m in mat:
            by_kind.setdefault(_kind(m), []).append(m)
        if any(len(v) >= 3 and ra.is_degraded({"misses": v}) for v in by_kind.values()):
            return "INVALIDATED"
        return "DEGRADED"
    if n <= 0:
        return "UNKNOWN"
    if n <= 2:
        return "EXPLORATORY"
    if n <= 4:
        return "PROVISIONAL"
    return "CALIBRATED"


def may_admit_large(state: str, tranche: bool = False) -> bool:
    if state in ("CALIBRATED", "PROVISIONAL"):
        return True
    return state == "DEGRADED" and bool(tranche)
