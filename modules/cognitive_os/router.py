#!/usr/bin/env python3
"""router.py -- CO-03: the Dynamic Cognitive Router (cheapest-first cascade).

Before any model is invoked, the router walks a cascade of progressively more
expensive resolutions and STOPS at the first that satisfies the task. The
expensive model is the LAST resort by construction, not the default:

  1. Vault        -- a CO-05 stored answer resolves it: ZERO new model tokens.
  2. Reusable asset -- a CO-05 template/rule applies deterministically: ~zero.
  3. Deterministic  -- code / rule / cache / a recovery op (/compact, /kclear):
                       no model at all.
  4. Haiku        -- needs a model but mechanical/bounded (NANO / tier 0-1).
  5. Sonnet       -- standard reasoning/execution (the MICRO/MACRO default).
  6. Opus         -- last resort: architecture, hard multi-step, iteration-on-error.

EXTEND, not NEW (CO-03 I.2): unifies the three routers that exist and disagree
today into ONE decision -- classify_tier (spec_gate) sets the task-shape FLOOR
(how cheap a rung is *allowed*), cost_collapse.route picks the model within it,
and budget pressure (CO-02) breaks ties toward cheaper. Conflicting signals
resolve to the HIGHEST floor any input demands (CO-03 III.1), never a silent pick.

Rungs 1-2 are CO-05 (not built yet) -> their resolvers default to "miss" and are
pluggable, so the cascade is live now (model tiers are fully real via the two
existing routers) and gains the zero-token rungs when CO-05 lands. Honest
guarantee (CO-10): governs model selection where it owns the call path; a model
call issued outside the cascade is CO-10's flagged residual.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

# Model ids (per ~/.claude/CLAUDE.md registry, 2026; opus-4-8 supersedes the
# stale opus-4-7 in cost_collapse).
HAIKU, SONNET, OPUS = "claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-8"
_MODEL_RANK = {HAIKU: 0, SONNET: 1, OPUS: 2}
_RANK_MODEL = {0: HAIKU, 1: SONNET, 2: OPUS}
_MODEL_RUNG = {HAIKU: "haiku", SONNET: "sonnet", OPUS: "opus"}

# task-shape floor (classify_tier tier -> minimum model rank allowed).
_TIER_FLOOR = {0: 0, 1: 0, 2: 1, 3: 2}        # 0=haiku 1=sonnet 2=opus
# keyword routing (cost_collapse route_class -> model rank).
_CLASS_RANK = {"nano": 0, "micro": 1, "macro": 2, "ultra": 2}

# Deterministic-resolvable without a model (CO-03 III.3: recovery ops).
_DETERMINISTIC_KW = ("/compact", "/kclear", "/clear", "compact the",
                     "kclear", "rollback the")


@dataclass
class RouteDecision:
    rung: str                          # vault|asset|deterministic|haiku|sonnet|opus
    model: str | None                  # model id, or None for the zero-token rungs
    reason: str
    tier: int | None = None            # classify_tier shape (None for zero rungs)
    route_class: str = ""              # cost_collapse class
    cost: str = ""                     # "zero" | "model"
    floor_rung: str = ""               # the cheapest model rung the shape allowed
    notes: list = field(default_factory=list)


def _default_deterministic(task: str):
    t = (task or "").lower()
    for kw in _DETERMINISTIC_KW:
        if kw in t:
            return f"recovery/deterministic op ({kw!r}) -- no model"
    return None


def route(task: str, *, budget_pressure: bool = False,
          vault_fn=None, asset_fn=None, deterministic_fn=None,
          classify_fn=None, route_fn=None) -> RouteDecision:
    """Walk the cascade; stop at the first rung that resolves `task`. Fail-open:
    any error in the cheap rungs falls through to model routing; a total failure
    defaults to Sonnet (never Opus-by-default, never a crash)."""
    # Rung 1 -- Vault (CO-05 stored answer). Pluggable; default miss.
    try:
        if vault_fn:
            hit = vault_fn(task)
            if hit:
                return RouteDecision("vault", None, f"vault hit: {hit}",
                                     cost="zero")
    except Exception:  # noqa: BLE001 -- a cheap-rung error never blocks routing
        pass

    # Rung 2 -- reusable asset (CO-05 template/rule). Pluggable; default miss.
    try:
        if asset_fn:
            hit = asset_fn(task)
            if hit:
                return RouteDecision("asset", None, f"asset applies: {hit}",
                                     cost="zero")
    except Exception:  # noqa: BLE001
        pass

    # Rung 3 -- deterministic / recovery / cache (no model).
    try:
        det = (deterministic_fn or _default_deterministic)(task)
        if det:
            return RouteDecision("deterministic", None, det, cost="zero")
    except Exception:  # noqa: BLE001
        pass

    # Rungs 4-6 -- a model is needed. Unify the two existing routers.
    try:
        if classify_fn is None:
            from modules.spec_gate.gate import classify_tier as classify_fn  # type: ignore
        tier = classify_fn(task).tier
    except Exception:  # noqa: BLE001
        tier = 1
    try:
        if route_fn is None:
            from modules.cost_collapse.router import route as route_fn  # type: ignore
        rr = route_fn(task)
        route_class = getattr(getattr(rr, "route_class", None), "value", "micro")
    except Exception:  # noqa: BLE001
        route_class = "micro"

    floor_rank = _TIER_FLOOR.get(tier, 1)
    kw_rank = _CLASS_RANK.get(route_class, 1)
    # Highest floor any input demands (CO-03 III.1): never under-serve a big task
    # because a keyword looked cheap.
    rank = max(floor_rank, kw_rank)
    notes = []
    if budget_pressure and rank > floor_rank:
        rank = max(floor_rank, rank - 1)   # bias cheaper, never below the floor
        notes.append("budget pressure -> stepped one rung cheaper (above floor)")

    model = _RANK_MODEL[rank]
    floor_model = _RANK_MODEL[floor_rank]
    reason = (f"tier {tier} (floor {_MODEL_RUNG[floor_model]}) + "
              f"{route_class} keyword -> {_MODEL_RUNG[model]}")
    return RouteDecision(_MODEL_RUNG[model], model, reason, tier, route_class,
                         "model", _MODEL_RUNG[floor_model], notes)


def escalate(current_model: str, *, reason: str = "") -> str:
    """The upward path (CO-03 II.3): when a rung fails its done-gate, escalate to
    the next model with context -- never stubbornly retry a too-weak rung
    (2-consecutive-failures law). Capped at Opus."""
    rank = _MODEL_RANK.get(current_model, 1)
    return _RANK_MODEL[min(2, rank + 1)]


def main(argv=None) -> int:
    import argparse
    import json
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("task", nargs="+")
    ap.add_argument("--budget-pressure", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    d = route(" ".join(args.task), budget_pressure=args.budget_pressure)
    if args.json:
        print(json.dumps(d.__dict__))
    else:
        print(f"rung={d.rung}  model={d.model or '(zero-token)'}")
        print(f"  {d.reason}")
        for n in d.notes:
            print(f"  note: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
