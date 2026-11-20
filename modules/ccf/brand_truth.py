"""Brand Truth evidence intake (BCAP2-07 / BI-08).

A typed, traceable record of what is known about the brand. Every field is either OBSERVED (carries a
source reference and a retrieval stamp) or STATED (the brief's own claim, attributed to the brief) or
absent. Nothing is invented: a missing field is listed under `unknown`, never filled. External
evidence is not fetched here; it arrives as already-sourced items from the CrawlOS/research owners.
Brand-name trademark clearance is never claimed: `clearance` is always NOT_ASSESSED.
"""
from __future__ import annotations

FIELDS = ("purpose", "audience", "sector", "category_codes", "geography_languages",
          "competitive_space", "positioning", "personality", "price_experience_signals",
          "claims_constraints", "existing_protected_assets")


def intake(brief_id: str, items) -> dict:
    """items: [{field, value, origin: 'observed'|'stated', source?, retrieved_at?}].
    An 'observed' item without source AND retrieved_at is refused into `rejected`, not downgraded
    silently into a fact. Unknown fields are rejected too."""
    facts, rejected = {}, []
    for it in items or []:
        f, o = it.get("field"), it.get("origin")
        if f not in FIELDS:
            rejected.append({"item": it, "why": f"unknown field {f!r}"})
        elif o == "observed" and not (it.get("source") and it.get("retrieved_at")):
            rejected.append({"item": it, "why": "observed evidence needs source and retrieved_at (no fabricated observations)"})
        elif o not in ("observed", "stated"):
            rejected.append({"item": it, "why": f"origin {o!r} must be observed or stated"})
        elif it.get("value") in (None, "", [], {}):
            rejected.append({"item": it, "why": "empty value is absence, not a fact"})
        else:
            facts.setdefault(f, []).append({k: it[k] for k in ("value", "origin", "source", "retrieved_at") if k in it})
    return {"brief_id": brief_id, "facts": facts, "rejected": rejected,
            "unknown": [f for f in FIELDS if f not in facts],
            "clearance": "NOT_ASSESSED"}
