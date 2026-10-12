"""Candidate snapshots on git objects (spec D23, R02; Phase 4).

A candidate is the tree object of the declared scope as it is on disk right now, written
through a throwaway index so the repository's own index, HEAD and refs are never touched.
The oid lives in the repository's object database: there is no copy store. Any doubt
(not a repo, a path that escapes the root, git failing, an empty scope) gives an
`unknown:` id and never raises, so every consumer falls back to the whole-tree / FULL path.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from .git_state import GIT_CANDIDATES

EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbbf4904"
UNKNOWN_PREFIX = "unknown:"


def _unknown(why: str) -> str:
    return f"{UNKNOWN_PREFIX}candidate:{why}"


def _run(root: Path, index: Path, *args: str) -> tuple[int, str]:
    env = dict(os.environ, GIT_INDEX_FILE=str(index))
    for exe in GIT_CANDIDATES:
        try:
            p = subprocess.run([exe, "-C", str(root), *args], capture_output=True, text=True,
                               timeout=60, stdin=subprocess.DEVNULL, env=env)
        except (OSError, subprocess.SubprocessError):
            continue
        return p.returncode, (p.stdout or "").strip()
    return 127, ""


def _scoped(paths) -> list[str] | None:
    """Root-relative POSIX paths, or None when any path is empty, absolute or escapes the root."""
    out: list[str] = []
    for raw in paths or []:
        p = str(raw).replace("\\", "/").strip()
        parts = p.split("/")
        if not p or p.startswith("/") or (len(p) > 1 and p[1] == ":") or ".." in parts:
            return None
        out.append(p)
    return out or None


def snapshot(root, paths) -> str:
    """The git tree oid of `paths` under `root` as it is now, or an `unknown:` id."""
    rel = _scoped(paths)
    if rel is None:
        return _unknown("scope")
    root = Path(root)
    if not root.is_dir():
        return _unknown("root")
    tmp = Path(tempfile.mkdtemp(prefix="cand-idx-"))
    try:
        index = tmp / "index"
        rc, _ = _run(root, index, "add", "-A", "--", *rel)
        if rc != 0:
            return _unknown("add")
        rc, out = _run(root, index, "write-tree")
        if rc != 0 or len(out) != 40:
            return _unknown("write-tree")
        if out == EMPTY_TREE:
            return _unknown("empty")
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def drift(promoted: dict, current_oid: str):
    """True when the candidate moved since `candidate.promoted`, False when it did not, and
    None when either side is unknown (unknown is never read as unchanged)."""
    was = (promoted or {}).get("tree")
    if not was or not current_oid:
        return None
    if str(was).startswith(UNKNOWN_PREFIX) or str(current_oid).startswith(UNKNOWN_PREFIX):
        return None
    return was != current_oid
