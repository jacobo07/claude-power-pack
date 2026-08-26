#!/usr/bin/env python3
"""V-COST-* -- the two cost-contract detectors added to UQF.

Both founding bugs are already fixed, so neither can be found in the tree.
A detector proven only against a repo that no longer contains the defect is
a detector proven against nothing, so each gate reconstructs the ORIGINAL
code from the commit that broke it. Gates must survive the fix.

  WIDENING AN INPUT CONTRACT MUST NOT WIDEN THE NO-INPUT PATH.
  INCREMENTALITY IS AN END-TO-END COST PROPERTY, NOT A LOCAL LOOP ONE.
"""
from __future__ import annotations

import sys
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PP))

from modules.uqf.anti_patterns import (  # noqa: E402
    detect_false_incrementality, detect_widened_fast_path, run_all)

EXPECTED_GATES = 8
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


# The shape of cascade.evaluate() as commit 44a8f7f left it: the store
# parse hoisted above the guard that used to make the common case free.
BROKEN_FAST_PATH = '''
def evaluate(current_error, project, category=None, subsystem=None):
    cascade_map = _build_cascade_map()
    if not category and not current_error:
        return None
    return cascade_map.get(category)
'''

# The same function after 064d29b: guard first, work second.
FIXED_FAST_PATH = '''
def evaluate(current_error, project, category=None, subsystem=None):
    if not category and not current_error:
        return None
    cascade_map = _build_cascade_map()
    return cascade_map.get(category)
'''

# A deliberate flag check placed after setup. Exits early, but is NOT a
# fast path -- this exact shape was the detector's only false positive.
FLAG_GUARD = '''
def cmd_migrate(args):
    files = list(SOME_DIR.glob("*.md"))
    if args.dry_run:
        return 0
    return len(files)
'''

# audit_cache.refresh_paths() as first written: given the exact files to
# refresh, it rebuilt the whole project's stem map. 3016 ms for one file.
BROKEN_INCREMENTAL = '''
def refresh_paths(project, rels):
    stem_map = build_stem_map(project)
    for rel in rels:
        reindex(rel, stem_map)
'''

# After the fix: the global part is persisted and reused.
FIXED_INCREMENTAL = '''
def refresh_paths(project, rels):
    stem_map = cache.get("stem_map") or {}
    for rel in rels:
        reindex(rel, stem_map)
'''


def main() -> int:
    print("V-COST -- fast-path and incrementality cost contracts")

    hits = detect_widened_fast_path(BROKEN_FAST_PATH)
    if len(hits) == 1 and "_build_cascade_map" in hits[0].snippet:
        _ok("V-COST-FASTPATH-CATCHES-FOUNDING-BUG",
            f"line {hits[0].line}: {hits[0].snippet}")
    else:
        _fail("V-COST-FASTPATH-CATCHES-FOUNDING-BUG",
              f"expected 1 hit on the pre-fix shape, got {hits}")

    if not detect_widened_fast_path(FIXED_FAST_PATH):
        _ok("V-COST-FASTPATH-BOOKEND-FIXED-IS-CLEAN",
            "guard-before-work produces no hit")
    else:
        _fail("V-COST-FASTPATH-BOOKEND-FIXED-IS-CLEAN",
              "flagged the CORRECT ordering")

    if not detect_widened_fast_path(FLAG_GUARD):
        _ok("V-COST-FASTPATH-BOOKEND-FLAG-IS-NOT-A-FASTPATH",
            "`if args.dry_run: return` is a flag check, not an input guard")
    else:
        _fail("V-COST-FASTPATH-BOOKEND-FLAG-IS-NOT-A-FASTPATH",
              "a deliberate flag check was read as a fast path")

    hits = detect_false_incrementality(BROKEN_INCREMENTAL)
    if len(hits) == 1 and "build_stem_map" in hits[0].snippet:
        _ok("V-COST-INCREMENTAL-CATCHES-FOUNDING-BUG",
            f"line {hits[0].line}: {hits[0].snippet}")
    else:
        _fail("V-COST-INCREMENTAL-CATCHES-FOUNDING-BUG",
              f"expected 1 hit on the pre-fix shape, got {hits}")

    if not detect_false_incrementality(FIXED_INCREMENTAL):
        _ok("V-COST-INCREMENTAL-BOOKEND-FIXED-IS-CLEAN",
            "persisted global part produces no hit")
    else:
        _fail("V-COST-INCREMENTAL-BOOKEND-FIXED-IS-CLEAN",
              "flagged the CORRECTED function")

    # A detector that flags the vocabulary it is written in is unusable.
    self_code = (PP / "modules" / "uqf" / "anti_patterns.py").read_text(
        encoding="utf-8-sig")
    self_hits = detect_false_incrementality(self_code)
    if not self_hits:
        _ok("V-COST-ANALYTICAL-EXEMPTION",
            "the detector module does not flag its own detectors")
    else:
        _fail("V-COST-ANALYTICAL-EXEMPTION", f"self-flagged: {self_hits}")

    # Registered, or it only ever runs from a test.
    reg = run_all("def f(a):\n    return a\n")
    for name in ("detect_widened_fast_path", "detect_false_incrementality"):
        if name not in reg:
            _fail("V-COST-REGISTERED", f"{name} missing from run_all")
            break
    else:
        _ok("V-COST-REGISTERED", "both detectors reachable through run_all")

    # Precision, measured on the estate rather than asserted. Three
    # tightening passes took this from 24 candidates to 2; a regression in
    # precision is a regression in the detector's usefulness.
    skip = {"__pycache__", ".git", "node_modules"}
    found = []
    for p in sorted(PP.rglob("*.py")):
        if any(s in p.parts for s in skip):
            continue
        try:
            code = p.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        for fn in (detect_widened_fast_path, detect_false_incrementality):
            for h in fn(code):
                found.append(f"{p.relative_to(PP).as_posix()}:{h.line}")
    if len(found) <= 4:
        _ok("V-COST-ESTATE-PRECISION",
            f"{len(found)} candidate(s) across the estate: {found}")
    else:
        _fail("V-COST-ESTATE-PRECISION",
              f"{len(found)} candidates -- precision regressed: {found[:8]}")

    total = _passes + _fails
    print(f"COST_CONTRACTS_PASS={_passes}/{total}  "
          f"threshold={EXPECTED_GATES}/{EXPECTED_GATES}")
    if total != EXPECTED_GATES:
        print(f"FAIL: {total} gates executed, {EXPECTED_GATES} declared")
        return 1
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
