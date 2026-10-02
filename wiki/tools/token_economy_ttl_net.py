"""Net effect of a 5 m cache TTL for MAIN-thread calls over 7 d (read-only, zero quota).

Today main calls write at the 1 h rate. Under 5 m: every write is cheaper (1.25x vs 2x input),
BUT a call arriving 5-60 min after the previous one in the same transcript, which today reads
its prefix from cache, would instead rewrite it. Calls after > 60 min miss either way.
Upper-bound model: on a 5-60 min gap the whole previous context is rewritten.
Also reports the subagent side (already 5 m by default) for reference. USD estimate, list price."""
import os, sqlite3, sys
from collections import defaultdict

sys.path.insert(0, r"C:\Users\User\.claude\skills\claude-power-pack\tools")
import usage_index as ui

p = os.path.expanduser("~/.claude/state/usage_index/index.sqlite")
c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
prices = ui.load_prices()
END = c.execute("select max(ts) from calls").fetchone()[0]
rows = c.execute("select file, ts, model, cw, cw5, cw1, cr from calls where is_sub=0 and ts>? and ts<=? order by file, ts",
                 (END - 7 * 86400, END)).fetchall()
save_writes = 0.0; extra_miss = 0.0; n_miss = 0; prev = {}
gaps = defaultdict(int)
for f, ts, m, cw, cw5, cw1, cr in rows:
    pr, _ = ui.price_for(m, prices)
    if not pr:
        continue
    save_writes += cw1 * (pr["cache_write_1h"] - pr["cache_write_5m"]) / 1e6
    if f in prev:
        gap = ts - prev[f]
        if 300 < gap <= 3600:
            n_miss += 1
            extra_miss += cr * (pr["cache_write_5m"] - pr["cache_read"]) / 1e6
            gaps["5-60m"] += 1
        elif gap <= 300:
            gaps["<=5m"] += 1
        else:
            gaps[">60m"] += 1
    prev[f] = ts
print(f"main calls={len(rows):,}; inter-call gaps: {dict(gaps)}")
print(f"5m TTL: cheaper writes save ~usd {save_writes:,.0f}; new misses on 5-60 min gaps n={n_miss:,} cost ~usd {extra_miss:,.0f}; "
      f"NET ~usd {save_writes - extra_miss:,.0f} (positive = 5m is cheaper)")
