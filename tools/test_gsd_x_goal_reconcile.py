#!/usr/bin/env python3
"""V-gates for the Goal Reconciler's decision table (C10).

Every branch is driven, and the load-bearing ones are the refusals: an empty
queue must never produce CONVERGED, and clear closure must produce
READY_FOR_JUDGE rather than convergence on the reconciler's own say-so.

    python tools/test_gsd_x_goal_reconcile.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import contract as gc       # noqa: E402
from modules.gsd_x.goal import convergence as cv    # noqa: E402
from modules.gsd_x.goal import epoch as ep          # noqa: E402
from modules.gsd_x.goal import log as gl            # noqa: E402
from modules.gsd_x.goal import reconcile as rc      # noqa: E402
from modules.gsd_x.mission import closure as mcl    # noqa: E402

REPO = "e" * 40
TREE = "git:" + "f" * 40
SCOPE = "scope1"
PIN = (("tools/gate.py", "9" * 64),)
ALL_PROV = ("gate", "codex", "claude-headless")


def build(base: Path, gid: str, *, with_obligation=True, satisfy=False):
    lg = gl.GoalLog(REPO, gid, base=base)
    gc.declare(lg, f"goal {gid}", ["it works"], [], {"paths": ["src"]})
    for plane in cv.PLANES:
        s = gc.project(lg)
        cv.set_plane(lg, s, plane, plane in cv.ALWAYS, "" if plane in cv.ALWAYS
                     else "not claimed by this goal", "t")
    if with_obligation:
        for plane in (cv.OUTCOME, cv.EVIDENCE, cv.REGRESSION, cv.UCR_CIF_LEARNING):
            cv.accept_obligation(lg, gc.project(lg), f"ob-{plane.lower()}", plane, "do it",
                                 "python tools/gate.py", PIN, "t")
    if satisfy:
        for oid in list(cv.project_convergence(gc.project(lg)).obligations):
            s = gc.project(lg)
            v = mcl.Verdict("tools/gate.py", 0, "ok", TREE, s.revision, "unit", PIN)
            cv.satisfy(lg, s, oid, v, "t")
    return lg


def ctx_for(lg, **kw):
    st = gc.project(lg)
    return rc.Context(state=st, tree_hash=kw.pop("tree", TREE), scope_hash=SCOPE,
                      providers=kw.pop("providers", ALL_PROV), now=kw.pop("now", 1000.0), **kw)


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def ok(g, ev):
        passes.append(g)
        print(f"  PASS {g}: {ev}")

    def bad(g, why):
        fails.append(g)
        print(f"  FAIL {g}: {why}")

    def check(g, cond, ev, why):
        (ok if cond else bad)(g, ev if cond else why)

    base = Path(tempfile.mkdtemp(prefix="gsdx_rc_"))

    # 1. an open obligation nothing has judged -> run its gate
    lg = build(base, "g-1")
    d = rc.decide(ctx_for(lg))
    check("V-RC-NEXT-GATE", d.kind == rc.NEXT_EPOCH and d.provider == "gate"
          and d.spec["obligation"].startswith("ob-"),
          f"an unjudged obligation dispatches its gate ({d.spec.get('obligation')})",
          rc.render(d))

    # 2. a dispatched-but-unhandled epoch is recovered before anything else
    st = gc.project(lg)
    e = ep.begin(lg, st, "gate", {"obligation": "ob-outcome"}, d.info_key, "initial", "t")
    d2 = rc.decide(ctx_for(lg))
    check("V-RC-RECOVER-FIRST", d2.kind == rc.RECOVER and d2.epoch_id == e.epoch_id,
          "an epoch with intent and no handle is resolved first", rc.render(d2))

    # 3. running -> WAIT; ended -> HARVEST; unobservable -> WAIT (never an ending)
    ep.mark_running(lg, gc.project(lg), e.epoch_id, {"pid": 1}, "t")
    d3 = rc.decide(ctx_for(lg, observations={e.epoch_id: ep.Observation(ep.OBS_RUNNING)}))
    check("V-RC-WAIT", d3.kind == rc.WAIT, "a running epoch is waited on", rc.render(d3))
    d4 = rc.decide(ctx_for(lg, observations={e.epoch_id: ep.Observation(ep.OBS_UNKNOWN)}))
    check("V-RC-UNKNOWN-IS-NOT-AN-ENDING", d4.kind == rc.WAIT,
          "an observation we could not make does not end an epoch", rc.render(d4))
    d5 = rc.decide(ctx_for(lg, observations={
        e.epoch_id: ep.Observation(ep.OBS_ENDED, ep.COMPLETED, "exit 0")}))
    check("V-RC-HARVEST", d5.kind == rc.HARVEST and d5.epoch_id == e.epoch_id,
          "an ended epoch is harvested before anything new starts", rc.render(d5))
    check("V-RC-DONE-IS-NOT-CONVERGED", d5.kind != rc.CONVERGED,
          "a provider reporting COMPLETED does not converge the goal", rc.render(d5))

    # 4. a failed gate is new information -> work provider
    ep.end(lg, gc.project(lg), e.epoch_id, ep.FAILED, "gate exited 1", "t")
    d6 = rc.decide(ctx_for(lg))
    check("V-RC-FAILED-GATE-NEEDS-WORK",
          d6.kind == rc.NEXT_EPOCH and d6.provider == "codex"
          and d6.hypothesis == "new_failure_signature",
          "a gate that ran and failed dispatches work with a named hypothesis", rc.render(d6))
    check("V-RC-PREFERS-UNATTENDED", d6.provider == "codex",
          "the unattended provider is preferred over the one needing a person", d6.provider)
    d6b = rc.decide(ctx_for(lg, providers=("gate", "claude-interactive")))
    check("V-RC-FALLS-BACK-TO-HUMAN", d6b.provider == "claude-interactive",
          "with no unattended provider, the human path is chosen rather than nothing",
          rc.render(d6b))

    # 5. no provider can act -> ESCALATE, never CONVERGED (the empty-queue rule)
    d7 = rc.decide(ctx_for(lg, providers=()))
    check("V-RC-EMPTY-QUEUE-IS-NOT-SUCCESS",
          d7.kind == rc.ESCALATE and "empty queue is not convergence" in str(d7.packet),
          "nothing runnable and gaps open escalates; there is no path to CONVERGED",
          rc.render(d7))

    # 6. clear closure -> READY_FOR_JUDGE, not CONVERGED
    lg2 = build(base, "g-2", satisfy=True)
    d8 = rc.decide(ctx_for(lg2))
    check("V-RC-CLOSURE-NEEDS-JUDGE", d8.kind == rc.READY_FOR_JUDGE,
          "nothing blocking is not convergence: an independent judge must run", rc.render(d8))
    st2 = gc.project(lg2)
    d9 = rc.decide(ctx_for(lg2, judge={"tree_hash": TREE, "revision": st2.revision,
                                       "verdict": "PASS"}))
    check("V-RC-CONVERGED-WITH-JUDGE", d9.kind == rc.CONVERGED,
          "a judge receipt at this tree and revision converges the goal (control)",
          rc.render(d9))
    d10 = rc.decide(ctx_for(lg2, judge={"tree_hash": "git:other", "revision": st2.revision,
                                        "verdict": "PASS"}))
    check("V-RC-JUDGE-MUST-MATCH-TREE", d10.kind == rc.READY_FOR_JUDGE,
          "a judge receipt about another tree does not converge this one", rc.render(d10))
    d11 = rc.decide(ctx_for(lg2, judge={"tree_hash": TREE, "revision": st2.revision,
                                        "verdict": "REFUSED", "reason": "gate file changed"}))
    check("V-RC-JUDGE-REFUSAL-ESCALATES", d11.kind == rc.ESCALATE,
          "a judge that refused escalates rather than retrying itself", rc.render(d11))

    # 7. external condition and budget
    d12 = rc.decide(ctx_for(lg, blocked_on="the Owner's HR-04 phrase for a production write"))
    check("V-RC-BLOCKED-NAMES-CONDITION",
          d12.kind == rc.BLOCKED and "HR-04" in d12.reason,
          "BLOCKED names the external condition", rc.render(d12))
    d13 = rc.decide(ctx_for(lg, budget={"max_epochs": 1}))
    check("V-RC-BUDGET-ESCALATES",
          d13.kind == rc.ESCALATE and "budget spent" in d13.reason,
          "a spent budget escalates with the open gaps attached", rc.render(d13))
    d14 = rc.decide(ctx_for(lg, budget={"max_hours": 2, "started_at": 0.0}, now=8000.0))
    check("V-RC-TIME-BUDGET", d14.kind == rc.ESCALATE and "time budget" in d14.reason,
          "a spent time budget escalates", rc.render(d14))

    # 8. determinism
    c = ctx_for(lg)
    check("V-RC-DETERMINISTIC", rc.decide(c).kind == rc.decide(c).kind
          and rc.decide(c).reason == rc.decide(c).reason,
          "the same context always produces the same decision", "the decision moved")

    # 9. a commit moves the tree: proof taken elsewhere is open work HERE.
    #    `lg2`'s obligations are all SATISFIED at TREE and d8 above proves that
    #    closes -- the control that stops this pair passing by refusing always.
    MOVED = "git:" + "a" * 40
    d15 = rc.decide(ctx_for(lg2, tree=MOVED))
    check("V-RC-REGATE-AFTER-TREE-MOVES",
          d15.kind == rc.NEXT_EPOCH and d15.provider == "gate"
          and "was proven at tree" in d15.reason,
          f"evidence from another tree re-runs its gate here: {d15.reason[:90]}",
          rc.render(d15))
    check("V-RC-REGATE-IS-NOT-AN-ESCALATION", d15.kind != rc.ESCALATE,
          "saving your work does not strand the goal", rc.render(d15))
    st2b = gc.project(lg2)
    st2b = gc.revise(lg2, st2b.last_seq + 1, st2b.intent, st2b.acceptance + ["and fast"],
                     st2b.constraints, st2b.scope)
    d16 = rc.decide(rc.Context(state=st2b, tree_hash=TREE, scope_hash=SCOPE,
                               providers=ALL_PROV, now=1000.0))
    check("V-RC-REGATE-AFTER-REVISION", d16.kind == rc.NEXT_EPOCH,
          "proof about an older revision is open work too", rc.render(d16))

    # 10. an obligation proven elsewhere needs its GATE re-run, never a coder:
    #     re-running a gate is cheap and decisive, writing code against a passing
    #     gate is neither.
    lg3 = build(base, "g-regate-work", satisfy=True)
    st3 = gc.project(lg3)
    k = ep.info_key(st3.revision, ["ob-outcome"], "gate", "initial", SCOPE)
    e3 = ep.begin(lg3, st3, "gate", {"obligation": "ob-outcome"}, k, "initial", "t")
    ep.mark_running(lg3, gc.project(lg3), e3.epoch_id, {"pid": 2}, "t")
    ep.end(lg3, gc.project(lg3), e3.epoch_id, ep.FAILED, "gate exited 1", "t")
    d17 = rc.decide(ctx_for(lg3, tree=MOVED, providers=("codex",)))
    check("V-RC-REGATE-IS-NOT-CODE-WORK", d17.provider != "codex",
          "a satisfied-elsewhere obligation is not sent to a work provider", rc.render(d17))

    total = len(passes) + len(fails)
    print(f"\nGSDX_RECONCILE_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
