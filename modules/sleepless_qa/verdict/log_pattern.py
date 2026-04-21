"""
Log-pattern verdict — regex matching against captured logs.

Anchors on log-level prefixes to avoid false positives on user-facing "error"
strings in UI copy. Each runtime class has its own pattern set.

This strategy is cheap (no API call) so it runs FIRST. If it emits a
confident FAIL, the visual strategy is skipped.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from ..dumpers.base import EvidenceBundle
from .schema import Verdict, VerdictStatus

logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    name: str
    regex: re.Pattern[str]
    priority_level: int  # 1=stability, 2=functionality
    fail_reason_template: str


# Crash / stability patterns (priority level 1)
STABILITY_PATTERNS = [
    Pattern(
        name="wii_isi",
        regex=re.compile(r"ISI\s+exception|Unhandled\s+exception|DSI\s+exception", re.IGNORECASE),
        priority_level=1,
        fail_reason_template="Wii CPU exception detected: {match}",
    ),
    Pattern(
        name="python_traceback",
        regex=re.compile(r"^Traceback \(most recent call last\):", re.MULTILINE),
        priority_level=1,
        fail_reason_template="Python traceback in daemon output",
    ),
    Pattern(
        name="python_unhandled",
        regex=re.compile(r"^\s*(\w+Error): (.+)$", re.MULTILINE),
        priority_level=1,
        fail_reason_template="Unhandled Python exception: {match}",
    ),
    Pattern(
        name="jvm_severe",
        regex=re.compile(r"\[.*?/SEVERE\]|\[ERROR\]\s+\[.*?\].*?Exception", re.IGNORECASE),
        priority_level=1,
        fail_reason_template="JVM SEVERE/ERROR: {match}",
    ),
    Pattern(
        name="segfault",
        regex=re.compile(r"Segmentation fault|SIGSEGV|core dumped", re.IGNORECASE),
        priority_level=1,
        fail_reason_template="Process segfault detected",
    ),
]

# Functional failure patterns (priority level 2)
FUNCTIONAL_PATTERNS = [
    Pattern(
        name="http_5xx",
        regex=re.compile(r'"(?:status|code)"\s*:\s*5\d\d|HTTP/\d\.\d 5\d\d'),
        priority_level=2,
        fail_reason_template="HTTP 5xx response: {match}",
    ),
    Pattern(
        name="console_error",
        regex=re.compile(r"^\[error\] ", re.MULTILINE),
        priority_level=2,
        fail_reason_template="Browser console error: {match}",
    ),
]

ALL_PATTERNS = STABILITY_PATTERNS + FUNCTIONAL_PATTERNS


def evaluate(bundle: EvidenceBundle) -> Verdict:
    """
    Scan all log excerpts for known failure patterns. Return earliest match
    at the highest priority (lowest level number).
    """
    corpus_parts: list[tuple[str, str]] = []
    for key, text in bundle.log_excerpts.items():
        if isinstance(text, str) and text:
            corpus_parts.append((key, text))
    if bundle.stdout:
        corpus_parts.append(("stdout", bundle.stdout))
    if bundle.stderr:
        corpus_parts.append(("stderr", bundle.stderr))

    # HTTP 5xx check directly on responses (structured, not log tail)
    for resp in bundle.http_responses:
        if 500 <= resp.status < 600:
            return Verdict(
                status=VerdictStatus.FAIL,
                confidence=0.99,
                reason=f"HTTP {resp.status} on {resp.method} {resp.url}",
                strategy="log_pattern",
                evidence_refs=[f"http:{resp.method}:{resp.url}"],
                priority_level=2,
            )

    # Sort patterns by priority level ascending (stability first)
    for pattern in sorted(ALL_PATTERNS, key=lambda p: p.priority_level):
        for source, text in corpus_parts:
            m = pattern.regex.search(text)
            if m:
                snippet = m.group(0)[:200]
                reason = pattern.fail_reason_template.format(match=snippet)
                logger.info("log_pattern matched %s in %s", pattern.name, source)
                return Verdict(
                    status=VerdictStatus.FAIL,
                    confidence=0.95,
                    reason=reason,
                    strategy="log_pattern",
                    evidence_refs=[f"{source}:{pattern.name}"],
                    priority_level=pattern.priority_level,
                )

    return Verdict(
        status=VerdictStatus.PASS,
        confidence=0.7,  # log scan alone is not high-confidence — needs visual or contract too
        reason="No failure patterns matched in logs",
        strategy="log_pattern",
        evidence_refs=[src for src, _ in corpus_parts],
        priority_level=2,
    )
