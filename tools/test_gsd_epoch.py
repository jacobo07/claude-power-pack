#!/usr/bin/env python
"""V-EPOCH-* gates for tools/gsd_epoch.py (spec vault/specs/parent-context-epoch-rotation.md).

Hermetic: state, transcripts, markers and the session registry are redirected to a temp dir
BEFORE import; the host, git and the launcher are injected. Every refusal or rotation has a
paired control that must come out the other way, so a module that always rotates (today's
behaviour) or always continues cannot go green.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-epoch-test-")
PROJ = Path(TMP) / "projects"
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(PROJ)
os.environ.pop("CPP_MISSION_CONTINUATION", None)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_long_run as lr  # noqa: E402
import gsd_mission as gm  # noqa: E402
import gsd_epoch as ge  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None   # hermetic: never run git in TMP

passes = fails = 0
NOW = 1_800_000_000.0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def iso(t):
    import datetime as dt
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).isoformat()


def transcript(sid, rows, sub=None):
    d = PROJ / "C--proj"
    d.mkdir(parents=True, exist_ok=True)
    main = d / f"{sid}.jsonl"
    with open(main, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    for name, srows in (sub or {}).items():
        sd = d / sid / "subagents"
        sd.mkdir(parents=True, exist_ok=True)
        with open(sd / name, "w", encoding="utf-8") as fh:
            for r in srows:
                fh.write(json.dumps(r) + "\n")
    return main


def asst(t, usage=None, tool_uses=(), text="ok"):
    content = [{"type": "text", "text": text}] + [
        {"type": "tool_use", "id": tid, "name": name, "input": inp} for tid, name, inp in tool_uses]
    msg = {"id": f"msg-{t}", "content": content}
    if usage:
        msg["usage"] = {"input_tokens": usage[0], "cache_creation_input_tokens": usage[1],
                        "cache_read_input_tokens": usage[2]}
    return {"type": "assistant", "timestamp": iso(t), "message": msg}


def result(t, tid, text):
    return {"type": "user", "timestamp": iso(t),
            "message": {"content": [{"type": "tool_result", "tool_use_id": tid, "content": text}]}}


def note(t, tid, status, op="enqueue"):
    return {"type": "queue-operation", "operation": op, "timestamp": iso(t),
            "content": f"<task-notification>\n<task-id>x</task-id>\n<tool-use-id>{tid}</tool-use-id>\n"
                       f"<status>{status}</status>\n</task-notification>"}


def running(mid, sid, epoch=1, **extra):
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", state=gm.RUNNING,
                  epoch=epoch, owner={"session_id": sid, "kind": "background", "epoch": epoch}, now=NOW,
                  **extra)
    return gm.load(mid)


def main() -> int:
    small = (2, 150_000, 30_000)     # 180k resident
    big = (2, 250_000, 100_000)      # 350k resident

    # --- context size is measured from the transcript, unmeasured is None --------------------
    transcript("s-ctx", [asst(NOW - 100, small)])
    check("V-EPOCH-CONTEXT-MEASURED", ge.context_tokens("s-ctx") == 180_002, ge.context_tokens("s-ctx"))
    check("V-EPOCH-CONTEXT-UNMEASURED-IS-NONE", ge.context_tokens("s-none") is None)

    # --- the core split: a turn end continues, the wall rotates -------------------------------
    rec = running("m-cont", "s-cont")
    transcript("s-cont", [asst(NOW - 100, small)])
    d = ge.decide_turn_end(rec, NOW)
    check("V-EPOCH-TURN-END-CONTINUES", d["decision"] == ge.CONTINUE and d["cause"] == ge.TURN_CONTINUATION
          and d["mechanism"] == ge.RESUME, d["reason"])

    rec = running("m-wall", "s-wall")
    transcript("s-wall", [asst(NOW - 100, small)])
    (Path(TMP) / "mission-wall-s-wall-e1.flag").write_text("1")
    d = ge.decide_turn_end(rec, NOW)
    check("V-EPOCH-WALL-ROTATES", d["decision"] == ge.ROTATE and d["cause"] == ge.CONTEXT_ROTATION
          and d["evidence"].get("trigger") == "wall", d["reason"])
    # control: a wall flag for ANOTHER epoch is not evidence for this one
    rec2 = running("m-wall2", "s-wall2", epoch=2)
    transcript("s-wall2", [asst(NOW - 100, small)])
    (Path(TMP) / "mission-wall-s-wall2-e1.flag").write_text("1")
    check("V-EPOCH-WALL-IS-PER-EPOCH", ge.decide_turn_end(rec2, NOW)["decision"] == ge.CONTINUE)

    rec = running("m-led", "s-led")
    transcript("s-led", [asst(NOW - 100, small)])
    lr.ledger_append("s-led", "handoff_already_asked", used_pct=40, mission_id="m-led")
    check("V-EPOCH-WALL-LEDGER-WITNESS", ge.decide_turn_end(rec, NOW)["cause"] == ge.CONTEXT_ROTATION)

    rec = running("m-big", "s-big")
    transcript("s-big", [asst(NOW - 100, big)])
    d = ge.decide_turn_end(rec, NOW)
    check("V-EPOCH-ECONOMIC-CEILING-ROTATES", d["decision"] == ge.ROTATE and d["cause"] == ge.CONTEXT_ROTATION
          and d["evidence"].get("trigger") == "economic_ceiling", d["reason"])
    rec = running("m-bigok", "s-bigok", continue_max_tokens=400_000)
    transcript("s-bigok", [asst(NOW - 100, big)])
    check("V-EPOCH-CEILING-PER-MISSION", ge.decide_turn_end(rec, NOW)["decision"] == ge.CONTINUE)

    rec = running("m-unm", "s-unm")
    d = ge.decide_turn_end(rec, NOW)
    check("V-EPOCH-UNMEASURED-GOES-FRESH-NOT-ROTATION",
          d["decision"] == ge.ROTATE and d["cause"] == ge.TURN_CONTINUATION, d["reason"])

    rec = running("m-ho", "s-ho")
    transcript("s-ho", [asst(NOW - 100, small)])
    gm.transition("m-ho", expect_epoch=1, expect_state=gm.RUNNING, event="t", state=gm.HANDOFF, now=NOW)
    check("V-EPOCH-HANDOFF-IS-ROTATION", ge.decide_turn_end(gm.load("m-ho"), NOW)["cause"] == ge.CONTEXT_ROTATION)

    os.environ["CPP_MISSION_CONTINUATION"] = "off"
    try:
        d = ge.decide_turn_end(running("m-ks", "s-cont"), NOW)
        check("V-EPOCH-KILL-SWITCH", d["decision"] == ge.ROTATE and d["cause"] == ge.TURN_CONTINUATION
              and d["mechanism"] == ge.FRESH, d["reason"])
    finally:
        os.environ.pop("CPP_MISSION_CONTINUATION", None)

    # --- G6 child work ------------------------------------------------------------------------
    bg = ("toolu_bg1", "Bash", {"command": "vitest", "run_in_background": True})
    transcript("s-kid", [asst(NOW - 60, small, [bg])])
    k = ge.child_work("s-kid", NOW)
    check("V-EPOCH-CHILD-PENDING-HOLDS", k["verdict"] == "HOLD" and len(k["pending"]) == 1, k)
    rec = running("m-kid", "s-kid")
    check("V-EPOCH-CHILD-HOLD-BEATS-CONTINUE", ge.decide_turn_end(rec, NOW)["decision"] == ge.HOLD)
    transcript("s-kid2", [asst(NOW - 60, small, [bg]), note(NOW - 30, "toolu_bg1", "completed"),
                          note(NOW - 20, "toolu_bg1", "completed", op="remove")])
    check("V-EPOCH-CHILD-REPORTED-CLEARS", ge.child_work("s-kid2", NOW)["verdict"] == "CLEAR")
    transcript("s-kid3", [asst(NOW - 60, small, [bg]), note(NOW - 30, "toolu_bg1", "completed")])
    k = ge.child_work("s-kid3", NOW)
    check("V-EPOCH-UNCONSUMED-RESULT-HOLDS", k["verdict"] == "HOLD" and k["unconsumed"] == ["toolu_bg1"], k)
    transcript("s-kid4", [asst(NOW - 4000, small, [bg])])
    k = ge.child_work("s-kid4", NOW)
    check("V-EPOCH-CHILD-EXPIRES", k["verdict"] == "EXPIRED", k)
    rec = running("m-kid4", "s-kid4")
    d = ge.decide_turn_end(rec, NOW)
    check("V-EPOCH-EXPIRED-NAMED-LOST", d["decision"] != ge.HOLD
          and d["evidence"].get("children_lost") == ["toolu_bg1"], d)
    sync = ("toolu_ag1", "Agent", {"description": "sync"})
    transcript("s-sync", [asst(NOW - 60, small, [sync]), result(NOW - 30, "toolu_ag1", "final answer: 42")])
    check("V-EPOCH-SYNC-AGENT-IS-NOT-A-CHILD", ge.child_work("s-sync", NOW)["verdict"] == "CLEAR")
    transcript("s-async", [asst(NOW - 60, small, [("toolu_ag2", "Agent", {"description": "a"})]),
                           result(NOW - 59, "toolu_ag2", "Async agent launched successfully.")])
    check("V-EPOCH-ASYNC-AGENT-IS-A-CHILD", ge.child_work("s-async", NOW)["verdict"] == "HOLD")
    transcript("s-sub", [asst(NOW - 60, small)],
               sub={"agent-1.jsonl": [asst(NOW - 50, None, [("toolu_sb", "Bash", {"run_in_background": True})])]})
    check("V-EPOCH-SUBAGENT-CHILD-SEEN", ge.child_work("s-sub", NOW)["verdict"] == "HOLD")
    check("V-EPOCH-NO-TRANSCRIPT-UNKNOWN", ge.child_work("s-nobody", NOW)["verdict"] == "UNKNOWN")

    # --- a continuation in flight is never doubled ------------------------------------------
    rec = running("m-fl", "s-fl", last_continuation_at=NOW - 30, last_continuation_session="s-fl")
    transcript("s-fl", [asst(NOW - 100, small)])
    check("V-EPOCH-CONTINUATION-IN-FLIGHT-HOLDS", ge.decide_turn_end(rec, NOW)["decision"] == ge.HOLD)
    check("V-EPOCH-CONTINUATION-NEVER-RAN-FAILS",
          ge.decide_turn_end(rec, NOW + ge.CONTINUATION_DEADLINE_S + 60)["cause"] == ge.CONTINUATION_FAILED)
    transcript("s-fl", [asst(NOW - 100, small), asst(NOW - 5, small)])
    check("V-EPOCH-CONTINUATION-RAN-CONTINUES-AGAIN", ge.decide_turn_end(rec, NOW)["decision"] == ge.CONTINUE)

    # --- the effect: exact argv, LAUNCHING at the same epoch, copy refused ------------------
    rec = running("m-eff", "abcdef12-0000-0000-0000-000000000000", epoch=3)
    seen = []
    runner = lambda argv, cwd: (seen.append(argv), type("R", (), {  # noqa: E731
        "returncode": 0, "stdout": "backgrounded · abcdef12 · m-eff-e3", "stderr": ""})())[1]
    dec = {"decision": ge.CONTINUE, "cause": ge.TURN_CONTINUATION, "reason": "t", "evidence": {"context_tokens": 1}}
    res = ge.continue_worker("m-eff", rec, prompt="/gsd-autonomous", decision=dec, runner=runner, now=NOW)
    after = gm.load("m-eff")
    check("V-EPOCH-RESUME-ARGV-HAS-NO-FLAGS",
          seen and seen[0][1:] == ["--bg", "--resume", "abcdef12-0000-0000-0000-000000000000", "/gsd-autonomous"],
          seen)
    check("V-EPOCH-CONTINUATION-SAME-EPOCH-LAUNCHING", res["ok"] and after["epoch"] == 3
          and after["state"] == gm.LAUNCHING and after["pending"]["bg_id"] == "abcdef12"
          and after["continuations"] == 1, after.get("state"))
    check("V-EPOCH-RESUMED-SESSION-IS-RECOGNISED",
          (gm.mission_for_session("abcdef12-0000-0000-0000-000000000000") or {}).get("mission_id") == "m-eff")
    acked = gm.ack_session("abcdef12-0000-0000-0000-000000000000", now=NOW + 5)
    check("V-EPOCH-ACK-RETURNS-TO-RUNNING-SAME-EPOCH", acked and acked["state"] == gm.RUNNING
          and acked["epoch"] == 3 and acked["iterations"] == rec.get("iterations", 0) + 1)
    rows = [e for e in lr.ledger_events("m-eff") if e.get("event") == "launch_cause"]
    check("V-EPOCH-CAUSE-RECORDED", rows and rows[-1]["cause"] == ge.TURN_CONTINUATION
          and rows[-1]["mechanism"] == ge.RESUME and rows[-1]["epoch"] == 3, rows[-1:])
    # a concurrent supervisor that observed RUNNING at the same epoch loses its CAS after the claim
    rec = running("m-race", "11111111-0000-0000-0000-000000000000", epoch=2)
    ge.continue_worker("m-race", rec, prompt="/x", decision=dec, runner=runner, now=NOW)
    try:
        gm.transition("m-race", expect_epoch=2, expect_state=gm.RUNNING, event="rival_replace",
                      state=gm.LAUNCHING, epoch=3, now=NOW)
        check("V-EPOCH-RIVAL-SUPERVISOR-LOSES-CAS", False, "rival claimed epoch 3 beside the resume")
    except gm.CasConflict:
        check("V-EPOCH-RIVAL-SUPERVISOR-LOSES-CAS", True)

    rec = running("m-copy", "22222222-0000-0000-0000-000000000000", epoch=1)
    stopped = []
    copy_runner = lambda argv, cwd: type("R", (), {"returncode": 0, "stderr": "",  # noqa: E731
        "stdout": "note: background session 22222222 keeps its own saved options, so the flags you "
                  "passed started a copy as 9f9f9f9f."})()
    res = ge.continue_worker("m-copy", rec, prompt="/x", decision=dec, runner=copy_runner,
                             stop_runner=lambda a: stopped.append(a), now=NOW)
    after = gm.load("m-copy")
    check("V-EPOCH-COPY-REFUSED-AND-STOPPED", not res["ok"] and stopped and stopped[0][-1] == "9f9f9f9f"
          and after["pending"].get("failed"), res)
    plan = gm.plan_next(after, NOW + 1, [])
    check("V-EPOCH-FAILED-CONTINUATION-IS-REPLACED", plan["action"] == "replace", plan)
    check("V-EPOCH-FAILED-CONTINUATION-CAUSE",
          ge.cause_for("replace", plan["reason"], after)["cause"] == ge.CONTINUATION_FAILED)

    # --- cause_for names every fresh launch -------------------------------------------------
    check("V-EPOCH-CAUSE-INITIAL", ge.cause_for("launch", "prepared", {"state": "PREPARED"})["cause"] == ge.INITIAL)
    check("V-EPOCH-CAUSE-RENEWAL", ge.cause_for("launch", "p", {"renewed_from": "m-x"})["cause"] == ge.MISSION_RENEWAL)
    check("V-EPOCH-CAUSE-RETRY", ge.cause_for("replace", "start ack overdue",
                                              {"state": "LAUNCHING", "pending": {"kind": "worker_start"}})["cause"] == ge.LAUNCH_RETRY)
    check("V-EPOCH-CAUSE-RECOVERY", ge.cause_for("replace", "owner dead: host lists session stopped",
                                                 {"state": "RUNNING"})["cause"] == ge.PROCESS_RECOVERY)
    check("V-EPOCH-CAUSE-UNKNOWN-IS-AN-ANSWER", ge.cause_for("replace", "???", {"state": "RUNNING"})["cause"] == ge.UNKNOWN)

    # --- S7 identity ------------------------------------------------------------------------
    (Path(TMP) / ".git").mkdir(exist_ok=True)
    base = {"mission_id": "m-id", "cwd": TMP, "epoch": 2, "owner": None,
            "pending": {"kind": "worker_start", "epoch": 2}}
    check("V-EPOCH-IDENTITY-OK", ge.identity_check(base, "s", TMP)["verdict"] == "OK")
    check("V-EPOCH-IDENTITY-WRONG-CWD", ge.identity_check(base, "s", str(PROJ))["verdict"] == "MISMATCH")
    check("V-EPOCH-IDENTITY-STALE-EPOCH",
          ge.identity_check({**base, "pending": {"kind": "worker_start", "epoch": 1}}, "s", TMP)["verdict"] == "MISMATCH")
    check("V-EPOCH-IDENTITY-UNKNOWN", ge.identity_check(base, "s", None)["verdict"] == "UNKNOWN")

    # --- G3 compaction ----------------------------------------------------------------------
    rec = running("m-cmp", "s-cmp")
    ge.on_session_start(rec, "s-cmp", "compact", TMP, first=False)
    ge.on_session_start(rec, "s-cmp", "resume", TMP, first=False)
    rows = [e for e in lr.ledger_events("m-cmp") if e.get("event") == "epoch_compacted"]
    check("V-EPOCH-COMPACTION-OBSERVED-ONCE", len(rows) == 1 and rows[0]["requested"] is False, rows)

    # --- G4 epochs view + historical classification -----------------------------------------
    mid = "m-view"
    for row in [
        {"event": "launch_claimed", "epoch": 1, "reason": "armed"},
        {"event": "worker_acked", "epoch": 1, "worker": "w1"},
        {"event": "turn_continued", "epoch": 1, "worker": "w1"},
        {"event": "worker_acked", "epoch": 1, "worker": "w1"},
        {"event": "epoch_compacted", "epoch": 1, "worker": "w1"},
        {"event": "launch_claimed", "epoch": 2, "reason": "owner's turn ended without completion: x"},
        {"event": "worker_acked", "epoch": 2, "worker": "w2"},
        {"event": "launch_claimed", "epoch": 3, "reason": "owner's turn ended without completion: x"},
        {"event": "worker_adopted", "epoch": 3, "worker": "w3"},
        {"event": "launch_claimed", "epoch": 4, "reason": "owner dead: gone"},
        {"event": "mission_halted", "epoch": 4},
    ]:
        lr.ledger_append(mid, row.pop("event"), mission_id=mid, **row)
    (Path(TMP) / "mission-wall-w2-e2.flag").write_text("1")   # w2 crossed its wall in epoch 2
    eps = ge.epochs(mid)
    check("V-EPOCH-VIEW-COUNTS", len(eps) == 4 and eps[0]["turns"] == 2 and eps[0]["continuations"] == 1
          and eps[0]["compactions"] == 1, [(e["epoch"], e["turns"], e["continuations"]) for e in eps])
    check("V-EPOCH-VIEW-CAUSES", [e["start_cause"] for e in eps] ==
          [ge.INITIAL, ge.TURN_CONTINUATION, ge.CONTEXT_ROTATION, ge.PROCESS_RECOVERY],
          [e["start_cause"] for e in eps])
    check("V-EPOCH-VIEW-WALL-BASIS", eps[2]["basis"] == "reason+wall_witness" and eps[1]["wall"] is True)
    check("V-EPOCH-VIEW-END-CAUSE", eps[0]["end_cause"] == ge.TURN_CONTINUATION and eps[3]["end_cause"] == "HALTED")

    # --- supervise end to end: the relay branch decides continue / rotate / hold --------------
    def host(sid, status="idle"):
        return [{"sessionId": sid, "id": sid[:8], "status": status, "kind": "background",
                 "pid": 4242, "name": "x"}]

    def sup(sid, fp="fp-A", **kw):
        calls = {"run": [], "stop": []}

        def runner(argv, cwd):
            calls["run"].append(argv)
            name = argv[argv.index("-n") + 1] if "-n" in argv else sid[:8]
            short = argv[3][:8] if "--resume" in argv else "fe5e5e5e"
            return type("R", (), {"returncode": 0, "stderr": "",
                                  "stdout": f"backgrounded · {short} · {name}"})()
        rows = gm.supervise(now=kw.get("now", NOW), sessions=kw.get("sessions") or host(sid),
                            gsd_status=lambda cwd, workstream=None: {"outcome": "OK"},
                            runner=runner, stop_runner=lambda a: calls["stop"].append(a),
                            pid_alive=lambda p: False, fingerprint=lambda wd: fp)
        return rows, calls

    for m in gm.all_missions():   # the unit cases above left RUNNING records; retire them
        if m["state"] not in gm.TERMINAL:
            gm.transition(m["mission_id"], expect_epoch=m["epoch"], expect_state=m["state"],
                          event="t_retire", state=gm.HALTED, now=NOW)

    sid = "aaaa1111-0000-0000-0000-000000000000"
    running("m-s1", sid, epoch=1)
    transcript(sid, [asst(NOW - 100, small)])
    rows, calls = sup(sid)
    r = next(x for x in rows if x["mission_id"] == "m-s1")
    after = gm.load("m-s1")
    check("V-EPOCH-SUP-CONTINUES-SAME-SESSION", r.get("action") == "continue" and calls["run"]
          and calls["run"][0][1:4] == ["--bg", "--resume", sid] and after["epoch"] == 1
          and after["state"] == gm.LAUNCHING, (r.get("action"), calls["run"][:1]))
    check("V-EPOCH-SUP-STOPS-BEFORE-RESUME", calls["stop"] and calls["stop"][0][-1] == sid[:8], calls["stop"])
    check("V-EPOCH-SUP-CONTINUATION-COUNTED-BY-PROGRESS", (after.get("progress") or {}).get("fp") == "fp-A")

    sid = "bbbb2222-0000-0000-0000-000000000000"
    running("m-s2", sid, epoch=1)
    transcript(sid, [asst(NOW - 100, small)])
    (Path(TMP) / f"mission-wall-{sid}-e1.flag").write_text("1")
    rows, calls = sup(sid)
    r = next(x for x in rows if x["mission_id"] == "m-s2")
    after = gm.load("m-s2")
    causes = [e for e in lr.ledger_events("m-s2") if e.get("event") == "launch_cause"]
    check("V-EPOCH-SUP-WALL-LAUNCHES-FRESH", calls["run"] and "--resume" not in calls["run"][0]
          and after["epoch"] == 2 and r.get("cause") == ge.CONTEXT_ROTATION, (r.get("cause"), after["epoch"]))
    check("V-EPOCH-SUP-FRESH-CAUSE-LEDGERED", causes and causes[-1]["cause"] == ge.CONTEXT_ROTATION
          and causes[-1]["mechanism"] == ge.FRESH and causes[-1]["epoch"] == 2
          and causes[-1].get("trigger") == "wall", causes[-1:])

    sid = "cccc3333-0000-0000-0000-000000000000"
    running("m-s3", sid, epoch=1)
    transcript(sid, [asst(NOW - 60, small, [("toolu_k", "Bash", {"run_in_background": True})])])
    rows, calls = sup(sid)
    r = next(x for x in rows if x["mission_id"] == "m-s3")
    check("V-EPOCH-SUP-CHILD-HOLDS-NOTHING-STOPPED", not calls["stop"] and not calls["run"]
          and gm.load("m-s3")["state"] == gm.RUNNING and "background child" in (r.get("held") or ""), r)

    sid = "dddd4444-0000-0000-0000-000000000000"
    running("m-s4", sid, epoch=1)
    transcript(sid, [asst(NOW - 100, small)])
    os.environ["CPP_MISSION_CONTINUATION"] = "off"
    try:
        rows, calls = sup(sid)
    finally:
        os.environ.pop("CPP_MISSION_CONTINUATION", None)
    check("V-EPOCH-SUP-KILL-SWITCH-IS-TODAY", calls["run"] and "--resume" not in calls["run"][0]
          and gm.load("m-s4")["epoch"] == 2 and next(x for x in rows if x["mission_id"] == "m-s4").get("cause")
          == ge.TURN_CONTINUATION)

    # e9 (T5) contract: a same-session loop that never changes the tree still HALTs.
    sid = "eeee5555-0000-0000-0000-000000000000"
    running("m-s5", sid, epoch=1)
    t = NOW
    halted = False
    for i in range(6):
        transcript(sid, [asst(t - 100 + i, small)])
        rows, calls = sup(sid, fp="fp-SAME", now=t)
        rec5 = gm.load("m-s5")
        if rec5["state"] == gm.HALTED:
            halted = "no_progress" in (rec5.get("reason") or "") or any(
                "no_progress" in str(e.get("reason")) for e in lr.ledger_events("m-s5"))
            break
        if rec5["state"] == gm.LAUNCHING:   # the resumed session acks, then its turn runs and ends
            gm.ack_session(sid, now=t + 1)
            t += 120
            transcript(sid, [asst(t - 10, small)])
        t += 60
    check("V-EPOCH-SUP-SAME-SESSION-LOOP-STILL-HALTS", halted, (i, gm.load("m-s5")["state"]))

    c = ge.census()
    check("V-EPOCH-CENSUS-SEPARATES-COUNTERS",
          c["fresh_worker_sessions"] >= 4 and c["context_rotations"] >= 1 and c["same_session_continuations"] >= 1
          and c["fresh_by_cause"][ge.TURN_CONTINUATION] >= 1, {k: c[k] for k in ("fresh_worker_sessions",
                                                                                  "context_rotations",
                                                                                  "same_session_continuations")})

    print(f"EPOCH_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
