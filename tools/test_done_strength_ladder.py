#!/usr/bin/env python3
"""V-gates for the DONE-strength ladder (LAW IX).

Every case below drives a branch. A ladder whose refusal paths nobody exercised
could have its comparisons deleted and report the same green.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.done_gate.strength_ladder import (  # noqa: E402
    LADDER,
    LADDER_FAILED,
    OVERSTATED,
    SUPPORTED,
    UNDETERMINED,
    assess,
    highest_supported,
)

PASSES = 0
FAILS = 0


def _ok(gate: str, evidence: str) -> None:
    global PASSES
    PASSES += 1
    print(f"  OK   {gate}  {evidence}")


def _fail(gate: str, diag: str) -> None:
    global FAILS
    FAILS += 1
    print(f"  FAIL {gate}  {diag}")


def check(gate: str, cond: bool, evidence: str) -> None:
    _ok(gate, evidence) if cond else _fail(gate, evidence)


FULL = {
    "spec_exists": True,
    "artifact_on_disk": True,
    "has_caller": True,
    "reachable_from_entrypoint": True,
    "activation_path_exists": True,
    "ran_at_least_once": True,
    "assertions_observed": True,
    "integration_boundary_exercised": True,
    "failure_branch_driven": True,
    "production_like_env_exercised": True,
    "real_boundary_exercised": True,
    "regression_case_pinned": True,
}


def main() -> int:
    # --- The motivating case -------------------------------------------------
    # Unit tests ran and passed; no real boundary was touched. A binary gate
    # calls this "done". The constitution calls it a vapor claim.
    unit_only = {k: True for k in (
        "spec_exists", "artifact_on_disk", "has_caller",
        "reachable_from_entrypoint", "activation_path_exists",
        "ran_at_least_once", "assertions_observed",
    )}
    unit_only["integration_boundary_exercised"] = False
    a = assess("PRODUCTION-REALITY-VERIFIED", unit_only)
    check("V-LADDER-VAPOR", a.outcome == OVERSTATED and a.highest_supported == "VERIFIED",
          f"unit evidence claiming production reality -> {a.outcome}, capped at {a.highest_supported}")

    # The same evidence, claimed honestly, must pass. A gate that refuses
    # everything is not a gate.
    a = assess("VERIFIED", unit_only)
    check("V-LADDER-HONEST", a.outcome == SUPPORTED,
          f"same evidence claimed as VERIFIED -> {a.outcome}")

    # --- Unknown is not a pass, and not a failure of the work ----------------
    a = assess("VERIFIED", {"spec_exists": True, "artifact_on_disk": True})
    check("V-LADDER-UNKNOWN", a.outcome == UNDETERMINED and a.unknown,
          f"uncollected evidence -> {a.outcome} ({len(a.unknown)} unknown)")
    check("V-LADDER-UNKNOWN-NOT-FAIL", a.outcome != OVERSTATED,
          "an unchecked claim is not reported as an overstated one")
    # Found by mutation probe: `r not in evidence` -> `r in evidence` survived,
    # because the assertion above only required the list to be non-empty.
    # Inverted, it names the evidence you DID collect as the evidence you are
    # missing -- same outcome, wrong fields, which is worse than a wrong verdict
    # because it sends you to re-check things already checked.
    check("V-LADDER-UNKNOWN-NAMES",
          "has_caller" in a.unknown and "spec_exists" not in a.unknown,
          "unknown list names the ABSENT evidence, not the present evidence")

    # Found by mutation probe: LADDER[0] -> LADDER[1] survived on the
    # failure path. A ladder that broke must report the WEAKEST rung; reporting
    # one rung up is a fail-open in the exact place fail-closed matters most.
    bad = assess("NOT-A-REAL-STATE", FULL)
    check("V-LADDER-FAIL-WEAKEST",
          bad.outcome == LADDER_FAILED and bad.highest_supported == LADDER[0],
          f"a failed ladder reports the weakest rung ({bad.highest_supported})")

    # --- Empty evidence cannot yield a strong rung ---------------------------
    best, _ = highest_supported({})
    check("V-LADDER-EMPTY", best == "IDEA",
          f"no evidence at all supports only {best}")

    # --- Full evidence reaches the top --------------------------------------
    a = assess("REGRESSION-PROVEN", FULL)
    check("V-LADDER-TOP", a.outcome == SUPPORTED,
          f"complete evidence -> {a.outcome} at {a.highest_supported}")

    # --- The ladder cannot be climbed by skipping ---------------------------
    # Real-boundary evidence present, but the thing was never wired. A naive
    # per-rung check would pass the top rung on its own requirement alone.
    skipped = dict(FULL)
    skipped["has_caller"] = False
    a = assess("PRODUCTION-REALITY-VERIFIED", skipped)
    check("V-LADDER-NOSKIP", a.outcome == OVERSTATED and a.highest_supported == "IMPLEMENTED",
          f"unwired artifact with real-boundary evidence -> {a.outcome}, capped at {a.highest_supported}")

    # --- Fail-closed on an unrecognised claim -------------------------------
    a = assess("TOTALLY-DONE", FULL)
    check("V-LADDER-UNKNOWN-STATE", a.outcome == LADDER_FAILED,
          f"invented state name -> {a.outcome} (not silently accepted)")

    # An unrecognised claim must not be quietly downgraded into a pass either.
    check("V-LADDER-NO-SILENT-DOWNGRADE", a.outcome != SUPPORTED,
          "an unrecognised state never resolves to SUPPORTED")

    # --- Case/format tolerance must not become a hole -----------------------
    a = assess("production_reality_verified", FULL)
    check("V-LADDER-NORMALISE", a.outcome == SUPPORTED,
          "underscore/lowercase spelling normalises to the same rung")

    # --- The ladder's own failure branch outranks a subject verdict ---------
    # Driven with a realistic caller error rather than a synthetic hostile
    # mapping. A first attempt used a dict subclass whose .get raised; assess's
    # own defensive dict(evidence) copy neutralised it, so that test reported a
    # clean UNDETERMINED while never reaching the branch it existed to drive --
    # an instrument failure wearing the costume of a product verdict.
    # A caller passing a count where an evidence map belongs is the real shape.
    a = assess("VERIFIED", 42)  # type: ignore[arg-type]
    check("V-LADDER-GATEFAIL", a.outcome == LADDER_FAILED,
          f"non-mapping evidence -> {a.outcome} (must not read as a subject verdict)")
    check("V-LADDER-GATEFAIL-NOT-PASS", a.outcome != SUPPORTED,
          "a ladder fault never resolves to SUPPORTED")

    # --- Structural: thirteen states, section 26 ----------------------------
    check("V-LADDER-THIRTEEN", len(LADDER) == 13, f"section 26 defines 13 states, ladder has {len(LADDER)}")

    print(f"LADDER_PASS={PASSES}/{PASSES + FAILS}  threshold={PASSES + FAILS}/{PASSES + FAILS}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
