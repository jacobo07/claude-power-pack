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


def commits_between(root: Path, before: str, after: str) -> list[str]:
    """Commits in before..after, oldest-last as git prints them.

    Through `_git`, never a hardcoded executable: a provider on a Linux host
    (the unattended Night Shift) raised FileNotFoundError at harvest when this
    was a Windows path spelled inline in three places."""
    if not before or not after or before == after:
        return []
    rc, out = _git(Path(root), "log", "--format=%H", f"{before}..{after}")
    return [c for c in out.split() if c] if rc == 0 else []


def _dirty(root: Path, paths: list[str] | None) -> bool:
    args = ["status", "--porcelain", "--"] + list(paths or ["."])
    rc, out = _git(Path(root), *args)
    return rc != 0 or bool(out.strip())


SHA256, BLOB = "sha256", "blob"
BLOB_PREFIX = "blob:"


def blob_oid(data: bytes) -> str:
    """git's blob id of `data` after line-ending normalization (UWCP S1-9).

    One committed file is CRLF on a Windows checkout and LF on a Linux node; a
    raw-byte hash gives it two identities, so a gate pinned on one host reads as
    "changed" on the other, and a failed attempt re-run there looks like new
    information. Text (no NUL in the first 8000 bytes -- git's own heuristic) is
    normalized to LF, then hashed as git hashes a blob, so the id equals what
    `git hash-object` reports for the normalized file on any host. Binary bytes
    are hashed untouched.
    """
    if b"\0" not in data[:8000]:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def file_digest(path: Path, scheme: str = SHA256) -> str:
    data = Path(path).read_bytes()
    if scheme == BLOB:
        return BLOB_PREFIX + blob_oid(data)
    if scheme == SHA256:
        return hashlib.sha256(data).hexdigest()
    raise ValueError(f"unknown pin scheme {scheme!r}")


def pin_scheme(pin) -> str:
    """The scheme a stored pin was taken in. Mixed pins are refused, not guessed."""
    kinds = {BLOB if str(d).startswith(BLOB_PREFIX) else SHA256 for _, d in (pin or ())}
    if len(kinds) > 1:
        raise ValueError(f"pin mixes digest schemes: {sorted(kinds)}")
    return kinds.pop() if kinds else SHA256


def digest_matches(path: Path, digest: str) -> bool:
    """Does the file still have `digest`, in whichever scheme it was taken?"""
    scheme = BLOB if str(digest).startswith(BLOB_PREFIX) else SHA256
    return file_digest(path, scheme) == digest


def file_pin(root: Path, files: list[str], scheme: str = SHA256) -> tuple:
    """((path, digest), ...) for the gate's own files, sorted.

    This is what an obligation pins at acceptance. A gate whose script or tests
    changed afterwards is a different gate, and an honest re-run of a rewritten
    gate proves nothing about the one that was accepted.

    `scheme` defaults to the historical raw sha256 so every stored pin keeps
    verifying; new obligations pin with BLOB (eol-invariant, portable across
    hosts), and a verdict is pinned in its obligation's scheme.
    """
    root = Path(root)
    out = []
    for rel in sorted(set(files or [])):
        p = root / rel
        if not p.is_file():
            raise FileNotFoundError(f"gate file {rel} does not exist under {root}")
        out.append((rel, file_digest(p, scheme)))
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
