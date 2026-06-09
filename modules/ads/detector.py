#!/usr/bin/env python3
"""ADS module-change detector (D1).

Given a repo root, inspects the git WORKING TREE (staged + unstaged +
untracked) and classifies each touched "module" as CREATED, UPDATED,
MINOR, or DELETED. Only CREATED and UPDATED warrant doc generation;
MINOR and DELETED are silent (DELETED is surfaced but never generates).

Design contract (sealed against the Phase-4 audit):
  * Module = the package directory containing a changed source file
    (a dir holding __init__.py / index.{js,ts,jsx,tsx} / mod.rs), else
    the changed source file itself when it is a standalone source file.
  * CREATED  = package-birth (a NEW package marker among the changes)
               OR a NEW standalone source file > MIN_NEW_LOC with a
               public symbol.
  * UPDATED  = an existing module whose (added+deleted) line churn over
               max(1, current on-disk LOC of the module) exceeds
               UPDATE_PCT.
  * DELETED  = every source file of the module removed.
  * MINOR    = anything else (incl. binary-only churn) -> silence.
  * A CREATED package subsumes its child files: per-file keys inside a
    newly-born package are suppressed in the same run (audit gap #6).
  * git is resolved by ABSOLUTE path on Windows (audit gap #10); if git
    is entirely absent or the repo is not a git repo, detection is a
    silent no-op (returns []).

Read-only, stdlib-only. Reuses scanner._SKIP_DIRS / _LANG_EXT and adds
an ADS-local skip set (docs, vault, _audit_cache, memory) plus a
self-exclusion of modules/ads (audit gaps #11, #14).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, field as dc_field
from enum import Enum
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.setup_os.scanner import _LANG_EXT, _SKIP_DIRS

# --- Tunable thresholds (audit-pinned; Owner-confirmed in Q&A) -----------
MIN_NEW_LOC = 80          # Q1: a new standalone file must exceed this
UPDATE_PCT = 25.0         # Q2: churn % over module LOC to count as UPDATED
GIT_TIMEOUT_S = 8         # bounded git calls -- never hang the Stop chain

# Package markers: presence of one of these in a dir makes it a package.
_PKG_MARKERS = ("__init__.py", "index.js", "index.ts", "index.jsx",
                "index.tsx", "mod.rs")

# ADS-local skip set on top of scanner._SKIP_DIRS (audit gap #14).
_ADS_SKIP_DIRS = frozenset(_SKIP_DIRS) | {
    "docs", "vault", "_audit_cache", "memory", ".specify",
    "_logs", "tasks",
    "_build", "deps", ".elixir_ls", "cover",
    ".tox", ".eggs", "site-packages", ".pytest_cache",
    "Pods", "DerivedData", ".dart_tool", "obj", "bin",
}

# Self-exclusion: the ADS module documents everything BUT itself, so an
# ADS dev turn in the PP repo does not regenerate modules/ads every Stop
# (audit gap #11). Stored as a POSIX-style relative prefix.
_SELF_PREFIX = "modules/ads"


class ChangeType(str, Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    MINOR = "MINOR"
    DELETED = "DELETED"


@dataclass
class ModuleChange:
    key: str                      # repo-relative POSIX path (module key)
    change_type: ChangeType
    files: list[str] = dc_field(default_factory=list)
    added: int = 0
    deleted: int = 0
    pct: float = 0.0
    is_package: bool = False
    rename_from: str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["change_type"] = self.change_type.value
        return d


# --- git plumbing --------------------------------------------------------

def resolve_git(explicit: str | None = None) -> str | None:
    """Resolve an invokable git. Absolute path on Windows (audit gap #10).

    Returns None only if no candidate is even worth trying; the caller
    treats a failing git invocation as a silent no-op regardless.
    """
    if explicit:
        return explicit
    env = os.environ.get("CLAUDE_GIT_EXE")
    if env:
        return env
    if sys.platform.startswith("win"):
        win = Path(r"C:\Program Files\Git\cmd\git.exe")
        if win.exists():
            return str(win)
    return "git"   # rely on PATH elsewhere; failure => no-op


def _git(git_exe: str, repo: Path, *args: str) -> str | None:
    """Run a git subcommand; return stdout, or None on any failure."""
    try:
        cp = subprocess.run(
            [git_exe, "-C", str(repo), *args],
            capture_output=True, text=True, timeout=GIT_TIMEOUT_S,
            encoding="utf-8", errors="replace",
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if cp.returncode != 0:
        return None
    return cp.stdout


def _is_git_repo(git_exe: str, repo: Path) -> bool:
    out = _git(git_exe, repo, "rev-parse", "--is-inside-work-tree")
    return bool(out) and out.strip() == "true"


# --- working-tree parsing ------------------------------------------------

@dataclass
class _FileChange:
    path: str                     # POSIX, repo-relative
    status: str                   # single normalized code: A M D R C ?
    rename_from: str | None = None
    added: int = 0
    deleted: int = 0
    binary: bool = False


def _parse_porcelain(text: str) -> list[_FileChange]:
    """Parse `git status --porcelain=v1` into normalized file changes.

    Each line: `XY <path>` or `XY <old> -> <new>` for renames/copies.
    We collapse the staged/unstaged XY pair into one effective status,
    preferring the more structural code (R/C/A/D over M).
    """
    changes: list[_FileChange] = []
    for raw in text.splitlines():
        if len(raw) < 4:
            continue
        xy = raw[:2]
        rest = raw[3:]
        rename_from = None
        path = rest
        if " -> " in rest:
            old, new = rest.split(" -> ", 1)
            rename_from = old.strip().strip('"')
            path = new.strip().strip('"')
        else:
            path = rest.strip().strip('"')
        code = _normalize_status(xy)
        changes.append(_FileChange(
            path=path.replace("\\", "/"), status=code,
            rename_from=rename_from.replace("\\", "/") if rename_from else None,
        ))
    return changes


def _normalize_status(xy: str) -> str:
    """Collapse a porcelain XY pair into one effective status code."""
    pair = xy.replace(" ", "")
    if "?" in xy:
        return "?"
    for pref in ("R", "C", "A", "D"):     # structural beats modify
        if pref in pair:
            return pref
    if "M" in pair:
        return "M"
    return pair[:1] or "M"


def _apply_numstat(git_exe: str, repo: Path,
                   by_path: dict[str, _FileChange]) -> None:
    """Fill added/deleted/binary from staged+unstaged numstat."""
    for args in (("diff", "--numstat"), ("diff", "--cached", "--numstat")):
        out = _git(git_exe, repo, *args)
        if not out:
            continue
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            a, d, path = parts[0], parts[1], parts[2]
            if " => " in path:        # rename in numstat form
                # e.g. modules/{old => new}/x.py  OR  old => new
                path = _numstat_rename_target(path)
            path = path.replace("\\", "/")
            fc = by_path.get(path)
            if fc is None:
                continue
            if a == "-" or d == "-":          # binary (audit gap #3)
                fc.binary = True
                continue
            try:
                fc.added += int(a)
                fc.deleted += int(d)
            except ValueError:
                fc.binary = True


def _numstat_rename_target(path: str) -> str:
    """Resolve `a/{b => c}/d` or `a => b` numstat path to its NEW path."""
    if "{" in path and "}" in path:
        pre, rest = path.split("{", 1)
        mid, post = rest.split("}", 1)
        new = mid.split(" => ", 1)[-1]
        return (pre + new + post).replace("//", "/")
    if " => " in path:
        return path.split(" => ", 1)[-1]
    return path


# --- module resolution ---------------------------------------------------

def _under_skip(path: str) -> bool:
    parts = path.split("/")
    if any(p in _ADS_SKIP_DIRS for p in parts[:-1]):
        return True
    return path.startswith(_SELF_PREFIX + "/") or path == _SELF_PREFIX


def _is_source(path: str) -> bool:
    return Path(path).suffix in _LANG_EXT


def _is_pkg_marker(path: str) -> bool:
    return Path(path).name in _PKG_MARKERS


def _module_key(repo: Path, path: str) -> tuple[str, bool] | None:
    """Map a file path to (module_key, is_package).

    Walk up looking for a package dir; if found, key = that dir.
    Otherwise the file itself is the module (only if it's source).
    Returns None for non-source files outside any package.
    """
    p = Path(path)
    cur = p.parent
    while True:
        rel = cur.as_posix()
        if rel in (".", "", "/"):
            break
        if any((repo / rel / m).exists() for m in _PKG_MARKERS):
            return rel, True
        # do not climb above repo root
        if cur.parent == cur:
            break
        cur = cur.parent
    if _is_source(path):
        return path, False
    return None


def _module_loc(repo: Path, key: str, is_package: bool) -> int:
    """Current on-disk LOC of a module (audit gap #3 denominator)."""
    total = 0
    target = repo / key
    if is_package and target.is_dir():
        for f in target.rglob("*"):
            if f.is_file() and f.suffix in _LANG_EXT:
                total += _count_lines(f)
    elif target.is_file():
        total += _count_lines(target)
    return total


def _count_lines(f: Path) -> int:
    try:
        with f.open("rb") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


def module_slug(key: str) -> str:
    """Collision-free doc filename slug (audit gap #5): / -> __."""
    s = key.replace("\\", "/").strip("/").replace("/", "__")
    return s or "root"


# --- public API ----------------------------------------------------------

def detect_changes(repo: str | Path,
                   git_exe: str | None = None) -> list[ModuleChange]:
    """Classify working-tree module changes in `repo`. No-op without git."""
    repo = Path(repo).resolve()
    gexe = resolve_git(git_exe)
    if gexe is None or not _is_git_repo(gexe, repo):
        return []

    # -uall expands untracked DIRECTORIES into individual files; without it
    # git collapses a brand-new package dir to a single `pkg/` entry and the
    # package-birth marker is never seen (caught by V-D1-CREATE-PACKAGE).
    status = _git(gexe, repo, "status", "--porcelain=v1", "-uall")
    if status is None:
        return []
    files = [fc for fc in _parse_porcelain(status)
             if not _under_skip(fc.path)]
    if not files:
        return []

    by_path = {fc.path: fc for fc in files}
    _apply_numstat(gexe, repo, by_path)
    # Untracked source files: numstat does not see them; count lines.
    for fc in files:
        if fc.status == "?" and not fc.binary and fc.added == 0:
            if _is_source(fc.path):
                fc.added = _count_lines(repo / fc.path)

    # Group file changes by module key.
    groups: dict[str, dict] = {}
    born_packages: set[str] = set()
    for fc in files:
        mk = _module_key(repo, fc.path)
        if mk is None:
            continue
        key, is_pkg = mk
        g = groups.setdefault(key, {
            "is_package": is_pkg, "files": [], "added": 0, "deleted": 0,
            "new_marker": False, "all_deleted": True, "has_public_new": False,
            "rename_from": None, "binary_only": True,
        })
        g["files"].append(fc.path)
        g["added"] += fc.added
        g["deleted"] += fc.deleted
        if not fc.binary:
            g["binary_only"] = False
        if fc.rename_from and not g["rename_from"]:
            g["rename_from"] = fc.rename_from
        if fc.status != "D":
            g["all_deleted"] = False
        if is_pkg and _is_pkg_marker(fc.path) and fc.status in ("A", "?"):
            g["new_marker"] = True
            born_packages.add(key)
        if (not is_pkg and fc.status in ("A", "?")
                and fc.added > MIN_NEW_LOC
                and _has_public_symbol(repo / fc.path)):
            g["has_public_new"] = True

    # Suppress per-file keys that live inside a newly-born package (#6).
    def _inside_born(key: str) -> bool:
        return any(key != bp and key.startswith(bp + "/")
                   for bp in born_packages)

    out: list[ModuleChange] = []
    for key, g in groups.items():
        if not g["is_package"] and _inside_born(key):
            continue
        loc = _module_loc(repo, key, g["is_package"])
        pct = round((g["added"] + g["deleted"]) / max(1, loc) * 100.0, 1)
        ct = _classify(g, pct)
        out.append(ModuleChange(
            key=key, change_type=ct, files=sorted(g["files"]),
            added=g["added"], deleted=g["deleted"], pct=pct,
            is_package=g["is_package"], rename_from=g["rename_from"],
        ))
    out.sort(key=lambda m: m.key)
    return out


def _classify(g: dict, pct: float) -> ChangeType:
    if g["all_deleted"] and g["files"]:
        return ChangeType.DELETED
    if g["new_marker"] or g["has_public_new"]:
        return ChangeType.CREATED
    if g["binary_only"]:
        return ChangeType.MINOR
    if pct > UPDATE_PCT:
        return ChangeType.UPDATED
    return ChangeType.MINOR


def _has_public_symbol(f: Path) -> bool:
    """Lightweight public-symbol check for a new file (no full AST)."""
    try:
        text = f.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    suffix = f.suffix
    if suffix in (".py",):
        for line in text.splitlines():
            s = line.lstrip()
            if (line[:1] not in (" ", "\t")
                    and (s.startswith("def ") or s.startswith("class "))):
                return True
        return False
    if suffix in (".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"):
        return ("export " in text or "module.exports" in text
                or "function " in text or "class " in text)
    # other languages: any non-trivial content counts as public surface
    return len(text.strip()) > 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="ADS module-change detector")
    ap.add_argument("--repo", default=".", help="repo root")
    ap.add_argument("--git-exe", default=None, help="absolute git path")
    ap.add_argument("--json", action="store_true", help="JSON output")
    args = ap.parse_args(argv)
    changes = detect_changes(args.repo, args.git_exe)
    if args.json:
        print(json.dumps([c.to_dict() for c in changes], indent=2))
    else:
        for c in changes:
            print(f"{c.change_type.value:<8} {c.key}  "
                  f"(+{c.added}/-{c.deleted}, {c.pct}%)")
        if not changes:
            print("(no significant module changes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
