#!/usr/bin/env python3
"""Context floor census: what a session's call-1 floor and each later call's growth are made of.

session_autopsy.py answers HOW MUCH a session re-sent (floor, growth, cost). This answers OF WHAT,
from the transcript alone (deterministic, read-only, no hook is run):

- floor: every item the model saw before its first call, sized in chars and ranked -- each
  instruction file by path, the skill / agent / deferred-tool listings, MCP instructions, each
  hook's injected text, the first prompt, the host system prompt. The measured call-1 usage
  (input + cache_creation + cache_read) minus the estimate of those items is reported as
  `unattributed`: built-in tool schemas and framing the transcript never records, plus error.
- history: for each call k+1, its usage delta over call k, minus call k's output, is charged to the
  items that arrived in between (tool results by tool name, attachments by type, prompts), split by
  chars. A falling total (compaction, rotation) is a reset, never charged.

Token figures for floor items are ESTIMATES (chars / ratio). Measured figures are the usage totals
and the history charges, which are usage deltas. The ratio is explicit, the default, or a median
calibrated from single-producer history steps when at least MIN_CALIBRATION_SAMPLES exist.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Optional

PROJECTS_DIR = Path.home() / ".claude" / "projects"
DEFAULT_CHARS_PER_TOKEN = 3.6
MIN_CALIBRATION_SAMPLES = 3
MIN_CALIBRATION_CHARS = 1000  # a short result is dominated by framing, not content
CALIBRATION_DOMINANCE = 0.9   # a step counts when one source carries this share of its chars
HOST_SOURCES = ("system_prompt(host)",)  # live in the cross-session cached prefix


def _rendered_chars(row: dict) -> int:
    rendered = row.get("rendered")
    if not isinstance(rendered, list):
        return 0
    return sum(len(x.get("content", "")) for x in rendered if isinstance(x, dict))


def _content_chars(content) -> tuple[int, int]:
    """(text chars, image blocks) of a message or tool_result content."""
    if isinstance(content, str):
        return len(content), 0
    chars = images = 0
    if isinstance(content, list):
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "image":
                images += 1
            elif b.get("type") == "tool_result":
                c, i = _content_chars(b.get("content"))
                chars, images = chars + c, images + i
            else:
                chars += len(b.get("text", "") or "")
    return chars, images


def _usage_total(usage: dict) -> int:
    return sum(int(usage.get(k) or 0) for k in
               ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))


def _items(row: dict, tool_names: dict, seen_results: set) -> list[tuple[str, int]]:
    """Model-visible items a non-assistant row contributes, as (source label, chars)."""
    t = row.get("type")
    if t == "attachment":
        a = row.get("attachment") if isinstance(row.get("attachment"), dict) else {}
        at = a.get("type", "?")
        if at == "prompt_snapshot":
            sp = a.get("systemPrompt")
            n = sum(len(x) for x in sp if isinstance(x, str)) if isinstance(sp, list) else 0
            return [("system_prompt(host)", n)] if n else []
        n = _rendered_chars(row)
        if not n:
            return []  # not rendered = not sent to the model
        if at == "instructions":
            out, used = [], 0
            for f in a.get("files") or []:
                c = len(f.get("content", "") or "")
                out.append((f"instructions:{f.get('path', '?')}", c))
                used += c
            if n > used:
                out.append(("instructions:(wrapper)", n - used))
            return out
        if at == "hook_additional_context":
            return [(f"hook:{a.get('hookEvent', '?')}:{a.get('hookName', '?')}", n)]
        return [(f"attachment:{at}", n)]
    if t == "user":
        msg = row.get("message") if isinstance(row.get("message"), dict) else {}
        content = msg.get("content")
        if isinstance(content, list) and any(isinstance(b, dict) and b.get("type") == "tool_result"
                                             for b in content):
            out = []
            for b in content:
                if not isinstance(b, dict) or b.get("type") != "tool_result":
                    continue
                tid = b.get("tool_use_id")
                if tid in seen_results:
                    continue
                seen_results.add(tid)
                c, _ = _content_chars(b.get("content"))
                out.append((f"tool_result:{tool_names.get(tid, '?')}", c))
            return out
        c, _ = _content_chars(content)
        if not c:
            return []
        return [("user_prompt:meta" if row.get("isMeta") else "user_prompt", c)]
    return []


def census(path: Path, chars_per_token: Optional[float] = None) -> dict:
    path = Path(path)
    calls: list[dict] = []          # {id, total, output}
    call_index: dict[str, int] = {}
    floor_items: list[tuple[str, int]] = []
    gaps: dict[int, list[tuple[str, int]]] = {}   # items after call k (0-based) -> charged to call k+1
    tool_names: dict[str, str] = {}
    seen_results: set = set()
    timed_out: list[dict] = []
    images = 0

    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if not isinstance(row, dict) or row.get("isSidechain"):
                continue
            if row.get("type") == "assistant":
                msg = row.get("message") if isinstance(row.get("message"), dict) else {}
                for b in msg.get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        tool_names[b.get("id")] = b.get("name") or "?"
                usage = msg.get("usage")
                mid = msg.get("id")
                if not isinstance(usage, dict) or not mid:
                    continue
                if mid in call_index:
                    calls[call_index[mid]]["output"] = int(usage.get("output_tokens") or 0)
                else:
                    call_index[mid] = len(calls)
                    calls.append({"id": mid, "total": _usage_total(usage),
                                  "cache_read": int(usage.get("cache_read_input_tokens") or 0),
                                  "output": int(usage.get("output_tokens") or 0)})
                continue
            a = row.get("attachment") if isinstance(row.get("attachment"), dict) else {}
            if row.get("type") == "attachment" and a.get("type") == "hook_cancelled" and a.get("timedOut") \
                    and not calls:
                timed_out.append({"hook": a.get("hookName"), "event": a.get("hookEvent"),
                                  "timeout_ms": a.get("timeoutMs")})
            if row.get("type") == "user":
                images += _content_chars((row.get("message") or {}).get("content"))[1]
            items = _items(row, tool_names, seen_results)
            if not calls:
                floor_items.extend(items)
            else:
                # A later prompt_snapshot re-records the system prompt; it adds no message content.
                gaps.setdefault(len(calls) - 1, []).extend(i for i in items if i[0] not in HOST_SOURCES)

    # History: charge each positive delta to the items that arrived since the previous call.
    by_producer: dict[str, float] = {}
    resets, samples = [], []
    output_carried = sum(c["output"] for c in calls[:-1])  # each is re-sent to the next call
    for k in range(1, len(calls)):
        delta = calls[k]["total"] - calls[k - 1]["total"]
        if delta < 0:
            resets.append({"call": k + 1, "delta": delta})
            continue
        charge = delta - calls[k - 1]["output"]
        items = [(s, c) for s, c in gaps.get(k - 1, []) if c > 0]
        chars = sum(c for _, c in items)
        if charge <= 0 or not chars:
            continue
        for s, c in items:
            by_producer[s] = by_producer.get(s, 0.0) + charge * c / chars
        per_source: dict[str, int] = {}
        for s, c in items:
            per_source[s] = per_source.get(s, 0) + c
        if max(per_source.values()) >= CALIBRATION_DOMINANCE * chars and chars >= MIN_CALIBRATION_CHARS:
            samples.append(chars / charge)

    # The calibrated ratio comes from tool output (paths, JSON, logs), which tokenizes denser than
    # the prose of instruction files, so it never sizes floor items; it only gives the second bound.
    calibrated = round(statistics.median(samples), 2) if samples else None
    if chars_per_token:
        ratio = {"value": float(chars_per_token), "source": "explicit"}
    else:
        ratio = {"value": DEFAULT_CHARS_PER_TOKEN, "source": "default"}

    merged: dict[str, int] = {}
    for s, c in floor_items:
        merged[s] = merged.get(s, 0) + c
    sources = [{"source": s, "chars": c, "est_tokens": round(c / ratio["value"])}
               for s, c in sorted(merged.items(), key=lambda kv: (-kv[1], kv[0]))]
    attributed = sum(merged.values())
    estimated = round(attributed / ratio["value"])
    measured = calls[0]["total"] if calls else None
    # Call 1's cache_read is the prefix shared across sessions (tool schemas + system prompt);
    # the rest of the floor was written for this session and is what CPP-authored items can explain.
    prefix = calls[0]["cache_read"] if calls else None
    session_chars = sum(c for s, c in merged.items() if s not in HOST_SOURCES)
    session_est = round(session_chars / ratio["value"])
    dense_bound = None
    if measured is not None and calibrated and len(samples) >= MIN_CALIBRATION_SAMPLES:
        dense_bound = measured - prefix - round(session_chars / calibrated)

    return {
        "session": path.stem,
        "calls": len(calls),
        "verdict": "MEASURED" if calls else "NO_CALL",
        "chars_per_token": ratio,
        "calibration": {"samples": len(samples), "median_chars_per_token": calibrated},
        "floor": {
            "measured_tokens": measured,
            "attributed_chars": attributed,
            "estimated_tokens": estimated,
            "unattributed_tokens": (measured - estimated) if measured is not None else None,
            "host_prefix_tokens": prefix,
            "session_tokens": (measured - prefix) if measured is not None else None,
            "session_estimated_tokens": session_est,
            "session_unattributed_tokens": (measured - prefix - session_est) if measured is not None else None,
            "session_unattributed_at_calibrated": dense_bound,
            "sources": sources,
            "hooks_timed_out": timed_out,
        },
        "history": {
            "by_producer": {s: round(v) for s, v in sorted(by_producer.items(), key=lambda kv: -kv[1])},
            "assistant_output_tokens": output_carried,
            "resets": resets,
            "last_call_tokens": calls[-1]["total"] if calls else None,
            "image_blocks": images,
        },
    }


def _short(source: str) -> str:
    home = str(Path.home())
    return source.replace(home, "~")


def render_markdown(results: list[dict], top: int = 15) -> str:
    out = []
    for r in results:
        fl, hi = r["floor"], r["history"]
        ratio = r["chars_per_token"]
        out.append(f"### {r['session'][:8]}: call-1 floor {fl['measured_tokens'] or 0:,} measured, "
                   f"{r['calls']} calls (ratio {ratio['value']} chars/token, {ratio['source']})")
        out.append("")
        out.append("| source | chars | est. tokens |")
        out.append("|---|---:|---:|")
        for s in fl["sources"][:top]:
            out.append(f"| {_short(s['source'])} | {s['chars']:,} | {s['est_tokens']:,} |")
        rest = fl["sources"][top:]
        if rest:
            out.append(f"| ({len(rest)} more) | {sum(s['chars'] for s in rest):,} | "
                       f"{sum(s['est_tokens'] for s in rest):,} |")
        un = fl["unattributed_tokens"]
        out.append(f"| unattributed (tool schemas, framing, estimate error) | - | "
                   f"{'n/a' if un is None else f'{un:,}'} |")
        if fl["measured_tokens"] is not None:
            out.append("")
            out.append(f"Split: host prefix (call-1 cache_read, shared across sessions) "
                       f"{fl['host_prefix_tokens']:,}; session-specific {fl['session_tokens']:,}, of which "
                       f"{fl['session_estimated_tokens']:,} estimated from the items above and "
                       f"{fl['session_unattributed_tokens']:,} unattributed"
                       + ("." if fl["session_unattributed_at_calibrated"] is None else
                          f" ({fl['session_unattributed_at_calibrated']:,} at the history-calibrated "
                          f"{r['calibration']['median_chars_per_token']} chars/token, the dense bound)."))
        if fl["hooks_timed_out"]:
            out.append("")
            out.append("Hooks timed out before call 1 (their text never arrived): "
                       + ", ".join(f"{h['hook']} ({h['timeout_ms']} ms)" for h in fl["hooks_timed_out"]))
        out.append("")
        out.append(f"History charged across calls (measured deltas; assistant output carried "
                   f"{hi['assistant_output_tokens']:,}; resets {len(hi['resets'])}):")
        out.append("")
        out.append("| producer | tokens |")
        out.append("|---|---:|")
        for s, v in list(hi["by_producer"].items())[:top]:
            out.append(f"| {s} | {v:,} |")
        out.append("")
    return "\n".join(out)


def _resolve(arg: str) -> Path:
    p = Path(arg)
    if p.is_file():
        return p
    hits = sorted(PROJECTS_DIR.glob(f"*/{arg}*.jsonl"))
    if not hits:
        raise SystemExit(f"no transcript matches {arg!r} under {PROJECTS_DIR}")
    return hits[0]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sessions", nargs="+", help="transcript paths or session ids (prefix ok)")
    ap.add_argument("--chars-per-token", type=float, default=None)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--json", metavar="PATH", help="also write the full census as JSON")
    a = ap.parse_args(argv)
    results = [census(_resolve(s), a.chars_per_token) for s in a.sessions]
    print(render_markdown(results, a.top))
    if a.json:
        Path(a.json).write_text(json.dumps(results, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
