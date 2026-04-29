r"""
topology_engine.py - Cursor workspace topology snapshotter (MC-LAZ-33-B).

Reads Cursor's per-workspace state.vscdb (SQLite, opened read-only) and
extracts the parts of the workspace that are reconstructible from disk:

  - Folder URI (which project the workspace points at)
  - Terminal layout: tabs, splits, relative sizes, active PIDs
    (from key `terminal.integrated.layoutInfo`)
  - Terminal env-var collections (from
    `terminal.integrated.environmentVariableCollectionsV2`) -- includes
    Anthropic.claude-code's CLAUDE_CODE_SSE_PORT per terminal
  - Panel position (1=right, 2=bottom)
  - Composer chat panes & their persistent IDs
    (from `workbench.panel.composerChatViewPane.*`)
  - aichat panel visibility counts

What is NOT here -- and explicitly cannot be without a Cursor extension:

  - Terminal scroll position (lives in xterm.js renderer state, ephemeral)
  - Terminal input buffer (typed text not yet submitted; same)
  - The exact assistant message that was on screen (renderer state)

These are the MC-LAZ-34 "DSP" gaps. The honest engineering call is to
ship topology + env-vars + chat-pane IDs (which we DO have) and surface
the missing renderer state as a known gap, not a fake stub.

Cursor stores workspaces under:
  %APPDATA%\Cursor\User\workspaceStorage\<32-hex-hash>\

with `workspace.json` (folder URI) and `state.vscdb` (SQLite, ItemTable
schema inherited from VSCode). Opened with mode=ro to avoid contention
with the live Cursor process holding a WAL handle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

USER_DIR = Path(os.path.expandvars(r"%APPDATA%\Cursor\User"))
WS_STORAGE = USER_DIR / "workspaceStorage"
LAZARUS_ROOT = Path(os.path.expanduser("~/.claude/lazarus"))
TOPOLOGY_DIR = LAZARUS_ROOT / "topology"

# Keys we extract from each workspace's ItemTable. Anything not in this
# set is intentionally ignored -- Cursor's ItemTable holds ~80 keys per
# workspace and most are renderer-internal (badges, last-known dimensions,
# etc.) that wouldn't help reconstruct a workspace.
TOPOLOGY_KEYS = (
    "terminal.integrated.layoutInfo",
    "terminal.integrated.environmentVariableCollectionsV2",
    "terminal.numberOfVisibleViews",
    "workbench.panel.position",
    "workbench.panel.hidden",
    "workbench.panel.wasLastMaximized",
)
# Prefix-matched keys (composer chat panes have UUIDs in the key name)
TOPOLOGY_PREFIXES = (
    "workbench.panel.composerChatViewPane.",
    "workbench.panel.aichat.",
)


def discover_workspaces() -> list[dict[str, Any]]:
    """Walk workspaceStorage/* and yield {hash, folder, db_path, ws_json_path}."""
    out: list[dict[str, Any]] = []
    if not WS_STORAGE.is_dir():
        return out
    for entry in sorted(WS_STORAGE.iterdir()):
        if not entry.is_dir():
            continue
        db = entry / "state.vscdb"
        if not db.is_file():
            continue
        ws_json = entry / "workspace.json"
        folder = None
        if ws_json.is_file():
            try:
                folder = json.loads(ws_json.read_text(encoding="utf-8")).get("folder")
            except (OSError, json.JSONDecodeError):
                pass
        out.append(
            {
                "hash": entry.name,
                "folder": folder,
                "db_path": str(db),
                "ws_json_path": str(ws_json) if ws_json.is_file() else None,
            }
        )
    return out


def _decode_value(raw: Any) -> Any:
    """ItemTable values are TEXT JSON or scalars. Decode JSON when possible."""
    if not isinstance(raw, (str, bytes)):
        return raw
    s = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    s = s.strip()
    if not s:
        return s
    if s[0] in "{[\"" or s in ("true", "false", "null") or _looks_numeric(s):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return s
    return s


def _looks_numeric(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def read_topology(db_path: str) -> dict[str, Any]:
    """Read topology keys from state.vscdb. Read-only, WAL-safe."""
    uri = f"file:{db_path}?mode=ro&immutable=0"
    out: dict[str, Any] = {}
    con = sqlite3.connect(uri, uri=True, timeout=2.0)
    try:
        cur = con.cursor()
        for key in TOPOLOGY_KEYS:
            row = cur.execute(
                "SELECT value FROM ItemTable WHERE key=?", (key,)
            ).fetchone()
            if row is not None:
                out[key] = _decode_value(row[0])
        for prefix in TOPOLOGY_PREFIXES:
            cur.execute(
                "SELECT key, value FROM ItemTable WHERE key LIKE ?",
                (prefix + "%",),
            )
            matched = {k: _decode_value(v) for k, v in cur.fetchall()}
            if matched:
                out.setdefault("__prefix_matched__", {})[prefix] = matched
    finally:
        con.close()
    return out


def snapshot_workspace(ws: dict[str, Any]) -> dict[str, Any]:
    """Capture one workspace's full topology snapshot."""
    return {
        "hash": ws["hash"],
        "folder": ws["folder"],
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "topology": read_topology(ws["db_path"]),
        "gaps": {
            "scroll_position_per_terminal": "NOT CAPTURED -- xterm.js renderer state, requires Cursor extension",
            "terminal_input_buffer": "NOT CAPTURED -- xterm.js renderer state, requires Cursor extension",
            "assistant_message_on_screen": "NOT CAPTURED -- renderer state, requires Cursor extension",
        },
    }


def snapshot_all() -> dict[str, Any]:
    """Snapshot every discovered workspace into one envelope."""
    workspaces = discover_workspaces()
    snapshots = []
    errors = []
    for ws in workspaces:
        try:
            snapshots.append(snapshot_workspace(ws))
        except sqlite3.Error as e:
            errors.append({"hash": ws["hash"], "folder": ws["folder"], "error": str(e)})
    return {
        "schema_version": 1,
        "envelope_captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "host": os.environ.get("COMPUTERNAME", os.uname().nodename if hasattr(os, "uname") else "unknown"),
        "workspace_count": len(workspaces),
        "snapshot_count": len(snapshots),
        "snapshots": snapshots,
        "errors": errors,
    }


def envelope_hash(envelope: dict[str, Any]) -> str:
    """Stable hash of the topology snapshots (skips timestamps)."""
    payload = {
        "snapshots": [
            {k: v for k, v in s.items() if k != "captured_at"} for s in envelope["snapshots"]
        ],
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as h:
            json.dump(payload, h, indent=2, sort_keys=False)
            h.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def write_snapshot(envelope: dict[str, Any], dest_dir: Path | None = None) -> Path:
    dest_dir = dest_dir or TOPOLOGY_DIR
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    dest = dest_dir / f"topology_{ts}.json"
    atomic_write_json(dest, envelope)
    latest = dest_dir / "topology_latest.json"
    atomic_write_json(latest, envelope)
    return dest


def restore_hint(snapshot_path: Path) -> str:
    """Cursor has no programmatic pane-rebuild API. Emit human-readable
    instructions describing the captured topology so the user can rebuild
    the layout manually (or so a future Cursor extension can consume the
    JSON directly)."""
    envelope = json.loads(snapshot_path.read_text(encoding="utf-8"))
    lines = [f"# Topology restore hint -- snapshot {snapshot_path.name}", ""]
    for snap in envelope["snapshots"]:
        folder = snap.get("folder") or "(no folder)"
        lines.append(f"## Workspace {snap['hash'][:8]}  -- {folder}")
        layout = snap["topology"].get("terminal.integrated.layoutInfo")
        if isinstance(layout, dict):
            tabs = layout.get("tabs", [])
            lines.append(f"  Terminal tabs: {len(tabs)}")
            for i, tab in enumerate(tabs):
                terminals = tab.get("terminals", [])
                active = " (active)" if tab.get("isActive") else ""
                lines.append(
                    f"    Tab {i}{active}: {len(terminals)} pane(s), active PID {tab.get('activePersistentProcessId')}"
                )
                for j, t in enumerate(terminals):
                    lines.append(
                        f"      Pane {j}: rel size {t.get('relativeSize')}, terminal {t.get('terminal')}"
                    )
        else:
            lines.append("  No terminal layout captured.")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="topology_engine",
        description="Cursor workspace topology snapshotter.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("discover", help="List workspaces visible to the engine.")
    sub.add_parser("snapshot", help="Capture all workspaces and write JSON.")
    p_read = sub.add_parser("read", help="Read topology of one workspace hash.")
    p_read.add_argument("hash")
    p_hint = sub.add_parser("restore-hint", help="Render human-readable rebuild plan.")
    p_hint.add_argument("snapshot", nargs="?", help="Snapshot path (default: latest)")
    args = parser.parse_args(argv)

    if args.cmd == "discover":
        for ws in discover_workspaces():
            folder = ws["folder"] or "(no folder)"
            print(f"{ws['hash']}  {folder}")
        return 0
    if args.cmd == "snapshot":
        env = snapshot_all()
        path = write_snapshot(env)
        h = envelope_hash(env)
        print(
            f"snapshot {path}  workspaces={env['workspace_count']}  hash={h[:12]}  errors={len(env['errors'])}"
        )
        return 0
    if args.cmd == "read":
        for ws in discover_workspaces():
            if ws["hash"].startswith(args.hash):
                snap = snapshot_workspace(ws)
                print(json.dumps(snap, indent=2))
                return 0
        print(f"no workspace matched prefix {args.hash!r}", file=sys.stderr)
        return 2
    if args.cmd == "restore-hint":
        target = (
            Path(args.snapshot) if args.snapshot else (TOPOLOGY_DIR / "topology_latest.json")
        )
        if not target.is_file():
            print(f"snapshot not found: {target}", file=sys.stderr)
            return 2
        print(restore_hint(target))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
