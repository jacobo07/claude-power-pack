"""pgo.py -- PRR resource profile ledger (goal prr, plan row R: Resource PGO).

Turns one bench run (`modules/prr/bench/longrun.py` JSON lines) into a resource profile and keeps the
profiles in an append-only ledger. A profile is what the recycle cadence is guided by:
  fresh_anon_mb        RssAnon after the first turn of a fresh process
  epoch_start_anon_mb  median RssAnon right after each resume (None when the run never recycled)
  growth_mb_per_turn   median in-epoch growth after a resume; for an unrecycled run, the run's own slope
  peak_hwm_mb          largest VmHWM sampled (images drive the peak, not the steady state)
`recommend_epoch` answers "how many turns fit in an epoch under this RssAnon budget" from a profile of the
SAME plane only: a GEX44 profile never answers for Windows.

CLI:
  python -m modules.prr.pgo ingest RUN.jsonl --workload bash --plane gex44
  python -m modules.prr.pgo recommend --workload bash --plane gex44 --budget-mb 200
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
import time
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[2] / "vault" / "programs" / "prr" / "pgo" / "profiles.jsonl"
SCHEMA = 1


def _anon(row: dict):
    return (row.get("main") or {}).get("RssAnon")


def profile_run(rows: list, *, workload: str, plane: str, source: dict) -> dict:
    samples = [r for r in rows if r.get("event") is None and "turn" in r and _anon(r) is not None]
    if not samples:
        raise ValueError("run has no memory samples")
    summary = next((r for r in reversed(rows) if "fit" in r), {})
    # Each epoch row follows the turn that triggered the resume; pair its start with the epoch's last sample.
    starts, last_turn = {}, 0
    for r in rows:
        if r.get("event") == "epoch":
            starts[r["epoch"]] = (last_turn, _anon(r), r.get("resume_s"))
        elif "turn" in r:
            last_turn = r["turn"]
    rates, spans = [], []
    for epoch, (t0, a0, _) in starts.items():
        ends = [s for s in samples if s["epoch"] == epoch and s["turn"] > t0]
        if ends and a0 is not None:
            end = max(ends, key=lambda s: s["turn"])
            rates.append((_anon(end) - a0) / (end["turn"] - t0))
            spans.append(end["turn"] - t0)
    if rates:
        growth = round(statistics.median(rates), 3)
    else:
        slope = (summary.get("fit") or {}).get("slope_mb_per_100_turns")
        growth = None if slope is None else round(slope / 100, 3)
    start_vals = [a for _, a, _ in starts.values() if a is not None]
    resumes = [r for _, _, r in starts.values() if r is not None]
    first = min(samples, key=lambda s: s["turn"])
    return {"schema": SCHEMA, "ts": time.time(), "workload": workload, "plane": plane, "source": source,
            "turns": summary.get("turns", max(s["turn"] for s in samples)),
            "epochs": summary.get("epochs", 1 + len(starts)),
            "fresh_anon_mb": _anon(first),
            "epoch_start_anon_mb": statistics.median(start_vals) if start_vals else None,
            "growth_mb_per_turn": growth,
            # In-epoch growth is steepest early, so a rate measured over short epochs overstates longer ones.
            "epoch_turns_measured": statistics.median(spans) if spans else None,
            "peak_hwm_mb": max((s.get("main") or {}).get("VmHWM", 0) for s in samples),
            "resume_s_median": round(statistics.median(resumes), 3) if resumes else None,
            "drift_mb_per_epoch": (summary.get("epoch_start_drift") or {}).get("mb_per_epoch")}


def load(ledger: Path) -> list:
    out = []
    try:
        with open(ledger, encoding="utf-8") as fh:
            for line in fh:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
    except FileNotFoundError:
        pass
    return out


def append(ledger: Path, profile: dict) -> bool:
    """Append-only: a profile whose source sha256 + workload + plane is already recorded is refused, never rewritten."""
    key = ((profile.get("source") or {}).get("sha256"), profile.get("workload"), profile.get("plane"))
    for p in load(ledger):
        if ((p.get("source") or {}).get("sha256"), p.get("workload"), p.get("plane")) == key:
            return False
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(profile, sort_keys=True) + "\n")
    return True


def recommend_epoch(profiles: list, *, workload: str, plane: str, anon_budget_mb: float) -> dict:
    cands = [p for p in profiles if p.get("workload") == workload and p.get("plane") == plane
             and p.get("epoch_start_anon_mb") is not None and p.get("growth_mb_per_turn")]
    if not cands:
        return {"turns": None, "plane": plane, "reason": f"no recycled profile for {workload} on {plane}"}
    p = max(cands, key=lambda q: q.get("ts", 0))
    basis = (p.get("source") or {}).get("sha256")
    head = anon_budget_mb - p["epoch_start_anon_mb"]
    if head <= 0:
        return {"turns": None, "plane": plane, "basis": basis,
                "reason": f"budget {anon_budget_mb} MB is at or under the epoch start {p['epoch_start_anon_mb']} MB"}
    turns = math.floor(head / p["growth_mb_per_turn"])
    measured = p.get("epoch_turns_measured")
    return {"turns": turns, "plane": plane, "basis": basis,
            "epoch_start_anon_mb": p["epoch_start_anon_mb"], "growth_mb_per_turn": p["growth_mb_per_turn"],
            "peak_hwm_mb": p["peak_hwm_mb"], "measured_epoch_turns": measured,
            # Past the measured epoch length the linear rate is an extrapolation (conservative: growth slows).
            "extrapolated": measured is None or turns > measured}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m modules.prr.pgo")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ing = sub.add_parser("ingest")
    ing.add_argument("run")
    rec = sub.add_parser("recommend")
    rec.add_argument("--budget-mb", type=float, required=True)
    for p in (ing, rec):
        p.add_argument("--workload", required=True)
        p.add_argument("--plane", required=True)
        p.add_argument("--ledger", default=str(LEDGER))
    args = ap.parse_args(argv)
    ledger = Path(args.ledger)
    if args.cmd == "ingest":
        raw = Path(args.run).read_bytes()
        rows = [json.loads(l) for l in raw.decode("utf-8").splitlines() if l.strip()]
        prof = profile_run(rows, workload=args.workload, plane=args.plane,
                           source={"path": Path(args.run).name, "sha256": hashlib.sha256(raw).hexdigest()})
        added = append(ledger, prof)
        print(json.dumps({"appended": added, **prof}))
        return 0
    print(json.dumps(recommend_epoch(load(ledger), workload=args.workload, plane=args.plane,
                                     anon_budget_mb=args.budget_mb)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
