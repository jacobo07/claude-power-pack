"""topology_reconcile.py -- Cursor-authoritative tab count for CPC-OS restore.

THE FIX for "a veces no regenera el mismo numero de cursor tabs"
(BL-CPCOS-RESTORE-004, 2026-06-16).

Background. CPC-OS restore *derived* the number of restored terminal tabs from
the heartbeat pane registry, then deduped twice (once by (cwd, session_id) in
snapshot.py, again by resume-string in vscode_autorun.py). That derivation
drifts three ways:

  RC-1  no production caller ever heartbeats a pane -> long-lived idle panes go
        stale (5 min) and get pruned (2 h) even though their Cursor tab is open;
  RC-2  every non-resumable pane resolves to the identical string
        ``cd "<cwd>" && claude`` -> N distinct chats collapse to ONE tab;
  RC-3  the transcript-birth race (Claude Code writes <sid>.jsonl ~1-2 min after
        SessionStart, and only ONE live_sid is trusted) non-deterministically
        decides which panes fall to RC-2.

The historic Lazarus topology engine never had this problem because it RECORDED
ground truth: it reads Cursor's own ``state.vscdb`` key
``terminal.integrated.layoutInfo`` and counts the literal terminal tabs Cursor
has open. A recording cannot miscount. This module reconnects that ground truth
to the active restore path: the COUNT of tabs to restore comes from Cursor's
live topology; the registry/transcripts only decide WHICH tabs resume a specific
conversation (exact ``claude --resume <sid>``) vs open fresh.

Once the count is authoritative, RC-1/RC-2/RC-3 can only change whether a tab
resumes-or-opens-fresh, never how many tabs there are.

Pure + hermetic: every parsing function takes an explicit envelope/value so
tests touch no Cursor install. ``current_tab_counts()`` is the only function
that reaches the live machine, and it is fail-open (returns {} on any error) so
a host without Cursor / without captured topology degrades to the old derived
behaviour instead of breaking restore.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import unquote, urlparse


def folder_uri_to_path(uri: str | None) -> str | None:
    """Cursor workspace folder URI -> Windows path.

    ``file:///c%3A/Users/U/Desktop/Cursor%20Projects/X``
        -> ``c:\\Users\\U\\Desktop\\Cursor Projects\\X``

    Returns None for an empty/unparseable URI. The drive letter is left as
    captured (callers compare case-insensitively via :func:`norm_path`)."""
    if not uri:
        return None
    try:
        if uri.startswith("file:"):
            path = unquote(urlparse(uri).path)
        else:
            path = unquote(uri)
    except (ValueError, TypeError):
        return None
    # urlparse yields "/c:/Users/..." for a file URI -- strip the leading slash
    # that sits in front of the drive letter.
    if len(path) >= 3 and path[0] == "/" and path[2] == ":":
        path = path[1:]
    return path.replace("/", "\\")


def norm_path(path: str | None) -> str:
    """Case/seperator-insensitive key for matching a snapshot cwd against a
    topology folder. Lowercase, backslashes, no trailing slash."""
    if not path:
        return ""
    return path.replace("/", "\\").rstrip("\\").lower()


def terminal_count(layout_info: Any) -> int:
    """Number of terminal SHELLS in one workspace's ``layoutInfo``.

    Counts every terminal pane across every tab (a split tab holds >1
    terminal). This is the faithful "how many claude shells were open" number;
    each restored task is its own dedicated terminal, so shells map 1:1 to
    restored tabs. Returns 0 when no terminal layout was captured (a closed /
    terminal-less workspace)."""
    if not isinstance(layout_info, dict):
        return 0
    tabs = layout_info.get("tabs")
    if not isinstance(tabs, list):
        return 0
    n = 0
    for tab in tabs:
        if not isinstance(tab, dict):
            continue
        terminals = tab.get("terminals")
        if isinstance(terminals, list):
            n += len(terminals)
    return n


def live_tab_counts(envelope: dict[str, Any]) -> dict[str, int]:
    """Map ``norm_path(cwd) -> live terminal-tab count`` from a topology
    envelope (the output of ``topology_engine.snapshot_all``).

    Cursor's ``workspaceStorage`` accumulates STALE hashes: one folder can
    appear under several hashes (empirically GEO-audit x3, nexumops x4), some
    with 0 tabs (closed). We must NOT sum them. For each folder we keep the
    LIVE workspace -- the one whose ``state.vscdb`` was modified most recently
    (``db_mtime``); ties break on the higher tab count. Workspaces with 0
    terminals are skipped entirely (a terminal-less / closed workspace
    contributes no restore tabs)."""
    best: dict[str, tuple[float, int]] = {}
    for snap in envelope.get("snapshots", []) or []:
        if not isinstance(snap, dict):
            continue
        path = folder_uri_to_path(snap.get("folder"))
        if not path:
            continue
        layout = (snap.get("topology") or {}).get("terminal.integrated.layoutInfo")
        count = terminal_count(layout)
        if count <= 0:
            continue
        key = norm_path(path)
        mtime = snap.get("db_mtime")
        mtime = float(mtime) if isinstance(mtime, (int, float)) else 0.0
        cur = best.get(key)
        if cur is None or (mtime, count) > cur:
            best[key] = (mtime, count)
    return {key: cnt for key, (_mt, cnt) in best.items()}


def current_tab_counts() -> dict[str, int]:
    """Live ``norm_path(cwd) -> tab count`` by capturing Cursor's topology RIGHT
    NOW (reads ``state.vscdb`` directly -- always current, no daemon needed).

    Fail-open by contract: returns {} when the topology engine is unavailable
    (no Cursor install, import path missing, sqlite error). Callers then keep
    the old derived tab behaviour, so restore never breaks on a bare host."""
    import os
    import sys
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        from lib.lazarus.topology_engine import snapshot_all
    except Exception:
        return {}
    try:
        envelope = snapshot_all()
    except Exception:
        return {}
    try:
        return live_tab_counts(envelope)
    except Exception:
        return {}
