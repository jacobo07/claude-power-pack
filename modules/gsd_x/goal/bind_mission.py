#!/usr/bin/env python3
"""Open one goal epoch that OBSERVES a Ralph mission already running (SPEC-GOAL-OBSERVE-RALPH).

Ralph missions are the live long-run path and none of them belongs to a goal.
This is the observe-only join: the goal records the mission as its in-flight
epoch, the sweep watches it end, and the gates re-run on the tree it left.
Nothing here arms, halts or writes a mission.

Refused before any append: a mission that is absent, unreadable or already
ended, and a mission whose working tree holds another repository -- a goal's
epoch must work on the goal's code.
"""
from __future__ import annotations

from pathlib import Path

from . import contract as gc
from . import epoch as ep
from . import log as gl
from .engine_identity import engine_identity
from .providers.long_run import LongRunProvider, _mission


def _check_mission(log: gl.GoalLog, mission_id: str) -> dict:
    gm = _mission()
    try:
        rec = gm.load(mission_id)
    except (gm.MissionError, OSError, ValueError) as exc:
        raise ep.EpochError(f"mission {mission_id} is unreadable: {exc}") from exc
    if rec is None:
        raise ep.EpochError(f"no mission {mission_id}")
    if rec["state"] in gm.TERMINAL:
        raise ep.EpochError(f"mission {mission_id} already ended ({rec['state']})")
    cwd = rec.get("cwd") or ""
    if not cwd or not Path(cwd).is_dir():
        raise ep.EpochError(f"mission {mission_id} names no readable working tree ({cwd!r})")
    rid = gl.repo_id(Path(cwd))
    if rid != log.repo:
        raise gl.GoalLogError(f"mission {mission_id} works in repository {rid[:12]}; goal "
                              f"{log.goal_id} belongs to {log.repo[:12]}")
    return rec


def bind_running_mission(log: gl.GoalLog, root: Path, mission_id: str, reason: str,
                         actor: str, run_dir: Path) -> ep.EpochRecord:
    """Begin, dispatch (observe-only) and mark running one cpp-gsd-long epoch."""
    _check_mission(log, mission_id)
    state = gc.project(log)
    paths = state.scope.get("paths") or ["."]
    pp_root = Path(__file__).resolve().parents[3]
    key = ep.info_key(state.revision, [f"mission:{mission_id}"], LongRunProvider.name,
                      "initial", ep.scope_hash(Path(root), paths),
                      engine=engine_identity(pp_root))
    e = ep.begin(log, state, LongRunProvider.name,
                 {"bind_mission": mission_id, "reason": reason}, key, "initial", actor)
    prov = LongRunProvider(run_dir)
    handle = prov.dispatch({"bind_mission": mission_id, "identity": e.identity})
    ep.mark_running(log, gc.project(log), e.epoch_id, handle, actor)
    return e
