"""
OmniCapture — Universal Telemetry Schema (UTS) Validator.
Validates incoming telemetry events against the UTS specification.
"""

import uuid
import hashlib
import time
from typing import Any

VALID_SOURCE_TYPES = {"python", "minecraft", "wii_cpp", "react_native", "generic"}
VALID_CATEGORIES = {"error", "performance", "state_dump", "network", "crash", "custom"}
VALID_SEVERITIES = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "FATAL"}
VALID_ENVIRONMENTS = {"development", "staging", "production"}

# Required payload fields per category
CATEGORY_REQUIRED_FIELDS = {
    "error": ["error_type", "message"],
    "performance": ["metric_name", "value"],
    "state_dump": ["dump_type", "data"],
    "network": ["url", "method", "status_code"],
    "crash": ["signal", "exit_code"],
    "custom": [],
}


def validate_event(event: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a single UTS event. Returns (is_valid, list_of_errors)."""
    errors: list[str] = []

    # Required top-level fields
    for field in ("source_type", "category", "severity", "timestamp_iso", "payload"):
        if field not in event:
            errors.append(f"missing required field: {field}")

    if errors:
        return False, errors

    # Enum validation
    if event["source_type"] not in VALID_SOURCE_TYPES:
        errors.append(f"invalid source_type: {event['source_type']}")
    if event["category"] not in VALID_CATEGORIES:
        errors.append(f"invalid category: {event['category']}")
    if event["severity"] not in VALID_SEVERITIES:
        errors.append(f"invalid severity: {event['severity']}")
    if event.get("environment") and event["environment"] not in VALID_ENVIRONMENTS:
        errors.append(f"invalid environment: {event['environment']}")

    # Payload validation per category
    if isinstance(event.get("payload"), dict):
        category = event["category"]
        required = CATEGORY_REQUIRED_FIELDS.get(category, [])
        for field in required:
            if field not in event["payload"]:
                errors.append(f"payload missing required field for {category}: {field}")
    else:
        errors.append("payload must be a dict")

    return len(errors) == 0, errors


def enrich_event(event: dict[str, Any], project_id: str) -> dict[str, Any]:
    """Add server-side fields to a validated event."""
    event["event_id"] = event.get("event_id") or str(uuid.uuid4())
    event["project_id"] = project_id
    event["timestamp_epoch_ms"] = event.get("timestamp_epoch_ms") or int(time.time() * 1000)
    event.setdefault("environment", "development")
    event.setdefault("hostname", "unknown")
    event.setdefault("process_name", "unknown")

    # Compute fingerprint if missing
    if not event.get("fingerprint"):
        event["fingerprint"] = _compute_fingerprint(event)

    return event


def _compute_fingerprint(event: dict[str, Any]) -> str:
    """Generate dedup fingerprint based on category-specific fields."""
    payload = event.get("payload", {})
    category = event.get("category", "")

    if category == "error":
        raw = f"{payload.get('error_type', '')}|"
        stacktrace = payload.get("stacktrace", [])
        raw += "|".join(stacktrace[:3])
    elif category == "crash":
        raw = f"{payload.get('signal', '')}|{payload.get('exit_code', '')}"
    elif category == "performance":
        raw = f"{payload.get('metric_name', '')}|{str(payload.get('tags', {}))}"
    elif category == "network":
        raw = f"{payload.get('url', '')}|{payload.get('method', '')}|{payload.get('status_code', '')}"
    else:
        raw = f"{category}|{str(payload)[:200]}"

    return hashlib.sha256(raw.encode()).hexdigest()[:16]
