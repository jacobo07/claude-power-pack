#!/usr/bin/env python3
"""test_duplicate_to_advantage.py -- done-gate for the D2A Engine (SCS C85).

V-D2A-* gates, hermetic (re-runnable ×3, byte-identical). Behavior gates over the engine
plus depth/no-duplicate gates over the doctrine dataset. Baseline gate re-runs the FD and
FIOS suites to prove no regression.

Run: python tools/test_duplicate_to_advantage.py [--json]
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.duplicate_to_advantage import (  # noqa: E402
    Proposal, run, OPERATIONS, ANTI_INFLATION_RULES, GAP_DIMENSIONS,
    PORTFOLIO_DIMENSIONS,
)
from modules.duplicate_to_advantage.d2a_engine import render  # noqa: E402

_KB = _PP_ROOT / "vault" / "knowledge_base" / "duplicate_to_advantage"
_DOCTRINE = _KB / "d2a_00_duplicate_to_advantage_doctrine.md"

# The canonical Token-Budget-Planner proposal (a genuine duplicate of FD-05 + budget owners).
_CANON = Proposal(
    "route the model budget, price frontier token cost as capital, plan reuse and "
    "deterministic conversion, adapt the session budget",
    "Token Budget Planner")
# A genuinely-novel proposal (should NOT be flagged as a high-coverage duplicate).
_NOVEL = Proposal("holographic tactile feedback surface for underwater sonar imaging",
                  "Sonar Haptics")

_passes = 0
_fails = 0
_log: list = []


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    _log.append(("PASS", gate, evidence))


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    _log.append(("FAIL", gate, diag))


def _part_word_counts(md_path: Path) -> list:
    """Words per top-level Part (## Part ...) section. Real prose words only (excludes the
    front-matter blockquote before the first Part)."""
    try:
        text = md_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    # Split on '## Part' headings.
    parts = re.split(r"(?m)^##\s+Part\b", text)
    counts = []
    for seg in parts[1:]:                       # [0] is the pre-Part front matter
        words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-]*", seg))
        counts.append(words)
    return counts


def _run_suite(script: str) -> tuple:
    """Run another test script; return (exit_code, tail)."""
    exe = sys.executable
    try:
        p = subprocess.run([exe, str(_PP_ROOT / "tools" / script)],
                           capture_output=True, text=True, cwd=str(_PP_ROOT), timeout=180)
        tail = (p.stdout or "").strip().splitlines()[-1:] or [""]
        return p.returncode, tail[0]
    except Exception as e:  # noqa: BLE001
        return 99, f"{type(e).__name__}"


def main(argv=None) -> int:
    as_json = "--json" in (argv or sys.argv[1:])

    v = run(_CANON)
    nov = run(_NOVEL)

    # V-D2A-DETECTION-SEMANTIC -- duplicate detected > 80%.
    if v.dupe.coverage_pct > 80 and v.dupe.is_duplicate:
        _ok("V-D2A-DETECTION-SEMANTIC",
            f"coverage={v.dupe.coverage_pct}% parent={v.dupe.parent_id} dup=True")
    else:
        _fail("V-D2A-DETECTION-SEMANTIC",
              f"coverage={v.dupe.coverage_pct}% dup={v.dupe.is_duplicate} (need >80% & True)")

    # V-D2A-GAP-MAPPED -- >= 8 of 14 dimensions classified.
    classified = sum(1 for x in v.gap.dimensions.values()
                     if x in ("covered", "partial", "absent"))
    if classified >= 8 and len(GAP_DIMENSIONS) == 14:
        _ok("V-D2A-GAP-MAPPED", f"{classified}/14 dims classified")
    else:
        _fail("V-D2A-GAP-MAPPED", f"{classified} classified, {len(GAP_DIMENSIONS)} dims")

    verticals = [c for c in v.portfolio if c.axis == "vertical"]
    horizontals = [c for c in v.portfolio if c.axis == "horizontal"]

    # V-D2A-VERTICAL-GENERATED -- >= 3 verticals with numeric scores.
    if len(verticals) >= 3 and all(c.scores and all(isinstance(x, (int, float))
                                                    for x in c.scores.values())
                                   for c in verticals):
        _ok("V-D2A-VERTICAL-GENERATED", f"{len(verticals)} verticals, all numeric")
    else:
        _fail("V-D2A-VERTICAL-GENERATED", f"{len(verticals)} verticals")

    # V-D2A-HORIZONTAL-GENERATED -- >= 3 horizontals with numeric scores.
    if len(horizontals) >= 3 and all(c.scores and all(isinstance(x, (int, float))
                                                     for x in c.scores.values())
                                    for c in horizontals):
        _ok("V-D2A-HORIZONTAL-GENERATED", f"{len(horizontals)} horizontals, all numeric")
    else:
        _fail("V-D2A-HORIZONTAL-GENERATED", f"{len(horizontals)} horizontals")

    # V-D2A-PORTFOLIO-SCORED -- every candidate carries all 16 dimension scores.
    dims16 = [k for k, _ in PORTFOLIO_DIMENSIONS]
    if len(dims16) == 16 and v.portfolio and all(
            set(c.scores.keys()) == set(dims16) for c in v.portfolio):
        _ok("V-D2A-PORTFOLIO-SCORED",
            f"{len(v.portfolio)} candidates x 16 dims each")
    else:
        bad = next((c.name for c in v.portfolio if set(c.scores.keys()) != set(dims16)),
                   "n/a")
        _fail("V-D2A-PORTFOLIO-SCORED", f"16 dims? {len(dims16)}; offender={bad}")

    # V-D2A-CONTRACT-MINIMAL -- Part over dataset when coverage warrants.
    if v.contract and v.contract.artifact == "dataset_part":
        _ok("V-D2A-CONTRACT-MINIMAL",
            f"artifact={v.contract.artifact} (not 'dataset') at coverage "
            f"{v.dupe.coverage_pct}%")
    else:
        got = v.contract.artifact if v.contract else "none"
        _fail("V-D2A-CONTRACT-MINIMAL", f"artifact={got} (expected dataset_part)")

    # V-D2A-ANTIINFLATION -- all 10 rules recorded on the contract.
    if (v.contract and len(ANTI_INFLATION_RULES) == 10
            and set(v.contract.anti_inflation.keys()) == set(ANTI_INFLATION_RULES)
            and all(isinstance(b, bool) for b in v.contract.anti_inflation.values())):
        npass = sum(1 for b in v.contract.anti_inflation.values() if b)
        _ok("V-D2A-ANTIINFLATION", f"10 rules recorded, {npass}/10 pass on canonical")
    else:
        _fail("V-D2A-ANTIINFLATION", "contract missing the 10-rule ledger")

    # V-D2A-NO-DUPLICATE -- registry references real sealed families; doctrine declares
    # non-duplication of each family axis. Also: exactly one prose dataset (not 6).
    from modules.duplicate_to_advantage.d2a_engine import FAMILY_REGISTRY
    real_ids = {"CO-01", "CO-03", "CO-05", "CO-08", "CO-12", "PM-02", "PM-03", "PM-04",
                "GK-01", "GK-04", "GK-08", "GK-09", "FD-01", "FD-03", "FD-05", "FD-06",
                "FIOS-EVO", "FIOS-IRR", "CDIO-05"}
    doctrine = _DOCTRINE.read_text(encoding="utf-8", errors="replace") if \
        _DOCTRINE.is_file() else ""
    n_datasets = len([p for p in _KB.glob("*.md")
                      if p.name.lower().startswith("d2a_")
                      and "index" not in p.name.lower()])
    declares = ("does NOT duplicate" in doctrine or "not duplicate" in doctrine.lower()
                or "non-duplication" in doctrine.lower())
    if set(FAMILY_REGISTRY.keys()) <= real_ids and declares and n_datasets == 1:
        _ok("V-D2A-NO-DUPLICATE",
            f"registry {len(FAMILY_REGISTRY)} real families; 1 prose dataset (anti-inflation)")
    else:
        _fail("V-D2A-NO-DUPLICATE",
              f"registry_ok={set(FAMILY_REGISTRY.keys()) <= real_ids} "
              f"declares={declares} datasets={n_datasets}")

    # V-D2A-DEPTH -- each doctrine Part > 2500 real words.
    counts = _part_word_counts(_DOCTRINE)
    if len(counts) >= 3 and all(c > 2500 for c in counts):
        _ok("V-D2A-DEPTH", f"{len(counts)} Parts, words={counts} (all >2500)")
    else:
        _fail("V-D2A-DEPTH", f"Parts={len(counts)} words={counts} (need 3x >2500)")

    # V-D2A-NUMERIC-BENCHMARKS -- every score in every candidate is a number 0-10.
    all_numeric = all(
        isinstance(x, (int, float)) and 0 <= x <= 10
        for c in v.portfolio for x in c.scores.values())
    if all_numeric and v.portfolio:
        _ok("V-D2A-NUMERIC-BENCHMARKS",
            f"all {len(v.portfolio)}x16 scores numeric in [0,10]")
    else:
        _fail("V-D2A-NUMERIC-BENCHMARKS", "a non-numeric or out-of-range score exists")

    # V-D2A-FAILOPEN -- pathological input -> DEFER, never raise.
    try:
        empty = run(Proposal("", ""))
        weird = run(Proposal("\x00﻿   ", "x" * 5000))
        if empty.contract is None and "DEFER" in empty.note and weird is not None:
            _ok("V-D2A-FAILOPEN", "empty -> DEFER; pathological -> no raise")
        else:
            _fail("V-D2A-FAILOPEN", f"empty.note={empty.note!r}")
    except Exception as e:  # noqa: BLE001
        _fail("V-D2A-FAILOPEN", f"raised {type(e).__name__} (must never raise)")

    # V-D2A-NOVEL-NOT-FLAGGED -- a genuinely-new proposal is not a high-coverage duplicate.
    if not nov.dupe.is_duplicate and nov.dupe.coverage_pct < 50:
        _ok("V-D2A-NOVEL-NOT-FLAGGED",
            f"novel coverage={nov.dupe.coverage_pct}% dup=False")
    else:
        _fail("V-D2A-NOVEL-NOT-FLAGGED",
              f"novel coverage={nov.dupe.coverage_pct}% dup={nov.dupe.is_duplicate}")

    # V-D2A-OPERATIONS -- exactly 15 operations; every candidate uses a valid one.
    if len(OPERATIONS) == 15 and "DO_NOT_BUILD" in OPERATIONS and all(
            c.operation in OPERATIONS for c in v.portfolio):
        _ok("V-D2A-OPERATIONS", "15 operations; every candidate uses a valid op")
    else:
        _fail("V-D2A-OPERATIONS", f"{len(OPERATIONS)} ops")

    # V-D2A-BASELINE -- FD + FIOS suites still green (no regression).
    fd_rc, fd_tail = _run_suite("test_fable_distillation.py")
    fi_rc, fi_tail = _run_suite("test_frontier_intelligence_os.py")
    if fd_rc == 0 and fi_rc == 0:
        _ok("V-D2A-BASELINE", f"FD rc=0 ({fd_tail}); FIOS rc=0 ({fi_tail})")
    else:
        _fail("V-D2A-BASELINE", f"FD rc={fd_rc}; FIOS rc={fi_rc}")

    total = _passes + _fails
    if as_json:
        import json
        print(json.dumps({"passes": _passes, "fails": _fails,
                          "log": [{"status": s, "gate": g, "evidence": e}
                                  for s, g, e in _log]}, indent=2))
    else:
        for status, gate, ev in _log:
            print(f"[{status}] {gate}: {ev}")
        print(f"\nD2A_PASS={_passes}/{total}  threshold={total}/{total}  "
              f"VERDICT={'PASS' if _fails == 0 else 'FAIL'}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
