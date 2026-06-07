#!/usr/bin/env python3
"""Consolidated V-gate test for the build-everything real-gap modules
(SCS C41). Covers the 3 systems built (the genuine gaps; the ~8 overlaps
were intentionally NOT duplicated):

  * A1 modules/sdd_os/prd_generator   -- tier-aware PRD scaffold
  * B2 modules/setup_os/backlog_generator -- ROI -> backlog bridge
  * B3 modules/setup_os/drift_detector    -- repo-config drift

Includes a no-duplication gate: the new modules COMPOSE the existing
classify_tier / what_now / scan (same object identity), proving SCS C28
was honored rather than re-implementing.

Hermetic (temp repos). Run: python tools/test_build_everything.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import modules.backlog_autopilot as _ba
import modules.setup_os.scanner as _scn
import modules.spec_gate as _sg
from modules.sdd_os import generate_prd, render_prd
from modules.sdd_os import prd_generator as _prd
from modules.setup_os import backlog_generator as _blg
from modules.setup_os.backlog_generator import generate_backlog, recommend
from modules.setup_os.drift_detector import detect_drift, snapshot

MIN_TIER2_SECTIONS = 8
MIN_BACKLOG = 5

results: list[tuple[str, bool, str]] = []


def gate(name: str, cond: bool, evidence: str = "") -> None:
    results.append((name, bool(cond), evidence))
    print(f"  {name:<26} {'PASS' if cond else 'FAIL'}  {evidence}")


def main() -> int:
    print("=" * 72)
    print("test_build_everything -- real-gap modules (SCS C41)")
    print("=" * 72)

    # --- BLOCK A: PRD generator (A1) ---
    print("\n[BLOCK A] PRD generator")
    p2 = generate_prd("build user auth system")
    gate("V-PRD-TIER2",
         p2.tier == 2 and len(p2.sections) >= MIN_TIER2_SECTIONS
         and "Architecture Spec" in p2.section_titles(),
         f"tier2 -> {len(p2.sections)} sections incl Architecture Spec")
    p0 = generate_prd("fix typo")
    gate("V-PRD-TIER0",
         p0.tier == 0 and p0.section_titles() == ["Mini-spec"],
         "typo -> Tier 0 mini-spec only")
    md = render_prd(p2)
    gate("V-PRD-RENDER",
         md.startswith("# PRD -- Tier 2") and "## Problem" in md,
         "renders tier-2 markdown with real section headers")

    # --- BLOCK B: backlog generator (B2) ---
    print("\n[BLOCK B] Backlog generator")
    with tempfile.TemporaryDirectory(prefix="be_bl_") as td:
        r = Path(td)
        (r / "app.py").write_text("x = 1\n", encoding="utf-8")
        (r / ".env").write_text("DB=postgres://x\n", encoding="utf-8")
        entries = generate_backlog(str(r))
        gate("V-BACKLOG-GENERATES",
             len(entries) >= MIN_BACKLOG
             and entries[0].item.priority == 0
             and all(e.done_gate for e in entries),
             f"{len(entries)} entries, first P0, all have done-gates")
        rec = recommend(str(r))
        gate("V-BACKLOG-NEXT",
             rec.recommended is not None
             and rec.recommended.id == "secret-firewall",
             f"what_now picks {rec.recommended.id if rec.recommended else None}")

    # --- BLOCK C: drift detector (B3) ---
    print("\n[BLOCK C] Drift detector")
    with tempfile.TemporaryDirectory(prefix="be_dr_") as td:
        r = Path(td)
        (r / "app.py").write_text("x = 1\n", encoding="utf-8")
        (r / "settings.json").write_text('{"a":1}\n', encoding="utf-8")
        base = snapshot(str(r))
        clean = detect_drift(str(r), base)
        gate("V-DRIFT-CLEAN",
             not clean.drifted and not clean.baseline_missing,
             "unchanged repo -> no drift")
        (r / "settings.json").write_text('{"a":2}\n', encoding="utf-8")
        moved = detect_drift(str(r), base)
        gate("V-DRIFT-DETECTS",
             moved.drifted and any(i.name == "settings.json"
                                   for i in moved.items),
             f"settings.json change -> {len(moved.items)} drift item(s)")
        missing = detect_drift(str(r), r / "nope.json")
        gate("V-DRIFT-NO-BASELINE",
             missing.baseline_missing and not missing.drifted,
             "missing baseline -> graceful (not a crash)")

    # --- BLOCK D: no duplication (SCS C28) ---
    print("\n[BLOCK D] Composition, not duplication (SCS C28)")
    gate("V-COMPOSE-NO-DUP",
         _prd.classify_tier is _sg.classify_tier
         and _blg.what_now is _ba.what_now
         and _blg.scan is _scn.scan,
         "prd_generator/backlog_generator reuse the canonical primitives")

    print("\n" + "=" * 72)
    passes = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"BUILD_EVERYTHING_PASS={passes}/{total}  threshold={total}/{total}")
    print("=" * 72)
    return 0 if passes == total else 1


if __name__ == "__main__":
    sys.exit(main())
