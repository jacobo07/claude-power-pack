#!/usr/bin/env python3
"""V-gates for the goal CLI, end to end (C11).

Every case drives the CLI as a SUBPROCESS against a real git repository: this
is the surface an operator and the sweep actually use, and testing it by
calling the functions would prove the functions.

    python tools/test_gsd_x_goal_cli.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GIT = r"C:\Program Files\Git\cmd\git.exe"
CLI = ROOT / "tools" / "gsd_x_goal.py"
MISSION_CLI = ROOT / "tools" / "gsd_x_mission.py"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
       "PYTHONIOENCODING": "utf-8"}

GATE_OK = "import sys\nprint('2 passed')\nsys.exit(0)\n"


def run(*argv, env=None):
    return subprocess.run([sys.executable, str(CLI), *argv], capture_output=True, text=True,
                          env=env or ENV, timeout=300)


def make_repo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="gsdx_cli_repo_"))
    subprocess.run([GIT, "init", "-q", str(d)], check=True, env=ENV)
    (d / "gate.py").write_text(GATE_OK, encoding="utf-8")
    subprocess.run([GIT, "-C", str(d), "add", "."], check=True, env=ENV)
    subprocess.run([GIT, "-C", str(d), "commit", "-qm", "seed"], check=True, env=ENV)
    return d


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def ok(g, ev):
        passes.append(g)
        print(f"  PASS {g}: {ev}")

    def bad(g, why):
        fails.append(g)
        print(f"  FAIL {g}: {why}")

    def check(g, cond, ev, why):
        (ok if cond else bad)(g, ev if cond else why)

    goals = Path(tempfile.mkdtemp(prefix="gsdx_cli_goals_"))
    env = {**ENV, "GSDX_GOALS_ROOT": str(goals)}
    repo = make_repo()
    G = ["--goal", "g-cli", "--root", str(repo)]

    r = run("declare", *G, "--intent", "Prove the CLI drives the spine.",
            "--acceptance", "the gate passes", "--scope-path", ".", env=env)
    check("V-CLI-DECLARE", r.returncode == 0 and "declared g-cli" in r.stdout,
          f"a goal is declared from the command line ({r.stdout.splitlines()[0]})",
          f"rc={r.returncode} {r.stdout}{r.stderr}")

    for plane in ("OUTCOME", "EVIDENCE", "FAILURE", "REGRESSION", "UCR_CIF_LEARNING"):
        run("plane", *G, "--plane", plane, env=env)
    for plane in ("REALITY", "SETUP_LEARNING", "TRANSFER", "RECOVERY", "OPERATIONAL"):
        run("plane", *G, "--plane", plane, "--not-applicable",
            "--reason", "this goal makes no such claim", env=env)
    r = run("plane", *G, "--plane", "REALITY", "--not-applicable", env=env)
    check("V-CLI-NA-NEEDS-REASON", r.returncode == 2 and "REFUSED" in r.stdout,
          "declaring a plane N/A with no reason is refused, exit 2",
          f"rc={r.returncode} {r.stdout}")

    r = run("status", *G, env=env)
    check("V-CLI-STATUS-BLOCKED", r.returncode == 1 and "CLOSURE  : BLOCKED" in r.stdout,
          "a goal with open planes reports BLOCKED and exits 1",
          f"rc={r.returncode}\n{r.stdout}")

    for plane in ("OUTCOME", "EVIDENCE", "REGRESSION", "UCR_CIF_LEARNING"):
        r = run("oblige", *G, "--id", f"ob-{plane.lower()}", "--plane", plane,
                "--text", "prove it", "--gate", f'"{sys.executable}" gate.py',
                "--gate-file", "gate.py", env=env)
        if r.returncode != 0:
            bad("V-CLI-OBLIGE", f"{r.stdout}{r.stderr}")
            break
    else:
        ok("V-CLI-OBLIGE", "obligations are accepted with their gate files pinned")

    r = run("reconcile", *G, env=env)
    check("V-CLI-RECONCILE-DECIDES",
          "NEXT_EPOCH" in r.stdout and "decision only" in r.stdout,
          "reconcile prints a decision and changes nothing without --apply",
          f"rc={r.returncode}\n{r.stdout}")

    r = run("reconcile", *G, "--apply", "--provider", "gate", env=env)
    check("V-CLI-RECONCILE-APPLIES", r.returncode == 0 and "dispatched ep-" in r.stdout,
          "with --apply the gate epoch is dispatched", f"rc={r.returncode}\n{r.stdout}")

    r = run("explain", *G, "--task", "finish it", env=env)
    check("V-CLI-EXPLAIN", "Prove the CLI drives the spine." in r.stdout
          and "may NOT write to any production system" in r.stdout,
          "explain compiles the epoch brief from durable state", r.stdout[:300])

    # --- binding routes the MISSION gate to the goal ------------------------------
    r = run("bind", *G, env=env)
    check("V-CLI-BIND", r.returncode == 0 and "bound" in r.stdout,
          "a root is bound to its goal", f"rc={r.returncode} {r.stdout}")
    m = subprocess.run([sys.executable, str(MISSION_CLI), "check", str(repo), "--exit-code"],
                       capture_output=True, text=True, env=env, timeout=300)
    payload = {}
    try:
        payload = json.loads(m.stdout)
    except json.JSONDecodeError:
        pass
    check("V-CLI-BOUND-GATE-ASKS-THE-GOAL",
          payload.get("capId") == "gsd-x-goal-obligations"
          and payload.get("goal_id") == "g-cli" and m.returncode == 1,
          "on a bound root the mission gate answers from the GOAL, blocking on its open "
          "obligations rather than failing closed",
          f"rc={m.returncode} out={m.stdout[:300]} err={m.stderr[:200]}")
    check("V-CLI-BOUND-GATE-NOT-AN-ERROR", "error" not in payload,
          "the bound answer is a verdict, not a breakage", f"{payload}")
    st_path = Path(repo) / ".gsd-x" / "obligations.json"
    m2 = subprocess.run([sys.executable, str(MISSION_CLI), "derive", str(repo)],
                        capture_output=True, text=True, env=env, timeout=300)
    check("V-CLI-BOUND-STORE-REFUSES",
          m2.returncode == 2 and "REFUSED" in m2.stdout and not st_path.is_file(),
          "the per-root mission store refuses to write under a bound goal",
          f"rc={m2.returncode} {m2.stdout[:200]}")

    # --- judge -----------------------------------------------------------------------
    r = run("judge", *G, env=env)
    check("V-CLI-JUDGE-REFUSES-UNPROVEN", r.returncode == 1
          and json.loads(r.stdout)["verdict"] in ("UNJUDGEABLE", "REFUSED"),
          "with nothing proven the judge does not certify", r.stdout[:200])

    # --- export / restore ---------------------------------------------------------------
    out = Path(tempfile.mkdtemp(prefix="gsdx_cli_exp_")) / "goal.json"
    r = run("export", *G, "--to", str(out), env=env)
    check("V-CLI-EXPORT", r.returncode == 0 and out.is_file()
          and json.loads(out.read_text(encoding="utf-8"))["events"],
          f"the goal exports a checkpoint ({out.name})", f"rc={r.returncode} {r.stdout}")
    r = run("restore", *G, "--from", str(out), env=env)
    check("V-CLI-RESTORE-IDEMPOTENT", r.returncode == 0 and "restored 0 event" in r.stdout,
          "restoring the same export is a no-op, not a replay", f"{r.stdout}")
    shrunk = json.loads(out.read_text(encoding="utf-8"))
    shrunk["events"] = shrunk["events"][:2]
    short = out.with_name("short.json")
    short.write_text(json.dumps(shrunk), encoding="utf-8")
    r = run("restore", *G, "--from", str(short), env=env)
    check("V-CLI-RESTORE-REFUSES-REGRESSION",
          r.returncode == 2 and "would lose what is here" in r.stdout,
          "an export older than the store is refused rather than replayed", r.stdout[:200])

    total = len(passes) + len(fails)
    print(f"\nGSDX_GOAL_CLI_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
