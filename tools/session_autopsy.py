#!/usr/bin/env python3
"""Session autopsy -- the context rent of ONE Claude Code session.

Context rent is what resident context costs because it is re-read on every
later call. The 2026-09-27 KobiiSports incident (session 04b41ed7) is the
reason this exists: 326 calls over 3 days at ~409 k resident each. Two
different levers hide inside that number, and this tool keeps them apart:

  floor              what call #1 already carried (system, tools, always-on
                     instructions, memory). A fresh session pays it again.
  growth above floor what the session accumulated. Only this is what a
                     fresh epoch can remove.

Reader: tools/tis_observed.py (one call counted once). Prices: the dated
vault/pricing/anthropic_YYYY-MM.json in force for each call's month; a model
with no price is UNKNOWN, never a default rate and never zero. USD is API
list-price equivalent; a subscription is not billed this way.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import pricing_source  # noqa: E402
import tis_observed as tis  # noqa: E402

DEFAULT_TTL_S = 3600  # Claude Code on a subscription writes 1h cache entries
_DATED = re.compile(r"^anthropic_(\d{4})-(\d{2})\.json$")


def _price_books(pricing_dir: Path = pricing_source.PRICING_DIR) -> list[tuple[tuple[int, int], dict, str]]:
    books = []
    for p in pricing_dir.glob("anthropic_*.json"):
        m = _DATED.match(p.name)
        if not m:
            continue
        data = json.loads(p.read_text(encoding="utf-8-sig"))
        books.append(((int(m.group(1)), int(m.group(2))), data.get("models") or {},
                      f"{p.name} (fetched {data.get('fetched_iso', '?')})"))
    return sorted(books)


def _model_row(models: dict, model_id: str) -> Optional[dict]:
    for key in sorted(models, key=len, reverse=True):  # opus-5-5 before opus-5
        if key in (model_id or ""):
            return models[key]
    return None


def _ts(s: Optional[str]) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None
    except ValueError:
        return None


def _cost_parts(usage: dict, row: dict) -> dict:
    """Per-category USD through tis_observed.cost_usd, so the TTL split has one owner."""
    def part(keys):
        return tis.cost_usd({k: usage[k] for k in keys if k in usage}, row)[0]
    return {"input": part(("input_tokens",)),
            "cache_write": part(("cache_creation_input_tokens", "cache_creation")),
            "cache_read": part(("cache_read_input_tokens",)),
            "output": part(("output_tokens",))}


def autopsy(path: Path, prices: Optional[dict] = None, ttl_s: int = DEFAULT_TTL_S) -> dict:
    """prices: {model: row} to price every call with (tests); default = the dated books."""
    calls, usage_lines, synthetic, bad = tis._calls_in(Path(path))
    books = [] if prices is not None else _price_books()
    sources = set()
    cost = {"input": 0.0, "cache_write": 0.0, "cache_read": 0.0, "output": 0.0}
    unpriced = 0
    resident, times = [], []
    gaps = rewrite_after_gap = 0
    cc_total = 0
    read_rate = None
    for i, c in enumerate(calls):
        u = c["usage"]
        ctx = tis._context_of(u)
        resident.append(ctx)
        t = _ts(c.get("ts"))
        cc = tis._int(u.get("cache_creation_input_tokens"))
        cc_total += cc
        if i and t and times[-1] and (t - times[-1]).total_seconds() > ttl_s:
            gaps += 1
            rewrite_after_gap += cc
        times.append(t)
        if prices is not None:
            row = _model_row(prices, c["model"])
        else:
            ym = (t.year, t.month) if t else None
            book = next((b for b in reversed(books) if ym and b[0] <= ym), books[-1] if books else None)
            row = _model_row(book[1], c["model"]) if book else None
            if row and book:
                sources.add(book[2])
        if row is None:
            unpriced += 1
            continue
        read_rate = row["cache_read"]
        for k, v in _cost_parts(u, row).items():
            cost[k] += v or 0.0
    total_usd = None if unpriced or not calls else sum(cost.values())
    floor = resident[0] if resident else 0
    growth = sum(max(0, r - floor) for r in resident)
    n = len(resident)
    curve = []
    for q in (0.1, 0.25, 0.5, 0.75, 0.9, 1.0):
        i = max(0, min(n - 1, int(n * q) - 1))
        if n:
            curve.append({"call": i + 1, "resident": resident[i],
                          "ts": times[i].isoformat() if times[i] else None})
    return {
        "path": str(path), "calls": n, "usage_lines": usage_lines,
        "synthetic_skipped": synthetic, "bad_lines": bad,
        "span": [times[0].isoformat() if times and times[0] else None,
                 times[-1].isoformat() if times and times[-1] else None],
        "floor_tokens": floor,
        "resident_total": sum(resident), "resident_max": max(resident, default=0),
        "resident_mean": (sum(resident) / n) if n else None,
        "growth_above_floor_tokens": growth,
        "growth_share": (growth / sum(resident)) if resident and sum(resident) else None,
        "cache_creation_tokens": cc_total,
        "gaps_over_ttl": gaps, "ttl_s": ttl_s, "rewrite_after_gap_tokens": rewrite_after_gap,
        "curve": curve,
        "cost_usd": {**{k: (v if not unpriced else None) for k, v in cost.items()}, "total": total_usd},
        "unpriced_calls": unpriced,
        "price_source": sorted(sources) or (["caller-supplied"] if prices is not None else []),
        # Re-reading growth-above-floor at the read rate is the MOST a fresh epoch could
        # have saved: it ignores rehydration writes and the capsule it would carry.
        "fresh_epoch_saving_bound": {
            "kind": "UPPER_BOUND",
            "usd": (growth * read_rate / 1_000_000) if read_rate is not None and not unpriced else None,
            "excludes": "rehydration cache writes, continuation capsule, quality effects"},
    }


def _resolve(arg: str) -> Path:
    p = Path(arg)
    if p.is_file():
        return p
    hits = sorted(tis.PROJECTS_DIR.glob(f"*/{arg}*.jsonl"))
    if not hits:
        raise SystemExit(f"no transcript matches {arg!r} under {tis.PROJECTS_DIR}")
    return hits[0]


def _fmt(r: dict) -> str:
    c = r["cost_usd"]
    usd = lambda v: "UNKNOWN" if v is None else f"${v:,.2f}"
    lines = [
        f"session  {Path(r['path']).stem}  {r['span'][0]} -> {r['span'][1]}",
        f"calls    {r['calls']} ({r['usage_lines']} usage lines; one call counted once)",
        f"floor    {r['floor_tokens']:,} tokens resident at call #1",
        f"resident mean {r['resident_mean'] or 0:,.0f}  max {r['resident_max']:,}  total re-read {r['resident_total']:,}",
        f"growth above floor {r['growth_above_floor_tokens']:,} ({(r['growth_share'] or 0):.0%} of re-read volume)",
        f"cache writes {r['cache_creation_tokens']:,}; {r['gaps_over_ttl']} gaps > {r['ttl_s']}s TTL "
        f"forced {r['rewrite_after_gap_tokens']:,} of them",
        f"cost (API list equivalent)  read {usd(c['cache_read'])}  write {usd(c['cache_write'])}  "
        f"output {usd(c['output'])}  input {usd(c['input'])}  TOTAL {usd(c['total'])}"
        + (f"  [{r['unpriced_calls']} unpriced calls]" if r["unpriced_calls"] else ""),
        f"fresh-epoch saving UPPER BOUND {usd(r['fresh_epoch_saving_bound']['usd'])} "
        f"(excludes {r['fresh_epoch_saving_bound']['excludes']})",
        f"prices   {', '.join(r['price_source']) or 'none'}",
        "curve    " + "  ".join(f"#{p['call']}:{p['resident']:,}" for p in r["curve"]),
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("session", help="transcript path or session id (prefix ok)")
    ap.add_argument("--ttl", type=int, default=DEFAULT_TTL_S)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    r = autopsy(_resolve(a.session), ttl_s=a.ttl)
    print(json.dumps(r, indent=2, default=str) if a.json else _fmt(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
