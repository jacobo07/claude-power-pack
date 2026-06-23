#!/usr/bin/env python3
"""token_ground_truth.py -- real per-session token usage, straight from disk.

THE source of truth for token TCO is Claude Code's own transcripts in
~/.claude/projects/<encoded-cwd>/<sid>.jsonl. Each assistant turn carries a
`message.usage` block: input_tokens, output_tokens, cache_creation_input_tokens,
cache_read_input_tokens. This tool aggregates those across all transcripts --
no estimates, no model-side hooks, no placeholders.

WHY this exists (FASE -1 audit, 2026-06-23): the PP's dedicated logger (TIS,
tools/tis.py) records JIT-INJECTION size per UserPromptSubmit (model
"claude-code-hook", cache fields always 0), NOT the real per-turn model usage.
budget_monitor.py tracks the separate programmatic-credit bucket. Neither
aggregates real session burn. This closes that gap (UKDL T-TCO-TRACKING-GAP-001).

Owner is on Claude Max (flat rate) -> marginal $/token = 0. The meaningful TCO
metric is therefore CACHE RATIO + output volume + context efficiency, not $.
Dollar figures here are HYPOTHETICAL "if-API" comparisons only.

Usage:
  python tools/token_ground_truth.py                       # stdout summary
  python tools/token_ground_truth.py --report out.md       # + markdown report
  python tools/token_ground_truth.py --top 20              # top N sessions
  python tools/token_ground_truth.py --since 2026-06-01    # filter by date

Importable: analyze(proj_base=...) returns the structured aggregate (used by
tools/test_tco_tracking.py with a hermetic tmp tree).
"""
from __future__ import annotations

import argparse
import json
import os
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

USAGE_KEYS = ("input_tokens", "output_tokens",
              "cache_creation_input_tokens", "cache_read_input_tokens")

# A session whose AVERAGE fresh (non-cached) input per turn exceeds this is a
# context hog worth /compact or /kclear. Fresh input -- not cache reads --
# because cache reads are ~free and do not pressure the live window.
HIGH_CONSUMER_AVG_INPUT = 100_000
# Below this cache ratio, the prompt cache is underused (variable prompts,
# timestamps, churn). UKDL T-CACHE-RATIO-LOW-001.
CACHE_HEALTHY_PCT = 50.0

DEFAULT_PROJ_BASE = Path.home() / ".claude" / "projects"


def _empty_agg() -> dict:
    return dict.fromkeys(USAGE_KEYS, 0)


def cache_ratio(agg: dict) -> float:
    """cache_read / (cache_read + fresh_input + cache_creation) * 100.

    The denominator is every input-side token the model had to be fed; the
    numerator is the portion served from cache. 0 when no input-side tokens."""
    rd = agg.get("cache_read_input_tokens", 0)
    denom = (rd + agg.get("input_tokens", 0)
             + agg.get("cache_creation_input_tokens", 0))
    return (rd / denom * 100.0) if denom else 0.0


def billable(agg: dict) -> int:
    """input + output (the non-cache token movement). Not a $ figure."""
    return agg.get("input_tokens", 0) + agg.get("output_tokens", 0)


def parse_session(fp: Path) -> dict | None:
    """Sum message.usage across a transcript. None on unreadable file."""
    agg = _empty_agg()
    turns = 0
    models: set[str] = set()
    last_ts = None
    try:
        text = fp.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = entry.get("timestamp")
        if ts:
            last_ts = ts
        msg = entry.get("message")
        if isinstance(msg, dict):
            usage = msg.get("usage")
            if isinstance(usage, dict) and usage:
                for k in USAGE_KEYS:
                    agg[k] += usage.get(k, 0) or 0
                turns += 1
                if msg.get("model"):
                    models.add(msg["model"])
    try:
        mtime = fp.stat().st_mtime
    except OSError:
        mtime = 0.0
    return {"agg": agg, "turns": turns, "models": sorted(models),
            "last_ts": last_ts, "mtime": mtime,
            "sid": fp.stem, "project": fp.parent.name, "file": str(fp)}


def _session_date(info: dict) -> str:
    """YYYY-MM-DD by last in-transcript timestamp, else file mtime."""
    ts = info.get("last_ts")
    if isinstance(ts, str) and len(ts) >= 10:
        return ts[:10]
    if info.get("mtime"):
        return datetime.fromtimestamp(info["mtime"]).strftime("%Y-%m-%d")
    return "unknown"


def iter_transcripts(proj_base) -> list[Path]:
    base = Path(proj_base or DEFAULT_PROJ_BASE)
    if not base.is_dir():
        return []
    out: list[Path] = []
    for sub in base.iterdir():
        if not sub.is_dir():
            continue
        for jf in sub.glob("*.jsonl"):
            if "subagent" in str(jf).lower():
                continue
            out.append(jf)
    return out


def analyze(proj_base=None, since: str | None = None,
            now: datetime | None = None) -> dict:
    """Aggregate real usage across all transcripts.

    `since` (YYYY-MM-DD) drops sessions dated earlier. `now` is injectable so
    tests are deterministic (today/month buckets do not depend on wall clock).
    """
    now = now or datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    month_str = now.strftime("%Y-%m")

    files = iter_transcripts(proj_base)
    life, today, month = _empty_agg(), _empty_agg(), _empty_agg()
    sessions: list[dict] = []
    files_total = len(files)
    files_with_usage = 0

    for fp in files:
        info = parse_session(fp)
        if not info or info["turns"] == 0:
            continue
        d = _session_date(info)
        if since and d < since:
            continue
        files_with_usage += 1
        info["date"] = d
        info["cache_ratio"] = cache_ratio(info["agg"])
        info["billable"] = billable(info["agg"])
        info["avg_input_per_turn"] = (
            info["agg"]["input_tokens"] / max(1, info["turns"]))
        for k in USAGE_KEYS:
            life[k] += info["agg"][k]
            if d == today_str:
                today[k] += info["agg"][k]
            if d.startswith(month_str):
                month[k] += info["agg"][k]
        sessions.append(info)

    sessions.sort(key=lambda s: s["billable"], reverse=True)
    high = [s for s in sessions
            if s["avg_input_per_turn"] > HIGH_CONSUMER_AVG_INPUT]

    return {
        "generated": now.strftime("%Y-%m-%d %H:%M"),
        "today_date": today_str,
        "month": month_str,
        "files_total": files_total,
        "files_with_usage": files_with_usage,
        "today": today, "today_cache_ratio": cache_ratio(today),
        "month_agg": month, "month_cache_ratio": cache_ratio(month),
        "lifetime": life, "lifetime_cache_ratio": cache_ratio(life),
        "sessions": sessions,
        "high_consumers": high,
    }


def today_output_tokens(proj_base=None, now: datetime | None = None) -> int | None:
    """Fast launch-gate burn: sum output_tokens from transcripts MODIFIED today.

    A full analyze() scans every transcript (hundreds of files) -- too slow for
    a pre-launch gate. This stats-filters to files touched since local midnight
    and parses only those. Approximation: a multi-day session file touched today
    contributes its whole output (earlier turns included) -- acceptable for an
    advisory and clearly an over-estimate, never an under-count. Returns None
    (honest "unmeasured") when no transcript was touched today, never a fake 0.
    """
    now = now or datetime.now()
    start = datetime(now.year, now.month, now.day).timestamp()
    total = 0
    seen = False
    for fp in iter_transcripts(proj_base):
        try:
            if fp.stat().st_mtime < start:
                continue
        except OSError:
            continue
        info = parse_session(fp)
        if not info or info["turns"] == 0:
            continue
        seen = True
        total += info["agg"]["output_tokens"]
    return total if seen else None


def _fmt_agg(a: dict) -> str:
    return (f"in={a['input_tokens']:,} out={a['output_tokens']:,} "
            f"cache_rd={a['cache_read_input_tokens']:,} "
            f"cache_cr={a['cache_creation_input_tokens']:,}")


def build_report(data: dict, top_n: int = 12) -> str:
    L: list[str] = []
    L.append("# Token Usage -- Real Ground Truth")
    L.append("")
    L.append(f"**Generated:** {data['generated']}  ")
    L.append("**Source:** `~/.claude/projects/*/*.jsonl` `message.usage` "
             "(real per-turn, no estimates)  ")
    L.append("**Plan:** Claude Max (flat rate) -- $ figures would be "
             "hypothetical; the real metric is cache ratio + output volume.  ")
    L.append(f"**Transcripts:** {data['files_with_usage']} with usage / "
             f"{data['files_total']} total")
    L.append("")
    L.append("## Aggregates")
    L.append("")
    L.append("| Window | Input | Output | Cache reads | Cache create | "
             "Cache ratio |")
    L.append("|---|---|---|---|---|---|")
    for label, agg, cr in (
        (f"Today ({data['today_date']})", data["today"],
         data["today_cache_ratio"]),
        (f"Month ({data['month']})", data["month_agg"],
         data["month_cache_ratio"]),
        ("Lifetime", data["lifetime"], data["lifetime_cache_ratio"]),
    ):
        L.append(f"| {label} | {agg['input_tokens']:,} | "
                 f"{agg['output_tokens']:,} | "
                 f"{agg['cache_read_input_tokens']:,} | "
                 f"{agg['cache_creation_input_tokens']:,} | {cr:.1f}% |")
    L.append("")
    health = ("HEALTHY" if data["lifetime_cache_ratio"] >= CACHE_HEALTHY_PCT
              else "LOW -- prompt cache underused")
    L.append(f"**Cache health:** {health} "
             f"(threshold {CACHE_HEALTHY_PCT:.0f}%).")
    L.append("")
    L.append(f"## Top {top_n} sessions by billable (input+output)")
    L.append("")
    L.append("| Billable | Date | Project | sid | Turns | Cache% | "
             "Avg fresh in/turn |")
    L.append("|---|---|---|---|---|---|---|")
    for s in data["sessions"][:top_n]:
        L.append(f"| {s['billable']:,} | {s['date']} | "
                 f"{s['project'][:30]} | {s['sid'][:8]} | {s['turns']} | "
                 f"{s['cache_ratio']:.1f}% | {s['avg_input_per_turn']:,.0f} |")
    L.append("")
    L.append("## High-consumer sessions "
             f"(avg fresh input/turn > {HIGH_CONSUMER_AVG_INPUT:,})")
    L.append("")
    if not data["high_consumers"]:
        L.append("None. No session pressures the live context window on a "
                 "per-turn basis -- cache absorbs the bulk.")
    else:
        L.append("| Project | sid | Avg fresh in/turn | Turns | "
                 "Recommended action |")
        L.append("|---|---|---|---|---|")
        for s in data["high_consumers"]:
            L.append(f"| {s['project'][:30]} | {s['sid'][:8]} | "
                     f"{s['avg_input_per_turn']:,.0f} | {s['turns']} | "
                     "/compact or /kclear |")
    L.append("")
    L.append("---")
    L.append("*Generated by tools/token_ground_truth.py "
             "(Claude Power Pack -- TCO ground truth).*")
    L.append("")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--report", default=None,
                    help="write a markdown report to this path")
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--since", default=None, help="YYYY-MM-DD filter")
    ap.add_argument("--proj-base", default=None,
                    help="override ~/.claude/projects (testing)")
    args = ap.parse_args(argv)

    data = analyze(proj_base=args.proj_base, since=args.since)
    print(f"transcripts with usage: {data['files_with_usage']}/"
          f"{data['files_total']}")
    print(f"TODAY    ({data['today_date']}): {_fmt_agg(data['today'])}  "
          f"cacheR={data['today_cache_ratio']:.1f}%")
    print(f"MONTH    ({data['month']}): {_fmt_agg(data['month_agg'])}  "
          f"cacheR={data['month_cache_ratio']:.1f}%")
    print(f"LIFETIME : {_fmt_agg(data['lifetime'])}  "
          f"cacheR={data['lifetime_cache_ratio']:.1f}%")
    print(f"high-consumer sessions: {len(data['high_consumers'])}")
    if args.report:
        out = Path(args.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build_report(data, args.top), encoding="utf-8")
        print(f"report -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
