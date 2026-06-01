"""PaneRegistry -- atomic, single-file source of truth.

Registry is a dict[pane_id, PaneRecord] persisted as JSON. Writes
are atomic via tempfile + os.replace -- a sibling pane reading the
file mid-write either sees the OLD payload (in full) or the NEW
payload (in full), never a half-written one.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Registry lives in the user-scope state dir so multiple panes on
# the same machine share it. Caller may pass a custom path.
DEFAULT_REGISTRY_PATH = Path.home() / ".claude" / "state" / "cpc_os_registry.json"

# Heartbeat tick interval (seconds) -- panes call heartbeat() at
# this cadence.
HEARTBEAT_INTERVAL_S = 30

# Stale threshold -- a pane with no heartbeat for this long is
# considered stale and will be marked accordingly.
STALE_THRESHOLD_S = 300


@dataclass
class PaneRecord:
    pane_id: str
    cwd: str
    task: str
    started_at: float
    last_heartbeat_at: float
    status: str = "active"  # active | stale | dead


def _atomic_write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        prefix=path.name + ".", dir=str(path.parent), suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(payload)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


@dataclass
class PaneRegistry:
    panes: dict[str, PaneRecord] = field(default_factory=dict)
    _path: Path | None = None

    @classmethod
    def load(cls, path: Path | None = None) -> "PaneRegistry":
        p = path or DEFAULT_REGISTRY_PATH
        if not p.is_file():
            return cls(_path=p)
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            # Corruption: caller can invoke recover_corrupt_registry().
            return cls(_path=p)
        panes: dict[str, PaneRecord] = {}
        for pid, rec in data.get("panes", {}).items():
            try:
                panes[pid] = PaneRecord(**rec)
            except (TypeError, ValueError):
                continue
        return cls(panes=panes, _path=p)

    def save(self, path: Path | None = None) -> None:
        p = path or self._path or DEFAULT_REGISTRY_PATH
        payload = json.dumps(
            {"panes": {pid: asdict(rec) for pid, rec in self.panes.items()}},
            indent=2,
        )
        _atomic_write(p, payload)

    def register_pane(
        self, pane_id: str, cwd: str, task: str,
    ) -> PaneRecord:
        now = time.time()
        rec = PaneRecord(
            pane_id=pane_id,
            cwd=cwd,
            task=task,
            started_at=now,
            last_heartbeat_at=now,
            status="active",
        )
        self.panes[pane_id] = rec
        self.save()
        return rec

    def heartbeat(self, pane_id: str) -> bool:
        if pane_id not in self.panes:
            return False
        self.panes[pane_id].last_heartbeat_at = time.time()
        if self.panes[pane_id].status != "dead":
            self.panes[pane_id].status = "active"
        self.save()
        return True

    def mark_dead(self, pane_id: str) -> bool:
        if pane_id not in self.panes:
            return False
        self.panes[pane_id].status = "dead"
        self.save()
        return True

    def get_active_panes(self) -> list[PaneRecord]:
        return [r for r in self.panes.values() if r.status == "active"]
