"""The verdict, in CLAE Part 27's sealed vocabulary.

Part 27 §6 already names the states this needs -- DONE_VERIFIED,
PARTIAL_VERIFIED, EVIDENCE_INCOMPLETE, BLOCKED. Minting new ones would leave
the repo with two vocabularies for one closure decision.

Two rules carry the gate:

  * The blocking condition is an ABSOLUTE count, never a ratio. A ratio is
    satisfied by deleting criteria (feedback_never_gate_on_a_ratio).
  * EVIDENCE_INCOMPLETE is not BLOCKED. "I could not check it" and "I checked
    it and it failed" are different claims, and collapsing them teaches people
    to route around the gate rather than to close it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .join import CriterionResult, Observed, Reach


class Verdict(str, Enum):
    DONE_VERIFIED = "DONE_VERIFIED"
    PARTIAL_VERIFIED = "PARTIAL_VERIFIED"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
    BLOCKED = "BLOCKED"
    INTENT_NOT_CAPTURED = "INTENT_NOT_CAPTURED"
    CRITERIA_NOT_MECHANICAL = "CRITERIA_NOT_MECHANICAL"


# Verdicts that permit a done claim. INTENT_NOT_CAPTURED is here by Owner
# decision (2026-08-14): it is reported and accumulates as debt, and a gate
# that blocks every unspecced task is disabled within a day.
PASSING = frozenset({Verdict.DONE_VERIFIED, Verdict.PARTIAL_VERIFIED,
                     Verdict.INTENT_NOT_CAPTURED})


@dataclass
class IntentVerification:
    verdict: Verdict
    results: list[CriterionResult] = field(default_factory=list)
    spec: str = ""
    reason: str = ""

    @property
    def passed(self) -> bool:
        return self.verdict in PASSING

    @property
    def critical(self) -> list[CriterionResult]:
        return [r for r in self.results if r.criterion.critical]

    @property
    def failed_critical(self) -> list[CriterionResult]:
        return [r for r in self.critical if r.observed is Observed.FAIL]

    @property
    def unobserved_critical(self) -> list[CriterionResult]:
        """Critical criteria the run could not turn into evidence."""
        return [r for r in self.critical if r.observed in (
            Observed.ABSENT, Observed.ERROR, Observed.NOT_RUN)]

    @property
    def unverifiable(self) -> list[CriterionResult]:
        return [r for r in self.results if r.reach is Reach.UNVERIFIABLE]

    @property
    def unjoined(self) -> list[CriterionResult]:
        return [r for r in self.results if r.reach is Reach.UNJOINED]

    def as_dict(self) -> dict:
        return {
            "verdict": self.verdict.value,
            "spec": self.spec,
            "reason": self.reason,
            "criteria_total": len(self.results),
            "criteria_critical": len(self.critical),
            "satisfied": sum(1 for r in self.results if r.satisfied),
            "failed_critical": [r.criterion.id for r in self.failed_critical],
            "unobserved_critical": [r.criterion.id
                                    for r in self.unobserved_critical],
            "unjoined": [r.criterion.id for r in self.unjoined],
            "unverifiable": [r.criterion.id for r in self.unverifiable],
            "results": [r.as_dict() for r in self.results],
        }


def decide(results: list[CriterionResult], spec: str = "",
           reason: str = "", bound: bool = True) -> IntentVerification:
    """Verdict from observed results. Order matters: a real failure outranks
    missing evidence, which outranks an unsatisfied advisory criterion."""
    if not bound:
        return IntentVerification(Verdict.INTENT_NOT_CAPTURED, results, spec,
                                  reason or "no spec declares coverage of "
                                            "this task")
    if not results:
        return IntentVerification(Verdict.CRITERIA_NOT_MECHANICAL, results,
                                  spec, reason or "the bound spec names no "
                                                  "V-gate criterion")
    v = IntentVerification(Verdict.DONE_VERIFIED, results, spec, reason)
    if v.failed_critical:
        v.verdict = Verdict.BLOCKED
        v.reason = (f"{len(v.failed_critical)} critical criterion/criteria "
                    f"observed failing: "
                    f"{', '.join(r.criterion.id for r in v.failed_critical)}")
    elif v.unobserved_critical:
        v.verdict = Verdict.EVIDENCE_INCOMPLETE
        v.reason = (f"{len(v.unobserved_critical)} critical criterion/criteria "
                    f"produced no evidence: "
                    f"{', '.join(r.criterion.id for r in v.unobserved_critical)}")
    elif any(not r.satisfied for r in results):
        unmet = [r.criterion.id for r in results if not r.satisfied]
        v.verdict = Verdict.PARTIAL_VERIFIED
        v.reason = ("every critical criterion is satisfied; advisory "
                    f"criteria unmet: {', '.join(unmet)}")
    else:
        v.reason = (f"all {len(results)} declared criteria observed passing "
                    f"against {spec or 'the bound spec'}")
    return v


def blocking_count(v: IntentVerification) -> int:
    """The absolute the gate exits on. Never a percentage."""
    return len(v.failed_critical) + len(v.unobserved_critical)


__all__ = ["Verdict", "PASSING", "IntentVerification", "decide",
           "blocking_count"]
