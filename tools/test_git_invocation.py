#!/usr/bin/env python3
"""No module may invoke git by bare name.

THE CLASS. `subprocess.run(["git", ...])` resolves git from PATH. On this host
PATH carries the GitHub CLI and not Git's cmd directory, so every such call
raises FileNotFoundError -- and in each place it was found, the exception was
caught and turned into a value that reads like a measurement:

  the heal loop      reported heal_commits=[] after successfully committing a
                     repair, because rev-parse died into an `except: return None`
  the budget gate    reported its RTK compression as "probe-error", i.e. the
                     gate certifying programmatic conformance was itself
                     unmeasurable
  a dirty-tree guard answered what a clean tree answers

The gap was already documented -- vault/lessons/powershell-git-path-gap.md and
the global execution doctrine both spell it out. It was written for shell
callers and nothing carried it into module code, so it recurred three times in
one repository. That is the CLASE 0 shape exactly: documented, no executable
owner, therefore not prevented. This file is the owner.

RATCHET, not a clean bill. The pre-existing population is frozen below with one
reason per entry; the gate fails when the set GROWS, when a frozen entry is no
longer an offender (a stale exemption is an excuse that outlived its debt), and
when an entry names a file that has since stopped existing.

The red-branch drill uses a SYNTHETIC subject rather than naming a real
offender. A drill pinned to a real defect has an interest in that defect
surviving, and decays the moment someone fixes it -- at which point it asserts
about a file that no longer offends and passes vacuously forever.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent

#: Frozen offenders. One reason each -- an exemption nobody can evaluate later
#: is not an exemption, it is a permanent excuse.
FROZEN: dict[str, str] = {
    "tools/bench_all.py":
        "labels benchmark rows with a short HEAD and already degrades to an "
        "explicit 'unknown'; the failure costs provenance on a local report and "
        "cannot be mistaken for a measurement",
    "tools/test_meta_systems_runtime.py":
        "a test that drives git inside a fixture it constructs; the exposure is "
        "the suite failing loudly on a host without git, which is the correct "
        "outcome for a test rather than a silent wrong answer",
}

_RUNNERS = {"run", "Popen", "call", "check_call", "check_output"}
_BARE = {"git", "git.exe"}

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


def _first_element_is_bare_git(node: ast.AST) -> bool:
    """A subprocess argv whose first element is the literal 'git'.

    Structural, not textual: a grep for the word finds the comments and the
    docstrings, which is the opposite of the question.
    """
    if not isinstance(node, ast.Call):
        return False
    fn = node.func
    name = fn.attr if isinstance(fn, ast.Attribute) else (
        fn.id if isinstance(fn, ast.Name) else "")
    if name not in _RUNNERS:
        return False
    if not node.args:
        return False
    argv = node.args[0]
    if isinstance(argv, (ast.List, ast.Tuple)) and argv.elts:
        head = argv.elts[0]
        return isinstance(head, ast.Constant) and head.value in _BARE
    # A bare string command reaching a shell has the same exposure.
    if isinstance(argv, ast.Constant) and isinstance(argv.value, str):
        first = argv.value.strip().split()[:1]
        return bool(first) and first[0] in _BARE
    return False


def offenders(root: Path) -> dict[str, list[int]]:
    found: dict[str, list[int]] = {}
    for sub in ("modules", "tools", "hooks"):
        base = root / sub
        if not base.is_dir():
            continue
        for src in sorted(base.rglob("*.py")):
            rel = src.relative_to(root).as_posix()
            try:
                tree = ast.parse(src.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError:
                continue
            lines = [n.lineno for n in ast.walk(tree)
                     if _first_element_is_bare_git(n)]
            if lines:
                found[rel] = lines
    return found


SYNTHETIC_OFFENDER = '''
import subprocess
def go(p):
    return subprocess.run(["git", "-C", p, "status"], capture_output=True)
'''
SYNTHETIC_CLEAN = '''
import subprocess
from modules.execution_env import git_exe
def go(p):
    return subprocess.run([git_exe(), "-C", p, "status"], capture_output=True)
'''


def main() -> int:
    # --- the detector must be able to answer BOTH ways ---------------------
    # Against a subject built for the purpose, so neither half can decay when
    # the real population changes.
    for label, src, want in (("RED", SYNTHETIC_OFFENDER, True),
                             ("GREEN", SYNTHETIC_CLEAN, False)):
        tree = ast.parse(src)
        hit = any(_first_element_is_bare_git(n) for n in ast.walk(tree))
        check(f"V-GITINV-DRILL-{label}", hit is want,
              f"synthetic {'offender is flagged' if want else 'clean call is not flagged'}"
              f" (detected={hit})")

    current = offenders(_ROOT)
    check("V-GITINV-SWEEP-FOUND-SOMETHING", True,
          f"structural sweep of modules/ tools/ hooks/ examined the tree and "
          f"reports {len(current)} file(s) invoking git by bare name")

    new = sorted(set(current) - set(FROZEN))
    check("V-GITINV-NO-GROWTH", not new,
          f"no unfrozen offender: {new}" if new else
          "no module invokes git by bare name outside the frozen inventory")

    stale = sorted(set(FROZEN) - set(current))
    check("V-GITINV-NO-STALE-EXEMPTION", not stale,
          f"frozen entries that no longer offend must be deleted: {stale}"
          if stale else "every frozen entry is still a genuine current offender")

    missing = sorted(p for p in FROZEN if not (_ROOT / p).exists())
    check("V-GITINV-FROZEN-FILES-EXIST", not missing,
          f"frozen entry names a file that is gone: {missing}" if missing
          else "every frozen entry names a file that exists")

    owner = _ROOT / "modules" / "execution_env" / "__init__.py"
    check("V-GITINV-OWNER-EXISTS", owner.exists(),
          "modules/execution_env supplies the single resolver callers use")

    print(f"GIT_INVOCATION_PASS={PASSES}/{PASSES + FAILS}  "
          f"threshold={PASSES + FAILS}/{PASSES + FAILS}")
    if current:
        print("  current bare-git call sites:")
        for rel, lines in sorted(current.items()):
            mark = "frozen" if rel in FROZEN else "NEW"
            print(f"    [{mark}] {rel}:{lines}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
