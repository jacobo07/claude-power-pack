#!/usr/bin/env python
"""V-PL-* gates: the phase lease on the mission record (set_envelope) and its breaker in supervise.

CCR v5 Stage A, A2. Measured 2026-10-15: the phase stop-loss was ROADMAP prose, so one gsd-planner spent 24.0M of an
80M incident. These gates drive the real set_envelope / supervise / set_owner_hold path with a stubbed meter and a
real STATE.md. Every stop has a paired control that is left running.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-mission-phaselease-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ.pop("CPP_COST_HOLD_STOP", None)
os.environ["CPP_MISSION_RECOVERY"] = "off"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gsd_mission as gm  # noqa: E402
import mission_spend as ms  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None

passes = fails = 0
NOW = 1_800_000_000.0
BASE = 5_000_000
FORECAST = 1_000_000
STATE = Path(TMP) / "STATE.md"
SPEND: dict[str, object] = {}
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


def _meter(rec):
    v = SPEND[rec["mission_id"]]
    if isinstance(v, Exception):
        raise v
    if callable(v):
        return v()
    return v


ms.processed_tokens = _meter


def _phase(n: str) -> None:
    STATE.write_text(f"---\ncurrent_phase: {n} - test\n---\n", encoding="utf-8")


def _running(mid: str, lease: bool = True) -> dict:
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    owner = {"session_id": f"{mid}-w", "pid": None, "proc_start": None, "heartbeat_at": NOW,
             "epoch": 1, "kind": "background"}
    SPEND[mid] = BASE
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.RUNNING,
                  epoch=1, max_hours=100.0, owner=owner, token_estimate=1_000_000_000)
    if lease:
        return gm.set_envelope(mid, phase_lease={"phase": "1", "forecast": FORECAST, "state_file": str(STATE)}, now=NOW)
    return gm.load(mid)


def _row(mid: str) -> list[dict]:
    return [{"sessionId": f"{mid}-w", "id": f"{mid}-w"[:8], "kind": "background", "state": "running"}]


def _sweep(mid: str, stops: list):
    rows = gm.supervise(now=NOW + 60, sessions=_row(mid), runner=lambda *a, **k: "",
                        stop_runner=lambda a: stops.append(a), pid_alive=gone, gsd_status=OK_GSD,
                        fingerprint=lambda wd: None)
    return {x["mission_id"]: x for x in rows}.get(mid), gm.load(mid)


def main() -> int:
    _phase("1")
    # 1. set_envelope stores a lease whose base is MEASURED, never supplied.
    rec = _running("m-pl-set")
    pl = rec.get("phase_lease") or {}
    check("V-PL-SET-MEASURES-BASE", pl.get("base") == BASE and pl.get("forecast") == FORECAST
          and pl.get("set_by") == "envelope", str(pl))
    rec2 = gm.set_envelope("m-pl-set", phase_lease={"phase": "1", "forecast": FORECAST, "base": 0,
                                                    "state_file": str(STATE)}, now=NOW)
    check("V-PL-CALLER-BASE-IGNORED", rec2["phase_lease"]["base"] == BASE, "a caller-supplied base=0 is not used")
    seq = gm.load("m-pl-set")["seq"]
    for label, lease in (("zero-forecast", {"phase": "1", "forecast": 0, "state_file": str(STATE)}),
                         ("bad-phase", {"phase": "x", "forecast": 5, "state_file": str(STATE)}),
                         ("no-state-file", {"phase": "1", "forecast": 5, "state_file": ""})):
        try:
            gm.set_envelope("m-pl-set", phase_lease=lease, now=NOW)
            check(f"V-PL-REFUSES-{label}", False, "accepted")
        except gm.MissionError as exc:
            check(f"V-PL-REFUSES-{label}", "phase lease refused" in str(exc), str(exc)[:100])
    check("V-PL-REFUSAL-WRITES-NOTHING", gm.load("m-pl-set")["seq"] == seq, "record untouched by refusals")
    SPEND["m-pl-set"] = RuntimeError("meter down")
    try:
        gm.set_envelope("m-pl-set", phase_lease={"phase": "1", "forecast": 5, "state_file": str(STATE)}, now=NOW)
        check("V-PL-REFUSES-UNMEASURABLE-BASE", False, "accepted a lease with no measurable base")
    except gm.MissionError as exc:
        check("V-PL-REFUSES-UNMEASURABLE-BASE", "cannot measure" in str(exc), str(exc)[:100])

    # 2. over hard while the worker is LIVE: held and stopped in the SAME pass, with no grace flag on disk.
    _running("m-pl-hard")
    SPEND["m-pl-hard"] = BASE + int(FORECAST * 1.5) + 1
    stops: list = []
    row, r = _sweep("m-pl-hard", stops)
    hold = r.get("owner_hold") or {}
    check("V-PL-HARD-HOLDS-AND-STOPS", hold.get("phase_breaker") is True and hold.get("kind") == "cost"
          and hold.get("worker_stopped_at") and len(stops) == 1 and (row or {}).get("action") == "cost_hold_stop",
          f"hold={hold} stops={stops} row={(row or {}).get('action')}")
    check("V-PL-HOLD-NAMES-REFORECAST", "reforecast" in str(hold.get("resume_with")), str(hold.get("resume_with")))

    # 3. controls: under warn is left alone; a plain cost hold with no flag keeps its grace (not stopped).
    _running("m-pl-under")
    SPEND["m-pl-under"] = BASE + int(FORECAST * 0.5)
    stops = []
    row, r = _sweep("m-pl-under", stops)
    check("V-PL-CONTROL-UNDER-LEFT-RUNNING", not r.get("owner_hold") and not stops, f"hold={r.get('owner_hold')}")
    _running("m-pl-plain", lease=False)
    gm.set_owner_hold("m-pl-plain", "cost breaker: processed 9 > 2 x estimate 3", now=NOW, kind="cost")
    stops = []
    row, r = _sweep("m-pl-plain", stops)
    check("V-PL-CONTROL-PLAIN-COST-HOLD-KEEPS-GRACE", not stops and not (r["owner_hold"] or {}).get("worker_stopped_at"),
          f"stops={stops}")

    # 4. WARN is ledgered once per lease, holds nothing.
    _running("m-pl-warn")
    SPEND["m-pl-warn"] = BASE + int(FORECAST * 1.3)
    stops = []
    _, r1 = _sweep("m-pl-warn", stops)
    _, r2 = _sweep("m-pl-warn", stops)
    warns = [e for e in gm.lr.ledger_events("m-pl-warn") if e.get("event") == "phase_warn"]
    check("V-PL-WARN-ONCE-NO-HOLD", not r2.get("owner_hold") and not stops and r1.get("phase_lease_warned")
          and len(warns) == 1, f"phase_warn rows={len(warns)}")

    # 5. ambiguity is BLOCKED -> held + stopped, never permission.
    _running("m-pl-moved")
    SPEND["m-pl-moved"] = BASE + 10
    _phase("2")
    stops = []
    _, r = _sweep("m-pl-moved", stops)
    hold = r.get("owner_hold") or {}
    check("V-PL-PHASE-MOVED-BLOCKS", hold.get("verdict") == "BLOCKED" and len(stops) == 1, f"hold={hold} stops={stops}")
    _phase("1")
    _running("m-pl-unmeasured")
    SPEND["m-pl-unmeasured"] = RuntimeError("transcript unreadable")
    stops = []
    _, r = _sweep("m-pl-unmeasured", stops)
    check("V-PL-UNMEASURED-BLOCKS", (r.get("owner_hold") or {}).get("verdict") == "BLOCKED" and len(stops) == 1,
          f"hold={r.get('owner_hold')}")
    _phase("1")
    os.remove(STATE)
    _running("m-pl-nostate", lease=False)
    SPEND["m-pl-nostate"] = BASE + 10
    gm.transition("m-pl-nostate", expect_epoch=1, expect_state=gm.RUNNING, event="t_lease",
                  phase_lease={"phase": "1", "forecast": FORECAST, "warn": 1.2, "hard": 1.5, "reserve": 0, "base": BASE,
                               "state_file": str(STATE), "set_by": "envelope", "set_at": NOW})
    stops = []
    _, r = _sweep("m-pl-nostate", stops)
    check("V-PL-STATE-UNREADABLE-BLOCKS", (r.get("owner_hold") or {}).get("verdict") == "BLOCKED" and len(stops) == 1,
          f"hold={r.get('owner_hold')}")

    # 6. kernel-u1 task 3: the breakers are judged BEFORE the host is asked for its sessions.
    _phase("1")
    real_host = gm.host_sessions
    for mid, spend, label in (("m-pl-first-over", BASE + int(FORECAST * 1.5) + 1, "OVER"),
                              ("m-pl-first-under", BASE + 10, "CONTROL-UNDER")):
        _running(mid)
        SPEND[mid] = spend
        seen: dict = {}

        def fake_host(mid=mid, seen=seen):
            seen["held_at_host_call"] = bool((gm.load(mid) or {}).get("owner_hold"))
            return _row(mid)

        gm.host_sessions = fake_host
        try:
            gm.supervise(now=NOW + 60, sessions=None, runner=lambda *a, **k: "", stop_runner=lambda a: None,
                         pid_alive=gone, gsd_status=OK_GSD, fingerprint=lambda wd: None)
        finally:
            gm.host_sessions = real_host
        want = label == "OVER"
        check(f"V-PL-BREAKER-FIRST-{label}", seen.get("held_at_host_call") is want,
              f"held when the host was asked={seen.get('held_at_host_call')} (want {want})")

    # 7. one slow meter cannot starve the breakers of the other missions (CPP_SWEEP_BREAKER_MISSION_S).
    import time
    _running("m-pl-slow")
    SPEND["m-pl-slow"] = lambda: (time.sleep(1.5), BASE + 10)[1]
    _running("m-pl-fast-over")
    SPEND["m-pl-fast-over"] = BASE + int(FORECAST * 1.5) + 1
    os.environ["CPP_SWEEP_BREAKER_MISSION_S"] = "0.3"
    t0 = time.time()
    try:
        gm.supervise(now=NOW + 60, sessions=_row("m-pl-slow") + _row("m-pl-fast-over"), runner=lambda *a, **k: "",
                     stop_runner=lambda a: None, pid_alive=gone, gsd_status=OK_GSD, fingerprint=lambda wd: None)
    finally:
        os.environ.pop("CPP_SWEEP_BREAKER_MISSION_S", None)
    took = time.time() - t0
    timeouts = [e for e in gm.lr.ledger_events("m-pl-slow") if e.get("event") == "breaker_timeout"]
    check("V-PL-SLOW-METER-TIMES-OUT-LEDGERED", len(timeouts) == 1 and timeouts[0].get("limit_s") == 0.3,
          f"breaker_timeout rows={len(timeouts)}")
    check("V-PL-SLOW-METER-DOES-NOT-STARVE-OTHERS", bool((gm.load("m-pl-fast-over") or {}).get("owner_hold")),
          f"fast over-hard mission held={bool((gm.load('m-pl-fast-over') or {}).get('owner_hold'))} in {took:.2f}s")
    check("V-PL-SLOW-METER-CONTROL-NOT-HELD", not (gm.load("m-pl-slow") or {}).get("owner_hold"),
          "the timed-out mission is skipped this pass, not held")

    print(f"PHASE_LEASE_MISSION_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    shutil.rmtree(TMP, ignore_errors=True)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
