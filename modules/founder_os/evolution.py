"""Evolution Engine: opportunity lifecycle and bottleneck selection, folded from the journal.

No second backlog: an opportunity is a journal event, its state is derived, and a state change is a
`decision` event that must pass `check_write` under the journal lock. Gates are free text; this module
verifies linkage and evidence class and never judges whether a gate was met.
"""
from __future__ import annotations

from . import kernel

LIVE_CAP = 5
CONFIDENCE = frozenset({"low", "medium", "high"})
STATE_CHANGES = frozenset({"adopt", "succeed", "abandon", "merge"})
LIVE_STATES = frozenset({"PROPOSED", "ACTIVE"})
NEXT = {"adopt": ("PROPOSED", "ACTIVE"), "succeed": ("ACTIVE", "DONE"),
        "abandon": (None, "ABANDONED"), "merge": (None, "ABANDONED")}


def states(events: list[dict]) -> dict[str, dict]:
    """{opportunity event_id: {state, summary, bottleneck, confidence}} folded from the journal."""
    opps: dict[str, dict] = {}
    for e in events:
        p = e.get("payload") or {}
        if e.get("kind") == "opportunity":
            opps[e["event_id"]] = {"state": "PROPOSED", "summary": p.get("summary"),
                                   "confidence": p.get("confidence", "unknown"), "history": []}
        elif e.get("kind") == "decision" and p.get("state_change") in STATE_CHANGES:
            target = opps.get(p.get("opportunity_ref"))
            if target is None:
                continue
            _, new = NEXT[p["state_change"]]
            target["state"] = new
            target["history"].append({"event_id": e["event_id"], "change": p["state_change"]})
    return opps


def live_count(events: list[dict]) -> int:
    return sum(1 for o in states(events).values() if o["state"] in LIVE_STATES)


def check_write(events: list[dict], kind: str, payload: dict) -> None:
    """Raise ValueError if this event would break the opportunity lifecycle. Called under the journal lock."""
    if "confidence" in payload and payload["confidence"] not in CONFIDENCE:
        raise ValueError(f"confidence must be one of {sorted(CONFIDENCE)} or absent (unknown)")
    for field in ("state_change", "proof_ref", "merged_into"):
        if field in payload and kind != "decision":
            raise ValueError(f"{field} is only valid on a decision event")
    if kind == "opportunity":
        if live_count(events) >= LIVE_CAP:
            raise ValueError(f"live opportunity cap reached ({LIVE_CAP}); adopt, abandon or merge one first")
        return
    change = payload.get("state_change")
    if kind != "decision" or change is None:
        return
    if change not in STATE_CHANGES:
        raise ValueError(f"state_change must be one of {sorted(STATE_CHANGES)}")
    opps = states(events)
    ref = payload.get("opportunity_ref")
    if ref not in opps:
        raise ValueError("state_change needs opportunity_ref naming an existing opportunity")
    current = opps[ref]["state"]
    needs, _ = NEXT[change]
    if current not in LIVE_STATES:
        raise ValueError(f"opportunity is already {current}; a terminal opportunity cannot move again")
    if needs and current != needs:
        raise ValueError(f"{change} requires the opportunity to be {needs}, not {current}")
    if change == "succeed":
        proof = next((e for e in events if e["event_id"] == payload.get("proof_ref")), None)
        pp = (proof or {}).get("payload", {})
        if not (proof and proof.get("kind") == "measurement" and pp.get("opportunity_ref") == ref):
            raise ValueError("succeed needs proof_ref naming a measurement event for this opportunity")
        if pp.get("evidence_class") != "verified":
            raise ValueError("succeed needs a verified measurement; simulated or hypothesis does not count")
    if change == "merge":
        target = opps.get(payload.get("merged_into"))
        if target is None or payload.get("merged_into") == ref or target["state"] not in LIVE_STATES:
            raise ValueError("merge needs merged_into naming a different live opportunity")


def bottleneck(view: dict) -> dict:
    """The bottleneck only when a live observation says so; otherwise the best uncertainty reducer."""
    row = view["bottleneck"]
    if row["status"] in kernel.LIVE:
        return {"bottleneck": row["value"], "status": row["status"], "provenance": row["source_ref"],
                "basis": "recorded evidence"}
    plan = kernel.plan_round(view)
    note = {"INFERRED": "an inferred bottleneck is a hypothesis, not a selection",
            "HYPOTHESIS": "a hypothesised bottleneck is not a selection",
            "SIMULATED": "a simulated bottleneck is not a selection",
            "STALE": "the last evidence is stale; refresh before relying on it",
            "CONTRADICTED": "live claims disagree; reconcile before choosing",
            "UNKNOWN": "no evidence names a bottleneck"}[row["status"]]
    return {"bottleneck": None, "status": row["status"], "reason": note,
            "next": plan[0] if plan else {"action": "record a bottleneck observation with its source",
                                          "lens": "Growth", "field": "bottleneck", "kind": "recommendation"}}
