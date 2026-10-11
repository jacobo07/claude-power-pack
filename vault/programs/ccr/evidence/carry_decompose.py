"""Decompose a Claude Code transcript's intra-epoch carry by category (offline, read-only).

Per API call (assistant message id with usage) it records the cumulative chars of every row
category before that call; carry[cat] = sum over calls. Images count as a fixed estimate.
"""
import json
import sys
from collections import defaultdict

IMG_CHARS = 6000  # ~1.5K tokens per image, an estimate; reported separately so it can be discarded


def blocks(content):
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return content or []


def size(b):
    t = b.get("type")
    if t == "image":
        return IMG_CHARS
    if t == "text":
        return len(b.get("text", ""))
    if t == "tool_use":
        return len(json.dumps(b.get("input", {})))
    if t == "thinking":
        return 0  # not carried by the API on later calls
    if t == "tool_result":
        return sum(size(x) for x in blocks(b.get("content")))
    return len(json.dumps(b))


def main(path):
    tool_names = {}
    cum = defaultdict(int)
    carry = defaultdict(int)
    calls = []
    seen_ids = set()
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            typ = r.get("type")
            m = r.get("message") or {}
            if typ == "assistant":
                mid = m.get("id")
                u = m.get("usage") or {}
                if mid and mid not in seen_ids and u:
                    seen_ids.add(mid)
                    total = u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                    calls.append(total)
                    for k, v in cum.items():
                        carry[k] += v
                for b in blocks(m.get("content")):
                    if b.get("type") == "tool_use":
                        tool_names[b.get("id")] = b.get("name", "?")
                    cat = "assistant:" + b.get("type", "?")
                    cum[cat] += size(b)
            elif typ == "user":
                for b in blocks(m.get("content")):
                    if b.get("type") == "tool_result":
                        name = tool_names.get(b.get("tool_use_id"), "?")
                        for x in blocks(b.get("content")):
                            cat = f"tool_result:{name}" + (":image" if x.get("type") == "image" else "")
                            cum[cat] += size(x)
                    else:
                        cum["user:" + b.get("type", "?")] += size(b)
            elif typ == "attachment":
                a = r.get("attachment") or {}
                # Transcript-only records: absent from the worker's CCR prompt.attachment receipt (d6343597),
                # so never model-facing. Any other type is counted.
                if a.get("type") in ("prompt_snapshot", "hook_success", "hook_cancelled"):
                    continue
                cum["attachment:" + str(a.get("type", "?"))] += len(json.dumps(a))
    tot = sum(carry.values()) or 1
    print(json.dumps({
        "calls": len(calls), "first_call": calls[0] if calls else None, "last_call": calls[-1] if calls else None,
        "processed_tokens": sum(calls),
        "carry_chars_total": tot,
        "carry_share": {k: round(v / tot, 3) for k, v in sorted(carry.items(), key=lambda kv: -kv[1])[:15]},
        "final_chars": dict(sorted(cum.items(), key=lambda kv: -kv[1])[:15]),
    }, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
