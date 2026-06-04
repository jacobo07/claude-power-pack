"""PaneRegistry -- atomic, single-file source of truth.

Registry is a dict[pane_id, PaneRecord] persisted as JSON. Writes
are atomic via tempfile + os.replace -- a sibling pane reading the
file mid-write either sees the OLD payload (in full) or the NEW
payload (in full), never a half-written one.

BL-CPCOS-002 (2026-06-02): PaneRecord gained an optional ``session_id``
(for §208.2 same-session continuity) and the status vocabulary gained
``paused`` (for §208.3 switch -- a source pane parked while its target
takes focus). Both are backward compatible: old JSON records omit
session_id (defaults to None) and never carry the paused status.

Snapshot extension (2026-06-03): PaneRecord gained an optional
``last_commit`` (short git HEAD of cwd captured at register time, for the
session_snapshot.md generator). Backward compatible the same way -- old
JSON omits it and load() defaults it to None.
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

# Valid lifecycle states. active <-> paused <-> active; any -> dead.
VALID_STATUSES = ("active", "stale", "paused", "dead")


@dataclass
class PaneRecord:
    pane_id: str
    cwd: str
    task: str
    started_at: float
    last_heartbeat_at: float
    status: str = "active"  # active | stale | paused | dead
    session_id: str | None = None  # claude conversation/session uuid (§208.2)
    last_commit: str | None = None  # short git HEAD of cwd at register (snapshot)


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
        session_id: str | None = None,
        last_commit: str | None = None,
    ) -> PaneRecord:
        now = time.time()
        rec = PaneRecord(
            pane_id=pane_id,
            cwd=cwd,
            task=task,
            started_at=now,
            last_heartbeat_at=now,
            status="active",
            session_id=session_id,
            last_commit=last_commit,
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

    def pause_pane(self, pane_id: str) -> bool:
        """Park a pane (§208.3 switch source). A dead pane cannot be
        paused -- death is terminal. Returns True on a real transition."""
        rec = self.panes.get(pane_id)
        if rec is None or rec.status == "dead":
            return False
        rec.status = "paused"
        self.save()
        return True

    def activate_pane(self, pane_id: str) -> bool:
        """Bring a pane back to active (§208.3 switch target). A dead
        pane cannot be revived this way. Returns True on transition."""
        rec = self.panes.get(pane_id)
        if rec is None or rec.status == "dead":
            return False
        rec.status = "active"
        rec.last_heartbeat_at = time.time()
        self.save()
        return True

    def get_active_panes(self) -> list[PaneRecord]:
        return [r for r in self.panes.values() if r.status == "active"]

    def prune_stale(self, max_age_s: int = 7200,
                    now: float | None = None) -> int:
        """Drop panes that are dead/stale AND have not heartbeat for
        ``max_age_s`` seconds (default 2h). Active and paused panes are
        NEVER pruned regardless of age -- only terminal/abandoned ones.

        FASE -1 forensics (2026-06-04) found the registry at 121 panes
        (119 stale / 2 active / 0 dead) -- pure same-day accumulation: every
        SessionStart registers a fresh pane and nothing prunes them. The
        stale panes' last heartbeat ranged 0.16h-18.6h old, NONE older than
        24h -- so the originally-planned 24h window pruned ZERO. A pane only
        receives ``stale`` status after STALE_THRESHOLD_S (300s) of missed
        30s heartbeats, so one silent for 2h (240 missed beats) is
        unambiguously abandoned. Default recalibrated 24h -> 2h to actually
        achieve the plan's stated outcome (registry -> active + recent-stale
        only). Env/param-overridable. The reclaimed bytes are KB-scale; the
        value is keeping the registry honest so crash-recovery and switch
        logic iterate only live panes.

        Returns the number of panes removed. Saves only if >0 changed.
        """
        now = time.time() if now is None else now
        prunable = {"stale", "dead"}
        victims = [
            pid for pid, rec in self.panes.items()
            if rec.status in prunable
            and (now - rec.last_heartbeat_at) > max_age_s
        ]
        for pid in victims:
            del self.panes[pid]
        if victims:
            self.save()
        return len(victims)
