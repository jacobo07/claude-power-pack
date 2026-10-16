"""Planning Necessity Gate: how much planning a work unit is allowed before it executes.

    python tools/planning_gate.py --unit <unit.json> [--repo <dir>]

Measured 2026-10-16 (Two Builders M2, m-f9290d78278f): /gsd-autonomous ran planner -> checker -> replanner for
a Cantina probe whose work class (TB-DISC-PROBE) had three executed precedents (P22-P24). 224 model turns,
29.9M processed tokens, five plans, zero execution. Nothing asked whether planning was needed at all.

A unit is JSON:
  {"work_class": "TB-DISC-PROBE", "capsule": ".planning/capsules/TB-DISC-PROBE.json" | null,
   "unknowns": ["is a loose .scp honoured", ...],      # the questions planning would have to answer
   "reversible": true, "blast_radius": "low|medium|high", "closes": [...], "claims": [...]}
A capsule is JSON in the repo: {"work_class", "max_unknowns", "planning_budget_tokens": {mode: n},
   "closed_obligations": [{"id", "proof"}], "invalidators": [{"path", "sha256"}]}

Decision (first match wins):
  missing reversible/blast_radius             -> OWNER       (unknown risk is not low risk)
  not reversible, or blast_radius high        -> FULL_PLAN   (planning earns its cost here)
  capsule named but unreadable or invalidated -> BOUNDED_PLAN (precedent not reusable; say which invalidator)
  no capsule                                  -> BOUNDED_PLAN
  capsule valid, no unknowns                  -> DIRECT_TEMPLATE
  capsule valid, unknowns <= max_unknowns     -> DELTA_PLAN  (a prereg that answers the unknowns; no planner agent)
  capsule valid, more unknowns                -> BOUNDED_PLAN
A claim that names a closed obligation is refused (the residual must not reopen proof without an invalidator).
The planning authority is the capsule's budget for the chosen mode (absent = null, never unlimited).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

MODES = ("DIRECT_TEMPLATE", "DELTA_PLAN", "BOUNDED_PLAN", "FULL_PLAN", "OWNER")


def _sha256(p: Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None


def load_capsule(repo: Path, rel: str) -> tuple[dict | None, list[str]]:
    """(capsule, invalidation reasons). Unreadable = invalidated, never valid."""
    try:
        cap = json.loads((repo / rel).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return None, [f"capsule unreadable: {type(e).__name__}"]
    why = [f"{iv['path']} changed" for iv in cap.get("invalidators") or []
           if _sha256(repo / iv["path"]) != iv["sha256"]]
    if not cap.get("invalidators"):
        why.append("capsule names no invalidators (validity cannot be checked)")
    return cap, why


def decide(unit: dict, repo: Path) -> dict:
    out = {"work_class": unit.get("work_class"), "unknowns": list(unit.get("unknowns") or []),
           "refused_claims": [], "invalidated_by": []}
    cap = None
    if unit.get("capsule"):
        cap, out["invalidated_by"] = load_capsule(repo, unit["capsule"])
        closed = {c["id"]: c.get("proof") for c in (cap or {}).get("closed_obligations") or []}
        out["refused_claims"] = [{"claim": c, "closed_by": closed[c]} for c in unit.get("claims") or [] if c in closed]
    if "reversible" not in unit or unit.get("blast_radius") not in ("low", "medium", "high"):
        mode, why = "OWNER", "reversibility or blast radius not stated"
    elif not unit["reversible"] or unit["blast_radius"] == "high":
        mode, why = "FULL_PLAN", "irreversible or high blast radius"
    elif not unit.get("capsule"):
        mode, why = "BOUNDED_PLAN", "no precedent capsule for this work class"
    elif cap is None or out["invalidated_by"]:
        mode, why = "BOUNDED_PLAN", "precedent not reusable: " + "; ".join(out["invalidated_by"])
    elif cap.get("work_class") != unit.get("work_class"):
        mode, why = "BOUNDED_PLAN", f"capsule is {cap.get('work_class')}, unit is {unit.get('work_class')}"
    elif not out["unknowns"]:
        mode, why = "DIRECT_TEMPLATE", "valid precedent, no open unknowns"
    elif len(out["unknowns"]) <= int(cap.get("max_unknowns") or 0):
        mode, why = "DELTA_PLAN", f"valid precedent, {len(out['unknowns'])} unknown(s) answered by the prereg"
    else:
        mode, why = "BOUNDED_PLAN", f"{len(out['unknowns'])} unknowns exceed the capsule's {cap.get('max_unknowns')}"
    out.update(mode=mode, why=why, planner_agent_admitted=mode in ("BOUNDED_PLAN", "FULL_PLAN"),
               planning_authority_tokens=((cap or {}).get("planning_budget_tokens") or {}).get(mode))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--unit", required=True)
    ap.add_argument("--repo", default=".")
    a = ap.parse_args(argv)
    d = decide(json.loads(Path(a.unit).read_text(encoding="utf-8")), Path(a.repo))
    print(json.dumps(d, indent=1))
    return 2 if d["refused_claims"] else 0


if __name__ == "__main__":
    sys.exit(main())
