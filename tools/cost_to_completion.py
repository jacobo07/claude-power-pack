"""Cost-to-completion: what a claim graph still costs, compiled from CLAIMS, never from phases.

Sibling of tools/route_admission.py (same floor/margin vocabulary): route_admission asks "does this
route fit its envelope?"; this asks "what does the work still to be proven cost?" Pure, deterministic,
no model. Live QA W0 (m-8bbdf725cd52) was planned by phase count at 4M and spent 53.7M; a phase is
not a unit of cost, a claim is.

Input JSON:
  {"claims": [{"id", "class", "status", "est_calls"?, "shared_with"?, "unit"?, "gates"?, "derived_from"?}],
   "profiles": {class: {"calls", "ctx_tokens"}}?,   # overrides the priors
   "actuals":  {class|unit: {"calls", "ctx_tokens"}}?,   # measured; beat both priors and profiles
   "units": [{"id", "est_calls", "reserve_calls", "profile", "model_prior", "ctx_tokens"}]?,
   "gates": [{"id"}]?, "unmeasured_allowance"?: number, "envelope"?: {"target", "calls"},
   "worker_floor"?: int, "default_min_calls"?: int, "deopt_factor"?: number}
Classes: satisfied | deterministic | known_transform | bounded_coding | novel | visual | owner_reality | sleeping.
  satisfied, sleeping   cost 0 (a sleeping claim is listed apart: parked, not free of the future, and
                        outside the active frontier and its cost)
  deterministic         0 model tokens (a script runs it)
  owner_reality         0 model tokens (only the Owner's reality can close it; listed)
  known_transform / bounded_coding / novel / visual   calls x ctx_tokens, per class profile
  `shared_with: <claim id>` (a model-class claim) costs 0 marginal calls: the referenced claim's work
  closes it. The id must exist (else BAD_CLAIM).
Three surfaces, floor <= candidate <= ceiling:
  floor      min calls (default_min_calls, capped by the candidate's calls) x the worker floor
  candidate  sum of est_calls (or the class profile's calls) x ctx_tokens (clamped up to the worker
             floor: every call re-reads at least the first-call context); `with_margin` adds the
             route_admission growth margin
  ceiling    the candidate with every `novel` / `visual` claim's cost multiplied by the deopt factor
UNITS path (when `units` is present, cost comes from units, not per-claim priors):
  candidate = sum(est_calls x max(ctx_tokens, floor of the unit's route-floors profile)), active units only
  ceiling   = candidate + sum(reserve_calls x ctx) + unmeasured_allowance x candidate (default 1.0; 0 once
              `actuals` cover every active model unit) + the deopt extra of units holding a novel/visual claim
Clean counts: o_total = o_zero + o_shared + o_irreducible; o_semantic_consumers = o_shared + o_irreducible.
Scope coverage (when the doc has `gates`): every gate referenced by >= 1 claim (UNCOVERED_GATE) and every
claim has `gates` or `derived_from` (ORPHAN_CLAIM). PRIORS and DEFAULT_DEOPT_FACTOR are chosen values, not
measured ones. REFUSED (exit 2): PHASE_MULTIPLIER, NO_CLAIMS, BAD_CLAIM, UNCOVERED_GATE, ORPHAN_CLAIM.

  cost_to_completion.py --claims CLAIMS.json [--floors F] [--margin 0.2] [--route [--remaining N]]
--route emits a route_admission route from the units and returns route_admission.admit's verdict: the
mission verdict IS the route's verdict (exit 0 only on ADMISSIBLE, 3 otherwise).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import route_admission as ra  # noqa: E402

CLASSES = ("satisfied", "deterministic", "known_transform", "bounded_coding", "novel", "visual",
           "owner_reality", "sleeping")
ZERO_CLASSES = ("satisfied", "deterministic", "owner_reality", "sleeping")
MODEL_CLASSES = ("known_transform", "bounded_coding", "novel", "visual")
DEOPT_CLASSES = ("novel", "visual")
PRIORS = {"known_transform": {"calls": 2, "ctx_tokens": 115_000},
          "bounded_coding": {"calls": 6, "ctx_tokens": 125_000},
          "novel": {"calls": 15, "ctx_tokens": 140_000},
          "visual": {"calls": 4, "ctx_tokens": 150_000}}
DEFAULT_DEOPT_FACTOR = 3.0
DEFAULT_UNMEASURED_ALLOWANCE = 1.0
PHASE_KEYS = ("phases", "phase_count", "phase_average", "phase_average_cost", "avg_phase_cost")
# Structural call model (canary T, 2026-10-06): a worker's calls are its shape, not a guess.
# orient (read packet + repo state), explore (batched reads), ceil(files / files_per_call) writes,
# runs (each distinct verification command), repairs (fix edits after a red run), commit, report (the
# final tool-less message, which every worker sends and est_calls never counted). extra_ctx is context a
# unit carries from its first call (a large packet). explore_ctx is context the explore calls READ beyond
# an ordinary text exploration (images, large dumps): split evenly over the explore calls and carried
# from the call after each one. ctx_start_over_floor already holds a typical text exploration's return.
WORK_KEYS = ("orient", "explore", "files", "runs", "repairs", "commit", "report", "extra_ctx", "explore_ctx")
CAL_KEYS = ("files_per_call", "ctx_start_over_floor", "ctx_growth_per_call", "output_per_call")


def work_cost(work: dict, cal: dict, floor: int) -> tuple[int, int]:
    """(calls, processed tokens) for a unit's `work` under a measured `calibration`.

    Context at call i (0-based) = floor + ctx_start_over_floor + extra_ctx + growth x i
    + explore_ctx x (explore calls already answered before call i) / explore; every call also emits
    output_per_call. Processed = sum over calls of context + output (what the census measures)."""
    fpc = float(cal["files_per_call"])
    n = int(sum(int(work.get(k, 0)) for k in ("orient", "explore", "runs", "repairs", "commit", "report"))
            + math.ceil(float(work.get("files", 0)) / fpc))
    if n <= 0:
        raise Refused("BAD_CLAIM", "work describes zero calls")
    c0 = floor + int(cal["ctx_start_over_floor"]) + int(work.get("extra_ctx", 0))
    g, out = int(cal["ctx_growth_per_call"]), int(cal["output_per_call"])
    orient, explore, ex = int(work.get("orient", 0)), int(work.get("explore", 0)), int(work.get("explore_ctx", 0))
    carried = sum(ex * min(max(i - orient, 0), explore) // explore for i in range(n)) if explore and ex else 0
    return n, n * c0 + g * n * (n - 1) // 2 + out * n + carried


class Refused(Exception):
    def __init__(self, reason: str, detail: str):
        super().__init__(f"{reason}: {detail}")
        self.reason, self.detail = reason, detail


def _pos(field: str, v, allow_zero: bool = False):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0 or (v == 0 and not allow_zero):
        raise Refused("BAD_CLAIM", f"{field} must be a positive number, not {v!r}")
    return v


def _eff(c: dict) -> str:
    if c.get("status") in ("satisfied", "done"):
        return "satisfied"
    if c.get("status") == "sleeping":
        return "sleeping"
    return c["class"]


def check_scope(doc: dict, claims: list) -> None:
    """Two-way scope coverage; pure. D3 (tools/cep_gen2.py check_obligations) is the convergence target:
    it owns obligation ledgers with a different shape (id/source/terminal), so this stays local until a
    claim graph and an obligation ledger share one schema. Raises Refused; no-op without `gates`."""
    gates = doc.get("gates")
    if gates is None:
        return
    if not isinstance(gates, list):
        raise Refused("BAD_CLAIM", "gates must be a list")
    gids = []
    for g in gates:
        gid = g.get("id") if isinstance(g, dict) else g
        if not gid or not isinstance(gid, str):
            raise Refused("BAD_CLAIM", f"gate needs a string id, not {g!r}")
        gids.append(gid)
    referenced = set()
    for c in claims:
        cg = c.get("gates")
        if cg is not None and not (isinstance(cg, list) and all(isinstance(x, str) for x in cg)):
            raise Refused("BAD_CLAIM", f"claim {c['id']!r}: gates must be a list of gate ids")
        for x in cg or []:
            if x not in gids:
                raise Refused("BAD_CLAIM", f"claim {c['id']!r} references unknown gate {x!r}")
            referenced.add(x)
        if not cg and not c.get("derived_from"):
            raise Refused("ORPHAN_CLAIM", f"claim {c['id']!r} has neither gates nor derived_from")
    missing = [g for g in gids if g not in referenced]
    if missing:
        raise Refused("UNCOVERED_GATE", f"no claim references gate(s) {', '.join(missing)}")


def _unit_rows(doc: dict, claims: list, effs: list, floors: dict, deopt: float):
    units = doc.get("units")
    if units is None:
        if any(c.get("unit") for c in claims):
            raise Refused("BAD_CLAIM", "a claim names a unit but the doc has no units")
        return None
    if not isinstance(units, list) or not units:
        raise Refused("BAD_CLAIM", "units must be a non-empty list")
    profiles = floors["profiles"]
    by_id: dict = {}
    for i, u in enumerate(units):
        if not isinstance(u, dict) or not u.get("id") or not isinstance(u["id"], str):
            raise Refused("BAD_CLAIM", f"unit {i}: needs a string id")
        if u["id"] in by_id:
            raise Refused("BAD_CLAIM", f"duplicate unit id {u['id']!r}")
        pf = (profiles.get(u.get("profile")) or {}).get("floor")
        if not isinstance(pf, int) or pf <= 0:
            raise Refused("BAD_CLAIM", f"unit {u['id']!r}: profile {u.get('profile')!r} has no measured floor")
        n = int(_pos(f"{u['id']}.est_calls", u.get("est_calls")))
        r = int(_pos(f"{u['id']}.reserve_calls", u.get("reserve_calls", 0), allow_zero=True))
        ctx = int(_pos(f"{u['id']}.ctx_tokens", u.get("ctx_tokens")))
        work = u.get("work")
        if work is not None:
            if not isinstance(work, dict) or not work:
                raise Refused("BAD_CLAIM", f"unit {u['id']!r}: work must be a non-empty object")
            bad = sorted(set(work) - set(WORK_KEYS))
            if bad:
                raise Refused("BAD_CLAIM", f"unit {u['id']!r}: unknown work keys {bad} (allowed: {', '.join(WORK_KEYS)})")
            work = {k: _pos(f"{u['id']}.work.{k}", v, allow_zero=True) for k, v in work.items()}
        by_id[u["id"]] = {"id": u["id"], "profile": u["profile"], "model_prior": u.get("model_prior"),
                          "est_calls": n, "reserve_calls": r, "ctx_tokens": ctx, "profile_floor": pf,
                          "order": u.get("order", i), "claims": [], "model": False, "deopt": False,
                          "work": work}
    for c, eff in zip(claims, effs):
        uid = c.get("unit")
        if uid is None:
            if eff in MODEL_CLASSES:
                raise Refused("BAD_CLAIM", f"model-class claim {c['id']!r} has no unit")
            continue
        if uid not in by_id:
            raise Refused("BAD_CLAIM", f"claim {c['id']!r} names unknown unit {uid!r}")
        row = by_id[uid]
        row["claims"].append(c["id"])
        if eff in MODEL_CLASSES:
            row["model"] = True
        if eff in DEOPT_CLASSES:
            row["deopt"] = True
    for row in by_id.values():
        if not row["claims"]:
            raise Refused("BAD_CLAIM", f"unit {row['id']!r} has no claims")
    return sorted(by_id.values(), key=lambda r: (r["order"], r["id"]))


def compile_cost(doc: dict, floors: dict, *, margin: float = ra.DEFAULT_GROWTH_MARGIN) -> dict:
    """Pure. Raises Refused on a phase-forecast, an empty or malformed claim set, or a scope gap."""
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
    counts["shared"] = 0
    sleeping, owner, ids, effs = [], [], set(), []
    for i, c in enumerate(claims):
        if not isinstance(c, dict) or not c.get("id") or c.get("class") not in CLASSES:
            raise Refused("BAD_CLAIM", f"claim {i}: needs an id and a class in {', '.join(CLASSES)}")
        if c["id"] in ids:
            raise Refused("BAD_CLAIM", f"duplicate claim id {c['id']!r}")
        ids.add(c["id"])
        effs.append(_eff(c))
    for c in claims:
        sw = c.get("shared_with")
        if sw is not None and (not isinstance(sw, str) or sw not in ids or sw == c["id"]):
            raise Refused("BAD_CLAIM", f"claim {c['id']!r}: shared_with {sw!r} is not another existing claim")
    check_scope(doc, claims)
    rows = _unit_rows(doc, claims, effs, floors, deopt)
    shared_flags = []
    for c, eff in zip(claims, effs):
        shared = bool(c.get("shared_with")) and eff in MODEL_CLASSES
        shared_flags.append(shared)
        counts["shared" if shared else eff] += 1
        if eff == "sleeping":
            sleeping.append(c["id"])
        if eff == "owner_reality":
            owner.append(c["id"])
    o_zero = sum(counts[k] for k in ZERO_CLASSES)
    o_shared = counts["shared"]
    o_irreducible = sum(counts[k] for k in MODEL_CLASSES)
    clean = {"o_total": len(claims), "o_zero": o_zero, "o_shared": o_shared,
             "o_irreducible": o_irreducible, "o_semantic_consumers": o_shared + o_irreducible}
    calls = cand = ceil = reserve_tokens = reserve_calls = 0
    allowance = None
    active_rows: list = []
    if rows is None:
        for c, eff, shared in zip(claims, effs, shared_flags):
            if eff in ZERO_CLASSES or shared:
                continue
            n = int(_pos(f"{c['id']}.est_calls", c["est_calls"])) if c.get("est_calls") is not None \
                else int(prof[eff]["calls"])
            ctx = max(int(prof[eff]["ctx_tokens"]), worker_floor)
            cost = n * ctx
            calls += n
            cand += cost
            ceil += math.ceil(cost * deopt) if eff in DEOPT_CLASSES else cost
    else:
        actuals = doc.get("actuals") or {}
        active = [r for r in rows if r["model"]]
        for r in active:
            a = actuals.get(r["id"])
            n, ctx = r["est_calls"], r["ctx_tokens"]
            if a:
                n = int(_pos(f"actual.{r['id']}.calls", a.get("calls", n)))
                ctx = int(_pos(f"actual.{r['id']}.ctx_tokens", a.get("ctx_tokens", ctx)))
            ctx = max(ctx, r["profile_floor"])
            cost = n * ctx
            reserve_cost = r["reserve_calls"] * ctx
            if r["work"] is not None and not a:
                cal = doc.get("calibration") or {}
                missing = [k for k in CAL_KEYS if k not in cal]
                if missing:
                    raise Refused("BAD_CLAIM", f"unit {r['id']!r} has work but calibration lacks {missing}")
                for k in CAL_KEYS:
                    _pos(f"calibration.{k}", cal[k], allow_zero=k != "files_per_call")
                n, cost = work_cost(r["work"], cal, r["profile_floor"])
                ctx = -(-cost // n)  # mean processed per call; the route charges calls x this
                # a reserve call lands after the planned ones, at the grown context
                last = r["profile_floor"] + int(cal["ctx_start_over_floor"]) + int(r["work"].get("extra_ctx", 0)) \
                    + int(r["work"].get("explore_ctx", 0)) + int(cal["ctx_growth_per_call"]) * n \
                    + int(cal["output_per_call"])
                reserve_cost = r["reserve_calls"] * last
            r.update(calls=n, ctx_eff=ctx, cost=cost, reserve_cost=reserve_cost, measured=bool(a))
            calls += n
            cand += cost
            reserve_calls += r["reserve_calls"]
            reserve_tokens += r["reserve_cost"]
            ceil += math.ceil(cost * (deopt - 1)) if r["deopt"] else 0
        allowance = doc.get("unmeasured_allowance", DEFAULT_UNMEASURED_ALLOWANCE)
        allowance = float(_pos("unmeasured_allowance", allowance, allow_zero=True))
        if active and all(r["measured"] for r in active):
            allowance = 0.0
        ceil += cand + reserve_tokens + math.ceil(cand * allowance)
        active_rows = active
    floor_calls = min(min_calls, calls)
    out = {
        "verdict": "COMPILED",
        "floor": {"calls": floor_calls, "tokens": floor_calls * worker_floor},
        "candidate": {"calls": calls, "tokens": cand, "with_margin": ra._with_margin(cand, margin)},
        "ceiling": {"tokens": ceil, "deopt_factor": deopt},
        "counts": counts, "clean": clean, **clean, "sleeping": sleeping, "owner_reality": owner,
        "profile_source": source, "worker_floor": worker_floor, "margin": margin,
        "units": [{k: r[k] for k in ("id", "profile", "model_prior", "calls", "reserve_calls", "ctx_eff",
                                     "profile_floor", "cost", "claims")} for r in active_rows],
        "reserve_calls": reserve_calls, "reserve_tokens": reserve_tokens,
        "unmeasured_allowance": allowance,
    }
    return out


def build_route(cost: dict, doc: dict) -> dict:
    """The route_admission route the unit costs describe: one worker per active unit."""
    rows = cost["units"]
    if not rows:
        raise Refused("BAD_CLAIM", "--route needs `units` with at least one active model claim")
    workers = [{"name": r["id"], "profile": r["profile"], "calls": r["calls"],
                "packet": max(r["ctx_eff"] - r["profile_floor"], 0)} for r in rows]
    ov = doc.get("envelope") or {}
    # target is the candidate WITH the growth margin: admit() charges floor x (1 + margin) against the
    # target, so a target equal to the bare candidate could never be admitted.
    target = int(ov.get("target") or cost["candidate"]["with_margin"])
    warn = max(target, target + cost["reserve_tokens"])
    stop = max(cost["ceiling"]["tokens"], warn)
    env_calls = int(ov.get("calls") or (cost["candidate"]["calls"] + cost["reserve_calls"]))
    return {"envelope": {"target": target, "warn": warn, "stop": stop, "calls": env_calls},
            "workers": workers}


def route_verdict(doc: dict, floors: dict, *, margin: float = ra.DEFAULT_GROWTH_MARGIN,
                  remaining: int | None = None, admit_fn=None) -> dict:
    """The mission verdict IS route_admission.admit's verdict: ADMISSIBLE is never reported otherwise."""
    cost = compile_cost(doc, floors, margin=margin)
    route = build_route(cost, doc)
    try:
        adm = (admit_fn or ra.admit)(route, floors, margin=margin, remaining=remaining)
    except ValueError as exc:
        raise Refused("BAD_CLAIM", f"route is malformed: {exc}")
    return {"verdict": adm["verdict"], "route": route, "admission": adm, "cost": cost}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="cost-to-completion from a claim graph")
    ap.add_argument("--claims", required=True)
    ap.add_argument("--floors")
    ap.add_argument("--margin", type=float, default=ra.DEFAULT_GROWTH_MARGIN)
    ap.add_argument("--route", action="store_true", help="emit a route and return route_admission's verdict")
    ap.add_argument("--remaining", type=int)
    args = ap.parse_args(argv)
    try:
        doc = json.loads(Path(args.claims).read_text(encoding="utf-8-sig"))
        floors = ra.load_floors(args.floors)
        if args.route:
            out = route_verdict(doc, floors, margin=args.margin, remaining=args.remaining)
        else:
            out = compile_cost(doc, floors, margin=args.margin)
    except Refused as r:
        print(json.dumps({"verdict": "REFUSED", "reason": r.reason, "detail": r.detail}))
        print(f"REFUSED {r.reason}: {r.detail}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        print(json.dumps({"verdict": "REFUSED", "reason": "BAD_INPUT", "detail": str(exc)}))
        return 2
    print(json.dumps(out, indent=2))
    return 3 if args.route and out["verdict"] != ra.ADMISSIBLE else 0


if __name__ == "__main__":
    sys.exit(main())
