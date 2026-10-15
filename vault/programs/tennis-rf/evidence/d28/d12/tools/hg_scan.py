"""Read-only reality scan: sharing structure of class 2-5 residuals (D3 residuals.jsonl)."""
import json, sys, collections

rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
tgt = [r for r in rows if r.get("distance") in (2, 3, 4, 5)]
print("class2-5 fns", len(tgt), "dist", collections.Counter(r["distance"] for r in tgt))

PES = len(sys.argv) > 2
key = lambda r, v: (r["fn"] + ":" + v["id"]) if (PES and v["type"] == "field_offset_untyped") else v["id"]
if PES:
    tgt = [r for r in tgt if not any(v["type"] in ("m2c", "m2c_failed") for v in r.get("unresolved_vars") or [])]
    print("pessimistic: offsets private, m2c fns dropped ->", len(tgt))
fv = {r["fn"]: {key(r, v) for v in r.get("unresolved_vars") or []} for r in tgt}
kinds = collections.Counter(v["type"] for r in tgt for v in r.get("unresolved_vars") or [])
print("var-occurrence kinds", dict(kinds))
nov = [r["fn"] for r in tgt if not fv[r["fn"]]]
print("fns with no named var (UNKNOWN residual)", len(nov))

vf = collections.defaultdict(set)
for f, vs in fv.items():
    for v in vs:
        vf[v].add(f)
deg = collections.Counter(len(s) for s in vf.values())
print("distinct vars", len(vf), "occurrences", sum(len(s) for s in vf.values()))
print("vars by degree: 1:%d 2-4:%d 5-19:%d 20+:%d" % (
    sum(c for d, c in deg.items() if d == 1), sum(c for d, c in deg.items() if 2 <= d <= 4),
    sum(c for d, c in deg.items() if 5 <= d <= 19), sum(c for d, c in deg.items() if d >= 20)))
sizes = sorted(len(v) for v in fv.values() if v)
q = lambda p: sizes[int(p * (len(sizes) - 1))]
print("vars per fn p25/med/p75/p90/max", q(.25), q(.5), q(.75), q(.9), sizes[-1])
priv = collections.Counter(sum(1 for v in fv[f] if len(vf[v]) == 1) for f in fv if fv[f])
print("fns whose vars are ALL shared (no private var)", priv.get(0, 0))

# Greedy closure: resolve vars one at a time choosing the var that completes most fns soonest
# (cost = vars resolved; a fn counts only when ALL its vars are resolved -> conjunctive unlock).
remaining = {f: set(v) for f, v in fv.items() if v}
resolved, done, curve = set(), 0, []
marks = {50, 100, 200, 400, 600, 800, 1000, 1200}
while remaining:
    # pick the fn with fewest unresolved vars (ties: most-shared vars), resolve all its vars
    f = min(remaining, key=lambda k: (len(remaining[k]), -sum(len(vf[v]) for v in remaining[k])))
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
print("conjunctive closure (fns fully unblocked, vars resolved):", curve)

# connected components of the fn-var bipartite graph
par = {}
def find(x):
    while par.setdefault(x, x) != x:
        par[x] = par[par[x]]
        x = par[x]
    return x
for f, vs in fv.items():
    for v in vs:
        par[find("f:" + f)] = find("v:" + v)
comp = collections.Counter(find("f:" + f) for f in fv if fv[f])
cs = sorted(comp.values(), reverse=True)
print("components", len(cs), "largest", cs[:5], "singleton-fn comps", sum(1 for c in cs if c == 1))
