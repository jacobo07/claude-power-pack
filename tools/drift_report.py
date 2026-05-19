#!/usr/bin/env python3
"""drift_report.py — gap-6 fix: classify PP↔loose mirror pairs.

Why this exists
---------------
Before any A1/A2 sync overwrites a PP-tracked canonical with its loose
``~/.claude/`` twin (or vice versa), we MUST know which side is the
authoritative-latest. A blind ``cp loose → repo`` regresses any
PP-tracked file that is intentionally ahead of loose. A blind
``cp repo → loose`` clobbers Owner-personal edits in the live tree.

This tool walks the canonical ``PAIRS`` inventory from
``tools/verify_global_mirrors.py`` (single source of truth for the
mirror set), LF-normalises + SHA-256s both sides, and prints one row
per pair classifying it as:

* ``equal``        — byte-identical (after LF normalization).
* ``loose-ahead``  — repo SHA differs, loose was written more recently;
                     the loose file is the candidate canonical promotion.
* ``pp-ahead``     — repo SHA differs, repo file was written more
                     recently OR loose is missing; the repo is the
                     canonical deploy target.
* ``loose-only``   — pair has a loose file but no repo file (a hook
                     not yet canonicalised — needs A2 to mirror it).
* ``repo-only``    — pair has a repo file but no loose file (loose
                     never installed — needs B1 install-global).

Read-only by design. No mutations. Suitable as the A0 gate before A1.

Exit codes:
  0 — every pair is ``equal`` (no drift).
  1 — at least one pair drifts (Owner ack needed before A1 acts).
  2 — could not read PAIRS / missing tooling (configuration error).
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
import sys
from pathlib import Path


def _norm_sha(data: bytes) -> str:
    """LF-normalize then SHA-256 — neutralizes ``core.autocrlf`` drift."""
    lf = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(lf).hexdigest()


def _load_pairs() -> list[tuple[str, str]] | None:
    """Import ``PAIRS`` from the sibling verify_global_mirrors.py."""
    here = Path(__file__).resolve().parent
    spec_path = here / "verify_global_mirrors.py"
    if not spec_path.exists():
        sys.stderr.write(f"drift_report: missing {spec_path}\n")
        return None
    spec = importlib.util.spec_from_file_location(
        "verify_global_mirrors", str(spec_path))
    if spec is None or spec.loader is None:
        sys.stderr.write("drift_report: spec_from_file_location failed\n")
        return None
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        sys.stderr.write(f"drift_report: cannot load PAIRS: {e}\n")
        return None
    pairs = getattr(mod, "PAIRS", None)
    if not isinstance(pairs, list) or not pairs:
        sys.stderr.write("drift_report: PAIRS is empty/missing\n")
        return None
    return pairs


def _read(path: str) -> bytes | None:
    try:
        return Path(path).read_bytes()
    except (OSError, FileNotFoundError):
        return None


def _mtime(path: str) -> float | None:
    try:
        return Path(path).stat().st_mtime
    except (OSError, FileNotFoundError):
        return None


def _classify(loose: str, repo: str) -> tuple[str, str]:
    """Return ``(verdict, detail)`` for one pair."""
    loose_bytes = _read(loose)
    repo_bytes = _read(repo)
    if loose_bytes is None and repo_bytes is None:
        return "missing-both", "neither side exists"
    if loose_bytes is None:
        return "repo-only", "loose missing — needs install-global"
    if repo_bytes is None:
        return "loose-only", "repo missing — needs A2 canonicalise"
    if _norm_sha(loose_bytes) == _norm_sha(repo_bytes):
        return "equal", "byte-identical (LF-normalised)"
    loose_m = _mtime(loose) or 0.0
    repo_m = _mtime(repo) or 0.0
    if loose_m > repo_m:
        delta_min = (loose_m - repo_m) / 60.0
        return "loose-ahead", f"loose newer by {delta_min:.1f} min"
    delta_min = (repo_m - loose_m) / 60.0
    return "pp-ahead", f"repo newer by {delta_min:.1f} min"


def main() -> int:
    pairs = _load_pairs()
    if pairs is None:
        return 2

    verdicts: dict[str, int] = {}
    rows: list[tuple[str, str, str, str]] = []
    for loose, repo in pairs:
        verdict, detail = _classify(loose, repo)
        verdicts[verdict] = verdicts.get(verdict, 0) + 1
        # Print the relative name of the file as the primary identity.
        rel = os.path.basename(loose)
        rows.append((verdict, rel, detail, repo))

    # Group by verdict for human-scannable output.
    print(f"drift_report — {len(pairs)} mirror pair(s)")
    print("=" * 60)
    for v in ("equal", "loose-ahead", "pp-ahead",
              "loose-only", "repo-only", "missing-both"):
        rows_v = [r for r in rows if r[0] == v]
        if not rows_v:
            continue
        print(f"\n[{v}]  ({len(rows_v)})")
        for _, rel, detail, _repo in rows_v:
            print(f"  {rel:<40s}  {detail}")

    print()
    print("summary:")
    for v, n in sorted(verdicts.items()):
        print(f"  {v:<14s} {n}")

    # Exit non-zero on any drift — A0's gate is "Owner ack before A1 acts".
    drift_present = any(v != "equal" for v in verdicts)
    return 1 if drift_present else 0


if __name__ == "__main__":
    sys.exit(main())
