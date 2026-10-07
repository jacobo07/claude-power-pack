#!/usr/bin/env python3
"""Sweep -> judge timeline instrument for GSD X goals (gsdx-pcc phase 1, R01).

Reads a goal's hash-chained event log and reports when each epoch dispatched, ran,
ended and returned its receipt, what each receipt cost and observed, and how long the
judge's gate replay took. A live goal store is only ever COPIED, never opened for write.

    python tools/gsdx_goal_timeline.py recorded --store DIR --repo ID --goal ID --out FILE.json
    python tools/gsdx_goal_timeline.py fixture --out FILE.json [--pass-interval-s 0.2]
        [--max-passes 40] [--bound-s 300]

recorded exit codes: 0 timeline written; 2 refused (missing goal dir, broken chain) with no
file. fixture drives a fresh goal through the real CLI (tools/gsd_x_goal.py) in a temp git
repo under a hermetic GSDX_GOALS_ROOT/HOME: 0 CONVERGED, 1 not within the bounds, 2 a
setup step failed or the goals root resolves under the live ~/.claude (JSON still written
except on that refusal).
A metric that cannot be computed is null in the JSON and prints UNKNOWN, never 0.

Analogs: the chain is read with GoalLog.read() (modules/gsd_x/goal/log.py:152-178),
the event types are imported from the goal package, the PASS/FAIL conventions of the
companion suite follow tools/test_gsd_x_goal_gate_provider.py.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import log  # noqa: E402
from modules.gsd_x.goal.contract import DECLARED  # noqa: E402
from modules.gsd_x.goal.epoch import DISPATCHING, ENDED, RECEIPT, RUNNING  # noqa: E402
from modules.gsd_x.goal.judge import JUDGED  # noqa: E402
from modules.gsd_x.goal.log import GoalLog, GoalLogError  # noqa: E402

_EPOCH_FIELD = {DISPATCHING: "dispatching_s", RUNNING: "running_s", ENDED: "ended_s", RECEIPT: "receipt_s"}


def _ts(ev) -> datetime:
    return datetime.fromisoformat(ev.ts)


def _rel(ev, t0) -> float:
    return round((_ts(ev) - t0).total_seconds(), 3)


def timeline(events) -> dict:
    """Pure: relative times, per-epoch phases, receipt cost/observed and judge replay.

    Emits only seq/type/relative times/epoch ids/cost seconds/verdicts/observed/gate
    seconds -- no handles, identities, briefs or intent text."""
    if not events:
        return {"events": [], "epochs": {}, "first_dispatch_s": None, "judged": [],
                "judge_replay_s": None, "declared_to_last_judged_s": None}
    first = next((e for e in events if e.type == DECLARED), events[0])
    t0 = _ts(first)
    rows, epochs, judged = [], {}, []
    first_dispatch = None
    for ev in events:
        t = _rel(ev, t0)
        eid = ev.data.get("epoch_id")
        rows.append({"seq": ev.seq, "type": ev.type, "t_s": t, **({"epoch_id": eid} if eid else {})})
        if ev.type in _EPOCH_FIELD and eid:
            ep = epochs.setdefault(eid, {"provider": None, "dispatching_s": None, "running_s": None,
                                         "ended_s": None, "receipt_s": None, "outcome": None,
                                         "cost_seconds": None, "observed": []})
            ep[_EPOCH_FIELD[ev.type]] = t
            if ev.type == DISPATCHING:
                ep["provider"] = ev.data.get("provider")
                if first_dispatch is None:
                    first_dispatch = t
            elif ev.type == ENDED:
                ep["outcome"] = ev.data.get("outcome")
            elif ev.type == RECEIPT:
                rec = ev.data.get("receipt") or {}
                secs = (rec.get("cost") or {}).get("seconds")
                ep["cost_seconds"] = secs if isinstance(secs, (int, float)) else None
                ep["observed"] = [v.get("observed") for v in rec.get("verdicts") or [] if isinstance(v, dict)]
        elif ev.type == JUDGED:
            gates = ev.data.get("gates") or []
            gsecs = [g.get("seconds") if isinstance(g, dict) else None for g in gates]
            numeric = bool(gsecs) and all(isinstance(s, (int, float)) and not isinstance(s, bool) for s in gsecs)
            judged.append({"seq": ev.seq, "t_s": t, "verdict": ev.data.get("verdict"),
                           "gate_count": len(gates), "gate_seconds": gsecs,
                           "replay_s": round(sum(gsecs), 1) if numeric else None})
    return {"events": rows, "epochs": epochs, "first_dispatch_s": first_dispatch, "judged": judged,
            "judge_replay_s": judged[-1]["replay_s"] if judged else None,
            "declared_to_last_judged_s": judged[-1]["t_s"] if judged else None}


def _fmt(v) -> str:
    return "UNKNOWN" if v is None else str(v)


def print_timeline(tl: dict) -> None:
    for r in tl["events"]:
        print(f"  {r['t_s']:>10.3f}s  #{r['seq']:<4} {r['type']:<20} {r.get('epoch_id', '')}")
    print(f"first dispatch        : {_fmt(tl['first_dispatch_s'])} s")
    for eid, ep in tl["epochs"].items():
        print(f"epoch {eid}: ended {_fmt(ep['ended_s'])} s outcome {_fmt(ep['outcome'])} "
              f"cost {_fmt(ep['cost_seconds'])} s observed {ep['observed']}")
    last = tl["judged"][-1] if tl["judged"] else {}
    print(f"judged gate count     : {_fmt(last.get('gate_count'))}")
    print(f"judged verdict        : {_fmt(last.get('verdict'))}")
    print(f"judge replay          : {_fmt(tl['judge_replay_s'])} s")
    print(f"declared -> judged    : {_fmt(tl['declared_to_last_judged_s'])} s")


def cmd_recorded(a) -> int:
    src = Path(a.store) / a.repo / a.goal
    if not src.is_dir():
        print(f"REFUSED: no goal directory {src} (absence is not an empty timeline)")
        return 2
    base = Path(tempfile.mkdtemp(prefix="gsdx_tl_copy_"))
    shutil.copytree(src, base / a.repo / a.goal)
    try:
        events = GoalLog(a.repo, a.goal, base=base).read()
    except GoalLogError as exc:
        print(f"REFUSED: {exc}")
        return 2
    tl = timeline(events)
    doc = {"source": "recorded", "store": str(a.store), "repo": a.repo, "goal": a.goal,
           "copied_to": str(base / a.repo / a.goal),
           "read_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "timeline": tl}
    Path(a.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    print_timeline(tl)
    print(f"written: {a.out}")
    return 0


REAL_HOME = Path.home()
CLI = ROOT / "tools" / "gsd_x_goal.py"
FIXTURE_GOAL = "g-w0-fixture"
GATE_OK = "import sys\nprint('2 passed')\nsys.exit(0)\n"  # tools/test_gsd_x_goal_cli.py:30


def _git() -> str:
    return shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"  # test_gsd_x_goal_cli.py:23


def _step(name: str, args: list, env: dict, timeout: float = 300) -> dict:
    t0 = time.perf_counter()
    r = subprocess.run([sys.executable, str(CLI), *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env, timeout=timeout, stdin=subprocess.DEVNULL)
    wall = round(time.perf_counter() - t0, 3)
    lines = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
    return {"name": name, "args": args, "rc": r.returncode, "wall_s": wall, "stdout_tail": lines[-3:],
            "_stdout": r.stdout}


def _public(step: dict) -> dict:
    return {k: v for k, v in step.items() if not k.startswith("_")}


def cmd_fixture(a) -> int:
    """Drive a fresh goal from declare to CONVERGED through the real CLI, hermetically.

    Step order is the proven sequence of tools/test_gsd_x_goal_cli.py:186-214."""
    root = Path(tempfile.mkdtemp(prefix="gsdx_tl_fixture_"))
    repo, goals, home = root / "repo", root / "goals", root / "home"
    for d in (repo, goals, home):
        d.mkdir()
    if goals.resolve().is_relative_to((REAL_HOME / ".claude").resolve()):
        print(f"REFUSED: fixture goals root {goals} resolves under the live ~/.claude")
        return 2
    env = dict(os.environ)
    env.update(GSDX_GOALS_ROOT=str(goals), HOME=str(home), USERPROFILE=str(home), PYTHONIOENCODING="utf-8",
               GIT_AUTHOR_NAME="gsdx-fixture", GIT_AUTHOR_EMAIL="fixture@local",
               GIT_COMMITTER_NAME="gsdx-fixture", GIT_COMMITTER_EMAIL="fixture@local")
    env.pop("GSDX_GOAL_EPOCH", None)  # a set epoch makes the judge refuse (judge.py:125-128)
    git = _git()
    subprocess.run([git, "init", "-q", str(repo)], check=True, env=env)
    (repo / "gate.py").write_text(GATE_OK, encoding="utf-8")
    subprocess.run([git, "-C", str(repo), "add", "."], check=True, env=env)
    subprocess.run([git, "-C", str(repo), "commit", "-qm", "seed"], check=True, env=env)

    try:
        engine = subprocess.run([git, "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True,
                                env=env, timeout=30).stdout.strip() or "UNKNOWN"
    except (OSError, subprocess.SubprocessError):
        engine = "UNKNOWN"
    doc = {"source": "fixture", "engine_commit": engine, "python": sys.version.split()[0],
           "pass_interval_s": a.pass_interval_s, "steps": [], "passes": [], "judge_cli_wall_s": None,
           "converged": False, "hermetic": {"goals_root": str(goals), "home": str(home)}, "timeline": None}

    def write() -> None:
        try:
            events = GoalLog(log.repo_id(repo), FIXTURE_GOAL, base=goals).read()
            doc["timeline"] = timeline(events)
        except GoalLogError as exc:
            doc["timeline"] = None
            doc["timeline_error"] = str(exc)
        Path(a.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")

    G = ["--goal", FIXTURE_GOAL, "--root", str(repo)]
    setup = [("declare", ["declare", *G, "--intent", "Reach CONVERGED from the CLI (W0 fixture).",
                          "--acceptance", "the gate passes", "--scope-path", "."])]
    for plane in ("OUTCOME", "EVIDENCE", "FAILURE", "REGRESSION", "UCR_CIF_LEARNING"):
        setup.append((f"plane {plane}", ["plane", *G, "--plane", plane]))
    for plane in ("REALITY", "SETUP_LEARNING", "TRANSFER", "RECOVERY", "OPERATIONAL"):
        setup.append((f"plane {plane} n/a", ["plane", *G, "--plane", plane, "--not-applicable",
                                             "--reason", "this fixture makes no such claim"]))
    for plane in ("OUTCOME", "EVIDENCE", "REGRESSION", "UCR_CIF_LEARNING"):
        setup.append((f"oblige ob-{plane.lower()}",
                      ["oblige", *G, "--id", f"ob-{plane.lower()}", "--plane", plane, "--text", "prove it",
                       "--gate", f'"{sys.executable}" gate.py', "--gate-file", "gate.py"]))
    for name, args in setup:
        s = _step(name, args, env)
        doc["steps"].append(_public(s))
        if s["rc"] != 0:
            print(f"setup step {name!r} failed rc={s['rc']}: {s['stdout_tail']}")
            write()
            return 2

    t_start = time.perf_counter()
    clear = False
    for i in range(a.max_passes):
        if time.perf_counter() - t_start > a.bound_s:
            break
        rec = _step("reconcile --apply", ["reconcile", *G, "--apply", "--provider", "gate"], env)
        st = _step("status", ["status", *G], env)
        doc["passes"].append({"pass": i + 1, "rc": rec["rc"], "wall_s": rec["wall_s"],
                              "actions": [l for l in rec["_stdout"].splitlines() if l.strip()][:6],
                              "status_rc": st["rc"], "status_wall_s": st["wall_s"]})
        if st["rc"] == 0 and "CLOSURE  : CLEAR" in st["_stdout"]:
            clear = True
            break
        time.sleep(a.pass_interval_s)
    if clear:
        j = _step("judge --record", ["judge", *G, "--record"], env)
        doc["steps"].append(_public(j))
        doc["judge_cli_wall_s"] = j["wall_s"]
        fin = _step("reconcile", ["reconcile", *G], env)
        doc["steps"].append(_public(fin))
        doc["converged"] = "CONVERGED" in fin["_stdout"] and "independent judge" in fin["_stdout"]
    write()

    tl = doc["timeline"] or {}
    print(f"engine {engine[:12]} python {doc['python']} passes {len(doc['passes'])} "
          f"closure_clear {clear} converged {doc['converged']}")
    print(f"declare -> first dispatch : {_fmt(tl.get('first_dispatch_s'))} s")
    for eid, ep in (tl.get("epochs") or {}).items():
        print(f"epoch {eid}: cost {_fmt(ep['cost_seconds'])} s observed {ep['observed']}")
    print(f"declare -> judged         : {_fmt(tl.get('declared_to_last_judged_s'))} s")
    print(f"judge replay              : {_fmt(tl.get('judge_replay_s'))} s")
    print(f"judge CLI wall            : {_fmt(doc['judge_cli_wall_s'])} s")
    print(f"written: {a.out} (fixture root {root})")
    return 0 if doc["converged"] else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("recorded")
    r.add_argument("--store", required=True)
    r.add_argument("--repo", required=True)
    r.add_argument("--goal", required=True)
    r.add_argument("--out", required=True)
    f = sub.add_parser("fixture")
    f.add_argument("--out", required=True)
    f.add_argument("--pass-interval-s", type=float, default=0.2)
    f.add_argument("--max-passes", type=int, default=40)
    f.add_argument("--bound-s", type=float, default=300)
    return p


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    return {"recorded": cmd_recorded, "fixture": cmd_fixture}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
