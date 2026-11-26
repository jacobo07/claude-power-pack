#!/usr/bin/env python
"""V-DUPARM-* gates for the duplicate-arm guard in tools/gsd_mission.py arm() (mission-capital W1).

Measured 2026-11-23 12:28Z (GEX44): a second mission was armed on anti-slop-web while its runtime successor
m-bc8814955e63 was RUNNING; a pgrep check missed the worker. The record is the truth. Hermetic: state goes to a temp
dir before import; arm runs with launch=False and preflighted=True (no worker, no scaffold). Every refusal has a
paired allow control.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="mission-duparm-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_RESOURCE_ADMISSION"] = "off"
os.environ["CPP_MISSION_ACCOUNT_ADMISSION"] = "off"
os.environ["CPP_MISSION_DUP_ARM_GUARD"] = "on"   # the enforcing pole; the shadow default is V-DUPARM-SHADOW-DEFAULT
os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402

passes = fails = 0
NOW = 1_800_000_000.0
GIT = gm.resolve_exe("git") or "git"


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def new_repo(name):
    repo = Path(TMP) / name
    repo.mkdir()
    for args in (("init", "-q"), ("config", "user.email", "t@t"), ("config", "user.name", "t")):
        subprocess.run([GIT, "-C", str(repo), *args], check=True, capture_output=True)
    (repo / "README.md").write_text("x", encoding="utf-8")
    subprocess.run([GIT, "-C", str(repo), "add", "-A"], check=True, capture_output=True)
    subprocess.run([GIT, "-C", str(repo), "commit", "-q", "-m", "init"], check=True, capture_output=True)
    return str(repo)


def arm(mod, repo, **kw):
    """(mission_id, None) or (None, refusal text)."""
    try:
        rec = mod.arm(repo, "/gsd-autonomous", launch=False, preflighted=True, **kw)
        return rec["mission"]["mission_id"], None
    except gm.MissionError as exc:
        return None, str(exc)
    except Exception as exc:  # noqa: BLE001 -- the old module raises its own MissionError class
        if type(exc).__name__ == "MissionError":
            return None, str(exc)
        raise


def old_module():
    """gsd_mission.py exactly as at 8c452fac: the revert control."""
    src = subprocess.run([GIT, "-C", str(Path(__file__).resolve().parent), "show", "8c452fac:tools/gsd_mission.py"],
                         capture_output=True, text=True, encoding="utf-8", check=True).stdout
    p = Path(TMP) / "oldmod" / "gsd_mission_8c452fac.py"
    p.parent.mkdir(exist_ok=True)
    p.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("gsd_mission_8c452fac", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def close(mid):
    rec = gm.load(mid)
    gm.transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], event="test_closed", state=gm.COMPLETED)


def main() -> int:
    # V-DUPARM-REFUSE: a live, unheld mission on the same repo refuses the second arm, naming it
    repo = new_repo("dup")
    first, why = arm(gm, repo)
    second, why2 = arm(gm, repo)
    check("V-DUPARM-REFUSE", first and second is None and why2 and first in why2 and "duplicate arm" in why2,
          f"first={first} refusal={why2}")
    # the same repo through a linked worktree (same git common dir) is the same repository
    wt = str(Path(TMP) / "dup-wt")
    subprocess.run([GIT, "-C", repo, "worktree", "add", "-q", "-b", "side", wt], check=True, capture_output=True)
    third, why3 = arm(gm, wt)
    check("V-DUPARM-REFUSE-WORKTREE", third is None and why3 and first in why3, f"refusal={why3}")
    # revert control: the 8c452fac arm lets the duplicate through
    old = old_module()
    dup_old, why_old = arm(old, repo)
    check("V-DUPARM-REFUSE-FAILS-AT-8c452fac", dup_old and why_old is None, f"8c452fac armed {dup_old}")
    if dup_old:
        close(dup_old)

    # V-DUPARM-PARALLEL-UNIT-ALLOWS: declared concurrency
    par, whyp = arm(gm, repo, parallel_unit="unit-b")
    check("V-DUPARM-PARALLEL-UNIT-ALLOWS", par and whyp is None, f"armed={par} why={whyp}")
    if par:
        close(par)

    # V-DUPARM-HELD-ALLOWS: the existing mission is under an Owner hold -> not a duplicate writer
    gm.set_owner_hold(first, "owner stop (test)", now=NOW, kind="owner_stop")
    held, whyh = arm(gm, repo)
    check("V-DUPARM-HELD-ALLOWS", held and whyh is None, f"armed={held} why={whyh}")
    if held:
        close(held)

    # V-DUPARM-TERMINAL-ALLOWS: a terminal record is history, not a live writer
    repo2 = new_repo("term")
    t1, _ = arm(gm, repo2)
    close(t1)
    t2, whyt = arm(gm, repo2)
    check("V-DUPARM-TERMINAL-ALLOWS", t1 and t2 and whyt is None, f"armed={t2} why={whyt}")

    # V-DUPARM-KILL-SWITCH: CPP_MISSION_DUP_ARM_GUARD=off restores the old behaviour; control: on again refuses
    os.environ["CPP_MISSION_DUP_ARM_GUARD"] = "off"
    try:
        k1, whyk = arm(gm, repo2)
    finally:
        os.environ["CPP_MISSION_DUP_ARM_GUARD"] = "on"
    if k1:
        close(k1)
    k2, whyk2 = arm(gm, repo2)
    check("V-DUPARM-KILL-SWITCH", k1 and whyk is None and k2 is None and t2 in (whyk2 or ""),
          f"off armed={k1}; on refusal={whyk2}")

    # V-DUPARM-SHADOW-DEFAULT: unset = shadow. The duplicate arms (other arm flows rely on it until classified) and
    # a duplicate_arm_shadow row names the live mission; control: the same arm under =on was refused just above.
    os.environ.pop("CPP_MISSION_DUP_ARM_GUARD")
    try:
        s1, whys = arm(gm, repo2)
    finally:
        os.environ["CPP_MISSION_DUP_ARM_GUARD"] = "on"
    ledger = Path(gm.lr.ledger_path()).read_text(encoding="utf-8", errors="replace")
    shadow = [ln for ln in ledger.splitlines() if '"duplicate_arm_shadow"' in ln and t2 in ln]
    check("V-DUPARM-SHADOW-DEFAULT", s1 and whys is None and len(shadow) >= 1,
          f"armed={s1} why={whys} shadow_rows={len(shadow)}")
    if s1:
        close(s1)

    print(f"DUPARM_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
