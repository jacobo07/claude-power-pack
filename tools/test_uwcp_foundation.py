#!/usr/bin/env python3
"""UWCP S1 foundation gates (V-UWCP-F-*).

Covers the goal-log durability additions made for a remote authority home.
Evidence class of this file: LOCAL_REALITY on the host that runs it. The POSIX
branch of the directory fsync can only be exercised on Linux; it is re-run on
the VPS authority home in S5 and is NOT claimed by a Windows run.

    python tools/test_uwcp_foundation.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import log as gl          # noqa: E402

REPO = "e" * 40


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def check(g, cond, ev, why):
        (passes if cond else fails).append(g)
        print(f"  {'PASS' if cond else 'FAIL'} {g}: {ev if cond else why}")

    base = Path(tempfile.mkdtemp(prefix="uwcp_f_"))
    lg = gl.GoalLog(REPO, "g-f", base=base)

    # --- S1-4 directory fsync happens after the name is published -------------
    calls: list[tuple[Path, bool]] = []
    real = gl._fsync_dir

    def spy(path):
        calls.append((Path(path), (Path(path) / f"{len(lg.read()):06d}.json").is_file()))

    gl._fsync_dir = spy
    try:
        lg.append(1, "goal.declared", {"x": 1}, "t")
        check("V-UWCP-F-DIRSYNC-CALLED",
              len(calls) == 1 and calls[0][0] == lg.dir and calls[0][1],
              "publish syncs the goal directory once, after the event name exists",
              f"calls={calls}")
        try:
            lg.append(1, "goal.declared", {"x": 2}, "t")
            raced = False
        except gl.LostRace:
            raced = True
        check("V-UWCP-F-DIRSYNC-NOT-ON-LOSS", raced and len(calls) == 1,
              "a lost race publishes nothing and syncs nothing", f"raced={raced} calls={calls}")
    finally:
        gl._fsync_dir = real

    if os.name == "nt":
        try:
            real(lg.dir)
            noop = True
        except OSError:
            noop = False
        check("V-UWCP-F-DIRSYNC-NT-NOOP", noop,
              "on Windows the directory sync is an explicit no-op, not a crash "
              "(POSIX branch: REMOTE_REALITY owed in S5)", "raised on Windows")
    else:
        real(lg.dir)
        check("V-UWCP-F-DIRSYNC-POSIX", True, "POSIX directory fsync ran without error", "")

    # --- S1-5 negative knowledge ---------------------------------------------
    from modules.gsd_x.goal import contract as gc   # noqa: PLC0415
    from modules.gsd_x.goal import evidence as ev   # noqa: PLC0415

    hl = gl.GoalLog(REPO, "g-hyp", base=base)
    gc.declare(hl, "find the sequencer starter", ["starter proven"], [], {"paths": ["src"]})

    def refused(fn):
        try:
            fn()
            return False
        except ev.HypothesisRefused:
            return True

    A = "the framework play pair is in the card vtable"
    ev.record(hl, gc.project(hl), "H-A", A, ev.OPEN, "epoch-1")
    check("V-UWCP-F-HYP-ESTABLISH-NEEDS-REF",
          refused(lambda: ev.record(hl, gc.project(hl), "H-A", A, ev.ESTABLISHED, "e1")),
          "established without a supporting ref is refused", "an opinion was recorded as fact")
    check("V-UWCP-F-HYP-REJECT-NEEDS-REF",
          refused(lambda: ev.record(hl, gc.project(hl), "H-A", A, ev.REJECTED, "e1")),
          "rejected without a contradicting ref is refused", "a rejection without evidence")
    ev.record(hl, gc.project(hl), "H-A", A, ev.REJECTED, "epoch-1",
              contradicting=["evidence/FP028.md#s3", "vtable 0x806BF618 dump"])
    check("V-UWCP-F-HYP-IMMUTABLE",
          refused(lambda: ev.record(hl, gc.project(hl), "H-A", A + " maybe", ev.OPEN, "e2")),
          "an id's statement cannot be reworded", "statement was rewritten in place")
    check("V-UWCP-F-HYP-NO-RESURRECT-SAME-ID",
          refused(lambda: ev.record(hl, gc.project(hl), "H-A", A, ev.OPEN, "epoch-2",
                                    contradicting=["evidence/FP028.md#s3"])),
          "reopening a rejected hypothesis with already-considered evidence is refused",
          "a rejected hypothesis came back without new information")
    check("V-UWCP-F-HYP-NO-RESURRECT-REWORDED-ID",
          refused(lambda: ev.record(hl, gc.project(hl), "H-A2", "  The framework PLAY pair "
                                    "is in the card vtable ", ev.OPEN, "epoch-2")),
          "a new id restating a rejected claim is refused", "resurrection by a new id")
    ev.record(hl, gc.project(hl), "H-A", A, ev.OPEN, "epoch-3",
              supporting=["new dump of vt[0x74] after patch 3"])
    check("V-UWCP-F-HYP-REOPEN-WITH-NEW-INFO",
          ev.project_hypotheses(gc.project(hl))["H-A"].status == ev.OPEN,
          "control: a genuinely new ref may reopen it", "new information was refused")
    ev.record(hl, gc.project(hl), "H-A", A, ev.REJECTED, "epoch-3",
              contradicting=["re-dump confirms absence"])
    ev.record(hl, gc.project(hl), "H-B", "starter is 0x801F5E54", ev.ESTABLISHED, "epoch-3",
              supporting=["static decode, commit 682f6dd"])
    check("V-UWCP-F-HYP-SUPERSEDE-NEEDS-SUCCESSOR",
          refused(lambda: ev.record(hl, gc.project(hl), "H-B", "starter is 0x801F5E54",
                                    ev.SUPERSEDED, "e4", superseded_by="H-NOPE")),
          "superseded must name an existing successor", "dangling supersession accepted")

    # A successor that has ONLY the durable log (fresh object, fresh projection).
    succ = gc.project(gl.GoalLog(REPO, "g-hyp", base=base))
    rj = ev.rejected(succ)
    check("V-UWCP-F-HYP-SURVIVES-SUCCESSOR",
          [h.hyp_id for h in rj] == ["H-A"]
          and "vtable 0x806BF618 dump" in rj[0].contradicting
          and "re-dump confirms absence" in rj[0].contradicting
          and ev.project_hypotheses(succ)["H-B"].status == ev.ESTABLISHED,
          "a successor reading only the log sees A rejected with ALL its evidence and B "
          "established (Golden 08, LOCAL_REALITY half)", f"successor saw {rj}")
    check("V-UWCP-F-HYP-OLD-READER",
          gc.project(gl.GoalLog(REPO, "g-hyp", base=base)).revision != "",
          "contract.project still replays a log carrying hypothesis events",
          "old reader broke on the new event type")

    total = len(passes) + len(fails)
    print(f"UWCP_FOUNDATION_PASS={len(passes)}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
