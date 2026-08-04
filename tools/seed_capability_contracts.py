#!/usr/bin/env python3
"""seed_capability_contracts.py -- the producer the capability layer lacked.

`capability_runtime` shipped as a reader with no writer: `contract.py` loads
contracts, `applicability.py` ranks them, `derivatives.py` specializes them, and
nothing on disk ever produced one. `/cpp-capability` answered "no capability
contracts found" -- a registry with no runtime, which is the anti-pattern the
proposal itself names.

This seeds the universal kernel set from capabilities THIS repo actually has.
Every contract below names a module or hook verified to exist; none describes an
aspiration. That is the whole discipline: a capability contract that does not
correspond to a live owner is a claim, and this registry stores no claims.

Idempotent and non-destructive: an existing contract file is left alone unless
--force is given, so hand-tuned fields survive a re-run.

Run:  python tools/seed_capability_contracts.py [--force] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.capability_runtime.contract import (  # noqa: E402
    CONTRACTS_DIR, CapabilityContract, ContractError, save_contract,
)

# The universal kernel set. Each entry cites the live owner it describes.
# Costs and risks are stated conservatively: over-stating leverage would bias
# every applicability score this registry ever produces.
KERNEL_CONTRACTS = [
    dict(
        id="premise_verification",
        name="Premise Verification",
        owner="modules/error_prevention/premise_verifier.py",
        sovereign_question="Do the files, functions and signatures this plan "
                           "names actually exist in this repo?",
        scope=["premise checking", "api existence"],
        non_scope=["code review", "test authoring"],
        triggers=["plan", "signature", "api", "refactor", "integrate",
                  "call", "import"],
        anti_triggers=["typo", "rename a string", "comment"],
        required_evidence=["source"],
        inputs=["a plan naming files or symbols"],
        outputs=["per-premise verdict", "the real public API on a miss"],
        consumers=["Claude Code", "modules/one_shot", "modules/spec_gate"],
        activation_cost="low", context_cost="low", operational_cost="low",
        expected_leverage="high", failure_risk_if_omitted="high",
        maturity="proven", risk_class="reversible",
        compatible_runtimes=["python", "node", "beam", "go", "rust", "jvm"],
        retirement_condition="the toolchain verifies symbol existence at edit "
                             "time for every supported language",
    ),
    dict(
        id="duplicate_detection",
        name="Duplicate-to-Advantage Detection",
        owner="modules/duplicate_to_advantage/d2a_engine.py",
        sovereign_question="Does an owner already hold the territory this "
                           "proposal claims?",
        scope=["overlap audit", "duplicate ownership"],
        non_scope=["building the proposed system"],
        triggers=["new system", "new module", "new dataset", "fabric",
                  "framework", "propose", "build", "corpus"],
        anti_triggers=["bug fix", "typo"],
        required_evidence=["source"],
        inputs=["a proposal", "the discovered module and family inventory"],
        outputs=["overlap verdict", "best adjacent capability"],
        consumers=["hooks/d2a_gate.js", "modules/spec_gate", "Owner"],
        activation_cost="medium", context_cost="medium", operational_cost="low",
        expected_leverage="high", failure_risk_if_omitted="critical",
        maturity="mature", risk_class="reversible",
        retirement_condition="proposals stop measuring majority-owned across "
                             "three consecutive audits",
    ),
    dict(
        id="liveness_reachability",
        name="Liveness and Reachability",
        owner="modules/liveness/reachability.py",
        sovereign_question="Is this shipped thing reachable from a live "
                           "surface, or does it merely exist?",
        scope=["reachability", "orphan detection"],
        non_scope=["judging value", "judging correctness"],
        triggers=["done", "ship", "complete", "module", "wire", "integrate",
                  "register"],
        anti_triggers=["draft", "sketch"],
        required_evidence=["source"],
        inputs=["the module tree", "the live dispatch table"],
        outputs=["per-module reachability verdict", "named standing debt"],
        consumers=["commands/liveness.md", "Owner", "done_gate"],
        activation_cost="low", context_cost="low", operational_cost="low",
        expected_leverage="high", failure_risk_if_omitted="high",
        maturity="proven", risk_class="reversible",
        retirement_condition="every module is registered at creation time by "
                             "construction",
    ),
    dict(
        id="secret_containment",
        name="Secret Firewall",
        owner="modules/secret_firewall",
        sovereign_question="Is a credential about to cross a boundary it can "
                           "never be recalled from?",
        scope=["secret detection", "redaction"],
        non_scope=["credential rotation", "key management"],
        triggers=["secret", "credential", "token", "api key", "env",
                  "commit", "push", "deploy"],
        anti_triggers=[],
        required_evidence=["source"],
        inputs=["file content", "emitted text"],
        outputs=["detection with pattern and line", "redacted text"],
        consumers=["hooks/secret_firewall_gate.js", "Owner"],
        activation_cost="low", context_cost="low", operational_cost="low",
        expected_leverage="high", failure_risk_if_omitted="critical",
        maturity="mature", risk_class="reversible",
        retirement_condition="never -- the failure is unrecoverable once it "
                             "occurs",
    ),
    dict(
        id="cascade_prevention",
        name="Cascade Error Prevention",
        owner="modules/cascade_prevention/engine.py",
        sovereign_question="Is this command the first link of a chain that has "
                           "ended badly before?",
        scope=["dangerous command interception", "cascade chains"],
        non_scope=["code review", "test execution"],
        triggers=["deploy", "delete", "remove", "reset", "force", "drop",
                  "migrate", "restart"],
        anti_triggers=["read", "list", "show"],
        required_evidence=["source"],
        inputs=["the pending command", "the recorded event history"],
        outputs=["block or allow with the matched chain"],
        consumers=["hooks/cascade_check_bash.js", "Owner"],
        activation_cost="low", context_cost="low", operational_cost="low",
        expected_leverage="high", failure_risk_if_omitted="critical",
        maturity="proven", risk_class="reversible",
        retirement_condition="the recorded chain set goes two years without a "
                             "new member",
    ),
    dict(
        id="spec_depth_selection",
        name="Adaptive Spec Depth",
        owner="modules/sdd_os",
        sovereign_question="How much specification does THIS task actually "
                           "need before the first edit?",
        scope=["spec tiering", "spec gate"],
        non_scope=["writing the implementation", "reviewing the result"],
        triggers=["feature", "endpoint", "migration", "integration", "agent",
                  "workflow", "module", "auth", "billing"],
        anti_triggers=["typo", "label", "comment", "rename"],
        required_evidence=["source"],
        inputs=["the task description", "the repo profile"],
        outputs=["tier T0-T3", "the minimum sufficient spec set"],
        consumers=["Claude Code", "modules/one_shot", "Owner"],
        activation_cost="low", context_cost="medium", operational_cost="low",
        expected_leverage="high", failure_risk_if_omitted="high",
        maturity="proven", risk_class="reversible",
        retirement_condition="spec omission stops appearing in the incident "
                             "record",
    ),
    dict(
        id="cost_routing",
        name="Model Cost Routing",
        owner="modules/cost_collapse/router.py",
        sovereign_question="What is the cheapest model that can still do this "
                           "task correctly?",
        scope=["model selection", "cost routing"],
        non_scope=["capability applicability", "skill loading"],
        triggers=["format", "lint", "rename", "search", "summarize", "test",
                  "document", "commit"],
        anti_triggers=["architecture", "security audit"],
        required_evidence=[],
        inputs=["the task description"],
        outputs=["route class", "recommended model"],
        consumers=["Claude Code", "modules/cognitive_os"],
        activation_cost="low", context_cost="low", operational_cost="low",
        expected_leverage="medium", failure_risk_if_omitted="medium",
        maturity="proven", risk_class="reversible",
        retirement_condition="model pricing converges so routing saves nothing",
    ),
    dict(
        id="output_quality_gate",
        name="Output Quality and Done Gate",
        owner="modules/done_gate",
        sovereign_question="Has this been observed to work, or only asserted "
                           "to work?",
        scope=["done gating", "output scoring"],
        non_scope=["writing the fix", "choosing the approach"],
        triggers=["done", "complete", "ready", "ship", "fixed", "works"],
        anti_triggers=["draft", "in progress", "exploring"],
        required_evidence=["source", "tests"],
        inputs=["the deliverable", "observed test output"],
        outputs=["quality score", "pass or block with the failing check"],
        consumers=["Claude Code", "Owner", "hooks/output_contract_stop.js"],
        activation_cost="low", context_cost="low", operational_cost="low",
        expected_leverage="high", failure_risk_if_omitted="critical",
        maturity="proven", risk_class="reversible",
        retirement_condition="never -- the Reality Contract depends on it",
    ),
    dict(
        id="architecture_reconstruction",
        name="Architecture Reconstruction",
        owner="modules/graphify",
        sovereign_question="What is the real structure here, as opposed to the "
                           "structure the names suggest?",
        scope=["architecture reconstruction", "dependency mapping"],
        non_scope=["deciding what to build", "specifying the change"],
        triggers=["architecture", "legacy", "reverse engineer", "cross-cutting",
                  "unclear", "lifecycle", "ownership", "undocumented"],
        anti_triggers=["single file", "typo"],
        required_evidence=["source"],
        inputs=["the repo tree", "the coordinate graph"],
        outputs=["contract graph", "uncertainty map"],
        consumers=["Claude Code", "modules/sdd_os", "Owner"],
        activation_cost="high", context_cost="high", operational_cost="medium",
        expected_leverage="high", failure_risk_if_omitted="critical",
        maturity="developing", risk_class="reversible",
        retirement_condition="the repo carries a maintained architecture "
                             "contract that is verified in CI",
    ),
]


def build() -> tuple:
    """Construct every kernel contract. Returns (contracts, errors)."""
    made, errs = [], []
    for spec in KERNEL_CONTRACTS:
        try:
            made.append(CapabilityContract(**spec))
        except ContractError as exc:
            errs.append(f"{spec.get('id')}: {exc}")
    return made, errs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Seed the universal capability contracts")
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing contract file")
    ap.add_argument("--dry-run", action="store_true",
                    help="validate and report; write nothing")
    ap.add_argument("--contracts-dir", default=None)
    args = ap.parse_args(argv)

    base = Path(args.contracts_dir) if args.contracts_dir else CONTRACTS_DIR
    contracts, errors = build()

    for e in errors:
        print(f"  INVALID {e}")

    written, skipped = 0, 0
    for c in contracts:
        target = base / f"{c.id}.json"
        if target.exists() and not args.force:
            skipped += 1
            print(f"  keep   {c.id} (exists)")
            continue
        if args.dry_run:
            print(f"  would  {c.id}")
            continue
        save_contract(c, base)
        written += 1
        print(f"  write  {c.id}")

    print(f"\nvalid={len(contracts)}/{len(KERNEL_CONTRACTS)} "
          f"written={written} kept={skipped} invalid={len(errors)}")
    print(f"contracts dir: {base}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
