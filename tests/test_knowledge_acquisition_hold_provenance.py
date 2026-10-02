"""Gates for HELD jobs and operator provenance attestations (2026-10-02).

Two Owner decisions after the EVA operator explained how EVA's figures are
built: real-case questions wait for the connected-data product (HELD), and
cohort statistics are labelled self-reported rather than unsourced
(provenance.py). Each behaviour is paired with the control that shows the old
path still holds when the new input is absent.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PP = Path(__file__).resolve().parents[1]
if str(_PP) not in sys.path:
    sys.path.insert(0, str(_PP))

from modules.knowledge_acquisition.boundary import detect_boundaries  # noqa: E402
from modules.knowledge_acquisition.classifier import Disposition, assess  # noqa: E402
from modules.knowledge_acquisition.cli import _select_by_lens  # noqa: E402
from modules.knowledge_acquisition.corpus_parser import parse_corpus  # noqa: E402
from modules.knowledge_acquisition.models import (  # noqa: E402
    IllegalTransition,
    JobState,
)
from modules.knowledge_acquisition.provenance import attestation_for  # noqa: E402
from modules.knowledge_acquisition.raw_vault import RawVault  # noqa: E402
from modules.knowledge_acquisition.store import Store  # noqa: E402

# Verbatim, SF30-022 and SF30-024 (same fixtures as test_..._phase5.py).
REFUSAL = (
    "Jacobo, en Consultoria.io no tenemos acceso a los datos financieros "
    "detallados de otros clientes ni a un registro de \"lanzamientos con menor "
    "capital inicial\" para compartir cifras exactas."
)
COHORT_STATS = (
    "Como te comenté, ninguna marca totalmente nueva ha alcanzado 100.000 €/$ "
    "en los primeros 30 días. El 100% de los casos que sí lo logran "
    "corresponden a operadores con experiencia, capital, audiencias o activos "
    "previos. La proporción de lanzamientos desde cero que alcanzan esa cifra "
    "es del 0-1%."
)
CASE_Q = "¿Qué capital tenían los casos de 100k en 30 días?"


def _assess(answer, *, attestation=None, prompt="¿Cómo cambia la probabilidad con 2k, 5k y 10k?"):
    return assess(
        prompt_id="p", response_id="r", prompt_text=prompt, answer_text=answer,
        known_boundaries=detect_boundaries(REFUSAL), attestation=attestation,
    )


# --------------------------------------------------------------------------
# Provenance attestation
# --------------------------------------------------------------------------


def test_attested_cohort_claim_is_self_reported_not_unverifiable():
    # Arrange
    att = attestation_for("eva")
    # Act
    a = _assess(COHORT_STATS, attestation=att)
    # Assert
    assert a.disposition is Disposition.DEEPEN
    assert any(f.code == "SELF_REPORTED_AGGREGATE" for f in a.flags)
    assert a.followups, "the 'how many cases?' follow-up must survive"


def test_without_an_attestation_the_crossing_is_still_unverifiable():
    """Control: the new branch fires only on the new input."""
    a = _assess(COHORT_STATS, attestation=None)
    assert a.disposition is Disposition.UNVERIFIABLE_CLAIM
    assert not any(f.code == "SELF_REPORTED_AGGREGATE" for f in a.flags)


def test_an_attestation_never_raises_the_epistemic_cap():
    a = _assess(COHORT_STATS, attestation=attestation_for("eva"))
    assert a.epistemic in ("DERIVED", "HYPOTHESIS")
    assert a.coverage == "UNCLASSIFIED"


def test_an_attestation_never_lifts_route_to_expert():
    """Connected case data still does not exist; case questions still route away."""
    a = _assess(COHORT_STATS, attestation=attestation_for("eva"), prompt=CASE_Q)
    assert a.route_to_expert is True


def test_attestation_lookup_is_per_interface():
    assert attestation_for("eva") is not None
    assert attestation_for("EVA") is not None
    assert attestation_for("some-other-source") is None
    assert attestation_for(None) is None


def test_attestation_names_a_role_and_a_date_not_a_person():
    att = attestation_for("eva")
    assert att.attested_on == "2026-10-02"
    assert "head of AI" in att.attested_by
    assert "may include the Owner's own store" in att.weaknesses


# --------------------------------------------------------------------------
# HELD
# --------------------------------------------------------------------------

REAL_CASE_PROMPT = ("Basándote en casos reales o patrones que conozca Consultoria.io, "
                    "¿cómo cambia el CAC según categoría, ticket medio y canal?")
THRESHOLD_PROMPT = ("¿Qué señales, métricas, rangos, thresholds y evidencia usarías para "
                    "decidir si el CAC es favorable, neutral o desfavorable?")


@pytest.fixture()
def store(tmp_path):
    s = Store(tmp_path / "kacq.db", RawVault(tmp_path / "raw"))
    yield s
    s.close()


def _ingest(tmp_path, store):
    p = tmp_path / "c.md"
    p.write_text(f"## Fam A\n1. {THRESHOLD_PROMPT}\n\n2. {REAL_CASE_PROMPT}\n",
                 encoding="utf-8")
    store.ingest_corpus(parse_corpus(p, "C", expected_count=2))


def _hold_real_cases(store):
    rows = _select_by_lens(store, "REAL_CASES", ("PENDING", "FAILED"), None)
    for r in rows:
        store.transition(r["prompt_id"], JobState.HELD, reason="test", actor="owner")
    return rows


def test_hold_selects_only_the_named_lens(tmp_path, store):
    # Arrange
    _ingest(tmp_path, store)
    # Act
    rows = _hold_real_cases(store)
    # Assert -- exactly the real-case prompt, not the threshold one
    assert [r["external_id"] for r in rows] == ["2"]


def test_a_held_job_is_never_claimed(tmp_path, store):
    # Arrange
    _ingest(tmp_path, store)
    _hold_real_cases(store)
    # Act
    first = store.claim_next("w1")
    second = store.claim_next("w1")
    # Assert -- the unheld prompt is claimable (control), the held one is not
    assert first is not None and first.external_id == "1"
    assert second is None


def test_release_returns_a_held_job_to_the_queue(tmp_path, store):
    _ingest(tmp_path, store)
    held = _hold_real_cases(store)
    store.claim_next("w1")  # drain the unheld one
    store.transition(held[0]["prompt_id"], JobState.PENDING, reason="release", actor="owner")
    again = store.claim_next("w1")
    assert again is not None and again.external_id == "2"


def test_a_running_job_cannot_be_held(tmp_path, store):
    _ingest(tmp_path, store)
    job = store.claim_next("w1")
    with pytest.raises(IllegalTransition):
        store.transition(job.prompt_id, JobState.HELD, reason="test", actor="owner")


def test_a_held_job_cannot_be_run_directly(tmp_path, store):
    _ingest(tmp_path, store)
    held = _hold_real_cases(store)
    with pytest.raises(IllegalTransition):
        store.transition(held[0]["prompt_id"], JobState.RUNNING, reason="x", actor="x")
