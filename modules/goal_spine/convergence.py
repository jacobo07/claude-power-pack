#!/usr/bin/env python3
"""Goal convergence -- computed by GSD X's closure, never by the spine's opinion.

THE JUDGE IS NOT THE SPINE
--------------------------
`compute()` builds the Mission Contract with GSD X's own `contract.project`, then
asks GSD X's own `closure.project_closure` whether the mission may close. The
spine adds exactly two things closure cannot know, and nothing else:

  1. MISSING REQUIRED OBLIGATIONS ARE OPEN. Closure only sees the obligations it
     is handed; a missing store reads as `[]`, and `[]` blocks nothing
     (audit gap 3). The Goal declares which obligation ids prove it, so an id
     that is absent from the store is an open requirement, not an absent one.
  2. A REQUIRED OBLIGATION CLOSED WITHOUT A REASON IS OPEN. NOT_APPLICABLE,
     REJECTED and DEFERRED close an obligation in closure's arithmetic. On a
     requirement the Goal itself declared, that closure must say why, or it is
     a requirement quietly dropped.

Production Reality is not special-cased here. It is an ACCEPTED obligation whose
done-gate is the project's verifier, so closure's existing rule -- ACCEPTED and
unproven blocks -- is what holds it (audit gap 2: `production_reality` in
`project_closure` is display text, and relying on it would have made the spine
its own judge).

THE ONLY PATH TO CONVERGED
--------------------------
`apply_verdict()` is the single place a Goal becomes CONVERGED. It re-reads the
obligations at the moment of application and refuses when their digest no longer
matches the verdict's: a verdict computed before the state moved authorises
nothing (authorise at the point of effect, never at the point of observation
alone). It also refuses a verdict for another Goal or another revision.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from modules.gsd_x.mission import closure as gsdx_closure
from modules.gsd_x.mission import contract as gsdx_contract
from modules.gsd_x.mission import obligation as gsdx_obligation
from modules.gsd_x.mission import store as gsdx_store

from . import goal as gl

_CLOSED_NEEDS_REASON = frozenset({gsdx_obligation.NOT_APPLICABLE,
                                  gsdx_obligation.REJECTED,
                                  gsdx_obligation.DEFERRED})
_CONVERGEABLE_FROM = frozenset({gl.ACTIVE, gl.HARVESTING})


@dataclass(frozen=True)
class Verdict:
    goal_id: str
    revision: int
    converged: bool
    blocking: tuple[str, ...]
    residual_risk: tuple[str, ...]
    obligations_digest: str
    computed_at: str
    required: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["blocking"], d["residual_risk"], d["required"] = (
            list(self.blocking), list(self.residual_risk), list(self.required))
        return d


def load_obligations(goal: gl.Goal) -> list[gsdx_obligation.Obligation]:
    """Read this Goal's obligations from their owner. A corrupt store raises."""
    return gsdx_store.load(Path(goal.root), namespace=goal.goal_id)


def obligations_digest(obligations: list[gsdx_obligation.Obligation]) -> str:
    canon = json.dumps(sorted((o.to_dict() for o in obligations),
                              key=lambda d: d["id"]),
                       sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def compute(goal: gl.Goal) -> Verdict:
    obligations = load_obligations(goal)
    contract = gsdx_contract.project(Path(goal.root), intent=goal.intent,
                                     obligations=obligations)
    closure = gsdx_closure.project_closure(
        contract, obligations,
        explicit_backlog_empty=goal.explicit_backlog_empty)

    blocking = list(closure.blocking)
    by_id = {o.identifier: o for o in obligations}
    for rid in goal.required_obligation_ids:
        o = by_id.get(rid)
        if o is None:
            blocking.append(f"{rid} is a declared requirement and is absent from the "
                            "obligation store -- absent is open, never satisfied")
        elif o.disposition in _CLOSED_NEEDS_REASON and not o.disposition_reason.strip():
            blocking.append(f"{rid} is a declared requirement closed as "
                            f"{o.disposition} with no reason")

    return Verdict(
        goal_id=goal.goal_id, revision=goal.revision,
        converged=closure.may_close and not blocking,
        blocking=tuple(blocking), residual_risk=tuple(closure.residual_risk),
        obligations_digest=obligations_digest(obligations),
        computed_at=gl.now_iso(), required=tuple(goal.required_obligation_ids),
    )


def apply_verdict(goal: gl.Goal, verdict: Verdict) -> None:
    """The only path to CONVERGED. Re-validates at the point of effect."""
    if not isinstance(verdict, Verdict):
        raise PermissionError("CONVERGED requires a Verdict produced by convergence.compute")
    if verdict.goal_id != goal.goal_id:
        raise PermissionError(f"verdict is for {verdict.goal_id}, not {goal.goal_id}")
    if verdict.revision != goal.revision:
        raise PermissionError(
            f"verdict judged revision {verdict.revision}; the Goal is at "
            f"{goal.revision} -- its target moved")
    if not verdict.converged:
        raise PermissionError("the verdict says the Goal has not converged: "
                              + "; ".join(verdict.blocking))
    if goal.state not in _CONVERGEABLE_FROM:
        raise PermissionError(f"a Goal in {goal.state} cannot converge; "
                              f"allowed from {sorted(_CONVERGEABLE_FROM)}")
    # RECOMPUTE, never trust the token. The verdict handed in is a claim; closure,
    # run again now, is the judge. An earlier version compared only the digest and
    # read `verdict.converged` -- so a caller who flipped that flag on a genuinely
    # open verdict (frozen blocks `v.converged = True`, not object.__setattr__)
    # converged a Goal whose obligations had not moved. Found by the independent
    # mutation probe: removing `frozen=True` survived, because nothing downstream
    # depended on the flag being honest.
    fresh = compute(goal)
    if fresh.obligations_digest != verdict.obligations_digest:
        raise PermissionError("the obligations changed after the verdict was computed; "
                              "recompute before converging")
    if not fresh.converged:
        raise PermissionError("recomputed at the point of effect, the Goal has not "
                              "converged: " + "; ".join(fresh.blocking))
    goal.state = gl.CONVERGED
    goal.converged_receipt = verdict.to_dict()
    goal.updated_at = gl.now_iso()
