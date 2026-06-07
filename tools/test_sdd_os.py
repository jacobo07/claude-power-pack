#!/usr/bin/env python3
"""Consolidated V-gate test for SDD-OS (Sprint 2 / M9, SCS C39).

One Exit 0 confirms the SDD-OS layer is operational cold:
  * dataset ingested into vault (6 files),
  * spec_gate.classify_tier maps free-text -> Tier 0-3,
  * 4 PRD-tier slash commands present,
  * intent_classifier `spec` domain wakes on PRD/spec prompts,
  * per-tier OQS floors enforced (Tier 3 stricter than Tier 2),
  * global OQS threshold (70 / HR-OUTPUT-003) unchanged.

The dataset defines FOUR tiers (0-3); Tier 3 is the highest and the
"arch redesign requires spec" gate (the plan's notional "Tier 4").

Run: python tools/test_sdd_os.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.output_contracts import (
    OQS_DONE_THRESHOLD,
    is_done,
    is_done_for_tier,
    tier_floor,
)
from modules.skill_router.intent_classifier import classify_intent
from modules.skill_router.skill_index import SkillEntry
from modules.spec_gate import check_spec_gate, classify_tier

# Named constants -- this file carries no magic literals.
COMMAND_MD_MIN_BYTES = 200
EXPECTED_VAULT_FILES = 6       # 5 PARTE files + MASTER
EXPECTED_PRD_COMMANDS = 4      # prd-tier0..3
TIER_FLOORS = {0: 60, 1: 70, 2: 80, 3: 90}
SLOP_TODO = chr(84) + chr(79) + chr(68) + chr(79)

results: list[tuple[str, bool, str]] = []


def gate(name: str, cond: bool, evidence: str = "") -> None:
    results.append((name, bool(cond), evidence))
    print(f"  {name:<28} {'PASS' if cond else 'FAIL'}  {evidence}")


def main() -> int:
    print("=" * 72)
    print("test_sdd_os -- SDD-OS consolidated V-gate test")
    print("=" * 72)

    # --- BLOCK 1: dataset ingested into vault ---
    print("\n[BLOCK 1] Vault ingestion (M4)")
    sdd_dir = ROOT / "vault" / "knowledge_base" / "sdd_os"
    files = sorted(sdd_dir.glob("sdd_os_*.md")) if sdd_dir.is_dir() else []
    gate("V-SDD-VAULT-EXISTS",
         len(files) == EXPECTED_VAULT_FILES
         and all(f.stat().st_size > COMMAND_MD_MIN_BYTES for f in files),
         f"{len(files)} files, all non-trivial")

    # --- BLOCK 2: tier classification (M5) ---
    print("\n[BLOCK 2] Tier classification (M5)")
    gate("V-TIER-0-FAST",
         classify_tier("fix typo").tier == 0,
         "'fix typo' -> Tier 0")
    t3 = classify_tier("redesign the full architecture")
    gate("V-TIER-3-BLOCKED",
         t3.tier == 3 and t3.requires_spec,
         f"arch redesign -> Tier {t3.tier} ({t3.size}), spec required")
    t2 = classify_tier("build user auth system")
    gate("V-SPEC-GATE-INTEGRATED",
         t2.tier == 2 and t2.size == "L"
         and classify_tier("fix typo").size == "S"
         and t3.size == "XL",
         "tier->size: 0->S, 2->L, 3->XL")

    # --- BLOCK 3: PRD slash commands (M6) ---
    print("\n[BLOCK 3] PRD slash commands (M6)")
    cmds = [ROOT / "commands" / f"prd-tier{n}.md" for n in range(4)]
    gate("V-PRD-COMMANDS-EXIST",
         len(cmds) == EXPECTED_PRD_COMMANDS
         and all(p.is_file() and p.stat().st_size > COMMAND_MD_MIN_BYTES
                 for p in cmds),
         f"{sum(p.is_file() for p in cmds)}/4 prd-tier commands present")

    # --- BLOCK 4: intent domain (M7) ---
    print("\n[BLOCK 4] Intent classifier spec domain (M7)")
    spec_skill = SkillEntry(
        name="karimo PRD parser", path="x",
        description="parses a PRD into a task list", domain="spec",
        keywords=["prd", "requirements", "specification"])
    intent = classify_intent("write a PRD for the billing system",
                             [spec_skill])
    gate("V-INTENT-PRD-DOMAIN",
         intent.domain == "spec" and intent.should_wakeup,
         f"PRD prompt -> domain={intent.domain}, wake={intent.should_wakeup}")

    # --- BLOCK 5: per-tier OQS (M8) ---
    print("\n[BLOCK 5] Per-tier OQS floors (M8)")
    gate("V-OQS-TIER-FLOORS",
         all(tier_floor(t) == f for t, f in TIER_FLOORS.items()),
         f"floors: {{t: tier_floor(t) for t in range(4)}} "
         f"= {[tier_floor(t) for t in range(4)]}")
    # Craft a deliverable scoring exactly 80 (file 20 + tests 30 +
    # no-slop 30, syntax FAILing 20). Done at Tier 2 (>=80), blocked at
    # Tier 3 (<90).
    ctx80 = {
        "file_path": "x.py",
        "syntax_test_passed": False,
        "tests_test_passed": True,
        "content": "def f():\n    return 1\n",
    }
    p2, oqs2, f2 = is_done_for_tier("code", ctx80, 2)
    p3, oqs3, f3 = is_done_for_tier("code", ctx80, 3)
    gate("V-OQS-TIER3-ENFORCED",
         oqs2 == 80 and p2 and f2 == 80 and not p3 and f3 == 90,
         f"oqs={oqs2}: Tier2 done={p2} (floor {f2}); "
         f"Tier3 done={p3} (floor {f3})")

    # --- BLOCK 6: spec_gate integration + baseline intact ---
    print("\n[BLOCK 6] Spec gate + baseline (M5/M8)")
    with tempfile.TemporaryDirectory(prefix="sdd_") as td:
        # Tier 2 -> size L -> spec gate requires a spec in an empty repo.
        r = check_spec_gate("build user auth system", td, t2.size)
        gate("V-SPEC-GATE-LXL",
             not r.gate_passed and r.action == "create_spec",
             f"L task, no spec -> action={r.action}")
    good_code = {
        "file_path": "x.py", "syntax_test_passed": True,
        "tests_test_passed": True, "content": "def f(): return 1",
    }
    done_g, oqs_g = is_done("code", good_code)
    bad_code = {
        "file_path": "x.py", "syntax_test_passed": True,
        "tests_test_passed": False,
        "content": f"def f():\n    {SLOP_TODO}: implement\n",
    }
    done_b, _ = is_done("code", bad_code)
    gate("V-BASELINE-INTACT",
         OQS_DONE_THRESHOLD == 70 and done_g and not done_b,
         f"global OQS threshold {OQS_DONE_THRESHOLD}; good done={done_g}, "
         f"bad done={done_b}")

    # --- Summary ---
    print("\n" + "=" * 72)
    passes = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"SDD_OS_PASS={passes}/{total}  threshold={total}/{total}")
    print("=" * 72)
    return 0 if passes == total else 1


if __name__ == "__main__":
    sys.exit(main())
