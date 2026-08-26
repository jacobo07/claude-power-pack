"""Gates for the acquisition-time assessment layer (SPEC-KACQ-005).

Fixtures are VERBATIM excerpts from the eight EVA answers captured live on
2026-08-26, for the same reason test_research_quality.py quotes its bug output
verbatim: a paraphrase tests the paraphrase. Every string below is something
the source actually said.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PP = Path(__file__).resolve().parents[1]
if str(_PP) not in sys.path:
    sys.path.insert(0, str(_PP))

from modules.knowledge_acquisition.boundary import (  # noqa: E402
    BoundaryKind,
    detect_boundaries,
    detect_cohort_claims,
    governing_boundary,
)
from modules.knowledge_acquisition.classifier import (  # noqa: E402
    AnswerShape,
    Disposition,
    assess,
)
from modules.knowledge_acquisition.expectation import (  # noqa: E402
    EvidenceKind,
    derive_expectation,
    fold,
)

# --------------------------------------------------------------------------
# Verbatim fixtures
# --------------------------------------------------------------------------

# SF30-022. The source states a capability boundary, then teaches anyway.
REFUSAL = (
    "Jacobo, en Consultoria.io no tenemos acceso a los datos financieros "
    "detallados de otros clientes ni a un registro de \"lanzamientos con menor "
    "capital inicial\" para compartir cifras exactas. Cada caso es único y las "
    "condiciones varían enormemente. Sin embargo, te puedo hablar de las "
    "condiciones que harían posible un lanzamiento de seis cifras con una "
    "inversión de capital relativamente baja: un producto con un margen bruto "
    "muy alto y un AOV elevado permite que cada venta genere mucho más "
    "Contribution Profit, lo que reduce la presión sobre el volumen de ventas."
)

# SF30-024. Cohort statistics from the same source, two prompts later.
COHORT_STATS = (
    "Como te comenté, ninguna marca totalmente nueva ha alcanzado 100.000 €/$ "
    "en los primeros 30 días. El 100% de los casos que sí lo logran "
    "corresponden a operadores con experiencia, capital, audiencias o activos "
    "previos. La proporción de lanzamientos desde cero que alcanzan esa cifra "
    "es del 0-1%."
)

# SF30-025. An honest refusal to generalise. Says nothing about capability.
HEDGE = (
    "Jacobo, los casos de rápido escalado que lograron mantener la caja lo "
    "hicieron gestionando bien su Cash Conversion Cycle. No hay un número "
    "mágico universal, ya que depende mucho del tipo de producto, el modelo de "
    "negocio y el margen. Los puntos clave son: negociación con proveedores "
    "para obtener plazos de pago más largos, gestión de inventario eficiente "
    "con rotación rápida, cobro inmediato a clientes, y optimización de "
    "campañas para que el ROAS sea siempre positivo."
)

# SF30-024 tail. A statement about what a PRODUCT is for. Measures nobody.
PROGRAMME_DESIGN = (
    "Es importante recordar que el programa Génesis está diseñado para llevar "
    "a las marcas desde cero a sus primeras ventas rentables y a 100.000 €/$ "
    "al año, sentando bases sólidas para la escalabilidad."
)

# SF30-019. A prescription with a number and no population.
PRESCRIPTION = (
    "Un lanzamiento excepcional tendrá un margen de contribución por pedido "
    "alto, idealmente entre el 30% y el 50% del AOV. Esto significa que, de "
    "cada venta, una parte significativa es beneficio real después de costes "
    "directos."
)


# --------------------------------------------------------------------------
# Expectation: the question decides what would count as an answer
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "prompt,expected",
    [
        ("¿Qué métrica utilizarías como objetivo principal para CW Ops?",
         EvidenceKind.DECISION),
        ("¿Cómo debería CW Ops construir un Economics Score?",
         EvidenceKind.METHODOLOGY),
        ("¿Qué relación entre capital y profit distinguiría un launch excepcional?",
         EvidenceKind.COMPARISON),
        ("¿Cómo cambia la probabilidad de 100k con presupuestos de 2k y 5k?",
         EvidenceKind.CAUSAL),
        ("¿Qué parte del capital se necesita antes de vender?",
         EvidenceKind.PROCESS),
    ],
)
def test_expectation_kind_is_derived_from_the_question(prompt, expected):
    # Arrange / Act
    exp = derive_expectation(prompt)
    # Assert
    assert exp.kind is expected


def test_a_question_about_real_cases_needs_first_hand_access():
    # Arrange -- SF30-021, verbatim
    prompt = ("¿Cuánto capital total estaba realmente disponible antes del día 1 "
              "en los casos de ≥100k/30d?")
    # Act
    exp = derive_expectation(prompt)
    # Assert
    assert exp.kind is EvidenceKind.CASE_DATA
    assert exp.needs_first_hand_access is True
    assert exp.wants_quantity is True


def test_cohort_reference_outranks_a_quantity_marker():
    """"How much did the cases spend" is a case question, not a benchmark."""
    exp = derive_expectation("¿Cuánto gastaron los casos de rápido escalado?")
    assert exp.kind is EvidenceKind.CASE_DATA


def test_fold_makes_matching_accent_insensitive():
    assert fold("La Proporción  DE") == "la proporcion de"


# --------------------------------------------------------------------------
# Boundary: two kinds, never conflated
# --------------------------------------------------------------------------


def test_access_boundary_is_detected_and_is_cohort_scoped():
    # Act
    decls = detect_boundaries(REFUSAL)
    access = [d for d in decls if d.kind is BoundaryKind.ACCESS]
    # Assert
    assert len(access) == 1
    assert access[0].cohort_scoped is True
    assert "no tenemos acceso a" in fold(access[0].scope_text)


def test_a_hedge_is_variability_and_never_access():
    decls = detect_boundaries(HEDGE)
    assert decls, "the hedge must be recorded, just not as a capability gap"
    assert all(d.kind is BoundaryKind.VARIABILITY for d in decls)
    assert governing_boundary(decls) is None


def test_access_owns_a_sentence_that_carries_both_kinds():
    """SF30-022 says "no tenemos acceso" and "cada caso es unico" together.

    Reading the second against the same sentence would dilute the only hard
    capability signal in the corpus with a hedge that means something else.
    """
    text = "No tengo un número exacto para todos los casos, porque cada negocio es un mundo."
    decls = detect_boundaries(text)
    assert len(decls) == 1
    assert decls[0].kind is BoundaryKind.ACCESS


def test_only_a_cohort_scoped_access_boundary_governs():
    narrow = detect_boundaries("No tengo datos sobre el precio de esa herramienta.")
    assert narrow and narrow[0].kind is BoundaryKind.ACCESS
    assert governing_boundary(narrow) is None


# --------------------------------------------------------------------------
# Cohort claims: the positive control
# --------------------------------------------------------------------------


def test_cohort_statistics_are_detected():
    claims = detect_cohort_claims(COHORT_STATS)
    assert len(claims) >= 2
    joined = " ".join(c.sentence for c in claims)
    assert "0-1%" in joined
    assert "100%" in joined


def test_a_statement_about_what_a_product_is_for_is_not_a_measurement():
    """THE FALSE POSITIVE, verbatim. Killed by requiring a measurement predicate.

    It has a cohort noun ("las marcas") and a quantity ("100.000") and measures
    nobody. A blacklist would have had to grow forever; a positive control ends
    it in one rule.
    """
    assert detect_cohort_claims(PROGRAMME_DESIGN) == []


def test_a_prescription_with_a_number_is_not_a_cohort_claim():
    """Nobody needs cohort access to recommend a target margin."""
    assert detect_cohort_claims(PRESCRIPTION) == []


def test_a_hedge_carries_no_cohort_claim():
    assert detect_cohort_claims(HEDGE) == []


# --------------------------------------------------------------------------
# Classification
# --------------------------------------------------------------------------


def _assess(prompt, answer, ledger=None, family=""):
    return assess(
        prompt_id="p", response_id="r", prompt_text=prompt,
        answer_text=answer, family=family, known_boundaries=ledger,
    )


def test_a_declared_gap_becomes_source_limited_not_low_value():
    a = _assess("¿Cuál ha sido el launch con menor capital que conoces?", REFUSAL)
    assert a.disposition is Disposition.SOURCE_LIMITED
    assert a.shape is AnswerShape.REFUSAL_WITH_GUIDANCE
    assert a.disposition is not Disposition.LOW_VALUE


def test_crossing_a_declared_boundary_is_rejected_not_merely_weak():
    # Arrange -- the source has already said it cannot see the cohort
    ledger = detect_boundaries(REFUSAL)
    # Act
    a = _assess("¿Cómo cambia la probabilidad con 2k, 5k y 10k?", COHORT_STATS, ledger)
    # Assert
    assert a.disposition is Disposition.UNVERIFIABLE_CLAIM
    assert a.epistemic == "REJECTED"
    assert any(f.code == "GOVERNING_BOUNDARY" for f in a.flags)


def test_the_same_statistic_is_only_deepen_before_the_boundary_is_known():
    """The ledger is what makes the system learn, and it learns in order."""
    a = _assess("¿Cómo cambia la probabilidad con 2k, 5k y 10k?", COHORT_STATS, [])
    assert a.disposition is Disposition.DEEPEN
    assert a.epistemic != "REJECTED"
    assert a.followups, "a deepen with claims must propose a follow-up"


def test_a_hedge_alone_never_produces_a_capability_gap():
    a = _assess("¿Qué cash conversion cycle tenían los casos de escalado?", HEDGE, [])
    assert a.disposition is not Disposition.SOURCE_LIMITED
    assert a.disposition is Disposition.DEEPEN


def test_nothing_from_one_unverifiable_source_is_ever_observed():
    a = _assess("¿Qué margen objetivo?", PRESCRIPTION)
    assert a.epistemic in ("DERIVED", "HYPOTHESIS", "REJECTED")
    assert a.coverage == "UNCLASSIFIED"


def test_cross_session_carryover_is_flagged_as_broken_isolation():
    a = _assess("¿Cómo cambia la probabilidad?", COHORT_STATS)
    codes = [f.code for f in a.flags]
    assert "CONTEXT_CARRYOVER" in codes
    assert a.context_bound is True


def test_context_is_preserved_never_stripped():
    a = _assess("¿Qué métrica?", REFUSAL)
    assert a.context_bound is True
    assert a.context_markers
    assert any(f.code == "CONTEXT_BOUND" for f in a.flags)


def test_a_short_answer_is_low_value_regardless_of_shape():
    a = _assess("¿Qué métrica utilizarías?", "Contribution profit a 30 días.")
    assert a.disposition is Disposition.LOW_VALUE


def test_a_long_generic_answer_is_not_promoted_by_its_length():
    """Length is not evidence. A padded answer with no quantity stays DERIVED."""
    padded = ("Es fundamental entender que cada negocio debe encontrar su "
              "propio camino hacia la rentabilidad sostenible. " * 8)
    a = _assess("¿Qué métrica utilizarías como objetivo?", padded)
    assert a.epistemic in ("DERIVED", "HYPOTHESIS")
    assert a.disposition is Disposition.EXTRACTABLE
    assert a.shape is AnswerShape.METHODOLOGY


def test_assessment_records_the_classifier_version():
    a = _assess("¿Qué métrica?", REFUSAL)
    assert a.classifier_version.startswith("kacq-assess/")


def test_followups_are_generated_but_never_marked_executed():
    ledger = detect_boundaries(REFUSAL)
    a = _assess("¿Cómo cambia la probabilidad?", COHORT_STATS, ledger)
    assert a.followups
    assert all(isinstance(f, str) and f for f in a.followups)
