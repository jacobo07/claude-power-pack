#!/usr/bin/env python3
"""GOAL RESIDENT entrance -- the goal engine's supervised driver.

    python tools/gsd_x_resident.py run      [--max-cycles N]   # the loop systemd calls
    python tools/gsd_x_resident.py once                          # one bounded cycle
    python tools/gsd_x_resident.py status   [--json]
    python tools/gsd_x_resident.py stop                          # writes <state>/STOP
    python tools/gsd_x_resident.py census                        # classify missions, dispatch nothing

Goals come from <state>/goals.json ({"goals": [{"root": ..., "goal": ...}]}) or
from repeated `--goal ID --root PATH` pairs. State lives under GSDX_RESIDENT_STATE
(default <goals_root>/../resident). Contract: vault/specs/gdd-resident-driver.md.

Exit codes: 0 did what it says; 1 refused (lock held, authority, STOP) or the
health is not HEALTHY/RUNNING/IDLE on `status`; 2 could not run; 3 `run` honoured
STOP (the unit's RestartPreventExitStatus, so a STOP is not restarted).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import log as gl                        # noqa: E402
from modules.gsd_x.goal.providers.gate import GateProvider      # noqa: E402
from modules.gsd_x.goal.resident import control, cycle, health, missions, procs, store  # noqa: E402

COULD_NOT_RUN = 2
STOPPED_EXIT = 3          # `run` honoured STOP; systemd must not restart it
OK_HEALTH = (health.HEALTHY, health.RUNNING, health.IDLE_NO_APPROVED_GOAL)


def _goals_arg(args):
    if not args.goal:
        return None
    if len(args.goal) != len(args.root or []):
        raise SystemExit("--goal and --root must be given in pairs")
    return [(gl.GoalLog(gl.repo_id(Path(r)), g), Path(r)) for g, r in zip(args.goal, args.root)]


def _resident(args) -> cycle.Resident:
    sd = store.StateDir(Path(args.state) if args.state else None)
    providers = {"gate": GateProvider(sd.runs)}
    return cycle.Resident(ROOT, providers, goals=_goals_arg(args), state_dir=sd.root)


def _print_report(rep: cycle.CycleReport) -> None:
    for line in rep.acted:
        print(f"  {line}")
    for line in rep.skipped:
        print(f"  skipped {line}")
    for line in rep.notes:
        print(f"  note {line}")
    for c in rep.cancels:
        print(f"  cancel {c['mission']}: clean={c['clean']} census={c['orphan_census']['status']}"
              + (f" failures={c['failures']}" if c["failures"] else ""))
    print(f"health: {rep.health} -- {rep.health_reason}")


def cmd_once(args) -> int:
    r = _resident(args)
    try:
        started = r.start()
    except procs.LockRefused as exc:
        print(f"REFUSED: {exc}")
        return 1
    try:
        for row in started["census"]:
            print(f"  census {row['mission']}: {row['classification']} -- {row['action']}")
        rep = r.once()
        _print_report(rep)
    finally:
        r.close()
    return 1 if rep.stopped else 0


def cmd_run(args) -> int:
    r = _resident(args)
    try:
        started = r.start()
    except procs.LockRefused as exc:
        print(f"REFUSED: {exc}")
        return 1
    try:
        print(f"resident generation {started['generation']}; census "
              f"{len(started['census'])} mission(s)")
        why = r.run(max_cycles=args.max_cycles)
        print(f"resident exited: {why}")
    finally:
        r.close()
    # A STOP must not look like a finished wake: under Restart=always an exit 0
    # is restarted, sees STOP again and exits again until StartLimitBurst marks
    # the unit failed. The unit lists STOPPED_EXIT in RestartPreventExitStatus.
    return STOPPED_EXIT if why == "STOPPED" else 0


def cmd_census(args) -> int:
    r = _resident(args)
    try:
        started = r.start(beat=False)
    except procs.LockRefused as exc:
        print(f"REFUSED: {exc}")
        return 1
    try:
        rows = started["census"]
        for row in rows:
            print(f"  {row['mission']}: {row['classification']} ({row['reason']}) -> "
                  f"{row['action']}")
        # ExecStopPost runs this after the unit's processes are gone: report any
        # owned mission whose process group still has members.
        for m in r.missions.non_terminal():
            if m.get("pgid") is not None:
                oc = control.orphan_census(m["pgid"], r.info)
                print(f"  orphan census {m['id']} pgid {m['pgid']}: {oc['status']} "
                      f"{oc.get('pids', '')}")
        print(f"census: {len(rows)} mission(s) classified; nothing dispatched")
    finally:
        r.close()
    return 0


def cmd_stop(args) -> int:
    sd = store.StateDir(Path(args.state) if args.state else None)
    sd.ensure()
    sd.stop.write_text(json.dumps({"ts": time.time(), "by": "gsd_x_resident stop"}),
                       encoding="utf-8")
    print(f"STOP written: {sd.stop} -- the loop cancels its owned missions and exits")
    return 0


def cmd_status(args) -> int:
    sd = store.StateDir(Path(args.state) if args.state else None)
    try:
        hb = store.read_json(sd.heartbeat)
    except FileNotFoundError:
        hb = None
    except store.StateUnreadable as exc:
        print(f"heartbeat unreadable: {exc}")
        return COULD_NOT_RUN
    ms_store = missions.MissionStore(sd.missions)
    by_state: dict = {}
    for m in ms_store.all():
        by_state[m["state"]] = by_state.get(m["state"], 0) + 1
    try:
        holder = store.read_json(sd.lock)
    except FileNotFoundError:
        holder = None
    except store.StateUnreadable as exc:
        holder = {"unreadable": str(exc)}
    liv = None
    if isinstance(holder, dict) and "pid" in holder:
        liv = procs.liveness(holder.get("pid"), holder.get("start_time"), procs.ProcInfo())
    out = {"state_dir": str(sd.root), "heartbeat": hb, "missions": by_state,
           "lock": holder, "lock_holder_liveness": liv, "stop_pending": sd.stop.exists()}
    if args.json:
        print(json.dumps(out, indent=2, default=str))
    else:
        if hb is None:
            print(f"no heartbeat under {sd.root}: the resident has never run here")
        else:
            age = time.time() - float(hb.get("ts", 0))
            print(f"health   : {hb.get('health')} -- {hb.get('health_reason')}")
            print(f"heartbeat: generation {hb.get('generation')} pid {hb.get('pid')} "
                  f"cycle {hb.get('cycle')} ({age:.0f}s ago)")
            print(f"current  : {hb.get('current')}")
            print(f"blockers : {hb.get('blockers')}")
        print(f"missions : {by_state or 'none'}")
        print(f"lock     : {holder} liveness={liv}")
        print(f"STOP     : {'pending' if out['stop_pending'] else 'no'}")
    if hb is None:
        return 1
    return 0 if hb.get("health") in OK_HEALTH else 1


def main(argv: list | None = None) -> int:
    ap = argparse.ArgumentParser(prog="gsd_x_resident")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--state", help="state dir (default: GSDX_RESIDENT_STATE or "
                                       "<goals_root>/../resident)")
        p.add_argument("--goal", action="append", help="goal id (pairs with --root)")
        p.add_argument("--root", action="append", help="repository root (pairs with --goal)")

    p = sub.add_parser("run")
    common(p)
    p.add_argument("--max-cycles", type=int, default=None)
    p.set_defaults(fn=cmd_run)
    for name, fn in (("once", cmd_once), ("census", cmd_census), ("stop", cmd_stop)):
        p = sub.add_parser(name)
        common(p)
        p.set_defaults(fn=fn)
    p = sub.add_parser("status")
    common(p)
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_status)
    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except (gl.GoalLogError, store.StateUnreadable, OSError) as exc:
        print(f"could not run: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return COULD_NOT_RUN


if __name__ == "__main__":
    sys.exit(main())
