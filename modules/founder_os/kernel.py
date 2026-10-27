"""Founder Kernel: a pure fold from journal events to a business-state view and a round plan.

No I/O and no store of its own. The view can only contain what an event in the journal says, so
an inferred fact cannot be promoted by being remembered. Money is out of scope here: amounts and
currencies are validated at the journal boundary and typed economics arrive with F3.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

PROFILE_FIELDS = ("business_model", "revenue_model", "customer_segments", "stage",
                  "products_services", "value_proposition", "objectives", "constraints",
                  "budget", "costs", "margins", "operating_capacity", "funnel", "metrics",
                  "risks")
# Missing-fact order = value of knowing it first; the first four decide which capability applies.
CORE = ("business_model", "revenue_model", "customer_segments", "stage")
SUBJECT_KINDS = frozenset({"observation", "measurement", "hypothesis"})
CLASS_OF = {"verified": "VERIFIED", "observed": "OBSERVED", "inferred": "INFERRED",
            "simulated": "SIMULATED", "hypothesis": "HYPOTHESIS"}
LIVE = frozenset({"VERIFIED", "OBSERVED"})
DEFAULT_TTL_DAYS = 90
MAX_PLAN = 5


def _when(payload: dict, ts: str) -> tuple[datetime, str]:
    raw = payload.get("observed_at")
    basis = "observed_at"
    if not raw:
        raw, basis = ts, "recorded_at"
    parsed = datetime.fromisoformat(raw)
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)), basis


def build_view(events: list[dict], as_of: datetime | None = None,
               ttl_days: int = DEFAULT_TTL_DAYS) -> dict:
    """Return {field: {...}} for every profile field. Unknown stays UNKNOWN."""
    now = as_of or datetime.now(timezone.utc)
    claims: dict[str, list[dict]] = {f: [] for f in PROFILE_FIELDS}
    retired: set[str] = set()
    for e in events:
        p = e.get("payload") or {}
        if p.get("supersedes"):
            retired.add(p["supersedes"])
        subject = p.get("subject")
        if e.get("kind") not in SUBJECT_KINDS or subject not in claims:
            continue
        cls = "HYPOTHESIS" if e["kind"] == "hypothesis" else CLASS_OF.get(p.get("evidence_class"))
        if cls is None:
            continue
        at, basis = _when(p, e["ts"])
        claims[subject].append({"event_id": e["event_id"], "status": cls, "value": p.get("value"),
                                "observed_at": at.isoformat(), "basis": basis,
                                "source_ref": p.get("source_ref"), "_at": at})
    view = {}
    for field, rows in claims.items():
        rows = [r for r in rows if r["event_id"] not in retired]
        if not rows:
            view[field] = {"status": "UNKNOWN",
                           "missing_evidence": f"an observation or measurement with subject={field}"}
            continue
        fresh = [r for r in rows if now - r["_at"] <= timedelta(days=ttl_days)]
        live = [r for r in fresh if r["status"] in LIVE]
        if len({r["value"] for r in live}) > 1:
            view[field] = {"status": "CONTRADICTED",
                           "claims": [_public(r) for r in live],
                           "resolve_with": "an event whose supersedes names the claim to retire"}
            continue
        if not fresh:
            last = _public(max(rows, key=lambda r: r["_at"]))
            view[field] = {**last, "status": "STALE", "last_class": last["status"]}
            continue
        best = max(fresh, key=lambda r: (r["status"] in LIVE, r["_at"]))
        view[field] = _public(best)
    return view


def _public(row: dict) -> dict:
    return {k: v for k, v in row.items() if not k.startswith("_")}


def plan_round(view: dict) -> list[dict]:
    """Deterministic recommendations, at most MAX_PLAN. Recommendations only; nothing is executed."""
    plan: list[dict] = []

    def add(action: str, lens: str, field: str, reason: str) -> None:
        if len(plan) < MAX_PLAN:
            plan.append({"action": action, "lens": lens, "field": field, "reason": reason,
                         "kind": "recommendation"})

    for field in PROFILE_FIELDS:
        if view[field]["status"] == "CONTRADICTED":
            add("reconcile", "Risk", field, "two live claims disagree; decisions on this fact are unsafe")
    for field in CORE:
        if view[field]["status"] == "UNKNOWN":
            add("discover", "Research", field, "core fact unknown; knowing it decides which capability applies")
            break  # one discovery at a time: the highest-value missing fact
    for field in PROFILE_FIELDS:
        if view[field]["status"] == "STALE":
            add("refresh", "Operations", field, "last live evidence is older than the freshness window")
    if all(view[f]["status"] in LIVE for f in CORE):
        for field in ("funnel", "metrics"):
            if view[field]["status"] == "UNKNOWN":
                add("instrument", "Growth", field,
                    "core model known but no measured baseline; a bottleneck cannot be chosen without one")
    return plan
