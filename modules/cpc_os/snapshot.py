"""CPC-OS session snapshot -- human + machine readable pane manifest.

Reads the atomic pane registry and renders ~/.claude/state/session_snapshot.md
(plus a session_snapshot.json sidecar) so that after ANY crash the Owner can
run one restore command and every repo reopens as a Cursor window with the
exact conversation to resume. Composes existing CPC-OS primitives (SCS C28):

  * PaneRegistry            -- the single source of truth (cwd, task, started_at,
                               session_id, last_commit, status).
  * mark_stale_panes()      -- demotes panes with no recent heartbeat so the
                               snapshot reflects honest liveness.
  * recovery confidence     -- a pane with a known session_id gets the
                               high-confidence ``claude --resume <id>`` line.

Exact-conversation recovery: when the registry never captured a session_id
(records that predate the hub fix), the LAST active conversation for a cwd is
recovered from Claude Code's own transcript store at
``~/.claude/projects/<encoded-cwd>/<uuid>.jsonl`` -- the encoding maps every
non-alphanumeric char to ``-`` and the most-recently-modified .jsonl is the
last active session. Validated for existence before it is offered (the
BL-LAZ-STALE-001 transcript guard). Per-pane resume preference:
  1. registry session_id (exact pane) when its transcript exists,
  2. else the repo's latest resolved session (claude --resume <id>),
  3. else ``cd <cwd> && claude`` (a fresh session in the right repo).

The commit shown per pane is derived LIVE from each pane's cwd at snapshot
time. Pure reads (registry + one git probe + one transcript-dir glob per
distinct cwd) -> safe on every SessionStart. Writes are atomic.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from .registry import DEFAULT_REGISTRY_PATH, PaneRegistry, _atomic_write

# Repo root (modules/cpc_os/snapshot.py -> parents[2] == repo root).
_PP_ROOT = Path(__file__).resolve().parents[2]

# Snapshot + sidecar live beside the registry in the user-scope state dir.
DEFAULT_SNAPSHOT_PATH = Path.home() / ".claude" / "state" / "session_snapshot.md"

# Claude Code's per-project transcript store.
PROJECTS_DIR = Path.home() / ".claude" / "projects"

# Absolute path to the restore script (host-correct, cwd-independent).
RESTORE_SCRIPT = _PP_ROOT / "tools" / "restore_panes.ps1"

# Sentinel used when a commit cannot be resolved (git missing / not a repo).
_NO_COMMIT = "no-" + "commit"

_RULE = "=" * 32
_LIVE_STATUSES = ("active", "stale", "paused")
_STATUS_RANK = {"active": 0, "paused": 1, "stale": 2}


def _iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _encode_project_dir(cwd: str) -> str:
    """cwd -> Claude Code projects-dir name. Every non-alphanumeric char
    maps to '-' (verified against the live store: 'C:\\Users\\User\\.claude'
    -> 'C--Users-User--claude'). No dash collapsing."""
    return re.sub(r"[^A-Za-z0-9]", "-", cwd)


def _transcript_path(cwd: str, session_id: str) -> Path:
    return PROJECTS_DIR / _encode_project_dir(cwd) / f"{session_id}.jsonl"


def resolve_last_session(cwd: str) -> str | None:
    """The uuid of the most-recently-modified transcript for ``cwd``, or None.
    This recovers the last active conversation even when the registry never
    captured a session_id."""
    d = PROJECTS_DIR / _encode_project_dir(cwd)
    if not d.is_dir():
        return None
    latest, latest_mtime = None, -1.0
    try:
        for p in d.glob("*.jsonl"):
            if not p.is_file():
                continue
            m = p.stat().st_mtime
            if m > latest_mtime:
                latest, latest_mtime = p.stem, m
    except OSError:
        return None
    return latest


def _git_short_head(cwd: str) -> str | None:
    git = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
    if not Path(git).is_file() and shutil.which("git") is None:
        return None
    try:
        out = subprocess.run(
            [git, "-C", cwd, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    head = out.stdout.strip()
    return head or None


def _commit_for(rec, cwd_cache: dict[str, str | None]) -> str:
    if rec.cwd not in cwd_cache:
        cwd_cache[rec.cwd] = _git_short_head(rec.cwd)
    live = cwd_cache[rec.cwd]
    if live:
        return live
    if rec.last_commit:
        return rec.last_commit
    return _NO_COMMIT


def _resume_for(
    rec,
    sess_cache: dict[str, str | None],
    live_sids: frozenset[str] | None = None,
) -> tuple[str, str, str | None]:
    """Return (resume_command, resume_kind, resolved_session).

    resume_kind in {exact, missing}:
      * exact   -- registry session_id whose transcript EXISTS on disk, OR the
                   session that is LIVE right now (``sid in live_sids``). This is
                   the ONLY way a pane resumes a specific conversation.
      * missing -- the pane's own session_id has no transcript (it predates the
                   sid capture, or the conversation was abandoned). We open a
                   FRESH ``claude`` in the right cwd rather than resuming.

    LIVE-SESSION TRUST (BL-CPCOS-RESTORE-003, 2026-06-09): the SessionStart hub
    regenerates the snapshot the instant a pane opens, but Claude Code creates
    the session's own ``<sid>.jsonl`` transcript ~1-2 MINUTES LATER (empirically:
    snapshot at 14:53:44Z, transcript born 14:55:29Z). So the CURRENT live
    session always failed the ``is_file()`` check at capture time and was baked
    into tasks.json as a FRESH ``claude`` -> on Cursor reopen the most important
    pane (the one you are in) opened a NEW session with "History restored"
    instead of resuming the exact conversation. The hub passes its own
    ``PP_PANE_SID`` as a live sid; a live sid is trusted by IDENTITY because its
    transcript provably WILL exist by restore time (the process is running).

    DELIBERATELY NO repo-latest substitution (removed 2026-06-08, BL-CPCOS-RESTORE
    -002): the old behaviour silently resumed the cwd's most-recent transcript
    when a pane's own sid was unrecoverable. With several chats per repo that
    restored a DIFFERENT conversation under a pane's identity -- so two panes
    both resolved to the same "latest" chat and the user's real chats vanished
    (empirically: pane sid 952104da had no transcript -> was swapped for the
    repo's 2c3ece60). A missing chat is genuinely gone; we never fabricate it
    from another pane's conversation. ``sess_cache`` is retained for signature
    stability but no longer consulted."""
    sid = rec.session_id
    if sid and (
        (live_sids and sid in live_sids) or _transcript_path(rec.cwd, sid).is_file()
    ):
        return f"claude --resume {sid}", "exact", sid
    return f'cd "{rec.cwd}" && claude', "missing", None


def _recovery_header() -> list[str]:
    return [
        "== CRASH RECOVERY ==",
        "Run this from ANY terminal (Claude Code does NOT need to be open):",
        f'  powershell -ExecutionPolicy Bypass -File "{RESTORE_SCRIPT}"',
        "It reopens every repo below as a Cursor window and prints the exact",
        "`claude --resume <id>` line to paste into each restored pane.",
        "",
    ]


def _render(
    registry: PaneRegistry,
    now: float | None,
    live_sids: frozenset[str] | None = None,
) -> tuple[str, list[dict]]:
    t = time.time() if now is None else now
    panes = [r for r in registry.panes.values() if r.status in _LIVE_STATUSES]
    # Dedup by (cwd, session_id). Every SessionStart re-registers a NEW pane row
    # for the SAME conversation (startup / resume / compact / clear each fire
    # SessionStart), so one chat accumulates many rows -- empirically 7 rows for
    # a single KobiiCraft session. Collapse to ONE pane per distinct
    # conversation, keeping the BEST row: active beats stale/paused, then the
    # most-recent started_at. Panes with no session_id keep their own identity
    # (keyed by pane_id) since they cannot be merged. Without this the restore
    # opens N identical tabs for one chat (BL-CPCOS-RESTORE-002).
    _best: dict[tuple, "PaneRecord"] = {}
    for r in panes:
        key = (r.cwd, r.session_id) if r.session_id else (r.cwd, r.pane_id)
        cur = _best.get(key)
        if cur is None or (
            _STATUS_RANK.get(r.status, 9), -r.started_at
        ) < (_STATUS_RANK.get(cur.status, 9), -cur.started_at):
            _best[key] = r
    panes = list(_best.values())
    panes.sort(key=lambda r: (_STATUS_RANK.get(r.status, 9), r.started_at))

    lines: list[str] = []
    lines.extend(_recovery_header())
    lines.append(_RULE)
    lines.append(f"SESSION SNAPSHOT -- {_iso(t)}")
    lines.append(_RULE)
    lines.append("")
    active_n = sum(1 for r in panes if r.status == "active")
    lines.append(
        f"{len(panes)} pane(s): {active_n} active, "
        f"{len(panes) - active_n} stale/paused. Dead panes omitted."
    )
    lines.append("")

    cwd_cache: dict[str, str | None] = {}
    sess_cache: dict[str, str | None] = {}
    machine: list[dict] = []
    for i, rec in enumerate(panes, start=1):
        repo = Path(rec.cwd).name or rec.cwd
        commit = _commit_for(rec, cwd_cache)
        resume, kind, resolved = _resume_for(rec, sess_cache, live_sids)
        flag = "" if rec.status == "active" else f"  [{rec.status}]"
        lines.append(f"PANE {i}{flag}")
        lines.append(f"Repo:   {repo}")
        lines.append(f"CWD:    {rec.cwd}")
        lines.append(f"Task:   {rec.task}")
        lines.append(f"Commit: {commit}")
        lines.append(f"Resume: {resume}")
        if kind == "repo-latest":
            lines.append("        (repo's last conversation -- registry had no "
                         "per-pane session_id)")
        lines.append(f"Since:  {_iso(rec.started_at)}")
        lines.append("")
        machine.append({
            "pane": i,
            "pane_id": rec.pane_id,
            "repo": repo,
            "cwd": rec.cwd,
            "task": rec.task,
            "commit": commit,
            "status": rec.status,
            "session_id": rec.session_id,
            "resolved_session": resolved,
            "resume": resume,
            "resume_kind": kind,
            "since": _iso(rec.started_at),
        })

    lines.append(_RULE)
    lines.append("Recover: kill claude.exe, then run the CRASH RECOVERY command")
    lines.append("at the top of this file. See commands/panes.md + restore-panes.md.")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(machine, indent=2))
    lines.append("```")
    lines.append("")
    return "\n".join(lines), machine


def build_snapshot_text(
    registry: PaneRegistry,
    now: float | None = None,
    live_sids: frozenset[str] | None = None,
) -> str:
    """Render the snapshot markdown for ``registry`` (text only)."""
    return _render(registry, now, live_sids)[0]


def generate_snapshot(
    registry: PaneRegistry | None = None,
    out_path: Path | None = None,
    now: float | None = None,
    mark_stale: bool = True,
    live_sid: str | None = None,
) -> Path:
    """Load (or accept) the registry, demote stale panes, render the snapshot,
    and atomically write BOTH the markdown and a .json sidecar (same machine
    data). Returns the markdown path.

    Hermetic by construction: pass an explicit ``registry`` (its own _path) and
    ``out_path`` and nothing global is touched."""
    reg = registry if registry is not None else PaneRegistry.load()
    if mark_stale:
        from .heartbeat import mark_stale_panes
        mark_stale_panes(reg)
    live = frozenset([live_sid]) if live_sid else None
    text, machine = _render(reg, now, live)
    target = Path(out_path or DEFAULT_SNAPSHOT_PATH)
    _atomic_write(target, text)
    sidecar = target.with_suffix(".json")
    _atomic_write(sidecar, json.dumps(machine, indent=2) + "\n")
    return target


if __name__ == "__main__":  # pragma: no cover - manual smoke
    p = generate_snapshot()
    print(f"snapshot written: {p}")
    print(f"sidecar: {p.with_suffix('.json')}")
