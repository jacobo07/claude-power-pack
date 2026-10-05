"""T2 C sensitivity (zero-model): floor choice. Reads the t2 cache. usage: python t2_c_sensitivity.py CACHE OUT.json
(1) per-transcript floor f0 = that transcript's own first-call ctx, with rehydration (S+f0) per restart (k4-comparable);
(2) main-sessions-only median floor; (3) meta-run call counts vs break-even."""
import json, sys, statistics as st
c = json.load(open(sys.argv[1])); res = {}
def tot(TT, N, S, fl, rehyd=True):
    t_ = 0
    for t in TT:
        x = [k["ctx"] for k in t["calls"]]; f = fl(t)
        for i in range(len(x)):
            if N is None: t_ += x[i]; continue
            g = (i // N) * N
            t_ += x[i] if g == 0 else min(x[i], f + S + (x[i] - x[g]))
            if rehyd and i > 0 and i % N == 0: t_ += S + f
    return t_ + sum(k["out"] for t in TT for k in t["calls"])
for nm, w in c.items():
    TT = w["transcripts"]; base = tot(TT, None, 0, lambda t: 0)
    mainfl = st.median([t["calls"][0]["ctx"] for t in TT if t["main"]]); subfl = st.median([t["calls"][0]["ctx"] for t in TT if not t["main"]]) if any(not t["main"] for t in TT) else None
    modes = {"per_transcript_f0_with_rehydration": lambda t: t["calls"][0]["ctx"], "main_median_floor_with_rehydration": lambda t: mainfl}
    r = {"main_floor_median": mainfl, "main_n": sum(t["main"] for t in TT), "sub_floor_median": subfl, "sub_n": sum(not t["main"] for t in TT)}
    for mn, fl in modes.items():
        g = {f"N={N or 'inf'},S={S//1000}k": round(100 * (tot(TT, N, S, fl) - base) / base, 1) for N in (1, 3, 5, 10, 20, 40, None) for S in (5000, 10000, 30000, 60000)}
        b = min(g, key=g.get); r[mn] = {"argmin": [b, g[b]], "N20_S10k": g["N=20,S=10k"], "N10_S10k": g["N=10,S=10k"], "N10_S30k": g["N=10,S=30k"], "N40_S30k": g["N=40,S=30k"]}
    meta = [t for t in TT if not t["main"] and t["stype"] in {"gsd-planner", "gsd-phase-researcher", "gsd-plan-checker"}]
    if meta:
        P = [sum(k["ctx"] + k["out"] for k in t["calls"]) for t in meta]; n = [len(t["calls"]) for t in meta]
        r["meta_runs"] = {"runs": len(meta), "mean_calls": st.mean(n), "mean_processed": st.mean(P), "mean_ctx_per_call": st.mean(P) / st.mean(n), "break_even_in_floor_sized_calls": st.mean(P) / r["main_floor_median"]}
    res[nm] = r
json.dump(res, open(sys.argv[2], "w"), indent=1); print(json.dumps(res, indent=1))