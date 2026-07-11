"""accountability.py -- Decision Accountability & Attribution (SDD-OS Parte VI).

Closes the loop DRK-01 opened: after a decision's outcome is known, its
predictions are scored against reality and the outcome is attributed to four
sources -- reasoning, execution, luck, context -- so a lucky bad decision is not
counted as a win (the two-ledger principle).

- score_predictions: compare predicted observables vs realized signals; each
  prediction is hit / miss / unobservable (never fabricated).
- attribute: decompose an outcome into reasoning / execution / luck / context,
  using the Decision Object's accepted_risks (luck isolation), an execution
  signal (was it built as decided), and a context signal (did the world shift).
- calibrate: over a population of records, whether confidence matched realized
  reasoning accuracy, and the three DRK-07 biases as verdict-distribution drifts.

Consumes DecisionRecord (decision_record.py); in a live wiring the realized
signals come from modules/liveness and the scheduled re-checks from fd_04_prover
(cross-ref, not re-narrated here). Feeds CO-12 as one producer, never a parallel
accountant. Fail-open: never raises; unmeasurable inputs are reported honestly.
"""
from __future__ import annotations

from .decision_record import DecisionRecord, Verdict


def score_predictions(record: DecisionRecord,
                      realized: dict[str, object]) -> dict:
    """Score each predicted consequence against realized signals.

    `realized` maps observable -> realized value (or absence). A prediction with
    no observable is 'unobservable' (a reasoning defect, never a pass). Realized
    values are read, never invented (invariant VI.7.3).
    """
    results = []
    hits = misses = unobservable = 0
    for pred in record.obj.predicted_consequences:
        if not isinstance(pred, dict):
            unobservable += 1
            results.append({"claim": str(pred), "status": "unobservable",
                            "reason": "prediction is not a structured record"})
            continue
        observable = pred.get("observable")
        claim = pred.get("claim", "")
        if not observable:
            unobservable += 1
            results.append({"claim": claim, "status": "unobservable",
                            "reason": "no observable named"})
            continue
        if observable not in realized:
            unobservable += 1
            results.append({"claim": claim, "observable": observable,
                            "status": "unobservable",
                            "reason": "observable not measurable at horizon"})
            continue
        expected = pred.get("expected")
        actual = realized.get(observable)
        ok = (expected == actual) if expected is not None else bool(actual)
        if ok:
            hits += 1
            results.append({"claim": claim, "observable": observable,
                            "status": "hit", "realized": actual})
        else:
            misses += 1
            results.append({"claim": claim, "observable": observable,
                            "status": "miss", "expected": expected,
                            "realized": actual})
    total_scorable = hits + misses
    error = (misses / total_scorable) if total_scorable else None
    summary = {
        "hits": hits, "misses": misses, "unobservable": unobservable,
        "scorable": total_scorable, "error": error, "per_prediction": results,
    }
    record.realized_consequences = [{"observable": k, "value": v}
                                    for k, v in realized.items()]
    record.prediction_error = summary
    return summary


def attribute(record: DecisionRecord, *, execution_ok: bool = True,
              context_changed: bool = False,
              failed_risk_was_accepted: bool | None = None) -> dict:
    """Decompose the outcome into four sources (Parte VI VI.4-VI.5).

    - execution_ok=False  -> outcome attributed (partly) to execution, not reasoning.
    - context_changed=True -> attributed to context (a fact went false, not the
      reasoning's fault).
    - failed_risk_was_accepted=True -> a PRICED risk landed badly = luck (variance),
      not a reasoning defect. If a failure matches no accepted risk, it is a
      reasoning defect (attribution laundering guard, VI.8).
    The reasoning residual is what remains after the other three are removed.
    """
    err = (record.prediction_error or {}).get("error")
    outcome_bad = bool(err and err > 0.0)

    sources = {"reasoning": 0.0, "execution": 0.0, "luck": 0.0, "context": 0.0}
    if not outcome_bad:
        # Good outcome: still separate -- do not credit reasoning for luck.
        sources["reasoning"] = 1.0 if execution_ok and not context_changed else 0.6
        if not execution_ok:
            sources["execution"] = 0.4
        record.attribution = _finalize_attr(sources, outcome_bad=False,
                                             note="good outcome; ledgers separated")
        return record.attribution

    # Bad outcome: assign to the non-reasoning sources first, residual = reasoning.
    residual = 1.0
    if not execution_ok:
        sources["execution"] = 0.5
        residual -= 0.5
    if context_changed:
        sources["context"] = min(residual, 0.4)
        residual -= sources["context"]
    if failed_risk_was_accepted:
        sources["luck"] = min(residual, 0.4)
        residual -= sources["luck"]
    elif failed_risk_was_accepted is False:
        # failure matched no accepted risk -> reasoning defect, no luck laundering.
        pass
    sources["reasoning"] = max(0.0, residual)
    note = ("reasoning residual is the calibration update; "
            "downstream failures do not contaminate it")
    record.attribution = _finalize_attr(sources, outcome_bad=True, note=note)
    return record.attribution


def _finalize_attr(sources: dict, *, outcome_bad: bool, note: str) -> dict:
    return {
        "sources": sources,
        "dominant": max(sources, key=sources.get),
        "outcome_bad": outcome_bad,
        "reasoning_residual": sources["reasoning"],
        "note": note,
    }


def calibrate(records: list[DecisionRecord | dict]) -> dict:
    """Population-level calibration + the three DRK-07 biases.

    Biases are verdict-distribution DRIFTS (never asserted): never-reject
    (approval rate ~1.0), always-reject (reject/block rate high), always-platform
    (consolidate rate high, keep-local ~0). Reported only above a population
    threshold (telemetry-before-claims); below it, 'insufficient_data'.
    """
    verdicts: list[str] = []
    residuals: list[tuple[int, float]] = []  # (confidence, reasoning_residual)
    for r in records:
        d = r.to_dict() if isinstance(r, DecisionRecord) else r
        v = d.get("verdict")
        if v:
            verdicts.append(v)
        attr = d.get("attribution") or {}
        conf = (d.get("decision") or {}).get("confidence")
        if attr and conf is not None:
            residuals.append((conf, attr.get("reasoning_residual", 0.0)))

    n = len(verdicts)
    MIN_POP = 8  # below this, distribution is noise
    if n < MIN_POP:
        return {"population": n, "status": "insufficient_data",
                "min_population": MIN_POP}

    def rate(*names) -> float:
        s = {x.value if isinstance(x, Verdict) else x for x in names}
        return sum(1 for v in verdicts if v in s) / n

    approve_rate = rate(Verdict.APPROVE, Verdict.APPROVE_WITH_CONDITIONS)
    reject_rate = rate(Verdict.REJECT)
    consolidate_rate = rate(Verdict.CONSOLIDATE)
    keep_local_rate = rate(Verdict.KEEP_LOCAL)
    blocked_rate = sum(1 for r in records
                       if (r.to_dict() if isinstance(r, DecisionRecord) else r
                           ).get("blocked")) / n if records else 0.0

    biases = []
    if approve_rate >= 0.98:
        biases.append("never-reject")
    if reject_rate + blocked_rate >= 0.5:
        biases.append("always-reject")
    if consolidate_rate >= 0.5 and keep_local_rate <= 0.02:
        biases.append("always-platform")

    return {
        "population": n,
        "status": "ok",
        "verdict_rates": {
            "approve": round(approve_rate, 3),
            "reject": round(reject_rate, 3),
            "consolidate": round(consolidate_rate, 3),
            "keep_local": round(keep_local_rate, 3),
            "blocked": round(blocked_rate, 3),
        },
        "biases_detected": biases,
        "calibration_samples": len(residuals),
    }
