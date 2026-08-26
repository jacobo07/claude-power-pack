"""Tests for the raw vault and the durable registry/ledger.

The interesting tests here are not the happy paths. They are the four ways a
long acquisition actually loses data:

  * the process dies mid-prompt and the job is stranded in RUNNING forever
  * the answer is persisted but the status update never lands
  * two workers claim the same prompt
  * something drags a COMPLETE prompt back into the work set
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from modules.knowledge_acquisition.corpus_parser import parse_corpus
from modules.knowledge_acquisition.models import (
    IllegalTransition,
    IntegrityVerdict,
    JobState,
)
from modules.knowledge_acquisition.raw_vault import RawVault, RawVaultError
from modules.knowledge_acquisition.store import Store


@pytest.fixture()
def vault(tmp_path):
    return RawVault(tmp_path / "raw")


@pytest.fixture()
def store(tmp_path, vault):
    s = Store(tmp_path / "kacq.db", vault)
    yield s
    s.close()


def _corpus(tmp_path, name="c.md", n=3, answered=0):
    """Build a small corpus file; the first `answered` prompts carry answers."""
    parts = ["## Fam A"]
    for i in range(1, n + 1):
        parts.append(f"{i}. Pregunta numero {i}?")
        parts.append("")
        if i <= answered:
            parts.append("Respuesta capturada. " + ("z" * 300))
            parts.append("")
    p = tmp_path / name
    p.write_text("\n".join(parts), encoding="utf-8")
    return parse_corpus(p, "C", expected_count=n)


# --------------------------------------------------------------------------
# Raw vault
# --------------------------------------------------------------------------


def test_vault_roundtrip(vault):
    art = vault.put("hola mundo", kind="response", prompt_id="p1")
    assert vault.get(art.digest, "response") == "hola mundo"
    assert vault.meta(art.digest, "response")["prompt_id"] == "p1"


def test_vault_is_write_once(vault):
    # Arrange
    a = vault.put("mismo texto", kind="response", prompt_id="p1")
    mtime = a.path.stat().st_mtime_ns

    # Act — a second put of identical bytes must not rewrite the file
    b = vault.put("mismo texto", kind="response", prompt_id="p1")

    # Assert
    assert b.already_present is True
    assert b.digest == a.digest
    assert b.path.stat().st_mtime_ns == mtime


def test_vault_refuses_empty_artifact(vault):
    with pytest.raises(RawVaultError):
        vault.put("", kind="response", prompt_id="p1")


def test_vault_detects_corruption(vault):
    # Arrange
    art = vault.put("contenido original", kind="response", prompt_id="p1")

    # Act — tamper with the stored bytes
    art.path.write_text("contenido alterado", encoding="utf-8")

    # Assert — must be loud, not silently trusted
    with pytest.raises(RawVaultError, match="corruption"):
        vault.get(art.digest, "response")


def test_vault_verify_all_reports_corrupt_artifacts(vault):
    good = vault.put("bueno", kind="response", prompt_id="p1")
    bad = vault.put("malo", kind="response", prompt_id="p2")
    bad.path.write_text("alterado", encoding="utf-8")

    checked, corrupt = vault.verify_all()

    assert checked == 2
    assert corrupt == [f"response/{bad.digest}"]
    assert good.digest not in corrupt


# --------------------------------------------------------------------------
# Ingest
# --------------------------------------------------------------------------


def test_ingest_marks_already_answered_prompts_complete(tmp_path, store):
    # Arrange — 3 prompts, the first 2 already answered in the source document
    result = _corpus(tmp_path, n=3, answered=2)

    # Act
    stats = store.ingest_corpus(result)

    # Assert — answered prompts never enter the work set
    assert stats["inserted"] == 3
    assert stats["imported_answers"] == 2
    assert store.stats()["by_state"]["COMPLETE"] == 2
    assert store.stats()["by_state"]["PENDING"] == 1


def test_ingest_is_idempotent(tmp_path, store):
    # Arrange
    result = _corpus(tmp_path, n=3, answered=1)
    store.ingest_corpus(result)

    # Act — re-ingesting the same corpus must change nothing
    second = store.ingest_corpus(result)

    # Assert
    assert second["inserted"] == 0
    assert second["already_present"] == 3
    assert store.stats()["prompts"] == 3


def test_imported_answers_are_marked_unverified(tmp_path, store):
    # An answer this system did not capture must not claim captured integrity.
    result = _corpus(tmp_path, n=1, answered=1)
    store.ingest_corpus(result)

    row = store.responses_for(result.prompts[0].prompt_id)[0]

    assert row["integrity_verdict"] == IntegrityVerdict.UNVERIFIED.value


# --------------------------------------------------------------------------
# Claiming and ordering
# --------------------------------------------------------------------------


def test_claim_respects_priority_then_ordinal(tmp_path, store):
    # Arrange — a low-priority-number corpus must drain first
    low = _corpus(tmp_path, "low.md", n=2)
    store.ingest_corpus(low, priority=10)

    # Act
    first = store.claim_next("w1")

    # Assert
    assert first is not None
    assert first.ordinal == 1


def test_claim_is_exclusive(tmp_path, store):
    # Arrange
    store.ingest_corpus(_corpus(tmp_path, n=2))

    # Act — two workers, two claims
    a = store.claim_next("w1")
    b = store.claim_next("w2")

    # Assert — never the same prompt
    assert a is not None and b is not None
    assert a.prompt_id != b.prompt_id


def test_claim_returns_none_when_drained(tmp_path, store):
    store.ingest_corpus(_corpus(tmp_path, n=1))
    store.claim_next("w1")

    assert store.claim_next("w1") is None


def test_failed_job_is_requeued_after_backoff(tmp_path, store):
    # Arrange — a failure that has already served its backoff window
    store.ingest_corpus(_corpus(tmp_path, n=1))
    pid = store.claim_next("w1").prompt_id
    store.transition(pid, JobState.FAILED, reason="boom")

    # FAILED is not claimable on its own; something must requeue it.
    assert store.claim_next("w1") is None

    # Act
    moved = store.requeue_failed(max_attempts=5, base_seconds=0)

    # Assert
    assert moved == 1
    again = store.claim_next("w1")
    assert again is not None and again.prompt_id == pid


def test_backoff_holds_a_fresh_failure(tmp_path, store):
    # Arrange — a failure that has NOT yet served its backoff window
    store.ingest_corpus(_corpus(tmp_path, n=1))
    pid = store.claim_next("w1").prompt_id
    store.transition(pid, JobState.FAILED, reason="boom")

    # Act
    moved = store.requeue_failed(max_attempts=5, base_seconds=600)

    # Assert — retry is bounded in time, not just in count
    assert moved == 0
    assert store.claim_next("w1") is None


def test_retry_is_bounded_by_attempt_count(tmp_path, store):
    # Arrange
    store.ingest_corpus(_corpus(tmp_path, n=1))
    pid = store.claim_next("w1").prompt_id
    store.transition(pid, JobState.FAILED, reason="boom")

    # Act / Assert — one attempt already spent, so max_attempts=1 refuses it
    assert store.requeue_failed(max_attempts=1, base_seconds=0) == 0
    assert store.requeue_failed(max_attempts=5, base_seconds=0) == 1


# --------------------------------------------------------------------------
# The four data-loss modes
# --------------------------------------------------------------------------


def test_crashed_worker_job_is_recovered_by_lease_expiry(tmp_path, store):
    # Arrange — claim a job, then simulate the process dying: no transition,
    # no cleanup, nothing graceful.
    store.ingest_corpus(_corpus(tmp_path, n=1))
    claimed = store.claim_next("dead-worker", lease_seconds=1)
    assert claimed is not None

    past = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
    store.con.execute(
        "UPDATE job SET lease_expires_at=? WHERE prompt_id=?", (past, claimed.prompt_id)
    )

    # Act
    recovered = store.recover_expired_leases()

    # Assert — back in the work set, attempt count preserved
    assert recovered == 1
    again = store.claim_next("fresh-worker")
    assert again is not None
    assert again.prompt_id == claimed.prompt_id
    assert again.attempt_count == 2


def test_answer_persisted_but_status_lost_does_not_duplicate(tmp_path, store):
    # Arrange — the classic at-least-once seam: raw landed, status did not.
    store.ingest_corpus(_corpus(tmp_path, n=1))
    claimed = store.claim_next("w1")
    digest = store.record_response(
        claimed.prompt_id, "La respuesta real de EVA.",
        source="eva", source_version="1", verdict=IntegrityVerdict.OK,
    )
    # process dies here — job never transitioned to COMPLETE
    past = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
    store.con.execute(
        "UPDATE job SET lease_expires_at=? WHERE prompt_id=?", (past, claimed.prompt_id)
    )
    store.recover_expired_leases()

    # Act — the retry re-captures the identical answer
    again = store.claim_next("w2")
    digest2 = store.record_response(
        again.prompt_id, "La respuesta real de EVA.",
        source="eva", source_version="1", verdict=IntegrityVerdict.OK,
    )

    # Assert — same digest, one row. At-least-once execution, exactly-one row.
    assert digest2 == digest
    assert len(store.responses_for(claimed.prompt_id)) == 1


def test_complete_prompt_can_never_return_to_the_work_set(tmp_path, store):
    # Arrange
    store.ingest_corpus(_corpus(tmp_path, n=1))
    claimed = store.claim_next("w1")
    store.transition(claimed.prompt_id, JobState.COMPLETE, reason="captured")

    # Act / Assert
    with pytest.raises(IllegalTransition):
        store.transition(claimed.prompt_id, JobState.PENDING, reason="oops")
    assert store.claim_next("w2") is None


def test_illegal_transition_leaves_state_untouched(tmp_path, store):
    # Arrange
    store.ingest_corpus(_corpus(tmp_path, n=1))
    pid = store.prompt_ids()[0] if hasattr(store, "prompt_ids") else None
    pid = pid or store.con.execute("SELECT prompt_id FROM prompt").fetchone()[0]

    # Act / Assert — PENDING cannot jump straight to COMPLETE
    with pytest.raises(IllegalTransition):
        store.transition(pid, JobState.COMPLETE, reason="skip execution")
    assert store.con.execute(
        "SELECT state FROM job WHERE prompt_id=?", (pid,)
    ).fetchone()[0] == "PENDING"


# --------------------------------------------------------------------------
# Durability across process restart
# --------------------------------------------------------------------------


def test_state_survives_store_reopen(tmp_path, vault):
    # Arrange — write with one Store instance
    db = tmp_path / "kacq.db"
    s1 = Store(db, vault)
    s1.ingest_corpus(_corpus(tmp_path, n=3, answered=1))
    claimed = s1.claim_next("w1")
    s1.record_response(
        claimed.prompt_id, "respuesta persistida",
        source="eva", source_version="1", verdict=IntegrityVerdict.OK,
    )
    s1.transition(claimed.prompt_id, JobState.COMPLETE, reason="captured")
    s1.close()

    # Act — a completely new process opens the same database
    s2 = Store(db, RawVault(tmp_path / "raw"))
    try:
        stats = s2.stats()
        # Assert
        assert stats["by_state"]["COMPLETE"] == 2  # 1 imported + 1 captured
        assert stats["by_state"]["PENDING"] == 1
        assert len(s2.responses_for(claimed.prompt_id)) == 1
    finally:
        s2.close()


# --------------------------------------------------------------------------
# Observability
# --------------------------------------------------------------------------


def test_event_log_records_every_transition(tmp_path, store):
    store.ingest_corpus(_corpus(tmp_path, n=1))
    claimed = store.claim_next("w1")
    store.transition(claimed.prompt_id, JobState.COMPLETE, reason="captured")

    history = [(e["from_state"], e["to_state"]) for e in store.history(claimed.prompt_id)]

    assert history == [(None, "PENDING"), ("PENDING", "RUNNING"), ("RUNNING", "COMPLETE")]


def test_fts_search_finds_prompts(tmp_path, store):
    store.ingest_corpus(_corpus(tmp_path, n=3))

    hits = store.search_prompts("numero")

    assert len(hits) == 3
    assert all("Pregunta" in h["raw_prompt"] for h in hits)
