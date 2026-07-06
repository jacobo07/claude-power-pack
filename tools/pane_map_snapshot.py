"""Pane-map versioning + Workspace Session Registry.

Companion to tools/build_pane_map.ps1. The PS builder writes the CURRENT
pane_map.json/.md (source = disk transcripts). This module VERSIONS that output:
timestamped snapshots under ~/.claude/state/pane_map_history/, a 7-day retention
prune, a set-difference diff between any two snapshots, and an append-only
Workspace Session Registry recording which repos held OPEN-NOW panes at each
snapshot instant.

Design (Reality Scan STOP #1, Owner-approved 2026-07-06):
  - Reuses G3's (modules/session_resilience/snapshot_versioning.py) PATTERN --
    atomic write + protected-retention + monotonic catalog -- but stores flat
    timestamped files, NOT a baseline+delta chain: the spec asks for
    pane_map_YYYYMMDD_HHMM.<ext> snapshots verbatim, and G3's diff() is coupled
    to session-resilience EXTRACTORS (tab/terminal dims) useless for pane diff.
  - Change detection = TOPOLOGY hash (set of sessionIds). A snapshot is written
    only when the pane SET changed AND >=15 min elapsed since the last snapshot
    (Owner decision 2: no duplicate files). Pure tier-aging does NOT trip a new
    snapshot; the diff still surfaces tier/topic changes between snapshots taken.
  - Workspace registry is written on the same gate ("por cada snapshot").
  - Standalone: repos_live is a NEW data source CO-12 telemetry MAY later consume
    (it does not reference it today -- premise corrected at STOP #1).

Hermetic: every entry point takes an explicit state_dir and an injectable `now`
so tests are deterministic and never touch the live ~/.claude/state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HISTORY_DIRNAME = "pane_map_history"
WORKSPACE_LOG = "workspace_sessions.jsonl"
INDEX_NAME = "_index.json"
SNAPSHOT_MIN_INTERVAL_MIN = 15
RETENTION_DAYS = 7
STAMP_FMT = "%Y%m%d_%H%M"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _default_state_dir() -> Path:
    return Path(os.path.expanduser("~")) / ".claude" / "state"


# --- atomic write (mirrors G3 _atomic_write_json semantics) -----------------

def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _read_json(path: Path):
    # utf-8-sig: pane_map.json is written by PowerShell UTF8Encoding($false) (no
    # BOM) but a sibling tool could re-save with one; -sig strips it either way.
    return json.loads(path.read_text(encoding="utf-8-sig"))


# --- change-detection signatures --------------------------------------------

def topology_hash(panes: list[dict]) -> str:
    """Signature of WHICH panes exist (sessionId set). A change here == a pane
    was opened or closed -- the primary 'qué panes se añadieron / cerraron' diff.
    Tier/topic changes deliberately do NOT alter this (they'd snapshot on pure
    aging); the diff presenter still reports them between snapshots taken."""
    ids = sorted(str(p.get("sessionId", "")) for p in panes)
    return hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()


def _open_now(panes: list[dict]) -> list[dict]:
    return [p for p in panes if p.get("tier") == "OPEN-NOW"]


def _workspace_signature(panes: list[dict]) -> tuple:
    repos = tuple(sorted({p.get("repo") for p in _open_now(panes) if p.get("repo")}))
    return (repos, len(_open_now(panes)))


# --- index (cheap last-snapshot lookup + catalog) ---------------------------

def _load_index(history_dir: Path) -> dict:
    p = history_dir / INDEX_NAME
    fresh = {"last_ts": None, "last_hash": None, "snapshots": []}
    if not p.is_file():
        return fresh
    try:
        return _read_json(p)
    except (json.JSONDecodeError, OSError):
        # corrupt / unreadable index -> rebuild fresh (fail-open; the next
        # snapshot re-establishes last_ts/last_hash). Never abort the build.
        return fresh


def _save_index(history_dir: Path, idx: dict) -> None:
    _atomic_write_text(history_dir / INDEX_NAME, json.dumps(idx, ensure_ascii=False, indent=2))


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


# --- gate -------------------------------------------------------------------

def should_snapshot(now: datetime, cur_hash: str, last_ts: datetime | None,
                    last_hash: str | None,
                    min_interval_min: int = SNAPSHOT_MIN_INTERVAL_MIN) -> tuple[bool, str]:
    if last_hash == cur_hash:
        return False, "unchanged"
    if last_ts is not None and (now - last_ts) < timedelta(minutes=min_interval_min):
        return False, "too-soon"
    return True, "changed"


# --- workspace session registry ---------------------------------------------

def _last_workspace_signature(log_path: Path) -> tuple | None:
    if not log_path.is_file():
        return None
    last = None
    for line in log_path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line:
            last = line
    if not last:
        return None
    try:
        e = json.loads(last)
        return (tuple(e.get("repos_live", [])), int(e.get("pane_count", 0)))
    except (json.JSONDecodeError, ValueError, TypeError):
        return None


def append_workspace(state_dir: Path, now: datetime, panes: list[dict],
                     snap_hash: str) -> bool:
    """Append a Workspace Session Registry line iff the live-repo set / count
    changed vs the previous line (dedup). Returns True if a line was written."""
    log_path = state_dir / WORKSPACE_LOG
    repos_live = sorted({p.get("repo") for p in _open_now(panes) if p.get("repo")})
    pane_count = len(_open_now(panes))
    sig = (tuple(repos_live), pane_count)
    if _last_workspace_signature(log_path) == sig:
        return False
    entry = {
        "timestamp": now.isoformat(),
        "repos_live": repos_live,
        "pane_count": pane_count,
        "session_hash": snap_hash,
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return True


# --- retention prune (never leave an orphan .md without its .json) -----------

def prune(history_dir: Path, idx: dict, now: datetime,
          retention_days: int = RETENTION_DAYS) -> list[str]:
    cutoff = now - timedelta(days=retention_days)
    removed: list[str] = []
    for f in list(history_dir.glob("pane_map_*")):
        if f.name == INDEX_NAME:
            continue
        stamp = f.stem.replace("pane_map_", "")
        try:
            ts = datetime.strptime(stamp, STAMP_FMT).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if ts < cutoff:
            try:
                f.unlink()
                removed.append(f.name)
            except OSError:
                # file locked / already gone -> leave it, retry next prune.
                # Not fatal: retention is best-effort, correctness is unaffected.
                continue
    if removed:
        rem = set(removed)
        idx["snapshots"] = [s for s in (idx.get("snapshots") or []) if s.get("file") not in rem]
    return removed


# --- take a snapshot --------------------------------------------------------

def take_snapshot(state_dir: Path | str, now: datetime | None = None,
                  min_interval_min: int = SNAPSHOT_MIN_INTERVAL_MIN,
                  retention_days: int = RETENTION_DAYS) -> dict:
    state_dir = Path(state_dir)
    now = now or _utcnow()
    pm_json = state_dir / "pane_map.json"
    if not pm_json.is_file():
        return {"created": False, "reason": "no-pane-map"}
    try:
        data = _read_json(pm_json)
    except (json.JSONDecodeError, OSError) as exc:
        return {"created": False, "reason": f"unreadable:{exc.__class__.__name__}"}
    panes = data.get("panes", [])
    history_dir = state_dir / HISTORY_DIRNAME
    idx = _load_index(history_dir)
    cur_hash = topology_hash(panes)
    do, reason = should_snapshot(now, cur_hash, _parse_iso(idx.get("last_ts")),
                                 idx.get("last_hash"), min_interval_min)
    if not do:
        return {"created": False, "reason": reason, "hash": cur_hash}

    stamp = now.strftime(STAMP_FMT)
    history_dir.mkdir(parents=True, exist_ok=True)
    snap_json = history_dir / f"pane_map_{stamp}.json"
    _atomic_write_text(snap_json, pm_json.read_text(encoding="utf-8-sig"))
    pm_md = state_dir / "pane_map.md"
    if pm_md.is_file():
        _atomic_write_text(history_dir / f"pane_map_{stamp}.md",
                           pm_md.read_text(encoding="utf-8-sig"))

    ws_written = append_workspace(state_dir, now, panes, cur_hash)

    idx.setdefault("snapshots", []).append(
        {"ts": now.isoformat(), "hash": cur_hash, "file": snap_json.name})
    idx["last_ts"] = now.isoformat()
    idx["last_hash"] = cur_hash
    removed = prune(history_dir, idx, now, retention_days)
    _save_index(history_dir, idx)
    return {"created": True, "file": snap_json.name, "hash": cur_hash,
            "workspace_written": ws_written, "pruned": removed}


# --- diff two snapshots -----------------------------------------------------

def _panes_by_id(data: dict) -> dict[str, dict]:
    return {str(p.get("sessionId", "")): p for p in data.get("panes", [])}


def diff_snapshots(older: dict, newer: dict) -> dict:
    """Set difference between two pane_map payloads: which panes opened, which
    closed, and -- for panes present in both -- tier/topic transitions."""
    a, b = _panes_by_id(older), _panes_by_id(newer)
    added = sorted(set(b) - set(a))
    closed = sorted(set(a) - set(b))
    tier_changed, topic_changed = [], []
    for sid in sorted(set(a) & set(b)):
        if a[sid].get("tier") != b[sid].get("tier"):
            tier_changed.append({"sessionId": sid, "from": a[sid].get("tier"),
                                 "to": b[sid].get("tier"), "repo": b[sid].get("repo")})
        if a[sid].get("topic") != b[sid].get("topic"):
            topic_changed.append({"sessionId": sid, "repo": b[sid].get("repo")})
    return {"added": [{"sessionId": s, "repo": b[s].get("repo"),
                       "topic": b[s].get("topic")} for s in added],
            "closed": [{"sessionId": s, "repo": a[s].get("repo"),
                        "topic": a[s].get("topic")} for s in closed],
            "tier_changed": tier_changed, "topic_changed": topic_changed}


def diff_files(path_a: Path | str, path_b: Path | str) -> dict:
    return diff_snapshots(_read_json(Path(path_a)), _read_json(Path(path_b)))


# --- CLI --------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Pane-map versioning + workspace registry")
    ap.add_argument("--snapshot", action="store_true", help="take a snapshot if changed & >=15min")
    ap.add_argument("--diff", nargs=2, metavar=("OLDER", "NEWER"), help="diff two snapshot json files")
    ap.add_argument("--state-dir", default=str(_default_state_dir()))
    args = ap.parse_args(argv)

    if args.diff:
        print(json.dumps(diff_files(args.diff[0], args.diff[1]), ensure_ascii=False, indent=2))
        return 0
    if args.snapshot:
        res = take_snapshot(args.state_dir)
        print(json.dumps(res, ensure_ascii=False))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
