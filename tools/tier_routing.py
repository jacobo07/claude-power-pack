"""A4 Work-Class tier routing. Pure, deterministic, no model.

Measured (Master Plan 2026-10-09): slim renewal worker 26k/call, default top-level worker 137k/call.
A work class picks the cheapest tier that can do it; a tier is raised ONLY by a failed verification,
never by a hunch. An unknown class or an unobserved verification never lowers or raises silently:
unknown class -> the default tier (absence is not "cheap"), unobserved verification -> hold + report.

  ZERO_MODEL  no worker (deterministic transform / script)
  SLIM        profile slim-t2 (needs vault/config/slim-critical-settings.json for the budget breaker)
  DEFAULT     profile top-level-worker
"""
from __future__ import annotations

ZERO_MODEL, SLIM, DEFAULT = "ZERO_MODEL", "SLIM", "DEFAULT"
LADDER = (ZERO_MODEL, SLIM, DEFAULT)
PROFILE = {SLIM: "slim-t2", DEFAULT: "top-level-worker"}
CLASS_TIER = {
    "deterministic": ZERO_MODEL,
    "known_transform": SLIM,
    "bounded_coding": SLIM,
    "novel": DEFAULT,
    "owner_reality": DEFAULT,
}
PASSED, FAILED = "PASSED", "FAILED"


EFFECT_TIER = {"ZERO_COGNITION": ZERO_MODEL, "DETERMINISTIC": ZERO_MODEL, "BOUNDED_COGNITION": SLIM,
               "NOVEL_COGNITION": DEFAULT, "OWNER_COGNITION": DEFAULT}   # CDC C2 enum names


def tier_for(work_class) -> str:
    if work_class in CLASS_TIER:
        return CLASS_TIER[work_class]
    return EFFECT_TIER.get(work_class, DEFAULT)


def escalate(tier: str, verification) -> dict:
    """Raise one rung only when verification is exactly FAILED. DEFAULT cannot rise: it is a stop."""
    if tier not in LADDER:
        raise ValueError(f"unknown tier {tier!r}")
    if verification == FAILED:
        if tier == DEFAULT:
            return {"tier": DEFAULT, "escalated": False, "stop": True,
                    "reason": "verification failed at the top tier: no higher rung, stop and report"}
        return {"tier": LADDER[LADDER.index(tier) + 1], "escalated": True, "stop": False,
                "reason": f"verification FAILED at {tier}"}
    if verification == PASSED:
        return {"tier": tier, "escalated": False, "stop": False, "reason": "verification passed"}
    return {"tier": tier, "escalated": False, "stop": False,
            "reason": f"verification {verification!r} is not an observed result: tier held, claim unproven"}


def review_policy(work_class, affected_green, unit_green=True) -> dict:
    """C5: a deterministic unit whose every affected test is observed green needs no reviewer.
    Red, unobserved (None/UNKNOWN) or non-deterministic -> escalate (existing behaviour)."""
    det = tier_for(work_class) == ZERO_MODEL
    green = affected_green is True and unit_green is True
    if det and green:
        return {"reviewer": False, "reason": "deterministic unit + all affected tests green"}
    why = ("affected tests red" if affected_green is False or unit_green is False
           else "affected tests unobserved" if not green else "not a deterministic unit")
    return {"reviewer": True, "reason": why}


def worker_for(work_class, name: str, calls: int, packet: int = 0):
    """Route worker row for the class's tier; None for ZERO_MODEL (no worker is spawned)."""
    t = tier_for(work_class)
    if t == ZERO_MODEL:
        return None
    return {"name": name, "profile": PROFILE[t], "calls": calls, "packet": packet}
