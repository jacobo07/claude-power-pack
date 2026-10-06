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
ADMISSIBLE, DEFER, RECOMPILE, ESCALATE = "ADMISSIBLE", "DEFER", "RECOMPILE", "ESCALATE"


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


def admit(route: dict, floors: dict, *, margin: float = DEFAULT_GROWTH_MARGIN,
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
