#!/usr/bin/env python
"""V-S9-WAIT-* gates: durable waits, checkpoint states and the Mission Workset (wave S9, Lane A1-A3).

Origins (2026-11-01, GEX44):
  * not_before parked a mission only when no live worker remained; an IDLE live worker kept receiving
    continuations through a known clock wait (resource_gate returned early for any non-DEAD owner);
  * m-f9560b5e8f1f: wave S8 closed, three fresh workers found nothing to run, the mission went HALTED
    no_progress (terminal) -- wave completion misread as a stall;
  * m-f9560b5e8f1f was armed in gen3-pp with add_dirs [] while its product commits landed in t1-campaign.

Hermetic: state in a temp dir before import, host rows and the stop runner injected. Every new behaviour has a paired
control so a module that parks (or never parks) everything cannot go green.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-mission-s9-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_MISSION_RECOVERY"] = "off"
os.environ.pop("CPP_WAIT_PARK_LIVE", None)
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402
import mission_resources as mres  # noqa: E402

gm.host_sessions = lambda *a, **k: None   # hermetic: the real host is never asked (an unanswerable host is the case)

passes = fails = 0
NOW = 1_800_000_000.0
gone = lambda pid: False   # noqa: E731
FUTURE = "2027-01-15T08:00:00+00:00"   # after NOW (2027-01-15T08:00:00Z == 1_800_000_000)
CLOCK = {**mres.PROBES, "not_before": lambda _a: NOW - 3600}   # one hour before the wait ends


def check(gate, cond, ev=""):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def _running(mid: str, max_hours: float = 24.0) -> dict:
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    owner = {"session_id": f"{mid}-w", "pid": None, "proc_start": None, "heartbeat_at": NOW, "epoch": 1,
             "kind": "background"}
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.RUNNING,
                         epoch=1, max_hours=max_hours, owner=owner)


def _row(mid: str, status: str) -> list[dict]:
    return [{"sessionId": f"{mid}-w", "id": f"{mid}-w"[:8], "status": status, "state": "running",
             "kind": "background"}]


def main() -> int:
    # 1. A live IDLE owner under an unmet clock is parked AND stopped (lease released); WAIT_TIME is typed.
    rec = _running("m-idle")
    gm.set_requires("m-idle", "O-1", [("not_before", FUTURE)], now=NOW)
    stops: list = []
    out = gm.resource_gate(gm.load("m-idle"), NOW, sessions=_row("m-idle", "idle"), pid_alive=gone,
                           probes=CLOCK, stop_runner=lambda argv: stops.append(argv))
    hold = out.get("owner_hold") or {}
    check("V-S9-WAIT-IDLE-LIVE-PARKED", hold.get("kind") == "resource" and hold.get("wait_type") == "WAIT_TIME",
          str({k: hold.get(k) for k in ("kind", "wait_type")}))
    check("V-S9-WAIT-IDLE-LIVE-STOPPED", bool(stops) and bool(hold.get("worker_stopped_at")), f"stops={stops}")
    p = gm.plan_next(out, NOW + 60, [], pid_alive=gone)
    check("V-S9-WAIT-STOPPED-NOT-SETTLED", p["action"] == "none" and "WAIT_TIME" in p["reason"], str(p))

    # 1b. Control: a BUSY live owner is not parked or stopped (its turn finishes first).
    _running("m-busy")
    gm.set_requires("m-busy", "O-1", [("not_before", FUTURE)], now=NOW)
    stops2: list = []
    out2 = gm.resource_gate(gm.load("m-busy"), NOW, sessions=_row("m-busy", "busy"), pid_alive=gone,
                            probes=CLOCK, stop_runner=lambda argv: stops2.append(argv))
    check("V-S9-WAIT-BUSY-NOT-PARKED", not out2.get("owner_hold") and not stops2, str(out2.get("owner_hold")))

    # 1c. Control: the kill switch restores the pre-S9 behaviour.
    _running("m-ks")
    gm.set_requires("m-ks", "O-1", [("not_before", FUTURE)], now=NOW)
    os.environ["CPP_WAIT_PARK_LIVE"] = "off"
    out3 = gm.resource_gate(gm.load("m-ks"), NOW, sessions=_row("m-ks", "idle"), pid_alive=gone, probes=CLOCK,
                            stop_runner=lambda argv: None)
    os.environ.pop("CPP_WAIT_PARK_LIVE", None)
    check("V-S9-WAIT-KILL-SWITCH", not out3.get("owner_hold"), str(out3.get("owner_hold")))

    # 1d. A non-clock unmet requirement stays WAIT_RESOURCE (the label is not blanket).
    ev = mres.evaluate([{"id": "x", "kind": "path_exists", "arg": str(Path(TMP) / "absent"), "obligation": "O"}])
    check("V-S9-WAIT-RESOURCE-LABEL", gm.wait_type_of(ev) == "WAIT_RESOURCE", gm.wait_type_of(ev))

    # 2. Waiting is not execution time: 30 h parked on a 24 h mission is not "older than 24 h"; control unparked is.
    w = _running("m-hours", max_hours=24.0)
    gm.set_owner_hold("m-hours", "clock", now=NOW, kind="resource")
    later = NOW + 30 * 3600
    check("V-S9-WAIT-NOT-MAX-HOURS", gm.budget_exhausted(gm.load("m-hours"), later) is None,
          str(gm.budget_exhausted(gm.load("m-hours"), later)))
    check("V-S9-WAIT-CONTROL-UNPARKED-AGES", gm.budget_exhausted(w, later) is not None, str(gm.budget_exhausted(w, later)))

    # 3. Checkpoint: nonterminal, typed non-Owner, idle declarer stopped, cleared by a new plan (stalls reset).
    _running("m-ck")
    gm.transition("m-ck", expect_epoch=1, expect_state=gm.RUNNING, event="t", now=NOW, touch=False,
                  progress={"fp": "a", "stalls": 2, "measured": True})
    ck = gm.set_checkpoint("m-ck", "NEXT_PLAN_REQUIRED", "S8 closed; goal 1086/1797", evidence="gen3 ddd4d95a", now=NOW)
    p = gm.plan_next(ck, NOW + 60, _row("m-ck", "idle"), pid_alive=gone)
    check("V-S9-CKPT-PARKS-NOT-HALTS", ck["state"] not in gm.TERMINAL and p["action"] == "none"
          and "NEXT_PLAN_REQUIRED" in p["reason"], str(p))
    blk = (ck.get("owner_hold") or {}).get("blocker") or {}
    check("V-S9-CKPT-NOT-OWNER-REQUIRED", blk.get("class") in (None, "CHECKPOINT") and not blk.get("owner_required"),
          str({k: blk.get(k) for k in ("class", "owner_required")}))
    stops3: list = []
    ck2 = gm.checkpoint_gate(gm.load("m-ck"), NOW + 60, _row("m-ck", "idle"), gone,
                             stop_runner=lambda a: stops3.append(a))
    check("V-S9-CKPT-IDLE-STOPPED", bool(stops3) and bool((ck2.get("owner_hold") or {}).get("worker_stopped_at")),
          f"stops={stops3}")
    dead = gm.plan_next(ck2, NOW + 120, [], pid_alive=gone)
    check("V-S9-CKPT-DEAD-OWNER-NOT-SETTLED", dead["action"] == "none", str(dead))
    cl = gm.clear_checkpoint("m-ck", "S9 plan 591176e2", now=NOW + 3600)
    check("V-S9-CKPT-CLEARED", not cl.get("owner_hold") and (cl.get("progress") or {}).get("stalls") == 0
          and int(cl.get("waited_s") or 0) >= 3540, str({k: cl.get(k) for k in ("waited_s", "progress")}))
    try:
        gm.set_checkpoint("m-ck", "DONE", "x")
        bad = False
    except gm.MissionError:
        bad = True
    check("V-S9-CKPT-REFUSES-UNKNOWN-STATE", bad)
    # Control: an Owner hold outranks a checkpoint declaration.
    _running("m-own")
    gm.set_owner_hold("m-own", "Owner park", now=NOW)
    try:
        gm.set_checkpoint("m-own", "NEXT_PLAN_REQUIRED", "x")
        won = False
    except gm.MissionError:
        won = True
    check("V-S9-CKPT-OWNER-HOLD-WINS", won)

    # 4. Workset: a sibling repo joins a live mission and moves the mission fingerprint; control without it does not.
    _running("m-ws")
    sib = Path(tempfile.mkdtemp(prefix="sibling-"))
    fps = {}
    fp_fn = lambda d: fps.get(d, "same")   # noqa: E731
    base = gm.mission_fingerprint(gm.load("m-ws"), gm.load("m-ws")["cwd"], fp_fn)
    ws = gm.add_workset("m-ws", str(sib), role="product", now=NOW)
    fps[str(sib.resolve())] = "moved"
    after = gm.mission_fingerprint(ws, ws["cwd"], fp_fn)
    check("V-S9-WORKSET-PROGRESS-VISIBLE", after != base, f"{base} -> {after}")
    check("V-S9-WORKSET-ROLES", [w["role"] for w in gm.workset(ws)] == ["control", "product"], str(gm.workset(ws)))
    try:
        gm.add_workset("m-ws", str(Path(TMP) / "nope"))
        refused = False
    except gm.MissionError:
        refused = True
    check("V-S9-WORKSET-REFUSES-MISSING-DIR", refused)

    # 4b. Hold is not settle: an OWNER park outlives its worker; a cost-breaker hold still settles (control).
    _running("m-oh")
    oh = gm.set_owner_hold("m-oh", "wait for the 00:00 UTC quota reset", now=NOW)
    done = [{"sessionId": "m-oh-w", "id": "m-oh-w"[:8], "kind": "background", "state": "done"}]
    p = gm.plan_next(oh, NOW + 60, done, pid_alive=gone)
    check("V-S9-HOLD-OUTLIVES-WORKER", p["action"] == "none" and "parked nonterminal" in p["reason"], str(p))
    _running("m-oc")
    oc = gm.set_owner_hold("m-oc", "cost breaker: processed 696,658 > 1.25 x estimate 420,000", now=NOW)
    done2 = [{"sessionId": "m-oc-w", "id": "m-oc-w"[:8], "kind": "background", "state": "done"}]
    p2 = gm.plan_next(oc, NOW + 60, done2, pid_alive=gone)
    check("V-S9-HOLD-COST-STILL-SETTLES", p2["action"] == "settle", str(p2))

    # 4c. Mission-id authority: a cwd assertion refuses the wrong mission; the right one passes (control).
    try:
        gm.assert_mission_cwd("m-oh", str(sib))
        wrong = False
    except gm.MissionError as exc:
        wrong = "wrong mission id" in str(exc)
    check("V-S9-ID-WRONG-CWD-REFUSED", wrong)
    check("V-S9-ID-RIGHT-CWD-PASSES", gm.assert_mission_cwd("m-oh", TMP)["mission_id"] == "m-oh")
    check("V-S9-ID-WORKSET-PATH-PASSES", gm.assert_mission_cwd("m-ws", str(sib))["mission_id"] == "m-ws")

    # 4d. Wake-when-ready: a decision whose wake hit an unreachable host stays a pending obligation; control --no-wake.
    _running("m-dw")
    out = gm.deliver_decision("m-dw", "use plan S9", wake=True, now=NOW, sessions=None)
    check("V-S9-WAKE-PENDING-ON-UNREACHABLE", out["woke"].get("pending") and gm.load("m-dw").get("pending_wake"),
          str(out["woke"]))
    _running("m-dn")
    out2 = gm.deliver_decision("m-dn", "record only", wake=False, now=NOW, sessions=None)
    check("V-S9-WAKE-CONTROL-RECORD-ONLY", not gm.load("m-dn").get("pending_wake"), str(out2["woke"]))
    busy = gm.retry_pending_wake(gm.load("m-dw"), NOW + 60, _row("m-dw", "busy"), gone,
                                 runner=lambda *a, **k: "", stop_runner=lambda a: None)
    check("V-S9-WAKE-BUSY-KEPT", bool(busy.get("pending_wake")))
    stops4: list = []
    gm.retry_pending_wake(gm.load("m-dw"), NOW + 120, _row("m-dw", "idle"), gone,
                          runner=lambda *a, **k: "", stop_runner=lambda a: stops4.append(a))
    check("V-S9-WAKE-IDLE-DELIVERS", bool(stops4), f"stops={stops4}")
    _running("m-dg")
    gm.deliver_decision("m-dg", "x", wake=True, now=NOW, sessions=None)
    gone_rows = [{"sessionId": "m-dg-w", "id": "m-dg-w"[:8], "kind": "background", "state": "done"}]
    cleared = gm.retry_pending_wake(gm.load("m-dg"), NOW + 60, gone_rows, gone)
    check("V-S9-WAKE-OWNER-GONE-CLEARED", not cleared.get("pending_wake"))

    # 5. The resolver inventory stays clean and the lease-contention probe no longer dies on an unbound name.
    src = (Path(__file__).resolve().parent / "gsd_mission.py").read_text(encoding="utf-8")
    check("V-S9-ONE-RESOLVER", src.count('rec.get("work_dir") or rec["cwd"]') == 0)
    check("V-S9-LEASE-CONTENTION-IMPORT", "import mission_spend as ms   # S9" in src)

    # 6. Review finding (inline, 2026-11-01): a pending wake must never resume a mission the same pass parked on a wait.
    _running("m-race")
    gm.deliver_decision("m-race", "go", wake=True, now=NOW, sessions=None)
    gm.set_requires("m-race", "O-1", [("not_before", FUTURE)], now=NOW)
    stops5: list = []
    parked = gm.resource_gate(gm.load("m-race"), NOW, sessions=_row("m-race", "idle"), pid_alive=gone, probes=CLOCK,
                              stop_runner=lambda a: stops5.append(("gate", a)))
    after = gm.retry_pending_wake(parked, NOW, _row("m-race", "idle"), gone, runner=lambda *a, **k: stops5.append("RUN"),
                                  stop_runner=lambda a: stops5.append(("wake", a)))
    check("V-S9-WAKE-NEVER-THROUGH-HOLD", not after.get("pending_wake") and "RUN" not in stops5
          and not any(s[0] == "wake" for s in stops5 if isinstance(s, tuple)), str(stops5))

    print(f"S9_WAIT_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
