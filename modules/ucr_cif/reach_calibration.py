"""UCR-CIF W7 -- activation reach calibration for the disposition consumers.

W5 proved the corpus can be consumed. W6 proved a SECOND real decision
boundary consumes the same authority. Neither measured how often that
boundary actually opens, and this module is the instrument for that
question -- nothing here changes routing, the selector, the ledger or any
gate. It is read-only over the estate and over the corpus.

Two independent factors decide whether the second door opens, and only one
of them is prompt-shaped:

  PROMPT-SIDE   does the text classify Tier >= 2 (L/XL)?
  REPO-SIDE     does the working directory already contain a spec?

`modules.pp_agents.signals.sdd_tier` emits its ProactiveSignal only when
`check_spec_gate` answers ``create_spec``, and the gate answers that only
when ``_find_spec`` finds NOTHING. So the repo-side factor is a per-repo
CONSTANT: in a repository that holds any file matching ``SPEC_GLOBS`` the
door is shut for every prompt, forever, whatever the prompt says. That
ceiling is measurable with no prompt population at all, which is why it is
measured first -- a prompt study interpreted without it would report a
recall figure whose denominator was never reachable.

Authority reuse, never re-implementation: ``SPEC_GLOBS``, ``_find_spec``,
``classify_tier`` and ``check_spec_gate`` are imported from
``modules.spec_gate.gate``. A local copy of the glob list would measure a
world the product does not live in, and would go quiet the day the real
list changes.

PRIVACY (Owner decision 4, capture=C). The durable record carries a stable
local identity, the repository's own directory NAME, the spec verdict and
the glob that matched. It never carries an absolute host path, a file body,
a prompt, or anything read out of the repository's contents.
"""
from __future__ import annotations

import hashlib
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]

#: Roots swept for repositories. Host-local by construction (Owner decision
#: 6): no VPS, no network share. Missing roots are reported, never assumed
#: empty -- an absent root and a root holding no repository are different
#: facts and only one of them is about the estate.
DEFAULT_ROOTS: tuple[str, ...] = (
    r"C:\Users\User\Desktop",
    r"C:\Users\User\Apps",
    r"C:\Users\User\.claude",
)

#: Directories never descended into. Kept deliberately short: an exclusion
#: is a silent denominator shrink, so each one has to earn its place by
#: being structurally incapable of holding a repository we work in.
_SKIP_DIRS = frozenset({
    "node_modules", ".venv", "venv", "__pycache__", ".next", ".nuxt",
    "dist", "build", ".gradle", ".cache", "site-packages", ".pytest_cache",
    "target", ".mypy_cache", ".ruff_cache",
})

#: A sweep that silently stopped matching reports the same clean answer as
#: a healthy estate with nothing in it. This floor is what tells the two
#: apart. Sized well below the 52 observed on 2026-09-21 so ordinary churn
#: does not trip it, and high enough that a broken matcher cannot pass.
POPULATION_FLOOR = 20


def repo_identity(path: Path) -> str:
    """Stable local identity for a repository, carrying no host path.

    A hash rather than the path itself so the durable artifact can be read,
    diffed and published without exporting anybody's directory layout, and
    stable across runs so two measurements of the same repository join.
    """
    raw = str(path.resolve()).lower().encode("utf-8", "replace")
    return hashlib.sha256(raw).hexdigest()[:12]


def repo_group(path: Path) -> tuple[str, str]:
    """Resolve a working directory to the REPOSITORY it belongs to.

    Measured 2026-09-21 and the reason this function exists: `C:\\Users\\User
    \\Apps` holds 81 directories carrying a `.git` marker, and almost all of
    them are git WORKTREES of about five parent repositories (`io-*`,
    `tuax-*`, `orca-*`, `pp-*`). Counting each as an independent repository
    would have inflated the denominator roughly threefold with copies of one
    source -- and because worktrees of one repo share its content, they also
    share their spec verdict, so the inflation is perfectly correlated with
    the thing being measured. That is a sample of five reported as a sample
    of 180.

    Both units are legitimate and they answer different questions, so both
    are kept and neither is allowed to stand alone:

      REPOSITORY        what fraction of PROJECTS have the door open
      WORKING DIRECTORY what fraction of SESSIONS start behind an open door

    Resolved by reading the `.git` marker rather than by spawning git: a
    worktree's `.git` file holds ``gitdir: <main>/.git/worktrees/<name>``, so
    the common directory is recoverable with one small read, 180 times,
    without 180 subprocesses on a host this session has already measured at
    1.1 % free memory.

    Returns (group_id, group_name). On any unreadable marker the directory
    is its OWN group -- fail-apart, never fail-together: wrongly splitting a
    group costs one duplicated observation, wrongly merging two repositories
    silently deletes one from the population.
    """
    marker = path / ".git"
    try:
        if marker.is_dir():
            return repo_identity(marker), path.name
        raw = marker.read_text("utf-8", errors="replace").strip()
    except OSError:
        return repo_identity(path), path.name
    if not raw.startswith("gitdir:"):
        return repo_identity(path), path.name
    target = Path(raw.split(":", 1)[1].strip())
    if not target.is_absolute():
        target = (path / target).resolve()
    parts = [p.lower() for p in target.parts]
    if "worktrees" in parts:
        idx = len(parts) - 1 - parts[::-1].index("worktrees")
        common = Path(*target.parts[:idx])
    else:
        common = target
    try:
        return repo_identity(common), common.parent.name or common.name
    except (OSError, ValueError):
        return repo_identity(path), path.name


@dataclass
class RepoSpecState:
    """The repo-side factor for one working directory."""

    repo_id: str
    name: str
    #: Identity of the REPOSITORY this working directory belongs to. Several
    #: worktrees of one repository share this, and share their verdict.
    group_id: str = ""
    group_name: str = ""
    #: True when `_find_spec` matches -> the gate can only ever answer
    #: read_spec here -> `sdd_tier` is structurally silent for every prompt.
    spec_present: bool = False
    #: Which SPEC_GLOBS pattern matched, so a ceiling can be attributed to a
    #: specific clause instead of to "specs exist".
    matched_globs: list[str] = field(default_factory=list)
    n_matches: int = 0
    #: True when create_spec is reachable at all in this repository.
    door_reachable: bool = False
    #: Days since this working directory last changed shape, taken as
    #: max(dir mtime, `.git` marker mtime). A PROXY for "work happens here",
    #: and a lower bound on activity in one direction only: editing a file
    #: in place moves neither, so a directory can be active and look stale.
    #: It cannot look active while being untouched, which is the direction
    #: that would flatter the result.
    idle_days: float | None = None
    error: str | None = None


@dataclass
class DiscoveryResult:
    """Repositories found, plus everything the sweep could NOT see.

    `errors` and `missing_roots` are first-class fields rather than log
    lines: a partial sweep that presents as a complete one is the failure
    this whole wave exists to avoid at one level up.
    """

    repos: list[Path] = field(default_factory=list)
    missing_roots: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    scanned_roots: list[str] = field(default_factory=list)


def _is_repo_marker(entry: os.DirEntry) -> bool:
    """A repository is marked by `.git` as a DIRECTORY **or** as a FILE.

    The file form is a git worktree or a submodule. Matching only the
    directory form silently drops every worktree -- including the one this
    mission is executed from -- and a sweep that cannot see its own working
    surface cannot be trusted about anybody else's.
    """
    return entry.name == ".git"


def discover_repos(roots: tuple[str, ...] = DEFAULT_ROOTS,
                   max_depth: int = 4) -> DiscoveryResult:
    """Walk `roots` and return every repository root, with the sweep's gaps.

    Iterative and depth-bounded. `scandir` errors (reparse points, denied
    ACLs, vanished directories) are collected per path instead of aborting
    the walk or -- worse -- being swallowed into a shorter list that reads
    like a smaller estate.
    """
    out = DiscoveryResult()
    for root in roots:
        rp = Path(root)
        if not rp.exists():
            out.missing_roots.append(root)
            continue
        out.scanned_roots.append(root)
        stack: list[tuple[Path, int]] = [(rp, 0)]
        while stack:
            cur, depth = stack.pop()
            try:
                entries = list(os.scandir(cur))
            except (OSError, ValueError) as exc:
                out.errors.append(f"{cur.name}: {type(exc).__name__}")
                continue
            is_repo = any(_is_repo_marker(e) for e in entries)
            if is_repo:
                out.repos.append(cur)
            if depth >= max_depth:
                continue
            for e in entries:
                if e.name in _SKIP_DIRS or e.name == ".git":
                    continue
                try:
                    if e.is_dir(follow_symlinks=False):
                        stack.append((Path(e.path), depth + 1))
                except OSError as exc:
                    out.errors.append(f"{e.name}: {type(exc).__name__}")
    out.repos = sorted(set(out.repos), key=lambda p: str(p).lower())
    return out


def measure_repo(path: Path) -> RepoSpecState:
    """Measure the repo-side factor for one repository.

    Uses the gate's OWN spec finder. If that import fails the state is
    recorded as an error rather than as `spec_present=False`: "we could not
    ask" and "there is no spec" would otherwise both read as an open door,
    which is the flattering direction.
    """
    gid, gname = repo_group(path)
    state = RepoSpecState(repo_id=repo_identity(path), name=path.name,
                          group_id=gid, group_name=gname,
                          spec_present=False)
    try:
        from modules.spec_gate.gate import SPEC_GLOBS, _find_spec
    except Exception as exc:  # noqa: BLE001 -- reported, never defaulted
        state.error = f"gate_unavailable: {type(exc).__name__}"
        return state

    matched: list[str] = []
    total = 0
    for pattern in SPEC_GLOBS:
        try:
            hits = [p for p in path.glob(pattern) if p.is_file()]
        except (OSError, ValueError):
            continue
        if hits:
            matched.append(pattern)
            total += len(hits)

    try:
        found = _find_spec(path)
    except (OSError, ValueError) as exc:
        state.error = f"find_spec_failed: {type(exc).__name__}"
        return state

    state.spec_present = found is not None
    state.matched_globs = matched
    state.n_matches = total
    state.door_reachable = not state.spec_present
    state.idle_days = _idle_days(path)
    return state


def _idle_days(path: Path) -> float | None:
    """Days since the working directory or its `.git` marker last moved."""
    newest = None
    for candidate in (path, path / ".git"):
        try:
            m = candidate.stat().st_mtime
        except OSError:
            continue
        newest = m if newest is None else max(newest, m)
    if newest is None:
        return None
    return round(max(0.0, (time.time() - newest) / 86400.0), 2)


def measure_ceiling(roots: tuple[str, ...] = DEFAULT_ROOTS,
                    max_depth: int = 4) -> dict:
    """The repo-side reach ceiling over the discovered estate.

    Returns numerator, denominator and every excluded population by name.
    A percentage without its denominator is the metric this wave is most
    exposed to, so no ratio is emitted without the counts beside it.
    """
    disc = discover_repos(roots, max_depth)
    states = [measure_repo(p) for p in disc.repos]

    measurable = [s for s in states if s.error is None]
    errored = [s for s in states if s.error is not None]
    reachable = [s for s in measurable if s.door_reachable]

    by_glob: dict[str, int] = {}
    for s in measurable:
        if not s.spec_present:
            continue
        for g in s.matched_globs:
            by_glob[g] = by_glob.get(g, 0) + 1

    # Collapse working directories to repositories. A group is counted as
    # door-open only when EVERY measurable member of it is door-open; a
    # disagreement inside one group is recorded rather than voted on,
    # because it means two worktrees of one repository answered differently
    # and that is a fact about the instrument, not about the estate.
    groups: dict[str, dict] = {}
    for s in measurable:
        g = groups.setdefault(s.group_id, {
            "name": s.group_name, "members": 0, "open": 0})
        g["members"] += 1
        g["open"] += 1 if s.door_reachable else 0
    split = [v["name"] for v in groups.values()
             if 0 < v["open"] < v["members"]]
    group_open = sum(1 for v in groups.values()
                     if v["members"] and v["open"] == v["members"])

    return {
        "population": {
            "working_dirs_discovered": len(disc.repos),
            "measurable": len(measurable),
            "errored": len(errored),
            "distinct_repositories": len(groups),
            "floor": POPULATION_FLOOR,
            "floor_met": len(disc.repos) >= POPULATION_FLOOR,
            "scanned_roots": disc.scanned_roots,
            "missing_roots": disc.missing_roots,
            "sweep_errors": disc.errors,
            "groups_with_split_verdict": split,
        },
        "ceiling_by_working_dir": {
            "door_reachable": len(reachable),
            "door_shut": len(measurable) - len(reachable),
            "denominator": len(measurable),
        },
        "ceiling_by_repository": {
            "door_reachable": group_open,
            "door_shut": len(groups) - group_open,
            "denominator": len(groups),
        },
        "ceiling_by_activity": {
            f"active_within_{d}d": _window(measurable, d)
            for d in (30, 90, 365)
        },
        "shut_by_glob": dict(sorted(by_glob.items(),
                                    key=lambda kv: -kv[1])),
        "repos": [asdict(s) for s in states],
    }


def _window(states: list[RepoSpecState], days: int) -> dict:
    """Ceiling restricted to working directories touched within `days`.

    The unweighted working-directory figure treats a worktree abandoned in
    March as equal to the one a session is running in now. This slice is
    the closer approximation to "where does work actually start", and it is
    reported as its own denominator rather than replacing the others.
    """
    sel = [s for s in states
           if s.idle_days is not None and s.idle_days <= days]
    op = sum(1 for s in sel if s.door_reachable)
    return {"door_reachable": op, "door_shut": len(sel) - op,
            "denominator": len(sel),
            "unmeasurable_mtime": sum(1 for s in states
                                      if s.idle_days is None)}


__all__ = [
    "DEFAULT_ROOTS", "POPULATION_FLOOR", "DiscoveryResult", "RepoSpecState",
    "discover_repos", "measure_ceiling", "measure_repo", "repo_group",
    "repo_identity",
]
