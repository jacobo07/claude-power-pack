"""Durable external knowledge acquisition.

Asks a large prompt corpus of an authenticated third-party knowledge interface
over many hours, surviving crashes, reboots and session expiry, without ever
losing a captured answer or re-asking an answered question.

Spec: SPEC.md (SPEC-KACQ-001).

Composition, not reimplementation. This module owns only the four primitives
the estate lacked -- prompt registry, durable job ledger, authenticated
browser session, immutable raw vault -- and delegates extraction, confidence,
contradiction detection, redaction, throttling and promotion to the modules
that already own them.
"""

from .models import (
    EXTRACTOR_VERSION,
    ConversationMode,
    IllegalTransition,
    IntegrityVerdict,
    JobState,
    PromptRecord,
    ResponseRecord,
    assert_transition,
    canonical_hash,
    content_hash,
)

__all__ = [
    "EXTRACTOR_VERSION",
    "ConversationMode",
    "IllegalTransition",
    "IntegrityVerdict",
    "JobState",
    "PromptRecord",
    "ResponseRecord",
    "assert_transition",
    "canonical_hash",
    "content_hash",
]
