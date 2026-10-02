"""Upper-bound lever estimates over the same 7-day window. ESTIMATES, not savings:
each ignores second-order costs (capsule re-read, quality, extra calls)."""
import os, sqlite3, sys
from collections import defaultdict
sys.path.insert(0, r"C:\Users\User\.claude\skills\claude-power-pack\tools")
import usage_index as ui

p = os.path.expanduser("~/.claude/state/usage_index/index.sqlite")
c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
prices = ui.load_prices()
END = c.execute("select max(ts) from calls").fetchone()[0]
START = END - 7 * 86400
rows = c.execute("select file,ts,model,is_sub,inp,cw,cw5,cw1,cr,out from calls where ts>? and ts<=? order by ts",
                 (START, END)).fetchall()


def usd(model, inp, cw5, cw1, cw, cr, out, as_model=None):
    pr, _ = ui.price_for(as_model or model, prices)
    if pr is None:
        return 0.0
    uns = max(0, cw - cw5 - cw1)
    return (inp * pr["input"] + cw5 * pr["cache_write_5m"] + (cw1 + uns) * pr["cache_write_1h"]
            + cr * pr["cache_read"] + out * pr["output"]) / 1e6


tot = sum(usd(*r[2:3], r[4], r[6], r[7], r[5], r[8], r[9]) for r in rows)
print(f"total est usd={tot:,.0f}")

# L1: main-thread context ceiling (rollover). Cost of cache-read tokens above the cap on main calls,
# minus a re-seed of FLOOR+capsule for each crossing. Crossings ~ (tokens above cap)/(cap-floor) per transcript.
FLOOR, CAPSULE = 115_000, 15_000
for cap in (150_000, 200_000, 250_000, 300_000):
    saved = 0.0; seeds = 0
    byf = defaultdict(list)
    for f, ts, m, s, inp, cw, cw5, cw1, cr, out in rows:
        if not s:
            byf[f].append((m, inp + cw + cr))
    for f, calls in byf.items():
        pr, _ = ui.price_for(calls[0][0], prices)
        if pr is None:
            continue
        over = [max(0, ctx - cap) for m, ctx in calls]
        if not any(over):
            continue
        # after a crossing the context restarts at FLOOR+CAPSULE: excess read is roughly ctx-cap
        saved += sum(over) * pr["cache_read"] / 1e6
        n_cross = max(1, int(max(ctx for m, ctx in calls) // cap))
        seeds += n_cross
        saved -= n_cross * (FLOOR + CAPSULE) * pr["cache_write_1h"] / 1e6
    print(f"[L1] main ctx cap {cap//1000}k: upper-bound saving ~usd {saved:,.0f} ({saved/tot:.1%}); crossings ~{seeds}")

# L2: subagents on Sonnet 5.5 instead of their actual model
sub_now = sum(usd(r[2], r[4], r[6], r[7], r[5], r[8], r[9]) for r in rows if r[3])
sub_son = sum(usd(r[2], r[4], r[6], r[7], r[5], r[8], r[9], as_model="claude-sonnet-5-5") for r in rows if r[3])
print(f"[L2] subagents actual usd={sub_now:,.0f} -> all-Sonnet-5.5 usd={sub_son:,.0f}: saving {sub_now-sub_son:,.0f} ({(sub_now-sub_son)/tot:.1%})")

# L3: 1h -> 5m TTL on writes (only valid where the next call lands within 5 min)
w1 = sum(r[7] for r in rows)
d = 0.0
for f, ts, m, s, inp, cw, cw5, cw1, cr, out in rows:
    pr, _ = ui.price_for(m, prices)
    if pr:
        d += cw1 * (pr["cache_write_1h"] - pr["cache_write_5m"]) / 1e6
gaps = []
last = {}
for f, ts, *_ in rows:
    if f in last:
        gaps.append(ts - last[f])
    last[f] = ts
within5 = sum(1 for g in gaps if g <= 300) / max(len(gaps), 1)
print(f"[L3] 1h writes={w1:,}; 1h->5m price delta={d:,.0f} ({d/tot:.1%}); inter-call gaps <=5min: {within5:.1%}")

# L4: floor shrink. Every call re-reads the floor; first call writes it.
for cut in (20_000, 40_000):
    s = 0.0
    seen = set()
    for f, ts, m, s_, inp, cw, cw5, cw1, cr, out in rows:
        pr, _ = ui.price_for(m, prices)
        if not pr:
            continue
        s += cut * pr["cache_read"] / 1e6
        if f not in seen:
            seen.add(f); s += cut * (pr["cache_write_1h"] - pr["cache_read"]) / 1e6
    print(f"[L4] floor -{cut//1000}k tokens on every call: saving ~usd {s:,.0f} ({s/tot:.1%})")
