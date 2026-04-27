#!/usr/bin/env python3
"""
lazarus_revive_all.py — Multi-session Lazarus restore lister.

The Lazarus snapshot hook (~/.claude/hooks/lazarus-snapshot.js) already
writes a per-session JSON to:

    ~/.claude/lazarus/<project-id>/sessions/<session_id>.json

…plus a per-project ``index.json`` (clean-exit ledger), a heartbeat
lock per live session, and ``pending_resume.txt`` for sessions that
crashed without a clean exit.

The legacy ``/lazarus`` command only loads ``last_session.json`` —
ONE session per project. When the user has multiple Cursor / VS Code /
WindowsTerminal windows open, each running its own Claude session,
the legacy view collapses them all into one row. This tool walks
every project, classifies every session by status, and emits a
restoration report so ``/lazarus all`` can revive the full mental
model — every window, every project, every session.

Status classification:
  CURRENT  — heartbeat written within ``--current-window`` (default 90s)
             AND project_path matches the cwd we were invoked from.
             This is the session you're already in — surfacing it as
             a resume target would just spawn a duplicate.
  LIVE     — heartbeat lock present and timestamp younger than the
             ``--live-window`` (default 5 min); not the current session
  CRASHED  — heartbeat lock present but stale, OR session listed in
             ``pending_resume.txt`` without a clean-exit marker
  CLEAN    — index.json marks ``status: clean_exit`` and no live
             heartbeat
  UNKNOWN  — snapshot exists but no index entry / heartbeat (tooling
             error or partial state)

Output modes:
  --mode auto    — current project's sessions if cwd matches a known
                   project; otherwise all-projects view (default)
  --mode all     — every project, every session
  --mode current — only the project derived from --project / cwd
  --mode since   — filter by --since <duration like 24h / 30m / 7d>

Output formats: human-readable text (default) or ``--json``.

Filtering:
  --exclude-current  — drop CURRENT rows entirely from the listing
                       (default; suppresses the "resume yourself" trap)
  --include-current  — keep CURRENT rows but render them with the
                       distinct CURRENT bullet so you can see the
                       complete picture

Usage:
  python tools/lazarus_revive_all.py
  python tools/lazarus_revive_all.py --mode all
  python tools/lazarus_revive_all.py --mode since --since 6h
  python tools/lazarus_revive_all.py --mode current --project <id> --json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Windows default stdout is cp1252 which can't encode the box-drawing /
# bullet glyphs in render_text(). Reconfigure to utf-8 if available
# (Python 3.7+); fall back to ASCII bullets in render_text otherwise.
_STDOUT_UTF8 = False
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        _STDOUT_UTF8 = True
except Exception:  # noqa: BLE001 — best-effort, never block tool start
    _STDOUT_UTF8 = False


HOME = Path(os.path.expanduser("~"))
LAZARUS_DIR = HOME / ".claude" / "lazarus"
GLOBAL_INDEX = LAZARUS_DIR / "global_index.json"

LIVE_WINDOW_DEFAULT_SECONDS = 5 * 60
CURRENT_WINDOW_DEFAULT_SECONDS = 90
SINCE_DEFAULT = "24h"

DURATION_RE = re.compile(r"^(\d+(?:\.\d+)?)([smhd])$")


# ─────────────────────────── status classification ────────────────


@dataclass
class SessionRow:
    project_id: str
    project_path: str
    session_id: str
    status: str
    started: str | None = None
    last_seen: str | None = None
    ended: str | None = None
    terminal_hint: str = ""
    terminal_keys: list[str] = field(default_factory=list)
    branch: str = ""
    uncommitted_count: int = 0
    last_intent: list[str] = field(default_factory=list)
    active_plan: str | None = None
    last_tool: str | None = None
    age_seconds: float | None = None
    snapshot_path: str | None = None
    is_current: bool = False

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "project_path": self.project_path,
            "session_id": self.session_id,
            "status": self.status,
            "started": self.started,
            "last_seen": self.last_seen,
            "ended": self.ended,
            "terminal_hint": self.terminal_hint,
            "terminal_keys": self.terminal_keys,
            "branch": self.branch,
            "uncommitted_count": self.uncommitted_count,
            "last_intent": self.last_intent,
            "active_plan": self.active_plan,
            "last_tool": self.last_tool,
            "age_seconds": self.age_seconds,
            "snapshot_path": self.snapshot_path,
            "is_current": self.is_current,
        }


# ─────────────────────────── helpers ──────────────────────────────


def parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        # Normalize Z and microseconds to ISO-8601 fromisoformat input.
        s = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def parse_duration(spec: str) -> timedelta:
    m = DURATION_RE.match(spec.strip().lower())
    if not m:
        raise argparse.ArgumentTypeError(
            f"bad duration {spec!r}; expected like 30m, 6h, 2d, 90s"
        )
    value = float(m.group(1))
    unit = m.group(2)
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return timedelta(seconds=value * multipliers[unit])


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def read_json(path: Path) -> dict | list | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def sanitize_cwd_to_project_id(cwd: Path) -> str:
    return re.sub(r"[^a-zA-Z0-9-]", "-", str(cwd))


# ─────────────────────────── per-project scan ─────────────────────


def list_known_projects() -> dict[str, dict]:
    raw = read_json(GLOBAL_INDEX) or {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict] = {}
    for pid, entry in raw.items():
        if isinstance(entry, dict):
            out[pid] = entry
    # Also pick up project dirs that exist on disk but missing from index.
    if LAZARUS_DIR.exists():
        for p in LAZARUS_DIR.iterdir():
            if p.is_dir() and p.name not in out:
                out[p.name] = {"project_path": "<unknown>", "timestamp": ""}
    return out


def load_bindings(snapshot_dir: Path) -> dict[str, list[str]]:
    """Return {session_id: [terminal_key, ...]} from bindings.json."""
    bindings_path = snapshot_dir / "bindings.json"
    raw = read_json(bindings_path) or {}
    keys = raw.get("terminal_keys") if isinstance(raw, dict) else None
    out: dict[str, list[str]] = {}
    if isinstance(keys, dict):
        for term_key, sid in keys.items():
            if isinstance(sid, str) and isinstance(term_key, str):
                out.setdefault(sid, []).append(term_key)
    return out


def scan_project(
    project_id: str,
    project_path: str,
    live_window: timedelta,
    since: timedelta | None,
    current_window: timedelta,
    current_session_id: str | None,
    cwd_project_id: str | None,
) -> list[SessionRow]:
    proj_dir = LAZARUS_DIR / project_id
    if not proj_dir.is_dir():
        return []
    rows: list[SessionRow] = []

    # 1) load index.json (per-session status ledger)
    index = read_json(proj_dir / "index.json") or {}
    indexed_sessions = index.get("sessions") if isinstance(index, dict) else None
    by_id: dict[str, dict] = {}
    if isinstance(indexed_sessions, list):
        for s in indexed_sessions:
            sid = s.get("session_id")
            if isinstance(sid, str):
                by_id[sid] = s

    # 2) collect pending_resume.txt
    pending: set[str] = set()
    pending_file = proj_dir / "pending_resume.txt"
    if pending_file.exists():
        try:
            for line in pending_file.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    pending.add(line.strip())
        except OSError:
            pass

    # 3) walk heartbeats/<sid>.lock for live detection
    heartbeats: dict[str, dict] = {}
    hb_dir = proj_dir / "heartbeats"
    hb_mtimes: dict[str, float] = {}
    if hb_dir.is_dir():
        for f in hb_dir.iterdir():
            if not f.is_file() or f.suffix != ".lock":
                continue
            sid = f.stem
            data = read_json(f)
            if isinstance(data, dict):
                heartbeats[sid] = data
            try:
                hb_mtimes[sid] = f.stat().st_mtime
            except OSError:
                pass

    # 4) walk per-session snapshots
    snap_dir = proj_dir / "sessions"
    snaps: dict[str, dict] = {}
    if snap_dir.is_dir():
        for f in snap_dir.iterdir():
            if not f.is_file() or f.suffix != ".json":
                continue
            sid = f.stem
            data = read_json(f)
            if isinstance(data, dict):
                snaps[sid] = data
                snaps[sid]["__snapshot_path"] = str(f)

    # 5) terminal-key bindings (work/plan/chat → session_id)
    bindings = load_bindings(proj_dir)

    # 6) union of all session_ids seen across the four data sources
    all_ids = set(by_id.keys()) | set(heartbeats.keys()) | set(snaps.keys()) | pending
    if not all_ids:
        return []

    now = now_utc()
    now_epoch = now.timestamp()
    is_cwd_project = (cwd_project_id == project_id)

    # Identify the "freshest heartbeat" in this project — used as the
    # auto-detected current session when an explicit hint is missing.
    freshest_sid: str | None = None
    if is_cwd_project and hb_mtimes:
        freshest_sid = max(hb_mtimes, key=lambda k: hb_mtimes[k])
        # Only honor the auto-detect if its mtime is fresh enough to be
        # plausibly "this very session" — otherwise leave it None.
        if (now_epoch - hb_mtimes[freshest_sid]) > current_window.total_seconds():
            freshest_sid = None

    for sid in sorted(all_ids):
        row = SessionRow(
            project_id=project_id,
            project_path=project_path,
            session_id=sid,
            status="UNKNOWN",
        )

        idx_entry = by_id.get(sid, {})
        snap = snaps.get(sid, {})
        hb = heartbeats.get(sid, {})

        row.started = idx_entry.get("started") or snap.get("timestamp")
        row.last_seen = (
            hb.get("timestamp")
            or idx_entry.get("last_seen")
            or snap.get("timestamp")
        )
        row.ended = idx_entry.get("ended")
        row.terminal_hint = idx_entry.get("terminal_hint") or hb.get("terminal_hint") or ""
        row.terminal_keys = bindings.get(sid, [])
        row.branch = snap.get("branch") or ""
        unc = snap.get("uncommitted_files") or []
        row.uncommitted_count = len(unc) if isinstance(unc, list) else 0
        intent = snap.get("last_intent") or []
        row.last_intent = intent[-3:] if isinstance(intent, list) else []
        row.active_plan = snap.get("active_plan")
        row.last_tool = hb.get("last_tool")
        row.snapshot_path = snap.get("__snapshot_path")

        last_ts = parse_iso(row.last_seen)
        if last_ts is not None:
            row.age_seconds = (now - last_ts).total_seconds()

        # Current-session detection.
        # 1) Explicit hint wins (e.g. lazarus.md passes the live session_id).
        # 2) Otherwise, in the cwd's own project, the freshest-heartbeat
        #    session within the current_window is "this one".
        if current_session_id and sid == current_session_id and is_cwd_project:
            row.is_current = True
        elif freshest_sid is not None and sid == freshest_sid:
            row.is_current = True

        # Status logic
        idx_status = idx_entry.get("status")
        if hb and last_ts is not None:
            age = (now - last_ts).total_seconds()
            if age <= live_window.total_seconds():
                row.status = "CURRENT" if row.is_current else "LIVE"
            else:
                row.status = "CRASHED" if idx_status != "clean_exit" else "CLEAN"
        elif sid in pending and idx_status != "clean_exit":
            row.status = "CRASHED"
        elif idx_status == "clean_exit":
            row.status = "CLEAN"
        elif snap and idx_status:
            row.status = idx_status.upper()
        elif snap:
            row.status = "UNKNOWN"
        else:
            row.status = "UNKNOWN"

        # If we deemed it CURRENT but the heartbeat went stale, demote
        # the marker — it's no longer "this session" in any real sense.
        if row.is_current and row.status not in ("CURRENT", "LIVE"):
            row.is_current = False

        # Filter by --since
        if since is not None and last_ts is not None:
            if (now - last_ts) > since:
                continue

        rows.append(row)

    return rows


# ─────────────────────────── rendering ────────────────────────────


def status_bullet(status: str) -> str:
    if _STDOUT_UTF8:
        return {
            "CURRENT":  "▶ ",
            "LIVE":     "● ",
            "CRASHED":  "✗ ",
            "CLEAN":    "○ ",
            "UNKNOWN":  "? ",
        }.get(status, "? ")
    # cp1252 / legacy console fallback
    return {
        "CURRENT": "> ",
        "LIVE":    "* ",
        "CRASHED": "x ",
        "CLEAN":   "o ",
        "UNKNOWN": "? ",
    }.get(status, "? ")


def _proj_marker() -> str:
    return "──" if _STDOUT_UTF8 else "--"


def _na_marker() -> str:
    return "—" if _STDOUT_UTF8 else "-"


def format_age(seconds: float | None) -> str:
    if seconds is None:
        return _na_marker()
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds / 60)}m"
    if seconds < 86400:
        return f"{seconds / 3600:.1f}h"
    return f"{seconds / 86400:.1f}d"


def render_text(rows: list[SessionRow], header: dict) -> str:
    lines: list[str] = []
    lines.append("Lazarus Multi-Session Restore Report")
    lines.append("=" * 38)
    lines.append(f"Generated: {header['generated_at']}")
    lines.append(
        f"Mode: {header['mode']}    Live-window: {header['live_window_s']}s    "
        f"Current-window: {header['current_window_s']}s"
    )
    if header.get("since"):
        lines.append(f"Filter: only sessions touched within {header['since']}")
    if header.get("exclude_current"):
        lines.append("Filter: CURRENT (this session) excluded from listing")
    lines.append("")
    lines.append(
        f"Total sessions: {header['total']}   "
        f"CURRENT: {header['by_status'].get('CURRENT', 0)}   "
        f"LIVE: {header['by_status'].get('LIVE', 0)}   "
        f"CRASHED: {header['by_status'].get('CRASHED', 0)}   "
        f"CLEAN: {header['by_status'].get('CLEAN', 0)}   "
        f"UNKNOWN: {header['by_status'].get('UNKNOWN', 0)}"
    )
    lines.append("")

    if not rows:
        lines.append("(no sessions match the current filter)")
        return "\n".join(lines)

    by_proj: dict[str, list[SessionRow]] = {}
    paths: dict[str, str] = {}
    for r in rows:
        by_proj.setdefault(r.project_id, []).append(r)
        paths[r.project_id] = r.project_path

    # Sort projects so most-recent activity appears first
    def proj_recency(pid: str) -> float:
        ages = [r.age_seconds for r in by_proj[pid] if r.age_seconds is not None]
        return min(ages) if ages else float("inf")

    for pid in sorted(by_proj.keys(), key=proj_recency):
        proj_rows = sorted(
            by_proj[pid],
            key=lambda r: (r.age_seconds if r.age_seconds is not None else float("inf")),
        )
        lines.append(f"{_proj_marker()} Project: {pid}")
        lines.append(f"   path: {paths[pid]}")
        lines.append(f"   sessions: {len(proj_rows)}")
        # Surface terminal-key bindings (visual layout map) for this
        # project. Read directly from bindings.json so bindings whose
        # target session was filtered out (e.g. CURRENT under default
        # --exclude-current) still appear in the visual map — the
        # bindings are project-level state, not session-level.
        raw_bindings = read_json(LAZARUS_DIR / pid / "bindings.json") or {}
        raw_keys = raw_bindings.get("terminal_keys") if isinstance(raw_bindings, dict) else None
        proj_term_keys: dict[str, str] = {}
        if isinstance(raw_keys, dict):
            for tk, sid in raw_keys.items():
                if isinstance(tk, str) and isinstance(sid, str):
                    proj_term_keys[tk] = sid
        if proj_term_keys:
            line = "   terminal-keys: " + " | ".join(
                f"{k}→{sid[:8]}" for k, sid in sorted(proj_term_keys.items())
            )
            lines.append(line)
        for r in proj_rows:
            tag = " [CURRENT]" if r.is_current else ""
            term_keys = (
                f"  keys=[{','.join(r.terminal_keys)}]" if r.terminal_keys else ""
            )
            lines.append(
                f"   {status_bullet(r.status)}{r.session_id}  "
                f"[{r.status:<7}]{tag}  age={format_age(r.age_seconds):<5}  "
                f"branch={r.branch or '?'}  unc={r.uncommitted_count}  "
                f"term={r.terminal_hint or _na_marker()}{term_keys}"
            )
            if r.last_intent:
                trimmed = r.last_intent[-1][:90]
                lines.append(f"        last_intent: \"{trimmed}\"")
            if r.last_tool:
                lines.append(f"        last_tool:   {r.last_tool}")
            if r.active_plan:
                lines.append(f"        active_plan: {r.active_plan}")
        lines.append("")

    # Restoration commands — skip CURRENT (you're already in it) and CLEAN
    # (intentional exit). LIVE = attach context here; CRASHED = revive.
    revivable = [
        r for r in rows
        if r.status in ("LIVE", "CRASHED") and not r.is_current
    ]
    lines.append("Restoration paths:")
    if revivable:
        lines.append("  Recommended next-steps (one window per row):")
        for r in revivable:
            display_path = paths.get(r.project_id, r.project_path) or r.project_path
            lines.append(
                f"    cd \"{display_path}\" && claude --resume {r.session_id}"
            )
        lines.append("")
    lines.append("  Resume current project (latest):       /lazarus")
    lines.append("  Re-run this listing:                   /lazarus all")
    if any(r.is_current for r in rows):
        lines.append(
            "  (CURRENT row is THIS session — not listed as a resume target)"
        )
    return "\n".join(lines)


# ─────────────────────────── main ─────────────────────────────────


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Lazarus multi-session lister")
    p.add_argument("--mode", choices=["auto", "all", "current", "since"],
                   default="auto", help="scan mode (default auto)")
    p.add_argument("--project", help="explicit project_id; if omitted, derived from cwd")
    p.add_argument("--cwd", help="override cwd for project derivation")
    p.add_argument("--since", default=SINCE_DEFAULT,
                   help=f"only sessions touched within this duration (default {SINCE_DEFAULT}); used when --mode is 'since' or 'auto'")
    p.add_argument("--live-window", type=int, default=LIVE_WINDOW_DEFAULT_SECONDS,
                   help=f"heartbeat freshness window in seconds (default {LIVE_WINDOW_DEFAULT_SECONDS})")
    p.add_argument("--current-window", type=int, default=CURRENT_WINDOW_DEFAULT_SECONDS,
                   help=f"window for auto-detecting THIS session via freshest heartbeat (default {CURRENT_WINDOW_DEFAULT_SECONDS}s)")
    p.add_argument("--current-session-id", default=None,
                   help="explicit session_id of the invoking Claude session (skill can pass this)")
    p.add_argument("--include-stale", action="store_true",
                   help="ignore --since filter; show every session regardless of age")

    cur_grp = p.add_mutually_exclusive_group()
    cur_grp.add_argument("--exclude-current", dest="exclude_current",
                         action="store_true", default=True,
                         help="drop CURRENT (this session) rows from the listing (default)")
    cur_grp.add_argument("--include-current", dest="exclude_current",
                         action="store_false",
                         help="keep CURRENT rows visible (still tagged [CURRENT])")

    p.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if not LAZARUS_DIR.is_dir():
        msg = f"lazarus_revive_all: no Lazarus dir at {LAZARUS_DIR}"
        if args.json:
            print(json.dumps({"error": msg, "rows": []}))
        else:
            print(msg, file=sys.stderr)
        return 0

    live_window = timedelta(seconds=args.live_window)
    current_window = timedelta(seconds=max(1, args.current_window))
    since: timedelta | None
    # --since is applied for every mode EXCEPT 'current' (where Owner
    # explicitly wants one project's full history). --include-stale
    # overrides everything.
    if args.include_stale or args.mode == "current":
        since = None
    else:
        try:
            since = parse_duration(args.since)
        except argparse.ArgumentTypeError as e:
            print(f"lazarus_revive_all: {e}", file=sys.stderr)
            return 2

    projects = list_known_projects()
    cwd = Path(args.cwd or os.getcwd())
    cwd_project_id = sanitize_cwd_to_project_id(cwd)
    derived_id = args.project or cwd_project_id

    if args.mode == "current":
        target_ids = [derived_id] if derived_id in projects else []
        if not target_ids:
            msg = f"no Lazarus data for project {derived_id}"
            if args.json:
                print(json.dumps({"error": msg, "rows": []}))
            else:
                print(msg, file=sys.stderr)
            return 0
    elif args.mode == "auto":
        # Auto: if cwd matches a known project, list THAT project's sessions
        # without --since filter; else all projects with --since filter.
        if derived_id in projects:
            target_ids = [derived_id]
            since = None
        else:
            target_ids = list(projects.keys())
    else:  # all, since
        target_ids = list(projects.keys())

    rows: list[SessionRow] = []
    for pid in target_ids:
        proj_path = projects.get(pid, {}).get("project_path", "<unknown>")
        rows.extend(scan_project(
            pid,
            proj_path,
            live_window,
            since,
            current_window,
            args.current_session_id,
            cwd_project_id,
        ))

    # Filter CURRENT rows (default) — they represent this very session,
    # so suggesting them as a resume target is the redundancy MC-LAZ-03 fixes.
    if args.exclude_current:
        rows = [r for r in rows if not r.is_current]

    by_status: dict[str, int] = {}
    for r in rows:
        by_status[r.status] = by_status.get(r.status, 0) + 1

    header = {
        "generated_at": now_utc().isoformat().replace("+00:00", "Z"),
        "mode": args.mode,
        "live_window_s": int(live_window.total_seconds()),
        "current_window_s": int(current_window.total_seconds()),
        "since": (None if since is None else args.since),
        "exclude_current": bool(args.exclude_current),
        "total": len(rows),
        "by_status": by_status,
    }

    if args.json:
        out = {"header": header, "rows": [r.to_dict() for r in rows]}
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        print(render_text(rows, header))
    return 0


if __name__ == "__main__":
    sys.exit(main())
