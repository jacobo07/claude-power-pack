"""What the source has told us it cannot know -- and when it forgot.

WHY THIS EXISTS
---------------
Measured on 2026-08-26 across eight live EVA answers. SF30-022 says:

    "en Consultoria.io no tenemos acceso a los datos financieros detallados
     de otros clientes"

Two prompts later SF30-024 says:

    "El 100% de los casos que si lo logran corresponden a operadores con
     experiencia"  ... "La proporcion de lanzamientos desde cero que alcanzan
     esa cifra es del 0-1%"

SF30-021 does both inside ONE answer: "No tengo un numero exacto" followed by
"el 100% de los casos que alcanzan 100.000 EUR/$ ... corresponden a nuevas
tiendas de operadores con experiencia".

The same source that disclaims access to cohort data emits cohort statistics.
In multi-source research a second source settles this. In single-source
interrogation there is no second source -- but there is a free signal: the
source's own declared boundary. A quantified claim about a population the
source said it cannot see is unsourced BY ITS OWN ADMISSION, and detecting that
costs nothing.

TWO KINDS, NEVER CONFLATED
--------------------------
ACCESS      -- "I do not have this data". A statement about possession.
               Load-bearing: it governs later claims and routes the question
               to a human expert.
VARIABILITY -- "there is no single number, it depends". A refusal to
               generalise, which is good epistemic manners and says NOTHING
               about capability.

SF30-025's "No hay un numero magico universal, ya que depende mucho del tipo de
producto" is the second kind. Collapsing the two would file an honest hedge as
a capability gap and route a perfectly answerable question to a human.

A POSITIVE CONTROL, NOT A BLACKLIST
-----------------------------------
First cut of `detect_cohort_claims` was (cohort noun + a number) and it fired on
    "el programa Genesis esta disenado para llevar a las marcas desde cero
     ... a 100.000 EUR/$ al ano"
which is a statement about what a PRODUCT is for, not a measurement of anyone.
Widening a blacklist to exclude it would have been endless. A measurement claim
asserts that something WAS OBSERVED about a population, and Spanish marks that
with a small closed set of predicates ("suelen", "se mueven", "corresponden a",
"es del"). Requiring one is a positive control: the detector now needs evidence
that a measurement is being asserted, rather than evidence that it is not.
Same lesson as the empty-page auth check in `session.py` -- absence of a
disqualifying marker is not presence of the thing.

ALL NEEDLES ARE ASCII
---------------------
Every haystack is passed through `fold()` first, so an accented literal in the
tables below could never match anything. They are written unaccented not as a
style choice but because the accented form would be dead code.

SCOPE MATCHING IS COARSE, DELIBERATELY
--------------------------------------
An ACCESS boundary whose scope names a cohort governs every cohort-quantified
claim from that interface. It does NOT attempt topic-level matching: the
declared scope ("datos financieros de otros clientes") and the crossing
("la proporcion de lanzamientos") share almost no vocabulary, so lexical
overlap would miss the very case this module was built for. Faking semantic
precision here would be less honest than admitting the granularity: the
governing boundary is reported by text on every flag, so the operator can see
exactly what reasoning produced the demotion.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import Enum

from .engine3 import has_measurable_datum
from .expectation import fold


class BoundaryKind(str, Enum):
    ACCESS = "ACCESS"            # the source lacks the data
    VARIABILITY = "VARIABILITY"  # the source declines to generalise


# Statements of possession.
_ACCESS_MARKERS = (
    "no tenemos acceso a", "no tengo acceso a", "no disponemos de",
    "no dispongo de", "no tenemos datos", "no tengo datos",
    "no tengo un numero exacto", "no tenemos un numero exacto",
    "no tenemos un registro", "no llevamos un registro",
    "no tengo informacion sobre", "no tenemos informacion sobre",
    "no puedo compartir", "no compartimos", "no tenemos visibilidad",
    "no puedo darte datos", "no tengo constancia",
)

# Refusals to generalise. No possession claim is made.
_VARIABILITY_MARKERS = (
    "no hay un numero magico", "no hay una cifra unica", "no hay un numero unico",
    "no hay una respuesta unica", "no existe una cifra", "no hay un unico",
    "cada caso es unico", "cada negocio es un mundo", "varia enormemente",
    "varian enormemente", "depende mucho de", "no hay una regla fija",
)

# Nouns that make a sentence a claim ABOUT A POPULATION rather than a
# prescription. "aim for 30-50% margin" is advice; "the cases ran at 25-35%" is
# a statistic, and only the second needs evidence the source may not have.
_COHORT_NOUNS = (
    "los casos", "las casos", "de casos", "casos que", "los lanzamientos",
    "lanzamientos que", "de lanzamientos", "las marcas", "marcas que",
    "los operadores", "operadores con", "los clientes", "otros clientes",
    "las tiendas", "tiendas de", "los mejores", "la mayoria", "las empresas",
    "los negocios", "la proporcion de", "el porcentaje de casos",
    "el 100% de", "el 100 % de", "ninguna marca", "ningun caso",
)

# The positive control. A measurement is being ASSERTED about the population,
# not merely mentioned alongside it. Deliberately small and closed: every entry
# is a predicate that states what a group does, was, or amounts to.
_MEASUREMENT_PREDICATES = (
    "suelen", "suele ser", "suele tener", "se mueven", "se situan",
    "corresponden a", "corresponde a", "es del", "son del", "es de un",
    "representan", "representa el", "alcanzan", "alcanzo", "han alcanzado",
    "ha alcanzado", "tenian", "tenia", "oscilan", "rondan", "promedian",
    "la proporcion de", "el porcentaje de", "ninguna", "ningun",
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?:;])\s+|\n+")
#: How much text after a marker is kept as the declared scope. Long enough to
#: carry the noun phrase, short enough that a following sentence does not leak
#: in and widen the boundary beyond what was actually said.
_SCOPE_CHARS = 160


@dataclass(frozen=True)
class BoundaryDeclaration:
    """One thing the source said it cannot do, in its own words."""

    kind: BoundaryKind
    marker: str
    scope_text: str          # the source's own phrasing, never paraphrased
    cohort_scoped: bool      # does the scope name a population?

    @property
    def boundary_id(self) -> str:
        basis = f"{self.kind.value}|{fold(self.scope_text)[:200]}"
        return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:32]


@dataclass(frozen=True)
class CohortClaim:
    """A quantified statement about a population, with the sentence that made it."""

    sentence: str
    cohort_marker: str
    predicate: str


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT.split(text or "") if s.strip()]


def _names_cohort(folded_text: str) -> str | None:
    for noun in _COHORT_NOUNS:
        if noun in folded_text:
            return noun
    return None


def _asserts_measurement(folded_text: str) -> str | None:
    for pred in _MEASUREMENT_PREDICATES:
        if pred in folded_text:
            return pred
    return None


def detect_boundaries(answer_text: str) -> list[BoundaryDeclaration]:
    """Every boundary the answer declares, strongest kind first.

    A sentence that carries both kinds resolves to ACCESS alone: SF30-022 says
    "no tenemos acceso" AND "cada caso es unico" in adjacent breath, and filing
    the second against the same sentence would dilute the only hard capability
    signal in the corpus with a hedge that means something else.
    """
    sentences = _sentences(answer_text)
    found: list[BoundaryDeclaration] = []
    seen: set[str] = set()
    access_sentences: set[int] = set()

    for i, sentence in enumerate(sentences):
        folded = fold(sentence)
        for marker in _ACCESS_MARKERS:
            idx = folded.find(marker)
            if idx < 0:
                continue
            decl = BoundaryDeclaration(
                kind=BoundaryKind.ACCESS,
                marker=marker,
                scope_text=sentence[idx: idx + _SCOPE_CHARS].strip(),
                cohort_scoped=bool(_names_cohort(folded)),
            )
            access_sentences.add(i)
            if decl.boundary_id not in seen:
                seen.add(decl.boundary_id)
                found.append(decl)
            break

    for i, sentence in enumerate(sentences):
        if i in access_sentences:
            continue  # ACCESS already owns this sentence
        folded = fold(sentence)
        for marker in _VARIABILITY_MARKERS:
            idx = folded.find(marker)
            if idx < 0:
                continue
            decl = BoundaryDeclaration(
                kind=BoundaryKind.VARIABILITY,
                marker=marker,
                scope_text=sentence[idx: idx + _SCOPE_CHARS].strip(),
                cohort_scoped=bool(_names_cohort(folded)),
            )
            if decl.boundary_id not in seen:
                seen.add(decl.boundary_id)
                found.append(decl)
            break

    return found


def detect_cohort_claims(answer_text: str) -> list[CohortClaim]:
    """Sentences asserting a measured quantity about a population.

    Three conjuncts, all required:
      1. a cohort noun      -- the claim is about a group, not a prescription
      2. a measurement predicate -- the group is being SAID to be that way
      3. a measurable datum -- delegated to the deep-research engine

    Dropping (2) admits "the programme is designed to take brands to 100.000
    EUR/year", which measures nothing. Dropping (1) admits "target a 30-50%
    margin", which needs no cohort access to say.
    """
    out: list[CohortClaim] = []
    for sentence in _sentences(answer_text):
        folded = fold(sentence)
        noun = _names_cohort(folded)
        if not noun:
            continue
        pred = _asserts_measurement(folded)
        if not pred:
            continue
        if not has_measurable_datum(sentence):
            continue
        out.append(CohortClaim(sentence=sentence, cohort_marker=noun, predicate=pred))
    return out


def governing_boundary(
    declarations: list[BoundaryDeclaration],
) -> BoundaryDeclaration | None:
    """The recorded ACCESS boundary that governs cohort claims, if any.

    Only a cohort-scoped ACCESS declaration governs. A source that cannot see
    its clients' finances has said something about the cohort; a source that
    cannot recall one tool's pricing has not.
    """
    for d in declarations:
        if d.kind is BoundaryKind.ACCESS and d.cohort_scoped:
            return d
    return None


__all__ = [
    "BoundaryKind",
    "BoundaryDeclaration",
    "CohortClaim",
    "detect_boundaries",
    "detect_cohort_claims",
    "governing_boundary",
]
