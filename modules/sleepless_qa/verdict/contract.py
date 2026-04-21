"""
Contract verdict — HTTP status code + JSON schema assertion.

Used when the action script's `expectations` field specifies structural
assertions on HTTP responses (e.g., "GET /users must return 200 with
{items: array}").
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ..dumpers.base import ActionScript, EvidenceBundle
from .schema import Verdict, VerdictStatus

logger = logging.getLogger(__name__)


def evaluate(bundle: EvidenceBundle, action: ActionScript) -> Verdict | None:
    """
    Evaluate HTTP contracts declared in action.expectations.

    Returns None if no contracts are declared (skip this strategy).
    Returns a Verdict otherwise.
    """
    expectations = action.expectations or {}
    http_asserts = expectations.get("http") or []
    if not http_asserts:
        return None

    failures: list[str] = []
    for assertion in http_asserts:
        method = (assertion.get("method") or "GET").upper()
        path = assertion.get("path") or "/"
        expect_status = int(assertion.get("status", 200))
        expect_json_keys = assertion.get("json_contains") or []

        # Find matching response
        match = None
        for resp in bundle.http_responses:
            if resp.method == method and path in resp.url:
                match = resp
                break

        if match is None:
            failures.append(f"no response for {method} {path}")
            continue

        if match.status != expect_status:
            failures.append(
                f"{method} {path} expected {expect_status}, got {match.status}"
            )
            continue

        if expect_json_keys:
            try:
                parsed = json.loads(match.body_excerpt) if match.body_excerpt else {}
            except json.JSONDecodeError:
                failures.append(f"{method} {path} body not JSON")
                continue
            missing = [k for k in expect_json_keys if k not in parsed]
            if missing:
                failures.append(f"{method} {path} missing keys: {missing}")

    if failures:
        return Verdict(
            status=VerdictStatus.FAIL,
            confidence=0.99,
            reason="; ".join(failures),
            strategy="contract",
            evidence_refs=[f"http:{i}" for i in range(len(bundle.http_responses))],
            priority_level=2,
        )

    return Verdict(
        status=VerdictStatus.PASS,
        confidence=0.95,
        reason=f"All {len(http_asserts)} HTTP contracts satisfied",
        strategy="contract",
        evidence_refs=[],
        priority_level=2,
    )
