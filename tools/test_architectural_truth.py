#!/usr/bin/env python3
"""V-gates for LAW II (architectural truth) and its connection to LAW IX.

Section 15 asks for fixtures that distinguish a correctly reached target from
six ways of reaching one through an invalid state. Each case below is one of
those forms, expressed in the abstract vocabulary of section 8 rather than in
one domain's -- the law is universal and a fixture set drawn entirely from web
requests would prove it only there.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.done_gate.architectural_truth import (  # noqa: E402
    CANONICAL_PAIRS,
    GATE_FAILED,
    PROXY_ONLY,
    UNDETERMINED,
    VALID,
    Pair,
    assess_state,
    ceiling_for,
)
from modules.done_gate.strength_ladder import LADDER, assess  # noqa: E402

PASSES = 0
FAILS = 0


def check(gate: str, cond: bool, evidence: str) -> None:
    global PASSES, FAILS
    if cond:
        PASSES += 1
        print(f"  OK   {gate}  {evidence}")
    else:
        FAILS += 1
        print(f"  FAIL {gate}  {evidence}")


def main() -> int:
    # --- Form 0: target reached correctly. The gate must not cry wolf. -------
    v = assess_state({"http_200": True, "operation_happened_exactly_once": True})
    check("V-LAW2-CORRECT", v.outcome == VALID and v.ceiling is None,
          f"proxy with its corroborant -> {v.outcome}, no cap")

    # --- Form 1: side effect reported successful, not durably committed -----
    v = assess_state({"function_returned_success": True, "side_effect_committed": False})
    check("V-LAW2-NOT-DURABLE", v.outcome == PROXY_ONLY,
          f"success return, uncommitted effect -> {v.outcome}")

    # --- Form 2: invalid initialization behind a loaded artifact ------------
    v = assess_state({"file_loaded": True, "file_consumed_correctly": False})
    check("V-LAW2-INIT", v.outcome == PROXY_ONLY,
          f"loaded but not consumed -> {v.outcome}")

    # --- Form 3: UI visible while underlying state invalid ------------------
    v = assess_state({"screen_appeared": True, "app_state_initialized": False})
    check("V-LAW2-UI", v.outcome == PROXY_ONLY,
          f"screen painted over invalid state -> {v.outcome}")

    # --- Form 4: required upstream domain transition missing ----------------
    v = assess_state({"row_exists": True, "valid_domain_transition": False})
    check("V-LAW2-UPSTREAM", v.outcome == PROXY_ONLY,
          f"row written by a forbidden path -> {v.outcome}")

    # --- Form 5: test passing while intended path not exercised -------------
    # This is the exact defect the previous session hit in its own fixture.
    v = assess_state({"test_passed": True, "intended_path_exercised": False})
    check("V-LAW2-VACUOUS-TEST", v.outcome == PROXY_ONLY,
          f"green test that never reached its target -> {v.outcome}")

    # --- Form 6: process success while external effect disagrees ------------
    v = assess_state({"process_exit_zero": True, "external_effect_durable": False})
    check("V-LAW2-EXIT-ZERO", v.outcome == PROXY_ONLY,
          f"exit 0, external effect absent -> {v.outcome}")

    # --- Unchecked corroborant is UNDETERMINED, never a pass ----------------
    v = assess_state({"http_200": True})
    check("V-LAW2-UNCHECKED", v.outcome == UNDETERMINED and v.unknown,
          f"corroborant never looked for -> {v.outcome}")
    check("V-LAW2-UNCHECKED-CAPS", v.ceiling is not None,
          "an unchecked corroborant still caps the claim")

    # --- No proxy claimed: the law has nothing to say, and says so ----------
    v = assess_state({})
    check("V-LAW2-SILENT", v.outcome == UNDETERMINED and v.ceiling is None,
          "no proxy claimed -> no verdict, no cap (must not manufacture a finding)")

    # --- Domain extension: the law is universal, its instances are not ------
    firmware = (Pair("flash_write_returned_ok", "readback_matches",
                     "a write call is not a verified erase-program cycle"),)
    v = assess_state({"flash_write_returned_ok": True, "readback_matches": False},
                     extra_pairs=firmware)
    check("V-LAW2-DOMAIN-EXT", v.outcome == PROXY_ONLY,
          f"caller-registered firmware pair -> {v.outcome} (no web vocabulary needed)")

    # --- THE CONNECTION: LAW II must actually constrain LAW IX --------------
    # Evidence that would otherwise reach VERIFIED, but rests on a proxy.
    ev = {
        "spec_exists": True, "artifact_on_disk": True, "has_caller": True,
        "reachable_from_entrypoint": True, "activation_path_exists": True,
        "ran_at_least_once": True, "assertions_observed": True,
    }
    unconstrained = assess("VERIFIED", ev)
    cap = ceiling_for({"test_passed": True, "intended_path_exercised": False})
    capped_ok = (
        unconstrained.outcome == "SUPPORTED"
        and cap == "EXECUTED"
        and LADDER.index(cap) < LADDER.index("VERIFIED")
    )
    check("V-LAW2-CAPS-LADDER", capped_ok,
          f"ladder alone says {unconstrained.outcome} at VERIFIED; LAW II caps at {cap}")

    # --- Fail-closed on the checker's own fault -----------------------------
    v = assess_state(42)  # type: ignore[arg-type]
    check("V-LAW2-GATEFAIL", v.outcome == GATE_FAILED,
          f"non-mapping input -> {v.outcome} (not a verdict about the subject)")

    # --- Structural: section 8 states seven pairs ---------------------------
    check("V-LAW2-SEVEN", len(CANONICAL_PAIRS) == 7,
          f"section 8 states 7 pairs, registry has {len(CANONICAL_PAIRS)}")

    print(f"LAW2_PASS={PASSES}/{PASSES + FAILS}  threshold={PASSES + FAILS}/{PASSES + FAILS}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
