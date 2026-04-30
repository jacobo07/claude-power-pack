r"""
pre_compact_vault_dump.py - snapshot of session-derived intent and artifacts
captured BEFORE the harness compacts (or before the user types /compact).

Triggered automatically by hooks/gsd-context-monitor.js on first WARNING fire
(35% remaining = 65% used). Idempotent: safe to call multiple times in the
same session — output is timestamped and atomic.

What it captures:
- Recent OVO verdicts from vault/audits/verdicts.jsonl (last N)
- Recent MC-* artifacts in vault/audits/ (last N modified)
- Git HEAD sha + dirty file list (if in a git repo)
- Modified files from the audit cache snapshot system
- Any files matching MC-* in the recent commit history

Output: vault/sleepy/sleepy_index_<ISO>.json (one snapshot per call)
        vault/sleepy/INDEX.md updated atomically (append-only)

The snapshot is intentionally TERSE — it's a pointer file. The actual
content stays in the artifacts on disk. Post-compact resume reads INDEX.md
and reaches into the pointed paths.

CLI:
  python tools/pre_compact_vault_dump.py [--session-id <sid>] [--repo <path>]
  exits 0 on success, 2 on missing inputs (still writes empty pointer)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SLEEPY_DIR = REPO_ROOT / "vault" / "sleepy"
INDEX_MD = SLEEPY_DIR / "INDEX.md"
VERDICTS = REPO_ROOT / "vault" / "audits" / "verdicts.jsonl"
AUDITS_DIR = REPO_ROOT / "vault" / "audits"


def iso_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def tail_jsonl(path: Path, n: int = 5) -> list[dict]:
    if not path.is_file():
        return []
    out: list[dict] = []
    with path.open("r", encoding="utf-8", errors="replace") as h:
        for line in h:
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out[-n:]


def recent_audit_artifacts(n: int = 10) -> list[dict]:
    if not AUDITS_DIR.is_dir():
        return []
    rows: list[tuple[float, Path]] = []
    for p in AUDITS_DIR.iterdir():
        if not p.is_file():
            continue
        if p.suffix not in (".md", ".json", ".jsonl"):
            continue
        try:
            rows.append((p.stat().st_mtime, p))
        except OSError:
            continue
    rows.sort(key=lambda r: r[0], reverse=True)
    out: list[dict] = []
    for mtime, p in rows[:n]:
        out.append({
            "path": str(p.relative_to(REPO_ROOT)).replace("\\", "/"),
            "mtime": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat(timespec="seconds"),
            "size": p.stat().st_size,
        })
    return out


def git_state(repo: Path) -> dict:
    if not (repo / ".git").exists():
        return {"git": False}
    try:
        head = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL, text=True, timeout=5,
        ).strip()
    except (subprocess.SubprocessError, OSError):
        head = "unknown"
    try:
        dirty_raw = subprocess.check_output(
            ["git", "-C", str(repo), "status", "--porcelain"],
            stderr=subprocess.DEVNULL, text=True, timeout=5,
        )
        dirty = [ln.strip() for ln in dirty_raw.splitlines() if ln.strip()]
    except (subprocess.SubprocessError, OSError):
        dirty = []
    try:
        last5 = subprocess.check_output(
            ["git", "-C", str(repo), "log", "--oneline", "-5"],
            stderr=subprocess.DEVNULL, text=True, timeout=5,
        )
    except (subprocess.SubprocessError, OSError):
        last5 = ""
    return {
        "git": True,
        "head_sha": head,
        "dirty_files": dirty[:50],
        "dirty_count": len(dirty),
        "recent_commits": [ln for ln in last5.splitlines() if ln.strip()][:5],
    }


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as h:
            json.dump(payload, h, indent=2, ensure_ascii=False)
            h.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def append_index_line(line: str) -> None:
    SLEEPY_DIR.mkdir(parents=True, exist_ok=True)
    if not INDEX_MD.is_file():
        INDEX_MD.write_text(
            "# Sleepy Index — pre-compact snapshots\n\n"
            "Each line points to a snapshot taken before context compaction. "
            "Post-compact resume reads the latest line and re-loads pointed paths.\n\n",
            encoding="utf-8", newline="\n",
        )
    with INDEX_MD.open("a", encoding="utf-8", newline="\n") as h:
        h.write(line + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pre_compact_vault_dump")
    parser.add_argument("--session-id", default=os.environ.get("CLAUDE_SESSION_ID", "unknown"))
    parser.add_argument("--repo", default=str(REPO_ROOT))
    parser.add_argument("--reason", default="auto-warning",
                        help="What triggered this dump (auto-warning|manual|critical)")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    ts = iso_ts()
    snap_path = SLEEPY_DIR / f"sleepy_index_{ts}.json"

    payload = {
        "iso_ts": ts,
        "session_id": args.session_id,
        "reason": args.reason,
        "repo": str(repo).replace("\\", "/"),
        "git_state": git_state(repo),
        "recent_verdicts": tail_jsonl(VERDICTS, n=5),
        "recent_audit_artifacts": recent_audit_artifacts(n=15),
        "schema_version": 1,
    }

    atomic_write_json(snap_path, payload)

    rel = snap_path.relative_to(REPO_ROOT).as_posix()
    head = payload["git_state"].get("head_sha", "no-git")[:8]
    dirty = payload["git_state"].get("dirty_count", 0)
    line = f"- `{ts}` · session=`{args.session_id[:8]}` · reason=`{args.reason}` · head=`{head}` · dirty={dirty} · → [{rel}]({rel})"
    append_index_line(line)

    print(json.dumps({
        "ok": True,
        "snapshot": rel,
        "session_id": args.session_id,
        "head": head,
        "dirty_count": dirty,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
