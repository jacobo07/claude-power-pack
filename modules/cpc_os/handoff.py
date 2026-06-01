"""Handoff records -- /restart and /switch produce one JSON file per
event under ~/.claude/state/handoffs/. Each record carries pane_id,
kind, reason, timestamp, dry_run flag. NEVER stores raw secrets."""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

HANDOFF_DIR = Path.home() / ".claude" / "state" / "handoffs"


@dataclass(frozen=True)
class HandoffRecord:
    pane_id: str
    kind: str  # restart | switch
    reason: str
    created_at: float
    dry_run: bool


def record_handoff(
    pane_id: str,
    kind: str,
    reason: str,
    dry_run: bool = False,
) -> HandoffRecord:
    rec = HandoffRecord(
        pane_id=pane_id,
        kind=kind,
        reason=reason,
        created_at=time.time(),
        dry_run=dry_run,
    )
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    path = HANDOFF_DIR / f"handoff_{pane_id}_{ts}.json"
    path.write_text(json.dumps(asdict(rec), indent=2), encoding="utf-8")
    return rec


def list_handoffs(pane_id: str | None = None) -> list[HandoffRecord]:
    if not HANDOFF_DIR.is_dir():
        return []
    records: list[HandoffRecord] = []
    pattern = f"handoff_{pane_id}_*.json" if pane_id else "handoff_*.json"
    for f in sorted(HANDOFF_DIR.glob(pattern)):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            records.append(HandoffRecord(**data))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            continue
    return records
