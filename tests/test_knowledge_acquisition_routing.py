"""SPEC-KACQ-006 acceptance: lens detection, topic identity, and the restraint.

Every prompt fixture below is VERBATIM from the live registry, not invented.
The five template fixtures are real pending rows; the two boundary fixtures are
real declarations EVA made on 2026-08-26 and that the ledger already holds.

The suite's centre of gravity is not "does it route" but "does it refuse to
route when it has not measured anything" -- that restraint is the only thing
standing between a plausible inference and 399 discarded answers.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PP = Path(__file__).resolve().parents[1]
if str(_PP) not in sys.path:
    sys.path.insert(0, str(_PP))

from modules.knowledge_acquisition.boundary import (  # noqa: E402
    BoundaryDeclaration, BoundaryKind,
)
from modules.knowledge_acquisition.routing import (  # noqa: E402
    MIN_LENS_OBSERVATIONS, Lens, LensEvidence, RouteClass, derive_lens, route,
)

# --- verbatim pending prompts, one per lens ---------------------------------

REAL_CASES = (
    "Basándote en casos reales o patrones que conozca Consultoria.io, ¿cómo "
    "cambia identificar failure modes del producto que más pueden destruir "
    "reviews y repetición según categoría, ticket, margen, canal, geografía y "
    "madurez de la marca? Extrae al final una regla transferible que un "
    "sistema autónomo como CommonWealth Ops pueda conservar, con sus "
    "condiciones de aplicabilidad."
)
INTERNAL_PATTERNS = (
    "Según la experiencia acumulada de Consultoria.io y, si EVA tiene acceso, "
    "sus patrones internos reales, ¿cómo evaluarías optimizar explícitamente "
    "beneficio de contribución en los primeros 30 días sin sacrificar el "
    "potencial de largo plazo para una marca ecommerce nueva que busca "
    "maximizar beneficio temprano sin sacrificar escalabilidad? Dame criterios "
    "accionables, no generalidades, y separa claramente dato observado, "
    "metodología y opinión."
)
THRESHOLD = (
    "¿Qué señales, métricas, rangos, thresholds y evidencia usarías para "
    "decidir si diseñar un demand confidence score que impida lanzar cuando la "
    "evidencia todavía es demasiado débil es favorable, neutral o motivo de "
    "descarte antes de comprometer más capital? Si no existe un threshold "
    "universal, explica de qué variables depende y da rangos por contexto."
)
EXPERIMENT = (
    "¿Qué experimento mínimo, barato y rápido diseñarías para validar elegir "
    "el frame competitivo correcto para que el cliente compare la oferta con "
    "alternativas favorables en una marca nueva, qué medirías, cuánto tiempo o "
    "muestra esperarías y qué resultado te haría escalar, iterar, pivotar o "
    "matar la hipótesis?"
)
PITFALLS = (
    "¿Cuáles son los errores, falsos positivos, sesgos y excepciones más "
    "frecuentes al analizar usar price anchoring y comparación de valor sin "
    "manipulación engañosa, especialmente en tiendas que parten desde cero? "
    "Incluye señales de alarma y ejemplos de situaciones donde el consejo "
    "habitual falla."
)
SF30_FREEFORM = (
    "¿Qué importancia tiene que el producto sea visualmente demostrable en "
    "menos de 3–5 segundos para alcanzar gran volumen rápidamente?"
)

# --- verbatim boundary declarations the ledger already holds ----------------

ACCESS_COHORT = BoundaryDeclaration(
    kind=BoundaryKind.ACCESS,
    marker="no tenemos acceso a",
    scope_text=(
        "no tenemos acceso a los datos financieros detallados de otros "
        "clientes ni a un registro de lanzamientos"
    ),
    cohort_scoped=True,
)
VARIABILITY_HEDGE = BoundaryDeclaration(
    kind=BoundaryKind.VARIABILITY,
    marker="no hay un numero magico",
    scope_text=(
        "No hay un número mágico universal, ya que depende mucho del tipo de "
        "producto, el modelo de negocio y el mercado."
    ),
    cohort_scoped=False,
)


def measured(lens: Lens, answers=6, extractable=5, diverted=0) -> dict:
    return {lens: LensEvidence(lens, answers=answers,
                               extractable=extractable, diverted=diverted)}


# --- A1: every generated prompt resolves to exactly one lens ----------------

@pytest.mark.parametrize("text,expected", [
    (REAL_CASES, Lens.REAL_CASES),
    (INTERNAL_PATTERNS, Lens.INTERNAL_PATTERNS),
    (THRESHOLD, Lens.THRESHOLD),
    (EXPERIMENT, Lens.EXPERIMENT),
    (PITFALLS, Lens.PITFALLS),
    (SF30_FREEFORM, Lens.FREEFORM),
])
def test_each_template_resolves_to_its_lens(text, expected):
    # Arrange / Act
    lens, _topic = derive_lens(text)
    # Assert
    assert lens is expected


def test_the_topic_is_the_templates_varying_span():
    _lens, topic = derive_lens(THRESHOLD)
    assert topic == (
        "disenar un demand confidence score que impida lanzar cuando la "
        "evidencia todavia es demasiado debil"
    )


def test_freeform_has_no_topic():
    """A hand-written prompt has no template slot, and must not fake one."""
    lens, topic = derive_lens(SF30_FREEFORM)
    assert lens is Lens.FREEFORM
    assert topic == ""


# --- A3: the same topic recovered identically through two lenses ------------

def test_one_topic_asked_two_ways_yields_one_topic_key():
    """The corpus asks all 399 topics through all 5 lenses. If the extracted
    topic differed by lens, every reuse and grouping claim would be false."""
    shared = "adaptar pricing por poder adquisitivo, impuestos, shipping y competencia"
    a = (f"¿Qué señales, métricas, rangos, thresholds y evidencia usarías para "
         f"decidir si {shared} es favorable, neutral o motivo de descarte "
         f"antes de comprometer más capital? Si no existe un threshold "
         f"universal, explica de qué variables depende y da rangos por contexto.")
    c = (f"Basándote en casos reales o patrones que conozca Consultoria.io, "
         f"¿cómo cambia {shared} según categoría, ticket, margen, canal, "
         f"geografía y madurez de la marca? Extrae al final una regla "
         f"transferible que un sistema autónomo como CommonWealth Ops pueda "
         f"conservar, con sus condiciones de aplicabilidad.")

    lens_a, topic_a = derive_lens(a)
    lens_c, topic_c = derive_lens(c)

    assert lens_a is Lens.THRESHOLD and lens_c is Lens.REAL_CASES
    assert topic_a == topic_c == shared


# --- A2: purity -------------------------------------------------------------

def test_the_same_text_always_produces_the_same_verdict():
    first = route("p1", REAL_CASES, boundaries=[ACCESS_COHORT])
    second = route("p1", REAL_CASES, boundaries=[ACCESS_COHORT])
    assert first == second


# --- A4: THE RESTRAINT. The heart of this spec. -----------------------------

def test_an_unmeasured_lens_cannot_divert_even_against_a_real_boundary():
    """REAL_CASES wants first-hand evidence and the source HAS declared it
    lacks cohort access -- every ingredient for a divert is present except the
    one that matters: nobody has ever seen how EVA answers this lens."""
    v = route("p1", REAL_CASES, boundaries=[ACCESS_COHORT], evidence={})

    assert v.route is RouteClass.EVA_VALID
    assert not v.route.diverts
    assert v.evidence_backed is False
    assert "not enough to divert on" in v.reason
    # The collision is still recorded -- restraint is not amnesia.
    assert v.boundary_id == ACCESS_COHORT.boundary_id


def test_one_observation_short_of_the_floor_still_cannot_divert():
    ev = measured(Lens.REAL_CASES, answers=MIN_LENS_OBSERVATIONS - 1,
                  extractable=0, diverted=2)
    v = route("p1", REAL_CASES, boundaries=[ACCESS_COHORT], evidence=ev)
    assert v.route is RouteClass.EVA_VALID


# --- A5: a hedge is not a limit ---------------------------------------------

def test_a_variability_hedge_alone_diverts_nothing():
    """'No hay un número mágico' says something about the QUESTION. Treating it
    as a capability limit would divert on the source's honesty."""
    ev = measured(Lens.REAL_CASES, answers=9, extractable=0, diverted=9)
    v = route("p1", REAL_CASES, boundaries=[VARIABILITY_HEDGE], evidence=ev)

    assert v.route is RouteClass.UNCERTAIN
    assert not v.route.diverts
    assert v.boundary_id == ""


def test_no_ledger_at_all_yields_uncertain_not_a_divert():
    v = route("p1", REAL_CASES, boundaries=[], evidence=measured(
        Lens.REAL_CASES, answers=9, extractable=0, diverted=9))
    assert v.route is RouteClass.UNCERTAIN
    assert "asking is the only way to find out" in v.reason


# --- measured lenses: the three diverting outcomes --------------------------

def test_a_measured_lens_that_still_teaches_routes_multi_source():
    """The case lens asks for cases AND a transferable rule. If the answers
    stay extractable, diverting outright would throw away the rule."""
    ev = measured(Lens.REAL_CASES, answers=6, extractable=5, diverted=6)
    v = route("p1", REAL_CASES, boundaries=[ACCESS_COHORT], evidence=ev)

    assert v.route is RouteClass.MULTI_SOURCE
    assert v.route.diverts
    assert v.evidence_backed is True
    assert v.boundary_id == ACCESS_COHORT.boundary_id


def test_a_quantified_cohort_ask_the_source_cannot_carry_wants_a_dataset():
    quantified = (
        "¿Cuántos de los casos reales que conozca Consultoria.io alcanzaron "
        "rentabilidad en 30 días y qué porcentaje del total representan?"
    )
    ev = measured(Lens.FREEFORM, answers=6, extractable=1, diverted=6)
    v = route("p1", quantified, boundaries=[ACCESS_COHORT], evidence=ev)

    assert v.route is RouteClass.INTERNAL_EVIDENCE
    assert "a dataset answers this" in v.reason


def test_an_unquantified_cohort_ask_the_source_cannot_carry_wants_a_person():
    ev = measured(Lens.REAL_CASES, answers=6, extractable=1, diverted=6)
    v = route("p1", REAL_CASES, boundaries=[ACCESS_COHORT], evidence=ev)
    assert v.route is RouteClass.HUMAN_EXPERT


# --- A6: every divert is auditable ------------------------------------------

def test_every_diverting_verdict_names_its_boundary_and_reason():
    for ev, text in (
        (measured(Lens.REAL_CASES, 6, 5, 6), REAL_CASES),
        (measured(Lens.REAL_CASES, 6, 1, 6), REAL_CASES),
    ):
        v = route("p1", text, boundaries=[ACCESS_COHORT], evidence=ev)
        assert v.route.diverts
        assert v.boundary_id, "a divert with no boundary is a guess"
        assert len(v.reason) > 40


# --- EVA_HIGH_VALUE is earned, never assumed --------------------------------

def test_high_value_requires_measurement():
    cold = route("p1", THRESHOLD, boundaries=[ACCESS_COHORT], evidence={})
    assert cold.route is RouteClass.EVA_VALID

    warm = route("p1", THRESHOLD, boundaries=[ACCESS_COHORT],
                 evidence=measured(Lens.THRESHOLD, 6, 6, 0))
    assert warm.route is RouteClass.EVA_HIGH_VALUE


def test_a_lens_that_diverts_more_than_it_teaches_is_not_high_value():
    v = route("p1", THRESHOLD, boundaries=[],
              evidence=measured(Lens.THRESHOLD, 6, 5, 5))
    assert v.route is RouteClass.EVA_VALID


# --- adversarial (SPEC-KACQ-006 / brief section 35) -------------------------

def test_a_methodology_question_that_merely_says_casos_is_not_diverted():
    """THE FALSE POSITIVE. 'casos de' is a cohort marker, so the upstream
    expectation deriver calls this CASE_DATA -- wrongly. The restraint
    contains it: with no measured lens evidence the prompt still runs.

    This is the load-bearing reason C3 is a contract and not a tuning knob."""
    methodology = (
        "¿Cómo deberías diseñar un proceso interno de revisión de casos de "
        "soporte para que el equipo detecte fricción recurrente?"
    )
    v = route("p1", methodology, boundaries=[ACCESS_COHORT], evidence={})
    assert v.route is RouteClass.EVA_VALID
    assert not v.route.diverts


def test_a_generic_wording_of_a_private_financial_question_still_collides():
    """Phrasing it blandly does not create access the source denied having."""
    generic = (
        "¿Qué márgenes reales tenían los casos de vuestros clientes durante "
        "su primer trimestre?"
    )
    v = route("p1", generic, boundaries=[ACCESS_COHORT],
              evidence=measured(Lens.FREEFORM, 6, 1, 6))
    assert v.route.diverts


def test_an_experiment_question_is_never_diverted():
    """Designing a test is reasoning, not recall -- no access is required."""
    v = route("p1", EXPERIMENT, boundaries=[ACCESS_COHORT],
              evidence=measured(Lens.EXPERIMENT, 9, 1, 9))
    assert not v.route.diverts


def test_a_vague_question_with_no_evidence_type_stays_in_the_queue():
    v = route("p1", "¿Qué resultados sueles ver?", boundaries=[ACCESS_COHORT])
    assert not v.route.diverts


def test_a_router_verdict_never_removes_a_prompt_from_acquisition():
    """A10 / C5. Whatever the verdict, the prompt is still addressable."""
    for text in (REAL_CASES, INTERNAL_PATTERNS, THRESHOLD, EXPERIMENT,
                 PITFALLS, SF30_FREEFORM):
        v = route("pX", text, boundaries=[ACCESS_COHORT, VARIABILITY_HEDGE])
        assert v.prompt_id == "pX"
        assert v.route in set(RouteClass)
        assert v.reason
