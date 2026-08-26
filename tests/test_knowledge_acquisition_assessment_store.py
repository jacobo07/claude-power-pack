"""Persistence gates for the assessment layer (SPEC-KACQ-005 sec.4.6).

The contract under test is that assessment is strictly downstream of raw: it is
versioned, it never overwrites, and nothing it does can cost a captured answer.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PP = Path(__file__).resolve().parents[1]
if str(_PP) not in sys.path:
    sys.path.insert(0, str(_PP))

from modules.knowledge_acquisition.boundary import detect_boundaries  # noqa: E402
from modules.knowledge_acquisition.classifier import assess  # noqa: E402
from modules.knowledge_acquisition.corpus_parser import parse_corpus  # noqa: E402
from modules.knowledge_acquisition.expectation import CLASSIFIER_VERSION  # noqa: E402
from modules.knowledge_acquisition.models import IntegrityVerdict  # noqa: E402
from modules.knowledge_acquisition.raw_vault import RawVault  # noqa: E402
from modules.knowledge_acquisition.store import Store  # noqa: E402

REFUSAL = (
    "Jacobo, en Consultoria.io no tenemos acceso a los datos financieros "
    "detallados de otros clientes ni a un registro de lanzamientos para "
    "compartir cifras exactas. Sin embargo, te puedo hablar de las condiciones "
    "que harian posible un lanzamiento de seis cifras con una inversion "
    "relativamente baja: un margen bruto alto y un AOV elevado reducen la "
    "presion sobre el volumen de ventas y sobre el gasto publicitario."
)


@pytest.fixture()
def vault(tmp_path):
    return RawVault(tmp_path / "raw")


@pytest.fixture()
def store(tmp_path, vault):
    s = Store(tmp_path / "kacq.db", vault)
    yield s
    s.close()


def _corpus(tmp_path, n=3):
    parts = ["## Fam A"]
    for i in range(1, n + 1):
        parts.append(f"{i}. Cuanto capital tenian los casos de escalado numero {i}?")
        parts.append("")
    p = tmp_path / "c.md"
    p.write_text("\n".join(parts), encoding="utf-8")
    return parse_corpus(p, "C", expected_count=n)


def _seeded(store, tmp_path, n=3):
    store.ingest_corpus(_corpus(tmp_path, n))
    return [r["prompt_id"] for r in store.con.execute(
        "SELECT prompt_id FROM prompt ORDER BY ordinal")]


def _assess_and_record(store, prompt_id, answer, *, ledger=None):
    digest = store.record_response(
        prompt_id, answer, source="eva", source_version="test",
        verdict=IntegrityVerdict.OK,
    )
    a = assess(
        prompt_id=prompt_id, response_id=digest,
        prompt_text="Cuanto capital tenian los casos?", answer_text=answer,
        known_boundaries=ledger if ledger is not None else store.known_boundaries(),
    )
    written = store.record_assessment(a)
    return a, written


# --------------------------------------------------------------------------
# Round-trip and versioning
# --------------------------------------------------------------------------


def test_assessment_round_trips(store, tmp_path):
    # Arrange
    pid = _seeded(store, tmp_path)[0]
    # Act
    a, written = _assess_and_record(store, pid, REFUSAL)
    # Assert
    assert written is True
    stats = store.assessment_stats()
    assert stats["assessed"] == 1
    assert stats["by_disposition"][a.disposition.value] == 1
    assert stats["context_bound"] == 1


def test_re_running_the_same_version_is_a_no_op(store, tmp_path):
    pid = _seeded(store, tmp_path)[0]
    _assess_and_record(store, pid, REFUSAL)
    _, written_again = _assess_and_record(store, pid, REFUSAL)
    assert written_again is False
    assert store.assessment_stats()["assessed"] == 1


def test_a_new_classifier_version_adds_a_row_and_never_overwrites(store, tmp_path):
    """A stored judgment is the only record of what the code believed then.

    Overwriting it on a version bump would destroy the evidence of a
    classifier regression at the moment it becomes most useful.
    """
    # Arrange
    pid = _seeded(store, tmp_path)[0]
    a, _ = _assess_and_record(store, pid, REFUSAL)

    # Act -- same response, a later classifier
    from dataclasses import replace
    store.record_assessment(replace(a, classifier_version="kacq-assess/9.9.9"))

    # Assert
    rows = store.con.execute(
        "SELECT classifier_version FROM assessment WHERE response_id=?",
        (a.response_id,)).fetchall()
    assert len(rows) == 2
    assert {r[0] for r in rows} == {CLASSIFIER_VERSION, "kacq-assess/9.9.9"}


# --------------------------------------------------------------------------
# The ledger accumulates, and that is what makes the system learn
# --------------------------------------------------------------------------


def test_boundaries_are_persisted_and_returned_as_declarations(store, tmp_path):
    pid = _seeded(store, tmp_path)[0]
    _assess_and_record(store, pid, REFUSAL)

    ledger = store.known_boundaries()
    assert ledger, "the declared boundary must survive the process"
    assert any(b.kind.value == "ACCESS" and b.cohort_scoped for b in ledger)


def test_a_boundary_declared_twice_is_counted_not_duplicated(store, tmp_path):
    pids = _seeded(store, tmp_path)
    _assess_and_record(store, pids[0], REFUSAL)
    _assess_and_record(store, pids[1], REFUSAL + " Un matiz adicional distinto.")

    rows = store.assessment_stats()["boundaries"]
    access = [r for r in rows if r["kind"] == "ACCESS"]
    assert len(access) == 1
    assert access[0]["times_seen"] == 2


def test_the_ledger_escalates_a_repeated_statistic_across_runs(store, tmp_path):
    """Same claim, different knowledge. Before the boundary: DEEPEN.
    After it: unsourced by the source's own admission."""
    # Arrange
    pids = _seeded(store, tmp_path)
    stats_answer = (
        "El 100% de los casos que lo logran corresponden a operadores con "
        "experiencia previa. La proporcion de lanzamientos desde cero que "
        "alcanzan esa cifra es del 0-1%, segun lo que hemos visto en el mercado."
    )
    before, _ = _assess_and_record(store, pids[0], stats_answer, ledger=[])
    assert before.disposition.value == "DEEPEN"

    # Act -- the source now declares the boundary, then we re-judge
    _assess_and_record(store, pids[1], REFUSAL)
    after = assess(
        prompt_id=pids[2], response_id="r-new",
        prompt_text="Cuanto capital?", answer_text=stats_answer,
        known_boundaries=store.known_boundaries(),
    )

    # Assert
    assert after.disposition.value == "UNVERIFIABLE_CLAIM"
    assert after.epistemic == "REJECTED"


# --------------------------------------------------------------------------
# Backfill selection
# --------------------------------------------------------------------------


def test_unassessed_responses_shrinks_as_work_lands(store, tmp_path):
    pids = _seeded(store, tmp_path)
    for pid in pids[:2]:
        store.record_response(pid, REFUSAL + pid[:8], source="eva",
                              source_version="t", verdict=IntegrityVerdict.OK)
    assert len(store.unassessed_responses(CLASSIFIER_VERSION)) == 2

    _assess_and_record(store, pids[2], REFUSAL + "otra cosa distinta aqui")
    remaining = store.unassessed_responses(CLASSIFIER_VERSION)
    assert len(remaining) == 2
    assert all(r["prompt_id"] != pids[2] for r in remaining)


# --------------------------------------------------------------------------
# Raw sovereignty
# --------------------------------------------------------------------------


def test_two_prompts_given_the_identical_answer_both_keep_it(store, tmp_path):
    """A canned refusal reaching two prompts must not erase one of them.

    response_id is content-addressed, so an identical answer to a different
    prompt collides on the primary key. If that write is silently ignored the
    second prompt is COMPLETE with no retrievable answer -- a lost capture that
    looks like a success. Adversarial case from the brief: "repeated answer
    from previous prompt".
    """
    pids = _seeded(store, tmp_path)
    canned = "No tenemos acceso a esos datos. " + ("Detalle util. " * 40)

    store.record_response(pids[0], canned, source="eva", source_version="t",
                          verdict=IntegrityVerdict.OK)
    store.record_response(pids[1], canned, source="eva", source_version="t",
                          verdict=IntegrityVerdict.OK)

    assert len(store.responses_for(pids[0])) == 1
    assert len(store.responses_for(pids[1])) == 1, (
        "the second prompt's answer was swallowed by the content-address "
        "collision"
    )
