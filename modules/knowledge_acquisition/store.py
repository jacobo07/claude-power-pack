"""Durable prompt registry and job ledger.

SQLite (WAL) rather than the estate's usual JSONL-append-and-fold, because
2,200 rows with a mutating state machine need transactional status updates.
An append log gives durability but not atomic read-modify-write, and the whole
point of this ledger is that two things never disagree about whether a prompt
was answered.

CRASH RECOVERY is lease-based, not heuristic. A worker claims a job by moving
it PENDING -> RUNNING inside one transaction and stamping a lease expiry. If
the process dies, nothing cleans up -- but the lease expires, and the next
`recover_expired_leases()` returns the job to PENDING with its attempt count
intact. There is no state that requires a graceful shutdown to be correct.

FTS5 sidecars are isolated per this module (own tables, own triggers). They
are a derived index; the raw vault remains the source of truth.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from .corpus_parser import ParseResult
from .models import (
    EXTRACTOR_VERSION,
    ConversationMode,
    IllegalTransition,
    IntegrityVerdict,
    JobState,
    assert_transition,
    response_row_id,
    utc_now,
)
from .raw_vault import RawVault

DEFAULT_LEASE_SECONDS = 900


class StoreError(Exception):
    """Raised on a refused operation. Never downgraded to a warning."""


_SCHEMA = """
CREATE TABLE IF NOT EXISTS corpus (
    corpus_id      TEXT PRIMARY KEY,
    source_path    TEXT NOT NULL,
    declared_count INTEGER NOT NULL,
    ingested_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prompt (
    prompt_id         TEXT PRIMARY KEY,
    corpus_id         TEXT NOT NULL REFERENCES corpus(corpus_id),
    external_id       TEXT NOT NULL,
    ordinal           INTEGER NOT NULL,
    family            TEXT NOT NULL,
    raw_prompt        TEXT NOT NULL,
    raw_digest        TEXT NOT NULL,
    conversation_mode TEXT NOT NULL,
    priority          INTEGER NOT NULL DEFAULT 100,
    parent_prompt_id  TEXT REFERENCES prompt(prompt_id),
    frontier_origin   TEXT,
    created_at        TEXT NOT NULL,
    UNIQUE (corpus_id, external_id)
);

CREATE TABLE IF NOT EXISTS job (
    prompt_id        TEXT PRIMARY KEY REFERENCES prompt(prompt_id),
    state            TEXT NOT NULL,
    attempt_count    INTEGER NOT NULL DEFAULT 0,
    last_error_class TEXT,
    last_error       TEXT,
    lease_owner      TEXT,
    lease_expires_at TEXT,
    updated_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS response (
    response_id       TEXT PRIMARY KEY,
    prompt_id         TEXT NOT NULL REFERENCES prompt(prompt_id),
    raw_digest        TEXT NOT NULL,
    char_count        INTEGER NOT NULL,
    source            TEXT NOT NULL,
    source_version    TEXT NOT NULL,
    extractor_version TEXT NOT NULL,
    integrity_verdict TEXT NOT NULL,
    integrity_reason  TEXT NOT NULL DEFAULT '',
    captured_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS event (
    event_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id  TEXT NOT NULL,
    from_state TEXT,
    to_state   TEXT NOT NULL,
    reason     TEXT NOT NULL DEFAULT '',
    actor      TEXT NOT NULL DEFAULT '',
    at         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_job_state    ON job(state);
CREATE INDEX IF NOT EXISTS ix_prompt_order ON prompt(priority, ordinal);
CREATE INDEX IF NOT EXISTS ix_resp_prompt  ON response(prompt_id);
CREATE INDEX IF NOT EXISTS ix_event_prompt ON event(prompt_id);
"""

# Isolated FTS5 sidecars -- own tables, own triggers, never a shared index.
_FTS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS kacq_prompt_fts
    USING fts5(prompt_id UNINDEXED, question, family, tokenize='unicode61');

CREATE TRIGGER IF NOT EXISTS kacq_prompt_ai AFTER INSERT ON prompt BEGIN
    INSERT INTO kacq_prompt_fts(prompt_id, question, family)
    VALUES (new.prompt_id, new.raw_prompt, new.family);
END;

CREATE TRIGGER IF NOT EXISTS kacq_prompt_ad AFTER DELETE ON prompt BEGIN
    DELETE FROM kacq_prompt_fts WHERE prompt_id = old.prompt_id;
END;

CREATE VIRTUAL TABLE IF NOT EXISTS kacq_response_fts
    USING fts5(response_id UNINDEXED, prompt_id UNINDEXED, body,
               tokenize='unicode61');
"""


@dataclass(frozen=True)
class ClaimedJob:
    prompt_id: str
    external_id: str
    corpus_id: str
    family: str
    ordinal: int
    raw_prompt: str
    conversation_mode: str
    attempt_count: int


def _has_fts5() -> bool:
    con = sqlite3.connect(":memory:")
    try:
        con.execute("CREATE VIRTUAL TABLE t USING fts5(x)")
        return True
    except sqlite3.OperationalError:
        return False
    finally:
        con.close()


class Store:
    """The registry + ledger. One instance per process."""

    def __init__(self, db_path: Path, vault: RawVault) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.vault = vault

        if not _has_fts5():
            raise StoreError(
                "this SQLite build has no FTS5; the registry requires it for "
                "prompt/response search. Rebuild python's sqlite3 with FTS5."
            )

        self.con = sqlite3.connect(str(self.db_path), isolation_level=None)
        self.con.row_factory = sqlite3.Row
        self.con.execute("PRAGMA journal_mode=WAL")
        self.con.execute("PRAGMA foreign_keys=ON")
        self.con.execute("PRAGMA synchronous=FULL")
        self.con.executescript(_SCHEMA)
        self.con.executescript(_FTS_SCHEMA)

    def close(self) -> None:
        self.con.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Connection]:
        self.con.execute("BEGIN IMMEDIATE")
        try:
            yield self.con
            self.con.execute("COMMIT")
        except BaseException:
            self.con.execute("ROLLBACK")
            raise

    # -- ingest -------------------------------------------------------------

    def ingest_corpus(
        self,
        result: ParseResult,
        *,
        priority: int = 100,
        conversation_mode: ConversationMode = ConversationMode.ISOLATED,
        source: str = "imported",
    ) -> dict:
        """Idempotent. Re-ingesting the same corpus changes nothing.

        A prompt that arrives carrying an inline answer is stored COMPLETE, so
        it never enters the work set. That is requirement G, and on this corpus
        it is live on day one: 22 of the 2,200 prompts are already answered.
        """
        stats = {"inserted": 0, "already_present": 0, "imported_answers": 0}
        now = utc_now()

        with self._tx() as con:
            con.execute(
                "INSERT OR IGNORE INTO corpus VALUES (?,?,?,?)",
                (result.corpus_id, str(result.source_path), len(result.prompts), now),
            )

            for p in result.prompts:
                existing = con.execute(
                    "SELECT 1 FROM prompt WHERE prompt_id=?", (p.prompt_id,)
                ).fetchone()
                if existing:
                    stats["already_present"] += 1
                    continue

                art = self.vault.put(
                    p.question, kind="prompt", prompt_id=p.prompt_id, source=source
                )
                con.execute(
                    "INSERT INTO prompt VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        p.prompt_id, result.corpus_id, p.external_id, p.ordinal,
                        p.family, p.question, art.digest, conversation_mode.value,
                        priority, None, None, now,
                    ),
                )

                if p.inline_answer:
                    self._import_answer(con, p, source, now)
                    state = JobState.COMPLETE
                    stats["imported_answers"] += 1
                else:
                    state = JobState.PENDING

                con.execute(
                    "INSERT INTO job (prompt_id, state, updated_at) VALUES (?,?,?)",
                    (p.prompt_id, state.value, now),
                )
                con.execute(
                    "INSERT INTO event (prompt_id, from_state, to_state, reason, "
                    "actor, at) VALUES (?,?,?,?,?,?)",
                    (p.prompt_id, None, state.value, "ingest", source, now),
                )
                stats["inserted"] += 1

        return stats

    def _import_answer(self, con, parsed, source: str, now: str) -> None:
        art = self.vault.put(
            parsed.inline_answer,
            kind="response",
            prompt_id=parsed.prompt_id,
            source=source,
            source_version="inline-import",
            extra={"external_id": parsed.external_id, "origin": "already-in-source-document"},
        )
        row_id = response_row_id(parsed.prompt_id, art.digest)
        con.execute(
            "INSERT OR IGNORE INTO response VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                row_id, parsed.prompt_id, art.digest, len(parsed.inline_answer),
                source, "inline-import", EXTRACTOR_VERSION,
                IntegrityVerdict.UNVERIFIED.value,
                "imported from source document; not captured by this system",
                now,
            ),
        )
        con.execute(
            "INSERT INTO kacq_response_fts (response_id, prompt_id, body) VALUES (?,?,?)",
            (row_id, parsed.prompt_id, parsed.inline_answer),
        )

    # -- state machine ------------------------------------------------------

    def _current_state(self, con, prompt_id: str) -> JobState:
        row = con.execute("SELECT state FROM job WHERE prompt_id=?", (prompt_id,)).fetchone()
        if row is None:
            raise StoreError(f"no job for prompt {prompt_id}")
        return JobState(row["state"])

    def transition(
        self,
        prompt_id: str,
        target: JobState,
        *,
        reason: str = "",
        actor: str = "",
        error_class: str | None = None,
        error: str | None = None,
    ) -> None:
        """Enforced transition. Illegal moves raise; they are never ignored."""
        with self._tx() as con:
            current = self._current_state(con, prompt_id)
            assert_transition(current, target)  # raises IllegalTransition
            now = utc_now()
            con.execute(
                "UPDATE job SET state=?, last_error_class=?, last_error=?, "
                "lease_owner=NULL, lease_expires_at=NULL, updated_at=? "
                "WHERE prompt_id=?",
                (target.value, error_class, error, now, prompt_id),
            )
            con.execute(
                "INSERT INTO event (prompt_id, from_state, to_state, reason, actor, at) "
                "VALUES (?,?,?,?,?,?)",
                (prompt_id, current.value, target.value, reason, actor, now),
            )

    def claim_next(
        self,
        worker: str,
        *,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
        corpus_id: str | None = None,
        family: str | None = None,
        max_attempts: int = 3,
    ) -> ClaimedJob | None:
        """Atomically take the highest-priority PENDING job. None when drained.

        Claim and state change happen in one transaction, so two workers can
        never hold the same prompt.
        """
        where = ["j.state = 'PENDING'", "j.attempt_count < ?"]
        params: list = [max_attempts]
        if corpus_id:
            where.append("p.corpus_id = ?")
            params.append(corpus_id)
        if family:
            where.append("p.family = ?")
            params.append(family)

        sql = (
            "SELECT p.prompt_id, p.external_id, p.corpus_id, p.family, p.ordinal, "
            "       p.raw_prompt, p.conversation_mode, j.attempt_count "
            "FROM job j JOIN prompt p ON p.prompt_id = j.prompt_id "
            f"WHERE {' AND '.join(where)} "
            "ORDER BY p.priority ASC, p.ordinal ASC LIMIT 1"
        )

        with self._tx() as con:
            row = con.execute(sql, params).fetchone()
            if row is None:
                return None

            now = datetime.now(timezone.utc)
            expires = (now + timedelta(seconds=lease_seconds)).isoformat()
            con.execute(
                "UPDATE job SET state='RUNNING', attempt_count=attempt_count+1, "
                "lease_owner=?, lease_expires_at=?, updated_at=? WHERE prompt_id=?",
                (worker, expires, now.isoformat(), row["prompt_id"]),
            )
            con.execute(
                "INSERT INTO event (prompt_id, from_state, to_state, reason, actor, at) "
                "VALUES (?,?,?,?,?,?)",
                (row["prompt_id"], "PENDING", "RUNNING", "claimed", worker,
                 now.isoformat()),
            )
            return ClaimedJob(
                prompt_id=row["prompt_id"],
                external_id=row["external_id"],
                corpus_id=row["corpus_id"],
                family=row["family"],
                ordinal=row["ordinal"],
                raw_prompt=row["raw_prompt"],
                conversation_mode=row["conversation_mode"],
                attempt_count=row["attempt_count"] + 1,
            )

    def recover_expired_leases(self, *, actor: str = "recovery") -> int:
        """Return crashed jobs to PENDING. This is the whole resume story.

        A killed process leaves its job RUNNING with a lease that stops being
        renewed. Nothing needs to have run at shutdown for this to be correct.
        """
        now = utc_now()
        with self._tx() as con:
            rows = con.execute(
                "SELECT prompt_id FROM job WHERE state='RUNNING' "
                "AND lease_expires_at IS NOT NULL AND lease_expires_at < ?",
                (now,),
            ).fetchall()
            for r in rows:
                con.execute(
                    "UPDATE job SET state='PENDING', lease_owner=NULL, "
                    "lease_expires_at=NULL, updated_at=? WHERE prompt_id=?",
                    (now, r["prompt_id"]),
                )
                con.execute(
                    "INSERT INTO event (prompt_id, from_state, to_state, reason, "
                    "actor, at) VALUES (?,?,?,?,?,?)",
                    (r["prompt_id"], "RUNNING", "PENDING", "lease expired", actor, now),
                )
            return len(rows)

    def requeue_failed(
        self,
        *,
        max_attempts: int = 3,
        base_seconds: int = 30,
        cap_seconds: int = 3600,
        actor: str = "retry",
    ) -> int:
        """Move eligible FAILED jobs back to PENDING after a backoff interval.

        Without this, FAILED is a black hole: the state machine permits
        FAILED -> PENDING but nothing performs it, so `claim_next` (which
        selects only PENDING) never offers the job again and "bounded retry"
        is a declared capability that does not exist. Caught by
        test_claim_skips_jobs_past_max_attempts.

        Backoff is deterministic exponential (no jitter). Jitter matters when
        many clients stampede a shared service; here execution is deliberately
        sequential, so determinism is worth more than decorrelation.
        """
        now_dt = datetime.now(timezone.utc)
        moved = 0
        with self._tx() as con:
            rows = con.execute(
                "SELECT prompt_id, attempt_count, updated_at FROM job "
                "WHERE state='FAILED' AND attempt_count < ?",
                (max_attempts,),
            ).fetchall()
            for r in rows:
                wait = min(cap_seconds, base_seconds * (2 ** max(0, r["attempt_count"] - 1)))
                try:
                    failed_at = datetime.fromisoformat(r["updated_at"])
                except ValueError:
                    failed_at = now_dt
                if (now_dt - failed_at).total_seconds() < wait:
                    continue

                now = now_dt.isoformat()
                con.execute(
                    "UPDATE job SET state='PENDING', updated_at=? WHERE prompt_id=?",
                    (now, r["prompt_id"]),
                )
                con.execute(
                    "INSERT INTO event (prompt_id, from_state, to_state, reason, "
                    "actor, at) VALUES (?,?,?,?,?,?)",
                    (r["prompt_id"], "FAILED", "PENDING",
                     f"retry after {wait}s backoff (attempt {r['attempt_count']})",
                     actor, now),
                )
                moved += 1
        return moved

    # -- responses ----------------------------------------------------------

    def record_response(
        self,
        prompt_id: str,
        raw_response: str,
        *,
        source: str,
        source_version: str,
        verdict: IntegrityVerdict,
        reason: str = "",
    ) -> str:
        """Persist raw FIRST, then the row. Ordering is the durability contract.

        If the process dies between the two, the answer is still on disk and
        the job's expired lease returns it to PENDING; the re-run's put() is a
        no-op that finds the identical digest already present. An answer is
        never lost, and never stored twice.
        """
        art = self.vault.put(
            raw_response,
            kind="response",
            prompt_id=prompt_id,
            source=source,
            source_version=source_version,
        )
        now = utc_now()
        row_id = response_row_id(prompt_id, art.digest)
        with self._tx() as con:
            con.execute(
                "INSERT OR IGNORE INTO response VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    row_id, prompt_id, art.digest, len(raw_response), source,
                    source_version, EXTRACTOR_VERSION, verdict.value, reason, now,
                ),
            )
            con.execute(
                "INSERT INTO kacq_response_fts (response_id, prompt_id, body) "
                "VALUES (?,?,?)",
                (row_id, prompt_id, raw_response),
            )
        return row_id

    def responses_for(self, prompt_id: str) -> list[sqlite3.Row]:
        return self.con.execute(
            "SELECT * FROM response WHERE prompt_id=? ORDER BY captured_at",
            (prompt_id,),
        ).fetchall()

    # -- assessment (SPEC-KACQ-005) ------------------------------------------
    #
    # Derived, versioned, and strictly downstream of raw. Nothing here can
    # rewrite a captured answer, change a job state, or fail a capture: the
    # runner calls it after the response row is already durable, and guards the
    # call. An assessment that cannot be produced is an absent assessment, not
    # a lost answer.

    _ASSESSMENT_SCHEMA = """
    CREATE TABLE IF NOT EXISTS assessment (
        assessment_id      TEXT PRIMARY KEY,
        response_id        TEXT NOT NULL,
        prompt_id          TEXT NOT NULL,
        classifier_version TEXT NOT NULL,
        expected           TEXT NOT NULL,
        shape              TEXT NOT NULL,
        coverage           TEXT NOT NULL,
        epistemic          TEXT NOT NULL,
        epistemic_reason   TEXT NOT NULL DEFAULT '',
        disposition        TEXT NOT NULL,
        context_bound      INTEGER NOT NULL DEFAULT 0,
        context_markers    TEXT NOT NULL DEFAULT '[]',
        flags              TEXT NOT NULL DEFAULT '[]',
        followups          TEXT NOT NULL DEFAULT '[]',
        assessed_at        TEXT NOT NULL,
        UNIQUE (response_id, classifier_version)
    );

    CREATE TABLE IF NOT EXISTS source_boundary (
        interface           TEXT NOT NULL,
        boundary_id         TEXT NOT NULL,
        kind                TEXT NOT NULL,
        scope_text          TEXT NOT NULL,
        cohort_scoped       INTEGER NOT NULL DEFAULT 0,
        first_seen_prompt   TEXT NOT NULL,
        first_seen_at       TEXT NOT NULL,
        times_seen          INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY (interface, boundary_id)
    );

    CREATE INDEX IF NOT EXISTS ix_assess_disp   ON assessment(disposition);
    CREATE INDEX IF NOT EXISTS ix_assess_resp   ON assessment(response_id);
    CREATE INDEX IF NOT EXISTS ix_boundary_iface ON source_boundary(interface);
    """

    def _ensure_assessment_schema(self) -> None:
        if getattr(self, "_assess_ready", False):
            return
        self.con.executescript(self._ASSESSMENT_SCHEMA)
        self._assess_ready = True

    def record_assessment(self, assessment, *, interface: str = "eva") -> bool:
        """Persist one assessment and any boundaries it declared.

        Idempotent per (response_id, classifier_version): re-running the same
        classifier is a no-op, and running a NEW version adds a row beside the
        old one rather than overwriting it. A stored judgment is evidence of
        what this code believed at that version; silently replacing it would
        destroy the only record of a classifier regression.

        Returns True when a new assessment row was written.
        """
        self._ensure_assessment_schema()
        import hashlib

        basis = f"{assessment.response_id}|{assessment.classifier_version}"
        assessment_id = hashlib.sha256(basis.encode("utf-8")).hexdigest()
        now = utc_now()

        with self._tx() as con:
            cur = con.execute(
                "INSERT OR IGNORE INTO assessment VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    assessment_id, assessment.response_id, assessment.prompt_id,
                    assessment.classifier_version, assessment.expected.value,
                    assessment.shape.value, assessment.coverage,
                    assessment.epistemic, assessment.epistemic_reason,
                    assessment.disposition.value, int(assessment.context_bound),
                    json.dumps(list(assessment.context_markers), ensure_ascii=False),
                    json.dumps([{"code": f.code, "evidence": f.evidence}
                                for f in assessment.flags], ensure_ascii=False),
                    json.dumps(list(assessment.followups), ensure_ascii=False),
                    now,
                ),
            )
            written = cur.rowcount > 0

            for b in assessment.boundaries:
                con.execute(
                    "INSERT INTO source_boundary "
                    "(interface, boundary_id, kind, scope_text, cohort_scoped, "
                    " first_seen_prompt, first_seen_at, times_seen) "
                    "VALUES (?,?,?,?,?,?,?,1) "
                    "ON CONFLICT(interface, boundary_id) DO UPDATE SET "
                    "times_seen = times_seen + 1",
                    (interface, b.boundary_id, b.kind.value, b.scope_text,
                     int(b.cohort_scoped), assessment.prompt_id, now),
                )
        return written

    def known_boundaries(self, interface: str = "eva") -> list:
        """The interface's accumulated ledger, as boundary.BoundaryDeclaration.

        This is what makes the system learn in order: a cohort statistic seen
        before any boundary was declared is only worth a follow-up; the same
        statistic assessed after the source admits it cannot see the cohort is
        unsourced by the source's own admission.
        """
        self._ensure_assessment_schema()
        from .boundary import BoundaryDeclaration, BoundaryKind

        rows = self.con.execute(
            "SELECT kind, scope_text, cohort_scoped FROM source_boundary "
            "WHERE interface=? ORDER BY cohort_scoped DESC, first_seen_at",
            (interface,),
        ).fetchall()
        return [
            BoundaryDeclaration(
                kind=BoundaryKind(r["kind"]),
                marker="",
                scope_text=r["scope_text"],
                cohort_scoped=bool(r["cohort_scoped"]),
            )
            for r in rows
        ]

    def unassessed_responses(self, classifier_version: str) -> list[sqlite3.Row]:
        """Responses with no assessment at this classifier version."""
        self._ensure_assessment_schema()
        return self.con.execute(
            "SELECT r.response_id, r.prompt_id, r.raw_digest, r.source, "
            "       p.raw_prompt, p.family, p.external_id, p.ordinal "
            "FROM response r JOIN prompt p ON p.prompt_id = r.prompt_id "
            "WHERE NOT EXISTS (SELECT 1 FROM assessment a "
            "                  WHERE a.response_id = r.response_id "
            "                    AND a.classifier_version = ?) "
            "ORDER BY p.ordinal",
            (classifier_version,),
        ).fetchall()

    def assessment_stats(self, interface: str = "eva") -> dict:
        """Distribution an operator can act on, not a dashboard."""
        self._ensure_assessment_schema()

        def group(sql: str) -> dict:
            return {r[0]: r[1] for r in self.con.execute(sql)}

        return {
            "assessed": self.con.execute(
                "SELECT COUNT(*) FROM assessment").fetchone()[0],
            "by_disposition": group(
                "SELECT disposition, COUNT(*) FROM assessment GROUP BY disposition"),
            "by_epistemic": group(
                "SELECT epistemic, COUNT(*) FROM assessment GROUP BY epistemic"),
            "by_expected": group(
                "SELECT expected, COUNT(*) FROM assessment GROUP BY expected"),
            "context_bound": self.con.execute(
                "SELECT COUNT(*) FROM assessment WHERE context_bound=1").fetchone()[0],
            "boundaries": [
                dict(r) for r in self.con.execute(
                    "SELECT kind, cohort_scoped, times_seen, scope_text "
                    "FROM source_boundary WHERE interface=? "
                    "ORDER BY times_seen DESC", (interface,))
            ],
        }

    # -- observability ------------------------------------------------------

    def stats(self) -> dict:
        by_state = {
            r["state"]: r["n"]
            for r in self.con.execute("SELECT state, COUNT(*) n FROM job GROUP BY state")
        }
        totals = self.con.execute(
            "SELECT (SELECT COUNT(*) FROM prompt) prompts, "
            "       (SELECT COUNT(*) FROM response) responses, "
            "       (SELECT COUNT(*) FROM event) events"
        ).fetchone()
        return {
            "prompts": totals["prompts"],
            "responses": totals["responses"],
            "events": totals["events"],
            "by_state": {s.value: by_state.get(s.value, 0) for s in JobState},
            "by_corpus": {
                r["corpus_id"]: r["n"]
                for r in self.con.execute(
                    "SELECT corpus_id, COUNT(*) n FROM prompt GROUP BY corpus_id"
                )
            },
        }

    def search_prompts(self, query: str, limit: int = 20) -> list[sqlite3.Row]:
        return self.con.execute(
            "SELECT p.prompt_id, p.external_id, p.family, p.raw_prompt, j.state "
            "FROM kacq_prompt_fts f "
            "JOIN prompt p ON p.prompt_id = f.prompt_id "
            "JOIN job j ON j.prompt_id = p.prompt_id "
            "WHERE kacq_prompt_fts MATCH ? ORDER BY rank LIMIT ?",
            (query, limit),
        ).fetchall()

    def history(self, prompt_id: str) -> list[sqlite3.Row]:
        return self.con.execute(
            "SELECT * FROM event WHERE prompt_id=? ORDER BY event_id", (prompt_id,)
        ).fetchall()


__all__ = ["Store", "StoreError", "ClaimedJob", "IllegalTransition", "DEFAULT_LEASE_SECONDS"]
