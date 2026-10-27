"""Providerless mission console (Tramo A2 Phase 7, A2-17). Status is read from files, never from a model.

    python tools/mission_console.py                               # this host
    python tools/mission_console.py --host gex44=ssh:gex44:/home/kobii/missions/ccr-a2   # + a remote host, read-only

`collect` (the remote half) prints one JSON object: live missions, the goal-status --consumers of every goal they spend
from, and the CCR generation census. The remote call is `ssh -o BatchMode=yes <host> python3 <repo>/tools/mission_console.py
collect </dev/null`: read-only, no model, no prompt. An unreachable host is a row that says so, never a silent absence.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
TERMINAL = ("COMPLETED", "HALTED", "ABANDONED", "FAILED", "CANCELLED")


def collect() -> dict:
    import gsd_mission as gm
    import mission_spend as ms
    missions, goals = [], {}
    for rec in gm.all_missions():
        if rec.get("state") in TERMINAL:
            continue
        goal = None
        try:
            goal = gm.spend_goal(rec)
        except Exception:
            pass
        missions.append({"mission_id": rec.get("mission_id"), "state": rec.get("state"), "epoch": rec.get("epoch"),
                         "goal": goal, "sid": (rec.get("owner") or {}).get("session_id")})
        if goal and goal not in goals:
            try:
                goals[goal] = ms._goal_ledger(goal).consumers()
            except Exception as exc:  # noqa: BLE001 -- reported in the row
                goals[goal] = {"error": f"{type(exc).__name__}: {exc}"}
    census = None
    try:
        r = subprocess.run([sys.executable, str(REPO / "tools" / "ccr_generation_census.py")], capture_output=True, text=True,
                           timeout=60, stdin=subprocess.DEVNULL)
        census = json.loads(r.stdout) if r.returncode == 0 else {"error": (r.stderr or r.stdout)[-300:]}
    except Exception as exc:  # noqa: BLE001
        census = {"error": f"{type(exc).__name__}: {exc}"}
    return {"missions": missions, "goals": goals, "census": census}


def fetch(spec: str) -> dict:
    """spec = name=ssh:<target>:<repo path>. BatchMode, no tty, stdin closed: it cannot prompt and cannot hang."""
    name, rest = spec.split("=", 1)
    _, target, repo = rest.split(":", 2)
    try:
        r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", target, "python3",
                            f"{repo}/tools/mission_console.py", "collect"],
                           capture_output=True, text=True, timeout=90, stdin=subprocess.DEVNULL)
        if r.returncode != 0:
            return {"host": name, "error": (r.stderr or r.stdout).strip()[-300:] or f"exit {r.returncode}"}
        return {"host": name, **json.loads(r.stdout)}
    except Exception as exc:  # noqa: BLE001
        return {"host": name, "error": f"{type(exc).__name__}: {exc}"}


def render(snaps: list[dict]) -> str:
    out = []
    for s in snaps:
        out.append(f"== {s['host']} ==")
        if "error" in s:
            out.append(f"  UNREACHABLE: {s['error']}")
            continue
        for m in s["missions"]:
            out.append(f"  {m['mission_id']}  {m['state']:<10} epoch {m['epoch']}  goal {m['goal'] or '-'}")
        if not s["missions"]:
            out.append("  (no live missions)")
        for g, c in s["goals"].items():
            if "error" in c:
                out.append(f"  goal {g}: {c['error']}")
                continue
            out.append(f"  goal {g}: lease {c['lease']} used {c['used']} remaining {c['remaining']} live burn/h {c['live_burn_per_hour']}")
            for x in c["consumers"]:
                out.append(f"    {x['sid'][:8]}  {x['share']*100:5.1f}%  spent {x['spent']}  burn/h {x['burn_per_hour']}  {'live' if x['live'] else 'idle'}  {x['role']}")
        cen = s.get("census") or {}
        if "error" in cen:
            out.append("  census: " + cen["error"])
        else:
            n = {}
            for p in cen.get("processes", []):
                n[p.get("state")] = n.get(p.get("state"), 0) + 1
            out.append(f"  census: active {cen.get('active')} impact {cen.get('impact_class')}  processes {json.dumps(n, sort_keys=True)}")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", nargs="?", default="show", choices=("show", "collect"))
    ap.add_argument("--host", action="append", default=[], help="name=ssh:<target>:<repo path>")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "collect":
        print(json.dumps(collect(), sort_keys=True))
        return 0
    snaps = [{"host": "local", **collect()}] + [fetch(h) for h in a.host]
    print(json.dumps(snaps, sort_keys=True) if a.json else render(snaps))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
