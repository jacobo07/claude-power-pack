"""Spend meter: processed tokens (input+cache_creation+cache_read+output), dedup by message id, for ONE transcript path.
usage: python meter.py PATH.jsonl"""
import json, sys
seen = {}
for line in open(sys.argv[1], encoding="utf-8", errors="replace"):
    if '"usage"' not in line: continue
    try: o = json.loads(line)
    except ValueError: continue
    if o.get("type") != "assistant": continue
    m = o.get("message") or {}; u = m.get("usage")
    if not u: continue
    k = m.get("id") or o.get("requestId") or o.get("uuid")
    v = (u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0)
    out = u.get("output_tokens") or 0
    if k in seen: seen[k][1] = max(seen[k][1], out); continue
    seen[k] = [v, out]
ctx = sum(v[0] for v in seen.values()); out = sum(v[1] for v in seen.values())
print(f"calls {len(seen)} processed {ctx+out:,} (ctx {ctx:,} out {out:,})")