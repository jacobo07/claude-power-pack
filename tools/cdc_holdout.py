#!/usr/bin/env python3
"""CDC C10 holdout replay: per-trace roles, avoidable share under CDC rules, scope-normalized table.

Reuses cognitive_pgo.analyse_file (roles, progress, NO_PROGRESS_RUN beyond C4 trip). Offline, zero model calls.
Avoidable (CDC rules) = ALWAYS_WASTE roles (REREAD, RECOVERY, CONTEXT_FAULT) + calls beyond the C4 breaker trip
with no progress. Admission denials cannot be replayed from a transcript: reported UNKNOWN, never 0.
Kill switch: CDC_HOLDOUT=off (exit 0, prints nothing).  Fails open on a malformed transcript (counted in `skipped`).
"""
import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cognitive_pgo as pgo  # noqa: E402


def summarise(parts: list[dict]) -> dict:
    """parts = analyse_file results (main + subagents) of ONE trace."""
    calls = [c for p in parts for c in p["calls"]]
    total = sum(t for _, t in calls)
    unprod = [u for p in parts for u in p["unprod"]]
    waste = sum(u["tokens"] for u in unprod)          # each call appears once in unprod
    by_cause = {}
    for u in unprod:
        k = u["cause"].split(":")[0]
        by_cause[k] = by_cause.get(k, 0) + u["tokens"]
    trip_calls = [u for u in unprod if u["cause"].startswith("NO_PROGRESS_RUN")]
    progress = sum(p["progress"] for p in parts)
    trans = sum(p["transitions"] for p in parts)
    seq = [lb for p in parts for lb, _ in p["seq"]]
    refetch = sum(1 for a, b in zip(seq, seq[1:]) if a.endswith(":proof") and b != a)
    roles = {}
    for r, t in calls:
        roles[r] = roles.get(r, 0) + t
    return {
        "calls": len(calls), "tokens": int(total),
        "roles": {k: round(v / total, 4) for k, v in sorted(roles.items(), key=lambda x: -x[1])} if total else {},
        "avoidable_tokens": int(waste), "avoidable_share": (waste / total) if total else None,
        "avoidable_by_cause": {k: int(v) for k, v in by_cause.items()},
        "breaker_trip_calls_after_25": len(trip_calls),
        "breaker_trip_tokens": int(sum(u["tokens"] for u in trip_calls)),
        "progress_events": progress, "transitions": trans,
        "tokens_per_progress": (total / progress) if progress else None,
        "proof_then_other_pairs": refetch,
        "admission_denials": "UNKNOWN (not recorded in historical transcripts)",
    }


def analyse_trace(path: Path) -> dict:
    parts = [pgo.analyse_file(path, "main")]
    sub = path.with_suffix("") / "subagents"
    skipped = 0
    if sub.is_dir():
        for f in sorted(sub.glob("*.jsonl")):
            try:
                parts.append(pgo.analyse_file(f, "sub:" + f.stem))
            except Exception:
                skipped += 1
    out = summarise(parts)
    out["subagent_files"] = len(parts) - 1
    out["skipped"] = skipped
    return out


def main(argv=None) -> int:
    if os.environ.get("CDC_HOLDOUT", "").lower() == "off":
        return 0
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", action="append", required=True, help="NAME=path1;path2 (repeatable)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    res = {}
    for g in a.group:
        name, _, paths = g.partition("=")
        res[name] = {}
        for p in filter(None, paths.split(";")):
            pp = Path(p)
            try:
                res[name][pp.stem[:8]] = analyse_trace(pp)
            except Exception as e:      # fail open: record, continue
                res[name][pp.stem[:8]] = {"error": repr(e)}
    Path(a.out).write_text(json.dumps(res, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
