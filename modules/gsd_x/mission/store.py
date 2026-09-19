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


def save(root: Path, obligations: list[Obligation]) -> Path:
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
