#!/usr/bin/env python
"""V-LIFE-APPROVAL-ONCE, V-LIFE-ADMIT-GOAL-DEFER, V-LIFE-ADMIT-NO-GOAL-UNCHANGED (WU-ADV2a). Hermetic.
Mutation drill: GSD_MISSION_DRILL_DIR (gsd_mission.py) / ledger mutated copy via PYTHONPATH repo root."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="advance-test-")
for k, v in (("GSD_LONG_RUN_STATE_DIR", TMP), ("GSD_LONG_RUN_SESSIONS_DIR", str(Path(TMP) / "sessions")),
             ("GSD_AUTORUN_MARKER_DIR", TMP), ("CPP_CLAUDE_JOBS_DIR", str(Path(TMP) / "jobs")),
             ("GSD_LONG_RUN_PROJECTS_DIR", str(Path(TMP) / "projects"))):
    os.environ[k] = v
os.environ.pop("CPP_ROUTE_ADMISSION", None)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
if os.environ.get("GSD_LEDGER_DRILL_ROOT"):
    sys.path.insert(0, os.environ["GSD_LEDGER_DRILL_ROOT"])
import gsd_mission as gm  # noqa: E402
from modules.provider_routing.ledger import GoalLedger  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
FLOORS = str(HERE.parent / "vault" / "config" / "route-floors.json")
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


def caps(root):
    return [r for r in GoalLedger(root, "g-t")._read() if r.get("op") == "cap"]


def admit(mid, goal_rem):
    repo = str(Path(TMP) / mid)
    Path(repo).mkdir()
    g = lambda *a: subprocess.run([GIT, "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t", *a],
                                  check=True, capture_output=True)
    g("init", "-q")
    (Path(repo) / "a.txt").write_text("a\n", encoding="utf-8")
    g("add", "a.txt")
    g("commit", "-q", "-m", "first")
    gm.create(repo, "/gsd-autonomous --ws wsx", mission_id=mid, now=NOW)
    pkt = Path(TMP) / f"{mid}-WU.md"
    pkt.write_text(f"# WU {mid}\n", encoding="utf-8")
    gm.set_envelope(mid, wu_packet=str(pkt), token_estimate=250_000, now=NOW)
    route = Path(TMP) / f"{mid}-route.json"
    route.write_text(json.dumps(SLIM), encoding="utf-8")
    gm.halt_authority = lambda rec: goal_rem
    return gm.admit_route(mid, str(route), floors_path=FLOORS, now=NOW, measure=lambda r: None)["admission"]


def advance_checks() -> None:
    """WU-ADV2b: advance_pass with a temp repo, injected headroom and arm_fn."""
    repo = Path(TMP) / "advrepo"
    pd = repo / "pk"
    pd.mkdir(parents=True)
    route = json.dumps({"envelope": {"target": 100_000}})
    for u in ("U1", "U2", "U3"):
        (pd / f"{u}.md").write_text(f"# {u}\n", encoding="utf-8")
        (pd / f"route-{u}.json").write_text(route, encoding="utf-8")
    (pd / "U1-receipt.md").write_text("# U1 receipt -- Status: DONE\n", encoding="utf-8")
    plan = repo / "plan.md"
    plan.write_text("---\nstatus: APPROVED\nunits: [U1, U2]\npacket_dir: pk\n---\nbody\n", encoding="utf-8")
    adir = Path(TMP) / "approvals"
    adir.mkdir(exist_ok=True)

    def rec(aid="ap-adv", **kw):
        (adir / f"{aid}.json").write_text(json.dumps({"approval_id": aid, "plan_path": str(plan), "goal": "g-adv",
                                                      "repo": str(repo), **kw}), encoding="utf-8")

    armed = []
    arm = lambda cwd, cmd, **k: (armed.append(Path(k["wu_packet"]).stem), {"ok": True, "mission_id": "m-x"})[1]
    rec()
    rows = gm.advance_pass(arm_fn=arm, headroom=lambda g: 1_000_000)
    check("V-LIFE-ADV-ARMS-NEXT", armed == ["U2"] and rows[0]["status"] == "ARMED", f"{armed} {rows}")
    gm.advance_pass(arm_fn=arm, headroom=lambda g: 1_000_000)
    check("V-LIFE-ADV-ONCE", armed == ["U2"], f"{armed}")
    # not listed: U3 has packet+route but is not in units; with U2 receipt done the plan is complete
    (pd / "U2-receipt.md").write_text("Status: DONE\n", encoding="utf-8")
    gm.advance_pass(arm_fn=arm, headroom=lambda g: 1_000_000)
    try:
        direct = gm.advance_unit(json.loads((adir / "ap-adv.json").read_text(encoding="utf-8")),
                                 gm.parse_plan(plan), "U3", repo, arm_fn=arm, headroom=lambda g: 1_000_000)
    except Exception as exc:  # noqa: BLE001 -- a raise is not a refusal; the gate must read it as a FAIL
        direct = {"status": f"RAISED {type(exc).__name__}"}
    check("V-LIFE-ADV-NOT-LISTED", "U3" not in armed and armed == ["U2"] and direct["status"] == "NOT_LISTED",
          f"{armed} {direct['status']}")
    # no authority: new plan, headroom too small
    plan2 = repo / "plan2.md"
    plan2.write_text("---\nstatus: APPROVED\nunits: [U1, U3]\npacket_dir: pk\n---\n", encoding="utf-8")
    (adir / "ap-adv.json").unlink()
    (adir / "ap-2.json").write_text(json.dumps({"approval_id": "ap-2", "plan_path": str(plan2), "goal": "g-adv",
                                                "repo": str(repo)}), encoding="utf-8")
    rows = gm.advance_pass(arm_fn=arm, headroom=lambda g: 10)
    st = (repo / "plan2.md.status").read_text(encoding="utf-8")
    check("V-LIFE-ADV-NO-AUTHORITY", "U3" not in armed and rows[0]["status"] == "WAITING_FOR_AUTHORITY"
          and st.startswith("WAITING_FOR_AUTHORITY"), f"{rows[0]['status']}")
    # stub receipt: U1 receipt is a stub, so U2 is never armed as successor
    (pd / "U1-receipt.md").write_text("Status: DONE (STUB)\n", encoding="utf-8")
    plan3 = repo / "plan3.md"
    plan3.write_text("---\nstatus: APPROVED\nunits: [U1, U2]\npacket_dir: pk\n---\n", encoding="utf-8")
    (adir / "ap-2.json").unlink()
    (adir / "ap-3.json").write_text(json.dumps({"approval_id": "ap-3", "plan_path": str(plan3), "goal": "g-adv3",
                                                "repo": str(repo)}), encoding="utf-8")
    (pd / "U2-receipt.md").unlink()
    before = list(armed)
    gm.advance_pass(arm_fn=arm, headroom=lambda g: 1_000_000)
    check("V-LIFE-ADV-STUB-RECEIPT-NO-ARM", armed == before, f"{armed}")
    # a DONE receipt may describe stubs and PARTIAL states in prose (WU-S5d's does); a status line decides
    prose = pd / "P-receipt.md"
    prose.write_text("# P receipt\n\nStatus: DONE\n- D2: a PARTIAL / IN PROGRESS / stub status now reads as no "
                     "receipt.\n", encoding="utf-8")
    title = pd / "T-receipt.md"
    title.write_text("# T receipt -- Status: PARTIAL\n", encoding="utf-8")
    check("V-LIFE-ADV-RECEIPT-PROSE", gm.receipt_complete(prose) and not gm.receipt_complete(title)
          and gm._receipt_present({"wu_packet": {"path": str(pd / "P.md")}}), "prose DONE / title PARTIAL")
    # an arm that raises armed nothing: the singleflight key is released and the next pass retries
    (adir / "ap-3.json").unlink()
    (pd / "U1-receipt.md").write_text("Status: DONE\n", encoding="utf-8")
    plan4 = repo / "plan4.md"
    plan4.write_text("---\nstatus: APPROVED\nunits: [U1, U3]\npacket_dir: pk\n---\n", encoding="utf-8")
    (adir / "ap-4.json").write_text(json.dumps({"approval_id": "ap-4", "plan_path": str(plan4), "goal": "g-adv",
                                                "repo": str(repo)}), encoding="utf-8")

    def boom(*a, **k):
        raise TypeError("unexpected keyword argument")
    first = gm.advance_pass(arm_fn=boom, headroom=lambda g: 1_000_000)
    again = gm.advance_pass(arm_fn=arm, headroom=lambda g: 1_000_000)
    check("V-LIFE-ADV-ARM-RAISES-RETRIES", first[0]["status"] == "ARM_FAILED" and again[0]["status"] == "ARMED"
          and armed[-1] == "U3", f"{first[0]['status']} -> {again[0]['status']}")
    (adir / "ap-4.json").unlink()


def advance_real_arm() -> None:
    """The real arm_chain, not an injected one: the kwargs advance_unit passes must bind (state dir is TMP)."""
    repo = Path(TMP) / "advreal"
    repo.mkdir()
    g = lambda *a: subprocess.run([GIT, "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                                  check=True, capture_output=True)
    g("init", "-q")
    pd = repo / "pk"
    pd.mkdir()
    (pd / "R1-receipt.md").write_text("Status: DONE\n", encoding="utf-8")
    (pd / "R2.md").write_text("# R2\n", encoding="utf-8")
    (pd / "route-R2.json").write_text(json.dumps(SLIM), encoding="utf-8")
    plan = repo / "plan.md"
    plan.write_text("---\nstatus: APPROVED\nunits: [R1, R2]\npacket_dir: pk\n---\n", encoding="utf-8")
    g("add", "-A")
    g("commit", "-q", "-m", "first")
    rec = {"approval_id": "ap-real", "plan_path": str(plan), "goal": "g-real", "repo": str(repo)}
    out = gm.advance_unit(rec, gm.parse_plan(plan), "R2", repo, headroom=lambda g_: 1_000_000)
    m = gm.load(out.get("mission_id") or "") if out.get("mission_id") else None
    check("V-LIFE-ADV-REAL-ARM", out["status"] == "ARMED" and m is not None and m["state"] == gm.PREPARED
          and Path(m["wu_packet"]["path"]).name == "R2.md", f"{out}")


def main() -> int:
    root = Path(TMP) / "goal"
    led = GoalLedger(root, "g-t")
    led.declare_cap(1_000_000, "init")
    a1 = led.declare_cap(3_000_000, "owner", approval_id="ap-1")
    a2 = led.declare_cap(3_000_000, "owner", approval_id="ap-1")
    n = len(caps(root))
    check("V-LIFE-APPROVAL-ONCE", a1.get("applied", True) and a2.get("applied") is False
          and "already consumed" in a2.get("reason", "") and n == 2 and "approval:ap-1" in str(caps(root)[-1]["source"]),
          f"caps={n} {a2.get('reason')}")
    a3 = led.declare_cap(4_000_000, "owner", approval_id="ap-2")
    check("V-LIFE-APPROVAL-ONCE-CONTROL-DIFFERENT-ID", a3.get("ok") and len(caps(root)) == 3
          and a3["cap"] == 4_000_000, f"caps={len(caps(root))} cap={a3.get('cap')}")
    low = admit("m-low", 1_000)
    check("V-LIFE-ADMIT-GOAL-DEFER", low["verdict"] == "DEFER" and low["remaining"] == 1_000,
          f"{low['verdict']} rem={low['remaining']}")
    ok = admit("m-nogoal", None)
    check("V-LIFE-ADMIT-NO-GOAL-UNCHANGED", ok["verdict"] == "ADMISSIBLE" and ok["remaining"] is None,
          f"{ok['verdict']} rem={ok['remaining']}")
    advance_checks()
    advance_real_arm()
    print(f"ADVANCE_PASS={passes} FAIL={fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
