#!/usr/bin/env python3
"""ADS retroactive backfill (D5).

Generates the four ADS docs for EVERY existing module in a repo that does
not yet have them. Unlike the Stop-chain runner (which is git-diff driven
and only touches CHANGED modules), backfill does a full read-only repo
walk and seeds docs for the modules that predate ADS.

NEVER stages or commits (audit gap #8) -- it only writes files to disk.
`--dry-run` lists what WOULD be generated without writing.

stdlib-only. Public API: enumerate_modules, backfill.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.ads.detector import (
    _ADS_SKIP_DIRS,
    _PKG_MARKERS,
    _SELF_PREFIX,
    MIN_NEW_LOC,
    _count_lines,
    _has_public_symbol,
    _is_source,
    module_slug,
)
from modules.ads.doc_generator import DOC_TYPES, write_docs

KILL_SWITCH = "docs/.ads-disabled"


def enumerate_modules(repo: str | Path) -> list[tuple[str, bool]]:
    """Return [(module_key, is_package)] for every module in the repo.

    Single os.walk with in-place dir pruning so skip-dirs (node_modules,
    .git, vendor, vault, docs, ...) are never descended -- bounded on real
    JS/monorepo trees.
    """
    repo = Path(repo).resolve()
    pkg_dirs: set[str] = set()
    standalone: list[str] = []

    for dirpath, dirnames, filenames in os.walk(repo):
        # Prune skip-dirs before descending.
        dirnames[:] = [d for d in dirnames if d not in _ADS_SKIP_DIRS]
        rel_dir = Path(dirpath).relative_to(repo).as_posix()
        if rel_dir == _SELF_PREFIX or rel_dir.startswith(_SELF_PREFIX + "/"):
            dirnames[:] = []
            continue
        is_pkg = any(m in filenames for m in _PKG_MARKERS)
        if is_pkg and rel_dir not in (".", ""):
            pkg_dirs.add(rel_dir)
        if is_pkg:
            continue
        for fn in filenames:
            rel = fn if rel_dir in (".", "") else f"{rel_dir}/{fn}"
            if not _is_source(rel):
                continue
            f = Path(dirpath) / fn
            if _count_lines(f) > MIN_NEW_LOC and _has_public_symbol(f):
                standalone.append(rel)

    modules: list[tuple[str, bool]] = [(p, True) for p in sorted(pkg_dirs)]
    # Drop standalone files that live under a package dir (covered already).
    for rel in standalone:
        if not any(rel.startswith(p + "/") for p in pkg_dirs):
            modules.append((rel, False))
    return modules


def _has_docs(repo: Path, key: str) -> bool:
    slug = module_slug(key)
    return all((repo / "docs" / d / f"{slug}.md").exists() for d in DOC_TYPES)


def backfill(repo: str | Path, now: str | None = None,
             dry_run: bool = False) -> dict:
    repo = Path(repo).resolve()
    summary = {"repo": str(repo), "generated": [], "skipped_existing": [],
               "dry_run": dry_run}
    if (repo / KILL_SWITCH).exists():
        summary["disabled"] = True
        return summary
    for key, is_pkg in enumerate_modules(repo):
        if _has_docs(repo, key):
            summary["skipped_existing"].append(key)
            continue
        if not dry_run:
            write_docs(key, repo, now, is_pkg)
        summary["generated"].append(key)
    return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="ADS retroactive backfill")
    ap.add_argument("--repo", default=".", help="repo root")
    ap.add_argument("--dry-run", action="store_true",
                    help="list modules without writing")
    args = ap.parse_args(argv)
    s = backfill(args.repo, dry_run=args.dry_run)
    if s.get("disabled"):
        print(f"ADS disabled in {s['repo']} (docs/.ads-disabled present)")
        return 0
    verb = "WOULD generate" if args.dry_run else "generated"
    print(f"Repo: {s['repo']}")
    print(f"{verb} docs for {len(s['generated'])} module(s); "
          f"{len(s['skipped_existing'])} already documented.")
    for k in s["generated"]:
        print(f"  + {k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
