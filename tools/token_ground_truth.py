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
    """Sum message.usage across a transcript, one API call once. None on unreadable file.

    The harness writes one line per content block and repeats the call's usage on
    each; summing lines overcounted 2.5x (KobiiSports 04b41ed7, 2026-09-27: 814 lines,
    332 M cache reads, for 326 calls and 132 M). A call is keyed (message.id,
    requestId), last copy wins -- the tools/tis_observed.py contract, pinned by
    tools/test_usage_dedup.py. `<synthetic>` harness notices are not API calls."""
    agg = _empty_agg()
    models: set[str] = set()
    last_ts = None
    calls: dict = {}
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
            if isinstance(usage, dict) and usage and msg.get("model") != "<synthetic>":
                key = (msg.get("id"), entry.get("requestId"))
                if key == (None, None):
                    key = ("line", len(calls))  # no identity: count once as-is
                calls[key] = usage
                if msg.get("model"):
                    models.add(msg["model"])
    for usage in calls.values():
        for k in USAGE_KEYS:
            agg[k] += usage.get(k, 0) or 0
    turns = len(calls)
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


def _store_dirs(proj_base) -> list[Path]:
    """Each project dir once, by resolved path.

    A directory junction aliases a project dir (projects/C--Users-User-Apps-
    mcp-video-analyzer -> the PP dir): walked as listed, 152 transcripts were
    read twice on 2026-10-02. Yielding the resolved path also makes the
    path-keyed identity of an id-less call independent of listing order, as
    usage_index does since f234580."""
    base = Path(proj_base or DEFAULT_PROJ_BASE)
    if not base.is_dir():
        return []
    seen: dict[str, Path] = {}
    for sub in sorted(base.iterdir()):
        if not sub.is_dir():
            continue
        real = Path(os.path.realpath(sub))
        seen.setdefault(os.path.normcase(str(real)), real)
    return list(seen.values())


def iter_transcripts(proj_base) -> list[Path]:
    out: list[Path] = []
    for sub in _store_dirs(proj_base):
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


def _parse_turn_ts(s):
    """ISO8601 (with trailing Z) -> aware datetime, else None."""
    if not isinstance(s, str) or len(s) < 19:
        return None
    try:
        from datetime import datetime as _dt
        d = _dt.fromisoformat(s.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _tis():
    """tools/tis_observed.py, the reference call reader (dedup, last copy wins)."""
    import importlib.util
    import sys
    if "tis_observed" in sys.modules:
        return sys.modules["tis_observed"]
    spec = importlib.util.spec_from_file_location(
        "tis_observed", Path(__file__).resolve().parent / "tis_observed.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tis_observed"] = mod
    spec.loader.exec_module(mod)
    return mod


def iter_transcripts_with_subagents(proj_base):
    """(path, is_subagent) for every transcript, subagents included.

    iter_transcripts() sees only top-level files; subagent transcripts live at
    <project>/<session>/subagents/*.jsonl and were 41 % of all calls in the
    2026-09-30..10-02 weekly-limit incident."""
    for sub in _store_dirs(proj_base):
        for jf in sub.glob("*.jsonl"):
            yield jf, False
        for jf in sub.glob("*/subagents/*.jsonl"):
            yield jf, True


def window_usage(hours: float, proj_base=None,
                 now: datetime | None = None) -> dict | None:
    """Every usage category for API calls whose own timestamp is in (now-hours, now].

    One call counted once, last copy wins (tis_observed contract): input and cache
    figures repeat across a call's lines but output_tokens grows while it streams.
    Subagent transcripts included. Keys: USAGE_KEYS + calls, subagent_calls,
    sdk_calls (entrypoint sdk-cli = claude -p / programmatic, i.e. not an
    interactive pane). mtime only prunes files, it never admits a call.

    None when no call fell in the window: unmeasured, never a fake 0."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    from datetime import timedelta
    start = now - timedelta(hours=hours)
    start_epoch = start.timestamp()
    tis = _tis()
    # Keyed across files: one session file can sit under two project dirs
    # (2026-10-02: 3,044 calls, +12.7 % when summed per file). The copy with
    # more output is the more complete one. Identity-less calls stay per file.
    best: dict = {}
    for fp, is_sub in iter_transcripts_with_subagents(proj_base):
        try:
            if fp.stat().st_mtime < start_epoch:
                continue
            calls, _, _, _ = tis._calls_in(fp)
        except (OSError, UnicodeDecodeError):
            continue
        for c in calls:
            ts = _parse_turn_ts(c.get("ts"))
            if ts is None or ts <= start or ts > now:
                continue
            key = c.get("key")
            if not key or key[0] == "line":
                key = (str(fp), key)
            prev = best.get(key)
            if prev is None or ((c["usage"].get("output_tokens") or 0)
                                > (prev[0]["usage"].get("output_tokens") or 0)):
                best[key] = (c, is_sub)
    if not best:
        return None
    out = {k: 0 for k in USAGE_KEYS}
    out.update(calls=len(best), subagent_calls=0, sdk_calls=0)
    for c, is_sub in best.values():
        for k in USAGE_KEYS:
            out[k] += c["usage"].get(k, 0) or 0
        out["subagent_calls"] += is_sub
        out["sdk_calls"] += c.get("entrypoint") == "sdk-cli"
    return out


def window_output(hours: float, proj_base=None,
                  now: datetime | None = None) -> int | None:
    """Output tokens for calls in the last `hours` -- window_usage()'s output.

    Until 2026-10-02 this summed every transcript LINE and skipped subagents:
    39.2 M for a window whose deduplicated output was 19.1 M. None when no call
    fell in the window (honest "unmeasured", never a fake 0)."""
    u = window_usage(hours, proj_base, now)
    return None if u is None else u["output_tokens"]


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
