#!/usr/bin/env python3
"""The single vocabulary for "this was not a model failure".

Four outcomes, one precedence, one predicate. The transport, the classifier, the
admission gate and every verifier ask the SAME question of the SAME type. The
phase-4 audit's closing warning is the reason this file exists at all: gap 4
(a dead endpoint entering the corpus as a model failure) and gap 18 (a verifier
that can only ever refuse) are the same defect, and fixing them separately would
produce two vocabularies of INCONCLUSIVE inside a module whose entire thesis is
that failure classes are ONE.

Why each outcome exists -- measured on 2026-09-24, not imagined:

  OK              The subject was asked and answered completely. The ONLY
                  outcome to which a failure class may ever be attached.

  UNAVAILABLE     The subject was never asked. `keos-llm.service` is a single
                  resident process on a host carrying 15 production services,
                  ~3.5 GB of free VRAM of 20 GB, and a disk at 93% that drains
                  on its own. ConnectionRefused, a GPU OOM, a `systemctl
                  restart` and a dead tunnel all produce "no useful answer" --
                  and recorded as a model failure they make the baseline
                  measure the health of the host instead of the quality of the
                  model.

  TRUNCATED       Asked, answered, and OUR window cut it off. llama-server
                  returns finish_reason="length" at the 32768 ctx it was
                  started with; the prompts already measured in this estate run
                  2254 to 6467 tokens and the doctrine arm nearly tripled the
                  control. A half-written test is syntactically invalid and
                  reads as incompetence when it is a context size we chose.

  HARNESS_FAILED  Our own instrument broke. It OUTRANKS every subject failure
                  in the same run, because a run that could not execute proves
                  nothing about what it skipped. The specific trap this module
                  must survive: if the package is not importable, EVERY
                  generated candidate fails to import and `verify_executable`
                  reports the model failing when it is measuring its own
                  environment.

The invariant every caller inherits: only OK may be classified, admitted, or
counted in a baseline. Everything else is archived with its reason and never
receives a failure class.
"""
from __future__ import annotations

from dataclasses import dataclass, field

OK = "OK"
UNAVAILABLE = "UNAVAILABLE"
TRUNCATED = "TRUNCATED"
HARNESS_FAILED = "HARNESS_FAILED"

ALL = (OK, UNAVAILABLE, TRUNCATED, HARNESS_FAILED)

# Worst first. A run is exactly as trustworthy as its least trustworthy member,
# and an instrument failure outranks anything the run thought it observed.
_PRECEDENCE = (HARNESS_FAILED, UNAVAILABLE, TRUNCATED, OK)

# llama.cpp / OpenAI-compatible finish_reason -> outcome.
#
# Written as a POSITIVE test on the answers we have actually observed, never as
# "anything that is not X is fine". A negative test silently absorbs the next
# finish_reason the server learns to emit, and absorbs it toward the permissive
# answer, which is the one direction this must not fail in.
_FINISH_REASON = {
    "stop": OK,
    "tool_calls": OK,
    "length": TRUNCATED,
}


class OutcomeError(ValueError):
    """An outcome that is not one of ALL, or a non-OK outcome with no reason.

    Raised rather than defaulted. A value we do not recognise is not evidence
    that everything is fine; defaulting it to OK is how an unknown server state
    becomes a sample in a training corpus.
    """


def classifiable(outcome: str) -> bool:
    """May a failure class be attached to this attempt?

    One predicate, one place. Every caller asks this instead of writing its own
    comparison, so a fifth outcome added later cannot be silently treated as OK
    by whichever module forgot to be updated.
    """
    if outcome not in ALL:
        raise OutcomeError(f"unknown outcome {outcome!r}; expected one of {ALL}")
    return outcome == OK


def worst(outcomes) -> str:
    """The governing outcome of a set of observations.

    An EMPTY set is HARNESS_FAILED, never OK. Nothing was observed, and reading
    "we observed nothing" as "nothing was wrong" is the exact shape of a sweep
    that silently matched no files and reported a clean bill.
    """
    seen = list(outcomes)
    # Validation BEFORE precedence, and this ordering is the whole point. With
    # precedence first, worst(["OK", "BOGUS"]) returns OK and never looks at
    # BOGUS -- an unrecognised outcome absorbed toward the permissive answer by
    # a function whose job is to be pessimistic. Caught here before shipping;
    # kept as V-KEOSQ-WORST-UNKNOWN-WITH-OK.
    unknown = [o for o in seen if o not in ALL]
    if unknown:
        raise OutcomeError(f"unknown outcome(s) {unknown!r}; expected members of {ALL}")
    if not seen:
        return HARNESS_FAILED
    for candidate in _PRECEDENCE:
        if candidate in seen:
            return candidate
    raise OutcomeError(
        "unreachable unless ALL and _PRECEDENCE have drifted apart; "
        "V-KEOSQ-PRECEDENCE-COVERS-ALL exists to make that impossible")


def from_finish_reason(finish_reason) -> tuple:
    """Map a server finish_reason to (outcome, reason).

    An absent or unrecognised finish_reason is HARNESS_FAILED, not OK: we do not
    know what the server did, and the honest reading of "could not tell" is
    refusal. The raw value travels in the reason so the first occurrence
    diagnoses itself instead of being silently absorbed.
    """
    if finish_reason in _FINISH_REASON:
        outcome = _FINISH_REASON[finish_reason]
        if outcome == TRUNCATED:
            return TRUNCATED, "server returned finish_reason='length': our ctx window cut the answer"
        return OK, f"server returned finish_reason={finish_reason!r}"
    return (HARNESS_FAILED,
            f"unrecognised finish_reason {finish_reason!r}; refusing to guess what the server did")


@dataclass(frozen=True)
class Attempt:
    """One observation, carrying WHY it is not OK when it is not OK.

    A non-OK outcome with no reason is refused at construction. "We could not
    tell" without saying what could not be told sends a reader to check
    everything, which is indistinguishable from telling them nothing.
    """

    outcome: str
    reason: str
    evidence: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.outcome not in ALL:
            raise OutcomeError(f"unknown outcome {self.outcome!r}; expected one of {ALL}")
        if self.outcome != OK and not (self.reason or "").strip():
            raise OutcomeError(f"{self.outcome} requires a reason; an unexplained refusal is not evidence")

    @property
    def classifiable(self) -> bool:
        return classifiable(self.outcome)

    def to_dict(self) -> dict:
        return {"outcome": self.outcome, "reason": self.reason, "evidence": dict(self.evidence)}
