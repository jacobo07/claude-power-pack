"""Canary #3 re-measure: refusals = journal `final` holds; post-deny requests keyed on the deny tool_result."""
import datetime as dt
import json
from pathlib import Path

GOAL, SINCE = "canary-20261007c", "2026-10-07T21:23:22"
SIDS = ("cd088f91-6a6d-4aa5-be5a-48c128f0748c", "c86a96b2-a9b7-4619-be98-7bc28f6778cd")
UK = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
jr = [json.loads(l) for l in (Path.home() / ".claude/state/goal-budget" / GOAL / "spend.journal.jsonl")
      .read_text(encoding="utf-8").splitlines() if l.strip()]
iso = lambda ts: dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:23]
print("journal rows", len(jr), "| finals:", [(r["sid"][:8], r["seq"], iso(r["ts"]), r["amount"], r["base"])
                                           for r in jr if r.get("kind") == "final"])
print("leases:", sum(1 for r in jr if r.get("kind") == "lease"), "agents:", sum(1 for r in jr if r.get("kind") == "agent"))
pdir = Path.home() / ".claude" / "projects"
for sid in SIDS:
    main = next(pdir.glob(f"*/{sid}.jsonl"))
    files = [main] + sorted((main.parent / sid / "subagents").glob("*.jsonl"))
    seen, reqs, denies = set(), [], []
    for f in files:
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if not isinstance(r, dict) or str(r.get("timestamp") or "") < SINCE:
                continue
            m = r.get("message") or {}
            if isinstance(m, dict) and isinstance(m.get("content"), list):
                for b in m["content"]:
                    if isinstance(b, dict) and b.get("type") == "tool_result" and "GOAL BUDGET" in json.dumps(b.get("content")):
                        denies.append((r["timestamp"], json.dumps(b.get("content"))[:160]))
            u = m.get("usage") if isinstance(m, dict) else None
            if not u or m.get("model") == "<synthetic>" or (m.get("id") or r.get("uuid")) in seen:
                continue
            seen.add(m.get("id") or r.get("uuid"))
            reqs.append((r["timestamp"], sum(int(u.get(k) or 0) for k in UK), f.name[:10]))
    reqs.sort()
    d0 = min(denies)[0] if denies else None
    after = [q for q in reqs if d0 and q[0] > d0]
    print(f"\n{sid[:8]}: files {len(files)} subagent files {len(files) - 1}; denies {len(denies)}; first {d0}")
    print("  deny text:", denies[0][1] if denies else None)
    print("  after first deny:", after, "sum", sum(q[1] for q in after))
    print("  last 3 before:", [q for q in reqs if not d0 or q[0] <= d0][-3:])
