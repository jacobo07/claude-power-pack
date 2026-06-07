#!/usr/bin/env python3
"""V-gate test for the Sovereign Epics triage (SCS C42).

The triage outcome was "build nothing" (0 of 5 epics passed the ROI
gate). So this suite verifies the TRIAGE ARTIFACTS are real -- the
roadmap with per-epic verdicts + activation criteria, the sealed C42
gate -- AND, crucially, that NO orphan epic code was written (an
upper-layer epic with no lower layer would be an orphan by construction).

Hermetic: reads repo files + import checks only. Run:
  python tools/test_sovereign.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PARTS = ("XIX", "XX", "XXI", "XXII", "XXIII")
MIN_BYTES = 400

results: list[tuple[str, bool, str]] = []


def gate(name: str, cond: bool, evidence: str = "") -> None:
    results.append((name, bool(cond), evidence))
    print(f"  {name:<26} {'PASS' if cond else 'FAIL'}  {evidence}")


def main() -> int:
    print("=" * 72)
    print("test_sovereign -- Sovereign Epics triage (SCS C42)")
    print("=" * 72)

    roadmap = ROOT / "vault" / "plans" / "sovereign-roadmap.md"
    rm = roadmap.read_text(encoding="utf-8") if roadmap.is_file() else ""
    gate("V-ROADMAP-EXISTS",
         roadmap.is_file() and len(rm) > MIN_BYTES
         and all(f"PART {p}" in rm for p in PARTS),
         f"roadmap names all 5 parts ({len(rm)} bytes)")

    gate("V-ROADMAP-VERDICTS",
         rm.count("Verdict:") >= 5
         and rm.count("Activation criterion:") >= 5
         and "DEFER" in rm,
         f"{rm.count('Verdict:')} verdicts, "
         f"{rm.count('Activation criterion:')} activation criteria")

    seal = ROOT / "vault" / "knowledge_base" / "sovereign-epics.md"
    sl = seal.read_text(encoding="utf-8") if seal.is_file() else ""
    gate("V-SCS-C42-SEALED",
         seal.is_file() and "SCS C42" in sl
         and "useful-in-theory is not enough" in sl,
         "C42 ROI gate sealed with the doctrine line")

    # No orphan epic code: no module implementing a Sovereign epic exists
    # (the whole point of the DEFER -- building one in isolation = orphan).
    forbidden = (
        ROOT / "modules" / "sovereign",
        ROOT / "modules" / "setup_os" / "agent_fleet.py",
        ROOT / "modules" / "setup_os" / "control_plane.py",
        ROOT / "modules" / "setup_os" / "execution_runtime.py",
        ROOT / "modules" / "setup_os" / "assurance.py",
        ROOT / "modules" / "setup_os" / "governance_network.py",
    )
    present = [p.name for p in forbidden if p.exists()]
    gate("V-NO-ORPHAN-CODE",
         not present,
         f"no orphan epic module created (checked {len(forbidden)})")

    # Baseline: the real-gap modules still import (no regression).
    try:
        from modules.sdd_os import generate_prd  # noqa: F401
        from modules.setup_os.backlog_generator import generate_backlog  # noqa: F401
        from modules.setup_os.drift_detector import detect_drift  # noqa: F401
        baseline_ok = True
    except Exception as exc:  # pragma: no cover
        baseline_ok = False
        print(f"    import error: {exc}")
    gate("V-BASELINE-INTACT", baseline_ok,
         "build-everything modules still import clean")

    print("\n" + "=" * 72)
    passes = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"SOVEREIGN_PASS={passes}/{total}  threshold={total}/{total}")
    print("=" * 72)
    return 0 if passes == total else 1


if __name__ == "__main__":
    sys.exit(main())
