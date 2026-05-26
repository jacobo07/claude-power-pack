#!/usr/bin/env python3
"""TIS Capa 3 -- handoff summarizer.

Takes the active session's TIS log and emits a <context_summary>
block describing what to compress/cache for the next session.

Reality Contract: when there are fewer than 3 calls in the session,
the report DOES NOT silently emit zeros -- it sets estimated_savings
to 0 AND surfaces `recommended_action: "INSUFFICIENT_TELEMETRY"`
with a concrete explanation. Zero with reason vs zero-without-reason
is the data-quality contract C8 enforces.
"""
from __future__ import annotations
import argparse
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tis  # noqa: E402
import tis_report  # noqa: E402  (for _cost_usd / PRICING)


HANDOFF_DIR = tis.LOGS_DIR
MIN_CALLS_FOR_RECOMMENDATION = 3


def _short(text: str, n: int = 60) -> str:
    text = text.replace("\n", " ")
    return text if len(text) <= n else text[: n - 1] + "..."


def _atomic_write(path: Path, text: str) -> None:
    import os
    import tempfile
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp",
                               dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def build_handoff(session_id: str, entries: list) -> dict:
    """Build the structured handoff report. Returns a dict with all
    fields populated -- the renderer is the only place that converts
    to the <context_summary> markdown block."""
    total_in = sum(e.get("input_tokens", 0) for e in entries)
    total_out = sum(e.get("output_tokens", 0) for e in entries)
    total_cr = sum(e.get("cache_read_tokens", 0) for e in entries)
    total_cc = sum(e.get("cache_creation_tokens", 0) for e in entries)
    cost = sum(tis_report._cost_usd(e) for e in entries)
    denom = total_in + total_cr
    cache_ratio = (total_cr / denom * 100.0) if denom else 0.0

    # Top-3 expensive by input_tokens (ties broken by output_tokens).
    ranked = sorted(
        entries,
        key=lambda e: (e.get("input_tokens", 0), e.get("output_tokens", 0)),
        reverse=True,
    )
    top_3 = ranked[:3]

    # Compression candidates: skills repeated >=2 times with the same
    # call_label (telemetry-detectable cache_control:ephemeral targets).
    label_counts = Counter()
    label_in = defaultdict(int)
    for e in entries:
        key = (e.get("skill_name", ""), e.get("call_label", ""))
        label_counts[key] += 1
        label_in[key] += e.get("input_tokens", 0)

    candidates = []
    for (skill, label), count in label_counts.items():
        if count >= 2 and label_in[(skill, label)] > 0:
            est_save = label_in[(skill, label)] - label_in[(skill, label)] // count
            candidates.append({
                "skill_name": skill,
                "call_label": label,
                "repetitions": count,
                "input_tokens_aggregate": label_in[(skill, label)],
                "estimated_savings_tokens": est_save,
                "reason": "repeated call with identical label -- "
                          "cache_control:ephemeral candidate",
            })

    # Also flag outputs > 500 tokens as summarisation candidates.
    for e in entries:
        if e.get("output_tokens", 0) > 500:
            candidates.append({
                "skill_name": e.get("skill_name", ""),
                "call_label": e.get("call_label", ""),
                "output_tokens": e.get("output_tokens", 0),
                "estimated_savings_tokens": e.get("output_tokens", 0) // 2,
                "reason": "output exceeds 500 tokens -- summarisation "
                          "candidate before next handoff",
            })

    estimated_savings = sum(c.get("estimated_savings_tokens", 0)
                            for c in candidates)

    # Recommended action with honest fallback (no silent zeros).
    if len(entries) < MIN_CALLS_FOR_RECOMMENDATION:
        recommended_action = (
            f"INSUFFICIENT_TELEMETRY: only {len(entries)} call(s) recorded "
            f"this session (< {MIN_CALLS_FOR_RECOMMENDATION} required). "
            f"No optimisation recommended; re-run the handoff after more "
            f"skill activations."
        )
        estimated_savings = 0
    elif not candidates:
        recommended_action = (
            "NO_CANDIDATES_DETECTED: all calls had distinct labels and "
            "outputs <= 500 tokens. Telemetry is healthy; no compression "
            "opportunities identified this session."
        )
    else:
        top_candidate = max(candidates,
                            key=lambda c: c.get("estimated_savings_tokens", 0))
        recommended_action = (
            f"COMPRESS '{top_candidate['skill_name']}' "
            f"({top_candidate.get('reason', '')[:60]}) -- "
            f"estimated savings {top_candidate['estimated_savings_tokens']} "
            f"tokens, ~{(top_candidate['estimated_savings_tokens'] / max(total_in, 1) * 100):.1f}%"
            f" of input."
        )

    return {
        "session_id": session_id,
        "generated_iso": datetime.now(timezone.utc).isoformat(),
        "calls_made": len(entries),
        "tokens_consumed_this_session": total_in + total_out,
        "input_tokens": total_in,
        "output_tokens": total_out,
        "cache_read_tokens": total_cr,
        "cache_creation_tokens": total_cc,
        "cache_hit_ratio_pct": round(cache_ratio, 2),
        "estimated_cost_usd": round(cost, 5),
        "top_3_expensive_calls": [
            {
                "skill_name": e.get("skill_name", ""),
                "call_label": e.get("call_label", ""),
                "input_tokens": e.get("input_tokens", 0),
                "output_tokens": e.get("output_tokens", 0),
            }
            for e in top_3
        ],
        "compression_candidates": candidates,
        "estimated_savings_next_session_tokens": estimated_savings,
        "recommended_action": recommended_action,
    }


def render_markdown(report: dict) -> str:
    lines = []
    lines.append(f"<context_summary session=\"{report['session_id']}\">")
    lines.append(f"generated_iso: {report['generated_iso']}")
    lines.append(f"calls_made: {report['calls_made']}")
    lines.append(f"tokens_consumed_this_session: "
                 f"{report['tokens_consumed_this_session']}")
    lines.append(f"input_tokens: {report['input_tokens']}")
    lines.append(f"output_tokens: {report['output_tokens']}")
    lines.append(f"cache_hit_ratio_pct: {report['cache_hit_ratio_pct']}")
    lines.append(f"estimated_cost_usd: {report['estimated_cost_usd']}")
    lines.append("top_3_expensive_calls:")
    for i, c in enumerate(report["top_3_expensive_calls"], 1):
        lines.append(f"  {i}. {c['skill_name']} ({c['call_label']}) "
                     f"-- input={c['input_tokens']} output={c['output_tokens']}")
    if not report["top_3_expensive_calls"]:
        lines.append("  (none)")
    lines.append("compression_candidates:")
    for c in report["compression_candidates"]:
        lines.append(f"  - [{c.get('skill_name', '?')}] "
                     f"{_short(c.get('reason', ''), 70)} "
                     f"(saves ~{c.get('estimated_savings_tokens', 0)} tokens)")
    if not report["compression_candidates"]:
        lines.append("  (none detected)")
    lines.append(f"estimated_savings_next_session_tokens: "
                 f"{report['estimated_savings_next_session_tokens']}")
    lines.append(f"recommended_action: {report['recommended_action']}")
    lines.append("</context_summary>")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session", help="override session id (default: active)")
    ap.add_argument("--out-dir", default=str(HANDOFF_DIR),
                    help="output directory (default: vault/token_logs)")
    args = ap.parse_args(argv)

    sid = args.session or tis.get_session_id()
    entries = tis.read_log(session_id=sid)
    report = build_handoff(sid, entries)
    body = render_markdown(report)

    print(body, end="")

    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out_path = Path(args.out_dir) / f"handoff_{sid}_{ts}.md"
    _atomic_write(out_path, body)
    print(f"\nwrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
