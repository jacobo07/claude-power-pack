"""Canonical repository identity for per-repo state.

THE DEFECT THIS CLOSES
----------------------
Per-repo ledgers -- FD deposits, UKDL candidates, FD-04 proofs -- are named by
slugging the session's current working directory. So one version-control
repository is one identity only for as long as nobody changes directory inside
it. `cd` into a subdirectory and the same repository acquires a second identity,
with its own empty ledger, and the reporter truthfully answers zero for a key
under which nothing was ever written.

Measured 2026-09-05: `KobiiRestore/` is not a separate version-control root, so
a session working there is the same repository as its parent and was writing --
and reading -- under a different key.

WHAT WAS NOT THE DEFECT
-----------------------
An earlier diagnosis held that two components of one hook chain derived the key
differently. That was falsified by reading them: identical expression,
byte-identical encoders, adjacent entries in one chain. It came from calling the
reporter with a hand-chosen key and observing it report zero -- an instrument
that could only confirm the hypothesis it was built to test. See INC-025.

COMPATIBILITY
-------------
`repo_key` of a repository ROOT is byte-identical to what the old encoder
produced for a session sitting at that root, so every existing path-keyed ledger
keeps its name and nothing is migrated. What changes is that a session in a
SUBDIRECTORY now resolves to the same key instead of inventing a new one.

Historical keys are read, never written. One repository in this estate carries a
ledger under an older bare-name scheme; `ledger_paths` unions it in so its
contents stay visible, and new deposits land under the canonical key only.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

# The encoder, unchanged from fd_07_flywheel._deposits_path and
# federated_ledger._slug. Deliberately not "improved": changing it would rename
# every ledger on disk, which is a migration, and this is not one.
_ENCODE = re.compile(r"[^a-zA-Z0-9]")

# What marks a version-control root. A worktree's `.git` is a FILE, not a
# directory, so both are accepted -- a check for `is_dir()` alone would send
# every worktree back to per-directory identity, silently.
_VCS_MARKERS = (".git", ".hg", ".svn")


def _encode(text: str) -> str:
    return _ENCODE.sub("-", text or "")


def canonical_repo(path: str | os.PathLike | None = None) -> str:
    """The version-control root containing `path`, as an absolute string.

    Falls back to the resolved path itself when nothing above it is a
    repository. That fallback is deliberate and is the pre-existing behaviour
    for non-repository directories: it keeps their state separate rather than
    collapsing every loose directory into one shared bucket.
    """
    if path is None:
        start = Path(os.getcwd())
    else:
        start = Path(path)
        # A caller that passed something which is not an existing absolute path
        # gets it back untouched. `Path.resolve()` would happily turn a bare
        # label like "myrepo" into "<cwd>/myrepo", inventing a key that no
        # existing ledger is filed under -- which is this module's own defect
        # committed in the act of fixing it.
        if not start.is_absolute() or not start.exists():
            return str(path)

    try:
        start = start.resolve()
    except OSError:
        # An unresolvable path is still a usable key; it just cannot be walked.
        return str(start)

    if start.is_file():
        start = start.parent

    for candidate in (start, *start.parents):
        for marker in _VCS_MARKERS:
            if (candidate / marker).exists():
                return str(candidate)
    return str(start)


def repo_key(path: str | os.PathLike | None = None) -> str:
    """The filename slug for a repository's per-repo state."""
    return _encode(canonical_repo(path))


def legacy_keys(path: str | os.PathLike | None = None) -> list[str]:
    """Keys that may hold this repository's history under an older scheme.

    Read-only. Two shapes are recognised:

    - the slug of the working directory itself, when it is not the repository
      root, which is what a subdirectory session used to write under;
    - the slug of the repository's bare name, which is what an earlier scheme
      used before keys became paths.

    The bare-name form can collide: two repositories sharing a directory name
    share the key. That flaw belongs to the historical scheme and is the reason
    these keys are never written to -- reading a colliding ledger shows a
    superset, which is visible and recoverable, while writing into one would
    merge two repositories' histories irreversibly.
    """
    canonical = canonical_repo(path)
    here = str(Path(path).resolve()) if path else os.getcwd()

    keys: list[str] = []
    if here != canonical:
        keys.append(_encode(here))

    bare = Path(canonical).name
    if bare and _encode(bare) != _encode(canonical):
        keys.append(_encode(bare))

    canonical_encoded = _encode(canonical)
    seen = {canonical_encoded}
    unique: list[str] = []
    for key in keys:
        if key not in seen:
            seen.add(key)
            unique.append(key)
    return unique


class PortableIdUnknown(ValueError):
    """No portable identity can be established -- never a made-up one."""


_GIT_CANDIDATES = (r"C:\Program Files\Git\cmd\git.exe", "git")


def _git(root: Path, *args: str) -> tuple[int, str]:
    import subprocess  # noqa: PLC0415 -- only the portable id needs a subprocess
    for exe in _GIT_CANDIDATES:
        try:
            p = subprocess.run([exe, "-C", str(root), *args], capture_output=True,
                               text=True, timeout=30, stdin=subprocess.DEVNULL)
        except (OSError, subprocess.SubprocessError):
            continue
        return p.returncode, (p.stdout or "").strip()
    return 127, ""


def portable_repo_id(path: str | os.PathLike) -> str:
    """The repository's identity ACROSS HOSTS: its single root commit.

    `repo_key` is a path slug, which is right for ledgers that live on one host
    and wrong for anything another machine must find: the same repository is
    `C--Users-...` on Windows and `-home-kobii-...` on a Linux node. A Workstream
    whose log lives on one host and runs on another needs the id both agree on.

    Refused rather than guessed:
      * no commits / not a repository;
      * more than one root commit (unrelated histories merged): no single id;
      * a SHALLOW clone: `rev-list --max-parents=0` answers with the shallow
        boundary, a commit that is not the root and differs per clone depth, so
        two clones of one repository would get two ids.
    """
    root = Path(path)
    rc, shallow = _git(root, "rev-parse", "--is-shallow-repository")
    if rc == 0 and shallow == "true":
        raise PortableIdUnknown(f"{root}: shallow clone; its boundary is not a root commit")
    rc, out = _git(root, "rev-list", "--max-parents=0", "HEAD")
    roots = [ln for ln in out.splitlines() if ln.strip()]
    if rc != 0 or not roots:
        raise PortableIdUnknown(f"{root}: not a git repository with commits (rc={rc})")
    if len(roots) > 1:
        raise PortableIdUnknown(f"{root}: {len(roots)} root commits; identity is ambiguous")
    return roots[0]


def ledger_paths(state_dir: str | os.PathLike, prefix: str,
                 path: str | os.PathLike | None = None) -> list[Path]:
    """Every file that may hold this repository's `prefix` ledger.

    The canonical path first -- it is the one written to, and it is returned
    whether or not it exists yet, because a caller appending needs a
    destination. Legacy paths follow, and only when they are actually on disk:
    returning a path for every historical scheme a repository never used would
    make the union look richer than it is.
    """
    root = Path(state_dir)
    paths = [root / f"{prefix}_{repo_key(path)}.jsonl"]
    for key in legacy_keys(path):
        candidate = root / f"{prefix}_{key}.jsonl"
        if candidate.is_file():
            paths.append(candidate)
    return paths
