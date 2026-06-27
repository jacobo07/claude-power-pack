"""G2 -- Multi-Window Coordinator.

Owns session state ABOVE the single window: how many Cursor windows existed,
which workspace each hosted, which was foreground, and the conflict-free order to
restore them. Window interiors are delegated (terminals -> CETTG, editor -> G1);
G2 says WHICH windows and IN WHAT ORDER, then composes per-window descriptions
(via G3) into a cross-window picture. Composes -- does NOT modify --
tools/build_pane_map.ps1 (which discovers per-repo panes on disk); G2 consumes
that kind of pane data and adds the window dimension + coordination.

Never trusts PIDs/handles (invalid after crash); identity is derived from durable
signals. Hermetic: the registry persists under an explicit ``state_dir``.

Eight entities (dataset session_resilience_02):
  1. WindowRegistry            -- durable, PID-free inventory of windows
  2. cross_window_topology     -- count + bindings + foreground graph
  3. resolve_window_identity   -- stable id across restart (no PID)
  4. bind_workspace            -- verify each window's workspace path exists
  5. restoration_order         -- ordered, resource-aware restore plan
  6. arbitrate_focus           -- exactly one foreground after restore
  7. lock_coordinator          -- no two windows claim one conversation/pane
  8. WindowLifecycle           -- clean-close reduces census; crash preserves it
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

# Window status values
OPEN = "open"
CLOSED_CLEAN = "closed_clean"        # intentional close -> drops from expected census
RECOVERY_PENDING = "recovery_pending"  # crash disappearance -> preserved for recovery


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


# --- Entity 3: Window Identity Resolver -------------------------------------

def resolve_window_identity(workspace_path: str, marker: str | None = None) -> str:
    """A stable window id derived from durable signals, NEVER a PID/handle.
    ``marker`` is a durable per-window token (written by the extension) that
    disambiguates two windows on the same workspace; without it, identity falls
    back to the workspace path alone (sufficient when one window per workspace)."""
    basis = f"{workspace_path}\x00{marker or ''}"
    return "win-" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:12]


# --- Entity 4: Window-to-Workspace Binding Engine ---------------------------

def bind_workspace(workspace_path: str) -> tuple[bool, str]:
    """Verify a window's workspace still exists. Returns (ok, reason). A missing
    path is flagged (blocked-with-reason) rather than opened wrong/empty."""
    if not workspace_path:
        return False, "no workspace_path"
    if Path(workspace_path).is_dir():
        return True, "workspace exists"
    return False, f"workspace path missing: {workspace_path}"


@dataclass
class WindowRecord:
    window_id: str
    workspace_path: str
    foreground: bool = False
    panes: list[dict] = field(default_factory=list)  # [{pane_id, cwd, conversation_id}]
    status: str = OPEN
    last_stable: str | None = None

    def to_dict(self) -> dict:
        return {
            "window_id": self.window_id, "workspace_path": self.workspace_path,
            "foreground": self.foreground, "panes": self.panes,
            "status": self.status, "last_stable": self.last_stable,
        }

    @staticmethod
    def from_dict(d: dict) -> "WindowRecord":
        return WindowRecord(
            window_id=d["window_id"], workspace_path=d.get("workspace_path", ""),
            foreground=bool(d.get("foreground")), panes=list(d.get("panes") or []),
            status=d.get("status", OPEN), last_stable=d.get("last_stable"),
        )


# --- Entity 1: Window Registry ----------------------------------------------

class WindowRegistry:
    """Durable, PID-free inventory of Cursor windows. Updated on lifecycle
    events, not just at shutdown, so a crash finds a current census."""

    def __init__(self, state_dir: Path | str, filename: str = "window_registry.json") -> None:
        self.path = Path(state_dir) / filename
        self._windows: dict[str, WindowRecord] = self._load()

    def _load(self) -> dict[str, WindowRecord]:
        if self.path.is_file():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8-sig"))
                return {k: WindowRecord.from_dict(v) for k, v in raw.get("windows", {}).items()}
            except (json.JSONDecodeError, KeyError):
                pass
        return {}

    def _save(self) -> None:
        _atomic_write_json(self.path, {"windows": {k: v.to_dict() for k, v in self._windows.items()}})

    def register(self, window_id: str, workspace_path: str, foreground: bool = False,
                 panes: list[dict] | None = None, ts: str | None = None) -> WindowRecord:
        rec = self._windows.get(window_id)
        if rec is None:
            rec = WindowRecord(window_id, workspace_path)
            self._windows[window_id] = rec
        rec.workspace_path = workspace_path
        rec.foreground = foreground
        if panes is not None:
            rec.panes = panes
        rec.status = OPEN
        rec.last_stable = ts
        self._save()
        return rec

    def windows(self, include_closed: bool = False) -> list[WindowRecord]:
        return [w for w in self._windows.values()
                if include_closed or w.status != CLOSED_CLEAN]

    def get(self, window_id: str) -> WindowRecord | None:
        return self._windows.get(window_id)

    def expected_census(self) -> int:
        """Windows that should be recovered: everything not cleanly closed
        (crash-pending windows are still expected)."""
        return sum(1 for w in self._windows.values() if w.status != CLOSED_CLEAN)


# --- Entity 8: Window Lifecycle (clean-close vs crash) ----------------------

class WindowLifecycle:
    """Distinguishes intentional clean close (reduces expected census) from crash
    disappearance (preserves the window for recovery) -- CETTG pane semantics at
    the window level."""

    def __init__(self, registry: WindowRegistry) -> None:
        self.registry = registry

    def clean_close(self, window_id: str) -> bool:
        rec = self.registry.get(window_id)
        if not rec:
            return False
        rec.status = CLOSED_CLEAN
        self.registry._save()
        return True

    def crash_gone(self, window_id: str) -> bool:
        rec = self.registry.get(window_id)
        if not rec:
            return False
        rec.status = RECOVERY_PENDING  # preserved, NOT removed
        self.registry._save()
        return True


# --- Entity 2: Cross-Window Topology Engine ---------------------------------

def cross_window_topology(registry: WindowRegistry) -> dict:
    """Compose the windows into one whole-session picture: count, per-window
    bindings + pane counts, and the single foreground."""
    wins = registry.windows()
    fg = [w.window_id for w in wins if w.foreground]
    return {
        "count": len(wins),
        "foreground": fg[0] if fg else None,
        "foreground_contested": len(fg) > 1,
        "windows": [
            {"window_id": w.window_id, "workspace_path": w.workspace_path,
             "foreground": w.foreground, "pane_count": len(w.panes), "status": w.status}
            for w in wins
        ],
    }


# --- Entity 6: Focus Arbitration Engine -------------------------------------

def arbitrate_focus(registry: WindowRegistry) -> tuple[str | None, str]:
    """Exactly one foreground after restore. Returns (window_id, reason).
    If several claim foreground -> deterministic pick (lowest window_id) + note.
    If none -> fallback to the window with the most panes (highest priority)."""
    wins = registry.windows()
    if not wins:
        return None, "no windows"
    claimers = sorted([w for w in wins if w.foreground], key=lambda w: w.window_id)
    if len(claimers) == 1:
        return claimers[0].window_id, "single foreground claimer"
    if len(claimers) > 1:
        return claimers[0].window_id, f"contested ({len(claimers)}) -> lowest id"
    best = max(wins, key=lambda w: (len(w.panes), w.window_id))
    return best.window_id, "no claimer -> most-panes fallback"


# --- Entity 7: Cross-Window Lock Coordinator --------------------------------

def lock_coordinator(registry: WindowRegistry) -> dict:
    """A conversation may be owned by exactly one window. Returns
    {grants: {conversation_id: window_id}, conflicts: [{conversation_id, windows}]}.
    On contention, grant to the foreground window (else lowest window_id) and
    block the other -- never duplicate ownership."""
    owners: dict[str, list[WindowRecord]] = {}
    for w in registry.windows():
        for pane in w.panes:
            conv = pane.get("conversation_id")
            if conv:
                owners.setdefault(conv, []).append(w)
    grants: dict[str, str] = {}
    conflicts: list[dict] = []
    for conv, wins in owners.items():
        if len(wins) == 1:
            grants[conv] = wins[0].window_id
            continue
        winner = sorted(wins, key=lambda w: (not w.foreground, w.window_id))[0]
        grants[conv] = winner.window_id
        conflicts.append({
            "conversation_id": conv,
            "granted_to": winner.window_id,
            "blocked": [w.window_id for w in wins if w.window_id != winner.window_id],
        })
    return {"grants": grants, "conflicts": conflicts}


# --- Entity 5: Window Restoration Orchestrator ------------------------------

def restoration_order(registry: WindowRegistry, resource_pressure: bool = False) -> dict:
    """Ordered, resource-aware restore plan. Priority: windows with an active
    lock first, then foreground, then most panes. Under resource pressure the
    plan is sequential (parallel_allowed False) -- never a simultaneous blast."""
    wins = [w for w in registry.windows() if w.status != CLOSED_CLEAN]

    def priority(w: WindowRecord) -> tuple:
        has_lock = any(p.get("locked") for p in w.panes)
        # lower tuple sorts first
        return (0 if has_lock else 1, 0 if w.foreground else 1, -len(w.panes), w.window_id)

    ordered = sorted(wins, key=priority)
    return {
        "order": [w.window_id for w in ordered],
        "parallel_allowed": not resource_pressure,
        "sequential_reason": "resource pressure -> one window at a time" if resource_pressure else "",
    }


# --- G2 -> G3 bridge: a single window's StateDescription --------------------

def window_state_description(rec: WindowRecord, editor: dict | None = None) -> dict:
    """Compose one window's recoverable description (terminals + optional editor)
    in the canonical shape G3 versions and G4 scores. The editor portion is
    supplied by G1 (extension capture); absent here, it is omitted."""
    window: dict = {
        "window_id": rec.window_id,
        "workspace_path": rec.workspace_path,
        "foreground": rec.foreground,
        "terminals": [
            {"pane_id": p.get("pane_id"), "cwd": p.get("cwd"),
             "conversation_id": p.get("conversation_id")}
            for p in rec.panes
        ],
    }
    if editor is not None:
        window["editor"] = editor
    return {"schema_version": 1, "captured_at": rec.last_stable, "windows": [window]}
