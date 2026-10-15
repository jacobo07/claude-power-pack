#!/usr/bin/env python
"""V-AMCR-* gates: Autonomous Mission Continuity & Recovery (vault/plans/amcr-mission-continuity-20261015.md).

Fixture = the Credit Score Engine incident of 2026-10-15 (m-4e31db7aca3f), at zero provider cost: a main checkout
the worker may not edit, a worktree it makes with `git worktree add` and enters with Set-Location (its transcript
cwd stays in main), a commit there, a background gsd-phase-researcher, a cost breaker at an 8,524,071 estimate.
The GSD files are the REAL ones that project's GSD 1.14 roadmapper wrote (tools/fixtures/amcr-gsd114), so the
residual parser is tested against its producer, not against a fixture written with the parser's assumption.

Real git repos and worktrees in a temp dir; every refusal has a paired control; the kill switch
CPP_MISSION_CONTINUITY=off reproduces the incident (proving the gates can fail).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="amcr-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["CLAUDE_CONFIG_DIR"] = str(Path(TMP) / "cc")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "cc" / "projects")
for k in ("CPP_MISSION_RECOVERY", "CPP_MISSION_CONTINUITY", "CPP_ROUTE_ADMISSION", "CPP_CCR_ADMISSION",
          "CPP_COG_ADMISSION"):
    os.environ.pop(k, None)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gsd_mission as gm  # noqa: E402
import mission_binding as mb  # noqa: E402
import mission_recovery as mr  # noqa: E402
import mission_spend as ms  # noqa: E402

GIT = gm.resolve_exe("git")
FIXTURE = HERE / "fixtures" / "amcr-gsd114"
EST = 8_524_071                       # the incident's auto envelope; stall budget = EST / 2 = 4,262,035
STALL = int(EST * ms.DEFAULT_STALL_FRACTION)
T0 = time.time()
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}"[:220])
    else:
        fails += 1
        print(f"FAIL {gate} {ev}"[:500])


def git(wd, *a):
    return subprocess.run([GIT, "-C", str(wd), "-c", "user.email=t@t", "-c", "user.name=t", *a],
                          capture_output=True, text=True, check=True).stdout


def repo(name: str) -> Path:
    main = Path(TMP) / name
    shutil.copytree(FIXTURE, main / ".planning")
    (main / "src.txt").write_text("v1\n", encoding="utf-8")
    git(main, "init", "-q", "-b", "main")
    git(main, "add", "-A")
    git(main, "commit", "-qm", "seed")
    return main


def worktree(main: Path, suffix: str, branch: str) -> Path:
    wt = Path(TMP) / f"{main.name}-{suffix}"
    git(main, "worktree", "add", "-q", "-b", branch, str(wt), "main")
    return wt


def commit(wt: Path, rel: str, text: str) -> None:
    p = wt / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    git(wt, "add", "-A")
    git(wt, "commit", "-qm", f"edit {rel}")


def iso(t: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t)) + ".000Z"


def write_transcript(main: Path, sid: str, wt: Path | None, *, child=False) -> Path:
    """The worker's own transcript: cwd stays `main` (Set-Location does not move it); its tool inputs name
    the worktree; optionally a background gsd-phase-researcher that never reported."""
    d = Path(os.environ["GSD_LONG_RUN_PROJECTS_DIR"]) / ms.encode_cwd(str(main))
    d.mkdir(parents=True, exist_ok=True)
    rows = []
    if wt:
        rows.append({"type": "assistant", "timestamp": iso(time.time()), "cwd": str(main), "message": {
            "content": [{"type": "tool_use", "id": "tu-wt", "name": "PowerShell",
                         "input": {"command": f"Set-Location \"{wt}\"; git status"}}]}})
    if child:
        rows.append({"type": "assistant", "timestamp": iso(time.time()), "cwd": str(main), "message": {
            "content": [{"type": "tool_use", "id": "tu-research", "name": "Agent",
                         "input": {"subagent_type": "gsd-phase-researcher", "description": "Research Phase 1",
                                   "prompt": "Research Phase 1 (Cases and Persistence); write 01-RESEARCH.md"}}]}})
        rows.append({"type": "user", "timestamp": iso(time.time()), "message": {"content": [
            {"type": "tool_result", "tool_use_id": "tu-research",
             "content": "Async agent launched successfully. agentId: a1 (runs in the background)"}]}})
    p = d / f"{sid}.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return p


def mission(mid: str, main: Path, sid: str, *, created: float) -> dict:
    gm.create(str(main), "/gsd-autonomous", mission_id=mid, now=created)
    owner = {"session_id": sid, "pid": None, "proc_start": None, "heartbeat_at": created, "epoch": 1,
             "kind": "background"}
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=created, state=gm.RUNNING,
                  epoch=1, max_hours=100.0, owner=owner, token_estimate=EST)
    return gm.load(mid)


def ledger(mid: str, event: str | None = None) -> list[dict]:
    p = Path(TMP) / "gsd-autorun-ledger.jsonl"
    rows = [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()] if p.exists() else []
    return [r for r in rows if r.get("session_id") == mid and (event is None or r.get("event") == event)]


def receipts(mid: str) -> list[str]:
    return [r.get("classification") for r in ledger(mid, "breaker_receipt")]


NO_KIDS = lambda sid, now=None: {"verdict": "CLEAR", "pending": [], "unconsumed": []}  # noqa: E731


def breaker(rec, spent, **kw):
    kw.setdefault("child_fn", NO_KIDS)
    return gm._reconciled_breaker(rec, time.time(), measure=lambda r: spent, **kw)


def incident(name: str, mid: str, *, child=False):
    """main checkout + the worker's worktree, a mission created before the worktree, a transcript naming it."""
    main = repo(name)
    rec = mission(mid, main, f"{mid}-w", created=time.time() - 60)
    wt = worktree(main, "wt", f"gsd/{name}")
    write_transcript(main, f"{mid}-w", wt, child=child)
    return main, wt, rec


# --- R1: main protected -> worktree -> commit -> main clean: no false stall ---------------------------------
main1, wt1, rec = incident("r1", "m-c00000000001")
rec = breaker(rec, 2_048_142)                                       # first look: the worker moved
check("V-AMCR-R1-REBIND-DETECTED", mb.generation(rec) == 1 and mb.execution_root(rec) == str(wt1.resolve())
      and receipts("m-c00000000001")[-1] == mb.TOPOLOGY_CHANGED, str(rec.get("binding"))[:160])
rec = breaker(rec, 2_048_142)                                       # frontier marked in the BOUND root
commit(wt1, ".planning/phases/01-cases-and-persistence/01-CONTEXT.md", "context v2\n")
rec = breaker(rec, 2_048_142 + 5_051_831)                           # the incident's spend, after a real commit
check("V-AMCR-R1-COMMIT-IN-WORKTREE-IS-PROGRESS", not rec.get("owner_hold")
      and receipts("m-c00000000001")[-1] == mb.GOOD and git(main1, "status", "--porcelain") == "",
      str(receipts("m-c00000000001")))
# control: the old observer on the same tree trips exactly as the incident did
os.environ["CPP_MISSION_CONTINUITY"] = "off"
main1b, wt1b, recb = incident("r1legacy", "m-c00000000002")
recb = gm._cost_breaker(recb, time.time(), measure=lambda r: 2_048_142)
commit(wt1b, ".planning/phases/01-cases-and-persistence/01-CONTEXT.md", "context v2\n")
recb = gm._cost_breaker(gm.load("m-c00000000002"), time.time(), measure=lambda r: 2_048_142 + 5_051_831)
os.environ.pop("CPP_MISSION_CONTINUITY")
check("V-AMCR-R1-CONTROL-LEGACY-FALSE-STALL", "since the work tree last changed" in
      str((gm.load("m-c00000000002").get("owner_hold") or {}).get("reason")), "kill switch reproduces the incident")

# --- R4: a clean tree right after a commit is progress; nothing after it is not --------------------------
rec = gm.load("m-c00000000001")
commit(wt1, "src.txt", "v2\n")
rec = breaker(rec, 7_200_000)
check("V-AMCR-R4-CLEAN-TREE-AFTER-COMMIT-IS-PROGRESS", not rec.get("owner_hold")
      and git(wt1, "status", "--porcelain") == "" and receipts("m-c00000000001")[-1] == mb.GOOD)
rec = breaker(rec, 7_200_000 + STALL + 1)
check("V-AMCR-R4-CONTROL-NOTHING-AFTER-IS-ZERO", bool(rec.get("owner_hold"))
      and receipts("m-c00000000001")[-1] == mb.ZERO_CONFIRMED, str(receipts("m-c00000000001")[-2:]))

# --- R4b: an empty commit moves no tree: not progress (anti-gaming) ---------------------------------------
main4, wt4, rec4 = incident("r4b", "m-c00000000003")
rec4 = breaker(breaker(rec4, 1_000_000), 1_000_000)
git(wt4, "commit", "-q", "--allow-empty", "-m", "nothing")
rec4 = breaker(rec4, 1_000_000 + STALL + 1)
check("V-AMCR-R4B-EMPTY-COMMIT-IS-NOT-PROGRESS", bool(rec4.get("owner_hold")), str(receipts("m-c00000000003")))

# --- R3: a sample of an older binding generation never trips -------------------------------------------
main3, wt3, rec3 = incident("r3", "m-c00000000004")
rec3 = breaker(breaker(rec3, 1_000_000), 1_000_000)
wt3b = worktree(main3, "wt2", "gsd/r3-second")


def rebind_mid_judgement(sid, now=None):
    gm.bind_mission("m-c00000000004", str(wt3b))
    return {"verdict": "CLEAR", "pending": [], "unconsumed": []}


rec3 = breaker(gm.load("m-c00000000004"), 1_000_000 + STALL + 1, child_fn=rebind_mid_judgement)
check("V-AMCR-R3-STALE-GENERATION-NO-TRIP", not gm.load("m-c00000000004").get("owner_hold")
      and receipts("m-c00000000004")[-1] == mb.STALE_GENERATION and mb.generation(gm.load("m-c00000000004")) == 2)

# --- R5: research-only progress (no code, an artifact in .planning) ---------------------------------------
main5, wt5, rec5 = incident("r5", "m-c00000000005")
rec5 = breaker(breaker(rec5, 1_000_000), 1_000_000)
gm.transition("m-c00000000005", expect_epoch=1, expect_state=gm.RUNNING, event="t", touch=False, obligations=[
    {"id": "tu-research", "kind": "gsd-phase-researcher", "state": "KILLED_WITH_PARENT", "expect": "-RESEARCH.md",
     "created_at": time.time() - 30}])
(wt5 / ".planning" / "phases" / "01-cases-and-persistence" / "01-RESEARCH.md").write_text("findings\n", encoding="utf-8")
rec5 = breaker(gm.load("m-c00000000005"), 1_000_000 + STALL + 1)
check("V-AMCR-R5-RESEARCH-ARTIFACT-IS-PROGRESS", not rec5.get("owner_hold")
      and receipts("m-c00000000005")[-1] == mb.GOOD)
check("V-AMCR-R5-ARTIFACT-CLOSES-CHILD-OBLIGATION", (rec5.get("obligations") or [{}])[0].get("state") == "COMPLETED",
      str(rec5.get("obligations"))[:200])

# --- R6: a working child extends the stall budget once; parent+child death keeps the obligation ----------
main6, wt6, rec6 = incident("r6", "m-c00000000006", child=True)
rec6 = breaker(breaker(rec6, 1_000_000), 1_000_000)
import gsd_epoch as ge  # noqa: E402
kids = ge.child_work("m-c00000000006-w")
young = lambda sid, now=None: {**kids, "verdict": "HOLD", "youngest_age_s": 60}  # noqa: E731
rec6 = breaker(gm.load("m-c00000000006"), 1_000_000 + STALL + 1, child_fn=young)
check("V-AMCR-R6-WORKING-CHILD-NO-TRIP", not rec6.get("owner_hold")
      and receipts("m-c00000000006")[-1] == mb.CHILD_ACTIVE, str(kids)[:160])
rec6 = breaker(gm.load("m-c00000000006"), 1_000_000 + 2 * STALL + 2, child_fn=young)
obs6 = gm.load("m-c00000000006").get("obligations") or []
check("V-AMCR-R6-CHILD-EXTENSION-IS-BOUNDED", bool(gm.load("m-c00000000006").get("owner_hold")))
check("V-AMCR-R6-OBLIGATION-SAVED-BEFORE-STOP", len(obs6) == 1 and obs6[0]["state"] == "KILLED_WITH_PARENT"
      and obs6[0]["kind"] == "gsd-phase-researcher" and Path(obs6[0]["prompt_ref"]).is_file()
      and "01-RESEARCH.md" in Path(obs6[0]["prompt_ref"]).read_text(encoding="utf-8"), str(obs6)[:200])
card6 = gm.render_card(gm.load("m-c00000000006"))
check("V-AMCR-R6-SUCCESSOR-CARD-CARRIES-OBLIGATION", "OUTSTANDING CHILD WORK" in card6
      and "gsd-phase-researcher" in card6 and f"gen 1, root {wt6.resolve()}" in card6)

# --- R2 + R10: the Credit Score case end to end -- worker died after its commit, legacy stall hold ----------
main2, wt2, rec2 = incident("r2", "m-c00000000007", child=True)
commit(wt2, ".planning/phases/01-cases-and-persistence/01-CONTEXT.md", "context committed by the worker\n")
time.sleep(1.1)
gm.set_owner_hold("m-c00000000007", "cost breaker: 5,051,831 processed since the work tree last changed (stall "
                  "budget 4,262,035); semantic progress is not keeping up with spend", now=time.time(), kind="cost")
gm.bind_mission("m-c00000000007", str(wt2), cause="migration")
dead = [{"sessionId": "m-c00000000007-w", "id": "m-c0000", "kind": "background", "state": "done"}]
plan2 = gm.plan_next(gm.load("m-c00000000007"), time.time(), dead, pid_alive=lambda p: False)
r2 = gm.recover_mission(gm.load("m-c00000000007"), dead, time.time(), pid_alive=lambda p: False,
                        gsd_status=lambda wd, workstream=None: {"outcome": "OK"})
a2 = gm.load("m-c00000000007")
check("V-AMCR-R2-FALSE-STALL-RECONCILED", plan2["action"] == "recover" and r2["action"] == "recover_false_stall"
      and not a2.get("owner_hold") and not a2.get("amr"), str(r2)[:200])
check("V-AMCR-R2-CHILD-OBLIGATION-SURVIVES", [o["state"] for o in a2.get("obligations") or []] == ["KILLED_WITH_PARENT"])
unit = mr.gsd_unit(str(wt2), None)
res = mr.compile_residual(unit, [])
check("V-AMCR-R2-RESIDUAL-IS-RESEARCH-NOT-CONTEXT", unit.get("phase") == 1 and unit.get("has_context")
      and not unit.get("has_research") and res[0]["do"].startswith("Research Phase 1")
      and "do not redo the discussion" in res[0]["do"] and unit.get("source") == "gsd", f"{unit.get('source')} {res[0]}")
plan10 = gm.plan_next(a2, time.time(), dead, pid_alive=lambda p: False)
check("V-AMCR-R10-NEXT-PASS-RELAUNCHES-WITHOUT-OWNER", plan10["action"] in ("replace", "relay"), str(plan10)[:200])
card2 = gm.render_card(a2)
check("V-AMCR-R10-SUCCESSOR-BRIEFED-ON-BOUND-ROOT", f"WORK TREE: the work is in {wt2.resolve()}" in card2
      and "OUTSTANDING CHILD WORK" in card2)
# control: a stall hold whose bound root did NOT change in the window is not "false" (AMR proper handles it)
main2c, wt2c, rec2c = incident("r2c", "m-c00000000008")
gm.bind_mission("m-c00000000008", str(wt2c), cause="migration")
gm.set_owner_hold("m-c00000000008", "cost breaker: 5,000,000 processed since the work tree last changed (stall "
                  "budget 4,262,035); semantic progress is not keeping up with spend", now=time.time(), kind="cost")
check("V-AMCR-R2-CONTROL-REAL-STALL-NOT-RECONCILED", mb.false_stall(gm.load("m-c00000000008"),
                                                                     gm.load("m-c00000000008")["owner_hold"]) is None)

# --- R7: one recovery source unreadable -> the other answers; none -> unreadable (never a silent wait) -----
def broken(*a, **k):
    raise RuntimeError("gsd-tools down")


u7 = mr.gsd_unit(str(wt2), None, manager=broken)
check("V-AMCR-R7-GSD-DOWN-STATE-BODY-ANSWERS", u7.get("phase") == 1 and u7.get("source") == "state.md"
      and u7.get("has_context") is True, str(u7)[:160])
blank = Path(TMP) / "r7blank"
(blank / ".planning").mkdir(parents=True)
(blank / ".planning" / "STATE.md").write_text("# nothing\n", encoding="utf-8")
check("V-AMCR-R7-NOTHING-READABLE-IS-EMPTY", mr.gsd_unit(str(blank), None, manager=broken) == {})

# --- R8: two successive worktrees -- only the latest generation is observed --------------------------------
main8, wt8, rec8 = incident("r8", "m-c00000000009")
rec8 = breaker(rec8, 1_000_000)                                     # gen 1 -> wt8
wt8b = worktree(main8, "wt2", "gsd/r8-second")
write_transcript(main8, "m-c00000000009-w", wt8b)
rec8 = breaker(gm.load("m-c00000000009"), 1_000_000)                # gen 2 -> wt8b
rec8 = breaker(rec8, 1_000_000)                                     # mark in wt8b
commit(wt8, "src.txt", "stale root edit\n")                         # the OLD root moves
rec8 = breaker(rec8, 1_000_000 + STALL + 1)
check("V-AMCR-R8-LATEST-GENERATION-ONLY", mb.generation(gm.load("m-c00000000009")) == 2
      and mb.execution_root(gm.load("m-c00000000009")) == str(wt8b.resolve())
      and bool(gm.load("m-c00000000009").get("owner_hold")), str(receipts("m-c00000000009")))

# --- R9: the bound worktree disappears -> unknown (never zero, never invented progress), then incident -----
main9, wt9, rec9 = incident("r9", "m-c0000000000a")
rec9 = breaker(breaker(rec9, 1_000_000), 1_000_000)
git(main9, "worktree", "remove", "--force", str(wt9))
for k in range(mb.UNKNOWN_INCIDENT_STREAK):
    rec9 = breaker(gm.load("m-c0000000000a"), 1_000_000 + STALL + 1 + k)
a9 = gm.load("m-c0000000000a")
check("V-AMCR-R9-REMOVED-ROOT-IS-UNKNOWN-NOT-ZERO", not a9.get("owner_hold")
      and receipts("m-c0000000000a")[-1] == mb.PROGRESS_UNKNOWN and a9["cost_mark"]["fp"] is not None)
check("V-AMCR-R9-UNKNOWN-STREAK-SURFACES-INCIDENT", len(ledger("m-c0000000000a", "progress_unknown_incident")) == 1
      and str(a9.get("reason", "")).startswith("INCIDENT"), str(a9.get("reason"))[:160])

# --- binding: refusals and the resolver inventory ----------------------------------------------------------
other = repo("unrelated")
try:
    gm.bind_mission("m-c00000000001", str(other))
    refused = False
except gm.MissionError as exc:
    refused = "not a worktree of the repository" in str(exc)
check("V-AMCR-BIND-REFUSES-OTHER-REPO", refused)
try:
    gm.bind_mission("m-c00000000001", str(wt1 / ".planning"))
    refused = False
except gm.MissionError as exc:
    refused = "not its top" in str(exc)
check("V-AMCR-BIND-REFUSES-SUBDIR", refused)
topo = gm.topology("m-c00000000001")
check("V-AMCR-TOPOLOGY-RECEIPT", topo["execution_root"] == str(wt1.resolve()) and topo["binding_generation"] == 1
      and topo["live_branch"] == "gsd/r1" and topo["goal_liveness"] in ("RECOVERING", "OWNER_BOUNDARY"), str(topo)[:200])
src = (HERE / "gsd_mission.py").read_text(encoding="utf-8")
legacy_sites = src.count('rec.get("work_dir") or rec["cwd"]')
check("V-AMCR-ONE-RESOLVER-INVENTORY", legacy_sites <= 1,
      f"{legacy_sites} site(s) still derive the root themselves (allowed: the kill-switch branch only)")

print(f"AMCR_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
sys.exit(0 if fails == 0 else 1)
