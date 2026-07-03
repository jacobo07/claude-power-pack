#!/usr/bin/env python3
"""
GK-08 Session Writeback — enrich the knowledge graph at session close.

A Stop hook. At session end it re-indexes the CURRENT repo into the central
store (global_store) so any knowledge file created or changed this session
becomes navigable in the NEXT session — this closes the WRITE -> READ -> ACT
loop: session_writeback WRITES the graph, the GK-12 Graph-First gate READS it,
navigation ACTS on it. A writer with no reader is documentation; here the
reader is the gate, so the cycle is whole.

Honest + bounded (GK-08's registered residual is "a silently-closed session"):
  - Fail-open ABSOLUTE: it NEVER blocks Stop. Any error -> a logged note and
    exit 0. A hook that stalls session close is worse than a stale graph.
  - Bounded: a full re-index hashes + parses every markdown node. For a
    29k-node repo that is far too slow for a Stop hook, so a repo with more than
    MAX_MD_FILES markdown files is SKIPPED with a logged "deferred" verdict
    (those refresh via the scheduled `indexer --all`). The skip is recorded,
    never silent — the residual is measured, per GK-12.
  - Cheap pre-check: counts markdown files with an early bail at the cap, so a
    huge repo costs a bounded directory walk, not a full parse.

Reads {cwd, session_id} from the Stop JSON on stdin. Also callable as
writeback(cwd) for tests.
"""

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import global_store as gs  # noqa: E402
# graphify_knowledge is importable because global_store put tools/ on sys.path.
import graphify_knowledge as gk  # noqa: E402

MAX_MD_FILES = 4000  # above this a Stop-time full re-index is too slow -> defer


def _log(payload: dict) -> None:
    """Append a one-line writeback receipt to the state dir. Best-effort."""
    try:
        d = gs.state_dir()
        d.mkdir(parents=True, exist_ok=True)
        payload["at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with open(d / "writeback.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except OSError:
        pass  # logging must never break Stop


def _md_count_capped(root: Path, cap: int) -> int:
    """Count markdown files under root (skipping generated/vendored dirs), with
    an early bail once the count passes cap — bounded cost on a huge repo."""
    n = 0
    for dpath, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in gk.SKIP_DIRS and not d.startswith(".")]
        for f in files:
            if f.endswith(".md"):
                n += 1
                if n > cap:
                    return n
    return n


def writeback(cwd, quiet: bool = True) -> dict:
    """Re-index cwd into the central store if it is within the size bound.
    Returns a verdict dict; never raises."""
    try:
        rp = Path(cwd)
        if not rp.is_dir():
            return {"verdict": "skip", "reason": "cwd not a dir", "repo": str(cwd)}

        md = _md_count_capped(rp, MAX_MD_FILES)
        if md > MAX_MD_FILES:
            return {"verdict": "deferred", "reason": f"{md}+ md files > {MAX_MD_FILES} cap",
                    "repo": str(rp), "hint": "refresh via 'indexer --all'"}

        res = gs.index_repo(rp, quiet=quiet)
        return {"verdict": "indexed" if res.get("ok") else "error",
                "repo": res.get("repo", str(rp)),
                "nodes": res.get("nodes"), "promoted": res.get("promoted"),
                "error": res.get("error")}
    except Exception as e:  # fail-open absolute
        return {"verdict": "error", "reason": str(e), "repo": str(cwd)}


def main() -> int:
    raw = ""
    try:
        raw = sys.stdin.read()
    except OSError:
        raw = ""
    data = {}
    try:
        data = json.loads(raw or "{}")
    except (json.JSONDecodeError, ValueError):
        data = {}

    cwd = data.get("cwd") or os.getcwd()
    verdict = writeback(cwd)
    verdict["session_id"] = data.get("session_id", "")
    _log(verdict)
    # Stop hooks emit optional JSON; we never block, so an empty object is fine.
    try:
        sys.stdout.write("{}")
    except OSError:
        pass
    return 0  # ALWAYS exit 0 — GK-08 never blocks session close


if __name__ == "__main__":
    sys.exit(main())
