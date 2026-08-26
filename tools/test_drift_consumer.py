#!/usr/bin/env python3
"""V-DRIFT-* -- the drift comparator can actually get an inventory.

`verify_global_mirrors` was migrated from a hand-curated `PAIRS` constant
to `mirror_discovery.discover()`, which finds pairs from what is on disk.
`drift_report._load_pairs()` still imported the retired constant, so
`getattr(mod, "PAIRS", None)` returned None and the tool exited 2 -- a
CONFIGURATION error -- on every run since.

The comparator was never broken. Nothing could hand it anything to
compare. A detector whose input is unreachable is not protection, and the
failure looked like a config problem rather than the dead consumer it was.
"""
from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PP))
sys.path.insert(0, str(PP / "tools"))

PY = sys.executable
DRIFT = PP / "tools" / "drift_report.py"

EXPECTED_GATES = 5
_passes = 0
_fails = 0


def _ok(g: str, e: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {g}: {e}")


def _fail(g: str, d: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {g}: {d}")


def main() -> int:
    print("V-DRIFT -- the canonical/live comparator has a reachable inventory")

    import drift_report  # noqa: PLC0415

    pairs = drift_report._load_pairs()
    if pairs:
        _ok("V-DRIFT-INVENTORY-REACHABLE",
            f"{len(pairs)} mirror pair(s) discovered from disk")
    else:
        _fail("V-DRIFT-INVENTORY-REACHABLE",
              "_load_pairs() returned nothing -- the comparator has no input")
        pairs = []

    # The retired symbol must not come back as a dependency -- asserted on
    # the AST, not on the text. A first version grepped the source and
    # failed on this module's own docstring, which NAMES the retired call
    # while explaining why it is gone. A detector that its own explanation
    # trips is measuring prose, not code.
    tree = ast.parse(DRIFT.read_text(encoding="utf-8-sig"))
    imported = {
        (n.module or "") for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom)
    } | {
        a.name for n in ast.walk(tree) if isinstance(n, ast.Import)
        for a in n.names
    }
    dynamic = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
               and getattr(n.func, "attr", "") == "spec_from_file_location"]
    if any("mirror_discovery" in m for m in imported) and not dynamic:
        _ok("V-DRIFT-NO-RETIRED-SYMBOL",
            "imports mirror_discovery; no dynamic load of the retired module")
    else:
        _fail("V-DRIFT-NO-RETIRED-SYMBOL",
              f"mirror_discovery imported={any('mirror_discovery' in m for m in imported)}, "
              f"dynamic spec loads={len(dynamic)}")

    # Pairs must be (live, repo) string 2-tuples, which is what _classify
    # unpacks. A shape mismatch here is how the last breakage hid.
    bad = [p for p in pairs[:50]
           if not (isinstance(p, tuple) and len(p) == 2
                   and all(isinstance(s, str) for s in p))]
    if pairs and not bad:
        _ok("V-DRIFT-PAIR-SHAPE", "every pair is a (live, repo) str 2-tuple")
    elif not pairs:
        _fail("V-DRIFT-PAIR-SHAPE", "no pairs to check")
    else:
        _fail("V-DRIFT-PAIR-SHAPE", f"{len(bad)} malformed, e.g. {bad[0]!r}")

    # Exit code must mean drift, never "could not run". 2 is the
    # configuration error this tool has been returning for months.
    run = subprocess.run([PY, str(DRIFT)], capture_output=True, text=True,
                         timeout=180)
    if run.returncode in (0, 1):
        _ok("V-DRIFT-EXIT-MEANS-DRIFT",
            f"exit {run.returncode} (0=clean, 1=drift), not a config error")
    else:
        _fail("V-DRIFT-EXIT-MEANS-DRIFT",
              f"exit {run.returncode}: {(run.stderr or '').strip()[:120]}")

    # And it must actually name what drifted, or the report is a number.
    out = run.stdout or ""
    if "mirror pair(s)" in out and re.search(r"\[(equal|pp-ahead|loose-ahead)\]", out):
        _ok("V-DRIFT-NAMES-THE-FILES",
            "report groups pairs by verdict with per-file detail")
    else:
        _fail("V-DRIFT-NAMES-THE-FILES", f"unexpected report: {out[:120]!r}")

    total = _passes + _fails
    print(f"DRIFT_CONSUMER_PASS={_passes}/{total}  "
          f"threshold={EXPECTED_GATES}/{EXPECTED_GATES}")
    if total != EXPECTED_GATES:
        print(f"FAIL: {total} gates executed, {EXPECTED_GATES} declared")
        return 1
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
