#!/usr/bin/env python
"""V-PROTO-* gates for `gsd_mission.py protocol --mission <id> --rollover-protocol capsule-v2`.

Hermetic, like test_gsd_mission_owner_hold.py: state goes to a temp dir BEFORE import, the pid probe is
injected. Every refusal has a paired control, so a module that refuses (or allows) everything cannot go
green. Mutation drill: GSD_MISSION_DRILL_DIR holds a mutated copy of gsd_mission.py.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-mission-proto-test-")
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

passes = fails = 0
NOW = 1_800_000_000.0
gone = lambda pid: False   # noqa: E731
alive = lambda pid: True   # noqa: E731


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def _mission(mid: str, mode: str = "auto") -> dict:
    """A RUNNING mission with an interactive-kind owner (pid 4242): liveness is decided by the pid probe."""
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW, permission_mode=mode)
    owner = {"session_id": f"{mid}-w", "pid": 4242, "proc_start": None, "heartbeat_at": NOW,
             "epoch": 1, "kind": "interactive"}
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                         state=gm.RUNNING, epoch=1, owner=owner)


def _refused(fn) -> bool:
    try:
        fn()
    except gm.MissionError:
        return True
    return False


def main() -> int:
    # 1. held mission with a live-looking owner: set succeeds; the record and the ledger carry it.
    rec = _mission("m-held")
    check("V-PROTO-LEGACY-ABSENT", "rollover_protocol" not in rec)
    gm.set_owner_hold("m-held", "park for protocol", now=NOW)
    out = gm.set_rollover_protocol("m-held", gm.CAPSULE_V2, now=NOW, sessions=[], pid_alive=alive)
    check("V-PROTO-HELD-SET", out.get("rollover_protocol") == gm.CAPSULE_V2 and out.get("owner_hold"),
          str(out.get("rollover_protocol")))
    check("V-PROTO-IDENTITY-KEPT", out["state"] == gm.RUNNING and out["epoch"] == 1
          and gm.load("m-held")["rollover_protocol"] == gm.CAPSULE_V2)
    led = Path(gm.lr.ledger_path()).read_text(encoding="utf-8-sig", errors="replace")
    check("V-PROTO-LEDGER-EVENT", "rollover_protocol_set" in led and "m-held" in led)

    # 2. not held, owner alive: refused and unchanged; control: same record, owner gone -> allowed.
    _mission("m-live")
    check("V-PROTO-LIVE-OWNER-REFUSED",
          _refused(lambda: gm.set_rollover_protocol("m-live", gm.CAPSULE_V2, now=NOW, sessions=[], pid_alive=alive)))
    check("V-PROTO-REFUSAL-LEAVES-RECORD", "rollover_protocol" not in gm.load("m-live"))
    out = gm.set_rollover_protocol("m-live", gm.CAPSULE_V2, now=NOW, sessions=[], pid_alive=gone)
    check("V-PROTO-DEAD-OWNER-ALLOWED", out.get("rollover_protocol") == gm.CAPSULE_V2)

    # 3. no owner at all (PREPARED) is allowed.
    gm.create(TMP, "/gsd-autonomous", mission_id="m-pre", now=NOW, permission_mode="bypassPermissions")
    check("V-PROTO-NO-OWNER-ALLOWED",
          gm.set_rollover_protocol("m-pre", gm.CAPSULE_V2, now=NOW)["rollover_protocol"] == gm.CAPSULE_V2)

    # 4. unknown protocol refused (a held mission, so only the protocol can be the cause).
    check("V-PROTO-UNKNOWN-REFUSED", _refused(lambda: gm.set_rollover_protocol("m-held", "capsule-v9", now=NOW)))

    # 5. permission-mode rule of arm: acceptEdits cannot run the successor's exam.
    gm.create(TMP, "/gsd-autonomous", mission_id="m-mode", now=NOW, permission_mode="acceptEdits")
    check("V-PROTO-MODE-REFUSED", _refused(lambda: gm.set_rollover_protocol("m-mode", gm.CAPSULE_V2, now=NOW)))

    # 6. unknown mission refused.
    check("V-PROTO-NO-MISSION-REFUSED", _refused(lambda: gm.set_rollover_protocol("m-nope", gm.CAPSULE_V2)))

    print(f"PROTOCOL_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
