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

Semantic stage (A5-U3, optional): a claim may carry `obligations` [{id, satisfier, family?, observation?,
proof?, invalidators?[], alternatives?[]}]. When present they REPLACE the claim's own class cost (a satisfied or
sleeping claim still costs 0). Satisfier -> class:
  STATE / OTHER_GOAL, PROOF with proof_valid   NO_WORK (needs non-empty invalidators, else REFUSED MISSING_INVALIDATOR;
                                               an invalidator {"id","stale":true} or {"valid":false} voids the reuse:
                                               the obligation is recomputed, priced known_transform, listed in `stale`)
  TRANSFORM / TOOL without family              NO_COMPUTE (0 model tokens)
  TRANSFORM / TOOL with family                 FAMILY: first instance bounded_coding (novel if "novel":true) and it needs
                                               a `proof` (else REFUSED FAMILY_NO_PROOF); the rest known_transform
  PROOF (not yet valid)                        SHARED_PROOF: priced once per distinct `proof` id (known_transform)
  OBSERVATION                                  SHARED_OBS: priced once per distinct `observation` id (known_transform)
  MODEL                                        novel decision, priced once per obligation (class `model_class`, default novel)
  OWNER                                        0 tokens, listed (an owner decision)
Output `semantic`: counts, irreducible lower bound (distinct novel decisions + distinct observations + assurance
judgments + owner decisions), overhead multiplier input (doc `historical_calls` / lower bound, null when unknown),
per-class interrupt budget (priced calls per class), alternatives per obligation. `HISTORICAL_PROFILE` is true unless
every model class is priced from a `profiles` override; a doc `label` of "new architecture" with historical profiles is
REFUSED HISTORICAL_PROFILE.

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
SATISFIERS = ("STATE", "PROOF", "TRANSFORM", "OTHER_GOAL", "OBSERVATION", "TOOL", "MODEL", "OWNER")
PHASE_KEYS = ("phases", "phase_count", "phase_average", "phase_average_cost", "avg_phase_cost")


class Refused(Exception):
    def __init__(self, reason: str, detail: str):
        super().__init__(f"{reason}: {detail}")
        self.reason, self.detail = reason, detail


def _pos(field: str, v, allow_zero: bool = False):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0 or (v == 0 and not allow_zero):
        raise Refused("BAD_CLAIM", f"{field} must be a positive number, not {v!r}")
    return v


def _inv_state(o: dict, where: str) -> str:
    """'valid' | 'stale'; refuses when a reused obligation names no invalidator."""
    inv = o.get("invalidators")
    if not isinstance(inv, list) or not inv or any(not i for i in inv):
        raise Refused("MISSING_INVALIDATOR", f"{where}: reused without invalidators; not reusable")
    for i in inv:
        if isinstance(i, dict) and (i.get("stale") or i.get("valid") is False):
            return "stale"
    return "valid"


def _semantic_claim(c: dict, st: dict, price) -> tuple[int, int, int]:
    """Price one claim's obligations against shared state `st`. Returns (calls, cost, ceiling)."""
    calls = cost = ceil = 0
    obs = c["obligations"]
    if not isinstance(obs, list) or not obs:
        raise Refused("BAD_CLAIM", f"{c['id']}: obligations must be a non-empty list")
    for o in obs:
        if not isinstance(o, dict) or not o.get("id") or o.get("satisfier") not in SATISFIERS:
            raise Refused("BAD_CLAIM", f"{c['id']}: obligation needs an id and a satisfier in {', '.join(SATISFIERS)}")
        oid, sat = f"{c['id']}/{o['id']}", o["satisfier"]
        if oid in st["ids"]:
            raise Refused("BAD_CLAIM", f"duplicate obligation id {oid!r}")
        st["ids"].add(oid)
        alts = o.get("alternatives", [])
        if not isinstance(alts, list) or any(a not in SATISFIERS for a in alts):
            raise Refused("BAD_CLAIM", f"{oid}: alternatives must be satisfiers")
        cls, priced = None, None          # priced: model class charged, or None
        if sat in ("STATE", "OTHER_GOAL") or (sat == "PROOF" and o.get("proof_valid")):
            if _inv_state(o, oid) == "valid":
                cls = "NO_WORK"
            else:
                cls, priced = "STALE_RECOMPUTE", "known_transform"
                st["stale"].append(oid)
        elif sat == "PROOF":
            if not o.get("proof"):
                raise Refused("BAD_CLAIM", f"{oid}: PROOF needs a proof id")
            cls = "SHARED_PROOF"
            if o["proof"] not in st["proofs"]:
                st["proofs"].add(o["proof"])
                priced = "known_transform"
                st["assurance"] += 1
        elif sat == "OBSERVATION":
            if not o.get("observation"):
                raise Refused("BAD_CLAIM", f"{oid}: OBSERVATION needs an observation id")
            cls = "SHARED_OBS"
            if o["observation"] not in st["obs"]:
                st["obs"].add(o["observation"])
                priced = "known_transform"
        elif sat in ("TRANSFORM", "TOOL"):
            fam = o.get("family")
            if not fam:
                cls = "NO_COMPUTE"
            else:
                cls = "FAMILY"
                if fam not in st["families"]:
                    if not o.get("proof"):
                        raise Refused("FAMILY_NO_PROOF", f"{oid}: first instance of family {fam!r} has no proof")
                    st["families"].add(fam)
                    priced = "novel" if o.get("novel") else "bounded_coding"
                    st["decisions"] += 1
                else:
                    priced = "known_transform"
        elif sat == "MODEL":
            mc = o.get("model_class", "novel")
            if mc not in MODEL_CLASSES:
                raise Refused("BAD_CLAIM", f"{oid}: model_class must be one of {', '.join(MODEL_CLASSES)}")
            cls, priced = "MODEL", mc
            st["decisions"] += 1
        else:  # OWNER
            cls = "OWNER"
            st["owner"].append(oid)
        if priced:
            n, ctx = price(priced)
            calls += n
            cost += n * ctx
            ceil += math.ceil(n * ctx * st["deopt"]) if priced == "novel" else n * ctx
            st["budget"][priced] = st["budget"].get(priced, 0) + n
        st["counts"][cls] = st["counts"].get(cls, 0) + 1
        st["alts"].append({"obligation": oid, "satisfier": sat, "class": cls, "alternatives": alts})
    return calls, cost, ceil


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
    st = {"ids": set(), "proofs": set(), "obs": set(), "families": set(), "stale": [], "owner": [], "alts": [],
          "counts": {}, "budget": {}, "assurance": 0, "decisions": 0, "deopt": deopt}
    any_semantic = False

    def price(cls):
        return int(prof[cls]["calls"]), max(int(prof[cls]["ctx_tokens"]), worker_floor)
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
        if c.get("obligations") is not None:
            any_semantic = True
            k, cs, ce = _semantic_claim(c, st, price)
            calls += k
            cand += cs
            ceil += ce
            continue
        n = int(_pos(f"{c['id']}.est_calls", c["est_calls"])) if c.get("est_calls") is not None \
            else int(prof[cls]["calls"])
        ctx = max(int(prof[cls]["ctx_tokens"]), worker_floor)
        cost = n * ctx
        calls += n
        cand += cost
        ceil += math.ceil(cost * deopt) if cls == "novel" else cost
    floor_calls = min(min_calls, calls)
    historical = not all(source[k] == "profile" for k in MODEL_CLASSES)
    label = doc.get("label")
    if isinstance(label, str) and label.strip().lower().replace("_", " ") == "new architecture" and historical:
        raise Refused("HISTORICAL_PROFILE", "forecast labelled 'new architecture' but model classes are priced from "
                      f"historical profiles ({source}); pass a `profiles` override for every model class")
    out = {
        "verdict": "COMPILED",
        "floor": {"calls": floor_calls, "tokens": floor_calls * worker_floor},
        "candidate": {"calls": calls, "tokens": cand, "with_margin": ra._with_margin(cand, margin)},
        "ceiling": {"tokens": ceil, "deopt_factor": deopt},
        "counts": counts, "sleeping": sleeping, "owner_reality": owner,
        "profile_source": source, "worker_floor": worker_floor, "margin": margin,
    }
    if label is not None or any_semantic:
        out["HISTORICAL_PROFILE"] = historical
    if any_semantic:
        lb = st["decisions"] + len(st["obs"]) + st["assurance"] + len(st["owner"])
        hist = doc.get("historical_calls")
        if hist is not None:
            _pos("historical_calls", hist)
        out["semantic"] = {
            "obligation_counts": st["counts"], "stale": st["stale"], "owner_decisions": st["owner"],
            "irreducible_lower_bound": {"total": lb, "novel_decisions": st["decisions"],
                                        "observations": len(st["obs"]), "assurance_judgments": st["assurance"],
                                        "owner_decisions": len(st["owner"]), "kind": "estimate"},
            "overhead_multiplier_input": (hist / lb) if hist is not None and lb else None,
            "interrupt_budget": st["budget"], "alternatives": st["alts"],
        }
    return out


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
