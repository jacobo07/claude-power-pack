#!/usr/bin/env python
"""V-AUTORES-* gates for spec vault/specs/mission-autoresolve.md: the supervisor resolves, from durable state,
the four stops that parked m-6043c9b8e6c4 on 2026-11-12 (about 9 h lost in one day). Every gate has a paired
control that must still refuse/hold. Hermetic: state dir, jobs dir and git trees are temp directories."""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="autores-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
for k in ("CPP_ROUTE_ADMISSION", "CPP_CCR_ADMISSION", "CPP_CE_GOAL"):
    os.environ.pop(k, None)
os.environ["CPP_RESOURCE_ADMISSION"] = "off"
os.environ["CPP_MISSION_ACCOUNT_ADMISSION"] = "off"  # account quota: covered by test_mission_account_admission
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gsd_mission as gm  # noqa: E402
import mission_recovery as mr  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
FLOORS = str(HERE.parent / "vault" / "config" / "route-floors.json")
NOW = 1_800_000_000.0
ROUTE = {"envelope": {"target": 6_153_846, "warn": 6_956_521, "stop": 8_000_000, "calls": 45},
         "workers": [{"name": "amr-successor", "profile": "top-level-worker", "calls": 45, "packet": 3000}]}
GIT = gm.resolve_exe("git") or "git"
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}"[:300])


def write(name, obj):
    p = Path(TMP) / name
    p.write_text(obj if isinstance(obj, str) else json.dumps(obj), encoding="utf-8")
    return str(p)


def git(wd, *a):
    return subprocess.run([GIT, "-C", str(wd), "-c", "user.email=t@t", "-c", "user.name=t", *a],
                          capture_output=True, text=True, check=True).stdout.strip()


# ---------------------------------------------------------------- R1: admission bounded by the Owner authority
def admitted(mid, src):
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.RUNNING,
                  epoch=1, token_estimate=25_229_538, token_estimate_src=src, authority_tokens=320_000_000)
    gm.set_envelope(mid, wu_packet=write(f"{mid}-WU.md", f"# WU {mid}\n"), now=NOW)
    # set_envelope may clear the estimate source; re-pin the incident's fields after it
    cur = gm.load(mid)
    gm.transition(mid, expect_epoch=cur["epoch"], expect_state=cur["state"], event="t_pin", now=NOW,
                  token_estimate=25_229_538, token_estimate_src=src)
    gm.admit_route(mid, write(f"{mid}-route.json", ROUTE), floors_path=FLOORS, now=NOW,
                   measure=lambda r: 49_698_364)
    return gm.load(mid)["admission"]


def r1():
    a = admitted("m-ar-amr", "amr")
    check("V-AUTORES-R1-AMR-ESTIMATE-YIELDS-TO-AUTHORITY", a["verdict"] == "ADMISSIBLE" and a["remaining"] > 200_000_000,
          f"verdict={a['verdict']} remaining={a['remaining']:,}")
    a = admitted("m-ar-auto", "auto")
    check("V-AUTORES-R1-AUTO-ESTIMATE-YIELDS-TO-AUTHORITY", a["verdict"] == "ADMISSIBLE", f"verdict={a['verdict']}")
    a = admitted("m-ar-oper", None)
    check("V-AUTORES-R1-CONTROL-OPERATOR-ESTIMATE-KEEPS-RATIO",
          a["verdict"] == "DEFER" and a["remaining"] == 2 * 25_229_538 - 49_698_364,
          f"verdict={a['verdict']} remaining={a['remaining']:,}")


# ---------------------------------------------------------------- R2: human_needed phases are not the next unit
def planning_tree(name, verification: dict):
    wd = Path(TMP) / name
    base = wd / ".planning"
    (base / "phases").mkdir(parents=True)
    (base / "STATE.md").write_text("---\nstatus: executing\n---\n# State\n", encoding="utf-8")
    (base / "ROADMAP.md").write_text("### Phase 1: Foundation\n  1. a\n\n### Phase 2: Next\n  1. b\n", encoding="utf-8")
    for num, slug in ((1, "foundation"), (2, "next")):
        d = base / "phases" / f"{num:02d}-{slug}"
        d.mkdir()
        if num in verification:
            (d / f"{num:02d}-VERIFICATION.md").write_text(f"---\nstatus: {verification[num]}\n---\n", encoding="utf-8")
    return str(wd)


def manager(wd, workstream=None):
    return ({"roadmap_exists": True, "state_exists": True,
             "phases": [{"number": "1", "name": "Foundation", "phase_complete": False},
                        {"number": "2", "name": "Next", "phase_complete": False}]}, "ok")


def r2():
    u = mr.gsd_unit(planning_tree("t-hn", {1: "human_needed"}), None, manager=manager)
    check("V-AUTORES-R2-HUMAN-NEEDED-SKIPPED", u.get("phase") == 2 and u.get("unit") == "root/phase-02",
          f"phase={u.get('phase')} unit={u.get('unit')}")
    u = mr.gsd_unit(planning_tree("t-pass", {1: "gaps_found"}), None, manager=manager)
    check("V-AUTORES-R2-CONTROL-OPEN-PHASE-STAYS-FIRST", u.get("phase") == 1, f"phase={u.get('phase')}")
    u = mr.gsd_unit(planning_tree("t-all", {1: "human_needed", 2: "human_needed"}), None, manager=manager)
    check("V-AUTORES-R2-CONTROL-ALL-HUMAN-FALLS-BACK-TO-FIRST", u.get("phase") == 1, f"phase={u.get('phase')}")


# ---------------------------------------------------------------- R3: planning-only divergence is not a hold
def diverged_pair(name, wt_file):
    main = Path(TMP) / name
    main.mkdir()
    git(main, "init", "-q", "-b", "main")
    (main / ".planning").mkdir()
    (main / ".planning" / "STATE.md").write_text("s0\n", encoding="utf-8")
    (main / "app.py").write_text("v0\n", encoding="utf-8")
    git(main, "add", "-A")
    git(main, "commit", "-qm", "seed")
    wt = Path(TMP) / f"{name}-wt"
    git(main, "worktree", "add", "-q", "-b", "side", str(wt))
    p = wt / wt_file
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("note\n", encoding="utf-8")
    git(wt, "add", "-A")
    git(wt, "commit", "-qm", "side change")
    (main / "app.py").write_text("v1\n", encoding="utf-8")
    git(main, "commit", "-qam", "main moves on")
    return str(main), str(wt)


def r3():
    main, wt = diverged_pair("t-plan", ".planning/STATE.md")
    a = gm.align_cwd(main, wt)
    check("V-AUTORES-R3-PLANNING-ONLY-DIVERGENCE-NOT-BLOCKING",
          a["status"] == "diverged_planning_only" and a["status"] not in gm.CWD_ALIGN_BLOCKING and a.get("stranded"),
          f"{a['status']}: {a['detail'][:120]}")
    main, wt = diverged_pair("t-code", "lib/code.py")
    a = gm.align_cwd(main, wt)
    check("V-AUTORES-R3-CONTROL-CODE-DIVERGENCE-STILL-HOLDS", a["status"] == "diverged", a["status"])


# ---------------------------------------------------------------- R4: the claude the host runs under
def r4():
    old_env, old_home = os.environ.get("CPP_CLAUDE_EXE"), os.environ.get("HOME")
    try:
        os.environ["CPP_CLAUDE_EXE"] = "/opt/x/claude"
        check("V-AUTORES-R4-ENV-WINS", gm.claude_exe() == "/opt/x/claude", gm.claude_exe())
        os.environ.pop("CPP_CLAUDE_EXE")
        home = Path(TMP) / "home"
        os.environ["HOME"] = str(home)
        check("V-AUTORES-R4-CONTROL-NO-LOCAL-INSTALL-PATH-CLAUDE", gm.claude_exe() == "claude", gm.claude_exe())
        if os.name != "nt":
            exe = home / ".local" / "bin" / "claude"
            exe.parent.mkdir(parents=True)
            exe.write_text("#!/bin/sh\n", encoding="utf-8")
            exe.chmod(exe.stat().st_mode | stat.S_IXUSR)
            check("V-AUTORES-R4-USER-LOCAL-INSTALL-BEFORE-PATH", gm.claude_exe() == str(exe), gm.claude_exe())
    finally:
        for k, v in (("CPP_CLAUDE_EXE", old_env), ("HOME", old_home)):
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def main() -> int:
    for fn in (r1, r2, r3, r4):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 -- a crashed gate is a FAIL, named
            check(f"V-AUTORES-{fn.__name__.upper()}-CRASHED", False, f"{type(exc).__name__}: {exc}")
    print(f"\n{passes} passed, {fails} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
