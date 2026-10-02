"""Read-only cuts of the usage index for the token-economy research (2026-10-02).
Tokens are MEASURED; usd is an ESTIMATE at list price (usage_index.load_prices)."""
import os, sqlite3, sys, time
sys.path.insert(0, r"C:\Users\User\.claude\skills\claude-power-pack\tools")
import usage_index as ui

p = os.path.expanduser("~/.claude/state/usage_index/index.sqlite")
c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
prices = ui.load_prices()
END = c.execute("select max(ts) from calls").fetchone()[0]
START = END - 7 * 86400
print(f"window: {time.strftime('%Y-%m-%d %H:%M', time.gmtime(START))}Z -> "
      f"{time.strftime('%Y-%m-%d %H:%M', time.gmtime(END))}Z")


def usd(model, inp, cw5, cw1, cw, cr, out):
    pr, _ = ui.price_for(model, prices)
    if pr is None:
        return 0.0
    uns = max(0, cw - cw5 - cw1)
    return (inp * pr["input"] + cw5 * pr["cache_write_5m"] + (cw1 + uns) * pr["cache_write_1h"]
            + cr * pr["cache_read"] + out * pr["output"]) / 1e6


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(len(xs) * q))] if xs else 0


rows = c.execute("select model,is_sub,entrypoint,inp,cw,cw5,cw1,cr,out,session,prompt_id,agent_id,file "
                 "from calls where ts>? and ts<=?", (START, END)).fetchall()
print(f"calls={len(rows)}")

# 1. category cost shares
cat = dict(input=0.0, cache_write=0.0, cache_read=0.0, output=0.0)
tok = dict(input=0, cache_write=0, cache_read=0, output=0)
for m, s, ep, inp, cw, cw5, cw1, cr, out, *_ in rows:
    pr, _ = ui.price_for(m, prices)
    if pr is None:
        continue
    uns = max(0, cw - cw5 - cw1)
    cat["input"] += inp * pr["input"] / 1e6
    cat["cache_write"] += (cw5 * pr["cache_write_5m"] + (cw1 + uns) * pr["cache_write_1h"]) / 1e6
    cat["cache_read"] += cr * pr["cache_read"] / 1e6
    cat["output"] += out * pr["output"] / 1e6
    tok["input"] += inp; tok["cache_write"] += cw; tok["cache_read"] += cr; tok["output"] += out
tot = sum(cat.values())
print(f"\n[1] est usd={tot:,.0f}")
for k in cat:
    print(f"  {k:12} tokens={tok[k]:>15,}  usd={cat[k]:>10,.0f}  share={cat[k]/tot:6.1%}")

# 2. per-call context, main vs sub
for label, flag in (("main", 0), ("sub", 1)):
    ctx = [inp + cw + cr for m, s, ep, inp, cw, cw5, cw1, cr, out, *_ in rows if s == flag]
    u = sum(usd(m, inp, cw5, cw1, cw, cr, out) for m, s, ep, inp, cw, cw5, cw1, cr, out, *_ in rows if s == flag)
    print(f"\n[2] {label}: calls={len(ctx)} ctx p10/p50/p90/p99 = {pct(ctx,.1):,}/{pct(ctx,.5):,}/"
          f"{pct(ctx,.9):,}/{pct(ctx,.99):,}  usd={u:,.0f} ({u/tot:.1%})")

# 3. by model
bym = {}
for m, s, ep, inp, cw, cw5, cw1, cr, out, *_ in rows:
    d = bym.setdefault(m, [0, 0.0])
    d[0] += 1; d[1] += usd(m, inp, cw5, cw1, cw, cr, out)
print("\n[3] by model")
for m, (n, u) in sorted(bym.items(), key=lambda x: -x[1][1])[:6]:
    print(f"  {m:40} calls={n:>7,} usd={u:>9,.0f} ({u/tot:.1%})")

# 4. by prompt source (who started the work)
kinds = dict(c.execute("select prompt_id, coalesce(kind,'?')||'/'||coalesce(source,'?') from prompts"))
byk = {}
for m, s, ep, inp, cw, cw5, cw1, cr, out, sess, pid, aid, f in rows:
    k = kinds.get(pid, "unknown-prompt")
    d = byk.setdefault(k, [0, 0.0])
    d[0] += 1; d[1] += usd(m, inp, cw5, cw1, cw, cr, out)
print("\n[4] by prompt kind/source")
for k, (n, u) in sorted(byk.items(), key=lambda x: -x[1][1])[:10]:
    print(f"  {k:40} calls={n:>7,} usd={u:>9,.0f} ({u/tot:.1%})")

# 5. by subagent type
types = dict(c.execute("select file, coalesce(agent_type,'?') from subagents"))
byt = {}
for m, s, ep, inp, cw, cw5, cw1, cr, out, sess, pid, aid, f in rows:
    if not s:
        continue
    t = types.get(f, "untyped")
    d = byt.setdefault(t, [0, 0.0, []])
    d[0] += 1; d[1] += usd(m, inp, cw5, cw1, cw, cr, out); d[2].append(inp + cw + cr)
print("\n[5] subagent types")
for t, (n, u, ctx) in sorted(byt.items(), key=lambda x: -x[1][1])[:10]:
    print(f"  {t:28} calls={n:>6,} usd={u:>8,.0f} ({u/tot:.1%}) ctx p50={pct(ctx,.5):,}")

# 6. entrypoint (cli vs sdk-cli = headless / missions)
bye = {}
for m, s, ep, inp, cw, cw5, cw1, cr, out, *_ in rows:
    d = bye.setdefault(ep or "?", [0, 0.0])
    d[0] += 1; d[1] += usd(m, inp, cw5, cw1, cw, cr, out)
print("\n[6] entrypoint")
for e, (n, u) in sorted(bye.items(), key=lambda x: -x[1][1]):
    print(f"  {e:14} calls={n:>7,} usd={u:>9,.0f} ({u/tot:.1%})")

# 7. sessions: concentration
bys = {}
for m, s, ep, inp, cw, cw5, cw1, cr, out, sess, *_ in rows:
    bys[sess] = bys.get(sess, 0.0) + usd(m, inp, cw5, cw1, cw, cr, out)
vals = sorted(bys.values(), reverse=True)
top10 = sum(vals[:10]); top50 = sum(vals[:50])
print(f"\n[7] sessions={len(vals)} top10={top10/tot:.1%} top50={top50/tot:.1%} median_session_usd={pct(vals,.5):,.1f}")

# 8. cache write TTL split
cw5 = sum(r[5] for r in rows); cw1 = sum(r[6] for r in rows); cwt = sum(r[4] for r in rows)
print(f"\n[8] cache writes: total={cwt:,} 5m={cw5:,} ({cw5/max(cwt,1):.1%}) 1h={cw1:,} ({cw1/max(cwt,1):.1%})")

# 9. growth: calls per session-file and context at last call vs first (main only)
from collections import defaultdict
seq = defaultdict(list)
for r in c.execute("select file, ts, inp+cw+cr from calls where ts>? and ts<=? and is_sub=0 order by ts", (START, END)):
    seq[r[0]].append(r[2])
firsts = [v[0] for v in seq.values() if len(v) >= 20]
lasts = [v[-1] for v in seq.values() if len(v) >= 20]
lens = [len(v) for v in seq.values()]
print(f"\n[9] main transcripts={len(seq)} calls/transcript p50={pct(lens,.5)} p90={pct(lens,.9)}; "
      f"(>=20 calls) first ctx p50={pct(firsts,.5):,} last ctx p50={pct(lasts,.5):,} p90={pct(lasts,.9):,}")
