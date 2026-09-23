#!/usr/bin/env python
"""V-MC-* gates for tools/gsd_mission.py (spec vault/specs/mission-continuity.md).

Hermetic: state is redirected to a temp dir BEFORE import, the host session list
and pid probe are injected, so nothing here reads or writes the live estate.
Every refusal has a paired control that must pass, so a module that refuses (or
replaces) everything cannot go green.
"""
from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-mission-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402

passes = fails = 0


def _ok(gate, ev=""):
    global passes
    passes += 1
    print(f"PASS {gate} {ev}")


def _fail(gate, ev=""):
    global fails
    fails += 1
    print(f"FAIL {gate} {ev}")


def check(gate, cond, ev=""):
    (_ok if cond else _fail)(gate, ev)


NOW = 1_800_000_000.0
alive = lambda pid: True   # noqa: E731
gone = lambda pid: False   # noqa: E731
cant = lambda pid: None    # noqa: E731


def main() -> int:
    # --- lifecycle: prepared is not running ------------------------------------------------
    rec = gm.create(TMP, "/gsd-autonomous", mission_id="m-a", now=NOW)
    check("V-MC-PREPARED-NOT-RUNNING", rec["state"] == gm.PREPARED and rec["owner"] is None,
          rec["state"])
    check("V-MC-PREPARED-PLANS-LAUNCH", gm.plan_next(rec, NOW, [])["action"] == "launch")
    try:
        gm.create(TMP, "/gsd-autonomous", mission_id="m-a", now=NOW)
        _fail("V-MC-NO-DOUBLE-CREATE", "second create of a live mission succeeded")
    except gm.MissionError:
        _ok("V-MC-NO-DOUBLE-CREATE")

    # --- CAS -------------------------------------------------------------------------------
    rec = gm.transition("m-a", expect_epoch=0, expect_state=gm.PREPARED, event="t_launch",
                        state=gm.LAUNCHING, epoch=1,
                        pending={"kind": "worker_start", "deadline": NOW + 300}, now=NOW)
    check("V-MC-CAS-CONTROL", rec["state"] == gm.LAUNCHING and rec["epoch"] == 1)
    try:
        gm.transition("m-a", expect_epoch=0, expect_state=gm.PREPARED, event="t_stale",
                      state=gm.RUNNING, now=NOW)
        _fail("V-MC-CAS-STALE-REFUSED", "stale observation was accepted")
    except gm.CasConflict:
        _ok("V-MC-CAS-STALE-REFUSED")

    # Two supervisors race to replace the same overdue launch: exactly one wins.
    results = []

    def racer(tag):
        try:
            gm.transition("m-a", expect_epoch=1, expect_state=gm.LAUNCHING, event=f"race_{tag}",
                          epoch=2, pending={"kind": "worker_start", "by": tag}, now=NOW)
            results.append("won")
        except gm.CasConflict:
            results.append("lost")

    threads = [threading.Thread(target=racer, args=(i,)) for i in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    check("V-MC-REPLACE-RACE-ONE-WINNER", results.count("won") == 1 and results.count("lost") == 5,
          str(results))

    # A malformed record is an error, never "absent".
    bad = gm.mission_path("m-bad")
    bad.write_text("{not json", encoding="utf-8")
    try:
        gm.load("m-bad")
        _fail("V-MC-MALFORMED-RAISES", "malformed record read as a value")
    except Exception:
        _ok("V-MC-MALFORMED-RAISES")
    check("V-MC-ABSENT-IS-NONE", gm.load("m-nope") is None)

    # --- liveness: DEAD only on positive evidence -----------------------------------------
    owner = {"session_id": "s-1", "pid": 4242, "proc_start": "111"}
    host_live = [{"sessionId": "s-1", "status": "busy", "state": "working"}]
    host_wait = [{"sessionId": "s-1", "status": "waiting", "waitingFor": "permission prompt",
                  "state": "blocked"}]
    host_stop = [{"sessionId": "s-1", "state": "stopped"}]
    v = lambda o, s, p=alive: gm.liveness(o, s, p)[0]  # noqa: E731
    check("V-MC-LIVE-HOST-LISTED", v(owner, host_live) == gm.LIVE)
    check("V-MC-LIVE-WAITING-IS-BLOCKED", v(owner, host_wait) == gm.WAITING_HUMAN)
    check("V-MC-LIVE-HOST-STOPPED-DEAD", v(owner, host_stop) == gm.DEAD)
    check("V-MC-LIVE-UNLISTED-PID-GONE-DEAD", v(owner, [], gone) == gm.DEAD)
    check("V-MC-LIVE-HOST-UNAVAILABLE-UNKNOWN", v(owner, None, gone) == gm.UNKNOWN)
    check("V-MC-LIVE-PID-UNCHECKABLE-UNKNOWN", v(owner, [], cant) == gm.UNKNOWN)
    check("V-MC-LIVE-UNLISTED-PID-ALIVE-UNKNOWN", v(owner, [], alive) == gm.UNKNOWN)
    check("V-MC-LIVE-NO-OWNER-UNKNOWN", v(None, host_live) == gm.UNKNOWN)
    # pid reuse: registry says another process now holds that pid
    sd = Path(os.environ["GSD_LONG_RUN_SESSIONS_DIR"])
    sd.mkdir(parents=True, exist_ok=True)
    (sd / "4242.json").write_text('{"pid":4242,"sessionId":"s-1","procStart":"999"}', encoding="utf-8")
    check("V-MC-LIVE-PID-REUSE-DEAD", v(owner, [], alive) == gm.DEAD)
    (sd / "4242.json").write_text('{"pid":4242,"sessionId":"s-1","procStart":"111"}', encoding="utf-8")
    check("V-MC-LIVE-PID-SAME-START-UNKNOWN", v(owner, [], alive) == gm.UNKNOWN)

    # --- plan_next ---------------------------------------------------------------------------
    base = {"state": gm.RUNNING, "epoch": 3, "owner": owner, "iterations": 1,
            "created_at": NOW, "failed_launches": 0, "pending": None}
    def plan(hs, pid_probe=alive, **kw):
        return gm.plan_next({**base, **kw}, NOW, hs, pid_probe)

    check("V-MC-PLAN-RUNNING-LIVE-NONE", plan(host_live)["action"] == "none")
    check("V-MC-PLAN-RUNNING-DEAD-REPLACE", plan([], gone)["action"] == "replace")
    check("V-MC-PLAN-RUNNING-UNKNOWN-NEVER-REPLACES", plan(None, gone)["action"] == "none")
    check("V-MC-PLAN-BLOCKED-SURFACED", plan(host_wait)["action"] == "surface_blocked")
    check("V-MC-PLAN-LAUNCH-AWAIT",
          plan(host_live, state=gm.LAUNCHING,
               pending={"deadline": NOW + 10})["action"] == "await")
    check("V-MC-PLAN-LAUNCH-OVERDUE-REPLACE",
          plan(host_live, state=gm.LAUNCHING,
               pending={"deadline": NOW - 1})["action"] == "replace")
    check("V-MC-PLAN-LAUNCH-BOUNDED-HALT",
          plan(host_live, state=gm.LAUNCHING, failed_launches=gm.MAX_REPLACEMENTS - 1,
               pending={"deadline": NOW - 1})["action"] == "halt")
    check("V-MC-PLAN-HANDOFF-AWAIT",
          plan(host_live, state=gm.HANDOFF, pending={"deadline": NOW + 60})["action"] == "await")
    check("V-MC-PLAN-HANDOFF-DEAD-REPLACE",
          plan([], gone, state=gm.HANDOFF, pending={"deadline": NOW + 60})["action"] == "replace")
    check("V-MC-PLAN-HANDOFF-OVERDUE-SURFACED",
          plan(host_live, state=gm.HANDOFF,
               pending={"deadline": NOW - 1})["action"] == "surface_blocked")
    check("V-MC-PLAN-BUDGET-HALT",
          plan(host_live, state=gm.PREPARED, iterations=999)["action"] == "halt")
    check("V-MC-PLAN-TERMINAL-NONE", plan(host_live, state=gm.COMPLETED)["action"] == "none")

    # --- launch / ack / hand-off ------------------------------------------------------------
    class R:
        def __init__(self, out, rc=0):
            self.stdout, self.stderr, self.returncode = out, "", rc

    calls = []

    def runner_ok(argv, cwd):
        calls.append(argv)
        return R("backgrounded · 1a2b3c4d · m-l-e1\n  claude agents  list sessions")

    gm.create(TMP, "/gsd-autonomous --from 2", mission_id="m-l", now=NOW)
    res = gm.launch_worker("m-l", expect_epoch=0, expect_state=gm.PREPARED, reason="t",
                           runner=runner_ok, now=NOW)
    rec = gm.load("m-l")
    check("V-MC-LAUNCH-BINDS-HOST-ID", res["ok"] and rec["pending"]["bg_id"] == "1a2b3c4d"
          and rec["state"] == gm.LAUNCHING and rec["epoch"] == 1, str(res))
    check("V-MC-LAUNCH-ARGV-BG-NO-SESSION-ID",
          "--bg" in calls[-1] and "--session-id" not in calls[-1]
          and calls[-1][-1] == "/gsd-autonomous --from 2", str(calls[-1]))
    # a launch loser of the CAS launches nothing
    before = len(calls)
    try:
        gm.launch_worker("m-l", expect_epoch=0, expect_state=gm.PREPARED, reason="dup",
                         runner=runner_ok, now=NOW)
        _fail("V-MC-LAUNCH-DUPLICATE-REFUSED", "stale claim launched")
    except gm.CasConflict:
        check("V-MC-LAUNCH-DUPLICATE-REFUSED", len(calls) == before, "no process spawned")
    # an unrelated session cannot ack; the launched one can
    check("V-MC-ACK-STRANGER-IGNORED", gm.ack_session("ffffffff-0000", now=NOW) is None)
    check("V-MC-STILL-LAUNCHING-UNTIL-ACK", gm.load("m-l")["state"] == gm.LAUNCHING)
    rec = gm.ack_session("1a2b3c4d-aaaa-bbbb", pid=77, proc_start="5", now=NOW + 5)
    check("V-MC-ACK-MAKES-RUNNING", rec and rec["state"] == gm.RUNNING
          and rec["owner"]["session_id"] == "1a2b3c4d-aaaa-bbbb" and rec["iterations"] == 1)
    rec = gm.ack_session("1a2b3c4d-aaaa-bbbb", now=NOW + 60)
    check("V-MC-HEARTBEAT", rec["owner"]["heartbeat_at"] == NOW + 60 and rec["state"] == gm.RUNNING)
    try:
        gm.request_handoff("someone-else", "x", now=NOW)
        _fail("V-MC-HANDOFF-OWNER-ONLY", "non-owner requested a hand-off")
    except gm.MissionError:
        _ok("V-MC-HANDOFF-OWNER-ONLY")
    rec = gm.request_handoff("1a2b3c4d-aaaa-bbbb", "next: phase 3 plan 2", now=NOW + 70)
    check("V-MC-HANDOFF-STATE", rec["state"] == gm.HANDOFF and rec["note"].startswith("next"))

    # launch whose host answer is unparseable: stays LAUNCHING with no bg_id, failure ledgered
    gm.create(TMP, "/gsd-autonomous", mission_id="m-f", now=NOW)
    res = gm.launch_worker("m-f", expect_epoch=0, expect_state=gm.PREPARED, reason="t",
                           runner=lambda a, c: R("Workspace not trusted", rc=1), now=NOW)
    rec = gm.load("m-f")
    check("V-MC-LAUNCH-FAIL-VISIBLE", not res["ok"] and rec["state"] == gm.LAUNCHING
          and "bg_id" not in rec["pending"], str(res))

    # card: mechanical, labelled note, capped
    card = gm.render_card({"epoch": 2, "mission_id": "m-l", "cwd": "C:/p", "resume_command": "/x",
                           "note": "N" * 20000}, {"head": "abc123", "dirty": 3, "recent": ["abc x"]})
    check("V-MC-CARD-CAPPED", len(card.encode()) <= gm.CARD_MAX_BYTES, str(len(card.encode())))
    check("V-MC-CARD-RECONCILE-FIRST", "RECONCILE BEFORE ACTING" in card and "abc123" in card)
    card2 = gm.render_card({"epoch": 2, "mission_id": "m", "cwd": "C:/p", "resume_command": "/x"})
    check("V-MC-CARD-NO-NOTE-SAYS-SO", "did not hand off" in card2)

    # --- W0 regressions: the host restarts a killed background worker ------------------------
    bg = {"session_id": "b-1", "pid": 5151, "kind": "background"}
    check("V-MC-BG-KILLED-NOT-DEAD", v(bg, [], gone) == gm.UNKNOWN,
          "W0 133c6f91: pid gone, host revived it; a replacement wrote a duplicate row")
    check("V-MC-BG-KILLED-NEVER-REPLACED",
          gm.plan_next({**base, "owner": bg}, NOW, [], gone)["action"] == "none")
    idle_row = [{"sessionId": "b-1", "status": "idle", "state": "working", "kind": "background"}]
    ended_row = [{"sessionId": "b-1", "state": "blocked", "kind": "background"}]
    busy_row = [{"sessionId": "b-1", "status": "busy", "state": "working", "kind": "background"}]
    check("V-MC-BG-TURN-ENDED-RELAY",
          gm.plan_next({**base, "owner": bg}, NOW, idle_row, alive)["action"] == "relay")
    check("V-MC-BG-BLOCKED-NO-WAITING-RELAY",
          gm.plan_next({**base, "owner": bg}, NOW, ended_row, alive)["action"] == "relay")
    check("V-MC-BG-BUSY-NO-RELAY",
          gm.plan_next({**base, "owner": bg}, NOW, busy_row, alive)["action"] == "none")

    # --- supervise end to end with fakes -------------------------------------------------------
    stops, launches = [], []

    def stop_run(argv):
        stops.append(argv)
        return R("stopped")

    def launch_run(argv, cwd):
        launches.append(argv)
        return R("backgrounded · 9e9e9e9e · x")

    def fresh(mid):
        for p in Path(TMP).glob("gsd-mission-*.json"):
            p.unlink()
        gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
        gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW,
                      state=gm.RUNNING, epoch=1, owner={**bg, "session_id": f"s-{mid}"})
        return [{"sessionId": f"s-{mid}", "status": "idle", "state": "working",
                 "kind": "background", "id": f"s-{mid}"[:8], "pid": 999}]

    def gsd(outcome):
        return lambda c, workstream=None: {"outcome": outcome, "reason": outcome.lower()}

    hs = fresh("m-ok")
    rows = gm.supervise(now=NOW, sessions=hs, gsd_status=gsd("OK"), runner=launch_run,
                        stop_runner=stop_run, pid_alive=gone)
    rec = gm.load("m-ok")
    check("V-MC-SUP-RELAY-STOPS-THEN-LAUNCHES",
          len(stops) == 1 and len(launches) == 1 and rec["state"] == gm.LAUNCHING
          and rec["epoch"] == 2 and rec["pending"]["bg_id"] == "9e9e9e9e", str(rows))
    hs = fresh("m-done")
    gm.supervise(now=NOW, sessions=hs, gsd_status=gsd("ALL_COMPLETE"), runner=launch_run,
                 stop_runner=stop_run, pid_alive=gone)
    check("V-MC-SUP-COMPLETE-NO-LAUNCH",
          gm.load("m-done")["state"] == gm.COMPLETED and len(launches) == 1)
    hs = fresh("m-unk")
    gm.supervise(now=NOW, sessions=hs, gsd_status=gsd("UNAVAILABLE"), runner=launch_run,
                 stop_runner=stop_run, pid_alive=gone)
    check("V-MC-SUP-GSD-UNAVAILABLE-HOLDS", gm.load("m-unk")["state"] == gm.RUNNING
          and len(launches) == 1 and len(stops) == 1)
    hs = fresh("m-stuck")
    ok, why = gm.stop_owner({**bg, "session_id": "s-m-stuck"}, hs, pid_alive=alive,
                            runner=stop_run, wait_s=0)
    check("V-MC-STOP-WAITS-FOR-PID", ok is False and "still alive" in why, why)

    print(f"MC_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
