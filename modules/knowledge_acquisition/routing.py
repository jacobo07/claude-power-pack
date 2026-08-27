"""Which source should answer this question, and what it would cost to ask.

WHY THIS EXISTS
---------------
SPEC-KACQ-005 decided what an answer was worth once it existed. By then the
query is already spent. On a 2,200-prompt corpus against a paid account that is
roughly eleven hours of interrogation, some fraction of which is spent
rediscovering a limit the source already declared in writing.

WHAT THE CORPUS TURNED OUT TO BE
--------------------------------
Measured before this module was designed: the 1,995 pending CWOPS2000 prompts
decompose with ZERO remainder into 399 topics x 5 templates, and the topic sets
of the five templates intersect at 399/399. The corpus is not 1,995 questions.
It is 399 questions asked five ways.

That matters because the five ways are not equivalent. Running the
SPEC-KACQ-005 expectation deriver unmodified over the pending corpus, the
case-data lens needs first-hand access 100% of the time and the other four need
it 0.3% of the time. The routing variable is the LENS, not the topic -- which
is why this module keys off the generator's template and not off subject matter.

WHAT THIS MODULE IS NOT ALLOWED TO DO
-------------------------------------
All 38 assessed answers are SF30 free-form. There is no observed evidence for
ANY of the five lenses that make up 92% of what remains. So the central
contract (SPEC-KACQ-006 C3) is a restraint, not a capability: a lens with no
measured behaviour cannot divert a prompt away from the source. It can rank it.
Diverting on an untested inference would trade eleven hours of possible spend
for an unknown number of discarded good answers, and the false-skip is the
error that leaves no evidence behind.

Fail-open by construction: every path that is not positively licensed returns a
verdict that keeps the prompt in the EVA queue.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

from .boundary import BoundaryDeclaration, governing_boundary
from .expectation import Expectation, derive_expectation, fold

#: Bump when routing changes in a way that alters a stored verdict.
ROUTER_VERSION = "kacq-route/1.0.0"

#: How many assessed answers a lens needs before its verdict may divert a
#: prompt away from the source. Three is the smallest number that can
#: distinguish a pattern from a coincidence, and the probe that feeds it costs
#: 15 prompts. Raising it costs live queries; lowering it lets one atypical
#: answer redirect 399 prompts.
MIN_LENS_OBSERVATIONS = 3


class Lens(str, Enum):
    """The template a generated prompt came from.

    FREEFORM is a real lens, not a parse failure: the 167 pending SF30 prompts
    were hand-written and carry no template at all.
    """

    THRESHOLD = "THRESHOLD"                  # what signals decide this
    INTERNAL_PATTERNS = "INTERNAL_PATTERNS"  # what your own data shows
    REAL_CASES = "REAL_CASES"                # what happened in real cases
    EXPERIMENT = "EXPERIMENT"                # how would you test this
    PITFALLS = "PITFALLS"                    # how does the usual advice fail
    FREEFORM = "FREEFORM"


class RouteClass(str, Enum):
    """Where the question belongs.

    Ordinal classes, not scores. A decimal here would be invented precision:
    nothing in the evidence distinguishes 0.71 from 0.68, and a number invites
    a threshold nobody measured.
    """

    EVA_HIGH_VALUE = "EVA_HIGH_VALUE"        # measured strong for this lens
    EVA_VALID = "EVA_VALID"                  # ask it; no evidence against
    MULTI_SOURCE = "MULTI_SOURCE"            # source answers part, not all
    INTERNAL_EVIDENCE = "INTERNAL_EVIDENCE"  # a dataset answers this, not talk
    HUMAN_EXPERT = "HUMAN_EXPERT"            # needs tacit judgment
    UNCERTAIN = "UNCERTAIN"                  # not licensed either way

    @property
    def diverts(self) -> bool:
        """Does this verdict move work away from the source?"""
        return self in (
            RouteClass.MULTI_SOURCE,
            RouteClass.INTERNAL_EVIDENCE,
            RouteClass.HUMAN_EXPERT,
        )


# The generator's five templates, as folded ASCII needles.
#
# fold() strips diacritics, so an accented literal here would be a branch
# nothing can reach -- the same dead-code trap SPEC-KACQ-005 hit with "se
# situan". The inverted question mark is NOT a combining mark and survives
# folding, so it is matched as a wildcard rather than written literally, which
# keeps every needle in this file ASCII.
_LENS_PATTERNS: tuple[tuple[Lens, re.Pattern[str]], ...] = (
    (Lens.REAL_CASES, re.compile(
        r"basandote en casos reales o patrones que conozca consultoria\.io, "
        r".{0,3}como cambia (.+?) segun categoria, ticket")),
    (Lens.INTERNAL_PATTERNS, re.compile(
        r"sus patrones internos reales, .{0,3}como evaluarias (.+?) "
        r"para una marca ecommerce nueva")),
    (Lens.THRESHOLD, re.compile(
        r"senales, metricas, rangos, thresholds y evidencia usarias para "
        r"decidir si (.+?) es favorable, neutral")),
    (Lens.EXPERIMENT, re.compile(
        r"experimento minimo, barato y rapido disenarias para validar (.+?) "
        r"en una marca nueva, que medirias")),
    (Lens.PITFALLS, re.compile(
        r"errores, falsos positivos, sesgos y excepciones mas frecuentes al "
        r"analizar (.+?), especialmente en tiendas")),
)


def derive_lens(prompt_text: str) -> tuple[Lens, str]:
    """Recover which template produced this prompt, and its topic.

    The topic is the template's varying span -- exact string identity after
    folding, never similarity. Two prompts share a topic or they do not; there
    is no threshold to tune and therefore no false merge to debug.
    """
    text = fold(prompt_text)
    for lens, pattern in _LENS_PATTERNS:
        match = pattern.search(text)
        if match:
            return lens, match.group(1).strip()
    return Lens.FREEFORM, ""


@dataclass(frozen=True)
class LensEvidence:
    """What has actually been observed for one lens.

    `answers` counts assessed responses whose prompt carried this lens.
    `extractable` counts those still worth keeping. `diverted` counts those the
    SPEC-KACQ-005 classifier marked route_to_expert.

    All three come from stored assessments. Nothing here is estimated: a lens
    with no rows reports zero and is therefore unable to license a divert.
    """

    lens: Lens
    answers: int = 0
    extractable: int = 0
    diverted: int = 0

    @property
    def measured(self) -> bool:
        return self.answers >= MIN_LENS_OBSERVATIONS

    @property
    def mostly_diverted(self) -> bool:
        return self.measured and self.diverted * 2 > self.answers

    @property
    def mostly_extractable(self) -> bool:
        return self.measured and self.extractable * 2 > self.answers


@dataclass(frozen=True)
class RouteVerdict:
    """Where one question belongs, and why.

    `reason` is mandatory prose naming the evidence. A verdict that diverts
    without naming the boundary it collided with is not auditable, and an
    unauditable divert is indistinguishable from a guess (SPEC-KACQ-006 A6).
    """

    prompt_id: str
    lens: Lens
    topic: str
    route: RouteClass
    evidence_kind: str
    reason: str
    boundary_id: str = ""
    evidence_backed: bool = False
    router_version: str = ROUTER_VERSION
    markers: tuple[str, ...] = field(default=())


def route(
    prompt_id: str,
    prompt_text: str,
    *,
    family: str = "",
    boundaries: list[BoundaryDeclaration] | None = None,
    evidence: dict[Lens, LensEvidence] | None = None,
) -> RouteVerdict:
    """Decide where this question belongs, given what the source has declared.

    Reads only the prompt text, the boundary ledger and measured lens evidence.
    No network, no answer, no DB. That purity is what makes a verdict
    reproducible from raw alone and safe to recompute at any time.
    """
    lens, topic = derive_lens(prompt_text)
    expectation: Expectation = derive_expectation(prompt_text, family)
    seen = (evidence or {}).get(lens, LensEvidence(lens))
    kind = expectation.kind.value

    def verdict(route_class: RouteClass, reason: str, *,
                boundary: BoundaryDeclaration | None = None) -> RouteVerdict:
        return RouteVerdict(
            prompt_id=prompt_id,
            lens=lens,
            topic=topic,
            route=route_class,
            evidence_kind=kind,
            reason=reason,
            boundary_id=boundary.boundary_id if boundary else "",
            evidence_backed=seen.measured,
            markers=expectation.markers,
        )

    # -- the question does not need anything the source cannot see -----------
    if not expectation.needs_first_hand_access:
        if seen.mostly_extractable and not seen.mostly_diverted:
            return verdict(
                RouteClass.EVA_HIGH_VALUE,
                f"{kind} question; this lens measured {seen.extractable}/"
                f"{seen.answers} extractable with no declared limit against it",
            )
        return verdict(
            RouteClass.EVA_VALID,
            f"{kind} question needing no first-hand access; "
            f"nothing the source has declared blocks it",
        )

    # -- it does. Has the source actually said it cannot? --------------------
    # Only a cohort-scoped ACCESS declaration counts. A VARIABILITY hedge ("no
    # hay un numero magico") is a fact about the question, not about the
    # source, and must never divert anything (SPEC-KACQ-006 C4/A5).
    governing = governing_boundary(list(boundaries or []))
    if governing is None:
        return verdict(
            RouteClass.UNCERTAIN,
            f"{kind} question wants first-hand evidence, but the source has "
            f"declared no access limit covering it -- asking is the only way "
            f"to find out",
        )

    # -- it has. Do we have the right to act on that for THIS lens? ----------
    # SPEC-KACQ-006 C3. The boundary is real, but a boundary declared while
    # answering a hand-written SF30 question is not yet evidence about how this
    # generated lens behaves. Rank it, do not divert it.
    if not seen.measured:
        return verdict(
            RouteClass.EVA_VALID,
            f"{kind} question collides with a declared access limit, but this "
            f"lens has only {seen.answers} observed answers "
            f"(needs {MIN_LENS_OBSERVATIONS}) -- not enough to divert on",
            boundary=governing,
        )

    # -- measured, and the source still answers usefully ---------------------
    # The case-data lens asks two things at once: real cases AND a transferable
    # rule. If the observed answers stay extractable the source is delivering
    # the second half, so diverting outright would discard it.
    if seen.mostly_extractable:
        return verdict(
            RouteClass.MULTI_SOURCE,
            f"{kind} question collides with a declared access limit, yet "
            f"{seen.extractable}/{seen.answers} observed answers on this lens "
            f"stayed extractable -- the source supplies the reasoning, another "
            f"source must supply the evidence",
            boundary=governing,
        )

    # -- measured, and the source cannot carry it ----------------------------
    # A quantified cohort ask is answered by a dataset; an unquantified one
    # needs somebody's judgment. That is the ASK / REQUEST_EVIDENCE split.
    if expectation.wants_quantity:
        return verdict(
            RouteClass.INTERNAL_EVIDENCE,
            f"{kind} question asks for a quantity about a population the "
            f"source has declared it cannot see; a dataset answers this, "
            f"another conversation does not",
            boundary=governing,
        )
    return verdict(
        RouteClass.HUMAN_EXPERT,
        f"{kind} question needs first-hand judgment about cases the source has "
        f"declared it cannot see",
        boundary=governing,
    )


__all__ = [
    "ROUTER_VERSION",
    "MIN_LENS_OBSERVATIONS",
    "Lens",
    "RouteClass",
    "LensEvidence",
    "RouteVerdict",
    "derive_lens",
    "route",
]
