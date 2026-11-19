"""Multi-territory concept check (BCAP2-07 / BI-09).

Pure function: does a concept set offer at least three genuinely different conceptual directions?
A direction is distinct only if BOTH its `mechanism` and its `brand_fact` differ from every other
direction's; the same icon in other colours is one direction. Fewer than three is allowed only through
an explicit, reasoned narrow-brief exception, which is returned as its own verdict (never as PASS).
A typography-only or monogram route is a legitimate mechanism and counts as a direction.
"""
from __future__ import annotations

MIN_TERRITORIES = 3
ROUTES_WITHOUT_ICON = ("typography-only", "monogram")


def _norm(v) -> str:
    return " ".join(str(v or "").lower().split())


def check_territories(concepts, narrow_brief=None) -> dict:
    """Return {verdict, distinct, reasons}. verdict: PASS | NARROW_BRIEF_EXCEPTION | FAIL.
    `narrow_brief` is None or {"reason": non-empty str}; a bare True or blank reason is refused."""
    reasons, kept, seen_m, seen_f, seen_i = [], [], set(), set(), set()
    for c in concepts or []:
        cid = c.get("id", "?")
        m, f, i = _norm(c.get("mechanism")), _norm(c.get("brand_fact")), _norm(c.get("icon"))
        if not m or not f:
            reasons.append(f"{cid}: missing mechanism or brand_fact (unmeasured, not counted)")
            continue
        if m in seen_m:
            reasons.append(f"{cid}: mechanism '{m}' repeats an earlier concept")
            continue
        if f in seen_f:
            reasons.append(f"{cid}: brand_fact repeats an earlier concept")
            continue
        if i and i in seen_i and m not in ROUTES_WITHOUT_ICON:
            reasons.append(f"{cid}: same icon as an earlier concept (recolour, not a territory)")
            continue
        seen_m.add(m)
        seen_f.add(f)
        seen_i.add(i)
        kept.append(cid)
    if len(kept) >= MIN_TERRITORIES:
        return {"verdict": "PASS", "distinct": kept, "reasons": reasons}
    reason = narrow_brief.get("reason") if isinstance(narrow_brief, dict) else None
    if isinstance(reason, str) and reason.strip():
        return {"verdict": "NARROW_BRIEF_EXCEPTION", "distinct": kept, "reasons": reasons,
                "exception_reason": reason.strip()}
    reasons.append(f"only {len(kept)} distinct territories; need {MIN_TERRITORIES} or a reasoned narrow-brief exception")
    return {"verdict": "FAIL", "distinct": kept, "reasons": reasons}
