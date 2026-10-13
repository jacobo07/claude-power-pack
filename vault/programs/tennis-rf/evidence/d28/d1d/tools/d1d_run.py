"""D1d: (a) idioms check -> idioms_status.json + facts.d1d.jsonl; (b) cluster abstention -> cluster_status.json.
    python3 -I d1d_run.py <d1d_dir>   (needs KSR_DECOMP_TOOLS; reads factor.json, facts.jsonl, asm)"""
import collections, json, os, random, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import asmlib as A, idioms as I, factor as Fa
NSEEDS = 20

def read_fixtures(path):
    blocks, cur = [], None
    for l in open(path):
        l = l.rstrip("\n")
        if l.startswith("### "):
            kv = dict(p.split("=", 1) for p in l[4:].split())
            cur = dict(kv, ins=[]); blocks.append(cur)
        elif l.strip() and cur is not None:
            a, t = l.split(" ", 1); cur["ins"].append(A.Insn(int(a, 16), t.strip()))
    return blocks

def idioms_status(d):
    bl = read_fixtures(os.path.join(d, "idioms_test.txt"))
    st = {}
    for n in I.NAMES:
        pos = [b for b in bl if b["idiom"] == n and b["label"] == "POS"]
        neg = [b for b in bl if b["idiom"] == n and b["label"] == "NEG"]
        pok = [bool(I.DETECT[n](b["ins"])) for b in pos]
        nok = [not I.DETECT[n](b["ins"]) for b in neg]
        if not pos or not neg:
            st[n] = dict(status="ABSTAIN", why="missing %s fixture" % ("positive" if not pos else "negative"))
        elif all(pok) and all(nok):
            st[n] = dict(status="VALID", why="%d pos hit, %d neg clean" % (len(pos), len(neg)),
                         pos=["%s@%s" % (b["fn"], b["addr"]) for b in pos], neg=["%s@%s" % (b["fn"], b["addr"]) for b in neg])
        else:
            st[n] = dict(status="ABSTAIN", why="fixture mismatch pos_ok=%s neg_ok=%s" % (pok, nok))
    json.dump(st, open(os.path.join(d, "idioms_status.json"), "w"), indent=1)
    ab = {n for n, v in st.items() if v["status"] != "VALID"}
    removed = collections.Counter()
    with open(os.path.join(d, "facts.d1d.jsonl"), "w") as w:
        for l in open(os.path.join(d, "facts.jsonl")):
            r = json.loads(l)
            for k in list(r.get("idiom_hits", {})):
                if k in ab:
                    removed[k] += r["idiom_hits"].pop(k)
            w.write(json.dumps(r, sort_keys=True) + "\n")
    print("idioms", {n: v["status"] for n, v in st.items()}, "removed", dict(removed))
    return st

def cluster_status(d):
    fj = json.load(open(os.path.join(d, "factor.json")))["summary"]
    facts = {json.loads(l)["fn"]: json.loads(l) for l in open(os.path.join(d, "facts.jsonl"))}
    names = sorted(facts); N = len(names)
    P = A.parse_program(Fa.ASM)
    blocks, bsizes = {}, {}
    for fn in names:
        bl, ed, back = A.cfg(fn, P.fns[fn], P.labels[fn], P.tables)
        blocks[fn] = (bl, len(ed), back); bsizes[fn] = [e - s for s, e in bl]
    def arity(fn): return tuple(sorted(max(s[0] for s in v) for v in facts[fn]["helper_sig"].values()))
    def skey(fn, sizes, ar):
        bl, ne, back = blocks[fn]
        return (len(bl), ne, back, A.sha(",".join(map(str, sizes))), ar)
    real = Fa.groups_summary(Fa.key_groups({fn: skey(fn, bsizes[fn], arity(fn)) for fn in names}), N)
    redA, redB, seeds = [], [], []
    for s in range(NSEEDS):
        seed = 20261013 + s; seeds.append(seed); rng = random.Random(seed)
        pool = [x for fn in names for x in bsizes[fn]]; rng.shuffle(pool); it = iter(pool)
        kA = {fn: skey(fn, [next(it) for _ in bsizes[fn]], arity(fn)) for fn in names}
        perm = names[:]; rng.shuffle(perm)
        kB = {fn: skey(fn, bsizes[fn], arity(perm[k])) for k, fn in enumerate(names)}
        redA.append(Fa.groups_summary(Fa.key_groups(kA), N)["members_in_groups_ge2"])
        redB.append(Fa.groups_summary(Fa.key_groups(kB), N)["members_in_groups_ge2"])
    R = real["members_in_groups_ge2"]; thr = R * 0.5
    def dist(v): return dict(min=min(v), max=max(v), mean=sum(v) / len(v), values=v, n_le_threshold=sum(1 for x in v if x <= thr))
    sv = "VALID" if max(redA) <= thr and max(redB) <= thr else "INCONCLUSIVE"
    out = dict(rule="VALID iff every permutation's red members_in_groups_ge2 <= 0.5 x real", seeds=seeds, n_permutations=NSEEDS,
        groupings={"structural_family": dict(real=R, threshold=thr, red_pooled_block_sizes=dist(redA), red_permuted_arity=dist(redB), status=sv,
                    p1p2_single_red=[fj["structural_family"]["red_pooled_block_sizes"]["members_in_groups_ge2"], fj["structural_family"]["red_permuted_arity"]["members_in_groups_ge2"], fj["structural_family"]["real"]["members_in_groups_ge2"]])})
    for g in ("data_family", "data_family_anchored", "idiom_family"):
        rr = fj[g]["real"]["members_in_groups_ge2"]; rd = fj[g][[k for k in fj[g] if k.startswith("red")][0]]["members_in_groups_ge2"]
        out["groupings"][g] = dict(real=rr, red_single_seed=rd, threshold=rr * 0.5, status="VALID" if rd <= rr * 0.5 else "INCONCLUSIVE",
                                   note="single P1P2 red (seed %s); 20-permutation rerun applied to the failing grouping only" % fj.get("seed"))
    m = fj["motifs"]; rf, df = m["real"]["covered_fraction"], m["red_shuffled_within_block"]["covered_fraction"]
    out["groupings"]["motifs"] = dict(real=rf, red_single_seed=df, threshold=rf * 0.5, status="VALID" if df <= rf * 0.5 else "INCONCLUSIVE")
    json.dump(out, open(os.path.join(d, "cluster_status.json"), "w"), indent=1)
    print("cluster", {g: v["status"] for g, v in out["groupings"].items()}, "structural real", R, "redA", dist(redA)["min"], dist(redA)["max"], "redB", dist(redB)["min"], dist(redB)["max"])

if __name__ == "__main__":
    d = sys.argv[1]; idioms_status(d); cluster_status(d)
