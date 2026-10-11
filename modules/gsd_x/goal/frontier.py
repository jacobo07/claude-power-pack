#!/usr/bin/env python3
"""The compiled execution frontier (GSD X Phase 3, spec S8 / S10).

`decide()` used to look at one epoch and say WAIT. A goal with one slow gate running and five
independent gates waiting then idled for no reason the log can justify. This module turns a
reconciler `Context` into a FRONTIER: the justified actions that can run now, each carrying the
read / write / resource sets that say what it may run beside.

Everything here is a pure projection of the goal log. Nothing is persisted: the only thing a
frontier ever adds to the log is the `unit` key on a frontier-path epoch spec (epoch.begin).

Undeclared is never independent (Law 4): a unit whose sets cannot be derived carries None, and
`proof.independent` treats a None set as conflicting with everything.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from math import log2
from statistics import median

from . import convergence as cv
from . import epoch as ep
from . import proof as pf
from .contract import GoalState

# Resource names are EXCLUSIVE environments. Shared CPU is not one: it never serialises work.
INTEGRATION_ENV = "integration-env"
REALITY_ENV = "reality-env"
WHOLE_TREE = "tree:*"
KNOWN_CLASSES = frozenset({"unit", "integration", "in_game", "live"})

# `FRONTIER.off` beside the goal store forces the legacy path for a scheduled sweep that cannot
# inherit an interactive environment variable. Either source off means legacy.
OFF_FILE = "FRONTIER.off"


def frontier_enabled() -> bool:
    """Env `GSDX_FRONTIER` on (Phase 2 token table) AND no OFF_FILE in the sweep state dir."""
    if not pf.switch_on(pf.FRONTIER_SWITCH):
        return False
    from . import sweep  # noqa: PLC0415 -- lazy: sweep imports reconcile imports this module
    return not (sweep.state_dir() / OFF_FILE).exists()


# --- units ---------------------------------------------------------------------

def _undeclared(obligation_id: str, gate_class: str, why: str) -> dict:
    return {"id": f"gate:{obligation_id}", "kind": "gate", "obligation": obligation_id,
            "gate_class": gate_class, "reads": None, "writes": None, "resources": None, "why": why}


def _causal_paths(state: GoalState, obligation) -> set:
    data, _refused = pf.effective_contract(pf.project_proofs(state), obligation)
    return {p for el in (data.get("elements") or []) for p in (el.get("causal_paths") or [])}


def gate_unit(obligation, state: GoalState) -> dict:
    """The unit that running `obligation`'s gate would be: what it reads, writes and holds.

    The gate class is the one the sweep dispatches (`o.gate_class or "unit"`, sweep.py:365); a
    REALITY-plane obligation without a runtime class is never dispatched, and a class this module
    does not know cannot be reasoned about, so both come back undeclared.
    """
    oid = obligation.identifier
    declared = obligation.gate_class
    reality = obligation.plane in cv.REALITY_PLANES
    if reality and declared not in cv.RUNTIME_GATE_CLASSES:
        return _undeclared(oid, declared, "reality obligation declares no runtime gate class")
    gate_class = declared or "unit"
    if gate_class not in KNOWN_CLASSES:
        return _undeclared(oid, gate_class, f"unknown gate class {gate_class!r}")
    try:
        causal = _causal_paths(state, obligation)
    except (KeyError, TypeError, AttributeError) as exc:
        return _undeclared(oid, gate_class, f"contract unreadable ({type(exc).__name__})")
    reads = {rel for rel, _ in obligation.gate_pin} | causal
    if not causal:
        reads.add(WHOLE_TREE)       # nothing says what it reads: it may read all of it
    resources: set = set()
    if gate_class == "integration":
        resources.add(INTEGRATION_ENV)
    if reality or gate_class in cv.RUNTIME_GATE_CLASSES:
        resources.add(REALITY_ENV)
    return {"id": f"gate:{oid}", "kind": "gate", "obligation": oid, "gate_class": gate_class,
            "reads": sorted(reads), "writes": [f"run:{oid}"], "resources": sorted(resources)}


def independent_units(a: dict, b: dict) -> bool:
    """The one definition of independence is `proof.independent` (spec S8)."""
    return pf.independent(a, b)


def stored_unit(unit: dict) -> dict:
    """The part of a unit that is written into an epoch spec: the sets, nothing derived."""
    return {k: unit.get(k) for k in ("id", "kind", "obligation", "gate_class", "reads", "writes",
                                     "resources")}


# --- postures, bounds, worker classes (D09, D27) -----------------------------------

POSTURES = ("ECONOMY", "BALANCED", "WALL_CLOCK")
POSTURE_BOUND = {"ECONOMY": 1, "BALANCED": 2, "WALL_CLOCK": 4}
DEFAULT_POSTURE = "ECONOMY"      # bound 1: a goal that never declares a posture runs as it always did
WORKER_CLASSES = ("cognitive", "deterministic", "environment", "reviewer", "speculative")


def _budget_value(ctx, key: str):
    """The goal budget's `key`: the Context's own budget first, then the projected goal budget."""
    for source in (getattr(ctx, "budget", None), getattr(getattr(ctx, "state", None), "budget", None)):
        if isinstance(source, dict) and key in source:
            return source[key]
    return None


def posture(ctx) -> str:
    raw = _budget_value(ctx, "posture")
    word = raw.strip().upper() if isinstance(raw, str) else ""
    return word if word in POSTURE_BOUND else DEFAULT_POSTURE


def bound(ctx) -> int:
    """How many deterministic gate epochs may be open at once. `max_parallel` only lowers it, and a
    value that is not a positive int is ignored rather than trusted (a bool is not a count)."""
    n = POSTURE_BOUND[posture(ctx)]
    cap = _budget_value(ctx, "max_parallel")
    if isinstance(cap, int) and not isinstance(cap, bool) and cap >= 1:
        n = min(n, cap)
    return n


def class_bound(worker_class: str, ctx) -> int:
    """Concurrency of agents is not concurrency of verification: only deterministic workers scale with
    the posture; environment workers are bounded by their one exclusive resource, the rest run alone."""
    if worker_class not in WORKER_CLASSES:
        raise ValueError(f"{worker_class!r} is not a worker class {WORKER_CLASSES}")
    return bound(ctx) if worker_class == "deterministic" else 1


# --- measured signals (D08, D28, D33, D34): from this goal's own log, nothing estimated -------

def _gate_runs(state) -> list:
    """(obligation, gate class, outcome, seconds) for every gate epoch that RAN to a verdict."""
    stamps: dict = {}
    for ev in state.events:
        eid = ev.data.get("epoch_id") if isinstance(ev.data, dict) else None
        if eid and ev.type in (ep.RUNNING, ep.ENDED):
            stamps.setdefault(eid, {})[ev.type] = ev.ts
    runs = []
    for e in ep.project_epochs(state).values():
        if e.provider != "gate" or e.outcome not in (ep.COMPLETED, ep.FAILED):
            continue       # lost, expired and cancelled epochs measured nothing
        st = stamps.get(e.epoch_id, {})
        if ep.RUNNING not in st or ep.ENDED not in st:
            continue
        seconds = (datetime.fromisoformat(st[ep.ENDED]) - datetime.fromisoformat(st[ep.RUNNING])).total_seconds()
        gate = e.spec.get("gate") or {}
        runs.append((e.spec.get("obligation"), gate.get("class") or "unit", e.outcome, seconds))
    return runs


def duration_prior(state, obligation_id: str, gate_class: str):
    """Median measured seconds: this obligation's own gate runs, else its gate class in this goal, else None."""
    runs = _gate_runs(state)
    own = [s for o, _c, _x, s in runs if o == obligation_id]
    if own:
        return float(median(own))
    same = [s for _o, c, _x, s in runs if c == gate_class]
    return float(median(same)) if same else None


def _fail_fraction(state, obligation_id: str):
    own = [x for o, _c, x, _s in _gate_runs(state) if o == obligation_id]
    return None if not own else sum(1 for x in own if x == ep.FAILED) / len(own)


def failure_risk(state, obligation_id: str, units: list):
    """Measured fail fraction x (1 + other units sharing a read). None with no history, never 0."""
    frac = _fail_fraction(state, obligation_id)
    if frac is None:
        return None
    mine = next((u for u in units if u["obligation"] == obligation_id), None)
    reads = set(mine["reads"] or ()) - {WHOLE_TREE} if mine else set()
    sharing = sum(1 for u in units if u["obligation"] != obligation_id
                  and reads & (set(u["reads"] or ()) - {WHOLE_TREE}))
    return frac * (1 + sharing)


def info_gain(state, obligation_id: str, gate_class: str):
    """Binary entropy of the measured pass fraction per second of measured duration. None unless both
    are measured; a measured duration of zero is a clock artefact, not an infinitely cheap gate."""
    frac = _fail_fraction(state, obligation_id)
    prior = duration_prior(state, obligation_id, gate_class)
    if frac is None or prior is None or prior <= 0:
        return None
    entropy = 0.0 if frac in (0.0, 1.0) else -(frac * log2(frac) + (1 - frac) * log2(1 - frac))
    return entropy / prior


def critical_path(units: list, edges: tuple, durations: dict) -> dict:
    """Longest chain through the units, following the resource edges (which are directed in frontier
    order). A unit with an unmeasured duration counts 0 toward the length and is listed in `unknown`,
    so `length` is then a lower bound and never a claim."""
    ids = [u["id"] for u in units]
    nxt: dict = {i: [] for i in ids}
    for a, b, kind in edges:
        if a in nxt and b in nxt and kind.startswith("resource:"):
            nxt[a].append(b)
    best: dict = {}

    def walk(i: str) -> tuple:
        if i not in best:
            own = durations.get(i) or 0.0
            tails = [walk(j) for j in nxt[i]]
            tail = max(tails, key=lambda t: t[0], default=(0.0, ()))
            best[i] = (own + tail[0], (i,) + tail[1])
        return best[i]

    for i in ids:
        walk(i)
    top = max((best[i] for i in ids), key=lambda t: t[0], default=(0.0, ()))
    return {"length": top[0], "nodes": top[1], "contrib": {i: best[i][0] for i in ids},
            "unknown": tuple(i for i in ids if durations.get(i) is None)}


def order_units(units: list, signals: dict) -> tuple:
    """The documented lexicographic order, never a blended score: unmeasured duration first (running it
    makes the prior), then critical-path contribution, failure risk, information gain, all descending
    with measured before unmeasured, then the position the units arrived in."""
    def key(pair):
        index, u = pair
        s = signals[u["id"]]
        risk, gain = s["risk"], s["gain"]
        return (0 if s["duration"] is None else 1, -s["contrib"],
                0 if risk is not None else 1, -(risk or 0.0),
                0 if gain is not None else 1, -(gain or 0.0), index)
    return tuple(u for _i, u in sorted(enumerate(units), key=key))


# --- the frontier ----------------------------------------------------------------

@dataclass(frozen=True)
class Frontier:
    expectation: tuple = ()       # obligation ids still part of what the goal expects
    execution: tuple = ()         # units that can be started now, in measured order
    proof: tuple = ()             # what blocks closure, and claims that are not fresh
    invalidation: tuple = ()      # claims proven earlier whose proof no longer holds here
    edges: tuple = field(default_factory=tuple)   # (src, dst, kind), derived only
    critical_path: dict = field(default_factory=dict)
    posture: str = DEFAULT_POSTURE
    bound: int = 1
    signals: dict = field(default_factory=dict)   # unit id -> {duration, contrib, risk, gain}


def open_obligations(state: GoalState) -> set:
    """Obligation ids with an epoch that has not ended."""
    return {e.spec.get("obligation") for e in ep.project_epochs(state).values() if e.state != "ended"}


def _runnable_gate_obligations(ctx) -> list:
    """Obligations whose gate the legacy path would run next, minus any that already have an open
    epoch (the legacy path relied on its one-open-epoch rule for that; with N epochs it cannot)."""
    from . import reconcile as rc  # noqa: PLC0415 -- lazy, see frontier_enabled
    st = ctx.state
    eps = ep.project_epochs(st)
    judged = {e.spec.get("obligation") for e in eps.values()
              if e.provider == "gate" and e.spec.get("tree_hash") == ctx.tree_hash
              and e.outcome in (ep.COMPLETED, ep.FAILED)}
    open_now = open_obligations(st)
    out = []
    for o in cv.project_convergence(st).obligations.values():
        if not rc._needs_a_gate_here(o, ctx) or o.identifier in judged or o.identifier in open_now:
            continue
        key = ep.info_key(st.revision, [o.identifier], "gate", "initial", ctx.scope_hash,
                          engine=ctx.engine)
        if any(e.info_key == key and e.outcome in ep.UNSUCCESSFUL for e in eps.values()):
            continue
        out.append((o, key))
    return out


def _open_epochs(state: GoalState) -> list:
    return [e for e in ep.project_epochs(state).values() if e.state != "ended"]


def _ended_sibling(ctx):
    """The first running epoch whose observation says it ended or was lost: legacy WAITs on an
    earlier running sibling and never reaches it."""
    from . import reconcile as rc  # noqa: PLC0415 -- lazy, see frontier_enabled
    for e in _open_epochs(ctx.state):
        obs = ctx.observations.get(e.epoch_id)
        if e.state == "running" and obs is not None and obs.state in (ep.OBS_ENDED, ep.OBS_LOST):
            return rc.Decision(rc.HARVEST, f"{e.epoch_id} ended {obs.outcome or obs.state}: "
                                           f"{obs.detail}", epoch_id=e.epoch_id)
    return None


def _may_start_new(ctx) -> bool:
    """Every condition under which legacy stops before step 5 (spec S8): a paused or cancelled goal,
    clear closure, an external block or a spent budget starts NOTHING while a sibling runs."""
    from . import reconcile as rc  # noqa: PLC0415 -- lazy, see frontier_enabled
    from .intervention import blocking_reason  # noqa: PLC0415
    st = ctx.state
    return not (blocking_reason(st) or cv.goal_closure(st, ctx.tree_hash).may_close
                or ctx.blocked_on or rc._budget_verdict(ctx))


def decide_frontier(ctx, legacy):
    """`legacy(ctx)` unless it said WAIT with epochs in flight: then harvest an ended sibling, or start
    a gate that is independent of everything open. Only WAIT is ever replaced."""
    from . import reconcile as rc  # noqa: PLC0415 -- lazy, see frontier_enabled
    base = legacy(ctx)
    open_eps = _open_epochs(ctx.state)
    if base.kind != rc.WAIT or (bound(ctx) == 1 and len(open_eps) < 2):
        return base
    harvest = _ended_sibling(ctx)
    if harvest is not None:
        return harvest
    if len(open_eps) >= bound(ctx) or not _may_start_new(ctx):
        return base
    stored = [e.spec.get("unit") for e in open_eps]
    if any(u is None for u in stored):
        return base                    # an open epoch with no declared unit conflicts with everything
    fr = compile_frontier(ctx)
    for u in fr.execution:
        if all(independent_units(u, other) for other in stored):
            o = cv.project_convergence(ctx.state).obligations[u["obligation"]]
            return rc.Decision(rc.NEXT_EPOCH,
                               f"{o.identifier} ({o.plane}) {rc._needs_a_gate_here(o, ctx)}",
                               provider="gate", hypothesis="initial", info_key=u["info_key"],
                               spec={"obligation": o.identifier, "gate": o.done_gate,
                                     "tree_hash": ctx.tree_hash, "plane": o.plane,
                                     "unit": stored_unit(u)})
    return base


def compile_frontier(ctx) -> Frontier:
    st = ctx.state
    convergence = cv.project_convergence(st)
    eps = ep.project_epochs(st)
    closure = cv.goal_closure(st, ctx.tree_hash)
    states = pf.proof_states(st, ctx.tree_hash)

    expectation = tuple(oid for oid, o in convergence.obligations.items()
                        if o.disposition in (cv.ACCEPTED, cv.SATISFIED))
    execution = []
    if "gate" in ctx.providers:
        for o, key in _runnable_gate_obligations(ctx):
            unit = gate_unit(o, st)
            unit["info_key"] = key
            unit["plane"] = o.plane
            unit["done_gate"] = o.done_gate
            execution.append(unit)
    proof_items = list(closure.blocking) + [
        f"claim:{oid}:{s['state']}" for oid, s in states.items()
        if s["state"] not in (pf.PS_FRESH, pf.PS_INHERITED, pf.NOT_APPLICABLE)]
    invalidation = tuple(oid for oid, s in states.items() if s["state"] in (pf.PS_STALE, pf.PS_UNKNOWN))

    edges = []
    for o in convergence.obligations.values():
        failed_before = o.disposition == cv.ACCEPTED and any(
            e.spec.get("obligation") == o.identifier and e.outcome in ep.UNSUCCESSFUL
            for e in eps.values())
        if failed_before:
            edges.append((f"work:{o.identifier}", f"gate:{o.identifier}", "work->gate"))
    for u in execution:
        edges.append((u["id"], "barrier", "gate->barrier"))
    for e in eps.values():
        if e.state != "ended" and e.spec.get("obligation"):
            edges.append((f"harvest:{e.epoch_id}", f"gate:{e.spec['obligation']}", "harvest->unit"))
    edges.append(("barrier", "judge", "barrier->judge"))
    for i, a in enumerate(execution):
        for b in execution[i + 1:]:
            for name in sorted(set(a["resources"] or ()) & set(b["resources"] or ())):
                edges.append((a["id"], b["id"], f"resource:{name}"))
    durations = {u["id"]: duration_prior(st, u["obligation"], u["gate_class"]) for u in execution}
    path = critical_path(execution, tuple(edges), durations)
    signals = {u["id"]: {"duration": durations[u["id"]], "contrib": path["contrib"][u["id"]],
                         "risk": failure_risk(st, u["obligation"], execution),
                         "gain": info_gain(st, u["obligation"], u["gate_class"])} for u in execution}
    ordered = order_units(execution, signals)
    return Frontier(expectation=expectation, execution=ordered, proof=tuple(proof_items),
                    invalidation=invalidation, edges=tuple(edges), critical_path=path,
                    posture=posture(ctx), bound=bound(ctx), signals=signals)
