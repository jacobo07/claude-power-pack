#!/usr/bin/env python
"""V-RETARGET-* gates for `gsd_mission.py retarget` (spec vault/specs/mission-retarget.md).

Origin S11-13 (2026-11-03): a new generation of the Solver Ascension needed a new launch prompt and the only route was
arming a second mission. Hermetic: state in a temp dir before import. Every refusal is paired with an allowed case, so a
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
TMP = tempfile.mkdtemp(prefix="gsd-retarget-test-")
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

gm.host_sessions = lambda *a, **k: None
NOW = 1_800_000_000.0
passes = fails = 0
OLD, NEW = "Execute Generation A of the programme.", "Execute Generation B of the programme (new method)."


def check(gate, cond, ev=""):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def refused(mid, cmd, reason="next generation"):
    before = gm.load(mid)
    try:
        gm.retarget_mission(mid, cmd, reason, now=NOW)
    except gm.MissionError as e:
        return gm.load(mid) == before, str(e)
    return False, "applied"


def running(mid, cmd=OLD):
    gm.create(TMP, cmd, mission_id=mid, now=NOW)
    owner = {"session_id": f"{mid}-w", "pid": None, "proc_start": None, "heartbeat_at": NOW, "epoch": 1,
             "kind": "background"}
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.RUNNING,
                         epoch=1, owner=owner)


def main() -> int:
    # 1. PREPARED applies; the record and the launch prompt carry the new text; lineage fields survive.
    gm.create(TMP, OLD, mission_id="m-prep", now=NOW)
    gm.add_directive("m-prep", "keep exact", now=NOW)
    rec = gm.retarget_mission("m-prep", NEW, "S11H generation", now=NOW)
    check("V-RETARGET-PREPARED-APPLIES", rec["resume_command"] == NEW and gm.launch_prompt(rec) == NEW
          and rec["directives"] == ["keep exact"] and len(rec["retargets"]) == 1, rec["resume_command"][:40])

    # 2. The ledger row carries both hashes and the reason, never the text.
    rows = [json.loads(x) for x in Path(lr.ledger_path()).read_text(encoding="utf-8").splitlines() if x.strip()]
    rt = [r for r in rows if r.get("event") == "mission_retargeted" and r.get("mission_id") == "m-prep"]
    blob = json.dumps(rt)
    check("V-RETARGET-LEDGER-HASH-ONLY", len(rt) == 1 and rt[0].get("to_sha256") and rt[0].get("from_sha256")
          and "Generation B" not in blob and "Generation A" not in blob, blob[:160])

    # 3. RUNNING without a hold refuses. Held with the owner still busy (host lists it running) refuses too: a
    #    checkpoint lets a busy worker finish its turn (review MEDIUM-1). Held with the host listing the owner `done`
    #    applies; held with the hold's own stop recorded applies without asking the host.
    running("m-live")
    same, why = refused("m-live", NEW)
    check("V-RETARGET-LIVE-UNHELD-REFUSES", same and "hold it first" in why, why[:80])
    gm.set_owner_hold("m-live", "checkpoint: wave closed", now=NOW, kind="checkpoint")
    busy = [{"sessionId": "m-live-w", "id": "m-live-w", "state": "running", "status": "busy", "kind": "background"}]
    before = gm.load("m-live")
    try:
        gm.retarget_mission("m-live", NEW, "next wave", now=NOW, sessions=busy)
        same, why = False, "applied"
    except gm.MissionError as e:
        same, why = gm.load("m-live") == before, str(e)
    check("V-RETARGET-HELD-BUSY-REFUSES", same and "not proven gone" in why, why[:80])
    unhosted = gm.load("m-live")
    try:   # host unavailable -> UNKNOWN, never DEAD: refuses
        gm.retarget_mission("m-live", NEW, "next wave", now=NOW, sessions=None)
        same = False
    except gm.MissionError:
        same = gm.load("m-live") == unhosted
    check("V-RETARGET-HOST-UNKNOWN-REFUSES", same)
    done = [{**busy[0], "state": "done", "status": None}]
    rec = gm.retarget_mission("m-live", NEW, "next wave", now=NOW, sessions=done)
    check("V-RETARGET-HELD-APPLIES", rec["resume_command"] == NEW and rec["state"] == gm.RUNNING
          and rec.get("owner_hold"), rec["state"])
    running("m-stopped")
    gm.set_owner_hold("m-stopped", "owner pause", now=NOW)
    h = gm.load("m-stopped")
    gm.transition("m-stopped", expect_epoch=h["epoch"], expect_state=h["state"], event="t_stop", now=NOW,
                  owner_hold={**h["owner_hold"], "worker_stopped_at": NOW, "stop": "test"})
    rec = gm.retarget_mission("m-stopped", NEW, "after pause", now=NOW, sessions=busy)
    check("V-RETARGET-HOLD-STOPPED-APPLIES", rec["resume_command"] == NEW)

    # 3b. Workstream change refuses (review HIGH-1): create derives the workstream from --ws; a retarget must not
    #     leave the record's workstream (goal key, GSD status) behind the command. Same workstream applies.
    gm.create(TMP, "/gsd-autonomous", mission_id="m-ws", now=NOW)
    same, why = refused("m-ws", "/gsd-autonomous --ws lobby")
    gm.create(TMP, "/gsd-autonomous --ws lobby", mission_id="m-ws2", now=NOW)
    rec = gm.retarget_mission("m-ws2", "/gsd-execute-phase 2 --ws lobby", "pin", now=NOW)
    check("V-RETARGET-WS-CHANGE-REFUSES", same and "workstream change" in why and rec.get("workstream") == "lobby",
          why[:80])

    # 3c. Compare-and-swap includes seq (review MEDIUM-2): a hold released between the load and the write moves seq
    #     only. Simulated by a load that returns the pre-release record once.
    running("m-race")
    gm.set_owner_hold("m-race", "checkpoint", now=NOW, kind="checkpoint")
    stale = gm.load("m-race")
    gm.release_owner_hold("m-race", now=NOW)
    real_load, calls = gm.load, []

    def stale_once(mid):
        calls.append(mid)
        return stale if len(calls) == 1 else real_load(mid)
    gm.load = stale_once
    try:
        gm.retarget_mission("m-race", NEW, "race", now=NOW, sessions=done and [{**done[0], "sessionId": "m-race-w"}])
        raced = "applied"
    except gm.CasConflict as e:
        raced = f"cas: {e}"
    except gm.MissionError as e:
        raced = f"refused: {e}"
    finally:
        gm.load = real_load
    check("V-RETARGET-SEQ-CAS", raced.startswith("cas:") and gm.load("m-race")["resume_command"] == OLD, raced[:90])

    # 4. TERMINAL refuses.
    running("m-dead")
    gm.transition("m-dead", expect_epoch=1, expect_state=gm.RUNNING, event="t_halt", now=NOW, state=gm.HALTED)
    same, why = refused("m-dead", NEW)
    check("V-RETARGET-TERMINAL-REFUSES", same and "successor" in why, why[:80])

    # 5. Route-class change refuses (both directions); same class applies (case 1 is prose->prose).
    gm.create(TMP, OLD, mission_id="m-route", now=NOW)
    s1, w1 = refused("m-route", "/gsd-autonomous")
    gm.create(TMP, "/gsd-autonomous", mission_id="m-route2", now=NOW)
    s2, w2 = refused("m-route2", OLD)
    rec = gm.retarget_mission("m-route2", "/gsd-execute-phase 3", "phase pin", now=NOW)
    check("V-RETARGET-ROUTE-CLASS-REFUSES", s1 and s2 and "re-arm" in w1 and rec["resume_command"].startswith("/gsd-"),
          f"{w1[:40]} | {w2[:40]}")

    # 6. A work-unit packet mission refuses (the packet, not resume_command, is what launches).
    gm.create(TMP, OLD, mission_id="m-pkt", now=NOW)
    gm.transition("m-pkt", expect_epoch=0, expect_state=gm.PREPARED, event="t_pkt", now=NOW,
                  wu_packet={"path": str(Path(TMP) / "p.md")})
    same, why = refused("m-pkt", NEW)
    check("V-RETARGET-PACKET-REFUSES", same and "packet" in why, why[:80])

    # 7. Empty command / empty reason refuse.
    gm.create(TMP, OLD, mission_id="m-empty", now=NOW)
    s1, _ = refused("m-empty", "   ")
    s2, _ = refused("m-empty", NEW, reason=" ")
    check("V-RETARGET-EMPTY-REFUSES", s1 and s2)

    # 8. CLI end to end, with --expect-cwd.
    cf = Path(TMP) / "cmd.txt"
    cf.write_text("Execute Generation C.", encoding="utf-8")
    gm.create(TMP, OLD, mission_id="m-cli", now=NOW)
    r = subprocess.run([sys.executable, "-B", str(Path(gm.__file__)), "retarget", "--mission", "m-cli",
                        "--command-file", str(cf), "--reason", "cli", "--expect-cwd", TMP],
                       capture_output=True, text=True, env=os.environ.copy(), timeout=120)
    check("V-RETARGET-CLI", r.returncode == 0 and "RETARGETED mission=m-cli" in r.stdout
          and gm.load("m-cli")["resume_command"] == "Execute Generation C.", (r.stdout + r.stderr)[-160:])

    print(f"RETARGET_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


DRILLS = [
    ("hold check removed", '        if not hold:\n            raise MissionError(f"{mission_id} is {rec[\'state\']} with no hold',
     '        if False:\n            raise MissionError(f"{mission_id} is {rec[\'state\']} with no hold',
     "V-RETARGET-LIVE-UNHELD-REFUSES"),
    ("owner liveness check removed", '            if verdict != DEAD:\n                raise MissionError(f"{mission_id} is held',
     '            if False:\n                raise MissionError(f"{mission_id} is held', "V-RETARGET-HELD-BUSY-REFUSES"),
    ("workstream check removed", 'if m and m.group(1) != rec.get("workstream"):', 'if False:',
     "V-RETARGET-WS-CHANGE-REFUSES"),
    ("seq dropped from the CAS", 'expect_seq=rec.get("seq"), resume_command=new', 'resume_command=new',
     "V-RETARGET-SEQ-CAS"),
    ("route-class check removed", 'if old.lstrip().startswith("/gsd-") != command.lstrip().startswith("/gsd-"):',
     'if False:', "V-RETARGET-ROUTE-CLASS-REFUSES"),
    ("text written to ledger", 'ledger_extra={k: row[k] for k in ("from_sha256", "to_sha256", "reason")}',
     'ledger_extra={**{k: row[k] for k in ("from_sha256", "to_sha256", "reason")}, "text": new}',
     "V-RETARGET-LEDGER-HASH-ONLY"),
]


def drills() -> int:
    src = (HERE / "gsd_mission.py").read_text(encoding="utf-8")
    bad = 0
    for name, needle, repl, gate in DRILLS:
        if src.count(needle) != 1:
            print(f"DRILL-FAIL {name}: needle not found exactly once")
            bad += 1
            continue
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "gsd_mission.py").write_text(src.replace(needle, repl, 1), encoding="utf-8")
            r = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve())], capture_output=True, text=True,
                               env={**os.environ, "GSD_MISSION_DRILL_DIR": td}, timeout=300)
            red = r.returncode != 0 and f"FAIL {gate}" in r.stdout
            print(f"{'DRILL-PASS' if red else 'DRILL-FAIL'} {name}: {gate} {'red' if red else 'stayed green'}")
            bad += 0 if red else 1
    print(f"RETARGET_DRILLS={len(DRILLS) - bad}/{len(DRILLS)}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(drills() if "--drills" in sys.argv else main())
