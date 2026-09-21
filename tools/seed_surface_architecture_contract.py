#!/usr/bin/env python3
"""Seed the surface-architecture capability contract.

    python tools/seed_surface_architecture_contract.py [--force] [--dry-run]

Written THROUGH `capability_runtime.contract.save_contract` so the four executable
HR-APA rules run before anything reaches disk. A hand-authored JSON would skip them.

WHY EACH ECONOMIC FIELD HAS THE VALUE IT HAS
--------------------------------------------
These are not self-description. `applicability.evaluate` computes

    relevance = matched_triggers / TOTAL_triggers          (applicability.py:178)

so a generous trigger list is self-defeating: eight triggers matching one gives
relevance 0.125 and pushes the capability toward dormant. Four tight, high-precision
triggers are worth more reach than twelve loose ones.

Computed against a realistic mission naming two of the four triggers:

    benefit  = 0.50*0.30 + 0.50*0.25 + 1.00*0.15 + 1.00*0.15 + 0.25*0.15 = 0.6125
    penalty  = 0.333*0.10 + 0.333*0.08 + 0.333*0.05                      = 0.0767
    score    = 0.536   ->  RECOMMENDED

`failure_risk_if_omitted` is MEDIUM on purpose. HIGH would clear the MANDATORY
conjunct (score >= 0.55 AND failure_risk >= 3) and this capability does not deserve
it: a design-advisory decision whose absence costs a worse surface is not in the same
class as a secret crossing a boundary. A contract that overstates its own stake is the
"activate everything for safety" posture HR-APA-005 exists to refuse.

`required_evidence` is EMPTY, deliberately. Any name there is a hard gate
(applicability.py:151-155, BLOCKED_BY_MISSING_EVIDENCE before any scoring) compared as
free text against whatever the caller happened to pass. A plausible-sounding evidence
name no caller supplies blocks the capability permanently and silently. `_ratio(...,
empty=1.0)` then scores it 1.0, which is stated here so it is a decision rather than an
accident.

WHAT THIS CONTRACT DOES NOT DO, stated in its own non_scope: registering a capability
makes it DISCOVERABLE, not CALLABLE. `compile_stack` returns capability ids and never
invokes a capability (applicability.py:245-252). Building that dispatch is DS08, which
the binding NON_DUPLICATION_LEDGER reserves to hooks/hook-dispatcher.js.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.capability_runtime.contract import (  # noqa: E402
    CONTRACTS_DIR, CapabilityContract, save_contract,
)

CONTRACT_ID = "surface_architecture"

CONTRACT = dict(
    id=CONTRACT_ID,
    name="Surface Architecture Selection",
    owner="modules/surface_architecture",
    sovereign_question=(
        "Given this product's measured constraints, which entry-surface architecture "
        "is justified, and where do its boundaries fall?"),
    scope=[
        "surface architecture selection",
        "entry boundary placement",
    ],
    non_scope=[
        "visual quality and interaction behaviour",
        "which component realises a semantic",
        "authentication mechanics",
        "dispatching its own decision",
    ],
    # Four, tight. See the module docstring: relevance divides by this length.
    triggers=[
        "entry surface",
        "first-run",
        "activation path",
        "surface architecture",
    ],
    anti_triggers=[
        "single file",
        "typo",
    ],
    prerequisites=[],
    required_evidence=[],
    inputs=["measured product constraints"],
    outputs=[
        "a justified archetype or a named refusal",
        "boundary placements with their basis",
        "the alternatives rejected, and why",
    ],
    consumers=[
        "Owner",
        "Claude Code",
        "commands/surface-architecture.md",
    ],
    dependencies=[],
    permissions=[],
    write_surfaces=[],
    risk_class="reversible",
    activation_cost="low",
    context_cost="low",
    operational_cost="low",
    expected_leverage="high",
    failure_risk_if_omitted="medium",
    maturity="experimental",
    portable=True,
    compatible_runtimes=[],
    rollback="",
    kill_switch="",
    retirement_condition=(
        "a surface-architecture decision is produced and consumed by a live "
        "dispatch path, making this registry entry redundant"),
    parent="",
    version="1.0.0",
)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing contract with this id")
    ap.add_argument("--dry-run", action="store_true",
                    help="validate and report, write nothing")
    args = ap.parse_args(argv)

    target = CONTRACTS_DIR / f"{CONTRACT_ID}.json"
    existing = sorted(p.stem for p in CONTRACTS_DIR.glob("*.json"))
    print(f"contracts on disk before: {len(existing)}")

    # save_contract does an atomic REPLACE with no existence probe
    # (contract.py:198-206), so a colliding id silently overwrites a live contract.
    # Probe explicitly rather than trusting the id to be unique.
    if target.exists() and not args.force:
        print(f"REFUSED: {target.name} already exists. Re-run with --force only if "
              "you intend to overwrite a registered capability.")
        return 1

    # Construction is fail-closed: an invalid contract raises here, not on read.
    c = CapabilityContract(**CONTRACT)
    print(f"validated: {c.id}  escalates={c.escalates}")

    if args.dry_run:
        print("dry run: nothing written")
        return 0

    path = save_contract(c)
    after = sorted(p.stem for p in CONTRACTS_DIR.glob("*.json"))
    print(f"wrote {path.relative_to(_PP_ROOT)}")
    print(f"contracts on disk after: {len(after)}  (added: "
          f"{sorted(set(after) - set(existing))})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
