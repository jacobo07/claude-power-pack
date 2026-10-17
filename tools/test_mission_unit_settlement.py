#!/usr/bin/env python
"""V-SETTLE-* gates (stage M4 part A of the knowledge-acquisition plan).

When a mission's GSD phase advances, the finished phase is settled into the mission's work-class profile
(tools/work_class_profile.py) BEFORE the next phase is admitted: processed = measured spend since the previous
settlement mark, forecast = the phase lease's forecast when one covered that phase, cause "phase N complete".
Unmeasured spend writes `unit_settle_unmeasured` and never a zero sample.

Hermetic like test_gsd_mission_resources.py. Mutation drill: GSD_MISSION_DRILL_DIR holding a mutated gsd_mission.py.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-mission-settle-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_MISSION_RECOVERY"] = "off"
PROFILE = Path(TMP) / "not-yet-created" / "profile"      # absent on purpose: the store must create it
os.environ["CPP_WORK_CLASS_PROFILE_DIR"] = str(PROFILE)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402
import mission_spend as ms  # noqa: E402
import phase_lease as pls  # noqa: E402
import work_class_profile as wcp  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
SPENT: dict = {}
ms.processed_tokens = lambda rec, *a, **k: SPENT.get(rec["mission_id"])

passes = fails = 0
NOW = 1_800_000_000.0
gone = lambda pid: False  # noqa: E731
OK_GSD = lambda cwd, workstream=None: {"outcome": "OK"}  # noqa: E731


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def _state(cwd: Path, phase) -> Path:
    p = cwd / ".planning" / "STATE.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"---\ncurrent_phase: {phase}\n---\n", encoding="utf-8")
    return p


def _mission(mid: str, phase, *, lease: dict | None = None, mark: dict | None = None, wc: str | None = None) -> dict:
    cwd = Path(TMP) / mid
    cwd.mkdir(parents=True, exist_ok=True)
    sf = _state(cwd, phase)
    gm.create(str(cwd), "/gsd-autonomous", mission_id=mid, now=NOW)
    owner = {"session_id": f"{mid}-w", "pid": None, "proc_start": None, "heartbeat_at": NOW,
             "epoch": 1, "kind": "background"}
    extra: dict = {"token_estimate": 10**12}
    if lease:
        extra["phase_lease"] = pls.make_lease(phase=lease["phase"], forecast=lease["forecast"], base=lease["base"],
                                              state_file=str(sf), set_at=NOW)
    if mark:
        extra["unit_settlement"] = mark
    if wc:
        extra["work_class"] = wc
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.RUNNING,
                         epoch=1, max_hours=100.0, owner=owner, **extra)


def _sup(launches: list) -> dict:
    done = [{"sessionId": f"{m['mission_id']}-w", "id": f"{m['mission_id']}-w"[:8], "kind": "background",
             "state": "done"} for m in gm.all_missions()]
    rows = gm.supervise(now=NOW + 60, sessions=done, runner=lambda *a, **k: launches.append(a) or "",
                        stop_runner=lambda a: None, pid_alive=gone, gsd_status=OK_GSD, fingerprint=lambda wd: None)
    return {r["mission_id"]: r for r in rows}


def _events(mid: str) -> list[str]:
    return [e.get("event") for e in gm.lr.ledger_events(mid)]


def _samples(cls: str) -> list[dict]:
    return wcp._load(cls)["samples"]


def main() -> int:
    check("V-SETTLE-ABSENT-PROFILE-DIR-PRECONDITION", not PROFILE.exists(), str(PROFILE))

    # ADVANCE-SETTLES: lease for phase 2 (base 1,000,000, forecast 3,000,000); GSD is on 3; spend 5,200,000.
    mid = "m-set-advance"
    _mission(mid, 3, lease={"phase": 2, "forecast": 3_000_000, "base": 1_000_000})
    SPENT[mid] = 5_200_000
    launches: list = []
    _sup(launches)
    s = [x for x in _samples("GSD_RESUME") if x["unit_id"] == f"{mid}-phase-2"]
    rec = gm.load(mid)
    check("V-SETTLE-ADVANCE-SETTLES", len(s) == 1 and s[0]["processed"] == 4_200_000
          and s[0]["receipt"]["forecast"] == 3_000_000 and "phase 2 complete" in s[0]["receipt"]["cause"],
          f"samples={[(x['unit_id'], x['processed']) for x in _samples('GSD_RESUME')]}")
    mark = rec.get("unit_settlement") or {}
    check("V-SETTLE-MARK-RECORDED", str(mark.get("phase")) == "3" and mark.get("processed") == 5_200_000, str(mark))
    check("V-SETTLE-ABSENT-PROFILE-DIR-CREATED", PROFILE.is_dir() and any(PROFILE.iterdir()), "store created on first settle")

    # IDEMPOTENT: a second pass with the same phase writes nothing more.
    _sup(launches)
    n = len([x for x in _samples("GSD_RESUME") if x["unit_id"].startswith(f"{mid}-")])
    check("V-SETTLE-IDEMPOTENT", n == 1 and _events(mid).count("unit_settled") == 1, f"samples={n} events={_events(mid)}")

    # The mark carries the next unit: phase 3 -> 4 settles the delta since the mark, with no lease forecast.
    mid = "m-set-chain"
    _mission(mid, 4, mark={"phase": "3", "processed": 5_200_000, "at": NOW, "work_class": "GSD_RESUME"})
    SPENT[mid] = 6_000_000
    _sup(launches)
    s3 = [x for x in _samples("GSD_RESUME") if x["unit_id"] == f"{mid}-phase-3"]
    check("V-SETTLE-DELTA-FROM-MARK", len(s3) == 1 and s3[0]["processed"] == 800_000 and s3[0]["receipt"]["forecast"] is None,
          f"{[(x['processed'], x['receipt']['forecast']) for x in s3]}")

    # NO-ADVANCE-NO-SETTLE
    mid = "m-set-noadvance"
    _mission(mid, 3, mark={"phase": "3", "processed": 100_000, "at": NOW, "work_class": "GSD_RESUME"})
    SPENT[mid] = 900_000
    before = len(_samples("GSD_RESUME"))
    _sup(launches)
    check("V-SETTLE-NO-ADVANCE-NO-SETTLE", len(_samples("GSD_RESUME")) == before and "unit_settled" not in _events(mid)
          and (gm.load(mid).get("unit_settlement") or {}).get("processed") == 100_000, f"events={_events(mid)}")

    # UNMEASURED-NOT-ZERO
    mid = "m-set-unmeasured"
    _mission(mid, 3, mark={"phase": "2", "processed": 100_000, "at": NOW, "work_class": "GSD_RESUME"})
    SPENT[mid] = None
    before = len(_samples("GSD_RESUME"))
    _sup(launches)
    _sup(launches)
    evs = _events(mid)
    check("V-SETTLE-UNMEASURED-NOT-ZERO", len(_samples("GSD_RESUME")) == before and evs.count("unit_settle_unmeasured") == 1
          and "unit_settled" not in evs and (gm.load(mid).get("unit_settlement") or {}).get("phase") == "2",
          f"events={evs}")

    # ORDER: no lease, mark says phase 2, GSD on 3 -> the receipt precedes the relaunch of the next phase.
    mid = "m-set-order"
    _mission(mid, 3, mark={"phase": "2", "processed": 0, "at": NOW, "work_class": "GSD_RESUME"})
    SPENT[mid] = 2_000_000
    launches = []
    row = _sup(launches).get(mid, {})
    evs = _events(mid)
    i = evs.index("unit_settled") if "unit_settled" in evs else -1
    later = [e for e in evs[i + 1:] if "launch" in str(e)] if i >= 0 else []
    check("V-SETTLE-ORDER", i >= 0 and bool(later) and not [e for e in evs[:i] if "launch" in str(e) and e != "launch_gate_unavailable"],
          f"action={row.get('action')} events={evs}")

    # Class selection: the record's work_class wins over the GSD_RESUME default.
    mid = "m-set-class"
    _mission(mid, 3, mark={"phase": "2", "processed": 0, "at": NOW}, wc="COMPILED_UNIT")
    SPENT[mid] = 1_500_000
    _sup(launches)
    check("V-SETTLE-WORK-CLASS-FIELD", any(x["unit_id"] == f"{mid}-phase-2" for x in _samples("COMPILED_UNIT")), "")

    # Next lease forecast comes from the profile once the class has samples.
    try:
        lf = wcp.lease_forecast("GSD_RESUME")
    except wcp.ProfileError as exc:
        lf = {"forecast": 0, "basis": str(exc)}
    rec = gm.load("m-set-advance")
    check("V-SETTLE-NEXT-FORECAST-FROM-PROFILE", (rec.get("unit_settlement") or {}).get("next_forecast") is not None
          and lf["forecast"] > 0, f"next={(rec.get('unit_settlement') or {}).get('next_forecast')} lease_forecast={lf}")

    print(f"SETTLE_PASS={passes}/{passes + fails}  threshold=N/N")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
