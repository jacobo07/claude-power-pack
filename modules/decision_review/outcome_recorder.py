#!/usr/bin/env python3
"""outcome_recorder.py -- the producer for the accountability half (UCEIMR G4).

`accountability.py` scores a decision's predictions against reality and splits
the outcome into reasoning / execution / luck / context. It has worked since it
shipped. Nothing ever called it with a real record.

Measured 2026-08-04: the registry holds 1 record; `realized_consequences`,
`prediction_error` and `attribution` are empty in 1 of 1. The decision carries
two structured predictions, each with a named observable and a horizon, so it
was always scorable -- there was simply no producer. Fields defined and consumed
with nothing writing them are dead by starvation
(`feedback_orphan_field_dead_recovery_path`).

This supplies the missing half:

  resolve_observables()  READ the named observable from the repo. A resolver it
                         does not have is left ABSENT, never guessed -- absence
                         makes score_predictions report `unobservable`, which is
                         the honest verdict (invariant VI.7.3: realized values
                         are read, never invented).
  due()                  which predictions have reached their horizon. Scoring
                         before the horizon manufactures a miss out of a result
                         that has not happened yet.
  record_outcome()       run the shipped scorer + attributor and APPEND a new
                         record carrying the accountability fields. The registry
                         is append-only (DRK-05): the outcome is a new line with
                         the same decision id, and `latest_by_id` resolves the
                         current view. Nothing is ever rewritten in place.

Determinism: `now` is supplied by the caller, never read from the clock, so a
replay is reproducible -- the same contract `decision_record` already keeps.

    python -m modules.decision_review.outcome_recorder            # report
    python -m modules.decision_review.outcome_recorder --write    # append

Stdlib only. Fail-open: never raises into a caller.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.decision_review.accountability import attribute, score_predictions
from modules.decision_review.decision_record import (
    DecisionObject, DecisionRecord, Registry, ReviewTier, Verdict)

PENDING = "PENDING_HORIZON"
RECORDED = "OUTCOME_RECORDED"
NOT_SCORABLE = "NO_RESOLVABLE_OBSERVABLE"
ALREADY = "ALREADY_RECORDED"

# Horizon vocabulary. An unrecognised horizon is None -> treated as NOT due,
# because assuming "due" would score a prediction whose deadline is unknown.
_HORIZON_DAYS = {
    "1d": 1, "1w": 7, "2w": 14, "1mo": 30, "6w": 42, "2mo": 60,
    "3mo": 90, "6mo": 180, "1y": 365,
}


def parse_horizon(h) -> int | None:
    if not h:
        return None
    key = str(h).strip().lower().replace(" ", "")
    if key in _HORIZON_DAYS:
        return _HORIZON_DAYS[key]
    m = re.fullmatch(r"(\d+)(d|w|mo|m|y)", key)
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2)
    return n * {"d": 1, "w": 7, "mo": 30, "m": 30, "y": 365}[unit]


def _parse_ts(ts: str):
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


# --- observable resolvers ------------------------------------------------
# Each entry is (signature, resolver). The signature must appear in the
# observable text for the resolver to claim it. Matching is deliberately
# narrow: a loose matcher that claimed the wrong observable would invent a
# realized value, which is the one thing this layer must never do.

def _count_proactive_findings(root: Path):
    """Rows at urgency MEDIUM or above across the proactive scan reports."""
    files = sorted((root / "vault" / "audits").glob("drk_proactive_*.md"))
    if not files:
        return None
    n = 0
    for f in files:
        try:
            text = f.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            if line.startswith("|") and re.match(
                    r"^\|\s*(MEDIUM|HIGH|CRITICAL)\b", line.strip(), re.I):
                n += 1
    return n


def _count_owner_queue_drk_rows(root: Path):
    """OWNER_QUEUE rows attributed to the proactive scanner."""
    candidates = [root / "vault" / "OWNER_QUEUE.md",
                  root / "OWNER_QUEUE.md"]
    for p in candidates:
        try:
            if not p.exists():
                continue
            text = p.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        return sum(1 for ln in text.splitlines()
                   if "drk-proactive" in ln.lower())
    return None


RESOLVERS = (
    ("drk_proactive_", _count_proactive_findings),
    ("owner_queue", _count_owner_queue_drk_rows),
)


def resolve_observables(record_dict: dict, root: Path | None = None) -> dict:
    """observable -> realized value, for the observables this repo can READ.

    An observable no resolver claims is ABSENT from the result. That absence is
    load-bearing: `score_predictions` then reports it `unobservable` instead of
    scoring a value nobody measured.
    """
    base = Path(root) if root is not None else _PP_ROOT
    out: dict = {}
    preds = (record_dict.get("decision") or {}).get("predicted_consequences") or []
    for pred in preds:
        if not isinstance(pred, dict):
            continue
        obs = pred.get("observable")
        if not obs:
            continue
        key = str(obs).lower().replace(" ", "_")
        for sig, fn in RESOLVERS:
            if sig in key:
                try:
                    val = fn(base)
                except Exception:  # noqa: BLE001 -- a resolver never breaks the run
                    val = None
                if val is not None:
                    out[obs] = val
                break
    return out


@dataclass
class OutcomeReport:
    decision_id: str
    status: str
    due: list = field(default_factory=list)
    pending: list = field(default_factory=list)
    resolved: dict = field(default_factory=dict)
    summary: dict | None = None
    attribution: dict | None = None
    written: bool = False
    reason: str = ""

    def render(self) -> str:
        head = f"  [{self.status:<22}] {self.decision_id}"
        bits = []
        if self.due or self.pending:
            bits.append(f"{len(self.due)} due / {len(self.pending)} pending")
        if self.summary:
            bits.append(f"hits={self.summary['hits']} misses={self.summary['misses']} "
                        f"unobservable={self.summary['unobservable']}")
        if self.attribution:
            bits.append(f"dominant={self.attribution['dominant']}")
        if self.reason:
            bits.append(self.reason)
        return head + ("  (" + "; ".join(bits) + ")" if bits else "")


def due(record_dict: dict, now: datetime) -> tuple:
    """(due, pending) predictions, split by whether the horizon has arrived."""
    ts = _parse_ts(record_dict.get("ts", ""))
    preds = (record_dict.get("decision") or {}).get("predicted_consequences") or []
    if ts is None:
        # No decision timestamp -> no horizon can be computed. Everything
        # pending: a prediction with an unknown deadline is not overdue.
        return [], [p for p in preds if isinstance(p, dict)]
    ready, waiting = [], []
    for p in preds:
        if not isinstance(p, dict):
            continue
        days = parse_horizon(p.get("horizon"))
        (ready if days is not None and now >= ts + timedelta(days=days)
         else waiting).append(p)
    return ready, waiting


def _rebuild(record_dict: dict) -> DecisionRecord:
    """A registry line back into the dataclass the shipped scorer consumes."""
    d = record_dict.get("decision") or {}
    obj = DecisionObject(
        id=d.get("id") or record_dict.get("id") or "",
        statement=d.get("statement", ""), problem=d.get("problem", ""),
        options=list(d.get("options") or []), chosen=d.get("chosen", ""),
        rationale=d.get("rationale", ""),
        accepted_risks=list(d.get("accepted_risks") or []),
        predicted_consequences=list(d.get("predicted_consequences") or []),
        confidence=d.get("confidence"),
    )
    def _enum(cls, v):
        try:
            return cls(v) if v else None
        except ValueError:
            return None
    return DecisionRecord(
        obj=obj, ts=record_dict.get("ts", ""),
        tier=_enum(ReviewTier, record_dict.get("tier")),
        verdict=_enum(Verdict, record_dict.get("verdict")),
        blocked=bool(record_dict.get("blocked")),
        cited_sources=list(record_dict.get("cited_sources") or []),
        guards_fired=list(record_dict.get("guards_fired") or []),
        conditions=list(record_dict.get("conditions") or []),
    )


def record_outcome(record_dict: dict, now: datetime, *,
                   registry: Registry | None = None, root: Path | None = None,
                   write: bool = False, execution_ok: bool = True,
                   context_changed: bool = False) -> OutcomeReport:
    """Score a decision whose horizon has arrived and append the outcome.

    Never scores a prediction before its horizon, never scores an observable it
    could not read, and never rewrites the original line -- the outcome is a new
    append carrying the same decision id.
    """
    did = record_dict.get("id") or ""
    ready, waiting = due(record_dict, now)
    if not ready:
        return OutcomeReport(did, PENDING, ready, waiting,
                             reason="no prediction has reached its horizon")

    resolved = resolve_observables(record_dict, root)
    rec = _rebuild(record_dict)
    # Only the due predictions are scored; a pending one must not be counted as
    # a miss for not having happened yet.
    rec.obj.predicted_consequences = ready
    summary = score_predictions(rec, resolved)
    if not summary["scorable"]:
        return OutcomeReport(did, NOT_SCORABLE, ready, waiting, resolved,
                             summary,
                             reason="every due observable is unreadable here")

    # A failure counts as luck only if it matches a risk the decision PRICED.
    # No accepted risks -> False, never None: None would let the attributor
    # skip the luck ledger entirely and quietly flatter the reasoning residual.
    failed_accepted = bool(rec.obj.accepted_risks) if summary["misses"] else None
    attr = attribute(rec, execution_ok=execution_ok,
                     context_changed=context_changed,
                     failed_risk_was_accepted=failed_accepted)
    rec.obj.predicted_consequences = (
        (record_dict.get("decision") or {}).get("predicted_consequences") or [])

    written = False
    if write:
        written = (registry or Registry()).append(rec)
    return OutcomeReport(did, RECORDED, ready, waiting, resolved, summary,
                         attr, written,
                         reason="" if written or not write else "append failed")


def latest_by_id(rows: list) -> dict:
    """The current view of an append-only registry: last line per decision id.

    Without this an outcome append reads as a second, contradictory decision.
    """
    out: dict = {}
    for r in rows:
        rid = r.get("id")
        if rid:
            out[rid] = r
    return out


def scan(now: datetime, *, registry: Registry | None = None,
         root: Path | None = None, write: bool = False) -> list:
    """Every decision in the registry, judged at `now`. Fail-open to []."""
    reg = registry or Registry()
    try:
        rows = reg.load()
    except Exception:  # noqa: BLE001
        return []
    reports = []
    for rid, row in latest_by_id(rows).items():
        if row.get("attribution"):
            reports.append(OutcomeReport(rid, ALREADY,
                                         reason="outcome already attributed"))
            continue
        try:
            reports.append(record_outcome(row, now, registry=reg, root=root,
                                          write=write))
        except Exception as e:  # noqa: BLE001
            reports.append(OutcomeReport(rid, NOT_SCORABLE,
                                         reason=f"{type(e).__name__}: {e}"))
    return reports


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Decision outcome producer (G4)")
    ap.add_argument("--write", action="store_true",
                    help="append the outcome record (default: report only)")
    ap.add_argument("--now", default="",
                    help="ISO instant to judge at (default: current UTC)")
    args = ap.parse_args(argv)

    now = _parse_ts(args.now) if args.now else datetime.now(timezone.utc)
    if now is None:
        print(f"REFUSED: --now {args.now!r} is not an ISO instant")
        return 1
    reports = scan(now, write=args.write)
    if not reports:
        print("no decision records to judge")
        return 0
    print(f"judging {len(reports)} decision(s) at {now.isoformat()}")
    for r in reports:
        print(r.render())
    counts = {s: sum(1 for r in reports if r.status == s)
              for s in (RECORDED, PENDING, NOT_SCORABLE, ALREADY)}
    print("DECISION_OUTCOMES " + "  ".join(f"{k}={v}" for k, v in counts.items()))
    return 0


__all__ = [
    "PENDING", "RECORDED", "NOT_SCORABLE", "ALREADY", "OutcomeReport",
    "parse_horizon", "resolve_observables", "due", "record_outcome",
    "latest_by_id", "scan", "main",
]

if __name__ == "__main__":
    raise SystemExit(main())
