"""OD7 escalation ladder: 2 fails -> Opus once, 3 fails -> STOP."""
from __future__ import annotations

# OD7 thresholds (Owner-sealed 2026-06-01).
ESCALATE_TO_OPUS_AT = 2  # second consecutive failure -> escalate model once
STOP_AT = 3              # third failure -> stop, surface to Owner


def should_escalate(fail_count: int) -> bool:
    return ESCALATE_TO_OPUS_AT <= fail_count < STOP_AT


def should_stop(fail_count: int) -> bool:
    return fail_count >= STOP_AT


def recommend_action(fail_count: int) -> str:
    if fail_count <= 0:
        return "proceed"
    if fail_count < ESCALATE_TO_OPUS_AT:
        return "retry-same-model"
    if fail_count < STOP_AT:
        return "escalate-to-opus"
    return "stop-and-escalate-to-Owner"
