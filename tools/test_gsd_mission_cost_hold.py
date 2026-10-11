#!/usr/bin/env python
"""V-CH-* gates for spec vault/specs/mission-cost-hold-stops-worker.md.

Measured 2026-10-11 (TUA-X m-560939805e63): the cost breaker held the mission at 74.5M processed and its
busy worker autocompacted on in one turn to 265.5M; the estimate it was judged against (36M) had been typed
with no look at the lineage's ~243M. These gates make the hold reach the worker, stop it past the grace,
park (not settle) what it stopped, and refuse an estimate far below the lineage's measured cost.

Hermetic like test_gsd_mission_owner_hold.py. Every refusal or stop has a paired control.
Mutation drill: GSD_MISSION_DRILL_DIR holding a mutated gsd_mission.py is imported instead of the real one.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-mission-costhold-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ.pop("CPP_COST_HOLD_STOP", None)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None

passes = fails = 0
NOW = 1_800_000_000.0
gone = lambda pid: False  # noqa: E731
OK_GSD = lambda cwd, workstream=None: {"outcome": "OK"}  # noqa: E731
TRIP = "cost breaker: processed 74,491,187 > 2 x estimate 36,000,000; explain the variance"


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def _running(mid: str) -> dict:
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    owner = {"session_id": f"{mid}-w", "pid": None, "proc_start": None, "heartbeat_at": NOW,
             "epoch": 1, "kind": "background"}
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                         state=gm.RUNNING, epoch=1, max_hours=100.0, owner=owner)


def _row(mid: str, state: str) -> list[dict]:
    return [{"sessionId": f"{mid}-w", "id": f"{mid}-w"[:8], "kind": "background", "state": state}]


def _flag(mid: str, asked_s: float, n: int = 1, set_at: float | None = None) -> None:
    """A first-notice flag for the mission's CURRENT hold (or for `set_at`, to fake an earlier hold)."""
    if set_at is None:
        set_at = (gm.load(mid).get("owner_hold") or {}).get("set_at")
    Path(TMP, f"mission-costhold-{mid}-w.flag").write_text(
        json.dumps({"asked_at": asked_s * 1000, "n": n, "hold_set_at": set_at}), encoding="utf-8")


def _hook(sid: str) -> dict | None:
    js = (f"const m=require({json.dumps(str(HERE.parent / 'hooks' / 'mission_wall.js'))});"
          f"process.stdout.write(JSON.stringify(m.decide({{session_id:{json.dumps(sid)}}})))")
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60,
                         env={**os.environ, "GSD_AUTORUN_MARKER_DIR": TMP, "GSD_LONG_RUN_STATE_DIR": TMP})
    return json.loads(out.stdout or "null")


def main() -> int:
    import gsd_epoch as ge

    # 1. hook: cost hold -> COST HOLD block even under the wall; Owner hold and no hold -> nothing.
    for mid, hold, kind in (("m-hk-cost", TRIP, "cost"), ("m-hk-owner", "Owner park for review", None),
                            ("m-hk-none", None, None)):
        _running(mid)
        if hold:
            gm.set_owner_hold(mid, hold, now=NOW, kind=kind)
        Path(TMP, f"gsd-autorun-{mid}-w.json").write_text(
            json.dumps({"mission_id": mid, "epoch": 1, "wall": {"advisory": 40}}), encoding="utf-8")
    d = _hook("m-hk-cost-w")
    check("V-CH-HOOK-COST-BLOCKS", bool(d) and d.get("decision") == "block" and "COST HOLD" in d.get("reason", ""),
          str(d)[:160])
    flag = Path(TMP, "mission-costhold-m-hk-cost-w.flag")
    first = json.loads(flag.read_text(encoding="utf-8")) if flag.exists() else {}
    d2 = _hook("m-hk-cost-w")
    second = json.loads(flag.read_text(encoding="utf-8")) if flag.exists() else {}
    check("V-CH-HOOK-KEEPS-FIRST-NOTICE", first.get("asked_at") and second.get("asked_at") == first.get("asked_at")
          and second.get("n") == 2 and "NOTICE 2" in (d2 or {}).get("reason", ""), f"{first} -> {second}")
    check("V-CH-CONTROL-HOOK-OWNER-HOLD-SILENT", _hook("m-hk-owner-w") is None)
    check("V-CH-CONTROL-HOOK-UNHELD-SILENT", _hook("m-hk-none-w") is None)

    # 1b. a worker with NO v2 marker (resume command over the 200-char typing limit, m-560939805e63) is
    # still reached through the worker index; the index carries no command. Control: neither file -> silent.
    _running("m-hk-idx")
    gm.set_owner_hold("m-hk-idx", TRIP, now=NOW, kind="cost")
    idx = gm.write_worker_index(gm.load("m-hk-idx"), "m-hk-idx-w")
    body = json.loads(idx.read_text(encoding="utf-8")) if idx else {}
    check("V-CH-INDEX-WRITTEN-NO-COMMAND", body.get("mission_id") == "m-hk-idx" and "resume_command" not in body
          and "command" not in body, str(body))
    d = _hook("m-hk-idx-w")
    check("V-CH-HOOK-REACHES-WORKER-VIA-INDEX", bool(d) and "COST HOLD" in (d or {}).get("reason", ""), str(d)[:120])
    check("V-CH-CONTROL-HOOK-NO-MARKER-NO-INDEX-SILENT", _hook("m-nobody-w") is None)

    # 2. cost_hold_overdue: past grace -> dict; within grace / no flag -> None.
    r = gm.load("m-hk-cost")
    _flag("m-hk-cost", NOW - 700)
    over = ge.cost_hold_overdue(r, NOW)
    check("V-CH-OVERDUE-PAST-GRACE", bool(over) and over["overdue_s"] == 100, str(over))
    _flag("m-hk-cost", NOW - 60)
    check("V-CH-CONTROL-WITHIN-GRACE", ge.cost_hold_overdue(r, NOW) is None)
    check("V-CH-CONTROL-NO-FLAG", ge.cost_hold_overdue(gm.load("m-hk-none"), NOW) is None)
    _flag("m-hk-cost", NOW - 7000, set_at=NOW - 9000)   # left by an earlier, released hold
    check("V-CH-STALE-FLAG-IGNORED", ge.cost_hold_overdue(r, NOW) is None)

    # 2b. the progress fingerprint covers add_dirs (m-4a0f39b59a60: commits in the add-dir read as no progress).
    trees = {"/base": "b1", "/extra": "e1"}
    fpf = lambda d: trees.get(d)  # noqa: E731
    plain_rec, multi_rec = {"add_dirs": []}, {"add_dirs": ["/extra"]}
    check("V-CH-CONTROL-FP-NO-ADDDIRS-UNCHANGED", gm.mission_fingerprint(plain_rec, "/base", fpf) == "b1")
    before = gm.mission_fingerprint(multi_rec, "/base", fpf)
    trees["/extra"] = "e2"
    check("V-CH-FP-SEES-ADDDIR-CHANGE", before and gm.mission_fingerprint(multi_rec, "/base", fpf) != before,
          f"{before}")
    check("V-CH-FP-ALL-UNMEASURED-NONE", gm.mission_fingerprint(multi_rec, "/nope", lambda d: None) is None)

    # 3. supervise: cost hold + LIVE + overdue -> stopped once, parked; Owner hold + same -> untouched.
    for mid, hold, kind in (("m-sv-cost", TRIP, "cost"), ("m-sv-owner", "Owner park for review", None)):
        _running(mid)
        gm.set_owner_hold(mid, hold, now=NOW, kind=kind)
        _flag(mid, NOW - 700)
    stops = []
    rows = gm.supervise(now=NOW, sessions=_row("m-sv-cost", "running") + _row("m-sv-owner", "running"),
                        runner=lambda *a, **k: "", stop_runner=lambda a: stops.append(a), pid_alive=gone,
                        gsd_status=OK_GSD, fingerprint=lambda wd: None)
    by = {x["mission_id"]: x for x in rows}
    c = gm.load("m-sv-cost")
    check("V-CH-SUPERVISE-STOPS-COST-HELD", len([s for s in stops if "m-sv-cos"[:8] in " ".join(s)]) == 1
          and by["m-sv-cost"].get("action") == "cost_hold_stop" and (c.get("owner_hold") or {}).get("worker_stopped_at"),
          f"stops={stops} row={by.get('m-sv-cost')}")
    check("V-CH-CONTROL-OWNER-HOLD-NOT-STOPPED", not any("m-sv-own"[:8] in " ".join(s) for s in stops)
          and not (gm.load("m-sv-owner").get("owner_hold") or {}).get("worker_stopped_at"), str(stops))

    # 4. a worker WE stopped is parked, not settled; without the mark the old settle stands.
    p = gm.plan_next(c, NOW + 60, _row("m-sv-cost", "done"), pid_alive=gone)
    check("V-CH-STOPPED-PARKED-NOT-SETTLED", p["action"] == "none" and "parked" in p["reason"], str(p))
    _running("m-sv-plain")
    plain = gm.set_owner_hold("m-sv-plain", TRIP, now=NOW, kind="cost")
    p = gm.plan_next(plain, NOW + 60, _row("m-sv-plain", "done"), pid_alive=gone)
    check("V-CH-CONTROL-UNSTOPPED-DEAD-SETTLES", p["action"] == "settle", str(p))
    rel = gm.release_owner_hold("m-sv-cost", now=NOW + 120)
    p = gm.plan_next(rel, NOW + 180, _row("m-sv-cost", "done"), pid_alive=gone)
    check("V-CH-RELEASE-REPLACES", p["action"] == "replace", str(p))

    # 5. calibration against the supersedes chain.
    gm.create(TMP, "/gsd-autonomous", mission_id="m-cal-p", now=NOW)
    gm.transition("m-cal-p", expect_epoch=0, expect_state=gm.PREPARED, event="t_done", now=NOW + 24 * 3600,
                  state=gm.HALTED, reason="test")
    for mid, sup in (("m-cal", "m-cal-p"), ("m-cal-new", None)):
        gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
        gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_sup", now=NOW,
                      supersedes=sup, max_hours=12.0)
    meas = lambda rr: 240_000_000 if rr["mission_id"] == "m-cal-p" else None  # noqa: E731
    try:
        gm.set_envelope("m-cal", token_estimate="36M", now=NOW, measure=meas)
        check("V-CH-CALIBRATION-REFUSES-LOW", False, "36M accepted against 120M expected")
    except gm.MissionError as exc:
        check("V-CH-CALIBRATION-REFUSES-LOW", "120,000,000 expected" in str(exc), str(exc)[:200])
    e = gm.set_envelope("m-cal", token_estimate="36M", now=NOW, measure=meas,
                        estimate_basis="phases 10.1-10.5 are docs-only")
    check("V-CH-BASIS-ACCEPTS-AND-STORES", e["token_estimate"] == 36_000_000
          and e.get("token_estimate_basis") == "phases 10.1-10.5 are docs-only"
          and "120,000,000 expected" in (e.get("token_estimate_calibration") or ""), str(e.get("token_estimate_calibration")))
    e = gm.set_envelope("m-cal", token_estimate="80M", now=NOW, measure=meas)
    check("V-CH-CONTROL-ADEQUATE-ACCEPTED", e["token_estimate"] == 80_000_000)
    e = gm.set_envelope("m-cal-new", token_estimate="2M", now=NOW, measure=meas)
    check("V-CH-NO-HISTORY-ACCEPTED-NAMED", e["token_estimate"] == 2_000_000
          and "no lineage history" in (e.get("token_estimate_calibration") or ""), str(e.get("token_estimate_calibration")))

    print(f"COST_HOLD_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    shutil.rmtree(TMP, ignore_errors=True)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
