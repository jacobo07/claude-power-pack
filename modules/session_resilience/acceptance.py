"""G4 -- Recovery Acceptance Framework (the arbiter).

Decides, at the level of the WHOLE session, whether a recovery is accepted:
the restored (observed) state is scored against the reference state it was meant
to reproduce. No recovery is "complete" unless the gate says RECOVERED. Pure
logic over canonical state descriptions (models.py) -> deterministic + fully
unit-testable; never touches a live editor or process.

Seven entities (dataset session_resilience_04):
  1. AcceptanceCriteria        -- the canonical "what counts as recovered" rules
  2. score_recovery            -- per-dimension scorecard (Scorecard Engine)
  3. equivalence_verdict       -- "indistinguishable from a Reload Window?" oracle
  4. classify                  -- RECOVERED / PARTIAL / FAILED + missing elements
  5. acceptance_gate           -- blocks the "complete" claim; fails safe (hold)
  6. Benchmark                 -- baseline expectations (time, fidelity)
  7. regression_check          -- detects acceptance regressions across releases
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import models

# Verdicts
RECOVERED = "RECOVERED"
PARTIAL = "PARTIAL"
FAILED = "FAILED"
UNKNOWN = "UNKNOWN"


# --- Entity 1: Acceptance Criteria Registry ---------------------------------

@dataclass(frozen=True)
class AcceptanceCriteria:
    """Canonical, versioned rules for a recovered session. ``required`` is the
    set of dimensions that MUST match for RECOVERED; ``tolerant`` dimensions use
    approximate comparison (scroll). Capability-aware acceptance (Dataset 04 s.10)
    excludes host-unrestorable dimensions from the equivalence denominator."""

    criteria_version: int = 1
    required: frozenset[str] = field(
        default_factory=lambda: frozenset(models.DIMENSIONS)
    )
    tolerant: frozenset[str] = field(default_factory=lambda: frozenset({"scroll"}))
    scroll_tolerance: float = models.DEFAULT_SCROLL_TOLERANCE

    def dimensions(self) -> tuple[str, ...]:
        return tuple(d for d in models.DIMENSIONS if d in self.required)


DEFAULT_CRITERIA = AcceptanceCriteria()


# --- Entity 2: Recovery Scorecard Engine ------------------------------------

@dataclass
class DimensionResult:
    name: str
    matched: bool
    detail: str
    measurable: bool = True  # False -> scored UNKNOWN, never assumed passing


@dataclass
class Scorecard:
    dimensions: dict[str, DimensionResult]
    reference_hash: str
    observed_hash: str

    def mismatches(self) -> list[str]:
        return [n for n, r in self.dimensions.items() if r.measurable and not r.matched]

    def unmeasurable(self) -> list[str]:
        return [n for n, r in self.dimensions.items() if not r.measurable]


def _scroll_match(ref: dict[str, float], obs: dict[str, float], tol: float) -> tuple[bool, str]:
    if set(ref) != set(obs):
        missing = sorted(set(ref) - set(obs))
        extra = sorted(set(obs) - set(ref))
        return False, f"document set differs (missing={missing} extra={extra})"
    worst = 0.0
    worst_key = ""
    for k, v in ref.items():
        d = abs(v - obs[k])
        if d > worst:
            worst, worst_key = d, k
    if worst > tol:
        return False, f"scroll off by {worst:.3f} > tol {tol:.3f} at {worst_key}"
    return True, f"all scroll within tol {tol:.3f} (worst {worst:.3f})"


def score_recovery(
    reference: dict,
    observed: dict,
    criteria: AcceptanceCriteria = DEFAULT_CRITERIA,
) -> Scorecard:
    """Deterministically score ``observed`` against ``reference`` per dimension."""
    results: dict[str, DimensionResult] = {}
    for dim in criteria.dimensions():
        extractor = models.EXTRACTORS[dim]
        try:
            ref_val = extractor(reference)
            obs_val = extractor(observed)
        except Exception as exc:  # noqa: BLE001 -- a dim we cannot measure is UNKNOWN
            results[dim] = DimensionResult(dim, False, f"unmeasurable: {exc}", measurable=False)
            continue
        if dim in criteria.tolerant and dim == "scroll":
            ok, detail = _scroll_match(ref_val, obs_val, criteria.scroll_tolerance)
        else:
            ok = ref_val == obs_val
            detail = "match" if ok else f"expected {ref_val!r} != actual {obs_val!r}"
        results[dim] = DimensionResult(dim, ok, detail)
    return Scorecard(
        dimensions=results,
        reference_hash=models.state_hash(reference),
        observed_hash=models.state_hash(observed),
    )


# --- Entity 3: Equivalence Oracle -------------------------------------------

def equivalence_verdict(
    scorecard: Scorecard,
    criteria: AcceptanceCriteria = DEFAULT_CRITERIA,
    host_capabilities: frozenset[str] | None = None,
) -> str:
    """RECOVERED iff every required, host-RESTORABLE dimension matched.

    Capability-aware: if ``host_capabilities`` is given, a required dimension the
    host provably cannot restore is excluded from the denominator (reported, not
    failed). A dimension the host COULD restore but didn't remains a real miss."""
    if not scorecard.dimensions:
        return UNKNOWN
    for dim, res in scorecard.dimensions.items():
        if host_capabilities is not None and dim not in host_capabilities:
            continue  # host limitation, outside our control -> excluded
        if not res.measurable:
            return UNKNOWN  # cannot prove equivalence on an unmeasured dimension
        if not res.matched:
            return FAILED
    return RECOVERED


# --- Entity 4: Partial-Recovery Classifier ----------------------------------

def classify(
    scorecard: Scorecard,
    criteria: AcceptanceCriteria = DEFAULT_CRITERIA,
    host_capabilities: frozenset[str] | None = None,
) -> tuple[str, list[str]]:
    """Return (verdict, missing_elements). RECOVERED / PARTIAL / FAILED:
      * RECOVERED -- every required restorable dimension matched
      * PARTIAL   -- some matched, some missed (at least one of each)
      * FAILED    -- nothing matched, or an unmeasurable required dimension
    ``missing_elements`` enumerates every shortfall (no silent summing)."""
    relevant = {
        d: r for d, r in scorecard.dimensions.items()
        if host_capabilities is None or d in host_capabilities
    }
    if not relevant:
        return UNKNOWN, []
    if any(not r.measurable for r in relevant.values()):
        missing = [f"{d}: {r.detail}" for d, r in relevant.items()
                   if not r.measurable or not r.matched]
        return FAILED, missing
    matched = [d for d, r in relevant.items() if r.matched]
    missed = [d for d, r in relevant.items() if not r.matched]
    if not missed:
        return RECOVERED, []
    missing_elems = [f"{d}: {relevant[d].detail}" for d in missed]
    if matched:
        return PARTIAL, missing_elems
    return FAILED, missing_elems


# --- Entity 5: Acceptance Gate ----------------------------------------------

@dataclass
class GateDecision:
    allow_complete: bool
    verdict: str
    reason: str
    missing_elements: list[str] = field(default_factory=list)


def acceptance_gate(
    scorecard: Scorecard,
    criteria: AcceptanceCriteria = DEFAULT_CRITERIA,
    host_capabilities: frozenset[str] | None = None,
) -> GateDecision:
    """The completion gate. Only a RECOVERED verdict allows a "complete" claim;
    anything else HOLDS (fails safe) and surfaces the gaps."""
    verdict, missing = classify(scorecard, criteria, host_capabilities)
    if verdict == RECOVERED:
        return GateDecision(True, verdict, "all required dimensions recovered")
    if verdict == UNKNOWN:
        return GateDecision(False, verdict, "cannot evaluate acceptance -- held (fail-safe)")
    return GateDecision(
        False, verdict,
        f"{verdict.lower()} recovery -- completion held until accepted",
        missing_elements=missing,
    )


# --- Entity 6: Recovery Benchmark Engine ------------------------------------

@dataclass
class Benchmark:
    expected_seconds: float | None
    expected_fidelity: float | None  # 0..1 mean dimension match rate
    provisional: bool
    sample_size: int


def compute_benchmark(history: list[dict]) -> Benchmark:
    """Baseline expectations from prior accepted recoveries. Each history item:
    {"duration_s": float, "fidelity": float}. < 5 samples -> provisional."""
    durations = [h["duration_s"] for h in history if "duration_s" in h]
    fidelities = [h["fidelity"] for h in history if "fidelity" in h]
    n = len(history)
    exp_s = (sum(durations) / len(durations)) if durations else None
    exp_f = (sum(fidelities) / len(fidelities)) if fidelities else None
    return Benchmark(exp_s, exp_f, provisional=(n < 5), sample_size=n)


# --- Entity 7: Regression Sentinel ------------------------------------------

def regression_check(
    current: dict, benchmark: Benchmark, slack: float = 1.5
) -> list[str]:
    """Alerts when current recovery is materially worse than baseline.
    ``current``: {"duration_s", "fidelity"}. Provisional benchmarks alert softly
    (noted) so a thin baseline does not raise false alarms."""
    alerts: list[str] = []
    note = " (provisional baseline)" if benchmark.provisional else ""
    if benchmark.expected_seconds and current.get("duration_s") is not None:
        if current["duration_s"] > benchmark.expected_seconds * slack:
            alerts.append(
                f"recovery time {current['duration_s']:.1f}s exceeds "
                f"{benchmark.expected_seconds:.1f}s x{slack}{note}"
            )
    if benchmark.expected_fidelity is not None and current.get("fidelity") is not None:
        if current["fidelity"] < benchmark.expected_fidelity - 0.1:
            alerts.append(
                f"fidelity {current['fidelity']:.2f} below "
                f"{benchmark.expected_fidelity:.2f}-0.10{note}"
            )
    return alerts


def fidelity(scorecard: Scorecard) -> float:
    """Mean measurable-dimension match rate (0..1) -- feeds benchmarks/telemetry."""
    measurable = [r for r in scorecard.dimensions.values() if r.measurable]
    if not measurable:
        return 0.0
    return sum(1 for r in measurable if r.matched) / len(measurable)
