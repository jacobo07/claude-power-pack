#!/usr/bin/env python3
"""economics.py -- CO-01: Work-Units-per-MTok, the kernel's headline efficiency.

The central metric of the whole family: *verifiable work finished per unit of
compute cost*, operationalized as **Work Units per Million Tokens (WU/MTok)**.
Tokens are an input, not an outcome; WU/MTok makes the 48h burn legible as a
RATIO COLLAPSE (tokens spiked, verified work did not) where the raw token counter
could not.

Numerator -- the Work Unit (CO-01 II.1). A Work Unit counts ONLY when the
existing Production Reality Gate certifies the artifact. This module NEVER builds
a parallel verifier and NEVER re-judges "done": it RECORDS the verdict a PP
done-gate already computed (its passes/total). A gate run that does not fully pass
earns ZERO Work Units regardless of token spend -- that is what makes the metric
hard to inflate (the scaffold illusion earns nothing).

Denominator -- true cost (CO-01 II.2): output + cache-creation tokens (cache-read
is ~free at the measured 96.6% cache ratio). Read straight from the transcripts
via tools/token_ground_truth.py -- the same single source of truth, never a
second token tracker.

The WU ledger (vault/cognitive_os/wu_ledger.jsonl) is append-only; each line is
one gate run's verdict. read_* helpers join it to the token window. Honesty rule
(CO-00 lineage): a sparse ledger or an unmeasured token window yields a
LOW-CONFIDENCE / unknown report, never a fabricated number.

Pure: true_cost_tokens(), wu_per_mtok(), credited_wu(). I/O: record_work_units(),
read_work_units(), economics_report().
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

DEFAULT_LEDGER = _PP_ROOT / "vault" / "cognitive_os" / "wu_ledger.jsonl"
# Below this many records in the window, WU/MTok is reported low-confidence: the
# gate-pass ledger is too sparse to be a dense control signal yet (honest gap).
MIN_RECORDS_FOR_CONFIDENCE = 3


# --------------------------------------------------------------------------
# Pure core
# --------------------------------------------------------------------------
def credited_wu(passes: int, total: int) -> int:
    """Work Units for one gate run. A Work Unit requires a FULLY-passed gate
    (CO-01 II.1: a failed/skipped gate earns zero). A fully-passed N/N suite
    credits N verified checks; any failure credits zero."""
    if total > 0 and passes == total:
        return passes
    return 0


def true_cost_tokens(agg: dict) -> int:
    """Denominator: output + cache-creation (cache-read ~free). CO-01 II.2."""
    return (agg.get("output_tokens", 0) or 0) + (
        agg.get("cache_creation_input_tokens", 0) or 0)


def wu_per_mtok(work_units: int, cost_tokens: int):
    """WU per million true-cost tokens. None when the denominator is 0/unknown
    (honest 'unmeasured', never a divide-by-zero or a fabricated ratio)."""
    if not cost_tokens or cost_tokens <= 0:
        return None
    return work_units / (cost_tokens / 1_000_000.0)


def cost_vector(agg: dict, *, context_tokens=None, latency_ms=None,
                ram_gb=None, parallel_panes=None) -> dict:
    """The 7-dimension cost vector (CO-01 I.2). Dimensions with no real source
    are recorded as None (unknown) -- NEVER silently zeroed (CO-00 honesty)."""
    return {
        "token": true_cost_tokens(agg),                 # real
        "token_breakdown": {k: agg.get(k, 0) for k in (
            "input_tokens", "output_tokens",
            "cache_creation_input_tokens", "cache_read_input_tokens")},
        "context": context_tokens,                      # real if supplied
        "latency_ms": latency_ms,                       # unknown unless measured
        "ram_gb": ram_gb,                               # unknown unless measured
        "parallelism": parallel_panes,                  # unknown unless supplied
        "risk": None,                                   # unknown (not faked)
        "recovery": None,                               # unknown (not faked)
    }


# --------------------------------------------------------------------------
# WU ledger (records the existing gate's verdict; not a parallel verifier)
# --------------------------------------------------------------------------
def record_work_units(gate: str, passes: int, total: int, *,
                      commit: str = "", now: datetime | None = None,
                      ledger_path=None) -> dict:
    """Append one gate run's verdict to the WU ledger. Best-effort: any I/O
    error returns the record without raising (never break a test on logging)."""
    now = now or datetime.now(timezone.utc)
    wu = credited_wu(passes, total)
    rec = {"ts": now.isoformat(), "gate": gate, "passes": passes,
           "total": total, "wu": wu, "certified": wu > 0, "commit": commit}
    try:
        p = Path(ledger_path) if ledger_path else DEFAULT_LEDGER
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return rec


def _parse_ts(s):
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def read_work_units(since: datetime | None = None, *, now: datetime | None = None,
                    ledger_path=None) -> tuple:
    """Sum credited WU over records at/after `since`. Returns (wu, n_records).
    Fail-open -> (0, 0)."""
    p = Path(ledger_path) if ledger_path else DEFAULT_LEDGER
    if not p.is_file():
        return 0, 0
    wu_total = 0
    n = 0
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = _parse_ts(rec.get("ts"))
            if since is not None and (ts is None or ts < since):
                continue
            wu_total += int(rec.get("wu", 0) or 0)
            n += 1
    except OSError:
        return 0, 0
    return wu_total, n


@dataclass
class EconomicsReport:
    window_hours: float
    work_units: int = 0
    records: int = 0
    cost_tokens: int = 0            # true cost (output + cache-creation) in window
    wu_per_mtok: float | None = None
    confidence: str = "unknown"     # high | low | unknown
    cost_vector: dict = field(default_factory=dict)
    note: str = ""


def economics_report(proj_base=None, ledger_path=None, *,
                     window_hours: float = 24.0,
                     now: datetime | None = None,
                     analyze_fn=None) -> EconomicsReport:
    """Join the WU ledger to the token window -> WU/MTok with an honest
    confidence flag. Fail-open: any error -> an unknown-confidence report."""
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(hours=window_hours)
    try:
        wu, n = read_work_units(since, now=now, ledger_path=ledger_path)
        if analyze_fn is None:
            from tools.token_ground_truth import analyze as analyze_fn  # type: ignore
        since_date = since.strftime("%Y-%m-%d")
        data = analyze_fn(proj_base=proj_base, since=since_date)
        # 'today' agg approximates the window's true cost for a ~24h window.
        agg = data.get("today") if window_hours <= 24 else data.get("month_agg")
        agg = agg or {}
        cost = true_cost_tokens(agg)
        ratio = wu_per_mtok(wu, cost)
        if n >= MIN_RECORDS_FOR_CONFIDENCE and cost > 0:
            conf, note = "high", "WU ledger + token truth both present"
        elif cost <= 0:
            conf, note = "unknown", "no token cost measured in window"
        else:
            conf = "low"
            note = (f"WU ledger sparse ({n} record(s) < "
                    f"{MIN_RECORDS_FOR_CONFIDENCE}); gates need to log passes "
                    f"more densely for a high-confidence ratio")
        return EconomicsReport(
            window_hours=window_hours, work_units=wu, records=n,
            cost_tokens=cost, wu_per_mtok=ratio, confidence=conf,
            cost_vector=cost_vector(agg), note=note)
    except Exception as e:  # noqa: BLE001 -- fail-open
        return EconomicsReport(window_hours=window_hours, confidence="unknown",
                               note=f"report errored (fail-open): {e!r}")


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--window-hours", type=float, default=24.0)
    ap.add_argument("--proj-base", default=None)
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--record", nargs=3, metavar=("GATE", "PASSES", "TOTAL"),
                    help="append a gate verdict, then exit")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.record:
        gate, passes, total = args.record
        rec = record_work_units(gate, int(passes), int(total),
                                ledger_path=args.ledger)
        print(json.dumps(rec) if args.json else f"recorded: {rec}")
        return 0
    r = economics_report(proj_base=args.proj_base, ledger_path=args.ledger,
                         window_hours=args.window_hours)
    if args.json:
        print(json.dumps(r.__dict__, default=str))
    else:
        ratio = f"{r.wu_per_mtok:.2f}" if r.wu_per_mtok is not None else "unknown"
        print(f"WU/MTok ({r.window_hours:.0f}h): {ratio}  "
              f"[{r.confidence}]  WU={r.work_units} from {r.records} gate run(s), "
              f"true-cost={r.cost_tokens:,} tok")
        if r.note:
            print(f"  note: {r.note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
