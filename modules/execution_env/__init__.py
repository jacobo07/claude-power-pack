"""Where is git? One answer, for every module that needs to ask.

THE INCIDENT CLASS. `subprocess.run(["git", ...])` resolves git from PATH, and
on this host PATH carries the GitHub CLI without Git's cmd directory. The gap is
documented -- vault/lessons/powershell-git-path-gap.md, and again in the global
execution doctrine -- as advice to shell callers, and the advice never reached
module code. Measured 2026-09-11, three independent live instances:

  modules/sleepless_qa/healer/orchestrator.py   a heal run repaired its target,
      committed the fix and re-verified green, then reported heal_commits=[]
      because rev-parse raised FileNotFoundError into an except that returned
      None. Success recorded as absence.
  tools/verify_full_install.py                  the mandatory budget gate's
      RTK compression probe returned "unmeasured (probe-error:FileNotFoundError)"
      on a host where the measurement is perfectly possible.
  the same file's status probe                  a guard that could not read the
      tree returned the value a clean tree returns.

Every one of the three swallowed the error and answered with something that
reads like a measurement. That is the shape the estate's own doctrine warns
about: could-not-look must never return what looked-and-found-nothing returns.

WHY A RESOLVER AND NOT A HARDCODED PATH. Shared modules carry no absolute
paths, so the conventional install location is derived from ProgramFiles in the
environment rather than written as a literal, and PP_GIT overrides everything
for hosts that put git elsewhere. An unresolvable git returns None, loudly, and
callers are expected to treat that as UNREADABLE rather than as a negative
answer.

Enforced by tools/test_git_invocation.py, which sweeps the estate for bare-git
subprocess calls so this class cannot quietly regrow.
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

#: Returned in place of a reading when git itself could not be located or run.
#: Distinct from any legitimate git output, so a caller cannot mistake "I could
#: not look" for "I looked and the answer was empty".
GIT_UNREADABLE = "<git-unreadable>"

_CONVENTIONAL = (
    ("Git", "cmd", "git.exe"),
    ("Programs", "Git", "cmd", "git.exe"),
)
_ROOTS = ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA")


@lru_cache(maxsize=1)
def git_exe() -> str | None:
    """Absolute path to git, or None once, with a reason in the log."""
    found = shutil.which("git") or shutil.which("git.exe")
    if found:
        return found
    override = os.environ.get("PP_GIT")
    if override and Path(override).is_file():
        return override
    for var in _ROOTS:
        base = os.environ.get(var)
        if not base:
            continue
        for rel in _CONVENTIONAL:
            cand = Path(base).joinpath(*rel)
            if cand.is_file():
                return str(cand)
    logger.error(
        "git could not be located: absent from PATH, PP_GIT unset or not a "
        "file, and no conventional install found under %s. Callers must report "
        "git observations as UNREADABLE, never as an absence.", ", ".join(_ROOTS))
    return None


def run_git(repo_path: Path | str | None, *args: str, timeout: int = 10):
    """Run one git command. Returns None when git itself is unavailable.

    None means "could not look". It is never "looked and found nothing", and
    conflating the two is the whole reason this module exists.
    """
    exe = git_exe()
    if exe is None:
        return None
    cmd = [exe]
    if repo_path is not None:
        cmd += ["-C", str(repo_path)]
    cmd += list(args)
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              timeout=timeout, check=False)
    except Exception:
        logger.exception("git %s failed", args[0] if args else "")
        return None
