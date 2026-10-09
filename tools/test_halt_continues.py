#!/usr/bin/env python
"""V-LIFE-HALT-* gates (WU-1H): a worker that stops without its receipt leaves a fault capsule and ONE
bounded renewal of the same packet (tools/gsd_mission.py halt_continue). Every refusal has a
continuing control. Hermetic: temp state dir, temp git repo, injected spawner and pid probe.
Mutation drill: GSD_MISSION_DRILL_DIR holding a mutated gsd_mission.py (tools/mutation_drill.py).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="halt-continues-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ.pop("CPP_MISSION_RENEW", None)
os.environ.pop("CPP_ROUTE_ADMISSION", None)
os.environ.pop("CPP_HALT_CONTINUE", None)
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402
import mission_spend as ms  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
REAL_HALT_AUTHORITY = gm.halt_authority
gm.halt_authority = lambda rec: 10_000_000
FLOORS = str(Path(__file__).resolve().parent.parent / "vault" / "config" / "route-floors.json")
NOW = 1_800_000_000.0
SLIM = {"envelope": {"target": 200_000, "warn": 250_000, "stop": 300_000, "calls": 10},
        "workers": [{"name": "s0", "profile": "slim-t2", "calls": 3, "packet": 500}]}
GIT = r"C:\Program Files\Git\cmd\git.exe" if Path(r"C:\Program Files\Git\cmd\git.exe").exists() else "git"
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def g(repo, *a):
    subprocess.run([GIT, "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t", *a],
                   check=True, capture_output=True)


def make_repo(name):
    repo = str(Path(TMP) / name)
    Path(repo).mkdir()
    g(repo, "init", "-q")
    (Path(repo) / "a.txt").write_text("a\n", encoding="utf-8")
    g(repo, "add", "a.txt")
    g(repo, "commit", "-q", "-m", "first")
    (Path(repo) / "dirty.txt").write_text("d\n", encoding="utf-8")
    return repo


def spawner(argv, cwd, out_path, err_path):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    return 4242


dead = lambda p: False  # noqa: E731


def successors(mid):
    ms_, _ = gm._scan()
    return [m for m in ms_ if m.get("renewed_from") == mid]


def run(mid, *, state=None, write_result=True, receipt=False, text="PASS V-X\nstopped",
        receipt_text="# receipt\nDONE\n"):
    repo = make_repo(mid)
    gm.create(repo, "/gsd-autonomous --ws wsx", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                  state=gm.RUNNING, epoch=1)
    pkt = Path(TMP) / f"{mid}-WU.md"
    pkt.write_text(f"# WU {mid}\n", encoding="utf-8")
    if receipt:
        (Path(TMP) / f"{mid}-WU-receipt.md").write_text(receipt_text, encoding="utf-8")
    gm.set_envelope(mid, wu_packet=str(pkt), token_estimate=250_000, now=NOW)
    route = Path(TMP) / f"{mid}-route.json"
    route.write_text(json.dumps(SLIM), encoding="utf-8")
    gm.admit_route(mid, str(route), floors_path=FLOORS, now=NOW, measure=lambda r: None)
    cur = gm.load(mid)
    gm.launch_worker(mid, expect_epoch=cur["epoch"], expect_state=cur["state"], reason="t",
                     runner=None, spawner=spawner, now=NOW)
    own = gm.load(mid)["owner"]
    if write_result:
        Path(own["out_path"]).write_text(json.dumps(
            {"type": "result", "is_error": False, "result": text, "session_id": own["session_id"],
             "usage": {"output_tokens": 5}, "permission_denials": []}), encoding="utf-8")
    if state:
        sp = ms.budget_path(own["session_id"])
        sp.with_name(f"session-budget-{own['session_id']}.state.json").write_text(json.dumps(state), encoding="utf-8")
    rows = gm.supervise(now=NOW + 60, sessions=[], pid_alive=dead)
    return gm.load(mid), [r for r in rows if r["mission_id"] == mid], repo


TRIP = {"ids": [], "tokens": 350_000, "calls": 3, "closeout": 1}
OKSTATE = {"ids": [], "tokens": 120_000, "calls": 3, "closeout": 0}


def capsule(mid, epoch=2):
    p = gm.lr.state_dir() / "fault-capsules" / f"{mid}-e{epoch}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main() -> int:
    # 1. tripped worker, no receipt: capsule + exactly one PREPARED successor carrying it
    rec, rows, repo = run("m-hc1", state=TRIP)
    cap, suc = capsule("m-hc1"), successors("m-hc1")
    one = suc[0] if len(suc) == 1 else {}
    check("V-LIFE-HALT-CONTINUES",
          rec["state"] == gm.HALTED and cap is not None and len(suc) == 1 and one.get("state") == gm.PREPARED
          and one["continuity_from"].get("capsule_path") == str(gm.lr.state_dir() / "fault-capsules" / "m-hc1-e2.json")
          and any("dirty.txt" in d for d in cap["partial_receipt"]["SALVAGE"])
          and isinstance(cap["partial_receipt"]["DONE"], list)  # F4: mission-scoped; "first" predates NOW
          and cap["head"] and cap["gate_lines"] == ["PASS V-X"] and "stopped" in cap["result"]
          and cap["spend"]["slim_tokens"] == 5,
          f"{rec['state']} suc={len(suc)} cap={bool(cap)}")
    check("V-LIFE-CAPSULE-IN-PROMPT", suc and str(gm.lr.state_dir() / "fault-capsules") in gm.launch_prompt(one)
          and "FAULT CAPSULE" in gm.launch_prompt(one))
    # 2. singleflight: a second pass over the same halt writes nothing new
    before = (gm.lr.state_dir() / "fault-capsules" / "m-hc1-e2.json").read_bytes()
    row2: dict = {}
    gm.halt_continue(gm.load("m-hc1"), repo, "x", None, row2, NOW + 120)
    check("V-LIFE-HALT-ONCE", len(successors("m-hc1")) == 1
          and (gm.lr.state_dir() / "fault-capsules" / "m-hc1-e2.json").read_bytes() == before
          and "already renewed" in str(row2.get("renewal")), str(row2))
    # 3. no authority: capsule written, no successor, reason recorded
    real = gm.halt_authority
    gm.halt_authority = lambda rec: 100
    rec, rows, _ = run("m-hc3", state=TRIP)
    gm.halt_authority = real
    check("V-LIFE-HALT-NO-AUTHORITY", capsule("m-hc3") is not None and not successors("m-hc3")
          and "not renewed: authority" in str(rows[0].get("renewal")), str(rows))
    # 4. kill switch: old behaviour
    os.environ["CPP_HALT_CONTINUE"] = "off"
    rec, rows, _ = run("m-hc4", state=TRIP)
    os.environ.pop("CPP_HALT_CONTINUE")
    check("V-LIFE-HALT-KILL", rec["state"] == gm.HALTED and capsule("m-hc4") is None and not successors("m-hc4"),
          str(rows))
    # 5. dead pid, empty out.json
    rec, rows, _ = run("m-hc5", write_result=False)
    check("V-LIFE-DEAD-NO-RESULT", rec["state"] == gm.HALTED and capsule("m-hc5") is not None
          and len(successors("m-hc5")) == 1, f"{rec['state']} {rows}")
    # 6. provider success without a receipt is not done
    rec, rows, _ = run("m-hc6", state=OKSTATE, text="done")
    check("V-LIFE-SUCCESS-NO-RECEIPT-NOT-COMPLETED",
          rec["state"] == gm.HALTED and "no receipt" in str(rec.get("reason") or rec)
          and capsule("m-hc6") is not None and len(successors("m-hc6")) == 1, f"{rec['state']} {rows}")
    # F5: a non-renewal always leaves its reason; force the exception path after the capsule decision
    real_wfc = gm.write_fault_capsule
    def boom(*a, **k):
        raise RuntimeError("forced")
    gm.write_fault_capsule = boom
    try:
        rec, rows, _ = run("m-hc5b", state=TRIP)
    finally:
        gm.write_fault_capsule = real_wfc
    check("V-LIFE-NONRENEW-HAS-REASON", not successors("m-hc5b") and rows
          and "not renewed" in str(rows[0].get("renewal")) and "forced" in str(rows[0].get("renewal")), str(rows))
    rec, rows, _ = run("m-hc5c", state=TRIP, receipt=True)
    check("V-LIFE-NONRENEW-RECEIPT-REASON", rows and "receipt present" in str(rows[0].get("renewal")), str(rows))
    # F4: capsule commits are only those since the mission was created
    sc = make_repo("scoped")
    (Path(sc) / "b.txt").write_text("b\n", encoding="utf-8")
    g(sc, "add", "b.txt")
    old_env = dict(os.environ)
    os.environ.update(GIT_COMMITTER_DATE="2020-01-01T00:00:00", GIT_AUTHOR_DATE="2020-01-01T00:00:00")
    try:
        g(sc, "commit", "-q", "-m", "ancient-history")
    finally:
        os.environ.pop("GIT_COMMITTER_DATE"); os.environ.pop("GIT_AUTHOR_DATE")
    (Path(sc) / "c.txt").write_text("c\n", encoding="utf-8")
    g(sc, "add", "c.txt")
    g(sc, "commit", "-q", "-m", "mission-work")
    gm.write_fault_capsule({"mission_id": "m-sc", "epoch": 3, "created_at": 1_700_000_000.0}, sc, "x", None)
    csc = capsule("m-sc", 3) or {}
    check("V-LIFE-CAPSULE-MISSION-SCOPED",
          any("mission-work" in c for c in csc.get("commits") or [])
          and not any("ancient-history" in c or "first" in c for c in csc.get("commits") or []),
          str(csc.get("commits")))
    # 7. controls: a receipt present means nothing to recover
    rec, rows, _ = run("m-hc7", state=TRIP, receipt=True)
    check("V-LIFE-HALT-RECEIPT-PRESENT", rec["state"] == gm.HALTED and capsule("m-hc7") is None
          and not successors("m-hc7"), str(rows))
    rec, rows, _ = run("m-hc8", state=OKSTATE, receipt=True, text="done")
    check("V-LIFE-SUCCESS-WITH-RECEIPT-COMPLETES", rec["state"] == gm.COMPLETED and capsule("m-hc8") is None
          and not successors("m-hc8"), str(rows))
    # 7b. a lower-case checkpoint stub is not a receipt (WU-ADV-receipt.md: "IN PROGRESS (checkpoint stub)")
    rec, rows, _ = run("m-hc9", state=TRIP, receipt=True, receipt_text="# WU-ADV receipt\n\ncheckpoint stub.\n")
    check("V-LIFE-HALT-STUB-LOWERCASE", capsule("m-hc9") is not None and len(successors("m-hc9")) == 1, str(rows))
    rec, rows, _ = run("m-hc10", state=TRIP, receipt=True, receipt_text="# WU receipt\n\nStatus: IN PROGRESS\n")
    check("V-LIFE-HALT-STATUS-IN-PROGRESS", capsule("m-hc10") is not None and len(successors("m-hc10")) == 1,
          str(rows))
    # 7c. the renewed successor is admitted, so the normal launch path can start it (renew never carries admission)
    one = successors("m-hc1")[0]
    check("V-LIFE-HALT-READMITTED", (one.get("admission") or {}).get("verdict") == "ADMISSIBLE"
          and gm.admission_refusal(one) is None and not one.get("owner_hold"),
          f"adm={(one.get('admission') or {}).get('verdict')} hold={one.get('owner_hold')}")
    # 7d. a sweep-armed record has no goal and no workstream: the cwd binding names the paying goal
    real = gm.halt_authority
    gm.halt_authority = real.__wrapped__ if hasattr(real, "__wrapped__") else REAL_HALT_AUTHORITY
    bound = make_repo("bound")
    ms.goal_declare("g-halt-test", 900_000, "test", roots=[bound])
    rb = {"mission_id": "x", "cwd": bound, "goal": None}
    ru = {"mission_id": "y", "cwd": make_repo("unbound"), "goal": None}
    check("V-LIFE-HALT-GOAL-BY-CWD", gm.spend_goal(rb) == "g-halt-test" and gm.halt_authority(rb) == 900_000
          and gm.spend_goal(ru) is None and gm.halt_authority(ru) is None,
          f"{gm.spend_goal(rb)} {gm.halt_authority(rb)} | {gm.spend_goal(ru)}")
    gm.halt_authority = real
    # 8. atomic arm
    pkt = Path(TMP) / "ac-WU.md"
    pkt.write_text("# WU\n", encoding="utf-8")
    route = Path(TMP) / "ac-route.json"
    route.write_text(json.dumps(SLIM), encoding="utf-8")
    bad = gm.arm_chain(make_repo("ac-bad"), "/gsd-autonomous --ws wsbad", wu_packet=str(pkt),
                       token_estimate=250_000, route=str(Path(TMP) / "nope.json"), floors_path=FLOORS)
    bm = gm.load(bad["mission_id"])
    good = gm.arm_chain(make_repo("ac-ok"), "/gsd-autonomous --ws wsok", wu_packet=str(pkt),
                        token_estimate=250_000, route=str(route), floors_path=FLOORS)
    gmm = gm.load(good["mission_id"])
    check("V-LIFE-ARMCHAIN-ATOMIC", bad["ok"] is False and bad["held"] and bm.get("owner_hold")
          and not bm.get("owner") and bm["state"] == gm.PREPARED
          and good["ok"] is True and not gmm.get("owner_hold") and not gmm.get("owner")
          and gmm["state"] == gm.PREPARED and gmm["admission"]["verdict"] == "ADMISSIBLE"
          and gmm["wu_packet"]["path"] == str(pkt), f"{bad.get('why')} | {gmm['state']}")
    # 9. S2: capsule survives PATH loss; unresolved git says UNRESOLVED, never ""
    pl = make_repo("pathloss")
    saved = os.environ.get("PATH")
    os.environ["PATH"] = ""
    try:
        gm.write_fault_capsule({"mission_id": "m-pl", "epoch": 7}, pl, "PASS V-X", None)
    finally:
        os.environ["PATH"] = saved
    cp = capsule("m-pl", 7) or {}
    check("V-LIFE-CAPSULE-PATH-LOSS",
          len(str(cp.get("head", ""))) == 40 and any("first" in c for c in cp.get("commits") or [])
          and any("dirty.txt" in d for d in cp.get("dirty") or []), f"{cp.get('head')} {cp.get('git')}")
    real_resolve = gm.resolve_exe
    gm.resolve_exe = lambda name: None
    try:
        gm.write_fault_capsule({"mission_id": "m-un", "epoch": 7}, pl, "PASS V-X", None)
    finally:
        gm.resolve_exe = real_resolve
    cu = capsule("m-un", 7) or {}
    check("V-LIFE-CAPSULE-UNRESOLVED",
          cu.get("git") == "UNRESOLVED" and cu.get("head") == "UNRESOLVED" and cu.get("commits") == "UNRESOLVED"
          and cu.get("dirty") == "UNRESOLVED", f"{cu.get('git')} {cu.get('head')!r}")
    print(f"HALT_CONTINUES_PASS={passes} FAIL={fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
