#!/usr/bin/env python3
"""token_corpus_audit.py -- structural token-optimization audit over the .jsonl corpus.

Extends token_ground_truth.py (per-session aggregate) with the per-TURN and
per-REPO structural analyses the FASE -1 corpus audit needs. THE constraint:
this tool scans transcripts ON DISK and emits only AGGREGATES -- it never loads
raw .jsonl content into the agent's context. Every number here is measured from
`message.usage` + `message.content` blocks, no estimates.

Six analyses (mirror the ULTRA-PLAN):
  A1  initial context load  -- first-turn (input+cache_creation) per repo,
                               turns-per-session, cache-read vs fresh-input share
  A2  output distribution   -- top sessions by output, output-per-turn spread,
                               share of output concentrated in the fattest turns
  A3  cache ratio per repo  -- weighted cache ratio grouped by project; low outliers
  A4  inefficiency patterns -- same-file re-reads within a session, repeated
                               FASE-1/Reality-Scan markers, turn-count overhead
  A5  hour-of-day burn      -- output per (date,hour); peak buckets + concurrent
                               distinct-session counts (parallel-burn hypothesis)
  A6  context% vs output    -- mean output bucketed by fed-context size

Owner is on Claude Max (flat rate) -> marginal $/token = 0. The meaningful metric
is OUTPUT VOLUME + CACHE RATIO + CONTEXT EFFICIENCY, never a $ figure.

Usage:
  python tools/token_corpus_audit.py                      # stdout summary
  python tools/token_corpus_audit.py --report out.md      # + markdown report
  python tools/token_corpus_audit.py --since 2026-06-01    # date filter
  python tools/token_corpus_audit.py --proj-base <dir>     # testing override

Importable: audit(proj_base=...) returns the structured aggregate (used by
tools/test_token_optimization.py with a hermetic tmp tree).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load_ground_truth():
    """Import token_ground_truth.py as a module (hyphen-free name, same dir)."""
    spec = importlib.util.spec_from_file_location(
        "token_ground_truth", _HERE / "token_ground_truth.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_GT = _load_ground_truth()
iter_transcripts = _GT.iter_transcripts
DEFAULT_PROJ_BASE = _GT.DEFAULT_PROJ_BASE

USAGE_KEYS = ("input_tokens", "output_tokens",
              "cache_creation_input_tokens", "cache_read_input_tokens")

# Fed-context buckets (proxy: input+cache_read+cache_creation fed to the turn).
# Nominal against a 200k window: <30% ~ <60k, 30-60% ~ 60-120k, >60% ~ >120k.
CTX_LOW = 60_000
CTX_HIGH = 120_000

_MARKER_RE = re.compile(r"FASE\s*-?\s*1|REALITY\s+SCAN|CORPUS\s+SCAN|"
                        r"PREFLIGHT", re.IGNORECASE)


def _parse_ts(s):
    if not isinstance(s, str) or len(s) < 19:
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def parse_turns(fp: Path) -> dict | None:
    """Single pass over one transcript. Returns per-turn records + session meta.

    A 'turn' here is any message carrying a usage block. Content signals
    (text length, tool names, Read paths, marker hits) are harvested from the
    same message.content in the same pass -- no re-read."""
    try:
        text = fp.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    turns: list[dict] = []
    read_counts: dict[str, int] = defaultdict(int)
    marker_hits = 0
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = entry.get("message")
        # content-signal harvest (both user + assistant carry content)
        text_chars = 0
        tool_names: list[str] = []
        if isinstance(msg, dict):
            content = msg.get("content")
            if isinstance(content, list):
                for blk in content:
                    if not isinstance(blk, dict):
                        continue
                    bt = blk.get("type")
                    if bt == "text" and isinstance(blk.get("text"), str):
                        t = blk["text"]
                        text_chars += len(t)
                        if _MARKER_RE.search(t):
                            marker_hits += 1
                    elif bt == "tool_use":
                        nm = blk.get("name") or ""
                        tool_names.append(nm)
                        if nm == "Read":
                            fp2 = (blk.get("input") or {}).get("file_path")
                            if isinstance(fp2, str):
                                read_counts[fp2] += 1
            elif isinstance(content, str):
                text_chars += len(content)
                if _MARKER_RE.search(content):
                    marker_hits += 1
        # usage turn
        if isinstance(msg, dict):
            usage = msg.get("usage")
            if isinstance(usage, dict) and usage:
                rec = {k: (usage.get(k, 0) or 0) for k in USAGE_KEYS}
                rec["ts"] = _parse_ts(entry.get("timestamp"))
                rec["text_chars"] = text_chars
                rec["tool_names"] = tool_names
                rec["model"] = msg.get("model") or ""
                turns.append(rec)
    if not turns:
        return None
    try:
        mtime = fp.stat().st_mtime
    except OSError:
        mtime = 0.0
    last = next((t["ts"] for t in reversed(turns) if t["ts"]), None)
    date = (last.strftime("%Y-%m-%d") if last
            else datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
            if mtime else "unknown")
    # re-read redundancy: reads of a path beyond the 2nd in one session
    reread_redundant = sum(max(0, c - 2) for c in read_counts.values())
    reread_files = sum(1 for c in read_counts.values() if c >= 3)
    return {
        "sid": fp.stem, "project": fp.parent.name, "date": date,
        "turns": turns, "n_turns": len(turns),
        "marker_hits": marker_hits,
        "reread_redundant": reread_redundant, "reread_files": reread_files,
    }


def _sum(recs, key):
    return sum(r[key] for r in recs)


def audit(proj_base=None, since: str | None = None) -> dict:
    files = iter_transcripts(proj_base)
    sessions: list[dict] = []
    for fp in files:
        s = parse_turns(fp)
        if not s:
            continue
        if since and s["date"] < since:
            continue
        recs = s["turns"]
        s["out"] = _sum(recs, "output_tokens")
        s["in"] = _sum(recs, "input_tokens")
        s["crd"] = _sum(recs, "cache_read_input_tokens")
        s["ccr"] = _sum(recs, "cache_creation_input_tokens")
        s["billable"] = s["in"] + s["out"]
        denom = s["crd"] + s["in"] + s["ccr"]
        s["cache_ratio"] = (s["crd"] / denom * 100.0) if denom else 0.0
        first = recs[0]
        s["first_load"] = first["input_tokens"] + \
            first["cache_creation_input_tokens"]
        sessions.append(s)

    sessions.sort(key=lambda s: s["out"], reverse=True)

    # ---- A2: output-per-turn distribution ----
    all_out_turns = [t["output_tokens"] for s in sessions for t in s["turns"]]
    all_out_turns_sorted = sorted(all_out_turns, reverse=True)
    total_out = sum(all_out_turns)
    n_turns = len(all_out_turns)
    top10pct_n = max(1, n_turns // 10)
    out_in_top10 = sum(all_out_turns_sorted[:top10pct_n])
    a2 = {
        "top_sessions": [
            {"project": s["project"][:30], "sid": s["sid"][:8],
             "out": s["out"], "turns": s["n_turns"], "date": s["date"],
             "cache_ratio": round(s["cache_ratio"], 1)}
            for s in sessions[:8]],
        "n_turns": n_turns,
        "total_out": total_out,
        "median_out_per_turn": statistics.median(all_out_turns) if all_out_turns else 0,
        "mean_out_per_turn": (total_out / n_turns) if n_turns else 0,
        "p95_out_per_turn": (all_out_turns_sorted[int(n_turns * 0.05)]
                             if n_turns else 0),
        "max_out_per_turn": all_out_turns_sorted[0] if all_out_turns_sorted else 0,
        "out_share_top10pct": (out_in_top10 / total_out * 100.0)
        if total_out else 0.0,
    }

    # ---- A3: cache ratio per repo ----
    repo = defaultdict(lambda: {"in": 0, "out": 0, "crd": 0, "ccr": 0,
                                "sessions": 0, "first_loads": []})
    for s in sessions:
        r = repo[s["project"]]
        r["in"] += s["in"]; r["out"] += s["out"]
        r["crd"] += s["crd"]; r["ccr"] += s["ccr"]
        r["sessions"] += 1
        r["first_loads"].append(s["first_load"])
    repo_rows = []
    for name, r in repo.items():
        denom = r["crd"] + r["in"] + r["ccr"]
        cr = (r["crd"] / denom * 100.0) if denom else 0.0
        repo_rows.append({
            "project": name[:40], "sessions": r["sessions"],
            "out": r["out"], "in": r["in"],
            "cache_ratio": round(cr, 1),
            "mean_first_load": int(statistics.mean(r["first_loads"]))
            if r["first_loads"] else 0,
        })
    repo_rows.sort(key=lambda x: x["out"], reverse=True)
    low_cache = sorted(
        [x for x in repo_rows if x["out"] > 500_000 and x["cache_ratio"] < 90.0],
        key=lambda x: x["cache_ratio"])

    # ---- A1: initial load + turns/session ----
    first_loads = [s["first_load"] for s in sessions]
    turns_per = [s["n_turns"] for s in sessions]
    a1 = {
        "mean_first_load": int(statistics.mean(first_loads)) if first_loads else 0,
        "median_first_load": int(statistics.median(first_loads)) if first_loads else 0,
        "max_first_load": max(first_loads) if first_loads else 0,
        "mean_turns_per_session": round(statistics.mean(turns_per), 1)
        if turns_per else 0,
        "median_turns_per_session": statistics.median(turns_per) if turns_per else 0,
        "sessions_over_40_turns": sum(1 for t in turns_per if t > 40),
    }

    # ---- A4: inefficiency ----
    a4 = {
        "sessions_with_reread": sum(1 for s in sessions if s["reread_files"] > 0),
        "total_redundant_rereads": sum(s["reread_redundant"] for s in sessions),
        "sessions_multi_marker": sum(1 for s in sessions if s["marker_hits"] >= 3),
        "top_marker_sessions": sorted(
            [{"project": s["project"][:30], "sid": s["sid"][:8],
              "markers": s["marker_hits"], "turns": s["n_turns"]}
             for s in sessions if s["marker_hits"] >= 3],
            key=lambda x: x["markers"], reverse=True)[:8],
    }

    # ---- A5: hour-of-day burn + concurrency ----
    hour_bucket = defaultdict(lambda: {"out": 0, "sids": set()})
    for s in sessions:
        for t in s["turns"]:
            if not t["ts"]:
                continue
            key = t["ts"].strftime("%Y-%m-%d %H:00")
            hb = hour_bucket[key]
            hb["out"] += t["output_tokens"]
            hb["sids"].add(s["sid"])
    hb_rows = sorted(
        ({"hour": k, "out": v["out"], "sessions": len(v["sids"])}
         for k, v in hour_bucket.items()),
        key=lambda x: x["out"], reverse=True)
    a5 = {
        "peak_hours": hb_rows[:10],
        "n_hour_buckets": len(hb_rows),
        "multi_session_peak_share": (
            sum(1 for x in hb_rows[:20] if x["sessions"] >= 2) / 20.0 * 100.0)
        if hb_rows else 0.0,
    }

    # ---- A6: context% vs output ----
    buckets = {"low": [], "mid": [], "high": []}
    for s in sessions:
        for t in s["turns"]:
            fed = (t["input_tokens"] + t["cache_read_input_tokens"]
                   + t["cache_creation_input_tokens"])
            b = ("low" if fed < CTX_LOW else "mid" if fed < CTX_HIGH else "high")
            buckets[b].append(t["output_tokens"])
    a6 = {b: {"n": len(v),
              "mean_out": round(statistics.mean(v), 0) if v else 0,
              "median_out": statistics.median(v) if v else 0}
          for b, v in buckets.items()}

    life = {"in": _sum(sessions, "in"), "out": _sum(sessions, "out"),
            "crd": _sum(sessions, "crd"), "ccr": _sum(sessions, "ccr")}
    denom = life["crd"] + life["in"] + life["ccr"]
    life["cache_ratio"] = round((life["crd"] / denom * 100.0) if denom else 0.0, 1)

    return {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "n_sessions": len(sessions),
        "lifetime": life,
        "a1": a1, "a2": a2, "a3": {"repo_rows": repo_rows[:15],
                                   "low_cache_outliers": low_cache},
        "a4": a4, "a5": a5, "a6": a6,
    }


def _classify_turn(content) -> dict:
    """Classify one assistant turn's output from its content blocks WITHOUT
    surfacing raw text. Returns category + reducibility signals only.

    Signals: primary tool, biggest content block size, line-uniqueness ratio
    (low = repetitive = structurally reducible), code-fence count."""
    biggest = ""
    biggest_kind = "text"
    tools: list[str] = []
    fence = 0
    if isinstance(content, str):
        biggest = content
        fence = content.count("```")
    elif isinstance(content, list):
        for blk in content:
            if not isinstance(blk, dict):
                continue
            if blk.get("type") == "text" and isinstance(blk.get("text"), str):
                t = blk["text"]
                fence += t.count("```")
                if len(t) > len(biggest):
                    biggest, biggest_kind = t, "text"
            elif blk.get("type") == "tool_use":
                nm = blk.get("name") or "?"
                tools.append(nm)
                inp = blk.get("input") or {}
                for k in ("content", "new_string", "command"):
                    v = inp.get(k)
                    if isinstance(v, str) and len(v) > len(biggest):
                        biggest, biggest_kind = v, f"tool:{nm}"
    lines = [ln for ln in biggest.split("\n") if ln.strip()]
    uniq = (len(set(lines)) / len(lines)) if lines else 1.0
    top_repeat = 0
    if lines:
        counts: dict[str, int] = defaultdict(int)
        for ln in lines:
            counts[ln.strip()] += 1
        top_repeat = max(counts.values())
    primary = "text-only"
    if tools:
        primary = max(set(tools), key=tools.count)
    # category + reducibility verdict
    if primary in ("Write", "Edit", "NotebookEdit") and biggest_kind.startswith("tool"):
        cat, reduce = "code/file-write", "NOT (real deliverable)"
    elif uniq < 0.5 or top_repeat >= 8:
        cat, reduce = "repetitive/dataset", "REDUCIBLE (structural repeat)"
    elif fence >= 2:
        cat, reduce = "code-in-prose", "LOW"
    elif primary == "text-only":
        cat, reduce = "reasoning/report", "PARTIAL (terser, quality risk)"
    else:
        cat, reduce = "mixed/tool-call", "LOW"
    return {"category": cat, "reducibility": reduce, "primary": primary,
            "uniq_ratio": round(uniq, 2), "top_repeat": top_repeat,
            "fence": fence, "big_kind": biggest_kind}


def sample_fat_turns(proj_base=None, top_n: int = 40,
                     min_out: int = 8000) -> dict:
    """Find the fattest output turns and classify each on disk. Emits category
    aggregates so the output-tail reducibility question has EVIDENCE."""
    fat: list[dict] = []
    for fp in iter_transcripts(proj_base):
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = entry.get("message")
            if not isinstance(msg, dict):
                continue
            usage = msg.get("usage")
            if not isinstance(usage, dict):
                continue
            out = usage.get("output_tokens", 0) or 0
            if out < min_out:
                continue
            c = _classify_turn(msg.get("content"))
            c.update({"out": out, "project": fp.parent.name[:28],
                      "sid": fp.stem[:8]})
            fat.append(c)
    fat.sort(key=lambda x: x["out"], reverse=True)
    fat = fat[:top_n]
    cat_agg: dict[str, dict] = defaultdict(lambda: {"turns": 0, "out": 0})
    for f in fat:
        cat_agg[f["category"]]["turns"] += 1
        cat_agg[f["category"]]["out"] += f["out"]
    return {"n": len(fat), "min_out": min_out,
            "turns": fat,
            "by_category": dict(cat_agg)}


def _fmtk(n):
    return f"{n:,}"


def build_report(d: dict) -> str:
    L = []
    L.append("# Token Optimization -- Corpus Structural Audit")
    L.append("")
    L.append(f"**Generated:** {d['generated']}  ")
    L.append(f"**Sessions analyzed:** {d['n_sessions']}  ")
    L.append("**Source:** `~/.claude/projects/*/*.jsonl` per-turn `message.usage` "
             "+ `message.content` (measured, no estimates)  ")
    lf = d["lifetime"]
    L.append(f"**Corpus totals:** in={_fmtk(lf['in'])} out={_fmtk(lf['out'])} "
             f"cache_rd={_fmtk(lf['crd'])} cache_cr={_fmtk(lf['ccr'])} "
             f"cacheR={lf['cache_ratio']}%  ")
    L.append("**Plan:** Claude Max (flat rate) -- real levers are OUTPUT VOLUME "
             "+ CACHE RATIO + CONTEXT EFFICIENCY, not $.")
    L.append("")

    a2 = d["a2"]
    L.append("## A2 -- Output distribution (the dominant cost)")
    L.append("")
    L.append(f"- Usage turns: **{_fmtk(a2['n_turns'])}**, total output "
             f"**{_fmtk(a2['total_out'])}**")
    L.append(f"- Output/turn: median **{_fmtk(a2['median_out_per_turn'])}**, "
             f"mean **{_fmtk(int(a2['mean_out_per_turn']))}**, "
             f"p95 **{_fmtk(a2['p95_out_per_turn'])}**, "
             f"max **{_fmtk(a2['max_out_per_turn'])}**")
    L.append(f"- **{a2['out_share_top10pct']:.1f}%** of all output is produced "
             f"by the fattest 10% of turns")
    L.append("")
    L.append("| Output | Date | Project | sid | Turns | Cache% |")
    L.append("|---|---|---|---|---|---|")
    for s in a2["top_sessions"]:
        L.append(f"| {_fmtk(s['out'])} | {s['date']} | {s['project']} | "
                 f"{s['sid']} | {s['turns']} | {s['cache_ratio']}% |")
    L.append("")

    a3 = d["a3"]
    L.append("## A3 -- Cache ratio per repo (outlier hunt)")
    L.append("")
    L.append("| Project | Sessions | Output | Cache% | Mean 1st-load |")
    L.append("|---|---|---|---|---|")
    for r in a3["repo_rows"]:
        L.append(f"| {r['project']} | {r['sessions']} | {_fmtk(r['out'])} | "
                 f"{r['cache_ratio']}% | {_fmtk(r['mean_first_load'])} |")
    L.append("")
    if a3["low_cache_outliers"]:
        L.append("**Low-cache outliers (>500k output, <90% cache):**")
        for r in a3["low_cache_outliers"]:
            L.append(f"- `{r['project']}` -- {r['cache_ratio']}% cache, "
                     f"{_fmtk(r['out'])} output")
    else:
        L.append("**No low-cache outliers.** Every repo with >500k output holds "
                 ">=90% cache ratio. Cache is not the lever.")
    L.append("")

    a1 = d["a1"]
    L.append("## A1 -- Initial context load + session shape")
    L.append("")
    L.append(f"- First-turn load (system prompt + skills + CLAUDE.md, mostly "
             f"cache-creation): mean **{_fmtk(a1['mean_first_load'])}**, "
             f"median **{_fmtk(a1['median_first_load'])}**, "
             f"max **{_fmtk(a1['max_first_load'])}**")
    L.append(f"- Turns/session: mean **{a1['mean_turns_per_session']}**, "
             f"median **{a1['median_turns_per_session']}**, "
             f"**{a1['sessions_over_40_turns']}** sessions over 40 turns")
    L.append("")

    a4 = d["a4"]
    L.append("## A4 -- Inefficiency patterns")
    L.append("")
    L.append(f"- Sessions re-reading a file >=3x: **{a4['sessions_with_reread']}** "
             f"({_fmtk(a4['total_redundant_rereads'])} redundant re-reads total; "
             "note: re-read tool_results are cache-side, low $ but live-window churn)")
    L.append(f"- Sessions with >=3 FASE-1/Reality-Scan/PREFLIGHT markers "
             f"(possible in-session duplication): **{a4['sessions_multi_marker']}**")
    if a4["top_marker_sessions"]:
        L.append("")
        L.append("| Project | sid | Markers | Turns |")
        L.append("|---|---|---|---|")
        for s in a4["top_marker_sessions"]:
            L.append(f"| {s['project']} | {s['sid']} | {s['markers']} | "
                     f"{s['turns']} |")
    L.append("")

    a5 = d["a5"]
    L.append("## A5 -- Hour-of-day burn + parallel-session hypothesis")
    L.append("")
    L.append(f"- Distinct (date,hour) buckets: **{a5['n_hour_buckets']}**")
    L.append(f"- Of the top-20 output hours, **{a5['multi_session_peak_share']:.0f}%** "
             "had >=2 sessions active concurrently")
    L.append("")
    L.append("| Hour (UTC) | Output | Concurrent sessions |")
    L.append("|---|---|---|")
    for x in a5["peak_hours"]:
        L.append(f"| {x['hour']} | {_fmtk(x['out'])} | {x['sessions']} |")
    L.append("")

    a6 = d["a6"]
    L.append("## A6 -- Context size vs output (is a big window buying value?)")
    L.append("")
    L.append("| Fed context | Turns | Mean output | Median output |")
    L.append("|---|---|---|---|")
    for label, key in (("<60k (low)", "low"), ("60-120k (mid)", "mid"),
                       (">120k (high)", "high")):
        b = a6[key]
        L.append(f"| {label} | {_fmtk(b['n'])} | {_fmtk(int(b['mean_out']))} | "
                 f"{_fmtk(b['median_out'])} |")
    L.append("")
    L.append("---")
    L.append("*Generated by tools/token_corpus_audit.py -- FASE -1 corpus audit.*")
    L.append("")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--report", default=None)
    ap.add_argument("--since", default=None)
    ap.add_argument("--proj-base", default=None)
    ap.add_argument("--sample-fat", type=int, default=0,
                    help="classify the top-N fattest output turns and exit")
    args = ap.parse_args(argv)
    if args.sample_fat:
        s = sample_fat_turns(proj_base=args.proj_base, top_n=args.sample_fat)
        print(f"sampled {s['n']} turns (output >= {_fmtk(s['min_out'])})\n")
        print("by category (output tokens in the fat tail):")
        for cat, v in sorted(s["by_category"].items(),
                             key=lambda kv: kv[1]["out"], reverse=True):
            print(f"  {cat:22s} turns={v['turns']:3d}  out={_fmtk(v['out'])}")
        print("\ntop 20 fattest turns:")
        print(f"  {'out':>7} {'category':20} {'primary':10} "
              f"{'uniq':>4} {'rep':>4}  project/sid")
        for f in s["turns"][:20]:
            print(f"  {f['out']:>7} {f['category']:20} {f['primary']:10} "
                  f"{f['uniq_ratio']:>4} {f['top_repeat']:>4}  "
                  f"{f['project']}/{f['sid']}")
        return 0
    d = audit(proj_base=args.proj_base, since=args.since)
    print(f"sessions: {d['n_sessions']}")
    print(f"lifetime out={_fmtk(d['lifetime']['out'])} "
          f"cacheR={d['lifetime']['cache_ratio']}%")
    print(f"A2 output/turn median={_fmtk(d['a2']['median_out_per_turn'])} "
          f"top10%share={d['a2']['out_share_top10pct']:.1f}%")
    print(f"A3 low-cache outliers: {len(d['a3']['low_cache_outliers'])}")
    print(f"A4 reread-sessions={d['a4']['sessions_with_reread']} "
          f"multi-marker={d['a4']['sessions_multi_marker']}")
    print(f"A6 out low/mid/high mean="
          f"{int(d['a6']['low']['mean_out'])}/"
          f"{int(d['a6']['mid']['mean_out'])}/"
          f"{int(d['a6']['high']['mean_out'])}")
    if args.report:
        out = Path(args.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build_report(d), encoding="utf-8")
        print(f"report -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
