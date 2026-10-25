#!/usr/bin/env python3
"""unit_econ -- per-unit economics receipt from one transcript. No model, no network.

    unit_econ.py --transcript T [--since ISO] --goal G --work-class C --unit U
                 [--forecast N] [--value-json F] [--write [FILE]]

Counting is mission_spend's: processed = input + cache_write + cache_read + output, one count per
message id (a streamed turn repeats its usage on every content block). The per-call list is built with the
same rule and its sum is cross-checked against mission_spend.session_tokens; a disagreement is reported,
never averaged away. The tool's own wall time is printed as the measurement tax.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mission_spend as ms  # noqa: E402

_UK = ms._UK  # input, cache_write, cache_read, output


def per_call(transcript: Path, since_iso: str | None = None) -> list[dict]:
    seen: set = set()
    out: list[dict] = []
    with open(transcript, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if not isinstance(r, dict):
                continue
            if since_iso and (r.get("timestamp") or "") < since_iso:
                continue
            m = r.get("message") or {}
            if not isinstance(m, dict):
                continue
            u = m.get("usage")
            if not u or m.get("model") == "<synthetic>":
                continue
            mid = m.get("id") or r.get("uuid")
            if mid in seen:
                continue
            seen.add(mid)
            v = [int(u.get(k) or 0) for k in _UK]
            out.append({"input": v[0], "cache_write": v[1], "cache_read": v[2], "output": v[3], "total": sum(v)})
    return out


def pct(sorted_vals: list[int], p: float) -> int:
    """Nearest-rank percentile; 0 for an empty list (reported with calls=0, not hidden)."""
    if not sorted_vals:
        return 0
    return sorted_vals[max(0, math.ceil(p * len(sorted_vals)) - 1)]


def build(transcript: Path, since_iso: str | None, goal: str, work_class: str, unit: str,
          forecast: int | None, value: object | None) -> dict:
    t0 = time.perf_counter()
    calls = per_call(transcript, since_iso)
    ref = ms.session_tokens(transcript, since_iso)
    sizes = sorted(c["total"] for c in calls)
    actual = sum(sizes)
    first = calls[0] if calls else {"cache_write": 0, "cache_read": 0}
    rec = {
        "goal": goal, "work_class": work_class, "unit": unit, "transcript": str(transcript), "since": since_iso,
        "calls": len(calls), "processed_tokens": actual,
        "first_call_cws": first["cache_write"], "first_call_cache_read": first["cache_read"],
        "first_call_cache_write": first["cache_write"],
        "avg_per_call": actual // len(calls) if calls else 0,
        "p50_per_call": pct(sizes, 0.5), "p80_per_call": pct(sizes, 0.8), "peak_per_call": sizes[-1] if sizes else 0,
        "forecast": forecast,
        "amplification": round(actual / forecast, 3) if forecast else None,
        "value_deposit": value,
        "mission_spend_tokens": ref["tokens"],
        "count_agrees_with_mission_spend": ref["tokens"] == actual,
    }
    rec["measurement_tax_s"] = round(time.perf_counter() - t0, 3)
    return rec


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--transcript", required=True)
    p.add_argument("--since")
    p.add_argument("--goal", required=True)
    p.add_argument("--work-class", required=True)
    p.add_argument("--unit", required=True)
    p.add_argument("--forecast", type=int)
    p.add_argument("--value-json")
    p.add_argument("--write", nargs="?", const="", default=None)
    a = p.parse_args(argv)
    value = json.loads(Path(a.value_json).read_text(encoding="utf-8-sig")) if a.value_json else None
    rec = build(Path(a.transcript), a.since, a.goal, a.work_class, a.unit, a.forecast, value)
    text = json.dumps(rec, indent=1)
    print(text)
    if a.write is not None:
        dest = Path(a.write) if a.write else Path(a.transcript).with_suffix(".unit_econ.json")
        dest.write_text(text, encoding="utf-8")
    return 0 if rec["count_agrees_with_mission_spend"] else 1


if __name__ == "__main__":
    sys.exit(main())
