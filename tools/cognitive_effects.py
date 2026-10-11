"""Cognitive effect classes + ABI for routes/packets (CDC C2). Pure, deterministic, no model.

One enum over cost_to_completion classes and tier_routing work classes; old names stay as aliases.
ABI fields: effect, deopt, invalidators, expected_boundaries. Absent effect = BOUNDED_COGNITION (logged).
"""
from __future__ import annotations

import os

ZERO_COGNITION, DETERMINISTIC, BOUNDED_COGNITION = "ZERO_COGNITION", "DETERMINISTIC", "BOUNDED_COGNITION"
NOVEL_COGNITION, OWNER_COGNITION = "NOVEL_COGNITION", "OWNER_COGNITION"
EFFECTS = (ZERO_COGNITION, DETERMINISTIC, BOUNDED_COGNITION, NOVEL_COGNITION, OWNER_COGNITION)
NO_MODEL_EFFECTS = (ZERO_COGNITION, DETERMINISTIC)
ALIASES = {
    "satisfied": ZERO_COGNITION, "sleeping": ZERO_COGNITION,
    "deterministic": DETERMINISTIC,
    "known_transform": BOUNDED_COGNITION, "bounded_coding": BOUNDED_COGNITION,
    "novel": NOVEL_COGNITION,
    "owner_reality": OWNER_COGNITION,
}
ABI_LEN_FIELDS = ("deopt", "invalidators", "expected_boundaries")


def normalize(name):
    """Enum name or legacy alias -> enum; None if unknown (UNKNOWN is not zero)."""
    if name in EFFECTS:
        return name
    return ALIASES.get(name) if isinstance(name, str) else None


def gate_enabled() -> bool:
    return os.environ.get("CDC_EFFECT_GATE", "").lower() != "off"


def validate_route(route: dict) -> dict:
    """-> {ok, effect, defaulted, reasons}. ok False only for a model boundary opened without deopt
    or a malformed ABI field. Never raises: own error returns ok True with reason (fail open)."""
    try:
        reasons = []
        raw = route.get("effect")
        defaulted = raw is None
        eff = BOUNDED_COGNITION if defaulted else normalize(raw)
        if eff is None:
            return {"ok": False, "effect": None, "defaulted": False,
                    "reasons": [f"unknown effect {raw!r}"]}
        for f in ABI_LEN_FIELDS:
            v = route.get(f)
            if v is not None and (not isinstance(v, list) or not all(isinstance(x, str) and x for x in v)):
                reasons.append(f"{f} must be a list of non-empty strings")
        if eff in NO_MODEL_EFFECTS and route.get("workers") and not route.get("deopt"):
            reasons.append(f"{eff} route requests model workers without a deopt entry")
        return {"ok": not reasons, "effect": eff, "defaulted": defaulted, "reasons": reasons}
    except Exception as e:  # noqa: BLE001 - fail open on own error
        return {"ok": True, "effect": None, "defaulted": False, "reasons": [f"effects check error: {e!r}"]}
