"""What kind of evidence would actually answer this question.

WHY THIS EXISTS
---------------
Grading every answer on one scale is the mistake this module prevents. A
methodology answer is excellent for "how should I build X" and a failure for
"what did the cases actually spend" -- the text can be identical and the verdict
must not be.

The expectation is DERIVED from the prompt, never hand-authored. 2,200 prompts
cannot be tagged by hand, and a tagging pass would rot the moment the corpus is
re-exported.

ACCENT FOLDING
--------------
Needles here are ASCII; the haystack is folded before matching. EVA's output is
Spanish and its accents are not reliable (the same word arrives as "validacion"
and "validación" across answers), so matching on accented literals would drop
real hits for a typographic reason. Folding also keeps this file ASCII-clean,
which the vault's write gates care about.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum

#: Bump when derivation changes in a way that alters a stored assessment.
CLASSIFIER_VERSION = "kacq-assess/1.3.0"


def fold(text: str) -> str:
    """Lowercase, strip diacritics, collapse whitespace. Matching normal form."""
    decomposed = unicodedata.normalize("NFD", (text or "").lower())
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", stripped).strip()


class EvidenceKind(str, Enum):
    """What the question is asking the source to produce."""

    CASE_DATA = "CASE_DATA"        # what actually happened in real cases
    BENCHMARK = "BENCHMARK"        # a number, threshold, range or rate
    METHODOLOGY = "METHODOLOGY"    # how to build or run something
    DECISION = "DECISION"          # which option to choose
    COMPARISON = "COMPARISON"      # what separates A from B
    PROCESS = "PROCESS"            # sequencing: what before what
    CAUSAL = "CAUSAL"              # why, or how an outcome changes
    OPEN = "OPEN"                  # nothing identifiable


# A question that names real observed instances. These are the ones a source
# without case access structurally cannot satisfy, so they are what drives
# expert routing -- getting this set wrong is expensive in both directions.
_COHORT_MARKERS = (
    "los casos", "en casos", "casos de", "casos reales", "algun caso",
    "mejores casos", "los mejores", "casos que", "de los casos",
    "que conoces", "que has visto", "has visto", "tenian los", "tenia el",
    "estaba disponible", "ejemplos reales", "otros clientes", "vuestros clientes",
    "de tus clientes", "cual ha sido", "cuales han sido", "que marcas",
    "que empresas", "quien ha", "alguna marca",
    # Observation verbs: the question asks what was SEEN, which only first-hand
    # access can supply. SF30-014 ("que MER ... se observaron en los mejores
    # casos") resolved to OPEN without these.
    "se observaron", "se observo", "que observas", "observas entre",
    "habeis visto", "habeis observado",
)

# Asking for a magnitude. Distinct from cohort: "what ROAS should I target" wants
# a number without claiming anyone measured it.
_QUANTITY_MARKERS = (
    "cuanto", "cuanta", "cuantos", "cuantas", "que porcentaje", "que % ",
    "que proporcion", "que parte", "que ratio", "que relacion", "cual es el numero",
    "que cifra", "que rango", "que umbral", "que margen", "how much", "how many",
    "what percentage", "que probabilidad", "probabilidad de",
)

# Ordered by strength of proof, not convenience: the first rule that fires wins,
# and the strongest signal must be tested first. CASE_DATA outranks BENCHMARK
# because "how much did the cases spend" is a case question that happens to want
# a number, not a benchmark question that happens to mention cases.
_KIND_MARKERS: tuple[tuple[EvidenceKind, tuple[str, ...]], ...] = (
    (EvidenceKind.METHODOLOGY, (
        "como deberia", "como deberias", "como construir", "como construiria",
        "como disenar", "como disenaria", "como implementar", "como montar",
        "como estructurar", "que pasos", "que proceso seguir", "how should",
        "how do i build", "como se construye", "como hacer",
    )),
    (EvidenceKind.COMPARISON, (
        "distinguiria", "distingue", "diferencia entre", "diferencian",
        "que separa", "frente a", "versus", " vs ", "mejor que",
        "en que se diferencia",
    )),
    (EvidenceKind.CAUSAL, (
        "como cambia", "que efecto", "por que", "que causa", "que provoca",
        "que impacto", "como afecta", "why does", "what happens when",
    )),
    (EvidenceKind.PROCESS, (
        "antes de", "despues de", "en que orden", "que va primero",
        "durante el propio", "que parte del", "en que momento", "cuando deberia",
    )),
    (EvidenceKind.DECISION, (
        "que metrica utilizarias", "utilizarias", "elegirias", "recomendarias",
        "que deberia priorizar", "cual escogerias", "que opcion",
        "should i use", "which should",
    )),
)


# The Spanish 2nd-person conditional ("usarias", "exigirias", "normalizarias")
# asks the source for its own judgment. The first cut of this module enumerated
# individual verbs and missed five of thirty prompts on morphology alone --
# "utilizarias" was listed, "usarias" was not. A verb list is the wrong shape
# for an inflected language; the ending IS the signal.
#
# Person matters. The 2nd-person ending means "what would YOU do" and marks an
# advisory question; the 3rd person ("que relacion distinguiria X de Y") does
# not, which is why this anchors on the final s.
#
# Unaccented by necessity, not style: the haystack is folded before matching,
# so an accented character class here would be a branch nothing can reach.
_CONDITIONAL_RX = re.compile(r"\b\w+[aei]rias\b")

# Typicality. "que margen SUELE permitir" asks for the usual value -- a
# benchmark request carrying no number word at all.
_TYPICALITY_MARKERS = ("suele", "suelen", "normalmente", "habitualmente",
                       "por lo general", "de media")

# Which advisory kind a conditional resolves to, decided by the interrogative
# it travels with: "como normalizarias" is a method, "que criterios usarias" is
# a choice.
_HOW_MARKERS = ("como ", "de que forma", "de que manera")


@dataclass(frozen=True)
class Expectation:
    """What would satisfy this question, and what it would take to satisfy it."""

    kind: EvidenceKind
    wants_quantity: bool
    wants_cohort_evidence: bool
    markers: tuple[str, ...] = field(default=())

    @property
    def needs_first_hand_access(self) -> bool:
        """True when only real observed data can answer this.

        The routing predicate: a source that has declared it cannot see the
        cohort will never satisfy one of these, no matter how well it writes.
        """
        return self.wants_cohort_evidence


def derive_expectation(prompt_text: str, family: str = "") -> Expectation:
    """Read the question; decide what kind of answer would count.

    `family` participates only as weak corroboration -- a section header names a
    topic, not an evidence type, and two prompts under one header routinely want
    different things (SF30-021 wants case figures, SF30-023 wants sequencing,
    and both sit under "Starting Capital").
    """
    text = fold(prompt_text)
    hits: list[str] = []

    cohort = [m for m in _COHORT_MARKERS if m in text]
    quantity = [m for m in _QUANTITY_MARKERS if m in text]
    quantity += [m for m in _TYPICALITY_MARKERS if m in text]
    hits.extend(cohort)
    hits.extend(quantity)

    # Cohort evidence outranks every other shape: it is the only expectation
    # whose satisfaction depends on what the source can SEE rather than on how
    # well it reasons.
    if cohort:
        return Expectation(
            kind=EvidenceKind.CASE_DATA,
            wants_quantity=bool(quantity),
            wants_cohort_evidence=True,
            markers=tuple(hits),
        )

    for kind, markers in _KIND_MARKERS:
        found = [m for m in markers if m in text]
        if found:
            return Expectation(
                kind=kind,
                wants_quantity=bool(quantity),
                wants_cohort_evidence=False,
                markers=tuple(found + quantity),
            )

    # Morphology before vocabulary: an inflected verb the tables never listed
    # still marks an advisory question, and which KIND it is depends on the
    # interrogative it travels with.
    conditional = _CONDITIONAL_RX.search(text)
    if conditional:
        kind = (EvidenceKind.METHODOLOGY
                if any(m in text for m in _HOW_MARKERS)
                else EvidenceKind.DECISION)
        return Expectation(
            kind=kind,
            wants_quantity=bool(quantity),
            wants_cohort_evidence=False,
            markers=tuple([conditional.group(0)] + quantity),
        )

    if quantity:
        return Expectation(
            kind=EvidenceKind.BENCHMARK,
            wants_quantity=True,
            wants_cohort_evidence=False,
            markers=tuple(quantity),
        )

    return Expectation(
        kind=EvidenceKind.OPEN,
        wants_quantity=False,
        wants_cohort_evidence=False,
        markers=(),
    )


__all__ = [
    "CLASSIFIER_VERSION",
    "EvidenceKind",
    "Expectation",
    "derive_expectation",
    "fold",
]
