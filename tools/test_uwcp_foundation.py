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
    from modules.gsd_x.goal import brief as gb      # noqa: PLC0415
    btext = gb.compile_brief(succ, [], "/w", "continue")
    check("V-UWCP-F-BRIEF-RENDERS-REJECTED",
          "do NOT retry" in btext and "[H-A]" in btext
          and "re-dump confirms absence" in btext and "goal log seq" in btext
          and "[H-B]" in btext.split("## Established")[1],
          "the successor's brief lists A as disproven with its refutation and log seq, "
          "and B as established", "brief omits negative knowledge")
    check("V-UWCP-F-HYP-OLD-READER",
          gc.project(gl.GoalLog(REPO, "g-hyp", base=base)).revision != "",
          "contract.project still replays a log carrying hypothesis events",
          "old reader broke on the new event type")

    # --- S1-7 operator intervention ------------------------------------------
    from modules.gsd_x.goal import epoch as ep            # noqa: PLC0415
    from modules.gsd_x.goal import intervention as iv     # noqa: PLC0415
    from modules.gsd_x.goal import reconcile as rc        # noqa: PLC0415

    ol = gl.GoalLog(REPO, "g-op", base=base)
    gc.declare(ol, "operator can steer", ["done"], [], {"paths": ["src"]})

    def decide(state):
        return rc.decide(rc.Context(state=state, tree_hash="git:t", scope_hash="s",
                                    providers=("gate",)))

    base_kind = decide(gc.project(ol)).kind
    check("V-UWCP-F-OP-CONTROL", base_kind != rc.BLOCKED,
          f"control: an untouched goal is not blocked ({base_kind})", "blocked with no operator")
    iv.intervene(ol, gc.project(ol), iv.PAUSE, "owner@laptop", reason="review first")
    d = decide(gc.project(ol))
    check("V-UWCP-F-OP-PAUSE-BLOCKS", d.kind == rc.BLOCKED and "paused by operator" in d.reason,
          f"a paused goal starts nothing new ({d.reason})", f"decided {d.kind}: {d.reason}")

    def op_refused(fn):
        try:
            fn()
            return False
        except iv.OperatorRefused:
            return True

    check("V-UWCP-F-OP-NOOP-REFUSED",
          op_refused(lambda: iv.intervene(ol, gc.project(ol), iv.PAUSE, "owner")),
          "a second pause is refused, not silently logged", "no-op pause accepted")
    stale = gc.project(ol)
    iv.intervene(ol, stale, iv.RESUME, "owner@pc2")
    try:
        iv.intervene(ol, stale, iv.CANCEL, "owner@laptop")
        cas = False
    except gl.LostRace:
        cas = True
    check("V-UWCP-F-OP-CAS", cas,
          "two control surfaces acting on the same stale state: the second loses the "
          "log's CAS and must re-read", "stale intervention was appended")
    check("V-UWCP-F-OP-RESUME-UNBLOCKS", decide(gc.project(ol)).kind != rc.BLOCKED,
          "resume lets work continue", "still blocked after resume")

    # A running epoch is still observed while paused: nothing in flight is orphaned.
    key = ep.info_key(gc.project(ol).revision, [], "gate", "initial", "s")
    e1 = ep.begin(ol, gc.project(ol), "gate", {}, key, "initial", "t")
    ep.mark_running(ol, gc.project(ol), e1.epoch_id, {"h": 1}, "t")
    iv.intervene(ol, gc.project(ol), iv.PAUSE, "owner")
    d2 = rc.decide(rc.Context(state=gc.project(ol), tree_hash="git:t", scope_hash="s",
                              providers=("gate",),
                              observations={e1.epoch_id: ep.Observation(ep.OBS_RUNNING)}))
    check("V-UWCP-F-OP-PAUSE-KEEPS-OBSERVING", d2.kind == rc.WAIT,
          "paused with an epoch in flight: the reconciler still waits on it and will "
          "harvest it", f"decided {d2.kind}: {d2.reason}")
    ep.end(ol, gc.project(ol), e1.epoch_id, ep.CANCELLED, "operator", "t")

    iv.intervene(ol, gc.project(ol), iv.CANCEL, "owner", reason="wrong target")
    d3 = decide(gc.project(ol))
    check("V-UWCP-F-OP-CANCEL-BLOCKS", d3.kind == rc.BLOCKED and "cancelled" in d3.reason,
          "a cancelled goal starts nothing new", f"decided {d3.kind}: {d3.reason}")
    check("V-UWCP-F-OP-CANCEL-TERMINAL",
          op_refused(lambda: iv.intervene(ol, gc.project(ol), iv.RESUME, "owner"))
          and op_refused(lambda: iv.intervene(ol, gc.project(ol), iv.PAUSE, "owner")),
          "cancellation is terminal: resume and pause are refused after it",
          "a cancelled goal was revived")
    iv.intervene(ol, gc.project(ol), iv.NOTE, "owner", text="leave FP-028 static")
    check("V-UWCP-F-OP-NOTE-AFTER-CANCEL",
          iv.project_operator(gc.project(ol)).notes[-1][2] == "leave FP-028 static",
          "notes are data and still recordable after a cancel", "note lost")

    total = len(passes) + len(fails)
    print(f"UWCP_FOUNDATION_PASS={len(passes)}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
