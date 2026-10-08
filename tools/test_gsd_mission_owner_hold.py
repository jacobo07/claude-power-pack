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

    # 6. the breaker never judges a terminal record (GEX44 sweep crashed every pass on one: set_owner_hold
    # refuses terminal records and the raise escaped supervise). Control: the same spend on RUNNING trips.
    trip = {"measure": lambda r: 10_000_000, "fingerprint": lambda wd: None}
    for mid, st in (("m-brk-run", gm.RUNNING), ("m-brk-done", gm.COMPLETED)):
        _mission(mid, gm.RUNNING)
        r = gm.load(mid)
        r = gm.transition(mid, expect_epoch=r["epoch"], expect_state=r["state"], event="t_env", now=NOW,
                          state=st, token_estimate=100_000)
        try:
            out, err = gm._cost_breaker(r, NOW + 60, **trip), None
        except Exception as exc:  # noqa: BLE001 -- the failure under test
            out, err = None, f"{type(exc).__name__}: {exc}"
        if st == gm.RUNNING:
            check("V-OH-CONTROL-BREAKER-TRIPS-LIVE", err is None and bool((out or {}).get("owner_hold")), str(err))
        else:
            check("V-OH-BREAKER-SKIPS-TERMINAL", err is None and out is not None and not out.get("owner_hold"),
                  str(err))
            if not hasattr(gm, "_auto_budget"):
                print("SKIP V-OH-AUTOBUDGET-SKIPS-TERMINAL (this build has no _auto_budget; not counted)")
                continue
            seq = gm.load(mid)["seq"]
            gm._auto_budget({**gm.load(mid), "token_estimate": None}, NOW + 60, measure=lambda rr: 1)
            check("V-OH-AUTOBUDGET-SKIPS-TERMINAL", gm.load(mid)["seq"] == seq, f"seq {seq} -> {gm.load(mid)['seq']}")

    # 7. a launch parked BEFORE adoption (EDD m-c597a68e7077): held LAUNCHING, host lists THIS launch's worker
    # done -> settle, recording who ran. Controls: the worker still running, and no host row for the launch id.
    r = _mission("m-lch", gm.LAUNCHING)
    r = gm.transition("m-lch", expect_epoch=r["epoch"], expect_state=gm.LAUNCHING, event="t_bg", now=NOW,
                      pending={**r["pending"], "bg_id": "f92cdad1"})
    h = gm.set_owner_hold("m-lch", "cost breaker: processed 692,049 > 1.25 x estimate 500,000", now=NOW)
    lrow = lambda st: [{"id": "f92cdad1", "sessionId": "f92cdad1-7481", "pid": 301196,  # noqa: E731
                        "kind": "background", "state": st}]
    p = gm.plan_next(h, NOW + 60, lrow("done"), pid_alive=gone)
    check("V-OH-HELD-LAUNCH-DONE-SETTLES", p["action"] == "settle" and p.get("launched"), str(p.get("reason")))
    check("V-OH-HELD-LAUNCH-RUNNING-PARKED", gm.plan_next(h, NOW + 60, lrow("running"), pid_alive=gone)["action"]
          == "none")
    check("V-OH-HELD-LAUNCH-UNLISTED-PARKED", gm.plan_next(h, NOW + 60, [], pid_alive=gone)["action"] == "none")
    gm.supervise(now=NOW + 60, sessions=lrow("done"), runner=lambda a: "", stop_runner=lambda a: None,
                 pid_alive=gone, gsd_status=lambda cwd, workstream=None: {"outcome": "OK"}, fingerprint=lambda wd: None)
    s = gm.load("m-lch")
    check("V-OH-LAUNCH-SETTLE-RECORDS-WORKER", s["state"] == gm.HALTED and bool(s.get("owner_hold"))
          and (s.get("owner") or {}).get("session_id") == "f92cdad1-7481" and (s.get("owner") or {}).get("pid") == 301196,
          f"{s['state']} owner={s.get('owner')}")

    # 8. one record's pre-plan failure must not end the pass for the others (GEX44 2026-10-07/08: the breaker's
    # raise sat outside the per-mission isolation, so ONE record crashed every pass for every mission, 264 + ~12
    # passes). The raise is the production error verbatim. Control: the healthy neighbour is still planned.
    for mid in ("m-iso-bad", "m-iso-ok"):
        r = _mission(mid, gm.RUNNING)
        gm.transition(mid, expect_epoch=r["epoch"], expect_state=r["state"], event="t_env", now=NOW,
                      token_estimate=100_000)
    real = gm._cost_breaker

    def poisoned(rec, now, **kw):
        if rec["mission_id"] == "m-iso-bad":
            raise gm.MissionError("m-iso-bad is COMPLETED; there is nothing to hold")
        return real(rec, now, **kw)
    gm._cost_breaker = poisoned
    try:
        rows, err = gm.supervise(now=NOW + 60, sessions=[], runner=lambda a: "", stop_runner=lambda a: None,
                                 pid_alive=gone, gsd_status=lambda cwd, workstream=None: {"outcome": "OK"},
                                 fingerprint=lambda wd: None), None
    except Exception as exc:  # noqa: BLE001 -- the failure under test
        rows, err = [], f"{type(exc).__name__}: {exc}"
    finally:
        gm._cost_breaker = real
    by = {r["mission_id"]: r for r in rows}
    check("V-OH-PREPLAN-FAILURE-ISOLATED", err is None and "MissionError" in str(by.get("m-iso-bad", {}).get("error"))
          and by["m-iso-bad"].get("action") == "none", str(err or by.get("m-iso-bad")))
    check("V-OH-CONTROL-NEIGHBOUR-STILL-PLANNED", "m-iso-ok" in by and not by["m-iso-ok"].get("error"),
          str(by.get("m-iso-ok")))
    # ... and the sweep's own call (`supervise --actions-only`) keeps the error row and exits non-zero, so the
    # heartbeat records it. Control: an error-free pass prints nothing and exits 0.
    import contextlib
    import io
    import json
    real_sup = gm.supervise
    for label, rows_in in (("err", [by["m-iso-bad"], by["m-iso-ok"]]), ("clean", [by["m-iso-ok"]])):
        gm.supervise = lambda dry_run=False, _r=rows_in: _r
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc = gm._cli(["supervise", "--actions-only"])
        finally:
            gm.supervise = real_sup
        shown = [r["mission_id"] for r in json.loads(buf.getvalue())]
        if label == "err":
            check("V-OH-SWEEP-CLI-SURFACES-ERROR", rc == 3 and shown == ["m-iso-bad"], f"rc={rc} shown={shown}")
        else:
            check("V-OH-CONTROL-SWEEP-CLI-CLEAN-RC0", rc == 0 and shown == [], f"rc={rc} shown={shown}")

    # 9. a packet unit is done when ITS done-check says so, not when GSD's whole workstream is (EDD P2-B m-0729ac737bec,
    # 2026-10-08: the unit finished in 8 calls; GSD answered "work remains" for phases 2-7, so the sweep launched a
    # successor that spent 20 calls / 2,130,930 re-certifying a finished unit). Control: a check that says "not done"
    # leaves the old path alone, and a check that cannot answer never completes anything.
    import sys as _sys
    for mid, code in (("m-unit-done", 0), ("m-unit-notdone", 1), ("m-unit-broken", 7)):
        r = _mission(mid, gm.RUNNING)
        gm.transition(mid, expect_epoch=r["epoch"], expect_state=r["state"], event="t_unit", now=NOW,
                      done_check=[_sys.executable, "-c", f"raise SystemExit({code})"], max_hours=100.0)
    launched = []
    rows = gm.supervise(now=NOW + 60, sessions=[{"sessionId": f"{m}-w", "id": f"{m}-w"[:8], "kind": "background",
                                                 "state": "done"} for m in ("m-unit-done", "m-unit-notdone",
                                                                            "m-unit-broken")],
                        runner=lambda *a, **k: launched.append(a) or "", stop_runner=lambda *a, **k: None,
                        pid_alive=gone, gsd_status=lambda cwd, workstream=None: {"outcome": "OK"},
                        fingerprint=lambda wd: None)
    by = {r["mission_id"]: r for r in rows}
    d = gm.load("m-unit-done")
    check("V-OH-UNIT-DONECHECK-COMPLETES", d["state"] == gm.COMPLETED and by["m-unit-done"].get("unit_done") == "DONE"
          and not any("m-unit-done" in str(a) for a in launched), f"{d['state']} row={by.get('m-unit-done')}")
    for mid, want in (("m-unit-notdone", "NOT_DONE"), ("m-unit-broken", "UNANSWERED")):
        check(f"V-OH-CONTROL-UNIT-{want}-NOT-COMPLETED", gm.load(mid)["state"] != gm.COMPLETED
              and by[mid].get("unit_done") == want, f"{gm.load(mid)['state']} row={by.get(mid)}")

    print(f"OWNER_HOLD_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
