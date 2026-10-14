#!/usr/bin/env python3
"""D12a step 1: base-object identity.  Run on GEX44:
  export KSR_DECOMP_TOOLS=/opt/ksr-decomp; python3 struct_clusters.py <M> <out_dir> [HUB]
M = /home/kobii/missions/tennis-w11.  Reads D3 residuals.jsonl (NOT modified), asm via asmlib.
Linear (control-flow-insensitive, reset after unconditional branch at a label) provenance of each memory-op base
register: ARG(fn,i) | GLB(sym) | RET(fn,addr) | FLD(root,off) | UNK.  Tier A = congruence of FLD + same GLB.
Tier B = tier A + call edges (caller passes root R as callee arg i  =>  ARG(callee,i) ~ R), hubs excluded.
STRUCTURE only; no semantics.  Writes struct_clusters.json, residuals_v1.jsonl, struct_summary.json."""
import collections, json, os, random, re, sys

M = sys.argv[1] if len(sys.argv) > 1 else "/home/kobii/missions/tennis-w11"
OUT = sys.argv[2] if len(sys.argv) > 2 else M + "/out/d28/d12"
HUB = int(sys.argv[3]) if len(sys.argv) > 3 else 50
sys.path.insert(0, M + "/out/d28/d1d/tools")
import asmlib as A  # noqa: E402

ASM = M + "/wst_tennis/step0/split_sports/out/asm"
SEED = 20261013
ARGREGS = ["r%d" % i for i in range(3, 11)]
UNCOND = ("b", "blr", "bctr")
LO = re.compile(r'^"?([A-Za-z_$][\w$]*)"?@(?:l|sda21|sda2)$')
HA = re.compile(r'^"?([A-Za-z_$][\w$]*)"?@(?:ha|h)$')


def entry_state(fn):
    return {r: (("ARG", fn, i), 0) for i, r in enumerate(ARGREGS)}


def analyse(fn, ins):
    """-> accesses [(addr, op, width, kind, rawoff, root, delta)], calls [(callee, addr, {argreg: (root,delta)})]"""
    st = entry_state(fn)
    acc, calls = [], []
    reset_next = False
    labelled = set()
    for idx, i in enumerate(ins):
        if reset_next and idx in A_LABELIDX:
            st = entry_state(fn)
        reset_next = False
        m = i.m.rstrip(".")
        mo = A.mem_op(i)
        if mo:
            kind, w, off, base, sym = mo
            if sym is not None:
                acc.append((i.addr, i.m, w, kind, 0, ("GLB", sym), 0))
            else:
                rd = st.get(base)
                if rd is not None and rd[0] is not None:
                    acc.append((i.addr, i.m, w, kind, off, rd[0], rd[1] + off))
                else:
                    acc.append((i.addr, i.m, w, kind, off, ("UNK", fn), off))
            if kind == "l" and m not in ("lmw",):
                d = i.ops[0]
                if sym is not None:
                    st[d] = (("FLD", ("GLB", sym), 0), 0) if not d.startswith("f") else (None, 0)
                else:
                    rd = st.get(base)
                    st[d] = (("FLD", rd[0], rd[1] + off), 0) if (rd and rd[0] is not None and not d.startswith("f")) else (None, 0)
            elif kind == "l":
                for k in range(int(i.ops[0][1:]), 32):
                    st["r%d" % k] = (None, 0)
            if m.endswith("u") and m[:-1] in A.WIDTH and mo[4] is None:
                rd = st.get(base)
                if rd and rd[0] is not None:
                    st[base] = (rd[0], rd[1] + off)
            continue
        if m == "bl":
            tgt = A.target(i)
            calls.append((tgt, i.addr, {r: st[r] for r in ARGREGS if st.get(r) and st[r][0] is not None}))
        if m in A.CALLS:
            for r in A.VOLATILE_G:
                st[r] = (None, 0)
            st["r3"] = (("RET", fn, i.addr), 0)
            continue
        if m == "mr" and len(i.ops) == 2:
            st[i.ops[0]] = st.get(i.ops[1], (None, 0))
        elif m == "lis" and len(i.ops) == 2 and HA.match(i.ops[1]):
            st[i.ops[0]] = (("GLB", HA.match(i.ops[1]).group(1)), 0)
        elif m == "addi" and len(i.ops) == 3:
            lo = LO.match(i.ops[2])
            if lo:
                st[i.ops[0]] = (("GLB", lo.group(1)), 0)
            elif A.NUM.match(i.ops[2]):
                rd = st.get(i.ops[1])
                st[i.ops[0]] = (rd[0], rd[1] + A.parse_num(i.ops[2])) if rd and rd[0] is not None else (None, 0)
            else:
                st[i.ops[0]] = (None, 0)
        else:
            for w_ in A.writes(i):
                st[w_] = (None, 0)
        if m in UNCOND:
            reset_next = True
    return acc, calls


A_LABELIDX = set()


class UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        r = x
        while self.p[r] != r:
            r = self.p[r]
        while self.p[x] != r:
            self.p[x], x = r, self.p[x]
        return r

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b:
            self.p[max(a, b, key=repr)] = min(a, b, key=repr)
            return True
        return False


def congruence(uf, flds):
    ch = True
    while ch:
        ch = False
        seen = {}
        for f in flds:
            _, base, off = f
            key = (uf.find(base), off)
            if key in seen:
                ch |= uf.union(f, seen[key])
            else:
                seen[key] = f


def build(prog, fns, tier_b, edges_override=None):
    uf = UF()
    allacc, allcalls = {}, {}
    global A_LABELIDX
    for fn in fns:
        A_LABELIDX = set(prog.labels[fn].values())
        allacc[fn], allcalls[fn] = analyse(fn, prog.fns[fn])
    flds = set()

    def reg(r):
        uf.find(r)
        while r[0] == "FLD":
            flds.add(r)
            r = r[1]
            uf.find(r)
    for fn, accs in allacc.items():
        for a in accs:
            reg(a[5])
    edges = []
    for fn, cs in allcalls.items():
        for callee, addr, args in cs:
            if callee in prog.fns:
                for r, (root, d) in args.items():
                    if d == 0:
                        edges.append((callee, ARGREGS.index(r), root, fn, addr))
    for e in edges:
        reg(e[2])
        reg(("ARG", e[0], e[1]))
    if edges_override is not None:
        edges = edges_override(edges)
    hubs = set()
    if tier_b:
        # fan-in of distinct provenance classes at tier-A congruence
        congruence(uf, flds)
        fan = collections.defaultdict(set)
        for callee, ai, root, _, _ in edges:
            fan[(callee, ai)].add(uf.find(root))
        hubs = {k for k, v in fan.items() if len(v) > HUB}
        for callee, ai, root, _, _ in edges:
            if (callee, ai) not in hubs:
                uf.union(("ARG", callee, ai), root)
    else:
        congruence(uf, flds)
    congruence(uf, flds)
    return uf, allacc, allcalls, edges, hubs


def clusters(uf, allacc, fnset):
    cl = collections.defaultdict(list)
    for fn, accs in allacc.items():
        if fn not in fnset:
            continue
        for addr, op, w, kind, raw, root, eff in accs:
            cl[uf.find(root)].append((fn, addr, op, w, kind, raw, eff, root))
    return cl


def conflicts(members):
    wd = collections.defaultdict(set)
    for fn, addr, op, w, kind, raw, eff, root in members:
        wd[eff].add(w)
    if members and members[0][7][0] == 'UNK':
        return {}  # per-fn untraced bucket: distinct unknown bases, widths not comparable
    return {eff: sorted(ws) for eff, ws in wd.items() if len(ws) > 1}


def conflict_rate(cl):
    """(cluster,offset) pairs with >=2 accesses that carry >1 width / pairs with >=2 accesses; UNK singletons excluded."""
    tot = bad = 0
    for k, mem in cl.items():
        if k[0] == "UNK":
            continue
        wd = collections.defaultdict(list)
        for m_ in mem:
            wd[m_[6]].append(m_[3])
        for ws in wd.values():
            if len(ws) >= 2:
                tot += 1
                bad += len(set(ws)) > 1
    return dict(pairs=tot, conflicting=bad, rate=round(bad / tot, 4) if tot else None)


def name(root):
    return json.dumps(root, separators=(",", ":"))


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = [json.loads(l) for l in open(M + "/out/d28/d3/residuals.jsonl") if l.strip()]
    tgt = [r for r in rows if r.get("distance") in (2, 3, 4, 5)]
    tfn = {r["fn"] for r in tgt}
    prog = A.parse_program(ASM)
    fns = [f for f in prog.order]  # whole program so call edges + congruence see all fns
    print("program fns", len(fns), "target fns", len(tfn), "missing in asm", len(tfn - set(prog.fns)))

    res = {}
    for label, tb in (("A", False), ("B", True)):
        uf, allacc, allcalls, edges, hubs = build(prog, fns, tb)
        cl = clusters(uf, allacc, tfn)
        res[label] = (uf, allacc, cl, edges, hubs)
        nconf = sum(1 for m in cl.values() if conflicts(m))
        print("tier", label, "clusters(target-touched)", len(cl), "with CONFLICT", nconf, "hubs", len(hubs))

    # red control: shuffle which root each (callee,argidx) edge receives, keep callee/argidx multiset
    def shuf(edges):
        rnd = random.Random(SEED)
        roots = [e[2] for e in edges]
        rnd.shuffle(roots)
        return [(e[0], e[1], r, e[3], e[4]) for e, r in zip(edges, roots)]
    ufc, accc, _, _, hubc = build(prog, fns, True, edges_override=shuf)
    clc = clusters(ufc, accc, tfn)
    ctl = dict(clusters=len(clc), conflicts=sum(1 for m in clc.values() if conflicts(m)), hubs=len(hubc),
               rate=conflict_rate(clc), real_A=conflict_rate(res["A"][2]), real_B=conflict_rate(res["B"][2]))

    # supported grouping = tier A (conflict rate below the shuffled control); tier B (call edges) is reported as a bound only
    uf, allacc, cl, edges, hubs = res["A"]
    ufa, _, cla, _, _ = res["B"]
    uf_b, _, cl_b, _, hubs = res["B"]
    ufa, cla = res["A"][0], res["A"][2]
    def distinct_traced(c):
        bf = collections.defaultdict(set)
        for k, mem in c.items():
            if k[0] == "UNK":
                continue
            for m_ in mem:
                bf[(m_[0], m_[5])].add((k, m_[6]))
        out = set()
        for r in tgt:
            for v in r.get("unresolved_vars") or []:
                if v["type"] == "field_offset_untyped":
                    out |= bf.get((r["fn"], int(v["id"], 16)), set())
        return len(out)
    dA, dB = distinct_traced(res["A"][2]), distinct_traced(res["B"][2])
    cid = {}
    for n, (k, mem) in enumerate(sorted(cl.items(), key=lambda kv: (-len(kv[1]), repr(kv[0])))):
        cid[k] = ("U%05d" % n) if k[0] == "UNK" else ("C%04d" % n)
    # per-fn occurrence index: (fn, rawoff or eff) -> cluster ids
    byfo = collections.defaultdict(set)
    byfo_eff = collections.defaultdict(set)
    ev = {}
    for k, mem in cl.items():
        for fn, addr, op, w, kind, raw, eff, root in mem:
            byfo[(fn, raw)].add((cid[k], eff))
            byfo_eff[(fn, eff)].add((cid[k], eff))
            ev[(fn, addr)] = name(root)
    out_clusters = []
    for k, mem in cl.items():
        cf = conflicts(mem)
        out_clusters.append(dict(
            cluster=cid[k], n_access=len(mem), n_fns=len({m_[0] for m_ in mem}),
            root_kinds=dict(collections.Counter(m_[7][0] for m_ in mem)),
            members=[dict(fn=m_[0], addr="%08X" % m_[1], op=m_[2], width=m_[3], offset=m_[6], root=name(m_[7])) for m_ in mem],
            conflict={hex(o): ws for o, ws in cf.items()} or None,
            status="CONFLICT" if cf else "OK",
            tierB_clusters_spanned=len({uf_b.find(m_[7]) for m_ in mem})))
    out_clusters.sort(key=lambda c: c["cluster"])
    json.dump(dict(hub_limit=HUB, hubs=sorted("%s#%d" % h for h in hubs), clusters=out_clusters), open(OUT + "/struct_clusters.json", "w"), indent=0)

    # ---- residuals_v1
    before, after_ids, after_a = set(), set(), set()
    traced = untraced = 0
    n_rows = 0
    with open(OUT + "/residuals_v1.jsonl", "w") as fo:
        for r in rows:
            r2 = json.loads(json.dumps(r))
            if r["distance"] in (2, 3, 4, 5):
                vs, new = r.get("unresolved_vars") or [], []
                struct_ids = []
                for v in vs:
                    if v["type"] == "field_offset_untyped":
                        before.add(r["fn"] + ":" + v["id"])
                        off = int(v["id"], 16)
                        hit = sorted(byfo.get((r["fn"], off), []))
                        if hit and all(c.startswith("U") for c, _ in hit):
                            untraced_base = globals().setdefault("UB", [0]); untraced_base[0] += 1
                        if hit:
                            traced += 1
                            for c, eff in hit:
                                nv = dict(id="STRUCT:%s+0x%X" % (c, eff), type="struct_field", from_var=v["id"],
                                          cluster=c, evidence_in="struct_clusters.json")
                                new.append(nv)
                                struct_ids.append(nv["id"])
                            new[-len(hit):] = [dict(n_, id=n_["id"].replace("STRUCT:U", "STRUCT:UNK-U"), type="struct_field_untraced")
                                               if n_["cluster"].startswith("U") else n_ for n_ in new[-len(hit):]]
                        else:
                            untraced += 1  # no access in this fn with that displacement (NO_ACCESS_MATCH)
                            new.append(dict(id="STRUCT:UNTRACED:%s+%s" % (r["fn"], v["id"]), type="struct_field_untraced", from_var=v["id"]))
                    elif v["type"] == "field_untyped":
                        before.add(v["id"])
                        new.append(dict(v, derived=True))
                    else:
                        new.append(v)
                # field_untyped marker is derived from the struct fields when the fn has any; else stays an independent var
                has_struct = any(n_["type"].startswith("struct_field") for n_ in new)
                final = []
                for n_ in new:
                    if n_.get("derived") and has_struct:
                        n_ = dict(n_, depends_on_struct=True)
                        final.append(n_)
                    else:
                        final.append(n_)
                r2["unresolved_vars"] = final
                r2["v1_collapse"] = "tierA"
            fo.write(json.dumps(r2, separators=(",", ":")) + "\n")
            n_rows += 1
    # distinct-var counts (derived markers with struct ids do not count as independent vars)
    d_after = set()
    for l in open(OUT + "/residuals_v1.jsonl"):
        r = json.loads(l)
        if r["distance"] in (2, 3, 4, 5):
            for v in r.get("unresolved_vars") or []:
                if v.get("depends_on_struct"):
                    continue
                d_after.add(v["id"] if v["type"] != "struct_field_untraced" else v["id"])
    # tier A distinct struct ids for the bound
    summ = dict(rows=n_rows, target_fns=len(tfn), hub_limit=HUB,
                offset_vars_before=len({x for x in before if not x.startswith("FIELD_UNTYPED")}),
                traced_offset_vars=traced, all_unk_base_offset_vars=globals().get("UB", [0])[0], untraced_offset_vars=untraced,
                distinct_vars_after_collapse_tierA_incl_untraced=len(d_after), distinct_struct_ids_traced_tierA=dA, distinct_struct_ids_traced_tierB=dB,
                clusters_A=len(res['A'][2]), clusters_B=len(res['B'][2]),
                conflict_clusters_A=sum(1 for m in res['A'][2].values() if conflicts(m)),
                conflict_clusters_B=sum(1 for m in res['B'][2].values() if conflicts(m)),
                red_control_shuffled_edges=ctl, hubs=len(hubs),
                largest_A=sorted((len(m) for m in cl.values()), reverse=True)[:8], largest_B=sorted((len(m) for m in res['B'][2].values()), reverse=True)[:8])
    json.dump(summ, open(OUT + "/struct_summary.json", "w"), indent=1)
    print(json.dumps(summ))


cl_by_id = {}
if __name__ == "__main__":
    main()
