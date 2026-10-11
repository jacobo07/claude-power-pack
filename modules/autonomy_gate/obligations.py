"""Owner classifier for Goal Spine obligations (EWC M3).

Reuses `gate.classify()` on the obligation's next_action -- no second set of regexes.
What this layer adds is the obligation context classify() cannot see:

  * RED with an internal next action is the AGENT's work NOW.
  * "another iteration", "takes effort", "uncertain but researchable" are never owner
    categories: classify() reads them as self-answerable and so does this layer.
  * A subjective-only item is the OWNER's (HUMAN_PREF), but a RED item is never
    reclassified as taste -- red means broken, not unliked.
  * `human_gate_ready(obs)`: the Owner may be asked only when no NOW work remains.

Fail closed, as the gate does: a classifier that raised hands the item to the OWNER.
"""
from __future__ import annotations

from . import gate as _g

NOW, APPROVAL, RESOURCE_C, HUMAN_PREF, INFO = "NOW", "APPROVAL", "RESOURCE", "HUMAN_PREF", "INFO"
_CLOSED_STATES = {"closed"}


def _is_open(ob) -> bool:
    return (str(ob.get("state", "open")) not in _CLOSED_STATES
            and str(ob.get("actionability", "")) != "WAIVED")


def classify_obligation(ob) -> dict:
    try:
        if not isinstance(ob, dict):
            raise TypeError("obligation is not a mapping")
        sev = str(ob.get("severity", "") or "")
        declared = str(ob.get("actionability", "") or "")
        action = ob.get("next_action", "")
        v = _g.classify(action if isinstance(action, str) else str(action))
        cat = v.get("category")
        if v.get("owner") == _g.OWNER:
            if cat == "gate-error":
                return {"owner": _g.OWNER, "category": "gate-error", "why": v["why"]}
            if cat == _g.RESOURCE:
                return {"owner": _g.OWNER, "category": RESOURCE_C, "why": v["why"]}
            if cat in (_g.IRREVERSIBLE, _g.OUTWARD):
                return {"owner": _g.OWNER, "category": APPROVAL, "why": v["why"]}
            if cat == _g.PREFERENCE:
                if sev == "RED":
                    return {"owner": _g.AGENT, "category": NOW,
                            "why": "RED is broken, not unliked: fix it, taste applies after"}
                return {"owner": _g.OWNER, "category": HUMAN_PREF, "why": v["why"]}
            return {"owner": _g.OWNER, "category": "gate-error", "why": f"unmapped category {cat!r}"}
        if declared == "HUMAN_PREF" and sev != "RED":
            return {"owner": _g.OWNER, "category": HUMAN_PREF,
                    "why": "declared subjective-only; no internal action derivable"}
        if sev == "INFO" or declared == "INFO":
            return {"owner": _g.AGENT, "category": INFO, "why": "informational; no action required"}
        return {"owner": _g.AGENT, "category": NOW,
                "why": "internal, reversible, derivable next action: do it now"}
    except Exception as exc:  # noqa: BLE001 -- fail closed
        return {"owner": _g.OWNER, "category": "gate-error",
                "why": f"obligation classifier failed ({exc.__class__.__name__}); surfacing instead of guessing"}


def human_gate_ready(obs) -> bool:
    """True iff something is the Owner's AND nothing the agent can do now remains."""
    try:
        open_obs = [o for o in (obs or []) if isinstance(o, dict) and _is_open(o)]
        verdicts = [classify_obligation(o) for o in open_obs]
        if any(v["owner"] == _g.AGENT and v["category"] == NOW for v in verdicts):
            return False
        if any(str(o.get("actionability", "")) == "AFTER_DEP" for o in open_obs):
            return False
        return any(v["owner"] == _g.OWNER for v in verdicts)
    except Exception:  # noqa: BLE001 -- not ready is the closed state
        return False
