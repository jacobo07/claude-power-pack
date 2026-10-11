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


# --- the frontier ----------------------------------------------------------------

@dataclass(frozen=True)
class Frontier:
    expectation: tuple = ()       # obligation ids still part of what the goal expects
    execution: tuple = ()         # units that can be started now, in legacy order
    proof: tuple = ()             # what blocks closure, and claims that are not fresh
    invalidation: tuple = ()      # claims proven earlier whose proof no longer holds here
    edges: tuple = field(default_factory=tuple)   # (src, dst, kind), derived only


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
    return Frontier(expectation=expectation, execution=tuple(execution), proof=tuple(proof_items),
                    invalidation=invalidation, edges=tuple(edges))
