"""K1: first-call context floor before/after E1 (live ~2026-10-05T12:34Z). Zero-model, reads g3_extract cache.
Positive control: instructions-attachment chars must drop ~32 KB after E1."""
import json, sys, statistics as st, datetime as dt, collections
S = json.load(open(sys.argv[1]))
CUT = dt.datetime(2026, 10, 5, 12, 34, tzinfo=dt.timezone.utc)
DAY0 = dt.datetime(2026, 10, 5, 0, 0, tzinfo=dt.timezone.utc)
def T(s): return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
def q(v, p):
    v = sorted(v)
    if not v: return None
    k = (len(v) - 1) * p; f = int(k); c = min(f + 1, len(v) - 1)
    return v[f] + (v[c] - v[f]) * (k - f)
def row(sess):
    t0 = T(sess["calls"][0][0]); c0 = sess["calls"][0][1]
    ins = [e for e in sess["events"] if e["t"] == "instructions" and e["i"] == 0]
    return {"t0": t0, "ctx": c0, "ins": ins[0]["files"] if ins else None, "insr": ins[0]["r"] if ins else None, "proj": sess["proj"], "sid": sess["sid"]}
_seen = set(); R = []
for s in S:  # the same session file can sit under two project dirs (copy): dedupe by session id + first call time
    k = (s["sid"], s["calls"][0][0])
    if k in _seen: continue
    _seen.add(k); R.append(row(s))
print("dedupe:", len(S), "->", len(R))
before = [r for r in R if DAY0 <= r["t0"] < CUT]
after = [r for r in R if r["t0"] >= CUT]
def rep(name, rs, fresh_only=False):
    if fresh_only: rs = [r for r in rs if r["ctx"] <= 250000]
    c = [r["ctx"] for r in rs]; i = [r["ins"] for r in rs if r["ins"]]; ir = [r["insr"] for r in rs if r["insr"]]
    if not c: print(name, "n=0"); return 0, None
    print(f"{name:34} n={len(c):3} ctx med={q(c,.5):9,.0f} p25={q(c,.25):9,.0f} p75={q(c,.75):9,.0f} | instr files chars med={q(i,.5) if i else 0:9,.0f} (n={len(i)}) rendered med={q(ir,.5) if ir else 0:9,.0f}")
    return q(c, .5), (q(i, .5) if i else None)
print(f"CUT {CUT.isoformat()}  sessions total {len(R)}; same-day before n={len(before)}, after n={len(after)}")
for fo in (False, True):
    print("--- fresh-only (first-call ctx<=250k)" if fo else "--- all main sessions")
    mb, ib = rep("before (same day)", before, fo); ma, ia = rep("after E1", after, fo)
    print(f"   delta first-call ctx median {ma-mb:+,.0f}; delta instructions chars {(ia or 0)-(ib or 0):+,.0f}")
    pj = collections.defaultdict(lambda: ([], []))
    for r in before: pj[r["proj"]][0].append(r)
    for r in after: pj[r["proj"]][1].append(r)
    for p, (b, a) in sorted(pj.items()):
        if fo: b = [r for r in b if r["ctx"] <= 250000]; a = [r for r in a if r["ctx"] <= 250000]
        if len(b) >= 3 and len(a) >= 3: rep(p[-30:] + " BEFORE", b); rep(p[-30:] + " AFTER", a)
print("instructions chars after-cut sessions, sorted sample:", sorted([r["ins"] for r in after if r["ins"]])[:5], "...", sorted([r["ins"] for r in after if r["ins"]])[-3:])
print("instructions chars before sessions sample:", sorted([r["ins"] for r in before if r["ins"]])[:3], "...", sorted([r["ins"] for r in before if r["ins"]])[-3:])
med_b = st.median([r["ins"] for r in before if r["ins"]]) if before else 0
print("after-cut with instructions >= 0.9*median(before):", sum(1 for r in after if r["ins"] and r["ins"] >= .9 * med_b), "of", sum(1 for r in after if r["ins"]))
