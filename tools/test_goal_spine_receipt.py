#!/usr/bin/env python3
"""V-gates for receipts (vault/specs/goal-spine-v1.md, AC10).

A receipt is a provider's claim. These gates pin every way a claim could move an
obligation it has not earned -- and, as the control, that a real verdict from the
named gate DOES move it and lets the Goal genuinely converge end to end.

    python tools/test_goal_spine_receipt.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["GOAL_SPINE_STATE_DIR"] = tempfile.mkdtemp(prefix="goal-rcpt-")

from modules.goal_spine import convergence as cv     # noqa: E402
from modules.goal_spine import epoch as ep_          # noqa: E402
from modules.goal_spine import goal as gl            # noqa: E402
from modules.goal_spine import receipt as rc         # noqa: E402
from modules.gsd_x.mission import obligation as ob   # noqa: E402
from modules.gsd_x.mission import store as gsdx      # noqa: E402

GATE = "kc:verify_change"


def _setup(state=ep_.STARTED, provider="verify"):
    root = tempfile.mkdtemp(prefix="rcpt-root-")
    g = gl.declare(root, "Prove the wiring.", ["DO-PR"], [{"id": "gate", "text": "t", "done": True}])
    gl.transition(g, gl.ACTIVE)
    gsdx.save(Path(root), [ob.Obligation("DO-PR", "production reality", "TEST", ["fact:x"],
                                         "a player cannot reach it", disposition=ob.ACCEPTED,
                                         done_gate=GATE)], namespace=g.goal_id)
    e = ep_.prepare(g, provider, ["DO-PR"], "d",
                    command="/gsd-autonomous" if provider == "gsd_long" else "")
    if state == ep_.STARTED and provider in ep_.AUTONOMOUS_PROVIDERS:
        ep_.mark_started_autonomous(e)
    ep_.save(e, expected_version=0)
    return g, e


def _r(g, e, **kw) -> rc.Receipt:
    base = dict(epoch_id=e.epoch_id, goal_id=g.goal_id, goal_revision=g.revision,
                obligation_id="DO-PR", provider=e.provider, gate=GATE, exit_status=0,
                observed="VERIFY_RESULT=DONE_VERIFIED")
    base.update(kw)
    return rc.Receipt(**base)


def _disp(g) -> str:
    return gsdx.load(Path(g.root), namespace=g.goal_id)[0].disposition


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def ok(n, ev):
        passes.append(n)
        print(f"  OK   {n}  {ev}")

    def bad(n, ev):
        fails.append(n)
        print(f"  FAIL {n}  {ev}")

    def expect_refused(name, g, receipt, needle):
        res = rc.ingest(g, receipt)
        if res.outcome == rc.REFUSED and needle in res.reason and _disp(g) == ob.ACCEPTED:
            ok(name, res.reason[:100])
        else:
            bad(name, f"{res.outcome}: {res.reason} disposition={_disp(g)}")

    # --- CONTROL: a real verdict from the named gate applies, and converges --
    g, e = _setup()
    res = rc.ingest(g, _r(g, e))
    v = cv.compute(g)
    if res.outcome == rc.APPLIED and _disp(g) == ob.SATISFIED and v.converged:
        cv.apply_verdict(g, v)
        ok("V-RCPT-CONTROL-APPLIES-AND-CONVERGES", f"SATISFIED -> Goal {g.state}")
    else:
        bad("V-RCPT-CONTROL-APPLIES-AND-CONVERGES", f"{res.outcome} {res.reason} converged={v.converged}")

    # --- duplicate delivery changes nothing -----------------------------------
    g, e = _setup()
    first = rc.ingest(g, _r(g, e))
    second = rc.ingest(g, _r(g, e))
    if first.outcome == rc.APPLIED and second.outcome == rc.DUPLICATE and first.receipt_id == second.receipt_id:
        ok("V-RCPT-DUPLICATE-IS-A-NO-OP", f"{first.receipt_id} applied once")
    else:
        bad("V-RCPT-DUPLICATE-IS-A-NO-OP", f"{first.outcome} then {second.outcome}")

    # --- the refusals ---------------------------------------------------------
    g, e = _setup()
    expect_refused("V-RCPT-NARRATIVE-SATISFIES-NOTHING", g,
                   _r(g, e, gate="", exit_status=0, observed="", narrative="DONE, all green"),
                   "not evidence")
    g, e = _setup()
    expect_refused("V-RCPT-WRONG-GATE-REFUSED", g, _r(g, e, gate="echo ok"), "evidence about something else")
    g, e = _setup()
    expect_refused("V-RCPT-FAILED-GATE-REFUSED", g,
                   _r(g, e, exit_status=1, observed="VERIFY_RESULT=BLOCKED"), "returned 1")
    g, e = _setup()
    stale = _r(g, e)
    gl.revise(g, "Prove the wiring and dispatch every role.")
    expect_refused("V-RCPT-STALE-REVISION-REFUSED", g, stale, "its target moved")
    g, e = _setup(state=ep_.PREPARED)
    expect_refused("V-RCPT-UNSTARTED-EPOCH-REFUSED", g, _r(g, e), "never started")
    g, e = _setup()
    expect_refused("V-RCPT-OUT-OF-SCOPE-REFUSED", g, _r(g, e, obligation_id="DO-OTHER"), "outside epoch")
    g, e = _setup()
    expect_refused("V-RCPT-PROVIDER-MISMATCH-REFUSED", g, _r(g, e, provider="codex"), "was given to verify")
    g, e = _setup()
    other, _ = _setup()
    expect_refused("V-RCPT-OTHER-GOAL-REFUSED", g, _r(g, e, goal_id=other.goal_id), "not " + g.goal_id)
    g, e = _setup()
    expect_refused("V-RCPT-UNKNOWN-EPOCH-REFUSED", g, _r(g, e, epoch_id="e-000000000000"), "no epoch")

    # --- a refused receipt is remembered, so its re-delivery is a no-op ------
    g, e = _setup()
    bad_r = _r(g, e, gate="echo ok")
    rc.ingest(g, bad_r)
    again = rc.ingest(g, bad_r)
    if again.outcome == rc.DUPLICATE and _disp(g) == ob.ACCEPTED:
        ok("V-RCPT-REFUSAL-IS-REMEMBERED", "re-delivery of a refused receipt changes nothing")
    else:
        bad("V-RCPT-REFUSAL-IS-REMEMBERED", again.outcome)

    # ---------------------------------------------------------------------------
    # Added after tools/mutation_probe.py scored receipt.py 14/24. `or` -> `and` on
    # the epoch-binding check survived: the receipt's OWN revision stamp is
    # checked earlier, but the EPOCH it cites was never pinned to this Goal and
    # this revision.
    # ---------------------------------------------------------------------------

    # --- an epoch prepared under an OLD revision cannot serve the new target --
    g, e = _setup()                      # epoch bound to revision 1
    gl.revise(g, "Prove the wiring and dispatch every role.")   # Goal now at 2
    forged = _r(g, e, goal_revision=g.revision)                # stamp claims rev 2
    expect_refused("V-RCPT-OLD-REVISION-EPOCH-REFUSED", g, forged, "serves")

    # --- an epoch belonging to ANOTHER Goal at the same revision -------------
    g, _ = _setup()
    other, other_epoch = _setup()
    expect_refused("V-RCPT-FOREIGN-EPOCH-REFUSED", g,
                   _r(g, other_epoch, goal_id=g.goal_id), "serves")

    # --- a refusal is recorded even on a machine with no state directory -----
    prev = os.environ["GOAL_SPINE_STATE_DIR"]
    g, e = _setup()
    os.environ["GOAL_SPINE_STATE_DIR"] = str(Path(tempfile.mkdtemp()) / "fresh" / "machine")
    try:
        res = rc.ingest(g, _r(g, e))      # epoch unknown here -> refused and recorded
        if res.outcome == rc.REFUSED and rc._ledger_path(res.receipt_id).is_file():
            ok("V-RCPT-REFUSAL-RECORDED-ON-FRESH-MACHINE", "refused, and the refusal persisted")
        else:
            bad("V-RCPT-REFUSAL-RECORDED-ON-FRESH-MACHINE", res.outcome)
    except OSError as exc:
        bad("V-RCPT-REFUSAL-RECORDED-ON-FRESH-MACHINE", repr(exc))
    finally:
        os.environ["GOAL_SPINE_STATE_DIR"] = prev

    total = len(passes) + len(fails)
    print(f"\nGOAL_RECEIPT_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
