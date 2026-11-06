"""V-CLOSE-*: `gsd_mission.py close` (spec vault/specs/mission-close.md).

Origin 2026-11-06 (GEX44, Solver Ascension coordinator): 12 missions were closed by a hand
`transition(event="hold_settled")` -- no Owner authority, no reason of the Owner's, no worker stop. Hermetic: state and
a fake Owner transcript live in a temp dir set before import. Every refusal is paired with an allowed case, so a
function that refuses (or applies) everything cannot go green. `--drills` mutates the module and expects red.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TMP = tempfile.mkdtemp(prefix="gsd-close-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_MISSION_RECOVERY"] = "off"
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
sys.path.insert(1, str(HERE))
import gsd_mission as gm  # noqa: E402
import gsd_long_run as lr  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
gm.STOP_WAIT_S = 0
NOW = 1_800_000_000.0
OWNER_SID = "owner-sess-0001"
TURN = f"{OWNER_SID}:2026-11-06T11:50:30"
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {gate} {'' if cond else ':: ' + str(ev)[:400]}")


def owner_transcript():
    d = Path(TMP) / "projects" / "laptop"
    d.mkdir(parents=True, exist_ok=True)
    rows = [{"type": "user", "timestamp": "2026-11-06T11:50:30.123Z", "uuid": "u-goahead",
             "message": {"role": "user", "content": "go ahead, close them"}},
            {"type": "user", "timestamp": "2026-11-06T11:51:00.000Z", "uuid": "u-tool",
             "message": {"role": "user", "content": [{"type": "tool_result", "content": "x"}]}}]
    (d / f"{OWNER_SID}.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def prepared(mid):
    return gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)


def running(mid):
    prepared(mid)
    owner = {"session_id": f"{mid}-w", "pid": 4242, "proc_start": None, "heartbeat_at": NOW, "epoch": 1,
             "kind": "background"}
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                         state=gm.RUNNING, epoch=1, max_hours=100.0, owner=owner)


def busy(mid):
    return [{"sessionId": f"{mid}-w", "id": f"{mid}-w"[:8], "kind": "background", "state": "busy", "pid": 4242}]


def events(mid, name):
    return [e for e in lr.ledger_events() if e.get("event") == name and e.get("mission_id") == mid]


def refused(mid, **kw):
    before = gm.load(mid)
    args = {"reason": "Owner: programme closed", "owner_turn": TURN, "now": NOW, "sessions": None,
            "pid_alive": lambda pid: False, "stop_runner": lambda argv: None}
    args.update(kw)
    try:
        out = gm.close_mission(mid, args.pop("reason"), args.pop("owner_turn"), **args)
    except gm.MissionError as exc:
        return gm.load(mid) == before, str(exc)
    return False, f"applied: {out.get('closed')}"


def close(mid, **kw):
    args = {"now": NOW, "sessions": None, "pid_alive": lambda pid: False, "stop_runner": lambda argv: None}
    args.update(kw)
    return gm.close_mission(mid, kw.pop("reason", "Owner: programme closed"), TURN,
                            **{k: v for k, v in args.items() if k != "reason"})


def main() -> int:
    owner_transcript()

    # 1. No owner (PREPARED): closes HALTED without asking the host (sessions=None is never consulted).
    prepared("m-c-prep")
    out = close("m-c-prep")
    r = gm.load("m-c-prep")
    check("V-CLOSE-PREPARED-HALTED", out["closed"] and r["state"] == gm.HALTED
          and (r.get("closed") or {}).get("owner_turn", {}).get("uuid") == "u-goahead"
          and (r.get("owner_hold") or {}).get("kind") == gm.CLOSED_HOLD_KIND
          and events("m-c-prep", "mission_closed") and not events("m-c-prep", "hold_settled"), r)

    # 2. RUNNING with a background worker: stopped through the host, then closed.
    running("m-c-run")
    calls = []
    out = close("m-c-run", sessions=busy("m-c-run"), stop_runner=lambda argv: calls.append(argv))
    r = gm.load("m-c-run")
    check("V-CLOSE-STOPS-WORKER", out["closed"] and any("stop" in a for a in calls) and r["state"] == gm.HALTED
          and "gone" in (r["closed"]["stop"] or "") and r["closed"]["prior_state"] == gm.RUNNING, (out, calls))

    # 3. RUNNING, host unavailable: refuses, record unchanged (stop_owner would have said "not listed" = ok).
    running("m-c-nohost")
    ok, why = refused("m-c-nohost", sessions=None)
    check("V-CLOSE-HOST-UNAVAILABLE-REFUSES", ok and "host" in why, why)

    # 4. RUNNING, the stop fails (pid survives): not closed, parked with an owner_stop hold, ledgered.
    running("m-c-stopfail")
    out = close("m-c-stopfail", sessions=busy("m-c-stopfail"), pid_alive=lambda pid: True)
    r = gm.load("m-c-stopfail")
    check("V-CLOSE-STOP-FAILED-PARKS", not out["closed"] and r["state"] == gm.RUNNING
          and (r.get("owner_hold") or {}).get("kind") == "owner_stop" and not r.get("closed")
          and events("m-c-stopfail", "mission_close_stop_failed"), (out, r.get("owner_hold")))

    # 5. Held with worker_stopped_at: closes without asking the host.
    running("m-c-paused")
    gm.owner_pause("m-c-paused", "Owner pause", now=NOW, sessions=busy("m-c-paused"),
                   pid_alive=lambda pid: False, stop_runner=lambda argv: None)
    out = close("m-c-paused", sessions=None)
    r = gm.load("m-c-paused")
    check("V-CLOSE-PAUSED-NO-HOST-NEEDED", out["closed"] and r["state"] == gm.HALTED
          and ((r.get("owner_hold") or {}).get("prior") or {}).get("kind") == "owner_stop", r.get("owner_hold"))

    # 6. Refusals, each with the record unchanged.
    ok, why = refused("m-c-prep")
    check("V-CLOSE-TERMINAL-REFUSES", ok and "already" in why, why)
    prepared("m-c-refuse")
    ok1, w1 = refused("m-c-refuse", reason="  ")
    ok2, w2 = refused("m-c-refuse", outcome="ORPHANED")
    ok3, w3 = refused("m-c-refuse", owner_turn=f"{OWNER_SID}:2026-11-06T11:51:00")   # a tool result, not the Owner
    ok4, w4 = refused("m-c-refuse", owner_turn="free text authority")
    check("V-CLOSE-REFUSALS", ok1 and ok2 and ok3 and ok4, (w1, w2, w3, w4))

    # 7. --outcome COMPLETED.
    prepared("m-c-done")
    out = close("m-c-done", outcome=gm.COMPLETED)
    check("V-CLOSE-OUTCOME-COMPLETED", out["closed"] and gm.load("m-c-done")["state"] == gm.COMPLETED)

    # 8. After a close: never renewed (even a budget halt reason), never planned, never released.
    r = gm.load("m-c-run")
    why_not = gm.renewal_refusal(r, "budget: max_cycles reached", "OK")
    plan = gm.plan_next(r, NOW + 60, [], pid_alive=lambda pid: False)
    try:
        gm.release_owner_hold("m-c-run", now=NOW)
        released = True
    except gm.MissionError:
        released = False
    check("V-CLOSE-NEVER-RENEWED", bool(why_not) and "owner hold" in why_not, why_not)
    check("V-CLOSE-NEVER-PLANNED", plan.get("action") == "none", plan)
    check("V-CLOSE-RELEASE-REFUSED", not released and gm.load("m-c-run")["state"] == gm.HALTED)
    # Control: release of an ordinary hold still works.
    prepared("m-c-ctl")
    gm.set_owner_hold("m-c-ctl", "Owner park", now=NOW)
    gm.release_owner_hold("m-c-ctl", now=NOW)
    check("V-CLOSE-CONTROL-PLAIN-RELEASE", not gm.load("m-c-ctl").get("owner_hold"))

    # 9. The record moves between the stop and the terminal write: CasConflict, not closed.
    prepared("m-c-race")
    real = gm.transition

    def racing(mission_id, **kw):
        if kw.get("event") == "mission_closed":
            cur = gm.load(mission_id)
            real(mission_id, expect_epoch=cur["epoch"], expect_state=cur["state"], event="t_race", now=NOW)
        return real(mission_id, **kw)

    gm.transition = racing
    try:
        close("m-c-race")
        raced = False
    except gm.CasConflict:
        raced = True
    finally:
        gm.transition = real
    check("V-CLOSE-CAS-SEQ", raced and gm.load("m-c-race")["state"] == gm.PREPARED)

    # 9b. Review F1: during the stop's wait the mission is already parked (the sweep launches nothing) ...
    running("m-c-park")
    seen = []
    close("m-c-park", sessions=busy("m-c-park"),
          stop_runner=lambda argv: seen.append((gm.load("m-c-park").get("owner_hold") or {}).get("kind")))
    check("V-CLOSE-PARKED-DURING-STOP", seen == ["owner_stop"] and gm.load("m-c-park")["state"] == gm.HALTED, seen)

    # ... and a successor launched during the stop anyway (epoch + owner moved) is never buried under a close.
    running("m-c-relaunch")

    def relaunch(argv):
        cur = gm.load("m-c-relaunch")
        gm.transition("m-c-relaunch", expect_epoch=cur["epoch"], expect_state=cur["state"], event="t_relaunch",
                      now=NOW, epoch=cur["epoch"] + 1,
                      owner={**cur["owner"], "session_id": "m-c-relaunch-w2", "epoch": cur["epoch"] + 1})

    try:
        close("m-c-relaunch", sessions=busy("m-c-relaunch"), stop_runner=relaunch)
        refused_relaunch = False
    except gm.CasConflict:
        refused_relaunch = True
    check("V-CLOSE-RELAUNCH-DURING-STOP", refused_relaunch and gm.load("m-c-relaunch")["state"] == gm.RUNNING
          and not gm.load("m-c-relaunch").get("closed"))

    # 10. CLI: no --owner-turn exits 2 and writes nothing; with it, the real transcript lookup closes.
    prepared("m-c-cli")
    before = gm.load("m-c-cli")
    rc = gm._cli(["close", "--mission", "m-c-cli", "--reason", "done"])
    check("V-CLOSE-CLI-NEEDS-OWNER-TURN", rc == 2 and gm.load("m-c-cli") == before, rc)
    rc = gm._cli(["close", "--mission", "m-c-cli", "--reason", "done", "--owner-turn", TURN])
    check("V-CLOSE-CLI-CLOSES", rc == 0 and gm.load("m-c-cli")["state"] == gm.HALTED, rc)

    print(f"MISSION_CLOSE_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


DRILLS = [
    ("host-None refusal removed", "        if sessions is None:\n            # stop_owner answers",
     "        if False:\n            # stop_owner answers", "V-CLOSE-HOST-UNAVAILABLE-REFUSES"),
    ("expect_seq dropped", 'expect_state=cur["state"], expect_seq=cur.get("seq"),\n                     event="mission_closed"',
     'expect_state=cur["state"],\n                     event="mission_closed"', "V-CLOSE-CAS-SEQ"),
    ("closed hold dropped", 'owner_hold={"kind": CLOSED_HOLD_KIND,', 'owner_hold=None and {"kind": CLOSED_HOLD_KIND,',
     "V-CLOSE-NEVER-RENEWED"),
    ("release refusal removed", 'if rec["owner_hold"].get("kind") == CLOSED_HOLD_KIND:',
     'if False and rec["owner_hold"].get("kind") == CLOSED_HOLD_KIND:', "V-CLOSE-RELEASE-REFUSED"),
    ("pre-stop park removed", "        if not hold:\n            # Park BEFORE the stop",
     "        if False:\n            # Park BEFORE the stop", "V-CLOSE-PARKED-DURING-STOP"),
    ("owner/epoch re-check removed", 'if cur["epoch"] != rec["epoch"] or cur.get("owner") != rec.get("owner"):',
     "if False:", "V-CLOSE-RELAUNCH-DURING-STOP"),
]


def drills() -> int:
    src = (HERE / "gsd_mission.py").read_text(encoding="utf-8")
    bad = 0
    for name, needle, repl, gate in DRILLS:
        if src.count(needle) != 1:
            print(f"DRILL-FAIL {name}: needle found {src.count(needle)} times, not once")
            bad += 1
            continue
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "gsd_mission.py").write_text(src.replace(needle, repl, 1), encoding="utf-8")
            r = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve())], capture_output=True, text=True,
                               env={**os.environ, "GSD_MISSION_DRILL_DIR": td}, timeout=300)
            red = r.returncode != 0 and f"FAIL {gate}" in r.stdout
            print(f"{'DRILL-PASS' if red else 'DRILL-FAIL'} {name}: {gate} {'red' if red else 'stayed green'}")
            bad += 0 if red else 1
    print(f"CLOSE_DRILLS={len(DRILLS) - bad}/{len(DRILLS)}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(drills() if "--drills" in sys.argv else main())
