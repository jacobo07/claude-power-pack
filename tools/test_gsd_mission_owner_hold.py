#!/usr/bin/env python
"""V-OH-* gates for the mission Owner hold (spec vault/specs/mission-owner-hold.md).

Hermetic, like test_gsd_mission.py: state goes to a temp dir BEFORE import and the host session list and
pid probe are injected. Every refusal has a paired control, so a module that answers `none` (or refuses
renewal) for everything cannot go green.

Mutation drill: set GSD_MISSION_DRILL_DIR to a directory holding a mutated copy of gsd_mission.py; it is
imported instead of the real module, so the live file is never edited to prove the gates can go red.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-mission-hold-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ.pop("CPP_MISSION_RENEW", None)
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None

passes = fails = 0
NOW = 1_800_000_000.0
LATER = NOW + 2 * 3600          # past a 1 h budget
gone = lambda pid: False        # noqa: E731
BUDGET_HALT = "owner BLOCKED and budget: older than 1.0 h"


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def _mission(mid: str, state: str) -> dict:
    """A mission in `state` whose 1 h budget is spent at LATER and whose background owner is gone."""
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    owner = None if state == gm.PREPARED else {"session_id": f"{mid}-w", "pid": 4242,
                                               "proc_start": None, "heartbeat_at": NOW,
                                               "epoch": 1, "kind": "background"}
    pending = {"kind": "worker_start", "epoch": 1, "deadline": NOW + 300} if state == gm.LAUNCHING else None
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                         state=state, epoch=0 if state == gm.PREPARED else 1, max_hours=1.0,
                         owner=owner, pending=pending)


def main() -> int:
    # 1. held + budget spent + owner gone -> none; the same record unheld -> halt (control).
    rec = _mission("m-blk", gm.BLOCKED)
    ctl = gm.plan_next(rec, LATER, [], pid_alive=gone)
    check("V-OH-CONTROL-UNHELD-HALTS", ctl["action"] == "halt", str(ctl))
    held = gm.set_owner_hold("m-blk", "TOK-18 S0 park", now=NOW)
    p = gm.plan_next(held, LATER, [], pid_alive=gone)
    check("V-OH-HELD-BLOCKED-NONE", p["action"] == "none" and "owner hold" in p["reason"], str(p))
    check("V-OH-HOLD-KEEPS-IDENTITY", held["state"] == gm.BLOCKED and held["epoch"] == rec["epoch"]
          and held["mission_id"] == "m-blk", f"{held['state']} e{held['epoch']}")

    # 2. every non-terminal state is parked.
    for mid, st in (("m-run", gm.RUNNING), ("m-lau", gm.LAUNCHING), ("m-pre", gm.PREPARED)):
        r = _mission(mid, st)
        before = gm.plan_next(r, LATER, [], pid_alive=gone)["action"]
        h = gm.set_owner_hold(mid, "park", now=NOW)
        after = gm.plan_next(h, LATER, [], pid_alive=gone)
        check(f"V-OH-HELD-{st}-NONE", before != "none" and after["action"] == "none",
              f"unheld={before} held={after['action']}")

    # 3. renewal: unheld budget halt renews (control); held is refused, naming the hold.
    # A launched record (epoch 1): a never-launched one is refused on its own (goal-governed C3).
    unheld = gm.load("m-run")
    unheld = {**unheld, "owner_hold": None}
    check("V-OH-CONTROL-RENEWAL-ALLOWED", gm.renewal_refusal(unheld, BUDGET_HALT, "OK") is None)
    why = gm.renewal_refusal(gm.load("m-blk"), BUDGET_HALT, "OK")
    check("V-OH-RENEWAL-REFUSED", bool(why) and "owner hold" in why, str(why))

    # 4. input refusals and release.
    try:
        gm.set_owner_hold("m-run", "   ", now=NOW)
        check("V-OH-EMPTY-REASON-REFUSED", False, "empty reason accepted")
    except gm.MissionError:
        check("V-OH-EMPTY-REASON-REFUSED", True)
    gm.create(TMP, "/gsd-autonomous", mission_id="m-done", now=NOW)
    gm.transition("m-done", expect_epoch=0, expect_state=gm.PREPARED, event="t_done", now=NOW,
                  state=gm.HALTED, reason="test")
    try:
        gm.set_owner_hold("m-done", "park", now=NOW)
        check("V-OH-TERMINAL-REFUSED", False, "terminal mission held")
    except gm.MissionError:
        check("V-OH-TERMINAL-REFUSED", True)
    rel = gm.release_owner_hold("m-blk", now=NOW)
    back = gm.plan_next(rel, LATER, [], pid_alive=gone)
    check("V-OH-RELEASE-RESUMES-SUPERVISION", not rel.get("owner_hold") and back["action"] == "halt",
          str(back))
    try:
        gm.release_owner_hold("m-blk", now=NOW)
        check("V-OH-RELEASE-UNHELD-REFUSED", False, "released twice")
    except gm.MissionError:
        check("V-OH-RELEASE-UNHELD-REFUSED", True)

    # 5. a hold may prevent relaunch, never terminal settlement (EDD m-79f84cdd34dc, 2026-10-08): held RUNNING,
    # host lists the worker done -> settle. Controls: host does not list it (UNKNOWN) and host lists it active.
    _mission("m-zmb", gm.RUNNING)
    z = gm.set_owner_hold("m-zmb", "cost breaker: processed 696,658 > 1.25 x estimate 420,000", now=NOW)
    row = lambda st: [{"sessionId": "m-zmb-w", "id": "m-zmb-w"[:8], "kind": "background", "state": st}]  # noqa: E731
    p = gm.plan_next(z, NOW + 60, row("done"), pid_alive=gone)
    check("V-OH-HELD-DEAD-SETTLES", p["action"] == "settle" and "host lists session done" in p["reason"], str(p))
    p = gm.plan_next(z, NOW + 60, [], pid_alive=gone)
    check("V-OH-HELD-UNKNOWN-STAYS-PARKED", p["action"] == "none", str(p))
    p = gm.plan_next(z, NOW + 60, row("running"), pid_alive=gone)
    check("V-OH-HELD-LIVE-STAYS-PARKED", p["action"] == "none", str(p))
    key = gm.goal_key(TMP, "ws-z")
    gm.transition("m-zmb", expect_epoch=z["epoch"], expect_state=gm.RUNNING, event="t_ws", now=NOW, workstream="ws-z")
    blocked = [c["mission_id"] for c in gm.goal_conflicts(key)]
    calls = []
    rows = gm.supervise(now=NOW + 60, sessions=row("done"), runner=lambda a: calls.append(a) or "",
                        stop_runner=lambda a: calls.append(a), pid_alive=gone,
                        gsd_status=lambda cwd, workstream=None: {"outcome": "OK"}, fingerprint=lambda wd: None)
    after = gm.load("m-zmb")
    check("V-OH-SWEEP-SETTLES-TERMINAL", after["state"] == gm.HALTED and bool(after.get("owner_hold"))
          and any(r["mission_id"] == "m-zmb" and r.get("action") == "settle" for r in rows),
          f"{after['state']} hold={bool(after.get('owner_hold'))}")
    check("V-OH-SETTLE-FREES-GOAL", blocked == ["m-zmb"] and gm.goal_conflicts(key) == [],
          f"before={blocked}")
    why = gm.renewal_refusal(after, BUDGET_HALT, "OK")
    check("V-OH-SETTLED-NEVER-RENEWED", bool(why) and "owner hold" in why, str(why))

    print(f"OWNER_HOLD_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
