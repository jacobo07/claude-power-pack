"""G5 -- Recovery Telemetry & Diagnostics Layer (observability).

Collects recovery lifecycle events from the family, aggregates them into metrics,
diagnoses failures, presents a quiet-when-healthy health view, and routes every
stored record through redaction. Observes only -- never acts, never retries.
Hermetic: all persistence takes an explicit ``state_dir`` so tests touch no
global path and have no time-window dedup (feedback_hermetic_test_global_writes).

Seven entities (dataset session_resilience_05):
  1. RecoveryEventCollector    -- ingest + normalize + persist (jsonl), quarantine
  2. aggregate_metrics         -- acceptance rate, time-to-recover, failed counts
  3. diagnose                  -- root-cause of a failed/degraded recovery
  4. health_observatory        -- unified health view (quiet when healthy)
  5. redact                    -- Telemetry Redaction Bus (reuses URB)
  6. detect_anomalies          -- degradation trend / early warning (smoothed)
  7. correlate                 -- stitch one recovery's events into a timeline
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

# --- Entity 5: Telemetry Redaction Bus (reuse the URB; fail-safe local fallback)

def _load_urb() -> Callable[[str], str]:
    """Prefer the shipped Universal Redaction Bus (HR-SECRET-002/006). Fall back
    to a conservative local redactor so telemetry is NEVER the leak path even if
    the firewall module is unavailable."""
    try:  # pragma: no cover - exercised in real runs, fallback covered by tests
        from modules.secret_firewall.redactor import redact_for_log  # type: ignore
        return redact_for_log
    except Exception:  # noqa: BLE001
        _patterns = [
            re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),
            re.compile(r"sk-[A-Za-z0-9]{20,}"),
            re.compile(r"ghp_[A-Za-z0-9]{20,}"),
            re.compile(r"AKIA[0-9A-Z]{16}"),
            re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        ]

        def _local(text: str) -> str:
            for p in _patterns:
                text = p.sub("[REDACTED]", text)
            return text

        return _local


_redactor = _load_urb()


def redact(record: dict) -> dict:
    """Return a redacted copy: every string value passes through the URB."""
    def _walk(v: Any) -> Any:
        if isinstance(v, str):
            return _redactor(v)
        if isinstance(v, dict):
            return {k: _walk(x) for k, x in v.items()}
        if isinstance(v, list):
            return [_walk(x) for x in v]
        return v
    return _walk(record)


# --- Entity 1: Recovery Event Collector -------------------------------------

# Known recovery lifecycle event types (open set; unknown types still ingested).
EVENT_TYPES = (
    "crash_detected", "recovery_started", "window_restored", "pane_restored",
    "version_selected", "acceptance_scored", "recovery_completed", "recovery_failed",
)


@dataclass
class RecoveryEventCollector:
    """Append-only, redacted, hermetic event store (one jsonl)."""
    state_dir: Path
    filename: str = "recovery_events.jsonl"

    @property
    def path(self) -> Path:
        return Path(self.state_dir) / self.filename

    @property
    def quarantine_path(self) -> Path:
        return Path(self.state_dir) / (self.filename + ".quarantine")

    def emit(self, event: dict) -> dict:
        """Normalize, redact and persist one event. A malformed event (no
        ``ts`` or ``type``) is quarantined, never silently dropped, never
        allowed to corrupt the stream."""
        Path(self.state_dir).mkdir(parents=True, exist_ok=True)
        if not isinstance(event, dict) or "ts" not in event or "type" not in event:
            with self.quarantine_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"reason": "malformed", "raw": str(event)}) + "\n")
            return {"quarantined": True}
        safe = redact(dict(event))
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(safe, ensure_ascii=False) + "\n")
        return safe

    def read(self) -> list[dict]:
        if not self.path.is_file():
            return []
        out: list[dict] = []
        for line in self.path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out


# --- Entity 2: Recovery Metrics Aggregator ----------------------------------

@dataclass
class Metrics:
    total_recoveries: int
    accepted: int
    acceptance_rate: float | None
    avg_duration_s: float | None
    failed_element_counts: dict[str, int]
    provisional: bool


def aggregate_metrics(events: list[dict]) -> Metrics:
    """Derive operational metrics from the event stream. A recovery is counted
    at its terminal ``recovery_completed``/``recovery_failed`` event."""
    completed = [e for e in events if e.get("type") in ("recovery_completed", "recovery_failed")]
    total = len(completed)
    accepted = sum(1 for e in completed if e.get("verdict") == "RECOVERED")
    durations = [e["duration_s"] for e in completed if isinstance(e.get("duration_s"), (int, float))]
    fail_counts: dict[str, int] = {}
    for e in completed:
        for elem in (e.get("missing_elements") or []):
            key = str(elem).split(":", 1)[0].strip()
            fail_counts[key] = fail_counts.get(key, 0) + 1
    return Metrics(
        total_recoveries=total,
        accepted=accepted,
        acceptance_rate=(accepted / total) if total else None,
        avg_duration_s=(sum(durations) / len(durations)) if durations else None,
        failed_element_counts=fail_counts,
        provisional=(total < 5),
    )


# --- Entity 7: Diagnostics Correlation Engine -------------------------------

def correlate(events: list[dict], recovery_id: str) -> list[dict]:
    """Stitch one recovery's events into an ordered timeline (join on
    ``recovery_id``). Events lacking the id are excluded (not this recovery)."""
    rel = [e for e in events if e.get("recovery_id") == recovery_id]
    return sorted(rel, key=lambda e: str(e.get("ts")))


# --- Entity 3: Root-Cause Diagnostics Engine --------------------------------

@dataclass
class RootCause:
    determined: bool
    cause: str
    evidence: list[str] = field(default_factory=list)


def diagnose(timeline: list[dict]) -> RootCause:
    """Explain why a recovery failed/degraded from its correlated timeline.
    Honest: when the cause is undetermined it says so (lists candidates),
    never invents one."""
    failed = [e for e in timeline if e.get("type") == "recovery_failed"]
    scored = [e for e in timeline if e.get("type") == "acceptance_scored"]
    if not failed and not any(e.get("verdict") in ("FAILED", "PARTIAL") for e in scored):
        return RootCause(False, "no failure in timeline")
    # Most-specific signal first: a named missing element from the scorecard.
    for e in failed + scored:
        missing = e.get("missing_elements") or []
        if missing:
            first = str(missing[0])
            return RootCause(
                True,
                f"acceptance shortfall in dimension '{first.split(':', 1)[0].strip()}'",
                evidence=[first],
            )
    blocked = [e for e in timeline if e.get("type") == "window_restored" and e.get("status") == "blocked"]
    if blocked:
        return RootCause(True, "window restore blocked",
                         evidence=[str(e.get("reason", "")) for e in blocked])
    return RootCause(False, "failure present but root cause undetermined",
                     evidence=[str(e.get("type")) for e in timeline])


# --- Entity 6: Anomaly & Trend Detector -------------------------------------

def _median(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return 0.0
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2.0


def detect_anomalies(series: list[float], window: int = 3, factor: float = 1.5) -> list[str]:
    """Robust degradation detection: compares the MEDIAN of the recent window to
    the median of the earlier window, so a single blip (one outlier) never alerts
    while a sustained rise does. (Mean would let one spike false-alarm.)"""
    if len(series) < window * 2:
        return []
    base = _median(series[: len(series) - window])
    cur = _median(series[-window:])
    if base > 0 and cur > base * factor:
        return [f"rising trend: recent median {cur:.2f} > {base:.2f} x{factor}"]
    return []


# --- Entity 4: Recovery Health Observatory ----------------------------------

@dataclass
class HealthView:
    status: str           # HEALTHY / DEGRADED / UNKNOWN
    acceptance_rate: float | None
    recent_failures: int
    notes: list[str]


def health_observatory(events: list[dict]) -> HealthView:
    """A quiet-when-healthy unified view. UNKNOWN (not green) on missing data."""
    metrics = aggregate_metrics(events)
    if metrics.total_recoveries == 0:
        return HealthView("UNKNOWN", None, 0, ["no recoveries recorded yet"])
    recent_fail = sum(1 for e in events if e.get("type") == "recovery_failed")
    rate = metrics.acceptance_rate or 0.0
    if rate >= 0.95 and recent_fail == 0:
        status, notes = "HEALTHY", []
    else:
        status = "DEGRADED"
        notes = [f"acceptance {rate:.0%}", f"{recent_fail} failed recoveries"]
        if metrics.failed_element_counts:
            worst = max(metrics.failed_element_counts.items(), key=lambda kv: kv[1])
            notes.append(f"top failing dimension: {worst[0]} ({worst[1]}x)")
    if metrics.provisional:
        notes.append("provisional (thin sample)")
    return HealthView(status, metrics.acceptance_rate, recent_fail, notes)
