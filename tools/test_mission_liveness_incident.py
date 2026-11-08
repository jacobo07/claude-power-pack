#!/usr/bin/env python
"""V-LIVE-* gates (stage M4 part B of the knowledge-acquisition plan).

An open mission whose worker is positively DEAD, with an actionable obligation, Owner authority with room and no
blocking hold, takes the ordinary relay/replace path. If anything still prevents the launch, ONE `liveness_incident`
row names the blocking condition (deduplicated per condition key). Authority without room for a minimum lease is
CAPITAL_EXHAUSTED at the Owner boundary, never a launch. A resource wait or a cost hold is a named wait, not an incident.

Hermetic like test_gsd_mission_resources.py. Mutation drill: GSD_MISSION_DRILL_DIR holding a mutated gsd_mission.py.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-mission-live-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_MISSION_RECOVERY"] = "off"
os.environ["CPP_WORK_CLASS_PROFILE_DIR"] = str(Path(TMP) / "profile")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402
import mission_spend as ms  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
SPENT: dict = {}
ms.processed_tokens = lambda rec, *a, **k: SPENT.get(rec["mission_id"])
try:
    import mission_resources as mres  # noqa: E402
    mres.PROBES.update({"path_exists": lambda arg: False})
except ImportError:
    mres = None

passes = fails = 0
NOW = 1_800_000_000.0
gone = lambda pid: False  # noqa: E731
OK_GSD = lambda cwd, workstream=None: {"outcome": "OK"}  # noqa: E731
NO_GSD = lambda cwd, workstream=None: {"outcome": "UNAVAILABLE", "reason": "gsd query timed out"}  # noqa: E731


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def _dead(mid: str, *, authority=20_000_000, spent=1_000_000, requires=None) -> dict:
    cwd = Path(TMP) / mid
    cwd.mkdir(parents=True, exist_ok=True)
    gm.create(str(cwd), "/gsd-autonomous", mission_id=mid, now=NOW)
    owner = {"session_id": f"{mid}-w", "pid": None, "proc_start": None, "heartbeat_at": NOW,
             "epoch": 1, "kind": "background"}
    extra: dict = {"token_estimate": authority, "authority_tokens": authority}
    if requires is not None:
        extra["requires"] = requires
    SPENT[mid] = spent
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.RUNNING,
                         epoch=1, max_hours=100.0, owner=owner, **extra)


class _Out:
    def __init__(self, out, rc=0):
        self.stdout, self.stderr, self.returncode = out, "", rc


def _runner(launches: list):
    def run(argv, cwd):
        launches.append(argv)
        return _Out(f"backgrounded · 9e9e9e9e · {argv[argv.index('-n') + 1]}")
    return run


def _sup(launches: list, gsd=OK_GSD) -> dict:
    done = [{"sessionId": f"{m['mission_id']}-w", "id": f"{m['mission_id']}-w"[:8], "kind": "background",
             "state": "done"} for m in gm.all_missions()]
    rows = gm.supervise(now=NOW + 60, sessions=done, runner=_runner(launches),
                        stop_runner=lambda a: None, pid_alive=gone, gsd_status=gsd, fingerprint=lambda wd: None)
    return {r["mission_id"]: r for r in rows}


def _incidents(mid: str) -> list[dict]:
    return [e for e in gm.lr.ledger_events(mid) if e.get("event") == "liveness_incident"]


def main() -> int:
    # DEAD-ACTIONABLE-AUTHORITY-RELAUNCHES: the ordinary path replaces the dead worker; nothing to report.
    mid = "m-live-ok"
    _dead(mid)
    launches: list = []
    row = _sup(launches).get(mid, {})
    check("V-LIVE-DEAD-ACTIONABLE-AUTHORITY-RELAUNCHES", row.get("action") == "replace" and "launch" in row
          and len(launches) >= 1 and not _incidents(mid), f"action={row.get('action')} launches={len(launches)}")

    # DEAD-NOTHING-ACTIONABLE-WAITS: every obligation WAIT_RESOURCE -> resource hold, no launch, no incident.
    mid = "m-live-wait"
    reqs = [{"id": "O1-path-1", "kind": "path_exists", "arg": "Z:/never", "obligation": "O1"}] if mres else None
    _dead(mid, requires=reqs)
    launches = []
    row = _sup(launches).get(mid, {})
    hold = gm.load(mid).get("owner_hold") or {}
    check("V-LIVE-DEAD-NOTHING-ACTIONABLE-WAITS", hold.get("kind") == "resource" and not launches
          and row.get("action") == "none" and not _incidents(mid),
          f"hold={hold.get('kind')} action={row.get('action')} launches={len(launches)} incidents={len(_incidents(mid))}")

    # DEAD-COST-HOLD-NO-RELAUNCH (control): a cost hold still blocks every launch path.
    mid = "m-live-cost"
    _dead(mid)
    gm.set_owner_hold(mid, "cost breaker: test hold", now=NOW, kind="cost")
    launches = []
    row = _sup(launches).get(mid, {})
    check("V-LIVE-DEAD-COST-HOLD-NO-RELAUNCH", row.get("action") not in ("launch", "replace", "relay") and not launches
          and "launch" not in row, f"action={row.get('action')} launches={len(launches)}")

    # DEAD-NO-AUTHORITY-ROOM: 1.0M left of 10M authority < minimum lease / (1 - reserve): no launch, CAPITAL_EXHAUSTED.
    mid = "m-live-capital"
    _dead(mid, authority=10_000_000, spent=9_000_000)
    launches = []
    row = _sup(launches).get(mid, {})
    rec = gm.load(mid)
    hold = rec.get("owner_hold") or {}
    inc = _incidents(mid)
    check("V-LIVE-DEAD-NO-AUTHORITY-ROOM", not launches and "launch" not in row and gm.is_cost_hold(hold)
          and "CAPITAL_EXHAUSTED" in str(hold.get("reason")) + str(hold.get("wait_type"))
          and len(inc) == 1 and inc[0].get("key") == "CAPITAL_EXHAUSTED" and hold.get("authority_kind") == "OWNER",
          f"action={row.get('action')} hold={str(hold.get('reason'))[:90]} incidents={len(inc)}")

    # Control: room exactly at the minimum is not exhaustion (the same record shape, authority left).
    mid = "m-live-room"
    _dead(mid, authority=10_000_000, spent=8_000_000)
    launches = []
    row = _sup(launches).get(mid, {})
    check("V-LIVE-AUTHORITY-WITH-ROOM-NOT-EXHAUSTED", row.get("action") == "replace" and not _incidents(mid),
          f"action={row.get('action')}")

    # INCIDENT-ONCE: the launch is held by an unanswered GSD query; the same blocker twice is ONE named row.
    mid = "m-live-once"
    _dead(mid)
    launches = []
    row = _sup(launches, NO_GSD).get(mid, {})
    _sup(launches, NO_GSD)
    inc = _incidents(mid)
    check("V-LIVE-INCIDENT-ONCE", len(inc) == 1 and "UNAVAILABLE" in str(inc[0].get("why")) and not launches,
          f"incidents={len(inc)} held={row.get('held')} why={[i.get('why') for i in inc]}")

    # A different blocker is a different condition: it adds its own row.
    mid = "m-live-two"
    _dead(mid)
    launches = []
    _sup(launches, NO_GSD)
    _sup(launches, lambda cwd, workstream=None: {"outcome": "NO_PHASES", "reason": "roadmap has no phases"})
    keys = {i.get("key") for i in _incidents(mid)}
    check("V-LIVE-INCIDENT-PER-CONDITION", len(keys) == 2, f"keys={keys}")

    print(f"LIVE_PASS={passes}/{passes + fails}  threshold=N/N")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
