"""Follow-up cuts: peer/system prompts, one-call transcripts, cold first-call writes."""
import os, sqlite3, sys
from collections import defaultdict, Counter
sys.path.insert(0, r"C:\Users\User\.claude\skills\claude-power-pack\tools")
import usage_index as ui

p = os.path.expanduser("~/.claude/state/usage_index/index.sqlite")
c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
prices = ui.load_prices()
END = c.execute("select max(ts) from calls").fetchone()[0]
START = END - 7 * 86400


def usd(model, inp, cw5, cw1, cw, cr, out):
    pr, _ = ui.price_for(model, prices)
    if pr is None:
        return 0.0
    uns = max(0, cw - cw5 - cw1)
    return (inp * pr["input"] + cw5 * pr["cache_write_5m"] + (cw1 + uns) * pr["cache_write_1h"]
            + cr * pr["cache_read"] + out * pr["output"]) / 1e6


rows = c.execute("select c.file,c.ts,c.model,c.is_sub,c.inp,c.cw,c.cw5,c.cw1,c.cr,c.out,c.prompt_id,"
                 "f.title,f.entrypoint from calls c left join files f on f.path=c.file "
                 "where c.ts>? and c.ts<=? order by c.ts", (START, END)).fetchall()
tot = sum(usd(r[2], r[4], r[6], r[7], r[5], r[8], r[9]) for r in rows)
kinds = dict(c.execute("select prompt_id, coalesce(kind,'?')||'/'||coalesce(source,'?') from prompts"))

# A. peer/system: which transcripts/projects carry it
peer = Counter(); peer_usd = defaultdict(float)
for f, ts, m, s, inp, cw, cw5, cw1, cr, out, pid, title, ep in rows:
    if kinds.get(pid) == "peer/system":
        proj = os.path.basename(os.path.dirname(f)) if not s else "SUB:" + os.path.basename(os.path.dirname(os.path.dirname(f)))
        peer[proj] += 1; peer_usd[proj] += usd(m, inp, cw5, cw1, cw, cr, out)
print("[A] peer/system by project dir")
for k, u in sorted(peer_usd.items(), key=lambda x: -x[1])[:8]:
    print(f"  {k[:70]:70} calls={peer[k]:>6} usd={u:>7,.0f}")
print("  prompt kinds in table:", Counter(k for k in kinds.values()).most_common(12))

# B. one-call main transcripts
calls_by_file = defaultdict(list)
for r in rows:
    if not r[3]:
        calls_by_file[r[0]].append(r)
one = [v[0] for v in calls_by_file.values() if len(v) == 1]
u1 = sum(usd(r[2], r[4], r[6], r[7], r[5], r[8], r[9]) for r in one)
print(f"\n[B] one-call main transcripts={len(one)} of {len(calls_by_file)}; usd={u1:,.0f} ({u1/tot:.1%}); "
      f"entrypoints={Counter(r[12] for r in one).most_common(3)}")
print("  sample titles:", [ (r[11] or '')[:50] for r in one[:8]])

# C. cold first call of every transcript (main + sub): the floor write
first = {}
for r in rows:
    first.setdefault(r[0], r)
cold_cw = sum(r[5] for r in first.values()); all_cw = sum(r[5] for r in rows)
cold_usd = sum(usd(r[2], r[4], r[6], r[7], r[5], r[8], r[9]) for r in first.values())
print(f"\n[C] transcripts={len(first)} first-call cache_write={cold_cw:,} ({cold_cw/max(all_cw,1):.1%} of all writes); "
      f"first-call usd={cold_usd:,.0f} ({cold_usd/tot:.1%})")
fc = sorted(r[5] + r[8] + r[4] for r in first.values())
print(f"  first-call context p10/p50/p90 = {fc[len(fc)//10]:,}/{fc[len(fc)//2]:,}/{fc[len(fc)*9//10]:,}")

# D. writes per subsequent call: how much of each later call is re-written (cache misses)
later = [r for r in rows if first.get(r[0]) is not r]
big = [r for r in later if r[5] > 50_000]
bu = sum(usd(r[2], r[4], r[6], r[7], r[5], r[8], r[9]) for r in big)
print(f"\n[D] later calls={len(later)}; with cache_write>50k (prefix rebuilt mid-session)={len(big)} "
      f"usd={bu:,.0f} ({bu/tot:.1%}); their cw sum={sum(r[5] for r in big):,}")
