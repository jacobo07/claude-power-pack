"""UCR-CIF W7 -- an independent relevance oracle for activation recall.

Recall cannot be computed against "did the trigger fire": that defines the
system as correct by construction and the number it returns is 100 % by
arithmetic, not by merit. Nor may it be computed from the selector, which
is the component whose output is being judged for usefulness.

So the oracle here is the ENGINEER'S OWN SUBSEQUENT BEHAVIOUR, read out of
git history, which neither the trigger nor the selector can influence:

    For a prompt issued in repository R at time T, which paths did R's
    commits actually touch in the window that followed?

If the work landed inside a path the corpus holds AUTHORITATIVE
dispositions about, then naming that owner before the spec was written
would have pointed at the place the work went -- which is exactly the
anti-duplication value UCR-CIF claims. If the work landed entirely
elsewhere, routing that owner would have been noise.

WHAT THIS IS NOT
It is a PROXY, and its limits are stated rather than buried:

  * POST-HOC. The label uses evidence created AFTER the prompt. It may
    never be read as "the agent could have known this at mission start".
  * Work landing in an owner path does not prove the agent was ignorant
    of the owner; it may have known perfectly well.
  * Work landing elsewhere does not prove the owner was irrelevant; the
    session may have been abandoned, or the advice correct and unheeded.
  * No commits in the window is UNLABELLED. Absence of a commit is not
    evidence of absence of relevance, and collapsing it into a negative
    is the single easiest way to manufacture a flattering precision.

DOMAIN. The 40 authoritative owners are all Power-Pack-internal paths, so
this oracle can only speak about prompts issued inside a Power Pack
checkout. Everything else is UNLABELLED BY DOMAIN and counted as such --
never as a negative, and never quietly dropped from the denominator.
"""
from __future__ import annotations

import subprocess
from bisect import bisect_left
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

#: Absolute path to git. PowerShell's non-interactive PATH on this host
#: does not carry it (documented estate trap), and a bare name here would
#: fail in a way that looks like "no commits".
GIT = r"C:\Program Files\Git\cmd\git.exe"

#: How long after a prompt its work is attributed. 24 h is long enough to
#: cover one working session including an overnight seal, short enough
#: that unrelated later waves do not bleed in. Reported with the result so
#: the choice is arguable rather than hidden.
DEFAULT_WINDOW_HOURS = 24

LABELS = (
    "RELEVANT",              # work landed inside a routed owner path
    "NOT_RELEVANT",          # work happened, and none of it landed there
    "AMBIGUOUS",             # work landed only in shared/global paths
    "UNLABELLED_NO_COMMITS",  # nothing to read; NOT a negative
    "UNLABELLED_BY_DOMAIN",  # cwd is not a Power Pack checkout
    "UNLABELLED_NO_HISTORY",  # git unavailable or repo unreadable
)

#: Paths that every wave touches whatever it is about. A commit that moves
#: only these says nothing about where the work belonged.
_SHARED = (
    "vault/knowledge_base/", "vault/audits/", "vault/governance/",
    "CLAUDE.md", "README.md", "MEMORY.md", "_logs/",
)


@dataclass
class RepoHistory:
    """Commit times and touched paths for one repository, read once."""

    times: list[datetime] = field(default_factory=list)
    paths: list[frozenset[str]] = field(default_factory=list)
    error: str | None = None


def load_history(repo: Path, git: str = GIT) -> RepoHistory:
    """Read (commit time, touched paths) for every reachable commit.

    One subprocess per REPOSITORY, not per prompt. A per-prompt call would
    have spawned thousands of processes on a host this session measured at
    1.1 % free memory -- the instrument would have become the load.
    """
    hist = RepoHistory()
    try:
        proc = subprocess.run(
            [git, "-C", str(repo), "log", "--all", "--no-merges",
             "--pretty=format:@@%cI", "--name-only"],
            capture_output=True, text=True, timeout=180,
            encoding="utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError) as exc:
        hist.error = f"{type(exc).__name__}"
        return hist
    if proc.returncode != 0:
        hist.error = f"git exit {proc.returncode}"
        return hist

    cur: datetime | None = None
    acc: set[str] = set()
    for line in proc.stdout.splitlines():
        if line.startswith("@@"):
            if cur is not None:
                hist.times.append(cur)
                hist.paths.append(frozenset(acc))
            acc = set()
            try:
                cur = datetime.fromisoformat(line[2:].strip())
            except ValueError:
                cur = None
        elif line.strip() and cur is not None:
            acc.add(line.strip().replace("\\", "/"))
    if cur is not None:
        hist.times.append(cur)
        hist.paths.append(frozenset(acc))

    order = sorted(range(len(hist.times)), key=lambda i: hist.times[i])
    hist.times = [hist.times[i] for i in order]
    hist.paths = [hist.paths[i] for i in order]
    return hist


def paths_touched(hist: RepoHistory, start: datetime,
                  hours: int = DEFAULT_WINDOW_HOURS) -> set[str]:
    """Union of paths touched in [start, start + hours]."""
    end = start + timedelta(hours=hours)
    lo = bisect_left(hist.times, start)
    out: set[str] = set()
    for i in range(lo, len(hist.times)):
        if hist.times[i] > end:
            break
        out |= hist.paths[i]
    return out


def _owner_hit(touched: set[str], owners: list[str]) -> list[str]:
    hits = []
    for owner in owners:
        norm = owner.rstrip("/")
        if any(p == norm or p.startswith(norm + "/") for p in touched):
            hits.append(owner)
    return hits


def label_case(owners: list[str], touched: set[str],
               had_history: bool, in_domain: bool) -> tuple[str, list[str]]:
    """Assign one independent relevance label.

    `owners` is used only to ask WHERE THE WORK WENT. It never decides the
    label on its own: a case with no commits is unlabelled whatever the
    selector proposed, which is what keeps this oracle independent.
    """
    if not in_domain:
        return "UNLABELLED_BY_DOMAIN", []
    if not had_history:
        return "UNLABELLED_NO_HISTORY", []
    if not touched:
        return "UNLABELLED_NO_COMMITS", []
    hits = _owner_hit(touched, owners)
    if hits:
        return "RELEVANT", hits
    substantive = {p for p in touched
                   if not any(p.startswith(s) for s in _SHARED)}
    if not substantive:
        return "AMBIGUOUS", []
    return "NOT_RELEVANT", []


def parse_ts(raw: str) -> datetime | None:
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


__all__ = [
    "DEFAULT_WINDOW_HOURS", "GIT", "LABELS", "RepoHistory", "label_case",
    "load_history", "parse_ts", "paths_touched",
]
