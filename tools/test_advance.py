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
    print(f"ADVANCE_PASS={passes} FAIL={fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
