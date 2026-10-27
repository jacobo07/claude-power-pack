"""Business Knowledge Compiler: a lens-scoped context from one business's kernel view plus universal baseline.

Pure composition. Sources are the kernel view of ONE business and the active `business_round` baseline
entries; nothing else is read, so nothing uncited can enter. Competitive intelligence owns no kernel
field and therefore returns a named gap instead of remembered text.
"""
from __future__ import annotations

from . import kernel

LENS_FIELDS = {
    "Strategy": ("business_model", "value_proposition", "objectives", "stage", "constraints"),
    "Growth": ("customer_segments", "funnel", "metrics", "stage"),
    "Sales": ("customer_segments", "funnel", "revenue_model", "value_proposition"),
    "Finance": ("revenue_model", "budget", "costs", "margins"),
    "Product": ("products_services", "value_proposition", "customer_segments"),
    "Operations": ("operating_capacity", "constraints", "costs"),
    "Customer": ("customer_segments", "funnel", "value_proposition"),
    "Competitive": (),
    "Research": kernel.PROFILE_FIELDS,
    "Experimentation": ("metrics", "funnel", "objectives"),
    "Risk": ("risks", "constraints", "budget", "margins"),
    "Knowledge": kernel.PROFILE_FIELDS,
}
# Principles are universal and selected by lens; ids are baseline entry ids, so each stays cited.
LENS_PRINCIPLES = {
    "Finance": ("business_round-amount-travels-with-qualifiers", "business_round-recommendation-is-not-a-fact"),
    "Sales": ("business_round-no-message-to-a-person-unreviewed", "business_round-claim-needs-a-fact"),
    "Growth": ("business_round-claim-needs-a-fact", "business_round-no-message-to-a-person-unreviewed"),
    "Customer": ("business_round-journal-refuses-customer-data", "business_round-no-message-to-a-person-unreviewed"),
    "Experimentation": ("business_round-recommendation-is-not-a-fact", "business_round-claim-needs-a-fact"),
    "Risk": ("business_round-global-flag-never-decides-per-business-effect",
             "business_round-journal-refuses-customer-data"),
    "Knowledge": ("business_round-claim-needs-a-fact", "business_round-journal-refuses-customer-data"),
}
KIND_OF = {"VERIFIED": "verified_fact", "OBSERVED": "observed_fact", "INFERRED": "inferred",
           "HYPOTHESIS": "hypothesis", "SIMULATED": "simulated", "STALE": "stale",
           "CONTRADICTED": "contradicted", "UNKNOWN": "gap"}
MAX_ITEMS = 12
MAX_CHARS = 2600


def lenses() -> list[str]:
    return list(LENS_FIELDS)


def _field_item(field: str, row: dict) -> dict:
    status = row["status"]
    item = {"kind": KIND_OF[status], "scope": "this_business", "field": field, "status": status}
    if status == "UNKNOWN":
        item["text"] = f"{field}: unknown. Needs {row['missing_evidence']}."
        item["provenance"] = None
    elif status == "CONTRADICTED":
        item["text"] = f"{field}: live claims disagree: " + "; ".join(str(c["value"]) for c in row["claims"])
        item["provenance"] = [{"event_id": c["event_id"], "source_ref": c["source_ref"]} for c in row["claims"]]
    else:
        item["text"] = f"{field}: {row['value']}"
        item["provenance"] = [{"event_id": row["event_id"], "source_ref": row["source_ref"]}]
        item["observed_at"] = row["observed_at"]
        item["freshness_basis"] = row["basis"]
    return item


def compile_context(view: dict, lens: str, principles: list[dict], baseline_stamp: str = "") -> dict:
    """Return {lens, items, omitted, chars}. `view` is one business's kernel view; `principles` are
    active family-baseline entries (each already cited). Unknown lens is refused, not guessed."""
    if lens not in LENS_FIELDS:
        raise ValueError(f"unknown lens {lens!r}; one of {lenses()}")
    items: list[dict] = []
    if not LENS_FIELDS[lens]:
        items.append({"kind": "gap", "scope": "this_business", "field": None, "status": "UNKNOWN",
                      "text": f"{lens}: no kernel field holds this; needs dated external observations "
                              "recorded as journal events with a source_ref before it can be used.",
                      "provenance": None})
    for field in LENS_FIELDS[lens]:
        items.append(_field_item(field, view[field]))
    by_id = {p["id"]: p for p in principles}
    for pid in LENS_PRINCIPLES.get(lens, ()):
        if pid in by_id:
            p = by_id[pid]
            items.append({"kind": "principle", "scope": "universal", "field": None, "status": "BASELINE",
                          "text": p["requirement"],
                          "provenance": {"baseline_entry": pid, "origin": p["origin"], "stamp": baseline_stamp}})
    # Contradictions and gaps are the most decision-relevant; keep them first when the cap bites.
    order = {"contradicted": 0, "stale": 1, "gap": 2}
    items.sort(key=lambda i: order.get(i["kind"], 3))
    kept, used = [], 0
    for item in items:
        cost = len(item["text"])
        if len(kept) >= MAX_ITEMS or used + cost > MAX_CHARS:
            continue
        kept.append(item)
        used += cost
    omitted = [i["field"] or i["provenance"]["baseline_entry"] for i in items if i not in kept]
    return {"lens": lens, "items": kept, "omitted": omitted, "chars": used}
