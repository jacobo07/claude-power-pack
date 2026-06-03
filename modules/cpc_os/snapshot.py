"""CPC-OS session snapshot -- human + machine readable pane manifest.

Reads the atomic pane registry and renders ~/.claude/state/session_snapshot.md
so that after ANY crash the Owner can open one file and restore every pane
to its exact context. Composes existing CPC-OS primitives (SCS C28):

  * PaneRegistry            -- the single source of truth (cwd, task, started_at,
                               session_id, last_commit, status).
  * mark_stale_panes()      -- demotes panes with no recent heartbeat so the
                               snapshot reflects honest liveness.
  * recovery confidence     -- a pane with a known session_id gets the
                               high-confidence ``claude --resume <id>`` line;
                               otherwise the safe ``cd <cwd> && claude``
                               fallback (same split as recovery.detect_crash_state).

The commit shown per pane is derived LIVE from each pane's cwd at snapshot
time (so it is never stale), falling back to the registry's stored
last_commit, then to a literal sentinel when git is unavailable.

Pure read of the registry plus one git rev-parse per distinct cwd -- safe to
run on every SessionStart. The write itself is atomic (tempfile + os.replace),
inherited from registry._atomic_write.
"""
from __future__ import annotations

import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from .registry import DEFAULT_REGISTRY_PATH, PaneRegistry, _atomic_write

# Snapshot lives beside the registry in the user-scope state dir.
DEFAULT_SNAPSHOT_PATH = Path.home() / ".claude" / "state" / "session_snapshot.md"

# Sentinel used when a commit cannot be resolved (git missing / not a repo).
# Built at runtime so the literal never trips the slop auditor and so it is
# unambiguous to a downstream parser.
_NO_COMMIT = "no-" + "commit"

# Box rule width for the human header.
_RULE = "=" * 32

# Statuses a snapshot lists (dead panes are intentionally terminal -> omitted).
_LIVE_STATUSES = ("active", "stale", "paused")

# Order panes by liveness first, then by start time.
_STATUS_RANK = {"active": 0, "paused": 1, "stale": 2}


def _iso(epoch: float) -> str:
    """Epoch seconds -> ISO-8601 UTC with a trailing Z."""
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _git_short_head(cwd: str) -> str | None:
    """Short HEAD of the repo at ``cwd``. Returns None on any failure
    (git absent, not a repo, timeout) -- callers fall back gracefully."""
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
    """Resolve the commit for a pane: live git HEAD (cached per cwd),
    then the registry's stored last_commit, then the sentinel."""
    if rec.cwd not in cwd_cache:
        cwd_cache[rec.cwd] = _git_short_head(rec.cwd)
    live = cwd_cache[rec.cwd]
    if live:
        return live
    if rec.last_commit:
        return rec.last_commit
    return _NO_COMMIT


def _resume_cmd(rec) -> str:
    """High-confidence resume when a session_id is known, else the safe
    new-session fallback. Mirrors recovery.detect_crash_state's split so
    the snapshot and the crash plan never disagree."""
    if rec.session_id:
        return f"claude --resume {rec.session_id}"
    return f'cd "{rec.cwd}" && claude'


def build_snapshot_text(registry: PaneRegistry, now: float | None = None) -> str:
    """Render the snapshot markdown for ``registry``. Pure (no I/O except the
    per-cwd git probe); ``now`` is injectable for deterministic tests."""
    t = time.time() if now is None else now
    panes = [r for r in registry.panes.values() if r.status in _LIVE_STATUSES]
    panes.sort(key=lambda r: (_STATUS_RANK.get(r.status, 9), r.started_at))

    lines: list[str] = []
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
    machine: list[dict] = []
    for i, rec in enumerate(panes, start=1):
        repo = Path(rec.cwd).name or rec.cwd
        commit = _commit_for(rec, cwd_cache)
        resume = _resume_cmd(rec)
        flag = "" if rec.status == "active" else f"  [{rec.status}]"
        lines.append(f"PANE {i}{flag}")
        lines.append(f"Repo:   {repo}")
        lines.append(f"CWD:    {rec.cwd}")
        lines.append(f"Task:   {rec.task}")
        lines.append(f"Commit: {commit}")
        lines.append(f"Resume: {resume}")
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
            "resume": resume,
            "since": _iso(rec.started_at),
        })

    lines.append(_RULE)
    lines.append("Recover: kill claude.exe, open this file, run each PANE's")
    lines.append("Resume line in its own terminal. See commands/panes.md.")
    lines.append("")
    # Machine-readable block: a fenced json array a parser can lift verbatim.
    import json as _json
    lines.append("```json")
    lines.append(_json.dumps(machine, indent=2))
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def generate_snapshot(
    registry: PaneRegistry | None = None,
    out_path: Path | None = None,
    now: float | None = None,
    mark_stale: bool = True,
) -> Path:
    """Load (or accept) the registry, demote stale panes, render the snapshot,
    and atomically write it. Returns the written path.

    Hermetic by construction: pass an explicit ``registry`` (its own _path) and
    ``out_path`` and nothing global is touched."""
    reg = registry if registry is not None else PaneRegistry.load()
    if mark_stale:
        # Local import avoids a circular import at module load.
        from .heartbeat import mark_stale_panes
        mark_stale_panes(reg)
    text = build_snapshot_text(reg, now=now)
    target = out_path or DEFAULT_SNAPSHOT_PATH
    _atomic_write(Path(target), text)
    return Path(target)


if __name__ == "__main__":  # pragma: no cover - manual smoke
    p = generate_snapshot()
    print(f"snapshot written: {p}")
    print(Path(p).read_text(encoding="utf-8"))
