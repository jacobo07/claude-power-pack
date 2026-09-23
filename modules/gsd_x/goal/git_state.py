#!/usr/bin/env python3
"""What tree is this evidence about? -- and the pin that says which gate ran.

A verdict has to name the state it was taken against, or it cannot be told
apart from one taken last week. Two honest answers exist and they are kept
distinguishable rather than blurred into one number:

    git:<tree-oid>   the scope is committed and clean; the canonical answer
    work:<hash>      the scope has uncommitted content; a real state, but one
                     no commit names, so it says so

Collapsing them would let evidence gathered on a dirty worktree read as
evidence about a commit, which is the tree-hash rule with the safety removed.
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

GIT_CANDIDATES = (r"C:\Program Files\Git\cmd\git.exe", "git")


def _git(root: Path, *args: str) -> tuple[int, str]:
    for exe in GIT_CANDIDATES:
        try:
            p = subprocess.run([exe, "-C", str(root), *args], capture_output=True,
                               text=True, timeout=60, stdin=subprocess.DEVNULL)
        except (OSError, subprocess.SubprocessError):
            continue
        return p.returncode, (p.stdout or "").rstrip("\n")
    return 127, ""


def head(root: Path) -> str:
    rc, out = _git(Path(root), "rev-parse", "HEAD")
    return out if rc == 0 else ""


def _dirty(root: Path, paths: list[str] | None) -> bool:
    args = ["status", "--porcelain", "--"] + list(paths or ["."])
    rc, out = _git(Path(root), *args)
    return rc != 0 or bool(out.strip())


def file_pin(root: Path, files: list[str]) -> tuple:
    """((path, sha256), ...) for the gate's own files, sorted.

    This is what an obligation pins at acceptance. A gate whose script or tests
    changed afterwards is a different gate, and an honest re-run of a rewritten
    gate proves nothing about the one that was accepted.
    """
    root = Path(root)
    out = []
    for rel in sorted(set(files or [])):
        p = root / rel
        if not p.is_file():
            raise FileNotFoundError(f"gate file {rel} does not exist under {root}")
        out.append((rel, hashlib.sha256(p.read_bytes()).hexdigest()))
    if not out:
        raise ValueError("a gate pin needs at least one file")
    return tuple(out)


def tree_id(root: Path, paths: list[str] | None = None) -> str:
    """The identity of the state a verdict is about. Never an empty string:
    a tree we could not read is reported as `unknown:` so it cannot silently
    match another unknown."""
    root = Path(root)
    rc, oid = _git(root, "rev-parse", "HEAD^{tree}")
    if rc != 0 or not oid:
        return "unknown:not-a-git-tree"
    if not _dirty(root, paths):
        return f"git:{oid}"
    h = hashlib.sha256()
    for rel in sorted(paths or ["."]):
        p = root / rel
        files = [p] if p.is_file() else [q for q in p.rglob("*")
                                         if q.is_file() and ".git" not in q.parts]
        for f in sorted(files):
            h.update(f.relative_to(root).as_posix().encode("utf-8") + b"\0")
            h.update(hashlib.sha256(f.read_bytes()).digest())
    return f"work:{h.hexdigest()[:24]}"
