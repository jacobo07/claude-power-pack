"""Five separate business verdicts from one kernel view. No blended score, no money arithmetic.

Each dimension answers its own question from its own facts. Only Growth Readiness depends on other
dimensions, and it says so. A projection or simulation can make a dimension UNPROVEN, never SUPPORTED.
"""
from __future__ import annotations

LIVE = frozenset({"VERIFIED", "OBSERVED"})
WEAK = frozenset({"INFERRED", "HYPOTHESIS", "SIMULATED", "STALE"})
NEEDS = {
    "economic_viability": ("revenue_model", "costs", "margins"),
    "demand_validation": ("customer_segments", "funnel"),
    "operational_readiness": ("operating_capacity", "constraints"),
}
RANK = {"CONTRADICTED": 0, "UNKNOWN": 1, "UNPROVEN": 2, "SUPPORTED": 3}


def _judge(view: dict, fields: tuple) -> dict:
    status = {f: view[f]["status"] for f in fields}
    missing = [f for f, s in status.items() if s == "UNKNOWN"]
    clash = [f for f, s in status.items() if s == "CONTRADICTED"]
    weak = [f for f, s in status.items() if s in WEAK]
    if clash:
        verdict, why = "CONTRADICTED", f"live claims disagree on {clash}"
    elif missing:
        verdict, why = "UNKNOWN", f"no evidence for {missing}"
    elif weak:
        verdict, why = "UNPROVEN", f"only projected, simulated, inferred or stale evidence for {weak}"
    else:
        verdict, why = "SUPPORTED", "every needed fact has live verified or observed evidence"
    return {"verdict": verdict, "needs": list(fields), "why": why,
            "evidence": {f: status[f] for f in fields}}


def assess(view: dict) -> dict:
    out = {name: _judge(view, fields) for name, fields in NEEDS.items()}
    prereq = ("economic_viability", "demand_validation", "operational_readiness")
    weakest = min(prereq, key=lambda n: RANK[out[n]["verdict"]])
    own = _judge(view, ("metrics", "objectives"))
    verdict = own["verdict"] if RANK[own["verdict"]] <= RANK[out[weakest]["verdict"]] else out[weakest]["verdict"]
    out["growth_readiness"] = {
        "verdict": verdict, "needs": own["needs"], "evidence": own["evidence"],
        "depends_on": list(prereq), "limited_by": weakest if out[weakest]["verdict"] != "SUPPORTED" else None,
        "why": f"own facts: {own['why']}; weakest prerequisite is {weakest} ({out[weakest]['verdict']})"}
    groups: dict[str, list] = {"verified": [], "observed": [], "weaker": [], "contradicted": [], "unknown": []}
    for field, row in view.items():
        s = row["status"]
        key = ("verified" if s == "VERIFIED" else "observed" if s == "OBSERVED"
               else "contradicted" if s == "CONTRADICTED" else "unknown" if s == "UNKNOWN" else "weaker")
        groups[key].append(field)
    out["evidence_confidence"] = {"breakdown": groups,
                                  "note": "named fields by class; deliberately not a ratio or a score"}
    return out
