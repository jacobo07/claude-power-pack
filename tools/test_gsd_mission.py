#!/usr/bin/env python
"""V-MC-* gates for tools/gsd_mission.py (spec vault/specs/mission-continuity.md).

Hermetic: state is redirected to a temp dir BEFORE import, the host session list
and pid probe are injected, so nothing here reads or writes the live estate.
Every refusal has a paired control that must pass, so a module that refuses (or
replaces) everything cannot go green.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-mission-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP  # adopt/ack write markers: never in the real dir
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

    # the two stdout shapes measured live (W8), ANSI codes included
    real_idle = ("\x1b[36ma554ff0e\x1b[39m \u00b7 m-130c7e665774-e1\x1b[2m (idle \u2014 send a prompt "
                 "to start)\x1b[22m\n\x1b[2m  claude agents             list sessions\x1b[22m")
    real_ok = "backgrounded \u00b7 \x1b[36m0b75ac7f\x1b[39m \u00b7 mc-ralph-1\n"
    check("V-MC-PARSE-REAL-IDLE", gm.parse_launch(real_idle, "m-130c7e665774-e1") == ("a554ff0e", True))
    check("V-MC-PARSE-REAL-BACKGROUNDED", gm.parse_launch(real_ok, "mc-ralph-1") == ("0b75ac7f", False))
    check("V-MC-PARSE-OTHER-NAME-REFUSED", gm.parse_launch(real_ok, "someone-else") == (None, False))
    argv = gm.worker_argv({"mission_id": "m", "epoch": 1, "allowed_tools": ["Read", "Edit"],
                           "add_dirs": ["C:/x"], "permission_mode": "acceptEdits"}, "/mc-task")
    check("V-MC-ARGV-PROMPT-NOT-AFTER-VARIADIC",
          argv[-1] == "/mc-task" and argv[-3] == "--autocompact"
          and max(i for i, a in enumerate(argv) if a in ("--add-dir", "--allowedTools")) < len(argv) - 4,
          str(argv))

    # --- workstream binding (2026-09-25: a bare /gsd-autonomous ran the ROOT milestone) ------
    rec = gm.create(TMP, "/gsd-autonomous", mission_id="m-ws", workstream="lobby-ws", now=NOW)
    check("V-MC-WS-BOUND-AT-CREATE", rec["resume_command"] == "/gsd-autonomous --ws lobby-ws",
          rec["resume_command"])
    rec = gm.create(TMP, "/gsd-autonomous", mission_id="m-ws-none", now=NOW)
    check("V-MC-WS-NONE-UNCHANGED", rec["resume_command"] == "/gsd-autonomous", rec["resume_command"])
    rec = gm.create(TMP, "/gsd-autonomous --ws lobby-ws --from 3", mission_id="m-ws-same",
                    workstream="lobby-ws", now=NOW)
    check("V-MC-WS-EXPLICIT-NOT-DOUBLED",
          rec["resume_command"] == "/gsd-autonomous --ws lobby-ws --from 3", rec["resume_command"])
    check("V-MC-WS-NON-GSD-UNCHANGED", gm.bind_workstream("/mc-task", "lobby-ws") == "/mc-task")
    try:
        gm.create(TMP, "/gsd-autonomous --ws other", mission_id="m-ws-bad", workstream="lobby-ws",
                  now=NOW)
        _fail("V-MC-WS-CONFLICT-REFUSED", "a --ws naming another workstream was accepted")
    except gm.MissionError:
        _ok("V-MC-WS-CONFLICT-REFUSED")
    # A record armed BEFORE the fix holds the bare command: the launch itself must bind it.
    legacy = gm.create(TMP, "/gsd-autonomous", mission_id="m-ws-legacy", now=NOW)
    legacy["workstream"] = "lobby-ws"
    gm._write(gm.mission_path("m-ws-legacy"), legacy)
    ws_calls = []

    def runner_ws(argv, cwd):
        ws_calls.append(argv)
        return R("backgrounded · 5e6f7a8b · m-ws-legacy-e1\n")

    gm.launch_worker("m-ws-legacy", expect_epoch=0, expect_state=gm.PREPARED, reason="t",
                     runner=runner_ws, now=NOW)
    check("V-MC-WS-LEGACY-LAUNCH-BINDS",
          bool(ws_calls) and ws_calls[-1][-1] == "/gsd-autonomous --ws lobby-ws",
          str(ws_calls[-1][-1] if ws_calls else None))

    # A launch with no note must not re-send an older epoch's card (2026-09-25, epoch 4 got 3's).
    stale = gm.create(TMP, "/gsd-autonomous", mission_id="m-stale-card", workstream="lobby-ws",
                      now=NOW)
    stale["card"] = "OLD-CARD epoch 1 WORK TREE: enter C:/elsewhere"
    gm._write(gm.mission_path("m-stale-card"), stale)
    sc_calls = []

    def runner_sc(argv, cwd):
        sc_calls.append(argv)
        return R("backgrounded · 9a8b7c6d · m-stale-card-e1\n")

    gm.launch_worker("m-stale-card", expect_epoch=0, expect_state=gm.PREPARED, reason="t",
                     runner=runner_sc, now=NOW)
    sent = sc_calls[-1][sc_calls[-1].index("--append-system-prompt") + 1] if (
        sc_calls and "--append-system-prompt" in sc_calls[-1]) else ""
    check("V-MC-CARD-NEVER-STALE", "OLD-CARD" not in sent and "worker epoch 1 " in sent
          and "--ws lobby-ws" in sent, sent[:160])

    wcard = gm.render_card({"epoch": 2, "mission_id": "m-ws", "cwd": "C:/p",
                            "resume_command": "/gsd-autonomous", "workstream": "lobby-ws"})
    check("V-MC-WS-CARD-PINS-POINTER",
          "/gsd-autonomous --ws lobby-ws" in wcard and "workstream.set lobby-ws" in wcard, wcard[:200])
    ncard = gm.render_card({"epoch": 2, "mission_id": "m", "cwd": "C:/p",
                            "resume_command": "/gsd-autonomous"})
    check("V-MC-WS-CARD-NONE-SILENT", "workstream.set" not in ncard)

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
        return R(f"backgrounded · 9e9e9e9e · {argv[argv.index('-n') + 1]}")

    def fresh(mid):
        for p in Path(TMP).glob("gsd-mission-*.json"):
            p.unlink()
        gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
        gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW,
                      state=gm.RUNNING, epoch=1, owner={**bg, "session_id": f"s-{mid}"})
        return [{"sessionId": f"s-{mid}", "status": "idle", "state": "working",
                 "kind": "background", "id": f"s-{mid}"[:8], "pid": 999}]

    def fresh_keep(mid):
        """fresh() without wiping the other missions: for multi-mission passes."""
        gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
        gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW,
                      state=gm.RUNNING, epoch=1, owner={**bg, "session_id": f"s-{mid}"})
        return [{"sessionId": f"s-{mid}", "status": "idle", "state": "working",
                 "kind": "background", "id": f"s-{mid}"[:8], "pid": 999}]

    def gsd(outcome):
        return lambda c, workstream=None: {"outcome": outcome, "reason": outcome.lower()}

    # W8: a worker that finished its turn reads host `done` -> plan REPLACE. A completed GSD
    # milestone must still end the mission, not start another worker.
    hs_done = fresh("m-fin")
    hs_done[0]["state"] = "done"
    hs_done[0].pop("status", None)
    n_before = len(launches)
    gm.supervise(now=NOW, sessions=hs_done, gsd_status=gsd("ALL_COMPLETE"), runner=launch_run,
                 stop_runner=stop_run, pid_alive=gone)
    check("V-MC-SUP-REPLACE-ASKS-GSD-FIRST", gm.load("m-fin")["state"] == gm.COMPLETED
          and len(launches) == n_before, gm.load("m-fin")["state"])

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

    # 2026-09-25 (m-3aaa15177f2b): host says `done`, the pid lingers for hours. Terminate it
    # only when the argv proves it is THIS worker; every other shape keeps the refusal.
    def linger(state, argv, dies=True):
        row = {**fresh("m-linger")[0], "state": state, "pid": 4242}
        row.pop("status", None)
        killed, dead = [], []
        alive_fn = lambda p: (False if (dead and dies) else True)
        ok_, why_ = gm.stop_owner({**bg, "session_id": "s-linger"}, [{**row, "sessionId": "s-linger"}],
                                  pid_alive=alive_fn, runner=stop_run, wait_s=0,
                                  cmdline=lambda p: argv,
                                  killer=lambda p: (killed.append(p), dead.append(p)))
        return ok_, why_, killed
    ok, why, killed = linger("done", "claude.exe --session-id s-linger -n m-x-e2")
    check("V-MC-STOP-LINGER-TERMINATED", ok is True and killed == [4242] and "terminated" in why, why)
    ok, why, killed = linger("done", "claude.exe --session-id someone-else")
    check("V-MC-STOP-LINGER-REUSED-PID-SPARED", ok is False and killed == [], why)
    ok, why, killed = linger("done", None)
    check("V-MC-STOP-LINGER-UNREADABLE-SPARED", ok is False and killed == [] and "unreadable" in why, why)
    ok, why, killed = linger("running", "claude.exe --session-id s-linger")
    check("V-MC-STOP-LINGER-LIVE-VERDICT-SPARED", ok is False and killed == [], why)
    ok, why, killed = linger("done", "claude.exe --session-id s-linger", dies=False)
    check("V-MC-STOP-LINGER-SURVIVOR-REPORTED", ok is False and "survived" in why, why)

    # an idle estate never asks the host (the 5-minute sweep must cost nothing)
    for p in Path(TMP).glob("gsd-mission-*.json"):
        p.unlink()
    real_host = gm.host_sessions
    asked = []
    gm.host_sessions = lambda *a, **k: asked.append(1) or []
    try:
        gm.supervise(now=NOW)
        check("V-MC-SUP-IDLE-NO-HOST-QUERY", asked == [], f"host asked {len(asked)}x")
        gm.create(TMP, "/gsd-autonomous", mission_id="m-live", now=NOW)
        gm.supervise(now=NOW, dry_run=True)
        check("V-MC-SUP-LIVE-ASKS-HOST", asked == [1], "control: a live mission does ask")
    finally:
        gm.host_sessions = real_host

    # a turn that ended past the budget halts instead of relaying forever
    check("V-MC-PLAN-RELAY-BUDGET-HALT",
          gm.plan_next({**base, "owner": bg, "iterations": 999}, NOW, idle_row, alive)["action"]
          == "halt")

    # the successor's note: taken from the predecessor's transcript, never a stale epoch's
    real_note = gm.handoff_note_from_transcript
    try:
        gm.handoff_note_from_transcript = lambda sid: "resume at f41" if sid == "s-m-n1" else ""
        hs = fresh("m-n1")
        rec = gm.load("m-n1")
        gm.transition("m-n1", expect_epoch=rec["epoch"], expect_state=gm.RUNNING, event="t",
                      now=NOW, note="STALE note from epoch 0")
        gm.supervise(now=NOW, sessions=hs, gsd_status=gsd("OK"), runner=launch_run,
                     stop_runner=stop_run, pid_alive=gone)
        check("V-MC-NOTE-FROM-TRANSCRIPT", gm.load("m-n1")["note"] == "resume at f41",
              repr(gm.load("m-n1")["note"]))
        gm.handoff_note_from_transcript = lambda sid: ""
        hs = fresh("m-n2")
        rec = gm.load("m-n2")
        gm.transition("m-n2", expect_epoch=rec["epoch"], expect_state=gm.RUNNING, event="t",
                      now=NOW, note="STALE note from epoch 0")
        gm.supervise(now=NOW, sessions=hs, gsd_status=gsd("OK"), runner=launch_run,
                     stop_runner=stop_run, pid_alive=gone)
        check("V-MC-STALE-NOTE-NOT-INHERITED", gm.load("m-n2")["note"] == "",
              repr(gm.load("m-n2")["note"]))
    finally:
        gm.handoff_note_from_transcript = real_note
    # the extractor itself, on a real-shaped transcript
    tdir = Path(TMP) / "projects" / "p"
    tdir.mkdir(parents=True, exist_ok=True)
    (tdir / "s-note-1.jsonl").write_text(json.dumps({"type": "assistant", "message": {"content": [
        {"type": "text", "text": "done f40.\n\nHANDOFF NOTE: next is f41; f40 verified."}]}}) + "\n",
        encoding="utf-8")
    real_find = gm.lr.find_transcript
    gm.lr.find_transcript = lambda sid: (tdir / f"{sid}.jsonl") if (tdir / f"{sid}.jsonl").exists() else None
    try:
        check("V-MC-NOTE-EXTRACTED", gm.handoff_note_from_transcript("s-note-1")
              == "next is f41; f40 verified.")
        check("V-MC-NOTE-ABSENT-EMPTY", gm.handoff_note_from_transcript("s-none") == "")
    finally:
        gm.lr.find_transcript = real_find

    # --- adopt: the host's witness of THIS launch, when the worker's own ack raced ------------
    for p in Path(TMP).glob("gsd-mission-*.json"):
        p.unlink()
    gm.create(TMP, "/gsd-autonomous", mission_id="m-ad", now=NOW)
    gm.transition("m-ad", expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW,
                  state=gm.LAUNCHING, epoch=1,
                  pending={"kind": "worker_start", "bg_id": "ad0ad0ad", "deadline": NOW + 300})
    listed = [{"id": "ad0ad0ad", "sessionId": "ad0ad0ad-1111-2222", "pid": 4321,
               "kind": "background", "state": "working", "status": "busy"}]
    stranger = [{"id": "5757aaaa", "sessionId": "5757aaaa-0000", "kind": "background",
                 "state": "working", "status": "busy"}]
    check("V-MC-ADOPT-PLANNED", gm.plan_next(gm.load("m-ad"), NOW, listed, alive)["action"] == "adopt")
    check("V-MC-ADOPT-NEVER-A-STRANGER",
          gm.plan_next(gm.load("m-ad"), NOW, stranger, alive)["action"] == "await",
          "a new unrelated session is not the launched worker (T-CONT-08)")
    gm.supervise(now=NOW, sessions=listed, gsd_status=gsd("OK"), runner=launch_run,
                 stop_runner=stop_run, pid_alive=alive)
    rec = gm.load("m-ad")
    check("V-MC-ADOPT-RUNNING", rec["state"] == gm.RUNNING
          and rec["owner"]["session_id"] == "ad0ad0ad-1111-2222" and rec["owner"]["kind"] == "background")
    check("V-MC-ADOPT-ARMS-MARKER", (Path(TMP) / "gsd-autorun-ad0ad0ad-1111-2222.json").exists())
    # its late SessionStart then only heartbeats, and still gets the card (epoch > 1 case)
    before_iter = rec["iterations"]
    gm.ack_session("ad0ad0ad-1111-2222", now=NOW + 1)
    check("V-MC-ADOPT-LATE-ACK-HEARTBEATS", gm.load("m-ad")["iterations"] == before_iter
          and gm.load("m-ad")["state"] == gm.RUNNING)

    # --- orphans: the W8 contamination, replayed -------------------------------------------
    for p in Path(TMP).glob("gsd-mission-*.json"):
        p.unlink()
    gm.create(TMP, "/mc-task", mission_id="mA", now=NOW)
    gm.transition("mA", expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW,
                  state=gm.HALTED, epoch=2)
    gm.create(TMP, "/mc-task", mission_id="mB", now=NOW)
    gm.transition("mB", expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW,
                  state=gm.RUNNING, epoch=1,
                  owner={"session_id": "bbbb0001-x", "kind": "background", "pid": 1})
    world = [
        {"id": "aaaa0002", "sessionId": "aaaa0002-x", "name": "mA-e2", "kind": "background",
         "state": "working", "status": "busy"},
        {"id": "bbbb0001", "sessionId": "bbbb0001-x", "name": "mB-e1", "kind": "background",
         "state": "working", "status": "busy"},
        {"id": "cccc0003", "sessionId": "cccc0003-x", "name": "someone-elses-run", "kind": "background",
         "state": "working", "status": "busy"},
    ]
    stopped = []
    gm.supervise(now=NOW, sessions=world, gsd_status=gsd("OK"), runner=launch_run,
                 stop_runner=lambda a: stopped.append(a[-1]) or R("stopped"), pid_alive=alive)
    check("V-MC-ORPHAN-OF-HALTED-STOPPED", "aaaa0002" in stopped, str(stopped))
    check("V-MC-ORPHAN-OWNER-KEPT", "bbbb0001" not in stopped)
    check("V-MC-ORPHAN-STRANGER-KEPT", "cccc0003" not in stopped)
    # an old terminal mission costs no host query
    for p in Path(TMP).glob("gsd-mission-*.json"):
        p.unlink()
    gm.create(TMP, "/mc-task", mission_id="mOld", now=NOW - 3 * 86400)
    gm.transition("mOld", expect_epoch=0, expect_state=gm.PREPARED, event="t",
                  now=NOW - 3 * 86400, state=gm.COMPLETED)
    real_host, asked = gm.host_sessions, []
    gm.host_sessions = lambda *a, **k: asked.append(1) or []
    try:
        gm.supervise(now=NOW)
        check("V-MC-OLD-TERMINAL-NO-HOST-QUERY", asked == [])
    finally:
        gm.host_sessions = real_host

    # --- the card is rendered at relay time; SessionStart spawns nothing --------------------
    for p in Path(TMP).glob("gsd-mission-*.json"):
        p.unlink()
    hs = fresh("m-card")
    real_git = gm._git_facts
    gm._git_facts = lambda cwd: {"head": "feedbee", "dirty": 0, "recent": ["feedbee x"]}
    try:
        gm.supervise(now=NOW, sessions=hs, gsd_status=gsd("OK"), runner=launch_run,
                     stop_runner=stop_run, pid_alive=gone)
    finally:
        gm._git_facts = real_git
    rec = gm.load("m-card")
    check("V-MC-CARD-PRERENDERED-AT-RELAY", "feedbee" in (rec.get("card") or "")
          and "epoch 2" in rec["card"], (rec.get("card") or "")[:60])

    last = launches[-1]
    check("V-MC-CARD-RIDES-THE-LAUNCH",
          "--append-system-prompt" in last
          and "feedbee" in last[last.index("--append-system-prompt") + 1]
          and last[-1] == "/gsd-autonomous", "card in argv, prompt still last")

    def boom(cwd):
        raise AssertionError("SessionStart must not run git")
    gm._git_facts = boom
    try:
        card = gm.session_start(f"{rec['pending']['bg_id']}-late", "startup")
        check("V-MC-SESSIONSTART-NO-GIT-NO-DUPLICATE", card == "", repr(card[:60]))
    except AssertionError as exc:
        check("V-MC-SESSIONSTART-NO-GIT-NO-DUPLICATE", False, str(exc))
    finally:
        gm._git_facts = real_git

    # --- adversarial review 2026-09-24 (scratchpad ADVERSARIAL-REVIEW.md) --------------------
    # H1: an overdue launch with the host unanswerable awaits; the answerable case replaces.
    check("V-MC-LAUNCH-OVERDUE-HOST-UNKNOWN-AWAITS",
          plan(None, state=gm.LAUNCHING, pending={"deadline": NOW - 1})["action"] == "await",
          "UNKNOWN never replaces (spec :166)")
    # H3: the budget binds an owner that can never become DEAD or idle ...
    check("V-MC-BUDGET-UNKNOWN-HALTS",
          plan(None, gone, owner=bg, iterations=999)["action"] == "halt")
    check("V-MC-BUDGET-BLOCKED-HALTS", plan(host_wait, iterations=999)["action"] == "halt")
    check("V-MC-BUDGET-LIVE-BUSY-FINISHES-TURN",
          plan(busy_row, owner=bg, iterations=999)["action"] == "none", "control")
    # ... and an owner UNKNOWN for longer than the stale bound is made visible, not replaced.
    stale = plan([], gone, owner=bg, updated_at=NOW - gm.HEARTBEAT_STALE_S - 10)
    check("V-MC-UNKNOWN-STALE-SURFACED", stale["action"] == "surface_blocked", stale["reason"])
    check("V-MC-UNKNOWN-FRESH-QUIET", plan([], gone, owner=bg, updated_at=NOW)["action"] == "none")

    # H2: the claim moves the lease; the old owner cannot claim the new epoch.
    hs = fresh("m-h2")
    gm.supervise(now=NOW, sessions=hs, gsd_status=gsd("OK"), runner=launch_run,
                 stop_runner=stop_run, pid_alive=gone)
    rec = gm.load("m-h2")
    check("V-MC-CLAIM-CLEARS-OWNER", rec["state"] == gm.LAUNCHING and rec["owner"] is None
          and rec["previous_owner"]["session_id"] == "s-m-h2", str(rec.get("owner")))
    check("V-MC-OLD-OWNER-CANNOT-CLAIM", gm.ack_session("s-m-h2", now=NOW + 1) is None
          and gm.load("m-h2")["state"] == gm.LAUNCHING)
    rec = gm.ack_session(f"{rec['pending']['bg_id']}-new", now=NOW + 2)
    check("V-MC-NEW-WORKER-STILL-CLAIMS", rec and rec["state"] == gm.RUNNING, "control")

    # M1: a DEAD owner whose pid lingers is waited on before the replacement launches.
    real_wait = gm.STOP_WAIT_S
    gm.STOP_WAIT_S = 0
    try:
        hs = fresh("m-m1")
        hs[0]["state"] = "done"
        hs[0].pop("status", None)
        n = len(launches)
        rows = gm.supervise(now=NOW, sessions=hs, gsd_status=gsd("OK"), runner=launch_run,
                            stop_runner=stop_run, pid_alive=alive)
        check("V-MC-REPLACE-WAITS-FOR-PID", len(launches) == n
              and gm.load("m-m1")["state"] == gm.RUNNING, str(rows))
        hs = fresh("m-m1b")
        hs[0]["state"] = "done"
        hs[0].pop("status", None)
        gm.supervise(now=NOW, sessions=hs, gsd_status=gsd("OK"), runner=launch_run,
                     stop_runner=stop_run, pid_alive=gone)
        check("V-MC-REPLACE-PID-GONE-LAUNCHES", len(launches) == n + 1, "control")
    finally:
        gm.STOP_WAIT_S = real_wait

    # M2: a launch in flight (claimed, bg_id not yet written) is not reaped as an orphan.
    for p in Path(TMP).glob("gsd-mission-*.json"):
        p.unlink()
    gm.create(TMP, "/mc-task", mission_id="mF", now=NOW)
    gm.transition("mF", expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW,
                  state=gm.LAUNCHING, epoch=2, pending={"kind": "worker_start", "deadline": NOW + 300})
    world = [{"id": "f0f00002", "sessionId": "f0f00002-x", "name": "mF-e2", "state": "working",
              "status": "busy"},
             {"id": "f0f00001", "sessionId": "f0f00001-x", "name": "mF-e1", "state": "working",
              "status": "busy"}]
    stopped = []
    gm.supervise(now=NOW, sessions=world, gsd_status=gsd("OK"), runner=launch_run,
                 stop_runner=lambda a: stopped.append(a[-1]) or R("stopped"), pid_alive=alive)
    check("V-MC-INFLIGHT-LAUNCH-NOT-REAPED", "f0f00002" not in stopped, str(stopped))
    check("V-MC-OLD-EPOCH-STILL-REAPED", "f0f00001" in stopped, "control")

    # M3: one mission's exception does not abort the pass for the others.
    for p in Path(TMP).glob("gsd-mission-*.json"):
        p.unlink()
    hs = fresh("m-x1") + fresh_keep("m-x2")
    calls_gsd = []

    def gsd_flaky(c, workstream=None):
        calls_gsd.append(1)
        if len(calls_gsd) == 1:
            raise PermissionError("os.replace refused (file held)")
        return {"outcome": "OK", "reason": "ok"}
    try:
        rows = gm.supervise(now=NOW, sessions=hs, gsd_status=gsd_flaky, runner=launch_run,
                            stop_runner=stop_run, pid_alive=gone)
    except Exception as exc:  # the defect itself: the pass died, so no row was judged
        rows = [{"escaped": f"{type(exc).__name__}: {exc}"}]
    errs = [r for r in rows if r.get("error")]
    launched = [r for r in rows if (r.get("launch") or {}).get("ok")]
    check("V-MC-SUP-ERROR-ISOLATED", len(errs) == 1 and len(launched) == 1, str(rows))

    # --- M6 finding: the run moved into a git worktree; the mission must follow it -----------
    import subprocess as _sp
    G = os.environ.get("CPP_GIT_EXE") or r"C:\Program Files\Git\cmd\git.exe"
    repo = Path(TMP) / "wt-repo"
    (repo / "sub").mkdir(parents=True, exist_ok=True)
    (repo / "sub" / "a.txt").write_text("a", encoding="utf-8")
    other = Path(TMP) / "other-repo"
    other.mkdir(exist_ok=True)
    for args in (["init", "-q", str(repo)], ["-C", str(repo), "add", "-A"],
                 ["-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "i"],
                 ["-C", str(repo), "worktree", "add", "-q", "-b", "run",
                  str(repo / ".claude" / "worktrees" / "run")],
                 ["init", "-q", str(other)]):
        _sp.run([G, *args], capture_output=True, timeout=60)
    wt = str((repo / ".claude" / "worktrees" / "run").resolve())
    tdir2 = Path(TMP) / "projects" / "wt"
    tdir2.mkdir(parents=True, exist_ok=True)

    def transcript(sid, cwds):
        (tdir2 / f"{sid}.jsonl").write_text(
            "".join(json.dumps({"type": "user", "cwd": c}) + "\n" for c in cwds), encoding="utf-8")
    transcript("s-wt", [str(repo), wt])
    transcript("s-sub", [str(repo), str(repo / "sub")])
    transcript("s-oth", [str(repo), str(other)])
    real_find = gm.lr.find_transcript
    gm.lr.find_transcript = lambda sid: (tdir2 / f"{sid}.jsonl") if (tdir2 / f"{sid}.jsonl").exists() else None
    try:
        got = gm.effective_workdir("s-wt", str(repo))
        check("V-MC-WORKDIR-FOLLOWS-WORKTREE", got and os.path.normcase(got) == os.path.normcase(wt),
              repr(got))
        check("V-MC-WORKDIR-SUBDIR-IGNORED", gm.effective_workdir("s-sub", str(repo)) == str(repo))
        check("V-MC-WORKDIR-OTHER-REPO-IGNORED", gm.effective_workdir("s-oth", str(repo)) == str(repo))
        check("V-MC-WORKDIR-NO-TRANSCRIPT-UNKNOWN", gm.effective_workdir("s-none", str(repo)) is None)
        # A workstream mission follows a worktree only where the predecessor worked THAT
        # workstream (2026-09-25: an off-mission worker's P0-A worktree was briefed as "the work").
        transcript("s-ws-off", [str(repo), wt])
        (tdir2 / "s-ws-on.jsonl").write_text(
            json.dumps({"type": "user", "cwd": str(repo)}) + "\n"
            + json.dumps({"type": "assistant", "input": {
                "file_path": "C:\\r\\.planning\\workstreams\\lobby-ws\\STATE.md"}}) + "\n"
            + json.dumps({"type": "user", "cwd": wt}) + "\n", encoding="utf-8")
        check("V-MC-WORKDIR-WS-OFF-MISSION-NOT-FOLLOWED",
              gm.effective_workdir("s-ws-off", str(repo), "lobby-ws") == str(repo),
              repr(gm.effective_workdir("s-ws-off", str(repo), "lobby-ws")))
        got_on = gm.effective_workdir("s-ws-on", str(repo), "lobby-ws")
        check("V-MC-WORKDIR-WS-ON-MISSION-FOLLOWED",
              got_on and os.path.normcase(got_on) == os.path.normcase(wt), repr(got_on))
        # The launch arguments name the workstream in EVERY worker's transcript (user line):
        # that alone is not evidence the worker worked it.
        (tdir2 / "s-ws-args.jsonl").write_text(
            json.dumps({"type": "user", "cwd": str(repo),
                        "message": {"content": "<command-args>--ws lobby-ws</command-args>"}}) + "\n"
            + json.dumps({"type": "user", "cwd": wt}) + "\n", encoding="utf-8")
        check("V-MC-WORKDIR-WS-ARGS-ONLY-NOT-FOLLOWED",
              gm.effective_workdir("s-ws-args", str(repo), "lobby-ws") == str(repo))
        # A worktree that PREDATES the base's latest workstream commit would regress the roadmap,
        # even when the (correctly bound) worker touched the workstream there.
        wsd = repo / ".planning" / "workstreams" / "lobby-ws"
        wsd.mkdir(parents=True, exist_ok=True)
        (wsd / "ROADMAP.md").write_text("# newer roadmap\n", encoding="utf-8")
        for args in (["-C", str(repo), "add", "-A"],
                     ["-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm",
                      "ws roadmap on base"]):
            _sp.run([G, *args], capture_output=True, timeout=60)
        check("V-MC-WORKDIR-WS-BEHIND-BASE-NOT-FOLLOWED",
              gm.effective_workdir("s-ws-on", str(repo), "lobby-ws") == str(repo),
              repr(gm.effective_workdir("s-ws-on", str(repo), "lobby-ws")))
        _sp.run([G, "-C", wt, "merge", "-q", "--ff-only", "master"], capture_output=True, timeout=60)
        _sp.run([G, "-C", wt, "merge", "-q", "--ff-only", "main"], capture_output=True, timeout=60)
        got_ff = gm.effective_workdir("s-ws-on", str(repo), "lobby-ws")
        check("V-MC-WORKDIR-WS-CONTAINS-BASE-FOLLOWED",
              got_ff and os.path.normcase(got_ff) == os.path.normcase(wt), repr(got_ff))

        # supervise: GSD is asked in the worktree, the card names it, the launch stays at cwd
        for p in Path(TMP).glob("gsd-mission-*.json"):
            p.unlink()
        gm.create(str(repo), "/gsd-autonomous", mission_id="m-wt", now=NOW)
        gm.transition("m-wt", expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW,
                      state=gm.RUNNING, epoch=1, owner={**bg, "session_id": "s-wt"})
        hs_wt = [{"sessionId": "s-wt", "status": "idle", "state": "working", "kind": "background",
                  "id": "s-wt", "pid": 999}]
        asked_at, launched_at = [], []

        def gsd_at(c, workstream=None):
            asked_at.append(os.path.normcase(str(c)))
            return {"outcome": "OK", "reason": "ok"}

        def launch_at(argv, cwd):
            launched_at.append(os.path.normcase(str(cwd)))
            return launch_run(argv, cwd)
        gm.supervise(now=NOW, sessions=hs_wt, gsd_status=gsd_at, runner=launch_at,
                     stop_runner=stop_run, pid_alive=gone)
        rec = gm.load("m-wt")
        check("V-MC-SUP-GSD-ASKED-IN-WORKTREE", asked_at == [os.path.normcase(wt)], str(asked_at))
        check("V-MC-CARD-NAMES-WORKTREE", "WORK TREE" in (rec.get("card") or "")
              and wt.lower() in (rec.get("card") or "").lower())
        check("V-MC-LAUNCH-STAYS-AT-TRUSTED-CWD",
              launched_at == [os.path.normcase(str(Path(repo).resolve()))], str(launched_at))
        # control: a predecessor that never left the main checkout gets no WORK TREE line
        for p in Path(TMP).glob("gsd-mission-*.json"):
            p.unlink()
        transcript("s-main", [str(repo)])
        gm.create(str(repo), "/gsd-autonomous", mission_id="m-main", now=NOW)
        gm.transition("m-main", expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW,
                      state=gm.RUNNING, epoch=1, owner={**bg, "session_id": "s-main"})
        asked_at.clear()
        gm.supervise(now=NOW, sessions=[{**hs_wt[0], "sessionId": "s-main", "id": "s-main"}],
                     gsd_status=gsd_at, runner=launch_at, stop_runner=stop_run, pid_alive=gone)
        check("V-MC-NO-WORKTREE-NO-LINE", "WORK TREE" not in (gm.load("m-main").get("card") or "")
              and asked_at == [os.path.normcase(str(Path(repo).resolve()))], str(asked_at))
    finally:
        gm.lr.find_transcript = real_find

    # M6: the supervisor's own GSD question waits longer than the arming ceiling (67.5 s measured)
    for p in Path(TMP).glob("gsd-mission-*.json"):
        p.unlink()
    hs = fresh("m-to")
    seen_to = []
    real_gs = gm.lr.gsd_status
    gm.lr.gsd_status = lambda c, timeout=45, workstream=None: (seen_to.append(timeout)
                                                                or {"outcome": "UNAVAILABLE", "reason": "t"})
    try:
        gm.supervise(now=NOW, sessions=hs, runner=launch_run, stop_runner=stop_run, pid_alive=gone)
    finally:
        gm.lr.gsd_status = real_gs
    check("V-MC-SUP-GSD-PATIENT", seen_to == [gm.SUPERVISE_GSD_TIMEOUT_S]
          and gm.SUPERVISE_GSD_TIMEOUT_S >= 120, str(seen_to))

    # Owner decision 2026-09-24: real mission workers run `auto` unless told otherwise. Driven
    # through the real CLI (hermetic state dir), so the default is executed, not just documented.
    import subprocess
    env = {**os.environ, "GSD_LONG_RUN_STATE_DIR": TMP, "GSD_AUTORUN_MARKER_DIR": TMP}
    cli = str(Path(__file__).resolve().parent / "gsd_mission.py")
    for mid_flag, want in ((None, "auto"), ("acceptEdits", "acceptEdits")):
        argv = [sys.executable, cli, "arm", "--cwd", TMP, "--command", "/x", "--no-launch"]
        if mid_flag:
            argv += ["--permission-mode", mid_flag]
        r = subprocess.run(argv, capture_output=True, text=True, env=env, timeout=120)
        try:
            got = json.loads(r.stdout)["mission"]["permission_mode"]
        except Exception as exc:  # noqa: BLE001
            got = f"unparseable: {exc}: {r.stdout[-200:]} {r.stderr[-200:]}"
        check(f"V-MC-CLI-PERMISSION-{want.upper()}", got == want, repr(got))

    print(f"MC_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
