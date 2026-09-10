#!/usr/bin/env python3
"""DONE-strength ladder -- LAW IX, "NO VAPOR DONE".

    The strength of a completion claim may never exceed the strength of its
    evidence.

Power Pack's existing done-gate answers a binary question: done, or not done.
That shape cannot express the constitution's actual requirement, because the
interesting failure is not "claimed done while broken" -- it is "claimed
PRODUCTION-REALITY VERIFIED while holding unit-test evidence". Both are green
under a binary gate. Only a graded one can tell them apart.

Section 26 defines thirteen states. This module grades a claim against the
evidence actually collected and refuses claims stronger than that evidence.

Three outcomes, because two is the bug
--------------------------------------
A guard that cannot evaluate must never return the same answer as a guard that
passed. Evidence here is deliberately three-valued:

    True     the evidence was collected and is positive
    False    the evidence was collected and is negative
    absent   nobody looked

An absent input yields UNDETERMINED, never a pass. "We did not check" and "we
checked and it was fine" are different states of the world, and collapsing them
is how a completion claim launders an unknown into a green.

Fail-closed
-----------
An unrecognised state name resolves to the weakest reading, not the strongest.
Absence is never the ambient default.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Section 26, in order. Index is the strength; later strictly outranks earlier.
LADDER: tuple[str, ...] = (
    "IDEA",
    "SPECIFIED",
    "IMPLEMENTED",
    "WIRED",
    "REACHABLE",
    "ACTIVATABLE",
    "EXECUTED",
    "VERIFIED",
    "INTEGRATION-VERIFIED",
    "ADVERSARIALLY-VERIFIED",
    "PRODUCTION-LIKE-VERIFIED",
    "PRODUCTION-REALITY-VERIFIED",
    "REGRESSION-PROVEN",
)

# What each rung demands. A rung inherits every requirement below it, so the
# ladder cannot be climbed by skipping. Keys are evidence names a caller
# supplies; the vocabulary is deliberately small and observable.
REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "IDEA": (),
    "SPECIFIED": ("spec_exists",),
    "IMPLEMENTED": ("artifact_on_disk",),
    "WIRED": ("has_caller",),
    "REACHABLE": ("reachable_from_entrypoint",),
    "ACTIVATABLE": ("activation_path_exists",),
    "EXECUTED": ("ran_at_least_once",),
    "VERIFIED": ("assertions_observed",),
    "INTEGRATION-VERIFIED": ("integration_boundary_exercised",),
    "ADVERSARIALLY-VERIFIED": ("failure_branch_driven",),
    "PRODUCTION-LIKE-VERIFIED": ("production_like_env_exercised",),
    "PRODUCTION-REALITY-VERIFIED": ("real_boundary_exercised",),
    "REGRESSION-PROVEN": ("regression_case_pinned",),
}

SUPPORTED = "SUPPORTED"
OVERSTATED = "OVERSTATED"
UNDETERMINED = "UNDETERMINED"
LADDER_FAILED = "LADDER_FAILED"


@dataclass
class Assessment:
    outcome: str
    claimed: str
    highest_supported: str
    missing: list[str] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    detail: str = ""

    def render(self) -> str:
        lines = [f"claim: {self.claimed}  ->  {self.outcome}"]
        lines.append(f"  evidence supports at most: {self.highest_supported}")
        for m in self.missing:
            lines.append(f"  NEGATIVE  {m}   (checked, and it failed)")
        for u in self.unknown:
            lines.append(f"  UNKNOWN   {u}   (nobody looked -- not a pass)")
        if self.detail:
            lines.append(f"  {self.detail}")
        return "\n".join(lines)


def _cumulative_requirements(index: int) -> list[str]:
    reqs: list[str] = []
    for rung in LADDER[: index + 1]:
        for r in REQUIREMENTS[rung]:
            if r not in reqs:
                reqs.append(r)
    return reqs


def highest_supported(evidence: dict[str, bool]) -> tuple[str, list[str]]:
    """Return the strongest rung the evidence actually supports.

    Stops at the first rung with a negative or unknown requirement. Returns the
    rung below it -- never the rung being reached for.
    """
    unknowns: list[str] = []
    best = LADDER[0]
    for i, rung in enumerate(LADDER):
        ok = True
        for req in _cumulative_requirements(i):
            val = evidence.get(req)
            if val is None:
                if req not in unknowns:
                    unknowns.append(req)
                ok = False
            elif val is False:
                ok = False
        if not ok:
            break
        best = rung
    return best, unknowns


def assess(claimed: str, evidence: dict[str, bool] | None = None) -> Assessment:
    """Grade a completion claim against collected evidence."""
    try:
        evidence = dict(evidence or {})
        # Normalise, fail-closed: an unrecognised claim is not silently
        # upgraded, downgraded, or ignored -- it is refused.
        key = str(claimed).strip().upper().replace("_", "-").replace(" ", "-")
        if key not in LADDER:
            return Assessment(
                LADDER_FAILED, str(claimed), LADDER[0],
                detail=f"unrecognised state {claimed!r}; not one of section 26's thirteen",
            )

        claim_index = LADDER.index(key)
        best, unknowns = highest_supported(evidence)
        best_index = LADDER.index(best)

        required = _cumulative_requirements(claim_index)
        negative = [r for r in required if evidence.get(r) is False]
        unknown_for_claim = [r for r in required if r not in evidence]

        if unknown_for_claim and not negative and best_index < claim_index:
            return Assessment(
                UNDETERMINED, key, best, unknown=unknown_for_claim,
                detail="cannot judge this claim: required evidence was never "
                       "collected. This is not a failure of the work.",
            )
        if best_index < claim_index:
            return Assessment(
                OVERSTATED, key, best, missing=negative, unknown=unknown_for_claim,
                detail=f"claim outruns evidence by {claim_index - best_index} rung(s)",
            )
        return Assessment(SUPPORTED, key, best)
    except Exception as exc:  # noqa: BLE001 - the ladder's own failure branch
        return Assessment(
            LADDER_FAILED, str(claimed), LADDER[0],
            detail=f"{type(exc).__name__}: {exc}; the claim was NOT judged",
        )
