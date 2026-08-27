#!/usr/bin/env python3
"""
GK-10 Indexer — build the global knowledge store over all active repos.

Discovers the Owner's active repos from vault/terminal_slots.json (the live
pane/session registry), filters out ephemeral temp/test dirs, and indexes each
into the central store (modules/graphify/global_store.py). Runs standalone —
NO Claude Code needs to be active in a target repo — so every open session gets
graph data on its next Read, without a restart.

Usage:
    python -m modules.graphify.indexer --all
    python -m modules.graphify.indexer --repo "C:/path/to/repo"
    python -m modules.graphify.indexer --query --type dataset
    python -m modules.graphify.indexer --summary
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import global_store as gs  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SLOTS = _REPO_ROOT / "vault" / "terminal_slots.json"

# Ephemeral / non-project paths in terminal_slots (temp dirs + transient
# git worktrees the churn creates — not durable repos worth a global graph).
_EPHEMERAL = re.compile(
    r"(l3proj-|/temp/|appdata/local/temp|windows/temp|/users/kobig/"
    r"|/_wt-|/apps/_wt|-worktree|/apps/io-|/apps/tuax-|/apps/ude-|/apps/ds-)",
    re.IGNORECASE,
)


def _started(meta: dict):
    try:
        return datetime.fromisoformat(str(meta.get("started_at", "")).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def active_repos(slots_path: Path = _SLOTS, since_days: int = 7,
                 top_level: bool = True) -> list:
    """Return existing, non-ephemeral repos with a session in the last
    `since_days`. terminal_slots.json is a historical accumulator, so recency
    is what distinguishes 'currently active' from months of history. With
    top_level=True, a path nested under another kept repo is dropped (a repo is
    indexed once, not once per sub-path)."""
    if not slots_path.exists():
        return []
    try:
        data = json.loads(slots_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    seen: set = set()
    candidates: list = []
    for raw, meta in data.get("slots", {}).items():
        norm = str(raw).replace("\\", "/")
        if _EPHEMERAL.search(norm):
            continue
        if since_days:
            ts = _started(meta if isinstance(meta, dict) else {})
            if ts is None or ts < cutoff:
                continue
        p = Path(norm)
        try:
            if not p.is_dir():
                continue
            key = str(p.resolve()).replace("\\", "/").lower()
        except OSError:
            continue
        if key in seen:
            continue
        seen.add(key)
        candidates.append((key, str(p)))

    if not top_level:
        return [orig for _, orig in candidates]

    # Drop any path nested under another kept repo (index a repo once).
    kept: list = []
    for key, orig in sorted(candidates, key=lambda kv: len(kv[0])):
        if any(key.startswith(k.rstrip("/") + "/") for k, _ in kept):
            continue
        kept.append((key, orig))
    return [orig for _, orig in kept]


def deferred_repos(log_path=None) -> list:
    """Repos the GK-08 Stop hook skipped for size and never came back to.

    session_writeback caps a Stop-time index at MAX_MD_FILES and emits
    verdict="deferred" with hint "refresh via 'indexer --all'". That hint named
    a refresher that did not exist: --all discovers from terminal_slots.json
    with a 7-day recency window, so a big repo not opened inside the window is
    never revisited, and nothing scheduled --all at all. "deferred" was a
    terminal state wearing the word "temporary" -- KobiiSports Resort's
    CursorProjects sat at 0 nodes for a month while every component passed.

    The debt set is DISCOVERED from the append-only log, never curated: a
    hand-kept list of deferred repos measures memory, not reality. A repo is
    debt only when its LATEST verdict is deferred AND the store holds no
    later successful index (a --repo run repairs the store without writing
    the log, so the log alone would keep reporting a repo already fixed).
    """
    path = Path(log_path) if log_path else gs.state_dir() / "writeback.log"
    if not path.exists():
        return []
    latest: dict = {}
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            repo = row.get("repo")
            if repo:
                latest[str(repo)] = row  # append-only: last write wins
    except OSError:
        return []

    store = {}
    try:
        store = json.loads(
            (gs.state_dir() / "graphify_global.json").read_text(encoding="utf-8")
        ).get("repos", {})
    except (OSError, json.JSONDecodeError, ValueError):
        store = {}

    out = []
    for repo, row in latest.items():
        if row.get("verdict") != "deferred":
            continue
        if _EPHEMERAL.search(repo.replace("\\", "/")):
            continue
        try:
            if not Path(repo).is_dir():
                continue
        except OSError:
            continue
        deferred_at = str(row.get("at", ""))
        rec = store.get(gs.repo_id(repo), {})
        # Repaired out-of-band: the store was written after this deferral.
        if str(rec.get("indexed_at", "")) > deferred_at and rec.get("node_count"):
            continue
        out.append({"repo": repo, "reason": row.get("reason", ""),
                    "deferred_at": deferred_at,
                    "nodes_in_store": rec.get("node_count", 0)})
    return sorted(out, key=lambda r: r["repo"].lower())


def main():
    ap = argparse.ArgumentParser(description="GK-10 global cross-repo indexer")
    ap.add_argument("--all", action="store_true", help="index every active repo")
    ap.add_argument("--repo", default=None, help="index a single repo path")
    ap.add_argument("--query", action="store_true", help="query the global store")
    ap.add_argument("--type", default=None)
    ap.add_argument("--edge", default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("--cross-repo-only", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--list", action="store_true", help="list discovered active repos")
    ap.add_argument("--deferred", action="store_true",
                    help="name the repos the Stop hook deferred and never refreshed "
                         "(exit 1 when the debt set is non-empty)")
    ap.add_argument("--repair", action="store_true",
                    help="with --deferred: full-index every deferred repo (uncapped; "
                         "minutes per repo -- never run this from a hook)")
    args = ap.parse_args()

    if args.deferred:
        debt = deferred_repos()
        if not args.repair:
            print(json.dumps({"deferred": debt, "count": len(debt)}, indent=2))
            return 1 if debt else 0
        results = [gs.index_repo(d["repo"]) for d in debt]
        ok = [r for r in results if r.get("ok")]
        print(json.dumps({
            "repaired": len(ok), "attempted": len(results),
            "repos": [{"repo": r.get("repo"), "nodes": r.get("nodes"),
                       "promoted": r.get("promoted"), "error": r.get("error")}
                      for r in results],
            "remaining": len(deferred_repos()),
        }, indent=2))
        return 0 if len(ok) == len(results) else 1

    if args.list:
        repos = active_repos()
        print(json.dumps({"active_repos": repos, "count": len(repos)}, indent=2))
        return 0

    if args.summary:
        print(json.dumps(gs.summary(), indent=2))
        return 0

    if args.query:
        res = gs.query_global(node_type=args.type, edge_type=args.edge,
                              name=args.name, cross_repo_only=args.cross_repo_only)
        # Aggregate origin repos. `repos_represented` counts ADDRESSES and
        # was read as a cross-repo proof; `independent_roots` counts
        # ANCESTORS. On the live store the first is roughly three times the
        # second, because a claim copied into four repos was being counted
        # four times. Both are printed so the gap is visible at the surface
        # that made the claim, not buried in the store.
        repos_hit = sorted({s for r in res for s in ([r["scope"]] if r["scope"] != "global" else r["origins"])})
        roots = sum(r.get("independent_roots", 1) for r in res)
        echoed = [r["node_id"] for r in res if r.get("echoes")]
        print(json.dumps({"count": len(res), "repos_represented": repos_hit,
                          "independent_roots": roots,
                          "echoed_nodes": echoed[:20],
                          "results": res[:40]}, indent=2))
        return 0

    if args.repo:
        print(json.dumps(gs.index_repo(args.repo), indent=2))
        return 0

    if args.all:
        repos = active_repos()
        if not repos:
            print(json.dumps({"error": "no active repos discovered",
                              "slots_file": str(_SLOTS)}, indent=2))
            return 1
        results = gs.index_all(repos)
        ok = [r for r in results if r.get("ok")]
        print(json.dumps({
            "indexed": len(ok), "attempted": len(results),
            "repos": [{"repo": r["repo"], "nodes": r.get("nodes"),
                       "promoted": r.get("promoted"),
                       "types": r.get("types_present"),
                       "error": r.get("error")} for r in results],
            "global": gs.summary(),
        }, indent=2))
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
