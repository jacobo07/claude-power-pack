#!/usr/bin/env python
"""V-PIVOT-* gates: opt-in Method-Pivot autonomy at a checkpoint (Game-A Generation S11, Lane A2).

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
SD8 = ("Decide whether cert-cxx may admit an sd8 variant (fn_00000A01 is the case in question); then a new S10-1 "
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
    S11 = ("OM-PR1 2/3: fn_00000A02 98.9 (mwcc reg priority), in-scope routes falsified; "
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

    # S11H P1-P4 (Owner "y" 2026-11-03): typed Method Failure Receipt, typed authority objects, Pivot Gen2 budget,
    # compiled Owner question. Authority = typed objects UNION the wording net (typed may only add); strategy (pivot or
    # stop, budget) is driven by the receipt alone when one is declared.
    def rcpt(method, delta=True, objs=(), fclass="METHOD_PLATEAU", **kw):
        return {"failure_class": fclass, "method_class": method, "evidence_delta": delta,
                "methods_falsified": [method], "residual_class": "COMPILER_SHAPE_RESIDUAL",
                "authority_objects": list(objs), **kw}

    def _gen2(mid, receipt, streak=0, history=(), authority=80_000_000, spent=10_000_000, reason=S11):
        _mission(mid, True)
        gm.transition(mid, expect_epoch=1, expect_state=gm.RUNNING, event="t_gen2", now=NOW, pivot_streak=streak,
                      pivot_history=list(history), authority_tokens=authority, cost_mark={"tokens": spent})
        gm.set_checkpoint(mid, "METHOD_PIVOT_REQUIRED", reason, residual="r.md", receipt=receipt, now=NOW)
        return _gate(mid)

    try:
        gm.set_checkpoint("m-pivot", "METHOD_PIVOT_REQUIRED", S11, residual="r.md",
                          receipt={"failure_class": "METHOD_PLATEAU", "evidence_delta": True}, now=NOW)
        bad = None
    except gm.MissionError as exc:
        bad = str(exc)
    try:
        gm.set_checkpoint("m-pivot", "METHOD_PIVOT_REQUIRED", S11, residual="r.md",
                          receipt=rcpt("x", objs=("MY_OWN_AUTHORITY",)), now=NOW)
        bad2 = None
    except gm.MissionError as exc:
        bad2 = str(exc)
    check("V-PIVOT-RECEIPT-INVALID-REFUSED", bool(bad) and "method_class" in bad and bool(bad2)
          and "MY_OWN_AUTHORITY" in bad2, f"{bad} | {bad2}")

    a = _gen2("m-r-obj", rcpt("ctor-hints", objs=("HELD_OUT_CONTRACT",)))
    ap_ = (a.get("owner_hold") or {}).get("pivot") or {}
    oq = ap_.get("owner_question") or {}
    check("V-PIVOT-RECEIPT-AUTHORITY-OBJECT", ap_.get("action") == "owner" and "HELD_OUT_CONTRACT" in ap_.get("why", "")
          and oq.get("authority_objects") == ["HELD_OUT_CONTRACT"] and oq.get("exhausted") == ["ctor-hints"],
          str(ap_)[:300])
    n_ = _gen2("m-r-net", rcpt("decl-order"), reason=SD8)
    check("V-PIVOT-RECEIPT-WORDING-NET-STAYS", ((n_.get("owner_hold") or {}).get("pivot") or {}).get("action") == "owner",
          "an empty authority list never removes the wording net: " + str((n_.get("owner_hold") or {}).get("pivot"))[:160])
    p_ = _gen2("m-r-ok", rcpt("pragmas"))
    check("V-PIVOT-RECEIPT-DRIVES", p_.get("owner_hold") is None and p_.get("pivot_streak") == 1
          and (p_.get("pivot_history") or [{}])[-1].get("method_class") == "pragmas", str(p_.get("pivot_history")))

    e_ = _gen2("m-g-early", rcpt("decl-order", delta=False), streak=1,
               history=[{"method_class": "decl-order", "evidence_delta": False}])
    check("V-PIVOT-GEN2-EARLY-STOP", ((e_.get("owner_hold") or {}).get("pivot") or {}).get("action") == "owner",
          "2 zero-delta receipts in one method class stop before the fixed 3: "
          + str((e_.get("owner_hold") or {}).get("pivot"))[:160])
    good = [{"method_class": m, "evidence_delta": True} for m in ("decl-order", "ctor-hints", "pragmas")]
    x_ = _gen2("m-g-ext", rcpt("coloring-model"), streak=3, history=good)
    check("V-PIVOT-GEN2-EXTENDS", x_.get("owner_hold") is None and x_.get("pivot_streak") == 4,
          f"distinct classes with evidence delta continue past 3: streak={x_.get('pivot_streak')}")
    c_ = _gen2("m-g-cap", rcpt("donor"), streak=gm.PIVOT_HARD_CAP,
               history=good + [{"method_class": "coloring-model", "evidence_delta": True},
                               {"method_class": "probe", "evidence_delta": True}])
    check("V-PIVOT-GEN2-HARD-CAP", ((c_.get("owner_hold") or {}).get("pivot") or {}).get("action") == "owner",
          str((c_.get("owner_hold") or {}).get("pivot"))[:160])
    d_ = _gen2("m-g-dup", rcpt("pragmas"), streak=3, history=good)
    check("V-PIVOT-GEN2-REPEAT-CLASS-NO-EXTENSION", ((d_.get("owner_hold") or {}).get("pivot") or {}).get("action") == "owner",
          "a class already in the streak is not independent: " + str((d_.get("owner_hold") or {}).get("pivot"))[:160])
    q_ = _gen2("m-g-poor", rcpt("coloring-model"), streak=3, history=good, authority=60_000_000, spent=59_000_000)
    check("V-PIVOT-GEN2-AUTHORITY-LEFT", ((q_.get("owner_hold") or {}).get("pivot") or {}).get("action") == "owner",
          "no extension without a lease of authority left: " + str((q_.get("owner_hold") or {}).get("pivot"))[:160])

    import json as _json
    rp = Path(TMP) / "receipt.json"
    rp.write_text(_json.dumps(rcpt("cli-route")), encoding="utf-8")
    _mission("m-cli", True)
    rc = gm._cli(["checkpoint", "--mission", "m-cli", "--state", "METHOD_PIVOT_REQUIRED", "--reason", "cli",
                  "--residual", "r.md", "--receipt", str(rp)])
    check("V-PIVOT-RECEIPT-CLI", rc == 0 and ((gm.load("m-cli").get("owner_hold") or {}).get("receipt") or {})
          .get("method_class") == "cli-route", f"rc={rc}")

    # S11H P5: a job that ENDED (lifecycle word in its record) is relayed as a dead owner, never as a decision
    # recovery (GEX44 2026-11-03 09:54:41Z spent one on the "question" `stopped`) and never surfaced as blocked.
    _mission("m-life", False)
    blk = [{"sessionId": "m-life-w", "id": "m-life-w"[:8], "kind": "background", "state": "blocked"}]
    lp = gm.plan_next(gm.load("m-life"), NOW + 60, blk, pid_alive=gone,
                      blocked_probe=lambda r: {"class": "STOPPED", "why": "job ended (blocked: stopped)"})
    check("V-PIVOT-LIFECYCLE-RELAYS", lp["action"] == "replace" and not lp.get("decision")
          and "decision recovery" not in lp.get("reason", ""), f"{lp['action']}: {lp.get('reason', '')[:100]}")

    # PA2-PR5: a fresh worker of an opted-in mission learns the typed checkpoint from its card, not from a prompt.
    on_card = gm.render_card(gm.load("m-cli"), {"head": "abc", "dirty": []})
    off_card = gm.render_card(gm.load("m-off"), {"head": "abc", "dirty": []})
    check("V-PIVOT-CARD-TEACHES-RECEIPT", "--receipt" in on_card and "method_class" in on_card
          and "--receipt" not in off_card, "opted-in card names --receipt; a mission without pivot autonomy does not")

    print(f"PIVOT_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


# --drills: each mutant of gsd_mission.py must turn the named gate red (the drill never writes tools/gsd_mission.py).
DRILLS = (
    ("D1 opt-in ignored", 'or not rec.get("pivot_autonomy") or not pivot_autonomy_on()', "or not pivot_autonomy_on()",
     "V-PIVOT-OPT-IN-ONLY"),
    ("D2 owner gate skipped", '    if objs:\n        why = "authority object(s) "',
     '    if False:\n        why = "authority object(s) "', "V-PIVOT-OWNER-BOUNDARY"),
    ("D3 streak cap removed", "if streak >= PIVOT_MAX_STREAK:", "if False:", "V-PIVOT-STREAK-CAP"),
    ("D4 blocked-after-checkpoint release removed",
     "return started <= set_at and now - set_at >= CHECKPOINT_BLOCKED_GRACE_S", "return False",
     "V-PIVOT-BLOCKED-AFTER-CHECKPOINT"),
    ("D5 grace dropped", "return started <= set_at and now - set_at >= CHECKPOINT_BLOCKED_GRACE_S",
     "return started <= set_at", "V-PIVOT-BLOCKED-GRACE"),
    ("D6 waitingFor not excluded", 'if not row or row.get("waitingFor") or row.get("state") != "blocked":',
     'if not row or row.get("state") != "blocked":', "V-PIVOT-PERMISSION-PROMPT-STAYS"),
    ("D7 declaration order ignored", "return started <= set_at and now - set_at", "return now - set_at",
     "V-PIVOT-BLOCKED-LATER-JOB-STAYS"),
    ("D8 typed authority objects ignored", 'objs = list((r or {}).get("authority_objects") or [])', "objs = []",
     "V-PIVOT-RECEIPT-AUTHORITY-OBJECT"),
    ("D9 wording net dropped when a receipt exists", 'g = mpol.gate_question(hold.get("reason") or "", {})',
     'g = {"result": "RESOLVE_BY_DEFAULT"} if r else mpol.gate_question(hold.get("reason") or "", {})',
     "V-PIVOT-RECEIPT-WORDING-NET-STAYS"),
    ("D10 Gen2 early stop removed", 'if not r["evidence_delta"] and any(', "if False and any(",
     "V-PIVOT-GEN2-EARLY-STOP"),
    ("D11 independence ignored", "if not independent or left is None", "if left is None",
     "V-PIVOT-GEN2-REPEAT-CLASS-NO-EXTENSION"),
    ("D12 authority-left ignored", " or left < PIVOT_LEASE_MIN_TOKENS:", ":", "V-PIVOT-GEN2-AUTHORITY-LEFT"),
    ("D13 lifecycle relay removed", 'if cls == "STOPPED":', "if False:", "V-PIVOT-LIFECYCLE-RELAYS"),
    ("D14 card receipt lesson removed", 'if rec.get("pivot_autonomy") else []),', "if False else []),",
     "V-PIVOT-CARD-TEACHES-RECEIPT"),
    ("D15 receipt validation bypassed", "        receipt = validate_receipt(receipt)\n", "        receipt = receipt\n",
     "V-PIVOT-RECEIPT-INVALID-REFUSED"),
)


def drills() -> int:
    import subprocess
    here = Path(__file__).resolve().parent
    src = (here / "gsd_mission.py").read_text(encoding="utf-8")
    ok = 0
    for name, needle, repl, gate in DRILLS:
        if needle not in src:
            print(f"DRILL-FAIL {name}: needle absent from tools/gsd_mission.py")
            continue
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "gsd_mission.py").write_text(src.replace(needle, repl, 1), encoding="utf-8")
            r = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve())], capture_output=True, text=True,
                               env={**os.environ, "GSD_MISSION_DRILL_DIR": td}, timeout=300)
        red = f"FAIL {gate}" in r.stdout
        print(f"{'DRILL-PASS' if red else 'DRILL-FAIL'} {name}: expected 'FAIL {gate}' -> {'seen' if red else 'NOT seen'}")
        ok += int(red)
    print(f"PIVOT_DRILLS_PASS={ok}/{len(DRILLS)}")
    return 0 if ok == len(DRILLS) else 1


if __name__ == "__main__":
    sys.exit(drills() if "--drills" in sys.argv[1:] else main())
