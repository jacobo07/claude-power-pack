"""Cold start and skill use over 7 d (read-only, zero model quota).

[F] first call of every transcript: how much of its context was READ from cache (shared with an
    earlier session/agent) vs WRITTEN fresh, main vs subagent, and the estimated cost of writing
    instead of reading.
[K] which listed skills were actually invoked (Skill tool calls, main + subagents).
USD is an ESTIMATE at list price; tokens are MEASURED.
"""
import json, os, sqlite3, sys
from collections import Counter, defaultdict

sys.path.insert(0, r"C:\Users\User\.claude\skills\claude-power-pack\tools")
import usage_index as ui

p = os.path.expanduser("~/.claude/state/usage_index/index.sqlite")
c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
prices = ui.load_prices()
END = c.execute("select max(ts) from calls").fetchone()[0]
START = END - 7 * 86400
rows = c.execute("select file, ts, model, is_sub, cw, cw5, cw1, cr, inp from calls where ts>? and ts<=? order by ts",
                 (START, END)).fetchall()
first = {}
for r in rows:
    first.setdefault(r[0], r)

agg = defaultdict(lambda: [0, 0, 0, 0.0, 0.0])   # n, cr, cw, usd actual, usd if cw were read
for f, ts, m, sub, cw, cw5, cw1, cr, inp in first.values():
    pr, _ = ui.price_for(m, prices)
    if not pr:
        continue
    a = agg["sub" if sub else "main"]
    a[0] += 1; a[1] += cr; a[2] += cw
    uns = max(0, cw - cw5 - cw1)
    a[3] += (cw5 * pr["cache_write_5m"] + (cw1 + uns) * pr["cache_write_1h"] + cr * pr["cache_read"]) / 1e6
    a[4] += ((cw + cr) * pr["cache_read"]) / 1e6
print("[F] first call per transcript: cache READ (shared prefix) vs WRITTEN fresh")
for k, (n, cr, cw, u, u_read) in agg.items():
    print(f"  {k:5} transcripts={n:>6,}  read p-share={cr/(cr+cw):.1%}  mean read={cr/n:>9,.0f}  mean written={cw/n:>9,.0f}  "
          f"usd actual={u:>6,.0f}  usd if all were reads={u_read:>5,.0f}  gap={u-u_read:>6,.0f}")

# distribution of the read part for main first calls (is there a stable shared floor?)
reads = sorted(r[7] for r in first.values() if not r[3])
q = lambda x: reads[min(len(reads) - 1, int(len(reads) * x))]
print(f"  main first-call cache_read p10/p50/p90 = {q(.1):,}/{q(.5):,}/{q(.9):,}")

# [K] skill invocations
inv = Counter(); listed = set(); files = {r[0] for r in rows}
for f in files:
    try:
        fh = open(f, encoding="utf-8")
    except OSError:
        continue
    for line in fh:
        if '"Skill"' not in line and '"skill_listing"' not in line:
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") == "attachment" and (d.get("attachment") or {}).get("type") == "skill_listing":
            listed.update((d["attachment"].get("names") or []))
        if d.get("type") == "assistant":
            for b in (d.get("message") or {}).get("content") or []:
                if b.get("type") == "tool_use" and b.get("name") == "Skill":
                    inv[(b.get("input") or {}).get("skill")] += 1
fh = None
print(f"\n[K] skills listed (union over transcripts)={len(listed)}; distinct invoked={len(inv)}; invocations={sum(inv.values())}")
print("  top invoked:", inv.most_common(15))
never = sorted(listed - set(inv))
print(f"  listed but never invoked in 7 d: {len(never)}")
