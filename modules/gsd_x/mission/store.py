#!/usr/bin/env python3
"""Durable storage for derived obligations -- one mission, one file.

This is the ONLY thing this wave persists, and it is scoped to the mission it
belongs to. It is deliberately not a database, not a registry, not a service and
not a second copy of anything GSD owns: the moment mission work state needs a
global store, the design has drifted into the thing the ownership audit refused.

It is also NOT the GSD X claims ledger. That ledger is PROGRAM knowledge about
GSD X -- what the programme has observed, decided and failed to prove. A mission
unknown ("does this service preserve ordering after a reconnect?") is work state
for one mission and belongs here. The two share epistemic manners; they do not
share storage, and a vocabulary that looks similar is not a reason to merge
them.
"""
from __future__ import annotations

import json
from pathlib import Path

from .obligation import Obligation

STORE_NAME = "obligations.json"


def store_path(root: Path) -> Path:
    return Path(root) / ".gsd-x" / STORE_NAME


def load(root: Path) -> list[Obligation]:
    p = store_path(root)
    if not p.is_file():
        return []
    try:
        raw = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        # A store that cannot be read is not an empty store. Saying "no
        # obligations" here would let a corrupt file close a mission.
        raise RuntimeError(f"obligation store at {p} is unreadable: {exc}") from exc
    return [Obligation.from_dict(d) for d in raw.get("obligations", [])]


# --- goal binding -------------------------------------------------------------
# THE ARGUED EXCEPTION to "one mission, one file". A goal spans worktrees and
# sessions, so its obligations cannot live in one worktree's .gsd-x/. When a goal
# is bound to this root the goal log (modules.gsd_x.goal) becomes the ONLY owner
# of intent and obligations, and this per-root store refuses writes: two stores
# for one mission is the second truth this module exists to refuse, and nothing
# would say which wins when they disagree. The binding file is a POINTER (repo
# id + goal id), never a copy of anything the goal owns.

BINDING_NAME = "GOAL_BINDING.json"


class GoalBound(RuntimeError):
    """This root's intent and obligations are owned by a goal, not by this store."""


def binding_path(root: Path) -> Path:
    return Path(root) / ".gsd-x" / BINDING_NAME


def bound_goal(root: Path) -> dict | None:
    p = binding_path(root)
    if not p.is_file():
        return None
    try:
        raw = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        # An unreadable binding is not "unbound": that reading would reopen
        # the per-root store under a goal that owns it.
        raise GoalBound(f"goal binding at {p} is unreadable: {exc}") from exc
    if not raw.get("goal_id") or not raw.get("repo"):
        raise GoalBound(f"goal binding at {p} names no goal")
    return raw


def bind(root: Path, repo: str, goal_id: str) -> Path:
    p = binding_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"repo": repo, "goal_id": goal_id}) + "\n", encoding="utf-8")
    return p


def refuse_if_bound(root: Path) -> None:
    b = bound_goal(root)
    if b is not None:
        raise GoalBound(f"{root} is bound to goal {b['goal_id']}: its intent and "
                        "obligations live in the goal log; this store is read-only")


def save(root: Path, obligations: list[Obligation]) -> Path:
    refuse_if_bound(root)
    p = store_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "obligations": [o.to_dict() for o in obligations],
    }
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    tmp.replace(p)          # atomic on both platforms we run on
    return p
