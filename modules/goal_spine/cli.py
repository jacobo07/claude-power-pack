#!/usr/bin/env python3
"""Goal Spine CLI -- the command every instruction and Owner packet points at.

    python -m modules.goal_spine.cli list
    python -m modules.goal_spine.cli status <goal-id>
    python -m modules.goal_spine.cli tick   <goal-id> [--gate ID ...]
    python -m modules.goal_spine.cli claim  <epoch-id> [--session SID]
    python -m modules.goal_spine.cli instruct <epoch-id>

`claim` is run BY a worker pane, IN that pane: with no --session it reads
CLAUDE_CODE_SESSION_ID from the environment, because the session that claims an
epoch must be the session that will run it. It refuses rather than guessing.

This generic CLI knows no gates. A project adapter that registers gates (for
KobiiCraft, tools/ksis/kseip/goal/) passes them to `tick`; `--gate` is here so a
worker can reproduce a decision by hand.
"""
from __future__ import annotations

import argparse
import os
import sys

from . import convergence as cv
from . import epoch as ep_
from . import goal as gl
from . import reconciler as rcn
from . import store as gs
from .providers import gsd_long


def _status(goal_id: str) -> int:
    g = gs.load(goal_id)
    v = cv.compute(g)
    print(f"{g.goal_id}  rev {g.revision}  {g.state}")
    print(f"  root     {g.root}")
    print(f"  intent   {g.intent[:100]}")
    if g.state == gl.BLOCKED:
        print(f"  blocked  {g.blocked_category}: {g.blocked_reason}")
    print(f"  converged {v.converged}")
    for b in v.blocking:
        print(f"    OPEN  {b}")
    for r in v.residual_risk:
        print(f"    RISK  {r}")
    for e in ep_.for_goal(goal_id):
        mark = "*" if e.state in ep_.OPEN_STATES else " "
        print(f"  {mark} {e.epoch_id}  {e.provider:<9} {e.state:<10} {', '.join(e.scope)}"
              + (f"  -- {e.outcome}" if e.outcome else ""))
    return 0 if v.converged else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="goal-spine")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    for name in ("status", "tick"):
        p = sub.add_parser(name)
        p.add_argument("goal_id")
        if name == "tick":
            p.add_argument("--gate", action="append", default=[])
    p = sub.add_parser("claim")
    p.add_argument("epoch_id")
    p.add_argument("--session", default="")
    sub.add_parser("instruct").add_argument("epoch_id")
    args = ap.parse_args(argv)

    if args.cmd == "list":
        for gid in gs.list_goals():
            g = gs.load(gid)
            print(f"{gid}  rev {g.revision}  {g.state:<16} {g.intent[:60]}")
        return 0
    if args.cmd == "status":
        return _status(args.goal_id)
    if args.cmd == "tick":
        a = rcn.tick(args.goal_id, gates=frozenset(args.gate))
        print(f"{a.kind}  {a.reason}")
        if a.epoch_id:
            print(f"  epoch {a.epoch_id} ({a.provider})")
        if a.packet_id:
            print(f"  owner packet {a.packet_id} delivered={a.packet_delivered}")
        return 0
    if args.cmd == "claim":
        sid = args.session or os.environ.get("CLAUDE_CODE_SESSION_ID", "")
        if not sid:
            print("REFUSED: no session id. Run this IN the worker pane, or pass --session. "
                  "The session that claims an epoch must be the one that runs it.",
                  file=sys.stderr)
            return 2
        e = gsd_long.claim(args.epoch_id, sid)
        print(f"claimed {e.epoch_id} for {e.claimed_by}; lease until {e.lease_expires_at}")
        print(f"now run: {e.command}")
        return 0
    if args.cmd == "instruct":
        e = ep_.load(args.epoch_id)
        print(gsd_long.instruction(gs.load(e.goal_id), e))
        return 0
    return 2                                            # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
