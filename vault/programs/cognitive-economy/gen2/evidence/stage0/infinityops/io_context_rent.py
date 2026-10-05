"""Context-rent attribution for the odr-device-trust mission workers (main transcripts only).

For each worker: the context of a call = input + cache_creation + cache_read of that assistant message.
The first call's context is the startup floor. Everything appended to the transcript after it is history;
each appended item is classified, sized in characters, and charged one unit of rent for every later call
in the same worker (workers ran one long turn each: no compaction, no continuation). Characters are
converted to tokens with one calibration per worker: (last context - first context) / chars appended
before the last call. Subagent transcripts are reported separately (they are their own contexts).
"""
import glob
import json
import os
import statistics
from collections import defaultdict

PROJ = os.path.expanduser(r"~\.claude\projects\C--Users-User-Apps-io-device-trust")
WORKERS = ["be2a71eb", "50d3a9f0", "affe87e4", "63bc3ed8", "dc79aa64", "5f5bc46f", "4f1b398d", "dfc0acda"]
KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


def classify(o):
    """Yield (category, chars) for one transcript line that enters the model context."""
    t = o.get("type")
    msg = o.get("message") or {}
    content = msg.get("content")
    if t == "assistant" and isinstance(content, list):
        for b in content:
            bt = b.get("type")
            if bt == "text":
                yield "assistant_text", len(b.get("text", ""))
            elif bt == "tool_use":
                name = b.get("name", "?")
                cat = "agent_spawn" if name in ("Agent", "Task") else "tool_call_input"
                yield cat, len(json.dumps(b.get("input", {})))
            elif bt == "thinking":
                yield "thinking", len(b.get("thinking", ""))
    elif t == "user":
        if isinstance(content, str):
            yield "user_or_injected_text", len(content)
        elif isinstance(content, list):
            for b in content:
                if b.get("type") == "tool_result":
                    c = b.get("content")
                    n = len(c) if isinstance(c, str) else len(json.dumps(c))
                    yield "tool_result", n
                elif b.get("type") == "text":
                    yield "user_or_injected_text", len(b.get("text", ""))
    elif t in ("attachment", "system"):
        yield "injected_attachment", len(json.dumps(o.get("attachment") or o.get("content") or ""))


grand = defaultdict(float)
floors, all_ctx = [], []
calls_total = 0
for w in WORKERS:
    f = glob.glob(os.path.join(PROJ, f"{w}-*.jsonl"))[0]
    items = []          # (call_index_at_append, category, chars)
    ctxs = []
    seen = set()
    with open(f, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            msg = o.get("message") or {}
            u = msg.get("usage")
            if o.get("type") == "assistant" and u:
                mid = msg.get("id") or o.get("uuid")
                if mid not in seen:
                    seen.add(mid)
                    ctxs.append(sum(int(u.get(k) or 0) for k in KEYS))
            for cat, n in classify(o):
                items.append((len(ctxs), cat, n))
    n_calls = len(ctxs)
    calls_total += n_calls
    floors.append(ctxs[0])
    all_ctx.extend(ctxs)
    appended = sum(n for i, _, n in items if 1 <= i < n_calls)
    tpc = (ctxs[-1] - ctxs[0]) / appended if appended else 0.0
    grand["floor_rent"] += ctxs[0] * n_calls
    for i, cat, n in items:
        if i < 1:
            continue                      # part of the first call = floor
        later = n_calls - i               # calls that carried it
        if later > 0:
            grand[cat] += n * tpc * later
    grand["measured_context_total"] += sum(ctxs)
    print(f"{w}: calls={n_calls:4} floor={ctxs[0]:7,} median={int(statistics.median(ctxs)):7,} "
          f"peak={max(ctxs):7,} tok/char={tpc:.3f}")

print()
print(f"calls={calls_total} floor mean={int(statistics.mean(floors)):,} min={min(floors):,} max={max(floors):,}")
print(f"context/call mean={int(statistics.mean(all_ctx)):,} median={int(statistics.median(all_ctx)):,} "
      f"p90={int(sorted(all_ctx)[int(0.9*len(all_ctx))]):,} peak={max(all_ctx):,}")
total = grand.pop("measured_context_total")
attributed = sum(grand.values())
print(f"measured context total (main transcripts) = {total:,.0f}; attributed = {attributed:,.0f} "
      f"({attributed/total*100:.1f}% of measured)")
for k, v in sorted(grand.items(), key=lambda kv: -kv[1]):
    print(f"  {k:24} {v:16,.0f}  {v/total*100:5.1f}%")
