"""Judge one captured answer: how much to bet on it, and what to do next.

TWO OUTPUTS, DELIBERATELY SEPARATE
----------------------------------
`epistemic`   -- how much a reader should bet. Produced by the deep-research
                 engine's `cap_epistemic`, called unmodified.
`disposition` -- what the pipeline should DO. Produced here.

They are separate because they vary independently. Almost every answer from a
single unverifiable vendor source lands at DERIVED -- that is honest and it is
also uninformative on its own. The variance an operator can act on lives in the
disposition: the same DERIVED answer may be extractable, may deserve a
follow-up, or may have told us the source cannot help and the question belongs
to a human.

WHY COVERAGE IS SUPPLIED RATHER THAN FORKED
-------------------------------------------
`cap_epistemic` keys off a landscape of many sources per claim. This corpus has
one source, always the same one, and it sells the programme it cites. Passing
its real landscape verdict (VENDOR_ONLY) would cap all 2,200 answers at
REJECTED -- defensible, useless, and it would erase the distinction between an
honest methodology answer and an invented statistic.

So the engine is called with the coverage that honestly describes the evidence
situation for each claim:

  UNCLASSIFIED  baseline. Provenance cannot be established from one
                unverifiable source, so nothing above an inference has been
                earned -- but the work is kept. Caps at DERIVED.
  VENDOR_ONLY   reserved for a claim that crosses a boundary the source itself
                declared. That claim is not weakly sourced, it is unsourced by
                the source's own admission. Caps at REJECTED.

VERIFIED is unreachable by construction: supporting_sources is always 1.

A DECLARED GAP IS NOT A FAILED ANSWER
-------------------------------------
SOURCE_LIMITED is recorded only when the source SAID it lacks the data. A
source that merely declines to generalise ("no hay un numero magico universal,
depende del producto") has answered honestly and the question is still worth
pursuing -- that is DEEPEN, not a capability gap. Filing the second as the
first would route perfectly answerable questions to a human expert and burn the
scarcest resource in the system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from . import engine3
from .boundary import (
    BoundaryDeclaration,
    BoundaryKind,
    CohortClaim,
    detect_boundaries,
    detect_cohort_claims,
    governing_boundary,
)
from .expectation import (
    CLASSIFIER_VERSION,
    EvidenceKind,
    Expectation,
    derive_expectation,
    fold,
)

#: Below this an answer carries no extractable content whatever its shape.
MIN_SUBSTANTIVE_CHARS = 400


class Disposition(str, Enum):
    """What the pipeline should do with this answer."""

    EXTRACTABLE = "EXTRACTABLE"                # proceed to claim extraction
    DEEPEN = "DEEPEN"                          # worth one targeted follow-up
    SOURCE_LIMITED = "SOURCE_LIMITED"          # declared gap; route elsewhere
    UNVERIFIABLE_CLAIM = "UNVERIFIABLE_CLAIM"  # crosses a declared boundary
    LOW_VALUE = "LOW_VALUE"                    # keep raw, skip downstream
    HUMAN = "HUMAN"                            # genuine escalation
    UNRATED = engine3.UNRATED                  # the judge itself failed


class AnswerShape(str, Enum):
    """What the answer actually delivers, independent of what was asked."""

    REFUSAL_WITH_GUIDANCE = "REFUSAL_WITH_GUIDANCE"
    COHORT_STATISTICS = "COHORT_STATISTICS"
    BENCHMARK = "BENCHMARK"
    METHODOLOGY = "METHODOLOGY"
    GENERIC = "GENERIC"


# Personalization. Detecting the SHAPE of context conditioning, not one
# vendor's vocabulary -- a hardcoded "Fitthouse" would make this module useless
# for the next source.
_CARRYOVER_MARKERS = (
    "como te comente", "como comentamos", "hemos discutido", "hemos hablado",
    "como vimos", "que te propuse", "te propuse", "como te dije",
    "en nuestra conversacion", "como hablamos", "te recomende",
)
_PROGRAM_MARKERS = (
    "tu programa", "de tu programa", "en tu programa", "tu plan",
    "de la semana", "la leccion", "tus recursos", "tu curso",
)
_DIRECT_ADDRESS = ("jacobo",)


@dataclass(frozen=True)
class Flag:
    code: str
    evidence: str


@dataclass(frozen=True)
class Assessment:
    """The full derived judgment. Versioned; raw is never touched."""

    prompt_id: str
    response_id: str
    classifier_version: str
    expected: EvidenceKind
    wants_cohort_evidence: bool
    shape: AnswerShape
    coverage: str
    epistemic: str
    epistemic_reason: str
    disposition: Disposition
    context_bound: bool
    context_markers: tuple[str, ...] = field(default=())
    boundaries: tuple[BoundaryDeclaration, ...] = field(default=())
    cohort_claims: tuple[CohortClaim, ...] = field(default=())
    flags: tuple[Flag, ...] = field(default=())
    followups: tuple[str, ...] = field(default=())


def _detect_context(answer: str) -> tuple[bool, tuple[str, ...]]:
    """Personalization markers, kept as provenance and never scored away.

    Carryover is the one that matters most: a reference to advice never given
    in this run is proof the source holds account-level memory the client
    cannot clear, which means ISOLATED mode cannot deliver isolation.
    """
    folded = fold(answer)
    found = [m for group in (_CARRYOVER_MARKERS, _PROGRAM_MARKERS, _DIRECT_ADDRESS)
             for m in group if m in folded]
    return bool(found), tuple(found)


def _has_carryover(markers: tuple[str, ...]) -> bool:
    return any(m in _CARRYOVER_MARKERS for m in markers)


def _derive_shape(
    answer: str,
    boundaries: list[BoundaryDeclaration],
    claims: list[CohortClaim],
) -> AnswerShape:
    has_access = any(b.kind is BoundaryKind.ACCESS for b in boundaries)
    if claims:
        return AnswerShape.COHORT_STATISTICS
    if has_access:
        return AnswerShape.REFUSAL_WITH_GUIDANCE
    if engine3.has_measurable_datum(answer):
        return AnswerShape.BENCHMARK
    if len(answer) >= MIN_SUBSTANTIVE_CHARS:
        return AnswerShape.METHODOLOGY
    return AnswerShape.GENERIC


def _decide(
    expectation: Expectation,
    boundaries: list[BoundaryDeclaration],
    claims: list[CohortClaim],
    governing: BoundaryDeclaration | None,
    answer: str,
) -> tuple[Disposition, str]:
    """Resolution order is by strength of evidence, not convenience."""
    if claims and governing is not None:
        return Disposition.UNVERIFIABLE_CLAIM, (
            f"{len(claims)} quantified claim(s) about a population the source "
            f"declared it cannot see"
        )
    if governing is not None and expectation.needs_first_hand_access:
        return Disposition.SOURCE_LIMITED, (
            "the question needs first-hand case evidence and the source "
            "declared it does not have it"
        )
    if claims:
        return Disposition.DEEPEN, (
            f"{len(claims)} quantified claim(s) about a population, from a "
            f"single source with no corroboration -- worth asking what they "
            f"rest on"
        )
    if len(answer) < MIN_SUBSTANTIVE_CHARS:
        return Disposition.LOW_VALUE, (
            f"{len(answer)} chars -- below the substantive floor "
            f"({MIN_SUBSTANTIVE_CHARS})"
        )
    if expectation.needs_first_hand_access:
        return Disposition.DEEPEN, (
            "case evidence was asked for and not delivered, but the source "
            "never said it lacks it -- a narrower question may still land"
        )
    return Disposition.EXTRACTABLE, "answer matches what the question asked for"


def _build_followups(
    disposition: Disposition, claims: list[CohortClaim], expectation: Expectation
) -> tuple[str, ...]:
    """Candidates only. Nothing here is ever executed automatically."""
    if disposition is Disposition.UNVERIFIABLE_CLAIM:
        return tuple(
            f"Sobre la afirmacion \"{c.sentence[:120].strip()}\": "
            f"en que datos concretos se basa esa cifra, y de cuantos casos?"
            for c in claims[:2]
        )
    if disposition is Disposition.DEEPEN and claims:
        return (
            f"De cuantos casos procede la cifra citada, y son casos medidos "
            f"o una estimacion?",
        )
    if disposition is Disposition.DEEPEN and expectation.needs_first_hand_access:
        return (
            "Sin pedir datos de otros clientes: que rango has visto tu mismo, "
            "y bajo que condiciones?",
        )
    return ()


def assess(
    *,
    prompt_id: str,
    response_id: str,
    prompt_text: str,
    answer_text: str,
    family: str = "",
    known_boundaries: list[BoundaryDeclaration] | None = None,
) -> Assessment:
    """Classify one answer against the question it was meant to answer.

    `known_boundaries` is the interface's accumulated ledger. It is what makes
    the system learn: a cohort statistic seen before any boundary was declared
    is only DEEPEN, and the same statistic re-assessed after the source admits
    it cannot see the cohort becomes UNVERIFIABLE_CLAIM. Re-assessment is an
    explicit operation, never a silent rewrite.
    """
    expectation = derive_expectation(prompt_text, family)
    declared = detect_boundaries(answer_text)
    claims = detect_cohort_claims(answer_text)

    ledger = list(known_boundaries or []) + declared
    governing = governing_boundary(ledger)

    context_bound, markers = _detect_context(answer_text)
    shape = _derive_shape(answer_text, declared, claims)
    disposition, why = _decide(expectation, declared, claims, governing, answer_text)

    coverage = (
        engine3.COVERAGE_VENDOR_ONLY
        if disposition is Disposition.UNVERIFIABLE_CLAIM
        else engine3.COVERAGE_UNCLASSIFIED
    )
    claimed = (
        engine3.EPI_OBSERVED
        if engine3.has_measurable_datum(answer_text)
        else engine3.EPI_DERIVED
    )
    epistemic, cap_reason = engine3.cap_epistemic(
        claimed, answer_text, why, 1, coverage
    )

    flags: list[Flag] = [Flag("DISPOSITION", why)]
    if governing is not None:
        flags.append(Flag("GOVERNING_BOUNDARY", governing.scope_text[:200]))
    for c in claims:
        flags.append(Flag("COHORT_CLAIM", c.sentence[:200]))
    if _has_carryover(markers):
        flags.append(Flag(
            "CONTEXT_CARRYOVER",
            "references an exchange outside this run -- the source holds "
            "account-level memory the client cannot clear",
        ))
    if context_bound:
        flags.append(Flag(
            "CONTEXT_BOUND",
            "conditioned on the operator's own business; not promotable as "
            "universal doctrine",
        ))

    return Assessment(
        prompt_id=prompt_id,
        response_id=response_id,
        classifier_version=CLASSIFIER_VERSION,
        expected=expectation.kind,
        wants_cohort_evidence=expectation.wants_cohort_evidence,
        shape=shape,
        coverage=coverage,
        epistemic=epistemic,
        epistemic_reason=cap_reason,
        disposition=disposition,
        context_bound=context_bound,
        context_markers=markers,
        boundaries=tuple(declared),
        cohort_claims=tuple(claims),
        flags=tuple(flags),
        followups=_build_followups(disposition, claims, expectation),
    )


__all__ = [
    "Assessment",
    "AnswerShape",
    "Disposition",
    "Flag",
    "assess",
    "MIN_SUBSTANTIVE_CHARS",
]
