#!/usr/bin/env python
"""V-AMR-* gates for Autonomous Mission Recovery (vault/plans/amr-autonomous-mission-recovery-20261013.md).

Fixture = the KSP-FUSION incident of 2026-10-13 (m-342bc71ba415), at zero provider cost: a small clear GSD phase,
a gsd-planner subagent that spent above the stall budget, no PLAN.md, no product delta, a hand-back that carries the
design, an untracked CONTEXT file, a hook-written file in the tree, and a cost hold. Expected: recover, not park.

Every refusal has a paired control. Hermetic: state dir, Claude config dir and work tree are temp directories.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="amr-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["CLAUDE_CONFIG_DIR"] = str(Path(TMP) / "cc")
for k in ("CPP_MISSION_RECOVERY", "CPP_ROUTE_ADMISSION", "CPP_CCR_ADMISSION", "CPP_COG_ADMISSION"):
    os.environ.pop(k, None)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gsd_mission as gm  # noqa: E402
import mission_recovery as mr  # noqa: E402
import mission_spend as ms  # noqa: E402

gm.progress_fingerprint = lambda work_dir: "fp-fixture"
GIT = gm.resolve_exe("git")
NOW = 1_800_000_000.0
TRIP = ("cost breaker: 4,471,659 processed since the work tree last changed (stall budget 3,750,000); "
        "semantic progress is not keeping up with spend")
GSD_OK = lambda wd, workstream=None: {"outcome": "OK"}  # noqa: E731
HANDBACK = "[Subagent hand-back] ## PLANNING INCONCLUSIVE\n" + ("Plan 01 tracer on SP1-L5177-5223. " * 80)
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}"[:220])
    else:
        fails += 1
        print(f"FAIL {gate} {ev}"[:400])


def _git(wd, *a):
    subprocess.run([GIT, "-C", str(wd), *a], capture_output=True, text=True, check=True)


def make_tree(name: str, *, plans=(), state=True, phase=1) -> Path:
    wd = Path(TMP) / name
    ws = wd / ".planning" / "workstreams" / "ksp"
    (ws / "phases" / "01-debt").mkdir(parents=True)
    (ws / "phases" / "02-universe").mkdir(parents=True)
    if state:
        (ws / "STATE.md").write_text(f"---\ncurrent_phase: {phase:02d}\n---\n", encoding="utf-8")
    (ws / "ROADMAP.md").write_text(
        "### Phase 1: SP1 debt\n**Success Criteria**:\n  1. tests red on mutations\n  2. 25 sub-records\n\n"
        "### Phase 2: Semantic universe\n  1. schema\n", encoding="utf-8")
    for p in plans:
        (ws / "phases" / "01-debt" / p).write_text("plan", encoding="utf-8")
    (wd / "vault" / "handoffs").mkdir(parents=True)
    (wd / "vault" / "handoffs" / "escalations.json").write_text("{}", encoding="utf-8")
    _git(wd, "init", "-q")
    _git(wd, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    _git(wd, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "seed")
    # after the seed: an untracked CONTEXT (capital) and a hook rewrite (noise)
    (ws / "phases" / "01-debt" / "01-CONTEXT.md").write_text("context", encoding="utf-8")
    (wd / "vault" / "handoffs" / "escalations.json").write_text('{"n": 2}', encoding="utf-8")
    return wd


def transcript(wd: Path, sid: str, *, planner=True, handback=True, tokens=6_000_000):
    d = ms.projects_root() / ms.encode_cwd(str(wd))
    d.mkdir(parents=True, exist_ok=True)
    rows = [{"type": "assistant", "timestamp": "2027-01-15T08:00:00", "message": {
        "id": f"{sid}-m1", "model": "claude", "usage": {"input_tokens": tokens},
        "content": ([{"type": "tool_use", "id": "tu1", "name": "Agent",
                      "input": {"subagent_type": "gsd-planner", "description": "Plan Phase 1", "prompt": "x",
                                "run_in_background": True}}] if planner else [])}}]
    if handback:
        rows.append({"type": "user", "message": {"content": HANDBACK}})
    (d / f"{sid}.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    sub = d / sid / "subagents"
    sub.mkdir(parents=True, exist_ok=True)
    (sub / "agent-a1.jsonl").write_text(json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Write", "input": {"file_path": str(Path(TMP) / "scan.py")}}]}}) + "\n",
        encoding="utf-8")


def held_mission(mid: str, wd: Path, *, estimate=7_500_000, kind="cost", tokens=6_000_000, planner=True,
                 handback=True) -> dict:
    gm.create(str(wd), "/gsd-autonomous --ws ksp", mission_id=mid, workstream="ksp", now=NOW)
    sid = f"{mid}-worker"
    owner = {"session_id": sid, "pid": None, "proc_start": None, "heartbeat_at": NOW, "epoch": 2,
             "kind": "background"}
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.RUNNING,
                  epoch=2, max_hours=100.0, owner=owner, token_estimate=estimate,
                  card="HEAD at hand-off: " + subprocess.run([GIT, "-C", str(wd), "rev-parse", "HEAD"],
                                                              capture_output=True, text=True).stdout.strip())
    transcript(wd, sid, planner=planner, handback=handback, tokens=tokens)
    gm.set_owner_hold(mid, TRIP, now=NOW, kind=kind)
    return gm.load(mid)


SIDS = [f"m-aaa00000000{c}-worker" for c in "0123456789abcd"] + [f"m-aaa0000000a{c}-worker" for c in "1234567"] + ["m-aaa000000001-succ1", "m-aaa000000001-succ2"]
DONE = [{"sessionId": s, "id": s[:8], "kind": "background", "state": "done"} for s in SIDS]


def blocked_row(mid):
    return [{"sessionId": f"{mid}-worker", "id": f"{mid}-worker"[:8], "kind": "background", "state": "blocked"}]


LAUNCHES = []


def fake_launch(mid, **kw):
    LAUNCHES.append((mid, kw))
    return {"ok": True, "epoch": kw["expect_epoch"] + 1, "bg_id": "bg123456"}


def stop_ok(argv):
    return subprocess.CompletedProcess(argv, 0, "", "")


def main() -> int:
    # --- 1. pure units --------------------------------------------------------------------------------
    s1 = mr.strategy_identity("g", "u", mr.PLANNER_AGENT, ["gsd-planner"])
    s2 = mr.strategy_identity("g", "u", mr.PLANNER_AGENT, ["gsd-planner"])          # new session, same planner
    s3 = mr.strategy_identity("g", "u", mr.MAIN_THREAD, [], "residual-in-order")
    check("V-AMR-STRATEGY-SAME-PLANNER-NEW-SESSION-EQUAL", s1 == s2)
    check("V-AMR-STRATEGY-MAIN-THREAD-MATERIALLY-DIFFERENT", s1 != s3)
    check("V-AMR-HOOK-OWNED-PATH-NOT-PROGRESS", mr.path_class("vault/handoffs/escalations.json") is None)
    # m-0a2b4dad289b (2026-10-17): every successor's first residual was "commit the uncommitted capital" =
    # session learnings a hook writes each session, so the item never ran out and polluted the product repo.
    session = [".claude/cache/learnings/2026-10-17_07ec482e.md", "LEARNINGS_PENDING.md", ".pp-capabilities",
               "_audit_cache/insights.json", ".claude/settings.local.json", ".claude\\cache\\learnings\\a.md"]
    check("V-AMR-SESSION-ARTIFACT-NOT-CAPITAL", all(mr.path_class(p) is None for p in session),
          str({p: mr.path_class(p) for p in session}))
    # lstrip("./") stripped characters, so .planning/ never read as PLAN.
    check("V-AMR-PLANNING-PATH-IS-PLAN", mr.path_class(".planning/phases/01-x/01-01-PLAN.md") == mr.PLAN,
          str(mr.path_class(".planning/phases/01-x/01-01-PLAN.md")))
    check("V-AMR-CONTROL-PATH-CLASSES-KEPT", mr.path_class("docs/dws/x.md") == mr.KNOWLEDGE
          and mr.path_class("./src/main/a.ts") == mr.PRODUCT and mr.path_class("tests/e2e/a.spec.ts") == mr.PROOF)
    # Every plan executed, no VERIFICATION.md: GSD says "verify", so the residual must ask for it, or the same
    # unit closes DONE and is recompiled forever (m-0a2b4dad289b r2, r3).
    done_unit = {"phase": 1, "name": "Row 61", "criteria": ["c1"], "plans": ["01-01-PLAN.md"],
                 "executed": ["01-01-PLAN.md"], "has_verification": False}
    res_v = mr.compile_residual(done_unit, [])
    check("V-AMR-RESIDUAL-ASKS-VERIFICATION", any("VERIFICATION.md" in i["do"] for i in res_v), str(res_v)[:300])
    res_nv = mr.compile_residual({**done_unit, "has_verification": True}, [])
    check("V-AMR-CONTROL-VERIFIED-UNIT-NOT-ASKED", not any("VERIFICATION.md" in i["do"] for i in res_nv))
    p0 = mr.classify_progress([], {"measured": False, "handbacks": []}, False)
    check("V-AMR-UNMEASURED-IS-UNKNOWN-NOT-ZERO", p0["class"] == mr.UNKNOWN, p0["class"])
    p1 = mr.classify_progress([], {"measured": True, "handbacks": []}, True)
    check("V-AMR-CONTROL-MEASURED-NOTHING-IS-ZERO", p1["class"] == mr.ZERO, p1["class"])
    p2 = mr.classify_progress(["vault/handoffs/escalations.json"], {"measured": True, "handbacks": [HANDBACK]}, True)
    check("V-AMR-HANDBACK-DESIGN-IS-PLAN-PROGRESS", p2["class"] == mr.PLAN and not p2["product"], str(p2))
    f = mr.classify_failure(TRIP, {"agents": [{"type": "gsd-planner"}]}, p2, s1, [])
    check("V-AMR-MODE-ROUTER-PLANNER-FAILURE-TYPED", f == mr.PLANNER_TOPOLOGY_FAILURE, f)
    t = mr.recompile_topology(f, "u", "g", ["gsd-planner"], [s1])
    check("V-AMR-DEFLATES-TO-MAIN-THREAD-EXECUTION", t and t["mode"] == "EXECUTION" and t["topology"] == mr.MAIN_THREAD
          and "gsd-planner" in t["deny_agent_types"] and t["strategy"] != s1, str(t)[:160])
    check("V-AMR-FENCED-SUCCESSOR-NOT-RECOMPILED", mr.recompile_topology(f, "u", "g", [], [s1, t["strategy"]]) is None)
    check("V-AMR-UNCLASSIFIED-HAS-NO-TOPOLOGY", mr.recompile_topology(mr.UNCLASSIFIED, "u", "g", [], []) is None)
    lease = mr.price_lease(6_000_000, 15_000_000, [1, 2, 3])
    check("V-AMR-LEASE-BOUNDED-BELOW-REMAINING", lease["ok"] and lease["lease"] <= int(9_000_000 * 0.85)
          and lease["lease"] == 6_000_000, str(lease))
    check("V-AMR-LEASE-EXHAUSTED-REFUSES", not mr.price_lease(14_500_000, 15_000_000, [1])["ok"])
    check("V-AMR-LEASE-UNMEASURED-REFUSES", not mr.price_lease(None, 15_000_000, [1])["ok"])

    # --- 2. the incident: plan_next answers recover, recovery launches a deflated successor -------------
    wd = make_tree("incident")
    rec = held_mission("m-aaa000000001", wd)
    guard = ms.budget_path("m-aaa000000001-worker")
    guard_before = guard.read_bytes() if guard.exists() else b""
    plan = gm.plan_next(rec, NOW + 60, blocked_row("m-aaa000000001"), pid_alive=lambda p: False)
    check("V-AMR-COST-HOLD-PLANS-RECOVER", plan["action"] == "recover", str(plan))
    LAUNCHES.clear()
    row = gm.recover_mission(rec, blocked_row("m-aaa000000001"), NOW + 60, pid_alive=lambda p: False,
                             stop_runner=stop_ok, launch=fake_launch, gsd_status=GSD_OK)
    after = gm.load("m-aaa000000001")
    check("V-AMR-RECOVERED-AND-LAUNCHED", row["action"] == "recovered" and len(LAUNCHES) == 1, str(row)[:200])
    check("V-AMR-HOLD-SUPERSEDED-NOT-DELETED", after.get("owner_hold") is None
          and (after.get("last_recovery") or {}).get("hold", {}).get("kind") == "cost")
    check("V-AMR-OLD-EXECUTOR-FENCE-KEPT", guard.exists() and guard.read_bytes() == guard_before
          and json.loads(guard_before or b"{}").get("stop") == 1)
    amr = after.get("amr") or {}
    hist = (amr.get("history") or [{}])[-1]
    check("V-AMR-FAILED-STRATEGY-FENCED", hist.get("failed_strategy") in amr.get("fenced", [])
          and hist.get("strategy") not in amr.get("fenced", []), str(amr.get("fenced")))
    check("V-AMR-FAILURE-AND-PROGRESS-RECORDED", hist.get("failure") == mr.PLANNER_TOPOLOGY_FAILURE
          and hist.get("progress") in (mr.PLAN, mr.MIXED), str(hist)[:200])
    pkt = Path((after.get("wu_packet") or {}).get("path") or "")
    text = pkt.read_text(encoding="utf-8") if pkt.is_file() else ""
    check("V-AMR-CONTEXTIMAGE-MINIMAL", pkt.is_file() and len(text) < 6000 and "Residual, in order" in text
          and "Write the plan files" in text and "01-CONTEXT.md" in text, f"{len(text)} chars")
    delta = Path(hist.get("dir", "")) / "semantic_delta.md"
    check("V-AMR-FAILED-ATTEMPT-CAPITALIZED", delta.is_file() and "Plan 01 tracer" in delta.read_text(encoding="utf-8")
          and str(delta) in text)
    check("V-AMR-NO-TRANSCRIPT-REPLAY", HANDBACK[:200] not in text)
    spent = hist.get("spent")
    est = after.get("token_estimate")
    check("V-AMR-SPEND-SETTLED-LEASE-PRICED", spent and (after.get("cost_mark") or {}).get("tokens") == spent
          and abs(2 * est - (spent + hist["lease"])) <= 2, f"spent={spent} est={est} lease={hist.get('lease')}")
    check("V-AMR-SUCCESSOR-ROUTE-ADMITTED", (after.get("admission") or {}).get("verdict") in gm.LAUNCHABLE_VERDICTS,
          str((after.get("admission") or {}).get("reasons")))
    check("V-AMR-PGO-ROW", any('"result": "LAUNCHED"' in ln for ln in
                               (Path(TMP) / "recovery" / "pgo.jsonl").read_text(encoding="utf-8").splitlines()))
    check("V-AMR-NOT-IN-WORK-TREE", not any(str(wd) in str(p) for p in (pkt, delta)))

    # --- 3. the successor itself stalls: second recovery narrows; third is an Owner boundary ------------
    transcript(wd, "m-aaa000000001-succ1", planner=False, handback=False, tokens=4_000_000)
    gm.transition("m-aaa000000001", expect_epoch=after["epoch"], expect_state=after["state"], event="t_adopt",
                  now=NOW + 100, state=gm.RUNNING, owner={"session_id": "m-aaa000000001-succ1", "pid": None,
                  "proc_start": None, "heartbeat_at": NOW, "epoch": after["epoch"], "kind": "background"},
                  worker="m-aaa000000001-succ1")
    gm.set_owner_hold("m-aaa000000001", TRIP, now=NOW + 200, kind="cost")
    r2 = gm.recover_mission(gm.load("m-aaa000000001"), DONE, NOW + 210, stop_runner=stop_ok, launch=fake_launch, gsd_status=GSD_OK)
    a2 = gm.load("m-aaa000000001")
    h2 = (a2.get("amr") or {}).get("history", [{}])[-1]
    check("V-AMR-SECOND-RECOVERY-DIFFERENT-STRATEGY", r2["action"] == "recovered" and h2.get("failed_strategy") == hist.get("strategy")
          and h2.get("strategy") not in (hist.get("strategy"), hist.get("failed_strategy")), str(r2)[:160])
    transcript(wd, "m-aaa000000001-succ2", planner=False, handback=False, tokens=2_000_000)
    gm.transition("m-aaa000000001", expect_epoch=a2["epoch"], expect_state=a2["state"], event="t_adopt", now=NOW + 300,
                  state=gm.RUNNING, owner={"session_id": "m-aaa000000001-succ2", "pid": None, "proc_start": None,
                                           "heartbeat_at": NOW, "epoch": a2["epoch"], "kind": "background"},
                  worker="m-aaa000000001-succ2")
    gm.set_owner_hold("m-aaa000000001", TRIP, now=NOW + 400, kind="cost")
    r3 = gm.recover_mission(gm.load("m-aaa000000001"), DONE, NOW + 410, stop_runner=stop_ok, launch=fake_launch, gsd_status=GSD_OK)
    a3 = gm.load("m-aaa000000001")
    check("V-AMR-RECURSION-BOUNDED", r3["action"] == "recover_boundary" and "recursion cap" in r3["reason"]
          and (a3.get("owner_hold") or {}).get("recovery", {}).get("state") == mr.OWNER_BOUNDARY, str(r3)[:160])
    p3 = gm.plan_next(a3, NOW + 500, DONE, pid_alive=lambda p: False)
    check("V-AMR-BOUNDARY-PARKS-NOT-SETTLES", p3["action"] == "none" and "boundary" in p3["reason"], str(p3)[:160])
    check("V-AMR-BOUNDARY-DECISION-PACKET", (Path(TMP) / "recovery" / "m-aaa000000001" / "owner-decision.md").is_file())

    # --- 4. authority exhausted -> Owner boundary, hold kept; control: authority raised -> recovers ------
    wd4 = make_tree("exhausted")
    rec4 = held_mission("m-aaa000000004", wd4, estimate=3_100_000, tokens=6_000_000)
    r4 = gm.recover_mission(rec4, DONE, NOW + 60, stop_runner=stop_ok, launch=fake_launch, gsd_status=GSD_OK)
    a4 = gm.load("m-aaa000000004")
    check("V-AMR-AUTHORITY-EXHAUSTED-OWNER-BOUNDARY", r4["action"] == "recover_boundary" and a4.get("owner_hold")
          and "authority exhausted" in str(a4["owner_hold"]["recovery"]["why"]), str(r4)[:160])
    check("V-AMR-AUTHORITY-NOT-SELF-EXPANDED", a4.get("authority_tokens") is None)
    wd4b = make_tree("raised")
    held_mission("m-aaa000000005", wd4b, estimate=3_100_000, tokens=6_000_000)
    gm.set_authority("m-aaa000000005", "20M", reason="test Owner raise")
    r4b = gm.recover_mission(gm.load("m-aaa000000005"), DONE, NOW + 60, stop_runner=stop_ok, launch=fake_launch, gsd_status=GSD_OK)
    check("V-AMR-CONTROL-AUTHORITY-RAISED-RECOVERS", r4b["action"] == "recovered", str(r4b)[:160])

    # --- 5. Owner park, kill switch, shadow -----------------------------------------------------------
    wd5 = make_tree("ownerpark")
    held_mission("m-aaa000000006", wd5, kind=None)
    gm.transition("m-aaa000000006", expect_epoch=2, expect_state=gm.RUNNING, event="t_reason", now=NOW,
                  owner_hold={"reason": "Owner park for review", "set_at": NOW})
    p5 = gm.plan_next(gm.load("m-aaa000000006"), NOW + 60, blocked_row("m-aaa000000006"), pid_alive=lambda p: False)
    check("V-AMR-OWNER-PARK-NOT-RECOVERED", p5["action"] != "recover", str(p5))
    check("V-AMR-LIVENESS-OWNER-PARK-IS-BOUNDARY", mr.goal_liveness(gm.load("m-aaa000000006")) == "OWNER_BOUNDARY")
    wd6 = make_tree("killswitch")
    rec6 = held_mission("m-aaa000000007", wd6)
    os.environ["CPP_MISSION_RECOVERY"] = "off"
    p6 = gm.plan_next(rec6, NOW + 60, blocked_row("m-aaa000000007"), pid_alive=lambda p: False)
    check("V-AMR-KILL-SWITCH-RESTORES-PARK", p6["action"] != "recover", str(p6))
    check("V-AMR-LIVENESS-INCIDENT-WHEN-RECOVERY-OFF", mr.goal_liveness(rec6) == "LIVENESS_INCIDENT")
    os.environ["CPP_MISSION_RECOVERY"] = "shadow"
    LAUNCHES.clear()
    r6 = gm.recover_mission(rec6, DONE, NOW + 60, stop_runner=stop_ok, launch=fake_launch, gsd_status=GSD_OK)
    a6 = gm.load("m-aaa000000007")
    check("V-AMR-SHADOW-COMPILES-NOT-LAUNCHES", r6["action"] == "recover_shadow" and not LAUNCHES
          and a6.get("owner_hold", {}).get("recovery", {}).get("state") == mr.SHADOW_COMPILED)
    os.environ.pop("CPP_MISSION_RECOVERY", None)
    check("V-AMR-LIVENESS-RECOVERING", mr.goal_liveness(rec6) == "RECOVERING")

    # --- 6. fence failure, launch failure, unreadable residual -------------------------------------------
    wd7 = make_tree("fence")
    rec7 = held_mission("m-aaa000000008", wd7)
    live = [{"sessionId": "m-aaa000000008-worker", "id": "m-aaa000", "kind": "background", "state": "active",
             "pid": 4242}]
    import gsd_mission as _g
    old_wait = _g.STOP_WAIT_S
    _g.STOP_WAIT_S = 0
    r7 = gm.recover_mission(rec7, live, NOW + 60, pid_alive=lambda p: True, stop_runner=stop_ok, launch=fake_launch, gsd_status=GSD_OK)
    _g.STOP_WAIT_S = old_wait
    check("V-AMR-NO-SUCCESSOR-BEFORE-FENCE", r7["action"] == "recover_wait_fence" and not gm.load("m-aaa000000008").get("amr"),
          str(r7)[:160])
    wd8 = make_tree("launchfail")
    rec8 = held_mission("m-aaa000000009", wd8)
    r8 = gm.recover_mission(rec8, DONE, NOW + 60, stop_runner=stop_ok,
                            launch=lambda mid, **kw: {"ok": False, "why": "launch refused"}, gsd_status=GSD_OK)
    check("V-AMR-LAUNCH-FAILURE-VISIBLE", r8["action"] == "recover_launch_failed", str(r8)[:160])
    wd9 = make_tree("nostate", state=False)
    rec9 = held_mission("m-aaa00000000a", wd9)
    r9 = gm.recover_mission(rec9, DONE, NOW + 60, stop_runner=stop_ok, launch=fake_launch, gsd_status=GSD_OK)
    # AMCR (2026-10-15, m-4e31db7aca3f): an unreadable residual is a FAILED recovery, retried, then a surfaced
    # liveness incident -- it used to become NOT_APPLICABLE, i.e. a silent Owner wait.
    check("V-AMR-RESIDUAL-UNKNOWN-IS-RECOVERY-FAILED", r9["action"] == "recover_failed" and "UNKNOWN" in r9["reason"]
          and gm.plan_next(gm.load("m-aaa00000000a"), NOW + 99, [], pid_alive=lambda p: False)["action"] == "recover"
          and mr.goal_liveness(gm.load("m-aaa00000000a")) == "RECOVERING", str(r9)[:200])
    for k in (2, 3):
        r9 = gm.recover_mission(gm.load("m-aaa00000000a"), DONE, NOW + 60 * k, stop_runner=stop_ok, launch=fake_launch,
                                gsd_status=GSD_OK)
    a9 = gm.load("m-aaa00000000a")
    check("V-AMR-RESIDUAL-UNKNOWN-EXHAUSTS-TO-INCIDENT",
          (a9["owner_hold"]["recovery"] or {}).get("state") == mr.RECOVERY_EXHAUSTED
          and mr.goal_liveness(a9) == "LIVENESS_INCIDENT"
          and gm.plan_next(a9, NOW + 999, [], pid_alive=lambda p: False)["action"] != "recover", str(a9.get("owner_hold"))[:200])
    with_kill = dict(os.environ)
    os.environ["CPP_MISSION_CONTINUITY"] = "off"
    try:
        wd9b = make_tree("nostate-legacy", state=False)
        r9b = gm.recover_mission(held_mission("m-aaa0000000a7", wd9b), DONE, NOW + 60, stop_runner=stop_ok,
                                 launch=fake_launch, gsd_status=GSD_OK)
    finally:
        os.environ.clear(); os.environ.update(with_kill)
    check("V-AMR-RESIDUAL-UNKNOWN-KILL-SWITCH-LEGACY", r9b["action"] == "recover_not_applicable", str(r9b)[:160])
    wd11 = make_tree("complete")
    rec11 = held_mission("m-aaa00000000c", wd11)
    r11 = gm.recover_mission(rec11, DONE, NOW + 60, stop_runner=stop_ok, launch=fake_launch,
                             gsd_status=lambda wd, workstream=None: {"outcome": "ALL_COMPLETE", "reason": "done"})
    check("V-AMR-GSD-COMPLETE-NOT-RECOVERED", r11["action"] == "recover_not_applicable" and not gm.load("m-aaa00000000c").get("amr"))
    wd12 = make_tree("unknown")
    rec12 = held_mission("m-aaa00000000d", wd12)
    LAUNCHES.clear()
    r12 = gm.recover_mission(rec12, None, NOW + 60, stop_runner=stop_ok, launch=fake_launch, gsd_status=GSD_OK)
    check("V-AMR-UNKNOWN-LIVENESS-NO-SECOND-WRITER", r12["action"] == "recover_wait_liveness" and not LAUNCHES
          and gm.load("m-aaa00000000d").get("owner_hold") and not gm.load("m-aaa00000000d").get("amr"), str(r12)[:160])

    # --- 7. unit advance keeps the deflated topology and the fence ---------------------------------------
    wd10 = make_tree("advance")
    rec10 = held_mission("m-aaa00000000b", wd10)
    gm.recover_mission(rec10, DONE, NOW + 60, stop_runner=stop_ok, launch=fake_launch, gsd_status=GSD_OK)
    a10 = gm.load("m-aaa00000000b")
    st = wd10 / ".planning" / "workstreams" / "ksp" / "STATE.md"
    st.write_text("---\ncurrent_phase: 02\n---\n", encoding="utf-8")
    n10, ok10 = gm.amr_advance(a10, NOW + 900)
    check("V-AMR-ADVANCE-NEXT-UNIT-SAME-FENCE", ok10 and (n10.get("amr") or {}).get("unit") == "ksp/phase-02"
          and n10["amr"]["deny_agent_types"] == a10["amr"]["deny_agent_types"]
          and n10["wu_packet"]["path"] != a10["wu_packet"]["path"], str((n10.get("amr") or {}).get("unit")))
    # The unit it advanced INTO closed again and GSD still lists it: its packet's done does not match GSD's.
    # A third compile of the same unit is a loop (m-0a2b4dad289b r3), so it parks at an Owner boundary.
    n10b, ok10b = gm.amr_advance(gm.load("m-aaa00000000b"), NOW + 950)
    check("V-AMR-SAME-UNIT-CLOSED-TWICE-PARKS", ok10b is False
          and (n10b.get("owner_hold") or {}).get("recovery", {}).get("state") == mr.OWNER_BOUNDARY
          and "same unit" in str((n10b.get("owner_hold") or {}).get("reason")), str(n10b.get("owner_hold"))[:200])

    # --- 8. the spawn hook enforces the fence ------------------------------------------------------------
    Path(TMP, "mission-worker-succ-sid.json").write_text(json.dumps({"mission_id": "m-aaa000000001"}), encoding="utf-8")
    hook = HERE.parent / "hooks" / "amr_fence.js"

    def spawn(sid, st):
        js = (f"const m=require({json.dumps(str(hook))});process.stdout.write(JSON.stringify(m.decide("
              f"{{session_id:{json.dumps(sid)},tool_name:'Agent',tool_input:{{prompt:'plan it '+Math.random(),"
              f"subagent_type:{json.dumps(st)}}}}},Date.now())))")
        out = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60,
                             env={**os.environ, "GSD_LONG_RUN_STATE_DIR": TMP})
        return json.loads(out.stdout or "null") or {}
    d1 = spawn("succ-sid", "gsd-planner")
    check("V-AMR-SPAWN-HOOK-DENIES-FENCED-PLANNER", "AMR FENCE" in str(d1.get("deny")), str(d1)[:160])
    check("V-AMR-CONTROL-SPAWN-HOOK-ALLOWS-EXPLORE", not spawn("succ-sid", "Explore").get("deny"))
    check("V-AMR-CONTROL-SPAWN-HOOK-UNFENCED-SESSION", not spawn("other-sid", "gsd-planner").get("deny"))

    # marker dir differs from state dir (audit F8): the fence must still find the worker
    md = Path(TMP) / "markers"
    md.mkdir(exist_ok=True)
    (md / "mission-worker-mk-sid.json").write_text(json.dumps({"mission_id": "m-aaa000000001"}), encoding="utf-8")
    js = (f"const m=require({json.dumps(str(hook))});process.stdout.write(JSON.stringify(m.decide("
          f"{{session_id:'mk-sid',tool_name:'Agent',tool_input:{{subagent_type:'gsd-planner'}}}})))")
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60,
                         env={**os.environ, "GSD_LONG_RUN_STATE_DIR": TMP, "GSD_AUTORUN_MARKER_DIR": str(md)})
    check("V-AMR-FENCE-READS-MARKER-DIR", "AMR FENCE" in out.stdout, out.stdout[:120])
    check("V-AMR-READ-ONLY-AGENT-NEVER-FENCED",
          "Explore" not in mr.recompile_topology(mr.PLANNER_TOPOLOGY_FAILURE, "u", "g", ["gsd-planner", "Explore"], [])["deny_agent_types"])

    # --- 9. audit findings, each with its failure scenario --------------------------------------------
    # F1: an Owner hold lands between lease and commit -> nothing launched, the Owner's hold survives.
    wdA = make_tree("interleave")
    recA = held_mission("m-aaa0000000a1", wdA)
    real_admit = gm.admit_route

    def admit_then_owner(mid, route, **kw):
        real_admit(mid, route, **kw)
        gm.set_owner_hold(mid, "Owner: stop everything", now=NOW + 77)
        return gm.load(mid)
    gm.admit_route = admit_then_owner
    LAUNCHES.clear()
    rA = gm.recover_mission(recA, DONE, NOW + 60, stop_runner=stop_ok, launch=fake_launch, gsd_status=GSD_OK)
    gm.admit_route = real_admit
    hA = gm.load("m-aaa0000000a1").get("owner_hold") or {}
    check("V-AMR-F1-OWNER-HOLD-NOT-OVERWRITTEN", rA["action"] == "recover_conflict" and not LAUNCHES
          and hA.get("reason") == "Owner: stop everything", str(rA)[:160])
    try:
        gm.transition("m-aaa0000000a1", expect_epoch=2, expect_state=gm.RUNNING, expect_seq=0, event="t", now=NOW)
        stale_ok = True
    except gm.CasConflict:
        stale_ok = False
    check("V-AMR-F1-SEQ-CAS-REFUSES-STALE-WRITE", not stale_ok)
    # F2: the lease pins wu_packet_epoch, so a refused launch is followed by a FRESH worker, not a continuation.
    a1 = gm.load("m-aaa000000001")
    check("V-AMR-F2-PACKET-EPOCH-PINNED", a1.get("wu_packet_epoch") is not None)
    # F4: an exhausted mission budget is a boundary, not a launch; capsule-v2 missions are not eligible.
    wdB = make_tree("budget")
    recB = held_mission("m-aaa0000000a2", wdB)
    gm.transition("m-aaa0000000a2", expect_epoch=2, expect_state=gm.RUNNING, event="t", now=NOW, max_hours=0.001)
    rB = gm.recover_mission(gm.load("m-aaa0000000a2"), DONE, NOW + 3600, stop_runner=stop_ok, launch=fake_launch,
                            gsd_status=GSD_OK)
    check("V-AMR-F4-BUDGET-GATE", rB["action"] == "recover_boundary" and "budget" in rB["reason"], str(rB)[:120])
    check("V-AMR-F4-CAPSULE-V2-INELIGIBLE", not mr.eligible({"resume_command": "/gsd-autonomous",
                                                              "rollover_protocol": "capsule-v2"}))
    # F5: an advance that cannot compile parks at a boundary and tells the relay not to launch.
    recC = gm.load("m-aaa00000000b")
    (wd10 / ".planning" / "workstreams" / "ksp" / "STATE.md").write_text("no phase here\n", encoding="utf-8")
    (wd10 / ".planning" / "workstreams" / "ksp" / "ROADMAP.md").unlink()   # nothing GSD could answer from either
    nC, okC = gm.amr_advance(recC, NOW + 1200)
    check("V-AMR-F5-ADVANCE-REFUSAL-PARKS", okC is False
          and (nC.get("owner_hold") or {}).get("recovery", {}).get("state") == mr.OWNER_BOUNDARY)
    # F6: GSD unanswered -> wait, nothing written.
    wdD = make_tree("gsdout")
    recD = held_mission("m-aaa0000000a3", wdD)
    seqD = recD["seq"]
    rD = gm.recover_mission(recD, DONE, NOW + 60, stop_runner=stop_ok, launch=fake_launch,
                            gsd_status=lambda wd, workstream=None: {"outcome": "UNAVAILABLE", "reason": "timeout"})
    check("V-AMR-F6-GSD-OUTAGE-WAITS", rD["action"] == "recover_wait_gsd" and gm.load("m-aaa0000000a3")["seq"] == seqD)
    # F3: our stop is recorded on the hold.
    wdE = make_tree("stoprec")
    recE = held_mission("m-aaa0000000a4", wdE)
    gm.transition("m-aaa0000000a4", expect_epoch=2, expect_state=gm.RUNNING, event="t", now=NOW, authority_tokens=7_000_000)
    rE = gm.recover_mission(gm.load("m-aaa0000000a4"), blocked_row("m-aaa0000000a4"), NOW + 60, stop_runner=stop_ok,
                            launch=fake_launch, gsd_status=GSD_OK)
    hE = gm.load("m-aaa0000000a4").get("owner_hold") or {}
    check("V-AMR-F3-STOP-RECORDED-ON-HOLD", rE["action"] == "recover_boundary" and hE.get("worker_stopped_at"),
          str(rE)[:140])

    # --- 10. a productive successor whose lease runs out renews the SAME strategy (law 2 is zero-progress) ----
    wdR = make_tree("renew")
    recR = held_mission("m-aaa0000000a5", wdR)
    gm.recover_mission(recR, DONE, NOW + 60, stop_runner=stop_ok, launch=fake_launch, gsd_status=GSD_OK)
    aR = gm.load("m-aaa0000000a5")
    (wdR / "src.py").write_text("x = 1\n", encoding="utf-8")
    _git(wdR, "-c", "user.email=t@t", "-c", "user.name=t", "add", "src.py")
    _git(wdR, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "real work")
    transcript(wdR, "m-aaa0000000a5-succ", planner=False, handback=False, tokens=3_000_000)
    gm.transition("m-aaa0000000a5", expect_epoch=aR["epoch"], expect_state=aR["state"], event="t_adopt", now=NOW + 100,
                  state=gm.RUNNING, owner={"session_id": "m-aaa0000000a5-succ", "pid": None, "proc_start": None,
                                           "heartbeat_at": NOW, "epoch": aR["epoch"], "kind": "background"},
                  worker="m-aaa0000000a5-succ", authority_tokens=40_000_000)
    gm.set_owner_hold("m-aaa0000000a5", "cost breaker: processed 9,000,000 > 2 x estimate 4,500,000", now=NOW + 200,
                      kind="cost")
    rows = DONE + [{"sessionId": "m-aaa0000000a5-succ", "id": "succ0000", "kind": "background", "state": "done"}]
    rR = gm.recover_mission(gm.load("m-aaa0000000a5"), rows, NOW + 210, stop_runner=stop_ok, launch=fake_launch,
                            gsd_status=GSD_OK)
    bR = gm.load("m-aaa0000000a5")
    hR = bR["amr"]["history"][-1]
    check("V-AMR-PRODUCTIVE-LEASE-RENEWS-SAME-STRATEGY", rR["action"] == "recovered"
          and hR["failure"] == mr.LEASE_EXHAUSTED_WITH_PROGRESS and hR["strategy"] == aR["amr"]["strategy"]
          and hR["strategy"] not in bR["amr"]["fenced"] and hR["cause"] == "renewal", str(hR)[:200])

    # --- 11. supervise-level: the real dispatch and the real launch_worker, host faked at the process edge ---
    wdS = make_tree("supervise")
    held_mission("m-aaa0000000a6", wdS)

    def host(argv, cwd):
        return subprocess.CompletedProcess(argv, 0, f"backgrounded \u00b7 9e9e9e9e \u00b7 {argv[argv.index('-n') + 1]}", "")
    rowsS = gm._supervise_core(now=NOW + 60, sessions=DONE, gsd_status=GSD_OK, runner=host, stop_runner=stop_ok,
                               pid_alive=lambda p: False)
    rowS = next((r for r in rowsS if r.get("mission_id") == "m-aaa0000000a6"), {})
    s6 = gm.load("m-aaa0000000a6")
    check("V-AMR-SUPERVISE-RECOVERS-AND-LAUNCHES", rowS.get("action") == "recovered" and s6["state"] == gm.LAUNCHING
          and (s6.get("pending") or {}).get("bg_id") == "9e9e9e9e" and not s6.get("owner_hold"), str(rowS)[:200])
    check("V-AMR-SUPERVISE-SUCCESSOR-GETS-PACKET-NOT-GSD", "successor-packet.md" in gm.launch_prompt(s6)
          and "/gsd-autonomous" not in gm.launch_prompt(s6))

    print(f"AMR_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
