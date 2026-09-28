"""V-ADAPT-* gates: genesis-task-adaptation CONNECTED to Goal Spine revisions (T9 item 32).

A revision may add; one that drops an acceptance criterion or a constraint is refused unless
the actor states why, and then the dropped items and the reason are recorded ON the revision.
Rewording counts as dropping the old words (exact comparison, deliberately conservative: a
reworded criterion may be a weaker one, and only a person can say it is not).

Not LIVE: contract.revise has no production caller (tests only), and the Goal Spine engine has
no live invoker (see test_task_ledger_seam). The rule is in the owner, waiting for its entrance.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.gsd_x.goal import contract as gc  # noqa: E402
from modules.gsd_x.goal import log as gl       # noqa: E402
from modules.gsd_x.goal.log import GoalLogError  # noqa: E402

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def goal(base: Path, gid: str):
    lg = gl.GoalLog("c" * 40, gid, base=base)
    gc.declare(lg, "ship the arena", ["arena loads", "no crash for 10 minutes"], ["no new dependency"],
               {"paths": ["src"]})
    return lg


def refused(fn) -> str:
    try:
        fn()
    except GoalLogError as exc:
        return str(exc)
    return ""


def main() -> int:
    base = Path(tempfile.mkdtemp(prefix="adapt-"))

    lg = goal(base, "g-add")
    s = gc.project(lg)
    s2 = gc.revise(lg, s.last_seq + 1, s.intent, s.acceptance + ["hotbar observed"], s.constraints, s.scope)
    last = s2.events[-1].data
    check("V-ADAPT-ADD-ALLOWED", "weakened" not in last and len(s2.acceptance) == 3,
          "adding a criterion needs no justification and records none")

    lg = goal(base, "g-drop")
    s = gc.project(lg)
    why = refused(lambda: gc.revise(lg, s.last_seq + 1, s.intent, ["arena loads"], s.constraints, s.scope))
    check("V-ADAPT-DROP-REFUSED", "weakens" in why and "no crash for 10 minutes" in why, why[:120])
    check("V-ADAPT-DROP-NOTHING-WRITTEN", gc.project(lg).revision == s.revision, "the refused revision left no event")

    why = refused(lambda: gc.revise(lg, s.last_seq + 1, s.intent, s.acceptance, [], s.scope))
    check("V-ADAPT-CONSTRAINT-REFUSED", "constraints" in why, why[:120])

    why = refused(lambda: gc.revise(lg, s.last_seq + 1, s.intent, ["arena loads", "no crash for 5 minutes"],
                                    s.constraints, s.scope))
    check("V-ADAPT-REWORD-IS-DROP", "no crash for 10 minutes" in why, "a reworded criterion needs a stated reason too")

    s3 = gc.revise(lg, s.last_seq + 1, s.intent, ["arena loads"], s.constraints, s.scope,
                   actor="founder", weakening_reason="the soak test moves to the next goal")
    ev = s3.events[-1]
    check("V-ADAPT-JUSTIFIED-RECORDED",
          ev.data.get("weakened") == {"acceptance": ["no crash for 10 minutes"]}
          and ev.data.get("weakening_reason") == "the soak test moves to the next goal" and ev.actor == "founder",
          f"what was dropped, why and by whom stay on the revision: {ev.data.get('weakened')}")
    why = refused(lambda: gc.revise(lg, s3.last_seq + 1, s3.intent, [], s3.constraints, s3.scope,
                                    weakening_reason="   "))
    check("V-ADAPT-BLANK-REASON", "weakens" in why, "a whitespace reason is no reason")
    print(f"ADAPT_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
