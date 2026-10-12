"""Carry by kind for one epoch (stream-json or transcript), in tokens.

Carry = sum over calls of (ctx_k - ctx_1). Image carry is exact per image (w*h/750, see image_carry.py). The rest
is text carry, split across kinds by each item's chars x rides (an item appended before call k rides calls k..N).
Kinds: tool_result text by tool, assistant tool_use input, assistant text/thinking, other user text.
Usage: python carry_by_kind.py <stream.jsonl>
"""
import json, sys
from collections import defaultdict
from image_carry import dims, images_in, tokens


def main(path: str) -> dict:
    calls, seen, items, tool_of = [], set(), [], {}
    for line in open(path, encoding="utf-8"):
        try:
            o = json.loads(line)
        except ValueError:
            continue
        if o.get("isSidechain"):
            continue
        m = o.get("message") or {}
        content = m.get("content") if isinstance(m.get("content"), list) else []
        if o.get("type") == "assistant":
            if m.get("id") and m["id"] not in seen and m.get("usage"):
                seen.add(m["id"])
                u = m["usage"]
                calls.append(u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0))
            for b in content:
                if b.get("type") == "tool_use":
                    tool_of[b.get("id")] = b.get("name", "?")
                    items.append((len(calls), "tool_use_input", len(json.dumps(b.get("input", {})))))
                elif b.get("type") in ("text", "thinking"):
                    items.append((len(calls), "assistant_text", len(b.get("text") or b.get("thinking") or "")))
        elif o.get("type") == "user":
            for b in content:
                if b.get("type") == "tool_result":
                    c = b.get("content")
                    n = len(c) if isinstance(c, str) else sum(len(x.get("text", "")) for x in (c or []) if isinstance(x, dict))
                    items.append((len(calls), f"result:{tool_of.get(b.get('tool_use_id'), '?')}", n))
                    imgs = []
                    images_in(c, imgs)
                    for d in imgs:
                        wh = dims(d)
                        items.append((len(calls), "image_tok", tokens(*wh) if wh else 0))
                elif b.get("type") == "text":
                    items.append((len(calls), "user_text", len(b.get("text", ""))))
    n = len(calls)
    carry = sum(c - calls[0] for c in calls) if calls else 0
    img = sum(v * (n - k) for k, kind, v in items if kind == "image_tok")
    chars = defaultdict(int)
    for k, kind, v in items:
        if kind != "image_tok":
            chars[kind] += v * (n - k)
    total_chars = sum(chars.values()) or 1
    text = carry - img
    kinds = {kind: round(text * c / total_chars) for kind, c in sorted(chars.items(), key=lambda x: -x[1])}
    processed = sum(calls)
    return {"calls": n, "processed": processed, "floor_total": calls[0] * n if calls else 0, "carry": carry,
            "image_carry": img, "text_carry": text,
            "shares_of_processed": {"floor": round(calls[0] * n / processed, 3), "image": round(img / processed, 3),
                                    **{k: round(v / processed, 3) for k, v in kinds.items()}}}


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1]), indent=1))
