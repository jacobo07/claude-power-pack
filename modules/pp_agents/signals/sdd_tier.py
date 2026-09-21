"""pp-sdd-tier signal -- SDD-OS tier classification + spec/PRD requirement.

Classifies the prompt into an SDD-OS Tier (0-3) via spec_gate.classify_tier,
then -- only for Tier >= 2 (Feature/System and Strategic/Platform) -- checks
whether the active repo has a spec. Fires ONE advisory naming the tier and the
missing spec. Silent for Tier 0-1 (micro/standard work: silence = approval) and
when a spec already exists.

Cross-repo by construction: takes the active cwd, no hardcoded paths. Composes
the existing cwd-aware primitives (SCS C28) -- classify_tier + check_spec_gate.

Takes the spec-governance slot in the dispatcher (richer than spec_compliance:
adds the tier). Sealed BL-GOV-PROP-001 (2026-06-08, SCS C43).
"""
from __future__ import annotations

import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[3]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.pp_agents.proactive_core import ProactiveSignal

_TIER_LABEL = {2: "Feature/System", 3: "Strategic/Platform"}


def evaluate(prompt: str = "",
             cwd: str = "",
             project: str = "global") -> ProactiveSignal | None:
    """Fire when a Tier >= 2 prompt starts in a repo with no spec."""
    if not prompt:
        return None
    try:
        from modules.spec_gate.gate import classify_tier, check_spec_gate
    except Exception:
        return None
    try:
        tier = classify_tier(prompt)
    except Exception:
        return None
    # Silence for Tier 0 (micro) and Tier 1 (standard) -- no spec needed.
    if tier.tier < 2:
        return None
    try:
        root = Path(cwd) if cwd else Path.cwd()
        gate = check_spec_gate(prompt, cwd=root, task_size=tier.size)
    except Exception:
        return None
    # Spec already exists (gate_passed / read_spec) -> stay silent; the tier is
    # informational only once the spec is in place.
    if gate.gate_passed or gate.action != "create_spec":
        return None
    label = _TIER_LABEL.get(tier.tier, "Feature/System")
    advisory = (
        f"SDD-OS Tier {tier.tier} ({label}) task in this repo, and no spec "
        f"was found ({tier.reason}). Tier >= 2 requires a spec/PRD BEFORE "
        f"coding -- the scope and done-gate belong in the spec, not in the "
        f"agent's head."
    )
    actionable = (
        "Establish the spec first: the auto-injected One-Shot contract "
        "(scope + done-gate + budget), or python "
        "modules/karimo-harness/prd_parser.py <prd> for a full PRD."
    )

    # UCR-CIF W6 -- the second consumption boundary's MATERIAL effect.
    #
    # This is the live surface. The gate's `message` is not: the JIT's One-Shot
    # injector calls compile_contract with no cwd (so it never reaches the gate
    # at all), and this function previously read `gate_passed` and `action` and
    # threw `message` away. Enriching prose nobody renders would have been a
    # reader, not a consumer -- the exact distinction W5 was called to make.
    #
    # Read the SELECTION, never the prose: `routing` is the machine-readable
    # field the gate compiled, so no consumer parses another's sentences and
    # there is no second selector. Owner paths and unit counts only -- no uids,
    # no evidence terms, no unit bodies (progressive disclosure); whoever wants
    # more has the ledger named below.
    owned = []
    try:
        routed = getattr(gate.routing, "owners", ()) or ()
        owned = [(o.owner, o.units) for o in routed]
    except Exception:  # noqa: BLE001 -- institutional state never blocks
        owned = []

    if owned:
        named = "; ".join(f"{path} ({n} authoritative disposition(s))"
                          for path, n in owned)
        advisory += (
            f" UCR-CIF has ADJUDICATED evidence that this is already owned: "
            f"{named}. A spec that creates something new here has to refute "
            f"that with file:line evidence -- absence of a spec is not "
            f"absence of an owner."
        )
        actionable = (
            f"INSPECT the named owner(s) BEFORE writing the spec -- {named} "
            f"-- and record in the spec, per owner, whether you are extending "
            f"it or why extending it is insufficient. Then establish the spec: "
            f"the auto-injected One-Shot contract, or python "
            f"modules/karimo-harness/prd_parser.py <prd>. Provenance: "
            f"vault/ucr_cif/disposition_ledger.json (AUTHORITATIVE, reviewed; "
            f"candidates, rejections and abstentions excluded)."
        )

    return ProactiveSignal(
        agent_name="pp-sdd-tier",
        trigger="tier_spec_required",
        value=0.7 if tier.tier == 2 else 0.85,
        advisory=advisory,
        gate="jobs",
        actionable=actionable,
    )


__all__ = ["evaluate"]
