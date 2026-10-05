"""Break down attachment rent by attachment type / hook name, and the pre-first-call floor by source."""
import glob
import json
import os
import re
from collections import defaultdict

PROJ = os.path.expanduser(r"~\.claude\projects\C--Users-User-Apps-io-device-trust")
WORKERS = ["be2a71eb", "50d3a9f0", "affe87e4", "63bc3ed8", "dc79aa64", "5f5bc46f", "4f1b398d", "dfc0acda"]
KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
TPC = 0.32


def label(o):
    a = o.get("attachment") or {}
    at = a.get("type") or o.get("subtype") or o.get("type")
    hook = a.get("hookName") or a.get("hookEvent") or ""
    if not hook:
        m = re.search(r'"(?:hookName|hook_event_name|hookEvent)":\s*"([^"]+)"', json.dumps(a)[:4000])
        hook = m.group(1) if m else ""
    return f"{at}:{hook}" if hook else str(at)


rent = defaultdict(float)
count = defaultdict(int)
floor_parts = defaultdict(int)
for w in WORKERS:
    f = glob.glob(os.path.join(PROJ, f"{w}-*.jsonl"))[0]
    rows, ncalls, seen = [], 0, set()
    with open(f, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            msg = o.get("message") or {}
            if o.get("type") == "assistant" and msg.get("usage"):
                mid = msg.get("id") or o.get("uuid")
                if mid not in seen:
                    seen.add(mid)
                    ncalls += 1
            if o.get("type") in ("attachment", "system"):
                rows.append((ncalls, label(o), len(json.dumps(o.get("attachment") or o.get("content") or ""))))
            elif o.get("type") == "user" and ncalls == 0:
                c = msg.get("content")
                floor_parts["first user message"] += len(c) if isinstance(c, str) else len(json.dumps(c))
    for i, lab, n in rows:
        if i == 0:
            floor_parts[f"attachment {lab}"] += n
        else:
            rent[lab] += n * TPC * (ncalls - i)
            count[lab] += 1

tot = sum(rent.values())
print(f"in-run attachment rent ~{tot:,.0f} tokens (TPC {TPC})")
for k, v in sorted(rent.items(), key=lambda kv: -kv[1])[:15]:
    print(f"  {k[:60]:60} n={count[k]:5}  rent={v:14,.0f}  {v/tot*100:5.1f}%")
print("\nvisible pre-first-call transcript material (8 workers, chars):")
for k, v in sorted(floor_parts.items(), key=lambda kv: -kv[1])[:12]:
    print(f"  {k[:60]:60} {v:10,}  ~{int(v*TPC/8):7,} tok/worker")
