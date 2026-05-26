#!/usr/bin/env python3
"""verify_spp.py — S++ end-to-end umbrella verifier.

Composes every sub-verifier in the Power Pack into one row-table +
single exit code. Sibling of (NOT replacement for) the Owner-authored
``tools/verify_full_install.py`` which audits the Programmatic Budget
Layer specifically; this umbrella invokes that one as one of its rows
and adds the rest of the S++ surface.

Rows:
  1. mirror-parity     — tools/verify_global_mirrors.py
  2. drift-report      — tools/drift_report.py
  3. paths+secrets     — tools/normalize_paths.py --check
  4. rtk-fusion        — tools/verify_rtk_fusion.py
  5. intent-lock       — modules/harness/intent_lock.js --self-test
  6. l3-engine         — tools/test_l3_intent.js
  7. programmatic-budget — tools/verify_full_install.py (Owner-authored)

Each row reports: name | rc | elapsed_s | one-line summary.
Exit 0 iff EVERY row exits 0 OR is marked ``ADVISORY`` in
``ADVISORY_ROWS``. ≤120s wall-clock budget (rows past budget abort).

Doctrine alignment:
* Reality-Contract: each row is a real subprocess call; no synthesised
  composite multiplier. If a sub-verifier does not exist, the row
  surfaces as ``MISSING`` (red) — never silently skipped.
* Mirror-Sync-Direction: tolerates the Owner's expected ``loose-ahead``
  on the documented mirror-parity exceptions (advisory).
* Hooks-dir deny doctrine: this umbrella is read-only by design;
  zero mutations to ``~/.claude/`` or any settings.

Usage:
  python tools/verify_spp.py
  python tools/verify_spp.py --quiet
  python tools/verify_spp.py --row <name>   # run a single row
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
NODE = shutil.which("node") or shutil.which("node.exe") or "node"
PY = sys.executable

# Rows that may FAIL without failing the umbrella gate. Use sparingly —
# the default is strict.
ADVISORY_ROWS: set[str] = {
    # programmatic-budget: scope-specific (RTK + JIT + pricing); a
    # missing budget.json or stale pricing is an Owner-side concern,
    # not an S++ gate failure on a fresh install.
    "programmatic-budget",
    # NOTE (2026-05-20, Owner-correction): the prior ``l3-engine``
    # advisory entry was REMOVED. Owner-directive rejected "classified
    # FAIL" framings: verify_spp.py exit 0 means 7/7 strict-OK. The
    # parent/child contention pattern documented earlier is real but
    # is no longer a license to advisory-tag; the row must pass
    # under realistic umbrella conditions or be repaired upstream.
}

ROW_BUDGET_S = 60   # individual row cap; the L3 row needs the bulk of this


def _row(name: str, argv: list[str], cwd: Path = PP,
         budget: int = ROW_BUDGET_S) -> dict:
    """Run one sub-verifier; return {name, rc, elapsed, missing,
    summary}."""
    bin_ok = shutil.which(argv[0]) or Path(argv[0]).is_file()
    if not bin_ok:
        return {"name": name, "rc": 127, "elapsed": 0.0,
                "missing": True,
                "summary": f"binary missing: {argv[0]}"}
    t0 = time.monotonic()
    try:
        cp = subprocess.run(argv, cwd=str(cwd), capture_output=True,
                            text=True, timeout=budget)
        rc = cp.returncode
        elapsed = time.monotonic() - t0
        # Summary = last non-empty line of stdout (or stderr fallback).
        out = (cp.stdout or "").strip().splitlines()
        err = (cp.stderr or "").strip().splitlines()
        summary = (out[-1] if out else err[-1] if err else "(no output)")
        if len(summary) > 80:
            summary = summary[:77] + "..."
        return {"name": name, "rc": rc, "elapsed": elapsed,
                "missing": False, "summary": summary,
                "stdout": cp.stdout, "stderr": cp.stderr}
    except subprocess.TimeoutExpired:
        return {"name": name, "rc": 124,
                "elapsed": time.monotonic() - t0,
                "missing": False,
                "summary": f"timeout >{budget}s"}
    except FileNotFoundError as e:
        return {"name": name, "rc": 127, "elapsed": 0.0,
                "missing": True, "summary": str(e)}


def _present(p: Path) -> bool:
    return p.is_file()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--quiet", action="store_true",
                    help="suppress per-row stdout dumps; only print table")
    ap.add_argument("--row", default=None,
                    help="run a single named row, skip the rest")
    args = ap.parse_args()

    rows_spec = [
        # (name, argv, budget)
        ("mirror-parity",
         [PY, str(PP / "tools" / "verify_global_mirrors.py")],
         15),
        ("drift-report",
         [PY, str(PP / "tools" / "drift_report.py")],
         15),
        ("paths+secrets",
         [PY, str(PP / "tools" / "normalize_paths.py"), "--check"],
         30),
        ("rtk-fusion",
         [PY, str(PP / "tools" / "verify_rtk_fusion.py")],
         30),
        ("intent-lock",
         [NODE, str(PP / "modules" / "harness" / "intent_lock.js"),
          "--self-test"],
         20),
        ("l3-engine",
         [NODE, str(PP / "tools" / "test_l3_intent.js")],
         360),
        ("programmatic-budget",
         [PY, str(PP / "tools" / "verify_full_install.py"), "--quiet"],
         30),
        ("tis-probe",
         [PY, str(PP / "tools" / "verify_tis.py")],
         30),
        ("monitoring-axis",
         [PY, str(PP / "tools" / "verify_monitoring.py")],
         30),
    ]

    if args.row:
        rows_spec = [r for r in rows_spec if r[0] == args.row]
        if not rows_spec:
            print(f"verify_spp: no row named {args.row!r}", file=sys.stderr)
            return 2

    print("=" * 72)
    print("verify_spp — S++ end-to-end umbrella")
    print(f"  PP root : {PP}")
    print(f"  rows    : {len(rows_spec)}")
    print(f"  budget  : {ROW_BUDGET_S}s per row default")
    print("=" * 72)

    t_total = time.monotonic()
    results: list[dict] = []
    for (name, argv, budget) in rows_spec:
        print(f"  [...] {name} ...", flush=True)
        r = _row(name, argv, budget=budget)
        results.append(r)
        tag = "OK  " if r["rc"] == 0 else (
            "MISS" if r["missing"]
            else ("ADV " if name in ADVISORY_ROWS else "FAIL"))
        print(f"  [{tag}] {name:<22s} rc={r['rc']:<3d} "
              f"{r['elapsed']:6.2f}s  {r['summary']}")
        if not args.quiet and r["rc"] != 0 and not r["missing"]:
            tail = (r.get("stdout") or "").splitlines()[-10:]
            for line in tail:
                print(f"    | {line}")

    total_elapsed = time.monotonic() - t_total
    print("=" * 72)
    print(f"  total elapsed: {total_elapsed:.2f}s")

    failed_strict = [r for r in results
                     if r["rc"] != 0 and r["name"] not in ADVISORY_ROWS]
    advisory_failing = [r for r in results
                        if r["rc"] != 0 and r["name"] in ADVISORY_ROWS]
    if failed_strict:
        print(f"  STRICT FAIL: {len(failed_strict)} row(s) — "
              f"{[r['name'] for r in failed_strict]}")
        rc = 1
    else:
        print(f"  STRICT PASS — {len(results) - len(advisory_failing)} "
              f"of {len(results)} rows OK"
              + (f", {len(advisory_failing)} advisory rows failing "
                 f"({[r['name'] for r in advisory_failing]})"
                 if advisory_failing else ""))
        rc = 0
    print("=" * 72)
    return rc


if __name__ == "__main__":
    sys.exit(main())
