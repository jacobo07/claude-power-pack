#!/usr/bin/env python3
"""Commit only the lines you wrote, in a file someone else is also writing.

WHY THIS EXISTS. Pathspec-scoped commits are the estate's standing defence
against concurrent writers, and they work -- until two writers are inside the
same file. Then the pathspec names a file containing both authors' hunks and
`git commit -- <path>` packages the other writer's uncommitted work under your
message. Measured 2026-09-11: a UKDL commit reported 467 insertions where about
85 were the session's own; 185 lines belonged to a concurrent capture system.
Both sides had followed the pathspec doctrine exactly. The unit of protection
was simply coarser than the collision.

THE MECHANISM. Authorship cannot be inferred from a diff, so it is recorded
instead. Before editing a contended file you take a SNAPSHOT of its exact bytes.
Everything already differing from HEAD at that moment is, by construction, not
yours. At commit time:

    index := worktree                      (your lines + theirs)
    index := index minus foreign-patch     (reverse-apply what predated you)
    index  = HEAD + your lines only

Their work is never touched: it stays uncommitted in the working tree exactly
as they left it, and their next commit carries it under their own message.

WHAT IT CANNOT DO. A writer who edits the file DURING your window is
indistinguishable from you, because nothing recorded the boundary. That is an
honest limit of a snapshot, not a bug, and it is why the outcome is reported as
FOREIGN_PRESERVED rather than "clean": the guard states what it subtracted, and
the operator can see whether that matches what they expected.

FAIL CLOSED. A file with no snapshot is REFUSED, not staged whole -- the whole
point is that you cannot prove which lines are yours, and a guard that falls
back to the unsafe default when uncertain is worse than no guard, because it
reports success. HEAD moving between snapshot and stage is likewise refused:
the recorded baseline no longer describes the tree.

OUTCOMES, with distinct exit codes, because a guard that broke and a guard that
refused your subject are different evidence:

    0  STAGED_CLEAN        no foreign delta existed; the whole file is yours
    0  FOREIGN_PRESERVED   foreign hunks subtracted from the index and verified
                           absent from the staged blob
    2  NOTHING_TO_STAGE    you changed nothing since the snapshot
    3  NO_BASE             never snapshotted, or the baseline is stale
    5  VERIFY_MISMATCH     the staged blob does not match what was intended
    4  GUARD_FAILED        the guard itself broke; says nothing about your files
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

STAGED_CLEAN = "STAGED_CLEAN"
FOREIGN_PRESERVED = "FOREIGN_PRESERVED"
NOTHING_TO_STAGE = "NOTHING_TO_STAGE"
NO_BASE = "NO_BASE"
VERIFY_MISMATCH = "VERIFY_MISMATCH"
GUARD_FAILED = "GUARD_FAILED"

EXIT = {
    STAGED_CLEAN: 0,
    FOREIGN_PRESERVED: 0,
    NOTHING_TO_STAGE: 2,
    NO_BASE: 3,
    GUARD_FAILED: 4,
    VERIFY_MISMATCH: 5,
}

_FALLBACK_GIT = r"C:\Program Files\Git\cmd\git.exe"


class GuardError(RuntimeError):
    """The guard could not do its job. Never a verdict about the subject."""


def git_exe() -> str:
    found = shutil.which("git")
    if found:
        return found
    if Path(_FALLBACK_GIT).exists():
        return _FALLBACK_GIT
    raise GuardError("git not found on PATH")


def git(repo: Path, *args: str, check: bool = True, binary: bool = False):
    proc = subprocess.run(
        [git_exe(), "-C", str(repo), *args],
        capture_output=True,
        check=False,
    )
    if check and proc.returncode != 0:
        raise GuardError(
            f"git {' '.join(args[:3])} failed ({proc.returncode}): "
            f"{proc.stderr.decode('utf-8', 'replace').strip()[:300]}"
        )
    return proc.stdout if binary else proc.stdout.decode("utf-8", "replace")


def guard_dir(repo: Path) -> Path:
    return repo / "vault" / "session_guard"


def _slug(rel: str) -> str:
    return hashlib.sha256(rel.encode("utf-8")).hexdigest()[:16]


def _rel(repo: Path, path: Path) -> str:
    return path.resolve().relative_to(repo.resolve()).as_posix()


def _head_blob(repo: Path, rel: str) -> bytes | None:
    """The file's content at HEAD, or None when HEAD does not carry it."""
    proc = subprocess.run(
        [git_exe(), "-C", str(repo), "show", f"HEAD:{rel}"],
        capture_output=True,
        check=False,
    )
    return proc.stdout if proc.returncode == 0 else None


def snapshot(repo: Path, paths: list[Path]) -> dict:
    """Record the bytes that predate your edits. Call BEFORE editing."""
    d = guard_dir(repo)
    d.mkdir(parents=True, exist_ok=True)
    head = git(repo, "rev-parse", "HEAD").strip()
    recorded = {}
    for p in paths:
        rel = _rel(repo, p)
        base = p.read_bytes() if p.exists() else b""
        slug = _slug(rel)
        (d / f"{slug}.base").write_bytes(base)
        meta = {
            "path": rel,
            "head": head,
            "base_sha256": hashlib.sha256(base).hexdigest(),
            "base_bytes": len(base),
        }
        # Written newline-pinned: a generated committed-adjacent artifact must
        # serialize identically on every platform (PR-DETERMINISTIC-SERIALIZATION-001).
        with open(d / f"{slug}.json", "w", encoding="utf-8", newline="\n") as fh:
            json.dump(meta, fh, indent=1, sort_keys=True)
            fh.write("\n")
        recorded[rel] = meta
    return recorded


def _load_meta(repo: Path, rel: str) -> dict | None:
    f = guard_dir(repo) / f"{_slug(rel)}.json"
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8"))


def _added_lines(patch: str) -> set:
    out = set()
    for line in patch.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            body = line[1:].strip()
            if body:
                out.add(body)
    return out


def _diff_blobs(repo: Path, old: bytes, new: bytes, rel: str) -> str:
    """A unified patch between two contents, addressed to `rel` so it can be
    applied to the index."""
    with tempfile.TemporaryDirectory() as td:
        a, b = Path(td) / "a", Path(td) / "b"
        a.write_bytes(old)
        b.write_bytes(new)
        proc = subprocess.run(
            [git_exe(), "-C", str(repo), "diff", "--no-index", "--no-color",
             "--src-prefix=a/", "--dst-prefix=b/", str(a), str(b)],
            capture_output=True, check=False,
        )
        raw = proc.stdout.decode("utf-8", "replace")
    if not raw.strip():
        return ""
    fixed = []
    for line in raw.splitlines():
        if line.startswith("--- "):
            fixed.append(f"--- a/{rel}")
        elif line.startswith("+++ "):
            fixed.append(f"+++ b/{rel}")
        elif line.startswith("diff --git "):
            fixed.append(f"diff --git a/{rel} b/{rel}")
        else:
            fixed.append(line)
    return "\n".join(fixed) + "\n"


def stage(repo: Path, paths: list[Path]) -> list[dict]:
    """Stage only the delta that postdates each file's snapshot."""
    results = []
    head_now = git(repo, "rev-parse", "HEAD").strip()
    for p in paths:
        rel = _rel(repo, p)
        meta = _load_meta(repo, rel)
        if meta is None:
            results.append({"path": rel, "outcome": NO_BASE,
                            "detail": "no snapshot recorded; authorship of the "
                                      "existing delta cannot be established"})
            continue
        if meta["head"] != head_now:
            results.append({"path": rel, "outcome": NO_BASE,
                            "detail": f"HEAD moved {meta['head'][:8]} -> "
                                      f"{head_now[:8]} since the snapshot"})
            continue

        base = (guard_dir(repo) / f"{_slug(rel)}.base").read_bytes()
        current = p.read_bytes() if p.exists() else b""
        mine = _diff_blobs(repo, base, current, rel)
        if not mine.strip():
            results.append({"path": rel, "outcome": NOTHING_TO_STAGE,
                            "detail": "file is byte-identical to its snapshot"})
            continue

        head_content = _head_blob(repo, rel)
        foreign = _diff_blobs(repo, head_content or b"", base, rel) if head_content is not None else ""

        git(repo, "add", "--", rel)
        if not foreign.strip():
            results.append({"path": rel, "outcome": STAGED_CLEAN,
                            "detail": "no delta predated the snapshot",
                            "foreign_lines": 0})
            continue

        with tempfile.TemporaryDirectory() as td:
            patch = Path(td) / "foreign.patch"
            with open(patch, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(foreign)
            proc = subprocess.run(
                [git_exe(), "-C", str(repo), "apply", "--cached", "--reverse",
                 "--unidiff-zero", str(patch)],
                capture_output=True, check=False,
            )
            if proc.returncode != 0:
                git(repo, "reset", "--quiet", "HEAD", "--", rel, check=False)
                results.append({
                    "path": rel, "outcome": VERIFY_MISMATCH,
                    "detail": "foreign hunks could not be separated from yours "
                              "(they interleave); index left untouched: "
                              + proc.stderr.decode("utf-8", "replace").strip()[:200],
                })
                continue

        # Verification. The property that matters is content-level, so assert
        # it directly on the staged blob rather than trusting the exit code of
        # the thing under test.
        staged = git(repo, "show", f":{rel}", binary=True)
        staged_text = staged.decode("utf-8", "replace")
        foreign_added = _added_lines(foreign)
        mine_added = _added_lines(mine)
        leaked = sorted(
            ln for ln in (foreign_added - mine_added)
            if ln in staged_text
        )
        dropped = sorted(
            ln for ln in (mine_added - foreign_added)
            if ln not in staged_text
        )
        if leaked or dropped:
            git(repo, "reset", "--quiet", "HEAD", "--", rel, check=False)
            results.append({
                "path": rel, "outcome": VERIFY_MISMATCH,
                "detail": f"{len(leaked)} foreign line(s) still staged, "
                          f"{len(dropped)} of yours missing; index reset",
            })
            continue

        results.append({
            "path": rel, "outcome": FOREIGN_PRESERVED,
            "detail": f"{len(foreign_added)} foreign added line(s) subtracted "
                      f"from the index and left in the working tree",
            "foreign_lines": len(foreign_added),
            "mine_lines": len(mine_added),
        })
    return results


# --------------------------------------------------------------------------
# Self-test. Real git, real concurrent edit, real reverse-apply. A simulated
# repository would prove only that the simulation agrees with itself.
# --------------------------------------------------------------------------

def _self_test() -> int:
    passes = fails = 0

    def ok(gate, cond, ev):
        nonlocal passes, fails
        if cond:
            passes += 1
            print(f"  OK   {gate}  {ev}")
        else:
            fails += 1
            print(f"  FAIL {gate}  {ev}")

    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        git(repo, "init", "--quiet")
        git(repo, "config", "user.email", "guard@test")
        git(repo, "config", "user.name", "guard")
        shared = repo / "shared.md"
        shared.write_text("line-committed-1\nline-committed-2\n",
                          encoding="utf-8", newline="\n")
        git(repo, "add", "-A")
        git(repo, "commit", "--quiet", "-m", "base")

        # Writer B lands uncommitted work FIRST. This is the 185 lines.
        with open(shared, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("FOREIGN-alpha\nFOREIGN-beta\n")

        # Now I arrive and snapshot before editing.
        snapshot(repo, [shared])

        # ... and append my own work.
        with open(shared, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("MINE-one\nMINE-two\n")

        res = stage(repo, [shared])[0]
        ok("V-HUNK-OUTCOME", res["outcome"] == FOREIGN_PRESERVED,
           f"two writers in one file -> {res['outcome']}")

        staged = git(repo, "show", ":shared.md")
        ok("V-HUNK-MINE-STAGED",
           "MINE-one" in staged and "MINE-two" in staged,
           "my lines reached the index")
        ok("V-HUNK-FOREIGN-WITHHELD",
           "FOREIGN-alpha" not in staged and "FOREIGN-beta" not in staged,
           "the other writer's lines did NOT reach the index")

        git(repo, "commit", "--quiet", "-m", "mine only")
        committed = git(repo, "show", "HEAD:shared.md")
        ok("V-HUNK-COMMIT-CLEAN",
           "FOREIGN-alpha" not in committed and "MINE-one" in committed,
           "the commit carries my work and none of theirs")

        worktree = shared.read_text(encoding="utf-8")
        ok("V-HUNK-FOREIGN-SURVIVES",
           "FOREIGN-alpha" in worktree and "FOREIGN-beta" in worktree,
           "their uncommitted work is still in the working tree, untouched")

        # The control: the unguarded path is what actually happened in the
        # incident. If this does NOT absorb, the fixture is not reproducing
        # the bug and every result above is about nothing.
        repo2 = Path(td) / "repo2"
        shutil.copytree(repo, repo2)
        git(repo2, "add", "--", "shared.md")
        naive = git(repo2, "show", ":shared.md")
        ok("V-HUNK-POSITIVE-CONTROL",
           "FOREIGN-alpha" in naive,
           "unguarded `git add <path>` DOES absorb the foreign lines "
           "(the defect is real and this fixture reproduces it)")

        # Fail-closed: a file nobody snapshotted must be refused, not staged.
        other = repo / "unsnapshotted.md"
        other.write_text("x\n", encoding="utf-8", newline="\n")
        r2 = stage(repo, [other])[0]
        ok("V-HUNK-NO-BASE", r2["outcome"] == NO_BASE,
           f"file with no snapshot -> {r2['outcome']} (refused, not staged whole)")

        # Fail-closed: a moved HEAD invalidates the baseline.
        snapshot(repo, [other])
        git(repo, "add", "-A")
        git(repo, "commit", "--quiet", "-m", "move head")
        with open(other, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("y\n")
        r3 = stage(repo, [other])[0]
        ok("V-HUNK-STALE-BASE", r3["outcome"] == NO_BASE,
           f"HEAD moved after snapshot -> {r3['outcome']}")

        # An untouched file is not a failure and must not read as one.
        snapshot(repo, [other])
        r4 = stage(repo, [other])[0]
        ok("V-HUNK-NOOP", r4["outcome"] == NOTHING_TO_STAGE,
           f"unchanged file -> {r4['outcome']} (distinct from a refusal)")

        ok("V-HUNK-DISTINCT-EXITS",
           len({EXIT[NO_BASE], EXIT[VERIFY_MISMATCH], EXIT[GUARD_FAILED],
                EXIT[NOTHING_TO_STAGE], EXIT[STAGED_CLEAN]}) == 5,
           "a broken guard, a refused subject and a clean pass exit differently")

    print(f"HUNK_GUARD_PASS={passes}/{passes + fails}  "
          f"threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("verb", choices=["snapshot", "stage", "self-test"])
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--repo", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.verb == "self-test":
        return _self_test()

    try:
        repo = Path(args.repo).resolve() if args.repo else Path(
            git(Path.cwd(), "rev-parse", "--show-toplevel").strip()).resolve()
        paths = [Path(p).resolve() for p in args.paths]
        if not paths:
            raise GuardError("no paths given")
        if args.verb == "snapshot":
            rec = snapshot(repo, paths)
            if args.json:
                print(json.dumps(rec, indent=2, sort_keys=True))
            else:
                for rel, m in rec.items():
                    print(f"  snapshot {rel}  {m['base_bytes']}B  "
                          f"head={m['head'][:8]}")
            return 0
        results = stage(repo, paths)
    except GuardError as exc:
        print(f"{GUARD_FAILED}: {exc}", file=sys.stderr)
        return EXIT[GUARD_FAILED]
    except Exception as exc:  # noqa: BLE001
        print(f"{GUARD_FAILED}: unexpected {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return EXIT[GUARD_FAILED]

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        for r in results:
            print(f"  {r['outcome']:<18} {r['path']}  -- {r['detail']}")
    return max(EXIT[r["outcome"]] for r in results)


if __name__ == "__main__":
    raise SystemExit(main())
