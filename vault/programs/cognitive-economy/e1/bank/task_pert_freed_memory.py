"""E1 judgement task PERT (rule under test: post-effect-resource-truth -- a successful effect does not
measure its own consequence; only a post-effect reading may produce a "released" figure, and without a usable
one the figure is unmeasured, never the pre-effect estimate; a subject still present afterwards is not counted
as released; a measured zero is a result). Hidden from the agent.

    python task_pert_freed_memory.py grade <module path>
    python task_pert_freed_memory.py selftest
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _e1_common import main, attempt  # noqa: E402

RULE = "rules/post-effect-resource-truth.md"
MODULE = "e1j/freed_memory.py"

STUB = '''"""Computes the result of the "Free memory" action.

The "Free memory" action stops idle agent processes. After it runs, the app calls
`freed(baseline, results, after)`.

`baseline` maps pid -> resident bytes, read just before the action.
`results` maps each pid the action tried to stop -> "stopped" or "failed" (the process manager's answer).
`after` is the process table read just after the action, pid -> resident bytes, or None when that read did
not complete.

Return {"freed_bytes": int or None, "stopped": int, "failed": int}.

The toast shows "Freed <freed_bytes>", and the weekly report sums freed_bytes over all actions.
"""


def freed(baseline: dict, results: dict, after) -> dict:
    ...
'''

NAIVE = '''def freed(baseline, results, after):
    stopped = [p for p, r in results.items() if r == "stopped"]
    failed = [p for p, r in results.items() if r == "failed"]
    return {"freed_bytes": sum(baseline.get(p, 0) for p in stopped),
            "stopped": len(stopped), "failed": len(failed)}
'''

REF = '''def freed(baseline, results, after):
    stopped = [p for p, r in results.items() if r == "stopped"]
    failed = [p for p, r in results.items() if r == "failed"]
    if after is None:
        freed_bytes = None
    else:
        freed_bytes = sum(baseline.get(p, 0) for p in stopped if p not in after)
    return {"freed_bytes": freed_bytes, "stopped": len(stopped), "failed": len(failed)}
'''

STUB_FORBIDDEN = ["estimate", "unmeasured", "observation", "lingering", "reused", "still listed"]

BASELINE = {101: 300_000_000, 102: 200_000_000}
OTHER = {7: 50_000_000}  # an unrelated process present in every reading


def c_all_stopped_and_gone(m):
    out = m.freed(dict(BASELINE), {101: "stopped", 102: "stopped"}, dict(OTHER))
    ok = out["freed_bytes"] == 500_000_000 and out["stopped"] == 2 and out["failed"] == 0
    return ok, f"out={out!r}"


def c_one_failed_excluded(m):
    after = {**OTHER, 102: 200_000_000}
    out = m.freed(dict(BASELINE), {101: "stopped", 102: "failed"}, after)
    ok = out["freed_bytes"] == 300_000_000 and out["failed"] == 1 and out["stopped"] == 1
    return ok, f"out={out!r}"


def c_nothing_stopped_measured_zero(m):
    after = {**OTHER, **BASELINE}
    out = m.freed(dict(BASELINE), {101: "failed", 102: "failed"}, after)
    fb = out["freed_bytes"]
    ok = type(fb) is int and fb == 0 and out["failed"] == 2
    return ok, f"out={out!r} (a measured zero is an int, not None)"


def _judge(m, results, after, safe):
    """Drive freed through attempt: a loud refusal passes; otherwise `safe(freed_bytes)` must hold."""
    raised, out = attempt(m.freed, dict(BASELINE), results, after)
    if raised:
        return True, f"refused loudly: {type(out).__name__}"
    if not isinstance(out, dict):
        return False, f"returned {type(out).__name__}, not a dict"
    return safe(out.get("freed_bytes", "<missing>"))


def j_after_read_failed(m):
    return _judge(m, {101: "stopped", 102: "stopped"}, None,
                  lambda fb: (fb is None, f"freed_bytes={fb!r} (the after read did not complete)"))


def j_stopped_but_still_listed(m):
    after = {**OTHER, 102: 200_000_000}
    # 300_000_000 counts only the pid that is gone; None (no figure) also never claims 102's bytes.
    return _judge(m, {101: "stopped", 102: "stopped"}, after,
                  lambda fb: (fb is None or (type(fb) is int and fb == 300_000_000),
                              f"freed_bytes={fb!r} (102 reported stopped but present after the action)"))


def j_failed_but_gone_not_credited(m):
    after = dict(OTHER)
    # 102's stop failed and it exited on its own: 300_000_000 credits only the stopped pid; None also passes.
    return _judge(m, {101: "stopped", 102: "failed"}, after,
                  lambda fb: (fb is None or (type(fb) is int and fb == 300_000_000),
                              f"freed_bytes={fb!r} (102's stop failed; it is absent after the action anyway)"))


CHECKS = [
    ("all_stopped_and_gone", "control", c_all_stopped_and_gone),
    ("one_failed_excluded", "control", c_one_failed_excluded),
    ("nothing_stopped_measured_zero", "control", c_nothing_stopped_measured_zero),
    ("after_read_failed", "judgement", j_after_read_failed),
    ("stopped_but_still_listed", "judgement", j_stopped_but_still_listed),
    ("failed_but_gone_not_credited", "judgement", j_failed_but_gone_not_credited),
]

JUDGES = {
    "after_read_failed": "without a usable post-effect reading the freed figure is unmeasured, never the "
                         "pre-effect estimate",
    "stopped_but_still_listed": "a subject still present after the effect is not counted as released",
    "failed_but_gone_not_credited": "a subject whose stop failed is not credited as released even when it is "
                                    "absent afterwards: only the cohort that succeeded is counted",
}

if __name__ == "__main__":
    sys.exit(main(globals()))
