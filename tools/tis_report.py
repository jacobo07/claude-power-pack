#!/usr/bin/env python3
"""TIS Capa 2 -- analytics CLI.

Four flags, all stdlib, ASCII tables:

  --summary       per-session aggregate (calls / in / out / cache% / cost$)
  --by-skill      top-N skills by input_tokens (default N=10)
  --cache-ratio   overall cache_read / (input + cache_read) percentage
  --since DATE    filter entries from YYYY-MM-DD inclusive (combinable)

Pricing constants (USD per 1M tokens) for Sonnet 4.6 by default; the
PRICING dict can be extended for Opus / Haiku without external deps.
"""
from __future__ import annotations
import argparse
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tis  # noqa: E402


# USD per 1M tokens. Source: anthropic.com/pricing (2026-05).
PRICING = {
    "claude-opus-4-7":     {"input": 15.0, "output": 75.0},
    "claude-opus-4-6":     {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-6":   {"input": 3.0,  "output": 15.0},
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5":    {"input": 0.80, "output": 4.0},
    # hook-level events are not LLM calls; pricing is 0 by definition.
    "claude-code-hook":    {"input": 0.0,  "output": 0.0},
    "default":             {"input": 3.0,  "output": 15.0},
}


def _price_for(model: str) -> dict:
    if model in PRICING:
        return PRICING[model]
    for key in PRICING:
        if key != "default" and key in (model or ""):
            return PRICING[key]
    return PRICING["default"]


def _cost_usd(entry: dict) -> float:
    p = _price_for(entry.get("model", ""))
    return (entry.get("input_tokens", 0) * p["input"] / 1_000_000 +
            entry.get("output_tokens", 0) * p["output"] / 1_000_000)


def _print_table(headers: list, rows: list) -> None:
    if not rows:
        print(f"(no data for {headers})")
        return
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    sep = "  "
    print(sep.join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    print(sep.join("-" * widths[i] for i in range(len(headers))))
    for row in rows:
        print(sep.join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)))


def cmd_summary(entries: list) -> int:
    per_session = defaultdict(lambda: {
        "calls": 0, "in": 0, "out": 0, "cr": 0, "cc": 0, "cost": 0.0,
    })
    for e in entries:
        s = per_session[e.get("session_id", "")]
        s["calls"] += 1
        s["in"]   += e.get("input_tokens", 0)
        s["out"]  += e.get("output_tokens", 0)
        s["cr"]   += e.get("cache_read_tokens", 0)
        s["cc"]   += e.get("cache_creation_tokens", 0)
        s["cost"] += _cost_usd(e)
    rows = []
    for sid, s in sorted(per_session.items()):
        denom = s["in"] + s["cr"]
        ratio = (s["cr"] / denom * 100) if denom else 0.0
        rows.append([sid, s["calls"], s["in"], s["out"],
                     f"{ratio:.1f}%", f"${s['cost']:.5f}"])
    _print_table(
        ["session", "calls", "in_tok", "out_tok", "cache%", "cost_usd"],
        rows,
    )
    return 0


def cmd_by_skill(entries: list, top_n: int = 10) -> int:
    agg = defaultdict(lambda: {"calls": 0, "in": 0, "out": 0, "cost": 0.0})
    for e in entries:
        name = e.get("skill_name", "")
        a = agg[name]
        a["calls"] += 1
        a["in"]    += e.get("input_tokens", 0)
        a["out"]   += e.get("output_tokens", 0)
        a["cost"]  += _cost_usd(e)
    ordered = sorted(agg.items(), key=lambda kv: kv[1]["in"], reverse=True)
    rows = [[name, a["calls"], a["in"], a["out"], f"${a['cost']:.5f}"]
            for name, a in ordered[:top_n]]
    _print_table(["skill", "calls", "in_tok", "out_tok", "cost_usd"], rows)
    return 0


def cmd_cache_ratio(entries: list) -> int:
    total_in = sum(e.get("input_tokens", 0) for e in entries)
    total_cr = sum(e.get("cache_read_tokens", 0) for e in entries)
    denom = total_in + total_cr
    ratio = (total_cr / denom * 100) if denom else 0.0
    print(f"cache_hit_ratio = {ratio:.2f}% "
          f"(cache_read={total_cr} / (input={total_in} + cache_read={total_cr}))")
    print(f"entries={len(entries)}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--summary", action="store_true",
                    help="per-session aggregate")
    ap.add_argument("--by-skill", action="store_true",
                    help="top-N skills by input_tokens")
    ap.add_argument("--cache-ratio", action="store_true",
                    help="overall cache-hit ratio")
    ap.add_argument("--since", metavar="YYYY-MM-DD",
                    help="filter entries from this date inclusive")
    ap.add_argument("--top", type=int, default=10,
                    help="N for --by-skill (default 10)")
    args = ap.parse_args(argv)

    if not any([args.summary, args.by_skill, args.cache_ratio]):
        ap.print_help()
        return 2

    entries = tis.read_log(since_date=args.since)
    if args.summary:
        return cmd_summary(entries)
    if args.by_skill:
        return cmd_by_skill(entries, top_n=args.top)
    if args.cache_ratio:
        return cmd_cache_ratio(entries)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
