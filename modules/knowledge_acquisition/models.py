"""Core records, identity and the job state machine.

Identity rule: a prompt's id is derived from its *canonical text*, never from
its position in a file. Reordering the corpus, renumbering it, or re-exporting
it from the source tool must not change any id -- otherwise a resumed run
re-asks questions that were already answered.

State machine rule: illegal transitions are refused, never logged-and-ignored.
A job that silently slides from COMPLETE back to PENDING re-asks a paid
question and corrupts provenance.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

# Bump when the parser or canonicalizer changes in a way that alters ids or
# extracted text. Recorded on every derived artifact so any derivation is
# reproducible from raw.
EXTRACTOR_VERSION = "kacq-parser/1.0.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------
# Identity
# --------------------------------------------------------------------------

_WS_RX = re.compile(r"\s+")


def canonicalize(text: str) -> str:
    """Normalize prompt text so cosmetic edits do not change its identity.

    NFKC folds typographic variants (curly quotes, non-breaking spaces) that
    round-tripping through a chat UI or a word processor introduces.
    """
    return _WS_RX.sub(" ", unicodedata.normalize("NFKC", text)).strip()


def canonical_hash(text: str) -> str:
    return hashlib.sha256(canonicalize(text).encode("utf-8")).hexdigest()


def content_hash(raw: str) -> str:
    """Hash of an artifact exactly as captured -- no canonicalization.

    Raw artifacts are addressed by their true bytes; normalizing here would
    make two materially different responses collide.
    """
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# State machine
# --------------------------------------------------------------------------


class JobState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    NEEDS_HUMAN = "NEEDS_HUMAN"


#: COMPLETE is terminal by design: nothing may move a captured answer back
#: into the work set. Re-acquiring a prompt is an explicit, audited operation
#: that creates a new prompt row, not a state transition on the old one.
LEGAL_TRANSITIONS: dict[JobState, frozenset[JobState]] = {
    JobState.PENDING: frozenset({JobState.RUNNING}),
    JobState.RUNNING: frozenset(
        {JobState.COMPLETE, JobState.FAILED, JobState.NEEDS_HUMAN, JobState.PENDING}
    ),
    JobState.FAILED: frozenset({JobState.PENDING, JobState.NEEDS_HUMAN}),
    JobState.NEEDS_HUMAN: frozenset({JobState.PENDING}),
    JobState.COMPLETE: frozenset(),
}

TERMINAL_STATES = frozenset({JobState.COMPLETE})


class IllegalTransition(Exception):
    """Raised when a caller attempts a transition the machine forbids."""


def assert_transition(current: JobState, target: JobState) -> None:
    allowed = LEGAL_TRANSITIONS[current]
    if target not in allowed:
        allowed_txt = ", ".join(sorted(s.value for s in allowed)) or "<none: terminal>"
        raise IllegalTransition(
            f"{current.value} -> {target.value} is not a legal transition "
            f"(allowed from {current.value}: {allowed_txt})"
        )


class ConversationMode(str, Enum):
    """Why a prompt shares (or does not share) context with another.

    ISOLATED  -- clean conversation per prompt; maximum epistemic independence.
    SECTION   -- one conversation per thematic family; deliberate accumulation.
    FOLLOW_UP -- intentional continuation of a specific parent response.
    """

    ISOLATED = "ISOLATED"
    SECTION = "SECTION"
    FOLLOW_UP = "FOLLOW_UP"


class IntegrityVerdict(str, Enum):
    OK = "OK"
    EMPTY = "EMPTY"
    TRUNCATED = "TRUNCATED"
    STALE = "STALE"  # captured text belongs to a previous prompt
    UNVERIFIED = "UNVERIFIED"


# --------------------------------------------------------------------------
# Records
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class PromptRecord:
    """One question in the corpus. Immutable once ingested."""

    prompt_id: str  # canonical_hash(raw_prompt)
    corpus_id: str  # which source file
    external_id: str  # the id the source document uses, e.g. "SF30-001"
    ordinal: int  # 1-based position within its corpus
    family: str  # section header it lives under
    raw_prompt: str
    conversation_mode: ConversationMode = ConversationMode.ISOLATED
    priority: int = 100  # lower runs first
    parent_prompt_id: str | None = None
    frontier_origin: str | None = None  # set when generated, not authored
    created_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class ResponseRecord:
    """One captured answer. The raw text lives in the raw vault, not here."""

    response_id: str  # content_hash(raw_response)
    prompt_id: str
    raw_path: str  # path within the immutable raw vault
    char_count: int
    source: str  # adapter that produced it, e.g. "eva"
    source_version: str  # adapter version
    extractor_version: str
    integrity_verdict: IntegrityVerdict
    integrity_reason: str = ""
    captured_at: str = field(default_factory=utc_now)
