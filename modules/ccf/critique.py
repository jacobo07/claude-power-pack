"""Independent concept critique (BCAP2-07 / BI-14).

Evidence and judgment are separate record kinds. Evidence carries an observed value and the
instrument that measured it; judgment is an opinion (e.g. an LLM) and is stored as such. A critique
may SUGGEST refinements but can never approve: approval needs a human selection among directions
that qualify. Criteria nobody assessed stay UNASSESSED, never defaulting to pass.
"""
from __future__ import annotations

CRITERIA = ("meaningfulness", "silhouette", "category_fit", "genericity", "spelling",
            "constructability", "emotion_fit", "user_intent")
HUMAN_ACTORS = ("human", "owner")


def build_critique(concept_id: str, items) -> dict:
    """items: list of {criterion, kind: evidence|judgment, value, instrument?, note?}.
    Evidence without an instrument is downgraded to judgment (an unsourced observation is an opinion)."""
    ev, jd, notes = {}, {}, []
    for it in items or []:
        c = it.get("criterion")
        if c not in CRITERIA:
            notes.append(f"unknown criterion {c!r} ignored")
            continue
        if it.get("kind") == "evidence" and it.get("instrument"):
            ev[c] = {"value": it.get("value"), "instrument": it["instrument"]}
        else:
            if it.get("kind") == "evidence":
                notes.append(f"{c}: evidence without instrument demoted to judgment")
            jd[c] = {"value": it.get("value"), "note": it.get("note", "")}
    return {"concept": concept_id, "evidence": ev, "judgment": jd,
            "unassessed": [c for c in CRITERIA if c not in ev and c not in jd],
            "approval": "NOT_APPROVED", "notes": notes}


def qualifies(critique: dict) -> bool:
    """A direction qualifies for human selection only on evidence: no criterion may be unassessed
    and none may be backed by a failing evidence value (value is False)."""
    if critique.get("unassessed"):
        return False
    return all(e.get("value") is not False for e in critique.get("evidence", {}).values())


def approve(critiques, selected_id: str, actor: str) -> dict:
    """Approve one concept. Only a human actor, only among >=2 qualifying distinct directions."""
    if actor not in HUMAN_ACTORS:
        return {"approved": False, "reason": f"actor {actor!r} cannot approve; critique only suggests"}
    ok = [c["concept"] for c in critiques if qualifies(c)]
    if len(ok) < 2:
        return {"approved": False, "reason": f"{len(ok)} qualifying direction(s); a human choice needs >=2"}
    if selected_id not in ok:
        return {"approved": False, "reason": f"{selected_id!r} does not qualify"}
    return {"approved": True, "concept": selected_id, "by": actor, "chosen_among": ok}
