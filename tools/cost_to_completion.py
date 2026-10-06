"""Cost-to-completion: what a claim graph still costs, compiled from CLAIMS, never from phases.

Sibling of tools/route_admission.py (same floor/margin vocabulary): route_admission asks "does this
route fit its envelope?"; this asks "what does the work still to be proven cost?" Pure, deterministic,
no model. Live QA W0 (m-8bbdf725cd52) was planned by phase count at 4M and spent 53.7M; a phase is
not a unit of cost, a claim is.

Input JSON:
  {"claims": [{"id", "class", "status", "est_calls"?}],
   "profiles": {class: {"calls", "ctx_tokens"}}?,   # overrides the priors
   "actuals":  {class: {"calls", "ctx_tokens"}}?,   # measured; beat both priors and profiles
   "worker_floor"?: int, "default_min_calls"?: int, "deopt_factor"?: number}
Classes: satisfied | deterministic | known_transform | bounded_coding | novel | owner_reality | sleeping.
  satisfied, sleeping   cost 0 (a sleeping claim is listed: it is parked, not free of the future)
  deterministic         0 model tokens (a script runs it)
  owner_reality         0 model tokens (only the Owner's reality can close it; listed)
  known_transform / bounded_coding / novel   calls x ctx_tokens, per class profile
Three surfaces, floor <= candidate <= ceiling:
  floor      min calls (default_min_calls, capped by the candidate's calls) x the worker floor
  candidate  sum of est_calls (or the class profile's calls) x ctx_tokens (clamped up to the worker
             floor: every call re-reads at least the first-call context); `with_margin` adds the
             route_admission growth margin
  ceiling    the candidate with every `novel` claim's cost multiplied by the deopt factor
PRIORS and DEFAULT_DEOPT_FACTOR are chosen values, not measured ones; the output names which class
used a prior and which an actual. REFUSED (exit 2): a phase list / phase-average input
(PHASE_MULTIPLIER), no claims (NO_CLAIMS), a malformed claim (BAD_CLAIM).

  cost_to_completion.py --claims CLAIMS.json [--floors F] [--margin 0.2]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import route_admission as ra  # noqa: E402

CLASSES = ("satisfied", "deterministic", "known_transform", "bounded_coding", "novel",
           "owner_reality", "sleeping")
ZERO_CLASSES = ("satisfied", "deterministic", "owner_reality", "sleeping")
MODEL_CLASSES = ("known_transform", "bounded_coding", "novel")
PRIORS = {"known_transform": {"calls": 2, "ctx_tokens": 115_000},
          "bounded_coding": {"calls": 6, "ctx_tokens": 125_000},
          "novel": {"calls": 15, "ctx_tokens": 140_000}}
DEFAULT_DEOPT_FACTOR = 3.0
PHASE_KEYS = ("phases", "phase_count", "phase_average", "phase_average_cost", "avg_phase_cost")


class Refused(Exception):
    def __init__(self, reason: str, detail: str):
        super().__init__(f"{reason}: {detail}")
        self.reason, self.detail = reason, detail


def _pos(field: str, v, allow_zero: bool = False):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0 or (v == 0 and not allow_zero):
        raise Refused("BAD_CLAIM", f"{field} must be a positive number, not {v!r}")
    return v


def compile_cost(doc: dict, floors: dict, *, margin: float = ra.DEFAULT_GROWTH_MARGIN) -> dict:
    """Pure. Raises Refused on a phase-forecast, an empty or malformed claim set."""
    if not isinstance(doc, dict):
        raise Refused("BAD_CLAIM", "input must be a JSON object")
    hit = [k for k in PHASE_KEYS if k in doc]
    if hit:
        raise Refused("PHASE_MULTIPLIER", f"{', '.join(hit)} given: cost is forecast from claims, "
                      "never from a phase count or a phase-average cost")
    claims = doc.get("claims")
    if not isinstance(claims, list) or not claims:
        raise Refused("NO_CLAIMS", "no claims: a claim graph is the only admissible basis")
    worker_floor = int(doc.get("worker_floor") or floors["profiles"][ra.TOP_LEVEL]["floor"])
    min_calls = int(doc.get("default_min_calls") or floors.get("default_min_calls") or 3)
    deopt = float(doc.get("deopt_factor") or DEFAULT_DEOPT_FACTOR)
    if deopt < 1:
        raise Refused("BAD_CLAIM", "deopt_factor must be >= 1")
    prof, source = {}, {}
    for cls in MODEL_CLASSES:
        p, src = dict(PRIORS[cls]), "prior"
        for layer, name in ((doc.get("profiles"), "profile"), (doc.get("actuals"), "actual")):
            o = (layer or {}).get(cls)
            if o:
                p = {"calls": _pos(f"{name}.{cls}.calls", o.get("calls", p["calls"])),
                     "ctx_tokens": _pos(f"{name}.{cls}.ctx_tokens", o.get("ctx_tokens", p["ctx_tokens"]))}
                src = name
        prof[cls], source[cls] = p, src
    counts = {c: 0 for c in CLASSES}
    sleeping, owner, seen = [], [], set()
    calls = cand = ceil = 0
    for i, c in enumerate(claims):
        if not isinstance(c, dict) or not c.get("id") or c.get("class") not in CLASSES:
            raise Refused("BAD_CLAIM", f"claim {i}: needs an id and a class in {', '.join(CLASSES)}")
        if c["id"] in seen:
            raise Refused("BAD_CLAIM", f"duplicate claim id {c['id']!r}")
        seen.add(c["id"])
        cls = c["class"]
        if c.get("status") in ("satisfied", "done"):
            cls = "satisfied"
        elif c.get("status") == "sleeping":
            cls = "sleeping"
        counts[cls] += 1
        if cls == "sleeping":
            sleeping.append(c["id"])
        if cls == "owner_reality":
            owner.append(c["id"])
        if cls in ZERO_CLASSES:
            continue
        n = int(_pos(f"{c['id']}.est_calls", c["est_calls"])) if c.get("est_calls") is not None \
            else int(prof[cls]["calls"])
        ctx = max(int(prof[cls]["ctx_tokens"]), worker_floor)
        cost = n * ctx
        calls += n
        cand += cost
        ceil += math.ceil(cost * deopt) if cls == "novel" else cost
    floor_calls = min(min_calls, calls)
    return {
        "verdict": "COMPILED",
        "floor": {"calls": floor_calls, "tokens": floor_calls * worker_floor},
        "candidate": {"calls": calls, "tokens": cand, "with_margin": ra._with_margin(cand, margin)},
        "ceiling": {"tokens": ceil, "deopt_factor": deopt},
        "counts": counts, "sleeping": sleeping, "owner_reality": owner,
        "profile_source": source, "worker_floor": worker_floor, "margin": margin,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="cost-to-completion from a claim graph")
    ap.add_argument("--claims", required=True)
    ap.add_argument("--floors")
    ap.add_argument("--margin", type=float, default=ra.DEFAULT_GROWTH_MARGIN)
    args = ap.parse_args(argv)
    try:
        doc = json.loads(Path(args.claims).read_text(encoding="utf-8-sig"))
        out = compile_cost(doc, ra.load_floors(args.floors), margin=args.margin)
    except Refused as r:
        print(json.dumps({"verdict": "REFUSED", "reason": r.reason, "detail": r.detail}))
        print(f"REFUSED {r.reason}: {r.detail}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        print(json.dumps({"verdict": "REFUSED", "reason": "BAD_INPUT", "detail": str(exc)}))
        return 2
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
