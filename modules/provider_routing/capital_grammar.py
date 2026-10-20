"""Closed capital grammar for the Owner Control Plane (Phase 2). Pure: no I/O, no model, no ledger.

`parse_intent(text)` classifies a WHOLE Owner message. Anything that is not exactly one grammar form is None
(left for the model path); a form with a bad amount is INVALID, so the router can answer it deterministically
instead of guessing. The existing `capital_authority.parse_approval` verbs (approve/modify/revoke) stay with that
module; this one adds the typed ADD/SET/KEEP/STOP forms and shares its negation guard.
"""
from __future__ import annotations

import re
import unicodedata

NEG = re.compile(r"(?:\b(?:don't|dont|do not|not|never|can't|cannot|no)\b|n't\b)")  # = capital_authority._NEG
GOAL = r"[a-z0-9][a-z0-9._-]*"
MAX_AMOUNT = 1_000_000_000  # stated ceiling: anything above is overflow, never clamped
MIN_RAW = 1_000             # a bare integer below this has no unit and no way to know what it means

_AMOUNT = r"\+?([0-9][0-9,_.]*)\s?(m|k)?"  # permissive on purpose: a malformed number is INVALID, not chat
_ADD = r"(?:subelo por|sube por|incrementa|suma|add|raise by|plus|increase by)"
_SET = r"(?:subelo a|sube a|pon el tope en|set to|set total|raise to)"
_AMBIGUOUS = r"(?:subelo|sube)"
_KEEP = {"mantener", "keep"}
_STOP = {"stop", "para", "cierra el goal"}


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t.strip().lower()).rstrip(".!")


def amount(num: str, unit: str | None) -> tuple[int | None, str]:
    """(value, reason). value is None with a reason when the amount is not admissible."""
    s = num.replace(",", "").replace("_", "")
    if "." in s and not unit:
        return None, "a decimal needs a unit (1.5M)"
    if s.count(".") > 1:
        return None, "malformed number"
    v = int(round(float(s) * {"m": 1_000_000, "k": 1_000, None: 1}[unit]))
    if v <= 0:
        return None, "amount must be positive"
    if not unit and v < MIN_RAW:
        return None, f"{v} has no unit: write {v}K, {v}M or the full integer"
    if v > MAX_AMOUNT:
        return None, f"{v:,} is above the stated ceiling {MAX_AMOUNT:,}"
    return v, ""


def _hit(op: str, value: int, **extra) -> dict:
    return {"op": op, "value": value, "goal": None, "reason": "", "choices": None, **extra}


def _invalid(reason: str) -> dict:
    return {"op": "INVALID", "value": None, "goal": None, "reason": reason, "choices": None}


def parse_intent(text) -> dict | None:
    """-> {op: ADD|SET|KEEP|STOP|CLARIFY|INVALID, value, goal, reason, choices} or None (not capital grammar)."""
    if not isinstance(text, str):
        return None
    t = _norm(text)
    if not t or NEG.search(t):
        return None
    if t in _KEEP:
        return {"op": "KEEP", "value": None, "goal": None, "reason": "", "choices": None}
    if t in _STOP:
        return {"op": "STOP", "value": None, "goal": None, "reason": "", "choices": None}
    for op, verb in (("ADD", _ADD), ("SET", _SET)):
        m = re.fullmatch(rf"{verb} {_AMOUNT}", t)
        if m:
            v, why = amount(m.group(1), m.group(2))
            return _hit(op, v) if v else _invalid(why)
    m = re.fullmatch(rf"modify ({GOAL}) to {_AMOUNT}", t)
    if m:
        v, why = amount(m.group(2), m.group(3))
        return _hit("SET", v, goal=m.group(1)) if v else _invalid(why)
    m = re.fullmatch(rf"revoke ({GOAL})", t)
    if m:
        return {"op": "STOP", "value": None, "goal": m.group(1), "reason": "", "choices": None}
    # A bare amount counts only with a unit: a lone "1" or "2" is an answer to a menu, not capital.
    m = re.fullmatch(rf"(?:{_AMBIGUOUS} )?{_AMOUNT}", t)
    if m and (t.split()[0] in ("subelo", "sube") or m.group(2)):
        v, why = amount(m.group(1), m.group(2))
        if not v:
            return _invalid(why)
        return {"op": "CLARIFY", "value": v, "goal": None, "reason": "add or set?",
                "choices": [f"ADD +{v}", f"SET total {v}"]}
    return None
