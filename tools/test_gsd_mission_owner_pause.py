"""V-OP-*: `gsd_mission.py hold --stop` (owner_pause). Measured 2026-10-16 (m-f9290d78278f): an Owner hold left
the worker running, and a hand SIGTERM was resumed by the Claude daemon as a crash. An Owner pause must stop
the worker through the host and then park it; an unexpected death without a pause must still be recovered."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-mission-ownerpause-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_MISSION_RECOVERY"] = "off"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
gm.STOP_WAIT_S = 0
NOW = 1_800_000_000.0
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes, fails = passes + bool(cond), fails + (not cond)
    print(("PASS " if cond else "FAIL ") + gate + ("" if cond else f" :: {ev}"))


def running(mid: str) -> dict:
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    owner = {"session_id": f"{mid}-w", "pid": 4242, "proc_start": None, "heartbeat_at": NOW, "epoch": 1,
             "kind": "background"}
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                         state=gm.RUNNING, epoch=1, max_hours=100.0, owner=owner)


def row(mid: str) -> list[dict]:
    return [{"sessionId": f"{mid}-w", "id": f"{mid}-w"[:8], "kind": "background", "state": "busy", "pid": 4242}]


def gone(mid: str) -> list[dict]:
    """The host lists the worker as ended (DEAD by the host's word)."""
    return [{**row(mid)[0], "state": "stopped"}]


def main() -> int:
    # Arrange/Act: an Owner pause with a live background worker the host stops.
    running("m-op-stop")
    calls = []
    out = gm.owner_pause("m-op-stop", "Owner: review before more spend", now=NOW, sessions=row("m-op-stop"),
                         pid_alive=lambda pid: False, stop_runner=lambda argv: calls.append(argv))
    hold = gm.load("m-op-stop").get("owner_hold") or {}
    check("V-OP-STOPS-THROUGH-HOST", out["ok"] and any("stop" in a for a in calls)
          and hold.get("kind") == "owner_stop" and hold.get("worker_stopped_at") == NOW, f"{out} {calls} {hold}")

    # The dead owner of a paused mission is parked, not recovered (no respawn).
    # The host LISTS the stopped worker (a bare "not listed" is UNKNOWN, which is parked for any mission and so
    # would prove nothing).
    p = gm.plan_next(gm.load("m-op-stop"), NOW + 60, gone("m-op-stop"), pid_alive=lambda pid: False)
    check("V-OP-PAUSED-DEAD-OWNER-PARKED", p.get("action") == "none" and "stopped" in p.get("reason", ""), str(p))

    # Control: a plain Owner hold (no --stop) never stops anything.
    running("m-op-plain")
    calls.clear()
    gm.set_owner_hold("m-op-plain", "Owner park", now=NOW)
    check("V-OP-CONTROL-PLAIN-HOLD-NO-STOP", not calls and not gm.load("m-op-plain")["owner_hold"].get("worker_stopped_at"))

    # A stop the host cannot confirm (pid still alive): ok=False, the hold stands, nothing claims a stop.
    running("m-op-fail")
    out = gm.owner_pause("m-op-fail", "Owner pause", now=NOW, sessions=row("m-op-fail"),
                         pid_alive=lambda pid: True, stop_runner=lambda argv: None)
    h = gm.load("m-op-fail").get("owner_hold") or {}
    check("V-OP-STOP-FAILED-HOLD-STANDS", not out["ok"] and h.get("reason") and not h.get("worker_stopped_at"), f"{out} {h}")

    # Unexpected death WITHOUT a pause (host lists it ended): the supervisor still acts (not parked).
    running("m-op-crash")
    p = gm.plan_next(gm.load("m-op-crash"), NOW + 60, gone("m-op-crash"), pid_alive=lambda pid: False)
    check("V-OP-CRASH-STILL-RECOVERED", p.get("action") not in (None, "none"), str(p))

    print(f"OWNER_PAUSE_PASS={passes}/{passes + fails}  threshold=5/5")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
