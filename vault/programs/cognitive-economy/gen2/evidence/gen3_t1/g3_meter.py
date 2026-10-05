"""Self-meter: processed tokens (input + cache_write + cache_read + output, deduped by message id) of the newest subagent transcript."""
import glob, json, os
D = os.path.expanduser(r"~\.claude\projects\C--Users-User--claude-skills-claude-power-pack\87601e81-fc6a-4199-a22a-3848715634a6\subagents")
fs = sorted(glob.glob(os.path.join(D, "*.jsonl")), key=os.path.getmtime)
f = fs[-1]; seen = {}
for l in open(f, encoding="utf-8", errors="replace"):
    if '"usage"' not in l: continue
    try: o = json.loads(l)
    except ValueError: continue
    m = o.get("message") or {}; u = m.get("usage")
    if not u: continue
    k = m.get("id") or o.get("uuid")
    seen[k] = u if k not in seen or (u.get("output_tokens") or 0) >= (seen[k].get("output_tokens") or 0) else seen[k]
tot = sum((u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("output_tokens") or 0) for u in seen.values())
print(os.path.basename(f), "calls", len(seen), "processed", f"{tot:,}")
