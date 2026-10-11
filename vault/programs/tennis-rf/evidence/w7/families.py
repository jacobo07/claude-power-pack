"""W7: features, families, novelty density, deterministic share, Scope A closure over all 1,797 Tennis candidates.
Zero model calls, zero compiles. Run: python -I families.py <out_dir>   (needs wst_tennis/w7/m2c_out from m2c_producer)
"""
import collections, hashlib, json, math, os, random, re, sys
sys.path.insert(0, r"C:\Users\User\Apps\recon_work\wst_tennis\step0"); sys.path.insert(0, r"C:\Users\User\Apps\recon_work\wst_tennis\step1")
sys.path.insert(0, r"C:\Users\User\Apps\recon_work\wst_tennis\step2"); sys.path.insert(0, r"C:\Users\User\Apps\recon_work\wst_tennis\step3")
import probe_tennis as p0, probe_step1 as p1, probe_step2 as p2, probe_step3 as p3

W = r"C:\Users\User\Apps\recon_work\wst_tennis\w7"
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
CALL = re.compile(r'^bl\s+(\w+)'); LBL = re.compile(r'\b(lbl_[0-9A-Fa-f_]+)')
BRANCH = re.compile(r'^(b|beq|bne|blt|bgt|ble|bge|bdnz|bdz|bso|bns|bc)[+-]?\s')
MNEM = lambda i: i.split()[0] if i.split() else ""
EXACTNUM = lambda body: hashlib.sha1("\n".join(p0.SYM.sub("S", i) for i in body).encode()).hexdigest()   # numbers kept


def jac(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def cos(a, b):
    d = sum(a[k] * b.get(k, 0) for k in a)
    n = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
    return d / n if n else 0.0


def edges(F):
    """union-find. edge iff shape view S AND (call-context C OR data-context D OR full-body-identical small X)."""
    par = {fn: fn for fn in F}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    by_size = sorted(F, key=lambda f: F[f]["insns"])
    n = 0
    for i, a in enumerate(by_size):
        A = F[a]
        for b in by_size[i + 1:]:
            B = F[b]
            if B["insns"] > A["insns"] * 1.18 + 1:
                break
            S = A["loose"] == B["loose"] or (min(A["insns"], B["insns"]) >= 12 and A["insns"] / B["insns"] >= 0.85 and cos(A["mh"], B["mh"]) >= 0.95)
            if not S:
                continue
            C = jac(A["calls"], B["calls"]) >= 0.5
            D = jac(A["data"], B["data"]) >= 0.5
            X = A["exactnum"] == B["exactnum"] and A["insns"] <= 16
            if C or D or X:
                ra, rb = find(a), find(b)
                if ra != rb:
                    par[ra] = rb
                n += 1
    fam = collections.defaultdict(list)
    for fn in F:
        fam[find(fn)].append(fn)
    return list(fam.values()), n


def main():
    rows = json.load(open(r"C:\Users\User\Apps\recon_work\wst_tennis\w3\tennis_fns.json"))
    names = [r["fn"] for r in rows]
    tset = set(names)
    sf, _, _, sunit = p0.scan(p0.SPORTS)
    fns = p2.parse(p0.SPORTS)
    cand = {}
    for fn, (u, ins) in fns.items():
        if len(ins) > 80:
            continue
        if p3.track(ins, {"r3": "M"}, set())["retc"]:
            cand[fn] = 1
    addr = p1.scan_graph(p0.SPORTS)[5]
    near = {fn for fn in cand if addr.get(fn) is not None and 0x800B7000 <= addr[fn] <= 0x800B9000}
    getters = set(near) | {"fn_801DDEC8"}
    res = {fn: p3.track(ins, {}, getters) for fn, (u, ins) in fns.items()}
    rf, _, _, _ = p0.scan(p0.RESORT)
    rex, rlo = set(), set()
    for b in rf.values():
        if b:
            e, l = p0.shapes(b)
            rex.add(e)
            rlo.add(l)
    callers = collections.defaultdict(set)
    for fn, b in sf.items():
        for i in b:
            m = CALL.match(i)
            if m:
                callers[m.group(1)].add(fn)
    m2c = {}
    tsv = os.path.join(W, "m2c_out", "results.tsv")
    if os.path.exists(tsv):
        for l in open(tsv, encoding="utf-8"):
            p = l.rstrip("\n").split("\t")
            if len(p) >= 2:
                m2c[p[0]] = p[1]

    def cstats(fn):
        f = os.path.join(W, "m2c_out", "c", "main_%08X.c" % addr[fn])
        if not os.path.exists(f):
            return None
        t = open(f, encoding="utf-8", errors="replace").read()
        return dict(unres=len(re.findall(r'(?<![\w])\?(?![\w])', t)), unk=len(re.findall(r'\bunk[0-9A-Fa-f]+\b', t)))
    F = {}
    for r in rows:
        fn = r["fn"]
        b = sf[fn]
        e, l = p0.shapes(b)
        calls = {m.group(1) for i in b for m in [CALL.match(i)] if m}
        data = set(LBL.findall(" ".join(b)))
        blocks = 1 + sum(1 for i in b if BRANCH.match(i))
        mh = collections.Counter(MNEM(i) for i in b)
        c = cstats(fn)
        st = m2c.get("main:%08X" % addr[fn], "NONE")
        gu = bool(res[fn]["c_call"] or res[fn]["c_inline"])
        F[fn] = dict(fn=fn, unit=r["unit"], insns=len(b), blocks=blocks, loose=l, exact=e, exactnum=EXACTNUM(b),
                     calls=calls, data=data, callers=len(callers[fn]), mh=mh,
                     getter_use=gu, getter_read=gu and bool(res[fn]["loads"]),
                     resort=("exact" if e in rex else "loose" if l in rlo else "none"), donor_proven=bool(r["donor_proven"]),
                     m2c=st, unres=c["unres"] if c else None, unk=c["unk"] if c else None)
    fams, nedges = edges(F)
    names_l = sorted(F)

    def permuted(fields, seed):
        rr = random.Random(seed)
        perm = names_l[:]
        rr.shuffle(perm)
        return {fn: {**F[fn], **{k: F[perm[i]][k] for k in fields}} for i, fn in enumerate(names_l)}
    f1, e1 = edges(permuted(("calls", "data", "exactnum"), 1))
    f2, e2 = edges(permuted(("loose", "mh"), 2))
    fams_b, _ = edges(F)
    deterministic_rerun = sorted(map(sorted, fams)) == sorted(map(sorted, fams_b))

    def summ(fl):
        sz = sorted((len(f) for f in fl), reverse=True)
        return dict(families=len(fl), singletons=sum(1 for s in sz if s == 1), largest=sz[:5], in_ge3=sum(s for s in sz if s >= 3),
                    hist={"1": sum(1 for s in sz if s == 1), "2": sum(1 for s in sz if s == 2), "3-5": sum(1 for s in sz if 3 <= s <= 5),
                          "6-20": sum(1 for s in sz if 6 <= s <= 20), ">20": sum(1 for s in sz if s > 20)})
    N = len(F)
    fam_of = {fn: i for i, f in enumerate(fams) for fn in f}
    w5_verified = set()   # W5a/W5b receipts: 0 verified members
    elig_donor = {fn for fn in F if F[fn]["donor_proven"] and F[fn]["resort"] == "exact"}
    m2c_clean = {fn for fn in F if F[fn]["m2c"] == "L1" and F[fn]["unres"] == 0 and F[fn]["unk"] == 0}
    elig_fam = {fn for fn in m2c_clean if any(m in w5_verified for m in fams[fam_of[fn]])}
    elig = elig_donor | elig_fam
    cfn = sorted(fn for fn in F if F[fn]["getter_use"])
    REGS = ["r%d" % i for i in range(3, 11)]

    def arg_taint(ins):
        """probe_step3.track clone: at each direct bl, record (callee, callee is getter, an arg register holds a controller)."""
        regs, out = {}, []
        for t in ins:
            mn = MNEM(t)
            m = CALL.match(t)
            if m or mn == "bctrl":
                if m:
                    out.append((m.group(1), m.group(1) in getters, any(regs.get(r) == "C" for r in REGS)))
                for k in p3.VOL:
                    regs.pop(k, None)
                if m and m.group(1) in getters:
                    regs["r3"] = "C"
                continue
            m2 = p3.GL.match(t)
            if m2:
                if m2.group(3) in p2.TARGETS:
                    regs[m2.group(2)] = "M"
                else:
                    regs.pop(m2.group(2), None)
                continue
            if p2.STOP.match(t):
                continue
            m2 = p3.LDX.match(t)
            if m2:
                d, a, b = m2.group(2), m2.group(3), m2.group(4)
                if regs.get(a) == "A" or regs.get(b) == "A":
                    regs[d] = "C"
                else:
                    regs.pop(d, None)
                continue
            m2 = p3.LD.match(t)
            if m2:
                op, d, o_s, base = m2.groups()
                o = p3.off(o_s)
                st = regs.get(base)
                if st == "M" and o == 0x1C:
                    new = "A"
                elif st == "A" and o is not None and 0 <= o <= 0xC and op.startswith("lwz"):
                    new = "C"
                else:
                    new = None
                if new:
                    regs[d] = new
                else:
                    regs.pop(d, None)
                continue
            m2 = p3.MR.match(t)
            if m2:
                if m2.group(2) in regs:
                    regs[m2.group(1)] = regs[m2.group(2)]
                else:
                    regs.pop(m2.group(1), None)
                continue
            if not mn.startswith(p2.NOWRITE):
                parts = t.split()
                if len(parts) > 1:
                    regs.pop(parts[1].rstrip(","), None)
        return out
    passed, upper = set(), set()
    # red control for the closure tracker: a synthetic body that passes a controller to a callee must be found, one that does not must not
    syn_pos = ["lwz r3, lbl_805133B8@sda21(r0)", "lwz r4, 0x1c(r3)", "lwz r5, 0x4(r4)", "mr r3, r5", "bl fn_SYN"]
    syn_neg = ["lwz r3, lbl_805133B8@sda21(r0)", "lwz r4, 0x1c(r3)", "lwz r5, 0x4(r4)", "li r3, 0", "li r4, 0", "li r5, 0", "bl fn_SYN"]
    ctrl = (arg_taint(syn_pos), arg_taint(syn_neg))
    for fn in cfn:
        for callee, isg, hasC in arg_taint(fns[fn][1]):
            if callee in tset and callee not in getters and callee not in cfn:
                upper.add(callee)
                if hasC:
                    passed.add(callee)
    closure = set(cfn) | passed
    closure_upper = set(cfn) | upper
    cl_f = {fam_of[fn] for fn in closure}
    clu_f = {fam_of[fn] for fn in closure_upper}
    summary = dict(
        N=N,
        method=dict(views="S=loose-shape-hash equal OR (>=12 insns, size ratio>=0.85, mnemonic cosine>=0.95); C=callee-set Jaccard>=0.5 (both nonempty); D=lbl-data-object-set Jaccard>=0.5 (both nonempty); X=full-body identical incl. numbers and <=16 insns. Edge iff S and (C or D or X). Families = connected components.",
                    seed=20261013, edges=nedges),
        families=summ(fams), red_control_permute_context=summ(f1) | {"edges": e1}, red_control_permute_shape=summ(f2) | {"edges": e2},
        deterministic_rerun_identical=deterministic_rerun,
        recurrence_fns_in_families_ge3=summ(fams)["in_ge3"], novelty_density=len(fams) / N,
        resort_match=dict(collections.Counter(F[fn]["resort"] for fn in F)),
        donor_proven_exact=len(elig_donor), m2c_status=dict(collections.Counter(F[fn]["m2c"] for fn in F)),
        m2c_clean_zero_unres_unk=len(m2c_clean), eligible_deterministic=len(elig), eligible_share=len(elig) / N,
        eligible_donor_only=len(elig_donor), eligible_via_family_verified=len(elig_fam), model_needed=N - len(elig), model_needed_share=1 - len(elig) / N,
        potential_if_m2c_clean_verified=len(elig | m2c_clean),
        scopeA=dict(getter_callers=len(cfn), arg_propagated_callees=len(passed), closure=len(closure), closure_families=len(cl_f),
                    upper_all_callees=len(closure_upper), upper_families=len(clu_f),
                    closure_in_eligible=len(closure & elig), closure_m2c_clean=len(closure & m2c_clean),
                    tracker_control=dict(positive_hasC=[x[2] for x in ctrl[0]], negative_hasC=[x[2] for x in ctrl[1]]),
                    definition="closure = the step3 getter callers (Tennis-unit functions with a tracked call to a controller getter or inline manager->array->controller load) PLUS Tennis-candidate callees receiving a controller-tainted value in r3-r10 at a direct bl (one level, same linear tracker as step3, getters excluded). upper = all Tennis-candidate direct callees of the getter callers."))
    # W5 cross-check: do the 18 drawn functions' family-mates look like them (unresolved-type / unk counts from the fresh m2c run)?
    ev = os.path.dirname(os.path.abspath(__file__)) + os.sep + ".."
    d5a = json.load(open(os.path.join(ev, "w5a", "draw.json")))
    d5b = json.load(open(os.path.join(ev, "w5b", "w5b_records.json")))
    w5rows = []
    for fn in [x["fn"] for k in ("clean", "few") for x in d5a.get(k, [])] + [x["fn"] for x in d5b["picks"]]:
        if fn not in F:
            continue
        mates = [m for m in fams[fam_of[fn]] if m != fn]
        mu = [F[m]["unres"] for m in mates if F[m]["unres"] is not None]
        w5rows.append(dict(fn=fn, family_size=len(mates) + 1, own_unres=F[fn]["unres"], mate_unres_min=min(mu) if mu else None,
                           mate_unres_max=max(mu) if mu else None, mates_donor_proven=sum(1 for m in mates if m in elig_donor)))
    summary["w5_cross_check"] = dict(n=len(w5rows), in_family_of_ge2=sum(1 for r in w5rows if r["family_size"] >= 2),
                                     own_within_mate_range=sum(1 for r in w5rows if r["mate_unres_min"] is not None and r["mate_unres_min"] <= r["own_unres"] <= r["mate_unres_max"]),
                                     rows=w5rows)
    summary["loose_donor_proven_extra"] = sum(1 for fn in F if F[fn]["donor_proven"] and F[fn]["resort"] == "loose")
    os.makedirs(OUT, exist_ok=True)
    fam_out = []
    for i, f in sorted(enumerate(fams), key=lambda t: -len(t[1])):
        fam_out.append(dict(id=i, size=len(f), members=sorted(f), loose_hashes=len({F[m]["loose"] for m in f}),
                            insns_median=sorted(F[m]["insns"] for m in f)[len(f) // 2],
                            donor_proven=sum(1 for m in f if m in elig_donor), in_closure=sum(1 for m in f if m in closure)))
    json.dump(dict(summary=summary, families=fam_out, closure=sorted(closure), closure_upper=sorted(closure_upper)),
              open(os.path.join(OUT, "families.json"), "w"), indent=1)
    feat = [{k: (sorted(v) if isinstance(v, set) else v) for k, v in F[fn].items() if k != "mh"} | {"family": fam_of[fn]} for fn in names_l]
    json.dump(feat, open(os.path.join(OUT, "features.json"), "w"))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
