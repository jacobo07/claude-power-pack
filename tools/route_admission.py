"""Route admission: is a work unit's topology feasible inside its token envelope BEFORE it runs?

Live QA W0 (m-8bbdf725cd52, 2026-10-05) was planned at 4M and ran to 53.7M of its own spend: an
orchestrator plus four GSD subagents, each re-reading a floor of ~85k (subagents) or ~111k (a
top-level worker) on every call. Nothing compared the topology with the envelope before launch; the
cost breaker only saw it afterwards. This module is that comparison. Pure, deterministic, no model.

Mechanical floor of a route = sum over its workers of calls x (profile floor + packet). It is a lower
bound: every call re-reads at least the first-call context. The growth margin covers the context
growing within the run; DEFAULT_GROWTH_MARGIN is a chosen value, not a measured one.

Verdicts (only ADMISSIBLE may launch):
  ADMISSIBLE  floor x (1 + margin) <= envelope target, and total calls <= envelope calls
  DEFER       admissible against the envelope, but more than the budget still remaining now
  RECOMPILE   does not fit; the envelope can hold a minimal unit, so the planner must thin the route
              (fewer calls, cheaper profiles, no agents) -- `max_calls_single_worker` says how far
  ESCALATE    nothing the planner can do: a profile has no measured floor (absent is not zero), or
              the envelope cannot hold even one top-level worker for default_min_calls -- Owner call

  route_admission.py admit --route ROUTE.json [--floors F] [--margin 0.2] [--remaining N]
ROUTE.json = {"envelope": {"target", "warn", "stop", "calls"},
              "workers": [{"name", "profile", "calls", "packet"}]}
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FLOORS_PATH = REPO_ROOT / "vault" / "config" / "route-floors.json"
DEFAULT_GROWTH_MARGIN = 0.20
TOP_LEVEL = "top-level-worker"
ADMISSIBLE, WATCHED, DEFER, RECOMPILE, ESCALATE = "ADMISSIBLE", "WATCHED", "DEFER", "RECOMPILE", "ESCALATE"
LOW_CONFIDENCE_N = 5            # fewer samples than this: SAFETY can only WATCH, never refuse (spec D3)
CHALLENGER_AUTHORITATIVE = False  # spec D3 flip held: it turns test_route_admission / test_gsd_mission_admission red (see RECEIPT-E1)


def load_floors(path: Path | str | None = None) -> dict:
    data = json.loads(Path(path or FLOORS_PATH).read_text(encoding="utf-8-sig"))
    profiles = data.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError("floor table has no profiles")
    return data


def _pos_int(field: str, value) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be a positive integer, not {value!r}")
    return value


def _with_margin(n: int, margin: float) -> int:
    # round first: 1000 x 1.1 is 1100.0000000000002 in floats, and ceil would make it 1101
    return math.ceil(round(n * (1 + margin), 6))


def route_digest(route: dict) -> str:
    return hashlib.sha256(json.dumps(route, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _calibrated(profile: dict, field: str) -> tuple[float, int, str] | None:
    """(value, n, basis) of a calibrated profile field, or None. Absent / malformed is UNKNOWN, never 0."""
    f = profile.get(field)
    if not isinstance(f, dict):
        return None
    v, n = f.get("value"), f.get("n")
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0:
        return None
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        return None
    return float(v), n, str(f.get("basis") or "estimated")


def _process_cost(floor: int, packet: int, g: float, calls: int) -> int:
    """n x (F + packet) + g x n(n-1)/2: context grows linearly inside one process, so cost is quadratic."""
    return round(calls * (floor + packet) + g * calls * (calls - 1) / 2)


def max_calls_per_process(floor: int, g: float, target: int) -> int:
    n = 0
    while _process_cost(floor, 0, g, n + 1) <= target:
        n += 1
    return n


def forecast_route(champ: dict, floors: dict, *, remaining: int | None = None) -> dict:
    """Expected-completion tiers over the champion's measured rows. `available: False` only for a legacy
    floor table that carries no growth calibration at all (the champion stands); a profile missing its own
    calibration inside a calibrated table is UNKNOWN -> ESCALATE."""
    profiles = floors["profiles"]
    if not any(isinstance(p, dict) and "growth_per_call" in p for p in profiles.values()):
        return {"available": False, "reason": "floor table has no growth calibration"}
    env = champ["envelope"]
    target, warn, stop, env_calls = env["target"], env["warn"], env["stop"], env["calls"]
    lower = champ["need"]
    expected = safety = 0
    unknown, ns, bases = [], [], []
    for r in champ["workers"]:
        prof = profiles[r["profile"]]
        g, err = _calibrated(prof, "growth_per_call"), _calibrated(prof, "calls_err")
        if g is None or err is None:
            unknown.append(f"{r['name']}: profile {r['profile']!r} has no calibrated "
                           f"{'growth_per_call' if g is None else 'calls_err'} (absent is not zero)")
            continue
        hi = math.ceil(round(r["calls"] * (1 + err[0]), 6))
        expected += _process_cost(r["floor"], r["packet"], g[0], r["calls"])
        safety += _process_cost(r["floor"], r["packet"], g[0], hi)
        ns += [g[1], err[1]]
        bases += [g[2], err[2]]
    top = profiles.get(TOP_LEVEL) or {}
    tg = _calibrated(top, "growth_per_call")
    cap = max_calls_per_process(top["floor"], tg[0], target) if tg and isinstance(top.get("floor"), int) else None
    out = {"available": True, "lower_bound": lower, "hard": stop, "max_calls_per_process": cap,
           "proof_repair": "included_in_calibration"}
    if unknown:
        return {**out, "expected": None, "safety": None, "confidence": {"level": "UNMEASURED", "n": 0},
                "basis": "unmeasured", "verdict": ESCALATE, "reasons": unknown}
    n_min = min(ns)
    low = n_min < LOW_CONFIDENCE_N
    weakest = "estimated" if any(not b.startswith("measured") for b in bases) else "measured"
    out.update(expected=expected, safety=safety, basis=weakest,
               confidence={"level": "LOW" if low else "OK", "n": n_min})
    reasons = []
    if env_calls is not None and champ["calls"] > env_calls:
        reasons.append(f"{champ['calls']} calls > envelope {env_calls}")
    if expected > target:
        reasons.append(f"expected {expected:,} > target {target:,}")
    if reasons:
        min_calls = int(floors.get("default_min_calls") or 1)
        top_floor = top.get("floor") if isinstance(top.get("floor"), int) else max(p["floor"] for p in profiles.values())
        if min_calls * top_floor > target:
            return {**out, "verdict": ESCALATE, "reasons": reasons + [
                f"the envelope cannot hold one {TOP_LEVEL} for {min_calls} calls: raise it or drop the unit"]}
        if cap is not None:
            reasons.append(f"thin the route: one {TOP_LEVEL}, no agents, at most {cap} calls per process fits")
        return {**out, "verdict": RECOMPILE, "reasons": reasons}
    if safety > stop:
        if low:
            verdict, why = WATCHED, (f"safety {safety:,} > stop {stop:,}, but confidence is LOW (n={n_min} < "
                                     f"{LOW_CONFIDENCE_N}): safety can only watch, never refuse")
        else:
            return {**out, "verdict": ESCALATE, "reasons": [f"safety {safety:,} > stop {stop:,}"]}
    elif safety > warn:
        verdict, why = WATCHED, f"safety {safety:,} > warn {warn:,}: reforecast at planned-calls exhaustion and at warn"
    else:
        verdict, why = ADMISSIBLE, None
    if remaining is not None and expected > remaining:
        return {**out, "verdict": DEFER,
                "reasons": [f"expects {expected:,} but only {remaining:,} of the budget remains"]}
    return {**out, "verdict": verdict, "reasons": [why] if why else []}


def dependent_admission(pred_spent: int | None, pred_target: int | None) -> dict:
    """A successor is admitted against its predecessor's METERED receipt (spent processed tokens), never
    the predecessor's estimate. Absent receipt / target is UNKNOWN -> ESCALATE, never admitted; spent over
    the target means the model that sized the predecessor is wrong, so the successor must not inherit it."""
    def _ok(v) -> bool:
        return isinstance(v, int) and not isinstance(v, bool) and v > 0
    if pred_spent is not None and (isinstance(pred_spent, bool) or not isinstance(pred_spent, int) or pred_spent < 0):
        pred_spent = None
    if pred_spent is None or not _ok(pred_target):
        return {"verdict": ESCALATE, "basis": "unmeasured", "spent": pred_spent, "target": pred_target,
                "reason": "predecessor has no metered receipt (absent is not zero): successor not admitted"}
    if pred_spent > pred_target:
        return {"verdict": ESCALATE, "basis": "measured:mission_spend", "spent": pred_spent, "target": pred_target,
                "reason": f"predecessor metered {pred_spent:,} > its target {pred_target:,}: "
                          f"successor inherits a bad model, escalate"}
    return {"verdict": None, "basis": "measured:mission_spend", "spent": pred_spent, "target": pred_target,
            "reason": f"predecessor metered {pred_spent:,} <= target {pred_target:,}: successor judged on its own forecast"}


def admit(route: dict, floors: dict, *, margin: float = DEFAULT_GROWTH_MARGIN,
          remaining: int | None = None, root: Path | str | None = None) -> dict:
    """Champion (floor x margin) plus challenger (expected completion). Once CHALLENGER_AUTHORITATIVE the
    challenger's verdict is the verdict and the champion's is kept under `champion`."""
    champ = _champion(route, floors, margin=margin, remaining=remaining, root=root)
    if "need" not in champ:        # an unmeasured floor / missing requires: the champion's ESCALATE stands
        return champ
    fc = forecast_route(champ, floors, remaining=remaining)
    out = {**champ, "champion": {k: champ.get(k) for k in ("verdict", "reasons", "need", "need_with_margin")}}
    if not fc["available"]:
        return {**out, "forecast": fc}
    out["max_calls_per_process"] = fc["max_calls_per_process"]
    out["forecast"] = {k: fc[k] for k in ("lower_bound", "expected", "safety", "hard", "confidence", "basis",
                                           "proof_repair")}
    out["challenger"] = {"verdict": fc["verdict"], "reasons": fc["reasons"]}
    if CHALLENGER_AUTHORITATIVE:
        out["verdict"], out["reasons"] = fc["verdict"], fc["reasons"]
    return out


def _champion(route: dict, floors: dict, *, margin: float = DEFAULT_GROWTH_MARGIN,
              remaining: int | None = None, root: Path | str | None = None) -> dict:
    """Judge `route` against its envelope. Raises ValueError on a malformed route (fail closed).
    `root` is the repo root that a profile's `requires` file is resolved against."""
    root = root or REPO_ROOT
    env = route.get("envelope") or {}
    target = _pos_int("envelope.target", env.get("target"))
    warn = _pos_int("envelope.warn", env.get("warn"))
    stop = _pos_int("envelope.stop", env.get("stop"))
    if not target <= warn <= stop:
        raise ValueError("envelope needs target <= warn <= stop")
    env_calls = env.get("calls")
    if env_calls is not None:
        env_calls = _pos_int("envelope.calls", env_calls)
    workers = route.get("workers")
    if not isinstance(workers, list) or not workers:
        raise ValueError("route needs at least one worker")
    if margin < 0:
        raise ValueError("margin must be >= 0")
    profiles = floors["profiles"]
    rows, unknown = [], []
    for i, w in enumerate(workers):
        name = str(w.get("name") or f"worker-{i}")
        calls = _pos_int(f"{name}.calls", w.get("calls"))
        packet = w.get("packet", 0)
        if isinstance(packet, bool) or not isinstance(packet, int) or packet < 0:
            raise ValueError(f"{name}.packet must be a non-negative integer")
        prof = profiles.get(w.get("profile"))
        if prof is None or not isinstance(prof.get("floor"), int) or prof["floor"] <= 0:
            unknown.append(f"{name}: profile {w.get('profile')!r} has no measured floor")
            continue
        req = prof.get("requires")
        if req and not (Path(root) / req).is_file():
            # slim-t2's floor was measured WITH the critical settings loaded; without that file the
            # worker would run with no budget breaker, which is the thing the profile exists to carry.
            unknown.append(f"{name}: profile {w.get('profile')!r} requires {req}, which is missing")
            continue
        rows.append({"name": name, "profile": w["profile"], "calls": calls, "packet": packet,
                     "floor": prof["floor"], "cost": calls * (prof["floor"] + packet)})
    out = {"envelope": {"target": target, "warn": warn, "stop": stop, "calls": env_calls},
           "margin": margin, "workers": rows, "route_sha256": route_digest(route)}
    if unknown:
        return {**out, "verdict": ESCALATE, "reasons": unknown}
    need = sum(r["cost"] for r in rows)
    need_m = _with_margin(need, margin)
    calls = sum(r["calls"] for r in rows)
    out.update(need=need, need_with_margin=need_m, calls=calls)
    top = profiles.get(TOP_LEVEL) or {}
    top_floor = top.get("floor") if isinstance(top.get("floor"), int) else max(p["floor"] for p in profiles.values())
    min_calls = int(floors.get("default_min_calls") or 1)
    out["max_calls_single_worker"] = int(target // ((1 + margin) * top_floor))
    reasons = []
    if need_m > target:
        reasons.append(f"floor {need:,} x {1 + margin:g} = {need_m:,} > target {target:,}")
    if env_calls is not None and calls > env_calls:
        reasons.append(f"{calls} calls > envelope {env_calls}")
    if not reasons:
        if remaining is not None and need_m > remaining:
            return {**out, "verdict": DEFER,
                    "reasons": [f"needs {need_m:,} but only {remaining:,} of the budget remains"]}
        return {**out, "verdict": ADMISSIBLE, "reasons": []}
    if _with_margin(min_calls * top_floor, margin) > target:
        reasons.append(f"the envelope cannot hold one {TOP_LEVEL} for {min_calls} calls "
                       f"({top_floor:,} floor): raise it or drop the unit")
        return {**out, "verdict": ESCALATE, "reasons": reasons}
    reasons.append(f"thin the route: one {TOP_LEVEL}, no agents, at most "
                   f"{out['max_calls_single_worker']} calls fits")
    return {**out, "verdict": RECOMPILE, "reasons": reasons}


def _main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="route_admission")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("admit")
    a.add_argument("--route", required=True)
    a.add_argument("--floors")
    a.add_argument("--margin", type=float, default=DEFAULT_GROWTH_MARGIN)
    a.add_argument("--remaining", type=int)
    args = ap.parse_args(argv)
    route = json.loads(Path(args.route).read_text(encoding="utf-8-sig"))
    res = admit(route, load_floors(args.floors), margin=args.margin, remaining=args.remaining)
    print(json.dumps(res, indent=1))
    return 0 if res["verdict"] == ADMISSIBLE else 3


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
