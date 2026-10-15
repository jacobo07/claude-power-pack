#!/usr/bin/env python3
"""D12a step 2: conjunctive hypergraph over residuals_v1.jsonl.  STRUCTURE, not cost.
usage: hypergraph.py <residuals_v1.jsonl> <out.json>"""
import collections, json, sys

rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
tgt = [r for r in rows if r.get("distance") in (2, 3, 4, 5)]
M2C = ("m2c", "m2c_failed")
resid_unknown = sorted(r["fn"] for r in tgt if any(v["type"] in M2C for v in r.get("unresolved_vars") or []))
ru = set(resid_unknown)


def varset(r):
    return {v["id"] for v in r.get("unresolved_vars") or [] if not v.get("depends_on_struct")}


fv = {r["fn"]: varset(r) for r in tgt if r["fn"] not in ru}
named = {f: v for f, v in fv.items() if v}
nov = sorted(f for f, v in fv.items() if not v)
vf = collections.defaultdict(set)
for f, vs in named.items():
    for v in vs:
        vf[v].add(f)
deg = collections.Counter(len(s) for s in vf.values())
sizes = sorted(len(v) for v in named.values())
q = lambda p: sizes[int(p * (len(sizes) - 1))]
priv = collections.Counter(sum(1 for v in named[f] if len(vf[v]) == 1) for f in named)

remaining = {f: set(v) for f, v in named.items()}
resolved, done, curve = set(), 0, []
marks = {50, 100, 200, 400, 600, 800, 1000, 1200}
while remaining:
    f = min(remaining, key=lambda k: (len(remaining[k]), -sum(len(vf[v]) for v in remaining[k]), k))
    new = set(remaining[f])
    resolved |= new
    for g in list(remaining):
        remaining[g] -= new
        if not remaining[g]:
            del remaining[g]
            done += 1
            if done in marks:
                curve.append((done, len(resolved)))
curve.append((done, len(resolved)))

par = {}
def find(x):
    while par.setdefault(x, x) != x:
        par[x] = par[par[x]]
        x = par[x]
    return x
for f, vs in named.items():
    for v in vs:
        par[find("f:" + f)] = find("v:" + v)
comp = collections.Counter(find("f:" + f) for f in named)
cs = sorted(comp.values(), reverse=True)
dist_hist = collections.Counter(min(len(v), 10) for v in named.values())
out = dict(label="STRUCTURE, not cost", n_target_fns=len(tgt), n_residual_unknown_m2c=len(resid_unknown),
           residual_unknown_fns_flag="RESIDUAL_UNKNOWN (m2c-kind var; D5: hidden co-blockers) - never counted as closed",
           n_fns_with_no_named_var=len(nov), n_fns_with_vars=len(named), distinct_vars=len(vf),
           occurrences=sum(len(s) for s in vf.values()),
           var_degree=dict(d1=deg.get(1, 0), d2_4=sum(c for d, c in deg.items() if 2 <= d <= 4),
                           d5_19=sum(c for d, c in deg.items() if 5 <= d <= 19), d20p=sum(c for d, c in deg.items() if d >= 20)),
           private_var_fraction=round(deg.get(1, 0) / max(1, len(vf)), 4),
           vars_per_fn=dict(p25=q(.25), med=q(.5), p75=q(.75), p90=q(.9), max=sizes[-1]),
           fns_all_shared=priv.get(0, 0), closure_curve=curve,
           components=len(cs), largest=cs[:5], singleton_comps=sum(1 for c in cs if c == 1),
           distance_to_autonomy_hist_by_n_vars=dict(sorted(dist_hist.items())),
           residual_unknown_fns=resid_unknown)
json.dump(out, open(sys.argv[2], "w"), indent=1)
print({k: v for k, v in out.items() if k != "residual_unknown_fns"})
