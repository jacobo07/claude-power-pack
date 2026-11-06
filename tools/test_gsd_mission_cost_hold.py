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
os.environ["CPP_MISSION_RECOVERY"] = "off"  # pins the legacy park/settle path AMR falls back to; AMR gates: test_mission_recovery.py
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
    # T1 F1: with no notice for this hold (GEX44's mission_wall never wrote one), the hold's set_at is the clock.
    _running("m-nf-old")
    gm.set_owner_hold("m-nf-old", TRIP, now=NOW - 700, kind="cost")
    over = ge.cost_hold_overdue(gm.load("m-nf-old"), NOW)
    check("V-CH-OVERDUE-NO-FLAG-USES-HOLD-CLOCK", bool(over) and over["overdue_s"] == 100
          and over["clock"] == "hold_set_at", str(over))
    _running("m-nf-new")
    gm.set_owner_hold("m-nf-new", TRIP, now=NOW - 60, kind="cost")
    check("V-CH-CONTROL-NO-FLAG-WITHIN-GRACE", ge.cost_hold_overdue(gm.load("m-nf-new"), NOW) is None)

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

    # 3b. T1 F1: an authority hold stops a LIVE worker on the first pass, no flag and no grace; an ordinary
    # cost hold set the same moment waits out its grace.
    auth_trip = (f"{gm.AUTHORITY_TRIP_PREFIX}: processed 152,641,947 >= authority 80,000,000 minus closeout "
                 "reserve 1,000,000; only closeout may run, new authority is the Owner's")
    for mid, hold in (("m-sv-auth", auth_trip), ("m-sv-fresh", TRIP)):
        _running(mid)
        gm.set_owner_hold(mid, hold, now=NOW, kind="cost")
    stops = []
    rows = gm.supervise(now=NOW, sessions=_row("m-sv-auth", "running") + _row("m-sv-fresh", "running"),
                        runner=lambda *a, **k: "", stop_runner=lambda a: stops.append(a), pid_alive=gone,
                        gsd_status=OK_GSD, fingerprint=lambda wd: None)
    by = {x["mission_id"]: x for x in rows}
    check("V-CH-AUTHORITY-HOLD-STOPS-NO-GRACE", any("m-sv-aut" in " ".join(s) for s in stops)
          and (by["m-sv-auth"].get("cost_hold_enforced") or {}).get("authority") is True, f"stops={stops}")
    check("V-CH-CONTROL-FRESH-COST-HOLD-WAITS-GRACE", not any("m-sv-fre" in " ".join(s) for s in stops),
          str(by.get("m-sv-fresh"))[:160])

    # 3c. T1 F1 (I4): authority is judged under another hold. A stall-held mission past its authority gets the
    # authority hold; the stop already recorded and the superseded hold travel with it.
    import mission_spend as ms
    _running("m-pr-over")
    gm.transition("m-pr-over", expect_epoch=1, expect_state=gm.RUNNING, event="t_auth", authority_tokens=56_000_000)
    stall = "cost breaker: 16,778,592 processed since the work tree last changed (stall budget 13,750,000)"
    gm.set_owner_hold("m-pr-over", stall, now=NOW, kind="cost", extra={"worker_stopped_at": NOW, "stop": "test"})
    h = (gm._authority_over_hold(gm.load("m-pr-over"), NOW + 60, measure=lambda r: 60_000_000).get("owner_hold") or {})
    check("V-CH-AUTHORITY-JUDGED-UNDER-HOLD", gm.is_authority_hold(h) and h.get("kind") == "cost"
          and (h.get("supersedes_hold") or {}).get("reason") == stall and h.get("worker_stopped_at") == NOW, str(h)[:200])
    check("V-CH-AUTHORITY-OVER-HOLD-LEDGERED", any(x.get("event") == "authority_over_hold"
          for x in gm.lr.ledger_events("m-pr-over")), "ledger row")
    for label, mid, auth, spent in (("UNDER-AUTHORITY", "m-pr-under", 56_000_000, 40_000_000),
                                    ("NO-AUTHORITY", "m-pr-none", None, 900_000_000)):
        _running(mid)
        if auth:
            gm.transition(mid, expect_epoch=1, expect_state=gm.RUNNING, event="t_auth", authority_tokens=auth)
        gm.set_owner_hold(mid, stall, now=NOW, kind="cost")
        h = gm._authority_over_hold(gm.load(mid), NOW + 60, measure=lambda r, s=spent: s).get("owner_hold") or {}
        check(f"V-CH-CONTROL-PRECEDENCE-{label}-KEEPS-HOLD", h.get("reason") == stall, str(h)[:120])

    def boom(_r):
        raise OSError("meter down")
    h = gm._authority_over_hold(gm.load("m-pr-under"), NOW + 60, measure=boom).get("owner_hold") or {}
    check("V-CH-PRECEDENCE-UNMEASURED-FAILS-OPEN", h.get("reason") == stall and any(
          x.get("event") == "authority_over_hold_unmeasured" for x in gm.lr.ledger_events("m-pr-under")), str(h)[:120])
    # Under an Owner's own hold the breach is ledgered once and the hold is kept (a cost hold would go to AMR).
    _running("m-pr-owner")
    gm.transition("m-pr-owner", expect_epoch=1, expect_state=gm.RUNNING, event="t_auth", authority_tokens=56_000_000)
    gm.set_owner_hold("m-pr-owner", "Owner park for review", now=NOW)
    for _ in range(2):
        h = gm._authority_over_hold(gm.load("m-pr-owner"), NOW + 60, measure=lambda r: 60_000_000).get("owner_hold") or {}
    rows = [x for x in gm.lr.ledger_events("m-pr-owner") if x.get("event") == "authority_breach_under_owner_hold"]
    check("V-CH-OWNER-HOLD-KEPT-BREACH-LEDGERED-ONCE", h.get("reason") == "Owner park for review" and len(rows) == 1,
          f"rows={len(rows)} hold={str(h)[:80]}")

    # Wiring: the judgement runs inside _breaker_first's timed thread; the untimed main-loop call does not meter.
    real_pt = ms.processed_tokens
    calls = []
    ms.processed_tokens = lambda r: calls.append(r["mission_id"]) or 70_000_000
    try:
        main_loop = gm._judge_pre_plan(gm.load("m-pr-under"), NOW + 120)
        main_calls = list(calls)
        judged, timed_out = gm._breaker_first([gm.load("m-pr-under")], NOW + 120)
    finally:
        ms.processed_tokens = real_pt
    check("V-CH-CONTROL-MAIN-LOOP-DOES-NOT-METER-HELD", main_calls == [] and main_loop["owner_hold"]["reason"] == stall,
          f"calls={main_calls}")
    check("V-CH-PRECEDENCE-WIRED-IN-BREAKER-FIRST", gm.is_authority_hold((judged.get("m-pr-under") or {}).get("owner_hold"))
          and not timed_out, str(((judged.get("m-pr-under") or {}).get("owner_hold") or {}).get("reason"))[:120])

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

    # 4b. spec mission-closeout-reserve-launch (S13 m-84f2641865dd: the reserve never launched a closeout).
    auth30 = (f"{gm.AUTHORITY_TRIP_PREFIX}: processed 29,400,000 >= authority 30,000,000 minus closeout reserve "
              "1,000,000; only closeout may run, new authority is the Owner's")
    launches = []

    def fake_launch(mid, **kw):
        launches.append((mid, kw))
        r = gm.load(mid)
        gm.transition(mid, expect_epoch=kw["expect_epoch"], expect_state=kw["expect_state"], event="t_claim", now=NOW,
                      state=gm.LAUNCHING, epoch=kw["expect_epoch"] + 1, owner=None, previous_owner=r.get("owner"),
                      pending={"kind": "worker_start", "epoch": kw["expect_epoch"] + 1, "requested_at": NOW,
                               "deadline": NOW + 300})
        return {"ok": True, "epoch": kw["expect_epoch"] + 1, "bg_id": "c1053d01"}

    def held(mid, hold=auth30, stopped=True, **fields):
        _running(mid)
        gm.transition(mid, expect_epoch=1, expect_state=gm.RUNNING, event="t_auth", authority_tokens=30_000_000,
                      **fields)
        return gm.set_owner_hold(mid, hold, now=NOW, kind="cost",
                                 extra={"worker_stopped_at": NOW, "stop": "test"} if stopped else None)

    m29 = lambda r: 29_400_000  # noqa: E731
    rec = gm.closeout_gate(held("m-c10a01"), NOW + 60, [], gone, measure=m29, launcher=fake_launch)
    lease = rec.get("closeout_lease") or {}
    check("V-COST-CLOSEOUT-LAUNCHES-ONE", len(launches) == 1 and lease.get("state") == gm.CL_LAUNCHED
          and "CLOSEOUT ONLY" in (launches[0][1].get("prompt_override") or ""), f"n={len(launches)} lease={lease}")
    check("V-COST-CLOSEOUT-LEASE-WITHIN-AUTHORITY", lease.get("tokens") == 600_000,
          f"tokens={lease.get('tokens')} (min(reserve 1M, 30M - 29.4M))")
    r = gm.closeout_gate(gm.load("m-c10a01"), NOW + 200, [], gone, measure=m29, launcher=fake_launch)
    check("V-COST-CLOSEOUT-SECOND-PASS-NO-LAUNCH", len(launches) == 1
          and (r.get("closeout_lease") or {}).get("state") == gm.CL_LAUNCHED, f"n={len(launches)}")
    p = gm.plan_next(gm.load("m-c10a01"), NOW + 120, [], pid_alive=gone)
    check("V-COST-CLOSEOUT-PLAN-HELD-OFF", p["action"] == "none" and "closeout running" in p["reason"], str(p))
    gm.closeout_gate(held("m-c10a09"), NOW + 60, [], gone, measure=m29, launcher=fake_launch)
    r = gm.closeout_gate(gm.load("m-c10a09"), NOW + 400, [], gone, launcher=fake_launch)
    check("V-COST-CLOSEOUT-NEVER-ACKED-FAILS", (r.get("closeout_lease") or {}).get("state") == gm.CL_FAILED
          and "never acked" in str((r.get("closeout_lease") or {}).get("why")), str(r.get("closeout_lease"))[:140])
    for label, mid, kw in (("NO-RESERVE", "m-c10a02", {"fields": {"closeout_tokens": 0}}),
                           ("NON-AUTHORITY-HOLD", "m-c10a03", {"hold": TRIP}),
                           ("LIVE-WORKER", "m-c10a04", {"stopped": False})):
        n0 = len(launches)
        r = gm.closeout_gate(held(mid, hold=kw.get("hold", auth30), stopped=kw.get("stopped", True),
                                  **kw.get("fields", {})),
                             NOW + 60, _row(mid, "running"), gone, measure=m29, launcher=fake_launch)
        check(f"V-COST-CLOSEOUT-CONTROL-{label}", len(launches) == n0 and not r.get("closeout_lease"),
              str(r.get("closeout_lease")))
    os.environ["CPP_MISSION_CLOSEOUT_LAUNCH"] = "off"
    n0 = len(launches)
    r = gm.closeout_gate(held("m-c10a05"), NOW + 60, [], gone, measure=m29, launcher=fake_launch)
    os.environ.pop("CPP_MISSION_CLOSEOUT_LAUNCH", None)
    check("V-COST-CLOSEOUT-KILL-SWITCH", len(launches) == n0 and not r.get("closeout_lease"), "off -> today's park")
    n0 = len(launches)
    r = gm.closeout_gate(held("m-c10a06"), NOW + 60, [], gone, measure=lambda r: 29_950_000, launcher=fake_launch)
    check("V-COST-CLOSEOUT-UNFUNDED-FAILS-NO-LAUNCH", len(launches) == n0
          and (r.get("closeout_lease") or {}).get("state") == gm.CL_FAILED, str(r.get("closeout_lease"))[:160])

    # the launched worker acks (epoch 2) -> its checkpoint completes the lease; the authority hold stays.
    def acked(mid, sid):
        r = gm.load(mid)
        return gm.transition(mid, expect_epoch=r["epoch"], expect_state=gm.LAUNCHING, event="t_ack", now=NOW,
                             state=gm.RUNNING, pending=None,
                             owner={"session_id": sid, "pid": None, "proc_start": None, "heartbeat_at": NOW,
                                    "epoch": r["epoch"], "kind": "background"})
    acked("m-c10a01", "m-c10a01-c")
    r = gm.set_checkpoint("m-c10a01", "CHECKPOINT_COMPLETE", "closeout written", residual="closeout.md", now=NOW + 500)
    check("V-COST-CLOSEOUT-CHECKPOINT-COMPLETES", (r.get("closeout_lease") or {}).get("state") == gm.CL_DONE
          and gm.is_authority_hold(r.get("owner_hold")), str(r.get("closeout_lease"))[:160])
    try:
        gm.set_checkpoint("m-c10a03", "CHECKPOINT_COMPLETE", "no lease", now=NOW + 500)
        refused = False
    except gm.MissionError:
        refused = True
    check("V-COST-CLOSEOUT-CONTROL-CHECKPOINT-REFUSED-WITHOUT-LEASE", refused, "a cost hold without a lease still wins")
    stops = []
    idle = [{"sessionId": "m-c10a01-c", "id": "m-c10a01"[:8], "kind": "background", "state": "running", "status": "idle"}]
    r = gm.closeout_gate(gm.load("m-c10a01"), NOW + 600, idle, gone, launcher=fake_launch,
                         stop_runner=lambda a: stops.append(a) or subprocess.CompletedProcess(a, 0, "", ""))
    check("V-COST-CLOSEOUT-DONE-WORKER-STOPPED", (r.get("closeout_lease") or {}).get("worker_stopped") is True
          and (r.get("closeout_lease") or {}).get("state") == gm.CL_DONE, str(r.get("closeout_lease"))[:160])

    # a closeout worker that ends its turn WITHOUT a checkpoint -> CLOSEOUT_FAILED, surfaced, never relaunched.
    gm.closeout_gate(held("m-c10a07"), NOW + 60, [], gone, measure=m29, launcher=fake_launch)
    acked("m-c10a07", "m-c10a07-c")
    n0 = len(launches)
    idle = [{"sessionId": "m-c10a07-c", "id": "m-c10a07"[:8], "kind": "background", "state": "running", "status": "idle"}]
    r = gm.closeout_gate(gm.load("m-c10a07"), NOW + 600, idle, gone, launcher=fake_launch,
                         stop_runner=lambda a: subprocess.CompletedProcess(a, 0, "", ""))
    r = gm.closeout_gate(gm.load("m-c10a07"), NOW + 900, [], gone, measure=m29, launcher=fake_launch)
    check("V-COST-CLOSEOUT-ENDED-WITHOUT-CHECKPOINT-FAILS", (r.get("closeout_lease") or {}).get("state") == gm.CL_FAILED
          and len(launches) == n0 and any(x.get("event") == "closeout_failed" for x in gm.lr.ledger_events("m-c10a07")),
          str(r.get("closeout_lease"))[:160])

    # review H1: a lease left AUTHORIZED (lost final write) is resolved from the claimed epoch, or failed when stale.
    held("m-c10a0a")
    a = {"state": gm.CL_AUTHORIZED, "granted_at": NOW, "tokens": 600_000, "claim_epoch": 1, "authority": 30_000_000}
    gm.transition("m-c10a0a", expect_epoch=1, expect_state=gm.RUNNING, event="t_lease", closeout_lease=a)
    fake_launch("m-c10a0a", expect_epoch=1, expect_state=gm.RUNNING)
    acked("m-c10a0a", "m-c10a0a-c")
    r = gm.closeout_gate(gm.load("m-c10a0a"), NOW + 60, [], gone, launcher=fake_launch)
    check("V-COST-CLOSEOUT-AUTHORIZED-RECOVERED", (r.get("closeout_lease") or {}).get("state") == gm.CL_LAUNCHED
          and (r.get("closeout_lease") or {}).get("epoch") == 2, str(r.get("closeout_lease"))[:140])
    held("m-c10a0b")
    gm.transition("m-c10a0b", expect_epoch=1, expect_state=gm.RUNNING, event="t_lease", closeout_lease=a)
    r = gm.closeout_gate(gm.load("m-c10a0b"), NOW + gm.START_DEADLINE_S + 60, [], gone, launcher=fake_launch)
    check("V-COST-CLOSEOUT-AUTHORIZED-STALE-FAILS", (r.get("closeout_lease") or {}).get("state") == gm.CL_FAILED,
          str(r.get("closeout_lease"))[:140])
    # the final write survives a CAS loss to the worker's ack (one injected conflict, then the retry lands).
    real_tr, hits = gm.transition, []

    def flaky(mid, **kw):
        if kw.get("event") == "closeout_launched" and not hits:
            hits.append(1)
            raise gm.CasConflict("injected ack race")
        return real_tr(mid, **kw)
    gm.transition = flaky
    try:
        r = gm.closeout_gate(held("m-c10a0c"), NOW + 60, [], gone, measure=m29, launcher=fake_launch)
    finally:
        gm.transition = real_tr
    check("V-COST-CLOSEOUT-FINAL-WRITE-RETRIED", hits == [1] and (r.get("closeout_lease") or {}).get("state")
          == gm.CL_LAUNCHED, str(r.get("closeout_lease"))[:140])

    # review M1: a second sweep holding the pre-lease record cannot authorize or launch a second worker.
    stale = held("m-c10a0d")
    inner = []

    def racing_launch(mid, **kw):
        inner.append(gm.closeout_gate(stale, NOW + 61, [], gone, measure=m29, launcher=fake_launch))
        return fake_launch(mid, **kw)
    n0 = len(launches)
    r = gm.closeout_gate(stale, NOW + 60, [], gone, measure=m29, launcher=racing_launch)
    check("V-COST-CLOSEOUT-CONCURRENT-SWEEP-ONE-LAUNCH", len(launches) == n0 + 1
          and (r.get("closeout_lease") or {}).get("state") == gm.CL_LAUNCHED, f"launches={len(launches) - n0}")

    # review M2: a finished lease is history only under a NEW Owner authority (a new trip gets its own closeout).
    r = gm.load("m-c10a01")
    gm.transition("m-c10a01", expect_epoch=r["epoch"], expect_state=r["state"], event="t_hold2",
                  owner_hold={**r["owner_hold"], "set_at": NOW + 700})
    n0 = len(launches)
    gm.closeout_gate(gm.load("m-c10a01"), NOW + 700, [], gone, measure=m29, launcher=fake_launch)
    check("V-COST-CLOSEOUT-CONTROL-SAME-AUTHORITY-NO-SECOND", len(launches) == n0, "same authority: one trip, one lease")
    r = gm.load("m-c10a01")
    gm.transition("m-c10a01", expect_epoch=r["epoch"], expect_state=r["state"], event="t_auth2",
                  authority_tokens=40_000_000)
    r = gm.closeout_gate(gm.load("m-c10a01"), NOW + 800, [], gone, measure=lambda r: 39_400_000, launcher=fake_launch)
    lease2 = r.get("closeout_lease") or {}
    check("V-COST-CLOSEOUT-NEW-AUTHORITY-NEW-TRIP", len(launches) == n0 + 1 and lease2.get("state") == gm.CL_LAUNCHED
          and lease2.get("authority") == 40_000_000 and (lease2.get("previous") or {}).get("state") == gm.CL_DONE,
          str(lease2)[:160])
    held("m-c10a0e")
    gm.closeout_gate(gm.load("m-c10a0e"), NOW + 60, [], gone, measure=m29, launcher=fake_launch)
    acked("m-c10a0e", "m-c10a0e-c")
    r = gm.load("m-c10a0e")
    gm.transition("m-c10a0e", expect_epoch=r["epoch"], expect_state=r["state"], event="t_relaunch", epoch=r["epoch"] + 1)
    r = gm.closeout_gate(gm.load("m-c10a0e"), NOW + 120, [], gone, launcher=fake_launch)
    check("V-COST-CLOSEOUT-SUPERSEDED-RETIRED", (r.get("closeout_lease") or {}).get("state") == gm.CL_FAILED
          and "superseded" in str((r.get("closeout_lease") or {}).get("why")), str(r.get("closeout_lease"))[:140])

    # the pre-call gate: the lease session is admitted under its lease and denied past it; the old worker stays denied.
    gm.closeout_gate(held("m-c10a08"), NOW + 60, [], gone, measure=m29, launcher=fake_launch)
    acked("m-c10a08", "m-c10a08-c")
    proj = Path(TMP) / "proj-closeout"
    proj.mkdir(exist_ok=True)

    def transcript(name, n):
        row = {"uuid": name, "timestamp": "2026-11-06T10:00:00Z", "message": {"id": name, "model": "claude", "usage": {
            "input_tokens": n, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 0}}}
        f = proj / f"{name}.jsonl"
        f.write_text(json.dumps(row) + "\n", encoding="utf-8")
        return str(f)
    for sid in ("m-c10a08-c", "m-c10a08-w"):
        Path(TMP, f"mission-worker-{sid}.json").write_text(json.dumps({"session_id": sid, "mission_id": "m-c10a08"}),
                                                           encoding="utf-8")

    def gate(sid, tp):
        lib = json.dumps(str(HERE.parent / "hooks" / "lib" / "mission_gate.js"))
        ev = json.dumps({"session_id": sid, "tool_name": "Read", "tool_input": {"file_path": "a"}, "transcript_path": tp})
        js = (f"const g=require({lib});const e={ev};"
              "process.stdout.write(JSON.stringify(g.holdDecision(e)||g.exposureDecision(e)))")
        out = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60,
                             env={**os.environ, "GSD_AUTORUN_MARKER_DIR": TMP, "GSD_LONG_RUN_STATE_DIR": TMP})
        return json.loads(out.stdout or "null")
    g_under = gate("m-c10a08-c", transcript("lease-under", 200_000))
    g_over = gate("m-c10a08-c", transcript("lease-over", 400_000))
    g_old = gate("m-c10a08-w", transcript("old-worker", 1_000))
    check("V-COST-CLOSEOUT-GATE-ADMITS-UNDER-LEASE", g_under is None, str(g_under)[:120] + "  (200k + 200k <= 600k)")
    check("V-COST-CLOSEOUT-GATE-DENIES-PAST-LEASE", "CLOSEOUT LEASE" in str((g_over or {}).get("deny")),
          str(g_over)[:120] + "  (400k + 400k > 600k)")
    check("V-COST-CLOSEOUT-GATE-OTHER-SESSION-DENIED", "MISSION COST HOLD" in str((g_old or {}).get("deny")),
          str(g_old)[:120])

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
