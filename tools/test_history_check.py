#!/usr/bin/env python3
"""V-HIST-* gates for modules/history_check (UWCP assimilation R3).

Every checker gets a history it must FAIL and a sibling it must PASS. The end-to-end
case builds its history from two independent sources -- the real LeaseStore journal
and a fenced resource's own accept/refuse log -- so the verdict is not the subject
grading itself.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.history_check import (FAIL, PASS, UNKNOWN, HistoryError, compose,  # noqa: E402
                                   from_lease_journal, unbridled_optimism)
from modules.history_check import checkers as C  # noqa: E402
from modules.lease import LeaseStore  # noqa: E402

passes = fails = 0


def check(gate, cond, good, bad):
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {good}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {bad}")


def H(*ops):
    return [{"index": i, **op} for i, op in enumerate(ops)]


def ok(f, **v):
    return {"type": "ok", "f": f, "value": v}


def info(f, **v):
    return {"type": "info", "f": f, "value": v}


def fail(f, **v):
    return {"type": "fail", "f": f, "value": v}


def pair(gate, checker, bad, good):
    vb, vg = checker(bad), checker(good)
    check(gate, vb.valid == FAIL and vg.valid == PASS and vb.witness,
          f"red history FAILs with a witness ({vb.detail}); green sibling PASSes",
          f"bad={vb} good={vg}")


def main() -> int:
    pair("V-HIST-ONE-OWNER", C.AtMostOneValidOwner,
         H(ok("dispatch", lease_id="A", classes=["g"]), ok("dispatch", lease_id="B", classes=["g"])),
         H(ok("dispatch", lease_id="A", classes=["g"]), ok("expire", lease_id="A", classes=["g"]),
           ok("dispatch", lease_id="B", classes=["g"])))
    pair("V-HIST-FENCE-MONOTONE", C.StaleFenceCannotAdvance,
         H(ok("effect", cls="g", fence=3), ok("effect", cls="g", fence=2)),
         H(ok("effect", cls="g", fence=2), fail("effect", cls="g", fence=1),
           ok("effect", cls="g", fence=3)))
    pair("V-HIST-ONE-JOB", C.DuplicateEnqueueOneJob,
         H(ok("enqueue", run_token="t", job_id="j1"), ok("enqueue", run_token="t", job_id="j2")),
         H(ok("enqueue", run_token="t", job_id="j1"), ok("enqueue", run_token="t", job_id="j1")))
    pair("V-HIST-UNKNOWN-NEVER-PASS", C.UnknownNeverPass,
         H(info("observe", epoch_id="e1", goal_id="g"), ok("judge", epoch_id="e1", verdict="PASS")),
         H(info("observe", epoch_id="e1", goal_id="g"), ok("observe", epoch_id="e1", goal_id="g"),
           ok("judge", epoch_id="e1", verdict="PASS")))
    pair("V-HIST-NO-REPLACE-ON-UNKNOWN", C.NoReplaceOnUnknown,
         H(info("observe", epoch_id="e1", goal_id="g"), ok("begin", epoch_id="e2", goal_id="g")),
         H(info("observe", epoch_id="e1", goal_id="g"), ok("cancel", goal_id="g"),
           ok("begin", epoch_id="e2", goal_id="h")))
    pair("V-HIST-CANCEL-ABSORBING", C.CancelledNeverResumes,
         H(ok("cancel", goal_id="g"), ok("resume", goal_id="g")),
         H(ok("resume", goal_id="g"), ok("cancel", goal_id="g")))
    pair("V-HIST-RECEIPT-OPEN-EPOCH", C.ReceiptOnlyForOpenEpoch,
         H(ok("end", epoch_id="e1"), ok("receipt", epoch_id="e1")),
         H(ok("receipt", epoch_id="e1"), ok("end", epoch_id="e1")))

    # info is not fail: a failed observation resolves nothing and licenses nothing
    v = C.NoReplaceOnUnknown(H(info("probe", epoch_id="e1", goal_id="g"),
                               fail("probe", epoch_id="e1", goal_id="g"),
                               ok("begin", epoch_id="e2", goal_id="g")))
    check("V-HIST-INFO-NOT-RESOLVED-BY-FAIL", v.valid == FAIL,
          "a later failed probe does not resolve an indeterminate epoch", f"{v}")

    v = C.UnknownNeverPass(H(info("observe", epoch_id="e1", goal_id="g"),
                             fail("observe", epoch_id="e1", goal_id="g"),
                             ok("judge", epoch_id="e1", verdict="PASS")))
    check("V-HIST-UNKNOWN-NOT-RESOLVED-BY-FAIL", v.valid == FAIL,
          "a failed observation does not make an indeterminate epoch judgeable", f"{v}")

    # --- composition ------------------------------------------------------------
    def boom(h):
        raise RuntimeError("bad parse")
    rep = compose(H(ok("effect", cls="g", fence=1)), (C.StaleFenceCannotAdvance, boom))
    check("V-HIST-CRASH-IS-UNKNOWN", rep.valid == UNKNOWN and rep.any_unknown
          and "crashed" in rep.by_name()["boom"].detail,
          "a crashing checker makes the report UNKNOWN, never PASS", f"{rep}")
    rep = compose(H(ok("effect", cls="g", fence=2), ok("effect", cls="g", fence=1)),
                  (C.StaleFenceCannotAdvance, boom))
    check("V-HIST-FAIL-KEEPS-UNKNOWN-VISIBLE", rep.valid == FAIL and rep.any_unknown,
          "a FAIL elsewhere does not hide that another checker could not judge", f"{rep}")
    rep = compose(H(ok("effect", cls="g", fence=1)), (C.DuplicateEnqueueOneJob,))
    check("V-HIST-FLOOR", rep.valid == UNKNOWN and rep.verdicts[0].judged == 0,
          "a checker that judged zero ops reports UNKNOWN, not PASS", f"{rep}")
    try:
        compose([{"index": 0, "type": "maybe", "f": "x"}])
        check("V-HIST-MALFORMED", False, "", "a malformed op type was accepted")
    except HistoryError:
        check("V-HIST-MALFORMED", True, "a malformed history is refused as input error", "")

    # negative control: the harness must notice being lied to
    bad = H(ok("effect", cls="g", fence=3), ok("effect", cls="g", fence=2))
    real, fake = compose(bad, (C.StaleFenceCannotAdvance,)), compose(bad, (unbridled_optimism,))
    check("V-HIST-NEGATIVE-CONTROL", real.valid == FAIL and fake.valid == PASS,
          "the known-bad history is red only because of the real checker", f"{real} {fake}")

    # --- end to end: real lease journal + the resource's own log -----------------
    class Clock:
        t = 1000.0

        def __call__(self):
            return self.t
    clk = Clock()

    def scenario(resource_checks: bool) -> list[dict]:
        store = LeaseStore(Path(tempfile.mkdtemp(prefix="hist-")), min_ttl_s=10, clock=clk)
        effects = []

        def resource_write(fence):          # the RESOURCE decides, and logs what it decided
            accepted = store.check("g", fence).ok if resource_checks else True
            effects.append({"type": "ok" if accepted else "fail", "f": "effect",
                            "value": {"cls": "g", "fence": fence}, "source": "resource"})
        a = store.acquire(["g"], "A", 30, "LA")
        store.dispatch("LA", "A", a.fences)
        resource_write(a.fences["g"])
        clk.t += 40                              # A is paused past its TTL
        b = store.acquire(["g"], "B", 30, "LB")
        store.dispatch("LB", "B", b.fences)
        resource_write(b.fences["g"])
        resource_write(a.fences["g"])           # A wakes and writes with its old fence
        lease_ops = from_lease_journal(store.records())
        return lease_ops + [{"index": len(lease_ops) + i, **e} for i, e in enumerate(effects)]

    fenced = compose(scenario(True), (C.AtMostOneValidOwner, C.StaleFenceCannotAdvance))
    naive = compose(scenario(False), (C.AtMostOneValidOwner, C.StaleFenceCannotAdvance))
    check("V-HIST-E2E-FENCED-RESOURCE", fenced.valid == PASS,
          "paused holder wakes after re-grant: a resource that checks the fence refuses it",
          f"{fenced}")
    check("V-HIST-E2E-NAIVE-RESOURCE", naive.valid == FAIL
          and naive.by_name()["StaleFenceCannotAdvance"].valid == FAIL
          and naive.by_name()["AtMostOneValidOwner"].valid == PASS,
          "a resource that trusts the lease accepts the stale write -- and the lease journal "
          "alone looks perfectly healthy (Kleppmann/Jepsen etcd 3.4.3)", f"{naive}")

    print(f"HIST_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
