"""Weighted context-pressure meter, token budget and the mission epoch reading.

Derived from vendor/context-budget/lib/context-budget.cjs (MIT, Context Budget contributors):
the two-segment ``normalize`` and the weighted blend are the upstream algorithm (parity is
checked through the Node bridge in tools/test_context_budget.py). Unknown-value semantics differ
on purpose -- see the package docstring.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

MEASURED, PARTIAL, UNMEASURED = "MEASURED", "PARTIAL", "UNMEASURED"
# Upstream DEFAULT_MODES: compressed at 0.4, emergency at 0.7.
BANDS = {"comfortable": 0.0, "stressed": 0.4, "critical": 0.7}
# Below this share of measured weight the blended number is not reported as a pressure at all.
MIN_COVERAGE = 0.5


def normalize(value: float, comfortable: float = 0.0, stressed: float = 1.0, critical: float = 2.0) -> float:
    """Upstream two-segment map: <=comfortable 0, ..stressed 0..0.5, ..critical 0.5..1, beyond 1."""
    v = float(value)
    if not math.isfinite(v) or v <= comfortable:
        return 0.0
    if v >= critical:
        return 1.0
    if v <= stressed:
        span = stressed - comfortable
        return 0.5 * ((v - comfortable) / span) if span > 0 else 0.5
    span = critical - stressed
    return 0.5 + 0.5 * ((v - stressed) / span) if span > 0 else 0.5


@dataclass
class Signal:
    name: str
    read: Callable[[], float | None] | float | None
    comfortable: float = 0.0
    stressed: float = 1.0
    critical: float = 2.0
    weight: float = 1.0

    def value(self) -> tuple[float | None, str]:
        try:
            raw = self.read() if callable(self.read) else self.read
        except Exception as exc:  # noqa: BLE001 -- recorded as UNMEASURED with the reason, never as 0
            return None, f"probe raised {exc.__class__.__name__}"
        if raw is None:
            return None, "no value"
        try:
            v = float(raw)
        except (TypeError, ValueError):
            return None, f"not a number: {raw!r}"
        if not math.isfinite(v):
            return None, "not finite"
        return v, ""


class Meter:
    def __init__(self, signals: list[Signal] | None = None, bands: dict | None = None,
                 min_coverage: float = MIN_COVERAGE):
        self.signals: list[Signal] = list(signals or [])
        self.bands = {**BANDS, **(bands or {})}
        self.min_coverage = min_coverage

    def add(self, sig: Signal) -> "Meter":
        self.signals.append(sig)
        return self

    def reading(self) -> dict:
        total_w = sum(max(0.0, s.weight) for s in self.signals)
        rows, measured_w, blended = [], 0.0, 0.0
        for s in self.signals:
            v, why = s.value()
            row = {"name": s.name, "weight": s.weight}
            if v is None:
                row.update(state=UNMEASURED, reason=why)
            else:
                n = normalize(v, s.comfortable, s.stressed, s.critical)
                row.update(state=MEASURED, value=v, normalized=round(n, 4))
                measured_w += max(0.0, s.weight)
                blended += n * max(0.0, s.weight)
            rows.append(row)
        coverage = (measured_w / total_w) if total_w > 0 else 0.0
        if measured_w <= 0 or coverage < self.min_coverage:
            return {"state": UNMEASURED, "pressure": None, "band": None, "coverage": round(coverage, 4),
                    "signals": rows}
        pressure = round(blended / measured_w, 4)
        band = "critical" if pressure >= self.bands["critical"] else (
            "stressed" if pressure >= self.bands["stressed"] else "comfortable")
        return {"state": MEASURED if coverage >= 0.999 else PARTIAL, "pressure": pressure, "band": band,
                "coverage": round(coverage, 4), "signals": rows}


def estimate_tokens(text: str | None) -> int:
    """Upstream tokenizer-free estimate (ceil(chars/4)). An ESTIMATE: label it so where reported."""
    s = "" if text is None else str(text)
    return math.ceil(len(s) / 4) if s else 0


class Budget:
    def __init__(self, total: int):
        self.total = max(0, int(total or 0))
        self.spent = 0

    def spend(self, amount_or_text) -> float:
        n = estimate_tokens(amount_or_text) if isinstance(amount_or_text, str) else max(0, int(amount_or_text or 0))
        self.spent += n
        return self.remaining()

    def remaining(self) -> float:
        return max(0, self.total - self.spent) if self.total else math.inf

    def over(self) -> bool:
        return bool(self.total) and self.spent > self.total


def epoch_reading(*, context_tokens: int | None, ceiling: int, transcript_bytes: int | None = None,
                  session_age_s: float | None = None, pending_children: int | None = None) -> dict:
    """The reading a mission epoch decision records as evidence. Signals and thresholds:
    - context_tokens vs the continuation ceiling (weight 3; the only direct measure)
    - transcript bytes (weight 1; growth proxy, 2/5/10 MB)
    - session age (weight 1; 1/3/6 h)
    - pending background children (weight 1; 0/2/4): work that must survive a boundary
    """
    m = Meter([
        Signal("context_tokens", context_tokens, comfortable=0.5 * ceiling, stressed=0.8 * ceiling,
               critical=float(ceiling), weight=3.0),
        Signal("transcript_bytes", transcript_bytes, comfortable=2e6, stressed=5e6, critical=1e7),
        Signal("session_age_s", session_age_s, comfortable=3600, stressed=3 * 3600, critical=6 * 3600),
        Signal("pending_children", pending_children, comfortable=0, stressed=2, critical=4),
    ])
    r = m.reading()
    r["estimator"] = "context-budget/native-1"
    return r
