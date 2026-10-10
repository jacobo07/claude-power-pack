#!/usr/bin/env python
"""A5-U7: stall trip K (guard + mission_spend default, env CPP_NOPROGRESS_K) and singleflight canary.
Hermetic; no model. Each rule has a control and one mutant that must be caught. Prints A5_U7_PASS=n/m."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

TMP = tempfile.mkdtemp(prefix="a5-u7-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_RESOURCE_ADMISSION"] = "off"
os.environ.pop("CPP_NOPROGRESS_K", None)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gsd_mission as gm  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
GUARD = HERE.parent / "hooks" / "session_budget_guard.js"
NODE = shutil.which("node") or "node"
NOW = 1_800_000_000.0
res: list[bool] = []


def check(name, cond, ev=""):
    res.append(bool(cond))
    print(f"{'PASS' if cond else 'FAIL'} {name} {ev}")


JS = r"""
const g = require(process.argv[1]);
const gap = Number(process.argv[2]);
const out = g.judge({stop: 1e12, target: 1e12, warn: 1e12, closeout_reserve_calls: 0, %s},
  {tokens: 1, context: 1, calls: gap, progress_at: 0});
process.stdout.write(JSON.stringify({deny: !!(out && out.hookSpecificOutput && out.hookSpecificOutput.permissionDecision === 'deny')}));
"""


def guard_denies(gap, env_k=None, path=GUARD, budget_k=None):
    env = {k: v for k, v in os.environ.items() if k != "CPP_NOPROGRESS_K"}
    if env_k is not None:
        env["CPP_NOPROGRESS_K"] = str(env_k)
    extra = f"noprogress_calls: {budget_k}" if budget_k else "x: 0"
    r = subprocess.run([NODE, "-e", JS % extra, str(path), str(gap)], env=env, capture_output=True,
                       text=True, timeout=20)
    return json.loads(r.stdout)["deny"]


def suite_guard(path, tag):
    return [guard_denies(14, path=path), guard_denies(15, path=path), guard_denies(20, env_k=30, path=path),
            guard_denies(31, env_k=30, path=path), guard_denies(5, budget_k=3, path=path)]


def main() -> int:
    # --- step 2: guard default 14, env override, per-session outranks
    exp = [False, True, False, True, True]
    got = suite_guard(GUARD, "real")
    check("U7-GUARD-K14", got == exp, f"gap14 allow, gap15 deny, env30 allow@20 deny@31, budget k=3 deny@5: {got}")
    d = Path(TMP) / "mut"
    d.mkdir()
    src = GUARD.read_text(encoding="utf-8").replace("require('./lib/goal_binding')",
                                                    f"require('{GUARD.parent.as_posix()}/lib/goal_binding')")
    m1 = d / "m1.js"
    m1.write_text(src.replace("const DEFAULT_NOPROGRESS = 14;", "const DEFAULT_NOPROGRESS = 25;"), encoding="utf-8")
    check("U7-GUARD-MUT-DEFAULT", suite_guard(m1, "m1") != exp, "default 25 is caught")
    m2 = d / "m2.js"
    m2.write_text(src.replace("process.env.CPP_NOPROGRESS_K", "process.env.CPP_NOPROGRESS_X"), encoding="utf-8")
    check("U7-GUARD-MUT-ENV", suite_guard(m2, "m2") != exp, "env ignored is caught")
    import mission_spend as ms
    check("U7-SPEND-DEFAULT", ms.DEFAULT_NOPROGRESS_CALLS == 14 and ms._noprogress_default() == 14, str(ms.DEFAULT_NOPROGRESS_CALLS))
    os.environ["CPP_NOPROGRESS_K"] = "30"
    check("U7-SPEND-ENV", ms._noprogress_default() == 30, "env 30 -> 30")
    os.environ["CPP_NOPROGRESS_K"] = "zero"
    check("U7-SPEND-ENV-BAD", ms._noprogress_default() == 14, "garbage env -> 14")
    os.environ.pop("CPP_NOPROGRESS_K")

    # --- STALL.md rule (step 1) pinned to the guard default
    stall = (HERE.parent / "vault/programs/cognitive-economy/a5/STALL.md").read_text(encoding="utf-8")
    check("U7-STALL-K", "Measured K = 14" in stall, "STALL.md states K=14")

    # --- step 3: singleflight canary
    ws = "--ws u7canary"
    gm.create(TMP, f"/gsd-autonomous {ws}", mission_id="m-first", now=NOW)
    key = gm.goal_key(TMP, "u7canary")
    first = gm.arm.__wrapped__ if hasattr(gm.arm, "__wrapped__") else None  # noqa: F841
    a = gm.arm(TMP, f"/gsd-autonomous {ws}", launch=False, mission_id="m-first2", now=NOW) if False else None  # noqa: F841
    gm.transition("m-first", expect_epoch=0, expect_state=gm.PREPARED, event="t_goal", now=NOW,
                  goal={"repo": key[0], "workstream": "u7canary", "unit": None}, workstream="u7canary")
    launches: list = []

    def runner(argv, cwd):
        launches.append(argv)
        return SimpleNamespace(stdout=f"backgrounded · c0ffee{len(launches):02x} · {argv[3]}", stderr="", returncode=0)

    def second_arm():
        try:
            gm.arm(TMP, f"/gsd-autonomous {ws}", launch=False, mission_id="m-second", now=NOW)
            return None
        except gm.MissionError as e:
            return str(e)

    why = second_arm()
    check("U7-REFUSE-LIVE", why is not None and "singleflight" in why and "m-first" in why, str(why)[:80])
    check("U7-NO-DUP-LAUNCH", len(launches) == 0 and gm.load("m-second") is None, "refused arm launched nothing")
    # mutant: goal_refusal blind -> second admitted while first is live
    real_ref = gm.goal_refusal
    gm.goal_refusal = lambda c, u=None: None
    mut_admits = second_arm() is None
    gm.goal_refusal = real_ref
    if mut_admits:
        gm.transition("m-second", expect_epoch=0, expect_state=gm.PREPARED, event="t_cleanup", now=NOW,
                      state=gm.HALTED, reason="mutant cleanup")
    check("U7-MUT-REFUSAL", mut_admits, "blind goal_refusal is caught")

    # first worker dies: RUNNING, background owner, host lists it stopped -> replace (DEAD); host unreachable -> never replace
    gm.transition("m-first", expect_epoch=0, expect_state=gm.PREPARED, event="t_run", now=NOW,
                  state=gm.RUNNING, epoch=1,
                  owner={"session_id": "dead-sid", "kind": "background", "pid": 999999})
    rec = gm.load("m-first")
    dead = gm.plan_next(rec, NOW + 10, [{"sessionId": "dead-sid", "state": "stopped"}])
    live = gm.plan_next(rec, NOW + 10, [{"sessionId": "dead-sid", "state": "running"}])
    unk = gm.plan_next(rec, NOW + 10, None)
    check("U7-KILL-DEAD-REPLACE", dead["action"] == "replace", dead.get("reason", "")[:80])
    check("U7-CTRL-LIVE-NOREPLACE", live["action"] != "replace" and unk["action"] != "replace",
          f"live -> {live['action']}, host unknown -> {unk['action']}")
    real_live = gm.liveness
    gm.liveness = lambda *a, **k: (gm.LIVE, "mutant")
    mut = gm.plan_next(rec, NOW + 10, [{"sessionId": "dead-sid", "state": "stopped"}])
    gm.liveness = real_live
    check("U7-MUT-LIVENESS", mut["action"] != "replace", f"always-LIVE misses the death: {mut['action']}")

    # replacement launches ONCE, same mission id and goal
    goal_before = gm.load("m-first")["goal"]
    cur = gm.load("m-first")
    r = gm.launch_worker("m-first", expect_epoch=cur["epoch"], expect_state=cur["state"], reason="replace dead",
                         runner=runner, now=NOW + 20)
    after = gm.load("m-first")
    check("U7-REPLACE-ONCE", r.get("ok") and len(launches) == 1 and after["mission_id"] == "m-first"
          and after["goal"] == goal_before and after["epoch"] == cur["epoch"] + 1,
          f"launches={len(launches)} epoch {cur['epoch']}->{after['epoch']} goal kept")
    cur2 = gm.load("m-first")
    stale = gm.launch_worker("m-first", expect_epoch=cur["epoch"], expect_state=cur["state"], reason="dup supervisor",
                             runner=runner, now=NOW + 21) if False else None  # noqa: F841
    check("U7-STILL-REFUSED", second_arm() is not None, "replacement is still a live attempt")

    # terminal -> second admits, goal kept
    gm.transition("m-first", expect_epoch=cur2["epoch"], expect_state=cur2["state"], event="t_term", now=NOW + 30,
                  state=gm.HALTED, pending=None, reason="first worker terminal")
    check("U7-ADMIT-AFTER-TERMINAL", second_arm() is None and gm.load("m-second") is not None
          and len(launches) == 1, "second armed after first terminal; no extra launch")
    sg = (gm.load("m-second") or {}).get("goal")
    check("U7-GOAL-KEPT", sg == goal_before or (sg and sg["workstream"] == "u7canary" and sg["repo"] == key[0]),
          str(sg)[:80])
    # mutant: conflicts ignore TERMINAL -> would refuse after terminal
    real_c = gm.goal_conflicts
    gm.goal_conflicts = lambda k, **kw: [{"mission_id": "m-first", "held": False, "unit": None}] if k else []
    gm.transition("m-second", expect_epoch=gm.load("m-second")["epoch"], expect_state=gm.PREPARED, event="t_t2",
                  now=NOW + 40, state=gm.HALTED, reason="cleanup")
    mut_t = second_arm()
    gm.goal_conflicts = real_c
    check("U7-MUT-TERMINAL", mut_t is not None, "terminal-blind conflicts is caught")

    n, ok = len(res), sum(res)
    print(f"A5_U7_PASS={ok}/{n}")
    shutil.rmtree(TMP, ignore_errors=True)
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(main())
