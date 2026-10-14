#!/usr/bin/env python3
"""D12b arm 2, cluster family of global lbl_80513E74. GEX44.
  split <out>              seeded 50/50 split of the dependents union; prints pack-only accesses per root
  run <out> <hdr_extra.h>  d5.run_set on ALL dependents with header+fact; in-sample vs held-out newly-clean
"""
import json, random, sys, collections, os
D = "/home/kobii/missions/tennis-w11/out/d28"
sys.path.insert(0, D + "/d5/tools"); sys.path.insert(0, D + "/tools")
SEED = 20261014
KEY = sys.argv[3] if len(sys.argv) > 3 and sys.argv[1] == "split" else "lbl_80513E74"
step, out = sys.argv[1], sys.argv[2]
C = json.load(open(D + "/d12/struct_clusters.json"))
mem = [(c["cluster"], m) for c in C["clusters"] for m in c["members"] if KEY in json.dumps(m["root"])]
U = sorted({m["fn"] for _, m in mem})
rng = random.Random("%s:%s" % (SEED, KEY)); sh = U[:]; rng.shuffle(sh)
pack, held = sorted(sh[:len(sh) // 2]), sorted(sh[len(sh) // 2:])
assert not set(pack) & set(held)
if step == "split":
    ps = set(pack)
    acc = collections.defaultdict(collections.Counter)
    for cid, m in mem:
        if m["fn"] in ps:
            acc[json.dumps(m["root"])][(m["offset"], m["op"], m["width"])] += 1
    json.dump(dict(key=KEY, seed=SEED, dependents=U, pack=pack, held_out=held), open(out + "/split_%s.json" % KEY, "w"), indent=1)
    print(len(U), len(pack), len(held))
    for r, c in acc.items():
        print(r, sorted(c.items()))
else:
    import d5
    hdr = open(sys.argv[3]).read().rstrip("\n").split("\n")
    ctx = d5.make_ctx(out + "/ctx_%s.h" % os.path.basename(sys.argv[3]), hdr)
    new, _ = d5.run_set(U, ctx)
    B = d5.load()["base"]
    res = dict(header=sys.argv[3], n=len(U))
    for name, S in (("in_sample", pack), ("held_out", held)):
        un, errs, _r = d5.measure(S, new)
        res[name] = dict(n=len(S), newly_clean=un, errors=errs,
                         base_clean=sum(1 for f in S if B[f]["clean"]),
                         now_clean=sum(1 for f in S if new[f][0]["clean"]),
                         changed=sum(1 for f in S if new[f][0]["c_sha256"] != B[f]["c_sha256"]))
    json.dump(res, open(out + "/arm2_%s.json" % os.path.basename(sys.argv[3]), "w"), indent=1)
    print(json.dumps({k: (v if k in ("header", "n") else {a: (b if not isinstance(b, list) else len(b)) for a, b in v.items()}) for k, v in res.items()}))