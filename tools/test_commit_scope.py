#!/usr/bin/env python3
"""Does the sanctioned commit wrapper actually scope a commit to named files?

The pathspec rule is doctrine in three separate places -- the global CLAUDE.md
("Every agent-issued commit MUST name its files"), rules/common/git-workflow.md,
and the concurrent-writers rule. It has an executable owner that every repo on
this host is told to use: tools/git_commit_safe.ps1. Until 2026-09-11 that owner
took no pathspec at all, so a caller following the instruction to the letter
still committed the whole index -- including a concurrent pane's staged files.

Documented rule, real owner, owner structurally unable to obey it. Nothing was
red, because nothing was asking.

This suite pins the repair. The load-bearing gate is the POSITIVE CONTROL: it
proves an unscoped commit really does absorb a foreign file in this exact
fixture, so the scoped case passing is evidence of scoping rather than evidence
that the fixture was never dangerous. A guard whose hazard was never
demonstrated is indistinguishable from a guard that does nothing.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from modules.execution_env import git_exe  # noqa: E402

WRAPPER = _ROOT / "tools" / "git_commit_safe.ps1"

# Resolved through the one owner rather than written as a literal. That is the
# estate's no-absolute-paths rule, and it is what tools/test_git_invocation.py
# exists to enforce -- a suite that hardcodes the path it tells other modules
# not to hardcode is not a gate, it is an exemption.
GIT = git_exe() or "git"
PWSH = shutil.which("powershell") or "powershell"

PASSES = 0
FAILS = 0


def check(gate: str, cond: bool, evidence: str) -> None:
    global PASSES, FAILS
    if cond:
        PASSES += 1
        print(f"  OK   {gate}  {evidence}")
    else:
        FAILS += 1
        print(f"  FAIL {gate}  {evidence}")


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([GIT, "-C", str(repo), *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          check=False)


def make_repo() -> Path:
    """A repo with one committed file, then TWO staged files: one this session
    owns and one a concurrent writer staged. That is the real hazard shape --
    both are in the index, and the index is shared."""
    d = Path(tempfile.mkdtemp(prefix="commitscope_"))
    git(d, "init", "--quiet")
    git(d, "config", "user.email", "t@t.t")
    git(d, "config", "user.name", "t")
    (d / "base.txt").write_text("base\n", encoding="utf-8")
    git(d, "add", "base.txt")
    git(d, "commit", "--quiet", "-m", "base")
    (d / "mine.txt").write_text("my work\n", encoding="utf-8")
    (d / "foreign.txt").write_text("another pane's work\n", encoding="utf-8")
    git(d, "add", "mine.txt", "foreign.txt")
    return d


def commit_via_wrapper(repo: Path, body: str, pathspec: list[str] | None,
                       direct: bool = False) -> subprocess.CompletedProcess:
    """Drive the real wrapper. `direct` runs the script as an executable rather
    than dot-sourcing it -- a separate code path that has its own argument
    forwarding, and therefore its own way to silently drop -PathSpec."""
    ps_list = ""
    if pathspec:
        ps_list = " -PathSpec " + ",".join(f"'{p}'" for p in pathspec)
    if direct:
        cmd = (f"& '{WRAPPER}' -Body '{body}' -RepoRoot '{repo}'{ps_list}")
    else:
        cmd = (f". '{WRAPPER}'; Invoke-GitCommitSafe -Body '{body}' "
               f"-RepoRoot '{repo}'{ps_list}")
    return subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-Command", cmd],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", check=False)


def files_in_head(repo: Path) -> set[str]:
    out = git(repo, "show", "--name-only", "--format=", "HEAD").stdout
    return {ln.strip() for ln in out.splitlines() if ln.strip()}


def still_staged(repo: Path) -> set[str]:
    out = git(repo, "diff", "--cached", "--name-only").stdout
    return {ln.strip() for ln in out.splitlines() if ln.strip()}


def main() -> int:
    if not WRAPPER.exists():
        print(f"  FAIL V-SCOPE-WRAPPER-PRESENT  missing {WRAPPER}")
        print("COMMIT_SCOPE_PASS=0/1  threshold=1/1")
        return 1

    # --- POSITIVE CONTROL -------------------------------------------------
    # Prove the hazard is real in this fixture. If an unscoped commit does NOT
    # absorb the foreign file here, then the scoped case below proves nothing
    # and every other gate in this file is decoration.
    repo = make_repo()
    try:
        cp = commit_via_wrapper(repo, "unscoped", None)
        head = files_in_head(repo)
        check("V-SCOPE-POSITIVE-CONTROL",
              {"mine.txt", "foreign.txt"} <= head,
              f"an unscoped commit DOES absorb the concurrent writer's file: "
              f"HEAD={sorted(head)}")
        check("V-SCOPE-UNSCOPED-IS-VISIBLE",
              "UNSCOPED COMMIT" in (cp.stderr or "") + (cp.stdout or ""),
              "the unscoped path warns and names what it is about to take")
    finally:
        shutil.rmtree(repo, ignore_errors=True)

    # --- the repair -------------------------------------------------------
    repo = make_repo()
    try:
        commit_via_wrapper(repo, "scoped", ["mine.txt"])
        head = files_in_head(repo)
        staged = still_staged(repo)
        check("V-SCOPE-COMMITS-ONLY-NAMED",
              "mine.txt" in head and "foreign.txt" not in head,
              f"HEAD carries only the named path: {sorted(head)}")
        check("V-SCOPE-FOREIGN-PRESERVED",
              "foreign.txt" in staged,
              "the concurrent writer's file is left staged, not committed and "
              "not discarded")
    finally:
        shutil.rmtree(repo, ignore_errors=True)

    # --- the second entry point ------------------------------------------
    # The script can be run directly instead of dot-sourced, and that path
    # forwards its own arguments. A parameter added to the function but not to
    # the forwarder is a gate with a caller that walks around it.
    repo = make_repo()
    try:
        commit_via_wrapper(repo, "scoped direct", ["mine.txt"], direct=True)
        head = files_in_head(repo)
        check("V-SCOPE-DIRECT-INVOCATION-FORWARDS",
              "mine.txt" in head and "foreign.txt" not in head,
              f"direct invocation honours -PathSpec too: {sorted(head)}")
    finally:
        shutil.rmtree(repo, ignore_errors=True)

    # --- file scope is not hunk scope ------------------------------------
    # Stated as an assertion rather than a comment so the boundary of this
    # protection cannot quietly be forgotten: a pathspec names a FILE, and a
    # file can hold two authors.
    check("V-SCOPE-HUNK-OWNER-EXISTS",
          (_ROOT / "tools" / "foreign_hunk_guard.py").exists(),
          "same-file contention escalates to the hunk-granular owner; pathspec "
          "alone does not cover two writers inside one file")

    # --- and the two protections are ALTERNATIVES, not layers -------------
    # This is the correction to guidance written earlier the same day. A
    # pathspec commit does NOT commit the index: `git commit -- <path>` takes
    # the WORKING TREE content of the named paths, discarding whatever was
    # staged for them. So running the hunk guard and then committing with a
    # pathspec silently throws the guard's careful index away and re-absorbs the
    # other writer. Measured in production: the guard subtracted five foreign
    # lines from the index and a pathspec commit put all five back.
    #
    # Correct composition:
    #   guard used      -> commit from the INDEX, no pathspec
    #   guard not used  -> commit with a pathspec, file granularity
    repo = make_repo()
    try:
        (repo / "mine.txt").write_text("STAGED VERSION\n", encoding="utf-8")
        git(repo, "add", "mine.txt")
        (repo / "mine.txt").write_text("WORKTREE VERSION\n", encoding="utf-8")
        commit_via_wrapper(repo, "pathspec beats index", ["mine.txt"])
        blob = git(repo, "show", "HEAD:mine.txt").stdout
        check("V-SCOPE-PATHSPEC-TAKES-WORKTREE-NOT-INDEX",
              "WORKTREE VERSION" in blob,
              "a pathspec commit takes the working tree and discards the staged "
              "version, so it OVERRIDES a curated index rather than adding to it")
    finally:
        shutil.rmtree(repo, ignore_errors=True)

    print(f"COMMIT_SCOPE_PASS={PASSES}/{PASSES + FAILS}  "
          f"threshold={PASSES + FAILS}/{PASSES + FAILS}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
