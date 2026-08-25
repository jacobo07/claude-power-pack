"""Provenance boundary for D2A family discovery.

`_discover_families()` promotes every directory under vault/knowledge_base/ to a parent
that future proposals are scored against. It reads the working tree, so a directory
written by an audit that is still running becomes a sealed parent the moment it exists.

Measured 2026-08-25: a mission wrote vault/knowledge_base/ucr_cif/ on Monday; by the next
session the engine was scoring new proposals against `KB-UCR-CIF` and reporting coverage
"capped by the plausibility floor" against it. The audit's own output had become the
authority its successor was measured against, and nothing in the engine could notice --
a filesystem-derived family carries no record of when it arrived or whether anyone sealed
it. That is not a transient read of the wrong file; it is contamination institutionalized
into the engine's family table, where it persists for every later proposal.

A family earns parent status by being *committed*. Tracked-ness is the cheapest signal
that survives this test: an in-flight audit's output is untracked, and sealed institutional
capital is not. One `git ls-files` for the whole knowledge_base answers it for every
directory at once, so the boundary costs a single subprocess at import.

Fail-open is deliberate and directional. When git cannot answer, every family is treated
as sealed -- the engine's behaviour before this module existed. Excluding a real parent
produces a false CREATE (build a duplicate); including a false parent produces a false
OWNED (skip something needed). This estate's base rate is fifteen consecutive mega-corpus
proposals measured majority-owned, so false CREATE is the costlier error and the fallback
leans away from it. The degradation is reported through `last_reason()`, never silent.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

_GIT_FALLBACK = r"C:\Program Files\Git\cmd\git.exe"

_cache: dict[str, frozenset] = {}
_reason: dict[str, str] = {}


def _git() -> str | None:
    exe = shutil.which("git")
    if exe:
        return exe
    return _GIT_FALLBACK if os.path.isfile(_GIT_FALLBACK) else None


def tracked_paths(repo_root, subdir: str = "") -> frozenset:
    """Repo-relative POSIX paths git tracks under `subdir`. Empty set means unknown.

    Cached per (repo_root, subdir): family discovery asks once per directory but the
    answer is one listing, and re-forking git per family would cost more than the
    contamination it prevents.
    """
    root = Path(repo_root).resolve()
    key = f"{root}|{subdir}"
    if key in _cache:
        return _cache[key]

    exe = _git()
    if exe is None:
        _reason[key] = "git not found on PATH or at the Windows fallback path"
        _cache[key] = frozenset()
        return _cache[key]

    args = [exe, "-C", str(root), "ls-files", "-z"]
    if subdir:
        args.append(subdir)
    try:
        out = subprocess.run(args, capture_output=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError) as e:
        _reason[key] = f"git ls-files failed: {type(e).__name__}"
        _cache[key] = frozenset()
        return _cache[key]

    if out.returncode != 0:
        _reason[key] = f"git ls-files exit {out.returncode}"
        _cache[key] = frozenset()
        return _cache[key]

    paths = out.stdout.decode("utf-8", "replace").split("\0")
    _reason[key] = ""
    _cache[key] = frozenset(p for p in paths if p)
    return _cache[key]


def last_reason(repo_root, subdir: str = "") -> str:
    """Why tracked_paths() returned empty, or '' when it answered normally."""
    return _reason.get(f"{Path(repo_root).resolve()}|{subdir}", "not queried")


CUTOFF_ENV = "PP_AUDIT_CUTOFF"


_births: dict[str, dict] = {}


def birth_map(repo_root, subdir: str = "") -> dict:
    """{repo-relative path: ISO timestamp of the commit that ADDED it}.

    One git call for the whole subtree, cached. The obvious implementation -- ask
    `git log --reverse -- <dir>` per family -- measured **741 ms per directory**, so
    discovering 26 families under a declared cutoff took 19 SECONDS and blew the
    umbrella's row budget. Same answer, one process instead of twenty-six.
    """
    root = Path(repo_root).resolve()
    key = f"{root}|{subdir}"
    if key in _births:
        return _births[key]

    exe = _git()
    if exe is None:
        _births[key] = {}
        return _births[key]

    args = [exe, "-C", str(root), "log", "--reverse", "--diff-filter=A",
            "--format=%x00%cI", "--name-only"]
    if subdir:
        args += ["--", subdir]
    try:
        out = subprocess.run(args, capture_output=True, timeout=120, check=False)
    except (OSError, subprocess.SubprocessError):
        _births[key] = {}
        return _births[key]
    if out.returncode != 0:
        _births[key] = {}
        return _births[key]

    births: dict[str, str] = {}
    ts = ""
    for line in out.stdout.decode("utf-8", "replace").splitlines():
        if line.startswith("\x00"):
            ts = line[1:].strip()
        elif line.strip() and ts:
            births.setdefault(line.strip(), ts)   # --reverse: oldest wins
    _births[key] = births
    return births


def first_commit_iso(path, repo_root, subdir: str = "") -> str:
    """ISO date the tree at `path` first appeared, or '' when git cannot say."""
    root = Path(repo_root).resolve()
    try:
        rel = Path(path).resolve().relative_to(root).as_posix()
    except ValueError:
        return ""
    bm = birth_map(root, subdir)
    if not bm:
        return ""
    prefix = rel + "/"
    seen = [v for k, v in bm.items() if k == rel or k.startswith(prefix)]
    return min(seen) if seen else ""


def _cutoff(repo_root) -> str:
    """Declared cutoff as an ISO timestamp. Accepts a date or any git revision."""
    raw = (os.environ.get(CUTOFF_ENV) or "").strip()
    if not raw:
        return ""
    if raw[:1].isdigit() and "-" in raw[:8]:          # already a date/ISO timestamp
        return raw
    exe = _git()
    if exe is None:
        return ""
    try:
        out = subprocess.run(
            [exe, "-C", str(Path(repo_root).resolve()), "show", "-s", "--format=%cI", raw],
            capture_output=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout.decode("utf-8", "replace").strip() if out.returncode == 0 else ""


def family_provenance(family_dir, repo_root, subdir: str = "") -> dict:
    """Classify one candidate family directory as sealed capital or in-flight output.

    Two boundaries, and only the second is sufficient on its own.

    Tracked-ness catches an audit whose output has not been committed yet. It does NOT
    catch one that has: the mission that produced vault/knowledge_base/ucr_cif/ committed
    it the same day, so by every git measure it is ordinary tracked content, and the next
    session was scored against it. A boundary that only sees uncommitted work would have
    passed the exact case it was written for -- recorded here rather than papered over.

    What closes it is a DECLARED cutoff (PP_AUDIT_CUTOFF, an ISO date or anything git
    rev-parse resolves). A family first committed after the moment an audit began is that
    audit's own output relative to that audit, whatever its tracked-ness. Declared, never
    sniffed: an auditor that infers its own start date can infer a convenient one, and
    section 6 of the mission brief asks for an explicit frontier for exactly that reason.
    """
    root = Path(repo_root).resolve()
    fdir = Path(family_dir).resolve()
    try:
        rel = fdir.relative_to(root).as_posix()
    except ValueError:
        return {"sealed": True, "tracked": 0, "reason": "outside repo root; not judged"}

    tracked = tracked_paths(root, subdir)
    if not tracked:
        return {"sealed": True, "tracked": 0,
                "reason": f"unknown, treated as sealed ({last_reason(root, subdir)})"}

    prefix = rel + "/"
    n = sum(1 for p in tracked if p.startswith(prefix))
    if not n:
        return {"sealed": False, "tracked": 0,
                "reason": "no tracked files -- in-flight output, not a sealed parent"}

    cut = _cutoff(root)
    if cut:
        born = first_commit_iso(fdir, root, subdir)
        if born and born > cut:
            return {"sealed": False, "tracked": n, "born": born,
                    "reason": f"first committed {born}, after declared cutoff {cut}"}
        if not born:
            return {"sealed": True, "tracked": n,
                    "reason": f"{n} tracked file(s); birth unknown, cutoff not applied"}
    return {"sealed": True, "tracked": n, "reason": f"{n} tracked file(s)"}


def is_sealed_family(family_dir, repo_root, subdir: str = "") -> bool:
    return family_provenance(family_dir, repo_root, subdir)["sealed"]


def reset_cache() -> None:
    """Drop memoised listings. Tests mutate the tree between assertions."""
    _cache.clear()
    _reason.clear()
    _births.clear()
