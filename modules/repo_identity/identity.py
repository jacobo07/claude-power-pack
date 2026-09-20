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


def main_repo_root(path: str | os.PathLike | None = None) -> str:
    """The MAIN repository root, resolving a linked git worktree to the
    repository it belongs to.

    `canonical_repo` deliberately stops at the nearest version-control root, so
    a linked worktree keys its own state separately. That is right for a ledger
    and wrong for the question "which repository is this?" -- a worktree of
    claude-power-pack IS claude-power-pack, and a self-identification test that
    reads only the checkout path answers no for it.

    A linked worktree's `.git` is a FILE holding `gitdir: <main>/.git/worktrees/
    <name>`, so the main root is recoverable without invoking git. A relative
    gitdir (git's `--relative-paths`) is resolved against the worktree.

    Falls back to `canonical_repo(path)` for a normal checkout, an unreadable
    `.git`, or any shape not recognised -- never raises, and never guesses.
    """
    root = Path(canonical_repo(path))
    marker = root / ".git"
    try:
        if not marker.is_file():
            return str(root)
        text = marker.read_text(encoding="utf-8", errors="replace").strip()
        if not text.lower().startswith("gitdir:"):
            return str(root)
        gitdir = Path(text.split(":", 1)[1].strip())
        if not gitdir.is_absolute():
            gitdir = (root / gitdir).resolve()
        parts = gitdir.parts
        # .../<main-root>/.git/worktrees/<name>  -- cut at the ".git" component
        # that is followed by "worktrees"; anything else is not a linked
        # worktree layout and is left alone.
        for i in range(len(parts) - 1):
            if parts[i] == ".git" and parts[i + 1] == "worktrees":
                return str(Path(*parts[:i]))
    except (OSError, ValueError, IndexError):
        return str(root)
    return str(root)


# Structural marks of THIS repository, chosen because each is a subsystem the
# Power Pack owns rather than a name anyone could choose. A majority is
# required, not all of them, so renaming one subsystem degrades identity to
# "still recognised" rather than to "suddenly a stranger".
_PP_MARKS = (
    "modules/capability_runtime/contract.py",
    "vault/hard_rules/HARD_RULES.md",
    "modules/rule_compiler",
    "tools/hardrule_compile.py",
    "modules/uqf",
)
_PP_MARKS_REQUIRED = 3


def is_power_pack(path: str | os.PathLike | None = None) -> bool:
    """True when `path` belongs to the Claude Power Pack repository.

    Identity is read from the repository's CONTENTS, resolved through
    `main_repo_root` so a linked worktree answers for the repository it belongs
    to. A directory basename is a display name: two different repositories may
    share one, one repository may be checked out under several, and W3 measured
    the first half of that -- `C:/Users/User/Apps/pp-ucr-cif` IS the Power Pack
    and says nothing of the kind, so the Power Pack served itself an advisory
    written for other repositories.

    The mirror half is the one a substring test cannot answer at all: an
    unrelated repository living under a path that happens to contain
    "claude-power-pack" reads as the Power Pack forever, and no amount of
    additional substrings fixes a predicate that is asking the wrong question.

    Fail-closed on an unreadable root: unknown is not identity.
    """
    try:
        root = Path(main_repo_root(path))
        hits = sum(1 for m in _PP_MARKS if (root / m).exists())
    except (OSError, ValueError):
        return False
    return hits >= _PP_MARKS_REQUIRED


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
