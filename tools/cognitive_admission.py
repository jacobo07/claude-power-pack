"""Capability rows for model-call admission (CDC C3). The ONE writer: hooks/cognitive_admission.js
(Agent|Task spawn) and gsd_mission.admit_route (worker launch) both append through `record`.

Row: {ts, cap_id, sid, unit, effect, decision, reason, prompt_hash, edge}. Append-only jsonl at
<state>/cognitive-admission.jsonl. Never raises: a writer that cannot write must not stop work.
`bind_unit` writes <state>/cognitive-unit/<sid>.json = {unit, route, root}: the session's bound unit.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import uuid
from pathlib import Path


def state_dir() -> Path:
    return Path(os.environ.get("GSD_LONG_RUN_STATE_DIR") or Path.home() / ".claude" / "state")


def log_path() -> Path:
    return state_dir() / "cognitive-admission.jsonl"


def prompt_hash(text: str) -> str:
    """sha256[:16] of the whitespace-collapsed, lower-cased prompt (same normalisation as the JS hook)."""
    return hashlib.sha256(" ".join(str(text or "").split()).lower().encode("utf-8")).hexdigest()[:16]


def record(sid, unit, effect, reason, *, decision: str = "allow", phash: str | None = None,
           edge: str = "agent", cap_id: str | None = None) -> dict | None:
    row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "cap_id": cap_id or uuid.uuid4().hex[:12], "sid": sid,
           "unit": unit, "effect": effect, "decision": decision, "reason": str(reason)[:300],
           "prompt_hash": phash, "edge": edge}
    try:
        p = log_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(row, sort_keys=True) + "\n")
        return row
    except OSError:
        return None


def bind_unit(sid: str, unit: str, route: str, root: str | None = None) -> Path:
    p = state_dir() / "cognitive-unit" / f"{sid}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"unit": unit, "route": str(route), "root": str(root or "")}), encoding="utf-8")
    return p


def _main(argv: list[str]) -> int:
    # `record <sid|-> <unit> <effect> <decision> <reason> <phash|-> <edge>` -- the hook's detached writer.
    if len(argv) >= 8 and argv[0] == "record":
        _, sid, unit, effect, decision, reason, ph, edge = argv[:8]
        record(None if sid == "-" else sid, unit, effect, reason, decision=decision,
               phash=None if ph == "-" else ph, edge=edge)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
