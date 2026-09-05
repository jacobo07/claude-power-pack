#!/usr/bin/env python3
"""Two-way proof for canonical repository identity (2026-09-05).

WHAT WAS WRONG
--------------
Per-repo ledgers are named by slugging the session's working directory, so one
version-control repository is one identity only until somebody changes
directory inside it. Measured: `KobiiRestore/` is not a separate version-control
root, so a session working there was the same repository writing -- and reading
-- under a different key, and the reporter truthfully answered zero for a key
under which nothing had ever been written.

WHAT WAS NOT WRONG
------------------
The earlier diagnosis, that two components of one hook chain derived the key
differently, is retracted. Identical expression, byte-identical encoders,
adjacent entries in one chain. It came from calling the reporter with a
hand-chosen key and watching it report zero.

WHAT THESE CLAUSES DRIVE
------------------------
Both directions, because a canonicaliser that collapsed every path to one key
would also make the subdirectory case pass. So there are clauses proving two
DIFFERENT repositories stay apart, and clauses proving the encoder is unchanged
for a root -- if it were not, every ledger on disk would silently be renamed and
its history would read as zero, which is the very failure being fixed.

Run: python tools/test_repo_identity.py
Exit 0 iff every clause passes. Prints REPO_IDENTITY=<pass>/<total>.
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from modules.repo_identity import identity as ri  # noqa: E402

PASSES: list[str] = []
FAILURES: list[str] = []


def _ok(name: str, evidence: str) -> None:
    PASSES.append(name)
    print(f"  [PASS] {name}: {evidence}")


def _fail(name: str, diagnostic: str) -> None:
    FAILURES.append(name)
    print(f"  [FAIL] {name}: {diagnostic}")


def _check(name: str, condition: bool, evidence: str, diagnostic: str) -> None:
    _ok(name, evidence) if condition else _fail(name, diagnostic)


def main() -> int:
    print("=== Canonical repository identity ===\n")

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp).resolve()

        # A repository with a nested subdirectory, and a second, separate one.
        repo_a = base / "project-alpha"
        (repo_a / ".git").mkdir(parents=True)
        nested = repo_a / "Component" / "src"
        nested.mkdir(parents=True)

        repo_b = base / "project-beta"
        (repo_b / ".git").mkdir(parents=True)

        # A worktree, whose .git is a FILE rather than a directory.
        worktree = base / "project-alpha-wt"
        worktree.mkdir()
        (worktree / ".git").write_text("gitdir: /elsewhere\n", encoding="utf-8")

        loose = base / "not-a-repository"
        loose.mkdir()

        # ---- the defect ------------------------------------------------
        _check("V-REPOIDENT-SUBDIR-SAME-KEY",
               ri.repo_key(nested) == ri.repo_key(repo_a),
               f"a session in Component/src keys as {ri.repo_key(repo_a)}",
               f"subdirectory keyed {ri.repo_key(nested)}, root keyed "
               f"{ri.repo_key(repo_a)} -- the defect is not fixed")

        _check("V-REPOIDENT-SUBDIR-SAME-ROOT",
               ri.canonical_repo(nested) == str(repo_a),
               f"resolves to {repo_a}",
               f"resolved to {ri.canonical_repo(nested)}")

        # ---- and the opposite direction, which a collapsing bug would fail
        _check("V-REPOIDENT-DIFFERENT-REPOS-STAY-APART",
               ri.repo_key(repo_a) != ri.repo_key(repo_b),
               "two repositories keep two identities",
               "two different repositories collapsed to one key")

        _check("V-REPOIDENT-LOOSE-DIR-KEEPS-ITS-OWN-KEY",
               ri.canonical_repo(loose) == str(loose),
               "a directory under no repository keys as itself, rather than "
               "every loose directory sharing one bucket",
               f"resolved to {ri.canonical_repo(loose)}")

        # ---- a worktree is a repository ---------------------------------
        _check("V-REPOIDENT-WORKTREE-MARKER-IS-A-FILE",
               ri.canonical_repo(worktree) == str(worktree),
               "a .git FILE marks a root; an is_dir() check would silently send "
               "every worktree back to per-directory identity",
               f"resolved to {ri.canonical_repo(worktree)}")

        # ---- compatibility: the encoder is unchanged for a root ----------
        old_encoder = re.sub(r"[^a-zA-Z0-9]", "-", str(repo_a))
        _check("V-REPOIDENT-ROOT-KEY-IS-BYTE-IDENTICAL-TO-THE-OLD-ONE",
               ri.repo_key(repo_a) == old_encoder,
               "existing path-keyed ledgers keep their names and nothing is "
               "migrated",
               f"new {ri.repo_key(repo_a)} != old {old_encoder} -- every ledger "
               f"on disk would be silently renamed and read as empty")

        # ---- a non-path caller is not rewritten -------------------------
        _check("V-REPOIDENT-A-BARE-LABEL-IS-RETURNED-UNTOUCHED",
               ri.canonical_repo("myrepo") == "myrepo"
               and ri.repo_key("myrepo") == "myrepo",
               "a caller passing something that is not an existing absolute "
               "path keeps its key, because resolving it would invent an "
               "address no ledger is filed under",
               f"'myrepo' became {ri.canonical_repo('myrepo')!r}")

        missing = base / "was-deleted"
        _check("V-REPOIDENT-A-VANISHED-PATH-KEEPS-ITS-KEY",
               ri.repo_key(missing) == re.sub(r"[^a-zA-Z0-9]", "-", str(missing)),
               "a repository that no longer exists on disk still addresses its "
               "own history rather than being re-keyed to its parent",
               f"{missing} keyed as {ri.repo_key(missing)}")

        # ---- legacy keys, read only -------------------------------------
        legacy = ri.legacy_keys(nested)
        _check("V-REPOIDENT-SUBDIR-IS-A-LEGACY-KEY",
               re.sub(r"[^a-zA-Z0-9]", "-", str(nested)) in legacy,
               "what a subdirectory session used to write under is still read",
               f"legacy keys were {legacy}")

        _check("V-REPOIDENT-BARE-NAME-IS-A-LEGACY-KEY",
               "project-alpha" in ri.legacy_keys(repo_a),
               "the older bare-name scheme is still read",
               f"legacy keys were {ri.legacy_keys(repo_a)}")

        _check("V-REPOIDENT-CANONICAL-IS-NEVER-ITS-OWN-LEGACY",
               ri.repo_key(repo_a) not in ri.legacy_keys(repo_a),
               "the canonical key is not listed as legacy, so a union cannot "
               "read the same ledger twice and double every count",
               "the canonical key appeared in its own legacy list")

        # ---- the union --------------------------------------------------
        state = base / "state"
        state.mkdir()
        canonical_file = state / f"deposits_{ri.repo_key(repo_a)}.jsonl"
        bare_file = state / "deposits_project-alpha.jsonl"

        paths = ri.ledger_paths(state, "deposits", repo_a)
        _check("V-REPOIDENT-UNION-RETURNS-THE-DESTINATION-EVEN-WHEN-ABSENT",
               paths and paths[0] == canonical_file,
               "an appending caller always has somewhere to write",
               f"first path was {paths[0] if paths else '(none)'}")

        _check("V-REPOIDENT-UNION-OMITS-LEGACY-FILES-THAT-DO-NOT-EXIST",
               len(paths) == 1,
               "a repository that never used the old scheme does not get a "
               "phantom path that would make the union look richer than it is",
               f"union was {[p.name for p in paths]} with nothing on disk")

        bare_file.write_text('{"claim":"historical"}\n', encoding="utf-8")
        paths_now = ri.ledger_paths(state, "deposits", repo_a)
        _check("V-REPOIDENT-UNION-PICKS-UP-A-REAL-LEGACY-FILE",
               bare_file in paths_now and paths_now[0] == canonical_file,
               "history under the older scheme stays visible, and the canonical "
               "path stays first so writes never land in it",
               f"union was {[p.name for p in paths_now]}")

        canonical_file.write_text('{"claim":"current"}\n', encoding="utf-8")
        _check("V-REPOIDENT-UNION-FROM-A-SUBDIRECTORY-SEES-THE-ROOT-LEDGER",
               canonical_file in ri.ledger_paths(state, "deposits", nested),
               "the false zero is closed: a session in a subdirectory now reads "
               "the repository's own deposits",
               "a subdirectory session still could not see the root ledger")

    total = len(PASSES) + len(FAILURES)
    print(f"\nREPO_IDENTITY={len(PASSES)}/{total}  threshold={total}/{total}")
    return 0 if not FAILURES else 1


if __name__ == "__main__":
    raise SystemExit(main())
