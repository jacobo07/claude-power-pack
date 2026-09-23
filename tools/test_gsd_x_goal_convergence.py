#!/usr/bin/env python3
"""V-gates for convergence planes, goal transitions and goal closure (C2/C3).

The positive control is load-bearing: a closure that refused every goal would
pass every refusal below. So the file first proves a fully evidenced goal DOES
close, then removes one piece of evidence at a time.

    python tools/test_gsd_x_goal_convergence.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import contract as gc     # noqa: E402
from modules.gsd_x.goal import convergence as cv  # noqa: E402
from modules.gsd_x.goal import log as gl          # noqa: E402
from modules.gsd_x.mission import closure as mcl  # noqa: E402

REPO = "b" * 40
TREE = "t" * 40
PIN = (("tools/gate.py", "1" * 64),)


def fresh(base: Path, gid: str, applicable_optional=()):
    lg = gl.GoalLog(REPO, gid, base=base)
    gc.declare(lg, f"goal {gid}", ["it works"], [], {"paths": ["src"]})
    for plane in cv.PLANES:
        s = gc.project(lg)
        if plane in cv.ALWAYS or plane in applicable_optional:
            cv.set_plane(lg, s, plane, True, "", "t")
        else:
            cv.set_plane(lg, s, plane, False, "no runtime/transfer claim in this goal", "t")
    for plane in (cv.OUTCOME, cv.EVIDENCE, cv.REGRESSION, cv.UCR_CIF_LEARNING,
                  *applicable_optional):
        # REALITY declares its class, like any real registration must. The
        # fixture used to omit it and lean on the sweep inferring `in_game` from
        # the plane, which is the defect this fixture would otherwise reproduce.
        cv.accept_obligation(lg, gc.project(lg), f"ob-{plane.lower()}", plane, "x",
                             "python tools/gate.py", PIN, "t",
                             gate_class="in_game" if plane in cv.REALITY_PLANES else "unit")
    return lg


def verdict(state, gate_class="unit", tree=TREE, rev=None, pin=PIN, exit_status=0):
    return mcl.Verdict("tools/gate.py", exit_status, "12 passed", tree,
                       state.revision if rev is None else rev, gate_class, pin)


def satisfy_all(lg, gate_class_for=None):
    s = gc.project(lg)
    for oid, o in cv.project_convergence(s).obligations.items():
        if o.disposition == cv.ACCEPTED:
            s = gc.project(lg)
            gcls = (gate_class_for or {}).get(o.plane, "unit")
            res = cv.satisfy(lg, s, oid, verdict(s, gcls), "t")
            assert res.allowed, res.reason


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

    def refused(g, fn, ev):
        try:
            fn()
            bad(g, "accepted")
        except gl.GoalLogError:
            ok(g, ev)

    base = Path(tempfile.mkdtemp(prefix="gsdx_conv_"))

    # --- positive control ------------------------------------------------------
    lg = fresh(base, "g-happy")
    satisfy_all(lg)
    c = cv.goal_closure(gc.project(lg), TREE)
    check("V-CONV-POSITIVE-CONTROL", c.may_close and not c.blocking,
          "a fully evidenced goal closes", f"blocking={c.blocking}")

    # --- planes ------------------------------------------------------------------
    lg2 = gl.GoalLog(REPO, "g-unjudged", base=base)
    gc.declare(lg2, "unjudged")
    c2 = cv.goal_closure(gc.project(lg2), TREE)
    check("V-CONV-UNKNOWN-BLOCKS", sum("never judged" in b for b in c2.blocking) == len(cv.PLANES),
          "every never-judged plane blocks closure", f"blocking={c2.blocking}")
    s2 = gc.project(lg2)
    refused("V-CONV-NA-NEEDS-REASON",
            lambda: cv.set_plane(lg2, s2, cv.TRANSFER, False, "  ", "t"),
            "N/A without a reason refused")
    refused("V-CONV-ALWAYS-NOT-NA",
            lambda: cv.set_plane(lg2, s2, cv.OUTCOME, False, "we are sure", "t"),
            "OUTCOME cannot be declared N/A, reason or not")
    refused("V-CONV-GATE-REQUIRED",
            lambda: cv.accept_obligation(lg2, s2, "o1", cv.OUTCOME, "x", " ", PIN, "t"),
            "an obligation with no done gate refused")
    refused("V-CONV-PIN-REQUIRED",
            lambda: cv.accept_obligation(lg2, s2, "o1", cv.OUTCOME, "x", "gate", (), "t"),
            "an obligation whose gate files are not pinned refused")

    lg3 = fresh(base, "g-empty-plane", applicable_optional=())
    s3 = gc.project(lg3)
    lg3.append(s3.last_seq + 1, cv.PLANE_SET, {"plane": cv.TRANSFER, "applicable": True,
                                               "reason": ""}, "t")
    satisfy_all(lg3)
    c3 = cv.goal_closure(gc.project(lg3), TREE)
    check("V-CONV-APPLICABLE-NEEDS-OBLIGATION",
          any("TRANSFER applies and has no obligation" in b for b in c3.blocking),
          "an applicable plane with no obligation blocks", f"blocking={c3.blocking}")

    # --- transitions ---------------------------------------------------------------
    lg4 = fresh(base, "g-trans", applicable_optional=(cv.REALITY,))
    s4 = gc.project(lg4)
    r = cv.satisfy(lg4, s4, "ob-outcome", None, "t", narrative="I finished it")
    check("V-CONV-NARRATIVE-NOT-AUTHORITY", not r.allowed and "claim about itself" in r.reason,
          "executor narrative refused (mission rule reused)", r.reason)
    r = cv.satisfy(lg4, gc.project(lg4), "ob-outcome", verdict(s4, exit_status=1), "t")
    check("V-CONV-FAILED-GATE", not r.allowed and "returned 1" in r.reason,
          "a failed gate refuses with its own reason", r.reason)
    r = cv.satisfy(lg4, gc.project(lg4), "ob-reality", verdict(s4, "unit"), "t")
    check("V-CONV-REALITY-NEEDS-RUNTIME", not r.allowed and "in_game/live" in r.reason,
          "a unit-test verdict cannot prove REALITY", r.reason)
    r = cv.satisfy(lg4, gc.project(lg4), "ob-reality", verdict(s4, "in_game"), "t")
    check("V-CONV-REALITY-ACCEPTS-RUNTIME", r.allowed,
          "an in_game verdict proves REALITY (control)", r.reason)
    r = cv.satisfy(lg4, gc.project(lg4), "ob-evidence", verdict(s4, tree=""), "t")
    check("V-CONV-TREE-REQUIRED", r.outcome == mcl.UNJUDGEABLE,
          "a verdict with no tree is unjudgeable, not refused, not allowed", r.reason)
    r = cv.satisfy(lg4, gc.project(lg4), "ob-evidence", verdict(s4, rev="deadbeef"), "t")
    check("V-CONV-VERDICT-REVISION", not r.allowed and "revision deadbeef" in r.reason,
          "a verdict about another revision refused", r.reason)
    r = cv.satisfy(lg4, gc.project(lg4), "ob-evidence",
                   verdict(s4, pin=(("tools/gate.py", "2" * 64),)), "t")
    check("V-CONV-GATE-PIN", not r.allowed and "not the gate pinned" in r.reason,
          "a gate whose files changed since acceptance refused", r.reason)

    # --- closure --------------------------------------------------------------------
    lg5 = fresh(base, "g-tree")
    satisfy_all(lg5)
    c5 = cv.goal_closure(gc.project(lg5), "u" * 40)
    check("V-CONV-CLOSE-AT-OTHER-TREE", not c5.may_close and
          any("not at the tree being closed" in b for b in c5.blocking),
          "evidence from another tree does not close this one", f"blocking={c5.blocking}")
    c5b = cv.goal_closure(gc.project(lg5), TREE, open_epochs=["ep-1"])
    check("V-CONV-OPEN-EPOCH", not c5b.may_close and "epoch ep-1 is still open" in c5b.blocking,
          "an open epoch blocks closure", f"blocking={c5b.blocking}")

    lg6 = fresh(base, "g-fail")
    satisfy_all(lg6)
    cv.record_failure(lg6, gc.project(lg6), "f1", "codex epoch lost mid-run", "t")
    c6 = cv.goal_closure(gc.project(lg6), TREE)
    check("V-CONV-FAILURE-BLOCKS", not c6.may_close and any("f1" in b for b in c6.blocking),
          "an undispositioned failure blocks closure", f"blocking={c6.blocking}")
    s6 = gc.project(lg6)
    refused("V-CONV-FAILURE-DISPOSITION-REASON",
            lambda: cv.disposition_failure(lg6, s6, "f1", "fixed", " ", "t"),
            "a failure disposition without a reason refused")
    refused("V-CONV-FAILURE-DISPOSITION-KIND",
            lambda: cv.disposition_failure(lg6, s6, "f1", "ignored", "meh", "t"),
            "an unknown failure disposition refused")
    cv.disposition_failure(lg6, s6, "f1", "regression_added", "chaos case C14-2", "t")
    check("V-CONV-FAILURE-DISPOSITIONED", cv.goal_closure(gc.project(lg6), TREE).may_close,
          "a dispositioned failure no longer blocks", "still blocked")

    # --- retiring an obligation that will never be proven -------------------------------
    lg8 = fresh(base, "g-retire")
    satisfy_all(lg8)
    s8 = gc.project(lg8)
    refused("V-CONV-OB-DISPOSITION-NOT-SATISFIED",
            lambda: cv.disposition_obligation(lg8, s8, "ob-outcome", cv.SATISFIED,
                                              "the gate passed, honest", "t"),
            "SATISFIED may not be declared on an obligation; only a verdict reaches it")
    refused("V-CONV-OB-DISPOSITION-NEEDS-REASON",
            lambda: cv.disposition_obligation(lg8, s8, "ob-outcome", cv.REJECTED, " ", "t"),
            "retiring an obligation without a reason refused")
    refused("V-CONV-OB-DISPOSITION-UNKNOWN-OB",
            lambda: cv.disposition_obligation(lg8, s8, "ob-nope", cv.REJECTED, "because", "t"),
            "retiring an obligation that does not exist refused")

    # Retiring the only obligation on an applicable plane must REOPEN that plane,
    # not close it. Without this the writer above is a way to converge a goal by
    # deleting the thing that would have proven it.
    cv.disposition_obligation(lg8, gc.project(lg8), "ob-outcome", cv.REJECTED,
                              "its gate pin names a path the commit moved", "t")
    c8 = cv.goal_closure(gc.project(lg8), TREE)
    check("V-CONV-RETIRED-IS-NOT-COVERAGE",
          not c8.may_close and any("retired unproven" in b for b in c8.blocking),
          "retiring the last obligation on an applicable plane blocks that plane",
          f"blocking={c8.blocking}")
    r = cv.satisfy(lg8, gc.project(lg8), "ob-outcome", verdict(gc.project(lg8)), "t")
    check("V-CONV-RETIRED-STAYS-RETIRED", not r.allowed and "no satisfied state" in r.reason,
          "a retired obligation cannot be proven afterwards (mission rule reused)", r.reason)

    # The control: a successor pinned to what exists now closes it. A pair that
    # only ever refuses would pass every assertion above.
    cv.accept_obligation(lg8, gc.project(lg8), "ob-outcome-2", cv.OUTCOME, "x",
                         "python tools/gate.py", PIN, "t")
    satisfy_all(lg8)
    c8b = cv.goal_closure(gc.project(lg8), TREE)
    check("V-CONV-RETIRED-WITH-SUCCESSOR-CLOSES", c8b.may_close,
          "a retired obligation replaced by a proven successor closes", f"blocking={c8b.blocking}")

    # --- revision change --------------------------------------------------------------
    lg7 = fresh(base, "g-rev")
    satisfy_all(lg7)
    s7 = gc.project(lg7)
    s7 = gc.revise(lg7, s7.last_seq + 1, s7.intent, s7.acceptance + ["and it is fast"],
                   s7.constraints, s7.scope)
    c7 = cv.goal_closure(s7, TREE)
    check("V-CONV-REVISION-STALES-EVIDENCE", not c7.may_close and
          any("proven under revision" in b for b in c7.blocking),
          "a new revision stops old proof from closing", f"blocking={c7.blocking}")
    r = cv.satisfy(lg7, s7, "ob-outcome", verdict(s7), "t")
    check("V-CONV-REVISION-NEEDS-CARRY", not r.allowed and "carry it forward" in r.reason,
          "an old-revision obligation cannot be re-proven until carried", r.reason)
    for oid in cv.project_convergence(s7).obligations:
        cv.carry_obligation(lg7, gc.project(lg7), oid, "same meaning under the new criterion", "t")
    satisfy_all(lg7)
    check("V-CONV-REVISION-CARRIED", cv.goal_closure(gc.project(lg7), TREE).may_close,
          "carried and re-proven obligations close the new revision", "still blocked")

    total = len(passes) + len(fails)
    print(f"\nGSDX_GOAL_CONV_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
