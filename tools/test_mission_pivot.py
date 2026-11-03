#!/usr/bin/env python
"""V-PIVOT-* gates: opt-in Method-Pivot autonomy at a checkpoint (Tennis Generation S11, Lane A2).

Origin (2026-11-02, GEX44): S10 (m-e6e0340e743d) and S10b (m-f41146776f2b) each ended at a checkpoint
(NEXT_PLAN_REQUIRED, METHOD_PIVOT_REQUIRED) whose next step was an engineering method change, and each parked until
the Owner wrote a new plan. The Owner addendum of the same day: a HOW pivot inside the approved envelope must not
interrupt the Owner; a WHAT change (truth contract, capital, held-out) still must.

MA-PR replays, hermetic (state in a temp dir before import, host rows injected, nothing launched):
  MA-PR1/2/3  S10b-shaped METHOD_PIVOT_REQUIRED with a residual on an opted-in mission -> directive + checkpoint cleared
  MA-PR4      the sd8 truth-contract question as the checkpoint reason -> stays parked, owner boundary recorded
  MA-PR5      a HOW-only reason pivots; the same mission without opt-in keeps today's park (control)
Paired controls: no residual parks; streak cap parks; --gain resets the streak; a busy worker is never pivoted;
CHECKPOINT_COMPLETE never pivots; kill switch CPP_PIVOT_AUTONOMY=off restores the park.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-mission-pivot-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_MISSION_RECOVERY"] = "off"
os.environ.pop("CPP_PIVOT_AUTONOMY", None)
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402

gm.host_sessions = lambda *a, **k: None

passes = fails = 0
NOW = 1_800_000_000.0
gone = lambda pid: False   # noqa: E731
S10B = ("S10b closed: frozen method c631de1e fails its positive control (operator OFF_SHAPE on the 3 known CXX); "
        "0 new CERTIFIED_CXX in dev batches")
SD8 = ("Decide whether cert-cxx may admit an sd8 variant (fn_80222ED8 is the case in question); then a new S10-1 "
       "plan can be written")


def check(gate, cond, ev=""):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def _mission(mid: str, opt_in: bool) -> dict:
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.RUNNING, epoch=1,
                  owner={"session_id": f"{mid}-w", "pid": None, "proc_start": None, "heartbeat_at": NOW, "epoch": 1,
                         "kind": "background"})
    if opt_in:
        gm.set_pivot_autonomy(mid, True, now=NOW)
    return gm.load(mid)


def _gate(mid: str, status: str = "idle") -> dict:
    rows = [{"sessionId": f"{mid}-w", "id": f"{mid}-w"[:8], "status": status, "state": "running", "kind": "background"}]
    return gm.checkpoint_gate(gm.load(mid), NOW + 60, sessions=rows, pid_alive=gone, stop_runner=lambda argv: None)


def main() -> int:
    # MA-PR1/2/3: an opted-in mission with a residual pivots: directive recorded, checkpoint cleared, streak 1.
    _mission("m-pivot", True)
    gm.set_checkpoint("m-pivot", "METHOD_PIVOT_REQUIRED", S10B, residual="evidence/ascension/s10b/closeout.md", now=NOW)
    out = _gate("m-pivot")
    dirs = out.get("directives") or []
    check("V-PIVOT-AUTO", out.get("owner_hold") is None and out.get("pivot_streak") == 1,
          f"hold={out.get('owner_hold')} streak={out.get('pivot_streak')}")
    check("V-PIVOT-DIRECTIVE", any("AUTO METHOD PIVOT 1/" in d and "closeout.md" in d for d in dirs), str(dirs)[-300:])
    stopped = [{"sessionId": "m-pivot-w", "id": "m-pivot-w"[:8], "kind": "background", "state": "done"}]
    p = gm.plan_next(out, NOW + 120, stopped, pid_alive=gone)
    check("V-PIVOT-RELAUNCHES", p["action"] not in ("none",), f"plan_next after pivot: {p['action']} {p.get('reason', '')[:80]}")

    # MA-PR4: a truth-contract reason never pivots; the boundary is recorded once.
    _mission("m-owner", True)
    gm.set_checkpoint("m-owner", "NEXT_PLAN_REQUIRED", SD8, residual="evidence/ascension/s10/closeout.md", now=NOW)
    o = _gate("m-owner")
    h = o.get("owner_hold") or {}
    check("V-PIVOT-OWNER-BOUNDARY", h.get("kind") == gm.CHECKPOINT_KIND and (h.get("pivot") or {}).get("action") == "owner"
          and "TRUTH_CONTRACT" in (h.get("pivot") or {}).get("why", ""), str(h.get("pivot")))
    check("V-PIVOT-OWNER-NO-DIRECTIVE", not (o.get("directives") or []), str(o.get("directives")))

    # MA-PR5 control: same HOW reason, mission NOT opted in -> today's park, untouched.
    _mission("m-off", False)
    gm.set_checkpoint("m-off", "METHOD_PIVOT_REQUIRED", S10B, residual="r.md", now=NOW)
    f = _gate("m-off")
    fh = f.get("owner_hold") or {}
    check("V-PIVOT-OPT-IN-ONLY", fh.get("kind") == gm.CHECKPOINT_KIND and "pivot" not in fh and not f.get("directives"),
          str({k: fh.get(k) for k in ("kind", "checkpoint", "pivot")}))

    # Controls.
    _mission("m-nores", True)
    gm.set_checkpoint("m-nores", "METHOD_PIVOT_REQUIRED", S10B, now=NOW)
    n = _gate("m-nores")
    check("V-PIVOT-NEEDS-RESIDUAL", (n.get("owner_hold") or {}).get("pivot", {}).get("action") == "park",
          str((n.get("owner_hold") or {}).get("pivot")))
    _mission("m-done", True)
    gm.set_checkpoint("m-done", "CHECKPOINT_COMPLETE", "ready for H2 preflight", residual="r.md", now=NOW)
    c = _gate("m-done")
    check("V-PIVOT-COMPLETE-NEVER", (c.get("owner_hold") or {}).get("kind") == gm.CHECKPOINT_KIND
          and (c.get("owner_hold") or {}).get("pivot", {}).get("action") == "park", str((c.get("owner_hold") or {}).get("pivot")))
    _mission("m-busy", True)
    gm.set_checkpoint("m-busy", "METHOD_PIVOT_REQUIRED", S10B, residual="r.md", now=NOW)
    b = _gate("m-busy", status="busy")
    check("V-PIVOT-BUSY-WAITS", (b.get("owner_hold") or {}).get("kind") == gm.CHECKPOINT_KIND
          and "pivot" not in (b.get("owner_hold") or {}), str(b.get("owner_hold")))

    # Streak cap and --gain reset.
    _mission("m-cap", True)
    gm.transition("m-cap", expect_epoch=1, expect_state=gm.RUNNING, event="t_streak", now=NOW,
                  pivot_streak=gm.PIVOT_MAX_STREAK)
    gm.set_checkpoint("m-cap", "METHOD_PIVOT_REQUIRED", S10B, residual="r.md", now=NOW)
    k = _gate("m-cap")
    check("V-PIVOT-STREAK-CAP", (k.get("owner_hold") or {}).get("pivot", {}).get("action") == "owner",
          str((k.get("owner_hold") or {}).get("pivot")))
    _mission("m-gain", True)
    gm.transition("m-gain", expect_epoch=1, expect_state=gm.RUNNING, event="t_streak", now=NOW,
                  pivot_streak=gm.PIVOT_MAX_STREAK)
    gm.set_checkpoint("m-gain", "METHOD_PIVOT_REQUIRED", S10B, residual="r.md", gain=True, now=NOW)
    g = _gate("m-gain")
    check("V-PIVOT-GAIN-RESETS", g.get("owner_hold") is None and g.get("pivot_streak") == 1, str(g.get("pivot_streak")))

    # Kill switch.
    _mission("m-ks", True)
    gm.set_checkpoint("m-ks", "METHOD_PIVOT_REQUIRED", S10B, residual="r.md", now=NOW)
    os.environ["CPP_PIVOT_AUTONOMY"] = "off"
    try:
        s = _gate("m-ks")
    finally:
        os.environ.pop("CPP_PIVOT_AUTONOMY", None)
    check("V-PIVOT-KILL-SWITCH", (s.get("owner_hold") or {}).get("kind") == gm.CHECKPOINT_KIND
          and "pivot" not in (s.get("owner_hold") or {}), str(s.get("owner_hold")))

    # S11 D1 -- incident 2026-11-03 (GEX44 m-f0b595fd509f epoch 13): the worker declared METHOD_PIVOT_REQUIRED at
    # 23:31:40Z and exited; the host kept listing its job as a bare state:"blocked" (no waitingFor, no status), so
    # owner_idle() was False, liveness() not DEAD, and checkpoint_gate returned before pivot_gate for ~6 h. The real
    # host row shape and the real reason are replayed here.
    S11 = ("OM-PR1 2/3: fn_80222480 98.9 (mwcc reg priority), in-scope routes falsified; "
           "6 dev registry-attributable CXX")

    def _blocked(mid: str, at: float, started_ms: float, waiting: str | None = None, stops: list | None = None) -> dict:
        row = {"id": f"{mid}-w"[:8], "cwd": "/w", "kind": "background", "startedAt": started_ms,
               "sessionId": f"{mid}-w", "name": f"{mid}-e13", "state": "blocked"}
        if waiting:
            row["waitingFor"] = waiting
        return gm.checkpoint_gate(gm.load(mid), at, sessions=[row], pid_alive=gone,
                                  stop_runner=lambda argv: (stops if stops is not None else []).append(argv))

    started = (NOW - 3600) * 1000
    _mission("m-blk", True)
    gm.set_checkpoint("m-blk", "METHOD_PIVOT_REQUIRED", S11, residual="evidence/ascension/s11/residual.md", now=NOW)
    stops: list = []
    early = _blocked("m-blk", NOW + 60, started, stops=stops)
    check("V-PIVOT-BLOCKED-GRACE", (early.get("owner_hold") or {}).get("kind") == gm.CHECKPOINT_KIND and not stops
          and "pivot" not in (early.get("owner_hold") or {}), f"1 min after the checkpoint: stops={stops}")
    late = _blocked("m-blk", NOW + gm.CHECKPOINT_BLOCKED_GRACE_S + 1, started, stops=stops)
    check("V-PIVOT-BLOCKED-AFTER-CHECKPOINT", late.get("owner_hold") is None and late.get("pivot_streak") == 1
          and len(stops) == 1, f"hold={late.get('owner_hold')} streak={late.get('pivot_streak')} stops={stops}")
    check("V-PIVOT-S11-REASON-PIVOTS", any("AUTO METHOD PIVOT 1/" in d and "residual.md" in d
                                           for d in (late.get("directives") or [])), str(late.get("directives"))[-200:])

    _mission("m-perm", True)
    gm.set_checkpoint("m-perm", "METHOD_PIVOT_REQUIRED", S11, residual="r.md", now=NOW)
    pstops: list = []
    p2 = _blocked("m-perm", NOW + 7200, started, waiting="permission: Bash(git push)", stops=pstops)
    check("V-PIVOT-PERMISSION-PROMPT-STAYS", (p2.get("owner_hold") or {}).get("kind") == gm.CHECKPOINT_KIND
          and not pstops, f"a waitingFor prompt is a human's, never stopped: stops={pstops}")

    _mission("m-later", True)
    gm.set_checkpoint("m-later", "METHOD_PIVOT_REQUIRED", S11, residual="r.md", now=NOW)
    lstops: list = []
    l2 = _blocked("m-later", NOW + 7200, (NOW + 30) * 1000, stops=lstops)
    check("V-PIVOT-BLOCKED-LATER-JOB-STAYS", (l2.get("owner_hold") or {}).get("kind") == gm.CHECKPOINT_KIND
          and not lstops, f"a job started after the checkpoint did not declare it: stops={lstops}")

    print(f"PIVOT_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
