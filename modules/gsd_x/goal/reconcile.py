#!/usr/bin/env python3
"""The Goal Reconciler: what is justified next, decided deterministically.

This is the runtime primitive the whole spine exists to support. It is a PURE
FUNCTION of durable state -- events, projections, observations, the clock -- and
it does no open-ended work: it orchestrates workers and never reasons in their
place. Deterministic software owns state, leases, budgets, retry semantics and
closure; models own architecture, research, implementation and debugging.

The rules that matter, each one a failure mode named in the plan:

  * **An empty queue is not success.** If nothing is running and the goal has
    not converged, that is a reason to compute the next action, never to report
    completion. There is no code path from "no work" to CONVERGED.
  * **A provider saying DONE is not convergence.** An ended epoch produces a
    receipt to harvest; what that receipt moves is decided by gates.
  * **Closure is necessary and not sufficient.** When nothing blocks, the goal
    is READY_FOR_JUDGE -- an independent judge re-runs the pinned gates. The
    reconciler cannot write CONVERGED on its own say-so.
  * **BLOCKED names an external condition.** Tests failing, an epoch ending, a
    spent context or hard work are NOT blocks; they are reasons to continue.
  * **No retry without new information**, enforced by the epoch's info key.

Decisions are data. Applying one is a separate step, so a decision can be
inspected, logged and tested without anything happening.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .contract import GoalState
from .convergence import (ACCEPTED, REALITY, SATISFIED, goal_closure,
                          project_convergence)
from .epoch import (HYPOTHESES, OBS_ENDED, OBS_LOST, OBS_RUNNING, OBS_UNKNOWN,
                    UNSUCCESSFUL, info_key, project_epochs)

# Decision kinds.
WAIT = "WAIT"                       # an epoch is running; nothing to do yet
RECOVER = "RECOVER"                 # an epoch died between intent and effect
HARVEST = "HARVEST"                 # an epoch ended; ingest what it produced
NEXT_EPOCH = "NEXT_EPOCH"           # dispatch a bounded attempt
READY_FOR_JUDGE = "READY_FOR_JUDGE"  # nothing blocks; the judge decides
CONVERGED = "CONVERGED"             # judge receipt seen and valid
BLOCKED = "BLOCKED"                 # a NAMED external condition
ESCALATE = "ESCALATE"               # a human decision is required


@dataclass(frozen=True)
class Decision:
    kind: str
    reason: str
    epoch_id: str = ""
    spec: dict = field(default_factory=dict)
    provider: str = ""
    hypothesis: str = ""
    info_key: str = ""
    packet: dict = field(default_factory=dict)


@dataclass
class Context:
    """Everything the decision is a function of. Nothing is read from the world
    inside `decide`, so the same context always produces the same decision."""
    state: GoalState
    tree_hash: str
    scope_hash: str
    observations: dict = field(default_factory=dict)   # epoch_id -> Observation
    judge: dict | None = None                          # judge receipt, if any
    now: float = 0.0
    budget: dict = field(default_factory=dict)         # max_epochs, max_hours
    providers: tuple = ()                              # provider names available
    blocked_on: str = ""                               # an external condition, named
    engine: str = ""                                   # identity of the orchestrating code


def _budget_verdict(ctx: Context) -> str:
    eps = project_epochs(ctx.state)
    max_epochs = int(ctx.budget.get("max_epochs") or 0)
    if max_epochs and len(eps) >= max_epochs:
        return f"epoch budget spent: {len(eps)}/{max_epochs}"
    max_hours = float(ctx.budget.get("max_hours") or 0)
    started = ctx.budget.get("started_at")
    # `is not None`, never truthiness: a start time of 0.0 is a time, and reading
    # it as "no start time was given" silently switches the budget off.
    if max_hours and started is not None and (ctx.now - float(started)) / 3600.0 >= max_hours:
        return f"time budget spent: {(ctx.now - float(started)) / 3600.0:.1f}h of {max_hours}h"
    return ""


def _work_provider(ctx: Context) -> str:
    """Who can write code here, in order of preference. Capability, not brand:
    the first provider that can run unattended wins, and the human path is last
    because it needs a person."""
    for name in ("codex", "claude-headless", "claude-interactive"):
        if name in ctx.providers:
            return name
    return ""


def decide(ctx: Context) -> Decision:
    st = ctx.state
    eps = project_epochs(st)
    cv = project_convergence(st)

    # 1. An epoch that died between intent and effect is resolved FIRST: it is
    #    the only state where a run may exist that nothing is tracking.
    for e in eps.values():
        if e.state == "dispatching":
            return Decision(RECOVER, f"{e.epoch_id} recorded its intent and never its handle",
                            epoch_id=e.epoch_id)

    # 2. Ended epochs are harvested before anything new is started, so the next
    #    decision is made on what actually happened rather than on a guess.
    for e in eps.values():
        obs = ctx.observations.get(e.epoch_id)
        if e.state == "running":
            if obs is None or obs.state == OBS_UNKNOWN:
                return Decision(WAIT, f"{e.epoch_id}: could not observe it; "
                                      "an unreadable observation is not an ending",
                                epoch_id=e.epoch_id)
            if obs.state in (OBS_ENDED, OBS_LOST):
                return Decision(HARVEST, f"{e.epoch_id} ended {obs.outcome or obs.state}: "
                                         f"{obs.detail}", epoch_id=e.epoch_id)
            if obs.state == OBS_RUNNING:
                return Decision(WAIT, f"{e.epoch_id} is running: {obs.detail or 'in flight'}",
                                epoch_id=e.epoch_id)

    # 3. Closure. Nothing blocking does NOT mean converged: the judge decides.
    closure = goal_closure(st, ctx.tree_hash)
    if closure.may_close:
        if ctx.judge and ctx.judge.get("tree_hash") == ctx.tree_hash \
                and ctx.judge.get("revision") == st.revision and ctx.judge.get("verdict") == "PASS":
            return Decision(CONVERGED, "closure is clear and an independent judge re-ran the "
                                       "pinned gates at this tree")
        if ctx.judge and ctx.judge.get("verdict") not in (None, "PASS"):
            return Decision(ESCALATE, f"the judge refused: {ctx.judge.get('reason', '')}",
                            packet={"judge": ctx.judge})
        return Decision(READY_FOR_JUDGE, "nothing blocks closure; an independent judge must "
                                         "re-run the pinned gates before this converges")

    # 4. An external condition the Factory cannot resolve.
    if ctx.blocked_on:
        return Decision(BLOCKED, f"blocked on an external condition: {ctx.blocked_on}")

    spent = _budget_verdict(ctx)
    if spent:
        return Decision(ESCALATE, f"{spent}; the goal is not converged and needs a decision",
                        packet={"blocking": closure.blocking, "budget": ctx.budget})

    # 5. Work. The cheapest justified action first: an accepted obligation whose
    #    gate has not been run at THIS tree is evidence waiting to be collected,
    #    and running a gate is cheaper and more decisive than writing code.
    open_obs = [o for o in cv.obligations.values() if o.disposition == ACCEPTED]
    ungated = [o for o in open_obs
               if not any(e.spec.get("obligation") == o.identifier
                          and e.spec.get("tree_hash") == ctx.tree_hash
                          and e.provider == "gate" for e in eps.values())]
    if ungated and "gate" in ctx.providers:
        o = ungated[0]
        key = info_key(st.revision, [o.identifier], "gate", "initial", ctx.scope_hash,
                       engine=ctx.engine)
        if not any(e.info_key == key and e.outcome in UNSUCCESSFUL for e in eps.values()):
            return Decision(NEXT_EPOCH,
                            f"{o.identifier} ({o.plane}) has never been judged at this tree",
                            provider="gate", hypothesis="initial", info_key=key,
                            spec={"obligation": o.identifier, "gate": o.done_gate,
                                  "tree_hash": ctx.tree_hash, "plane": o.plane})

    # 6. A gate that ran and failed is new information: someone has to change
    #    the code. That is work, and work needs a work provider.
    failing = [o for o in open_obs
               if any(e.spec.get("obligation") == o.identifier and e.outcome in UNSUCCESSFUL
                      for e in eps.values())]
    provider = _work_provider(ctx)
    if failing and provider:
        o = failing[0]
        sig = f"gate-failed:{o.identifier}"
        key = info_key(st.revision, [o.identifier], provider, "new_failure_signature",
                       ctx.scope_hash, sig, engine=ctx.engine)
        if not any(e.info_key == key and e.outcome in UNSUCCESSFUL for e in eps.values()):
            return Decision(NEXT_EPOCH,
                            f"{o.identifier} has a gate that ran and failed; that is new "
                            "information and needs work",
                            provider=provider, hypothesis="new_failure_signature",
                            info_key=key,
                            spec={"obligation": o.identifier, "task": o.text,
                                  "tree_hash": ctx.tree_hash, "plane": o.plane})

    # 7. There ARE open gaps and nothing above could act on them. This is the
    #    empty-queue case, and it is the one that must never read as success.
    return Decision(ESCALATE,
                    "the goal is not converged and no justified action remains: "
                    + "; ".join(closure.blocking[:6]),
                    packet={"blocking": closure.blocking,
                            "providers": list(ctx.providers),
                            "note": "an empty queue is not convergence"})


def render(d: Decision) -> str:
    out = [f"{d.kind}: {d.reason}"]
    if d.epoch_id:
        out.append(f"  epoch    : {d.epoch_id}")
    if d.provider:
        out.append(f"  provider : {d.provider} (hypothesis {d.hypothesis})")
    if d.spec:
        out.append(f"  spec     : {d.spec}")
    if d.packet.get("blocking"):
        out.append("  blocking :")
        out += [f"    - {b}" for b in d.packet["blocking"][:8]]
    return "\n".join(out)
