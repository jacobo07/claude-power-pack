"""Canary #5: per-file requests of each pane vs the journal's holds, from 21:46:30."""
import datetime as dt
import json
from pathlib import Path

GOAL, FROM = "canary-20261007e", "2026-10-07T21:46:30"
UK = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
iso = lambda ts: dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%H:%M:%S.%f")[:12]
jr = [json.loads(l) for l in (Path.home() / ".claude/state/goal-budget" / GOAL / "spend.journal.jsonl")
      .read_text(encoding="utf-8").splitlines() if l.strip()]
ev = []
for r in jr:
    if iso(r["ts"]) >= FROM[11:]:
        d = (f"settle {r['measured']:,} closes={len(r['closes'])}" if r["op"] == "settle"
             else f"{r['op']} {r.get('kind')} {r.get('amount', ''):,} base={r.get('base', '')}" if r["op"] == "reserve"
             else r["op"])
        ev.append((iso(r["ts"]), f"J{r['seq']:>3} {r.get('sid', '')[:8]}", d))
pdir = Path.home() / ".claude" / "projects"
for sid in ("ae5b2f23-5111-43da-a397-a1d32345d5b8", "5c78f87b-6cc7-4c2f-bfba-bd60a3439b0e"):
    main = next(pdir.glob(f"*/{sid}.jsonl"))
    seen = set()
    for f in [main] + sorted((main.parent / sid / "subagents").glob("*.jsonl")):
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            m = r.get("message") if isinstance(r, dict) else None
            ts = str(r.get("timestamp") or "") if isinstance(r, dict) else ""
            if not isinstance(m, dict) or ts < FROM:
                continue
            if isinstance(m.get("content"), list) and any(isinstance(b, dict) and b.get("type") == "tool_result"
                                                          and "GOAL BUDGET" in json.dumps(b.get("content")) for b in m["content"]):
                ev.append((ts[11:23], f"T   {sid[:8]}", f"DENY in {f.name[:14]}"))
            u = m.get("usage")
            if not u or m.get("model") == "<synthetic>" or (m.get("id") or r.get("uuid")) in seen:
                continue
            seen.add(m.get("id") or r.get("uuid"))
            tools = [b.get("name") for b in m.get("content") or [] if isinstance(b, dict) and b.get("type") == "tool_use"]
            ev.append((ts[11:23], f"T   {sid[:8]}", f"req {sum(int(u.get(k) or 0) for k in UK):>7,} {f.name[:14]} {tools}"))
for e in sorted(ev):
    print(*e)
