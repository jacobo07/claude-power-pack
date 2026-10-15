#!/usr/bin/env python3
"""D12b arm-2 pack builder. GEX44. usage: pack.py <cluster> <out_dir>  (seed 20261014; half A = pack, half B = held-out)"""
import json, random, sys, collections
D = "/home/kobii/missions/tennis-w11/out/d28"
SEED = 20261014
cl_id, out = sys.argv[1], sys.argv[2]
C = json.load(open(D + "/d12/struct_clusters.json"))
cl = [c for c in C["clusters"] if c["cluster"] == cl_id][0]
fns = sorted({m["fn"] for m in cl["members"]})
rng = random.Random("%s:%s" % (SEED, cl_id))
sh = fns[:]; rng.shuffle(sh)
half = len(sh) // 2
pack, held = sorted(sh[:half]), sorted(sh[half:])
assert not set(pack) & set(held)
acc = collections.Counter((m["offset"], m["op"], m["width"]) for m in cl["members"] if m["fn"] in set(pack))
# pointee fields: members of other clusters whose root is a FLD of this cluster's root
roots = {json.dumps(m["root"]) for m in cl["members"]}
child = collections.Counter()
for c in C["clusters"]:
    for m in c["members"]:
        r = m["root"]
        if isinstance(r, list) and r and r[0] == "FLD" and json.dumps(r[1]) in roots and m["fn"] in set(pack):
            child[(json.dumps(r), m["offset"], m["op"], m["width"])] += 1
json.dump(dict(cluster=cl_id, seed=SEED, n_fns=len(fns), pack=pack, held_out=held, root_kinds=cl["root_kinds"],
               accesses=sorted([list(k) + [v] for k, v in acc.items()], key=str),
               child_accesses=sorted([list(k) + [v] for k, v in child.items()], key=str)),
          open("%s/pack_%s.json" % (out, cl_id), "w"), indent=1)
print(cl_id, len(fns), len(pack), len(held), cl["root_kinds"], len(acc), len(child))