"""WU-P1P2 Pass 2 + Knowledge Shock. Zero model, zero compile: reads facts.jsonl, the m2c run records/outputs, the asm,
W7 features, the context header. Writes factor.json, blockers.json, hypotheses.json, knowledge_shock.json and merges
m2c_with_ctx into facts.jsonl.

    python3 -I factor.py <p1p2_dir>
Every grouping is STRUCTURAL ("structural family", "data family", ...), never a claim of same code. Red controls:
pre-declared COLLAPSE iff red members-in-groups>=2 <= 0.5 x real (groupings), red covered-insn fraction <= 0.5 x real
(motifs). A grouping whose red control does not collapse is reported INCONCLUSIVE.
"""
import collections
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asmlib as A  # noqa: E402
import extract  # noqa: E402
import idioms  # noqa: E402

M = "/home/kobii/missions/tennis-w11"
ASM = os.path.join(M, "wst_tennis/step0/split_sports/out/asm")
W7 = os.path.join(M, "trf/measure/features.json")
GEX = os.path.join(M, "wt/tools/wros/binary/decomp/gex44")
sys.path.insert(0, GEX)
import source_lint  # noqa: E402
import tennis_context  # noqa: E402

SEED = 20261012
MOTIF_LEN, MOTIF_MIN_FNS, DATA_MIN, JAC = 6, 3, 3, 0.5
PROTO = re.compile(r'^\s*([\w\s\*]+?)\s*\b(fn_[0-9A-Fa-f]{8})\s*\(([^)]*)\)\s*;', re.M)
EXTERN = re.compile(r'^(.*\b(\w+)\s*\(.*\)\s*;)\s*/\*\s*(?:extern|static)\s*\*/', re.M)
UNKREF = re.compile(r'([A-Za-z_]\w*)\s*(\[[^\]]*\])?\s*(->|\.)\s*unk([0-9A-Fa-f]+)\b')
M2CERR = re.compile(r'M2C_ERROR\(/\*\s*(.*?)\s*\*/\)')


def uf(keys):
    par = {k: k for k in keys}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            par[max(ra, rb)] = min(ra, rb)
    return find, union


def groups_summary(groups, n_total):
    sz = sorted((len(g) for g in groups), reverse=True)
    return dict(groups=len(groups), members_in_groups_ge2=sum(s for s in sz if s >= 2), groups_ge2=sum(1 for s in sz if s >= 2),
                largest=sz[:5], singletons=sum(1 for s in sz if s == 1), n_total=n_total)


def key_groups(keymap):
    g = collections.defaultdict(list)
    for fn, k in keymap.items():
        if k is not None:
            g[k].append(fn)
    return sorted((sorted(v) for v in g.values()), key=lambda v: (-len(v), v[0]))


def jaccard_groups(sets):
    fns = sorted(f for f, s in sets.items() if len(s) >= DATA_MIN)
    find, union = uf(fns)
    inv = collections.defaultdict(list)
    for f in fns:
        for e in sets[f]:
            inv[e].append(f)
    seen = set()
    for f in fns:
        cand = set()
        for e in sets[f]:
            cand.update(inv[e])
        for g in cand:
            if g <= f or (f, g) in seen:
                continue
            seen.add((f, g))
            a, b = sets[f], sets[g]
            if len(a & b) / len(a | b) >= JAC:
                union(f, g)
    comp = collections.defaultdict(list)
    for f in fns:
        comp[find(f)].append(f)
    return sorted((sorted(v) for v in comp.values()), key=lambda v: (-len(v), v[0]))


def collapse(real, red, field="members_in_groups_ge2"):
    return red[field] <= 0.5 * real[field] if real[field] else False


def header_info(text):
    tags = tennis_context.members(text)
    proto = {}
    for ret, fn, params in PROTO.findall(text):
        gi, regs = 3, {}
        for p in [x.strip() for x in params.split(",") if x.strip() and x.strip() != "void"]:
            if re.match(r'^(f32|f64|float|double)\b', p) and "*" not in p:
                continue
            m = re.match(r'^(?:const\s+)?(\w+)\s*\*', p)
            if m and m.group(1) in tags:
                regs["r%d" % gi] = m.group(1)
            gi += 1
        proto[fn] = regs
    return tags, proto


def anchor(origin, regs):
    if origin.startswith(("&", "*lbl", "*(&", "*(*")) or (origin.startswith("*") and not origin.startswith("*(r")):
        return origin, True
    m = re.match(r'^(\*\()?(r\d+)(.*)$', origin)
    if m and m.group(2) in regs:
        return "%sT:%s%s" % (m.group(1) or "", regs[m.group(2)], m.group(3)), True
    return "arg:" + origin, False


def motif_index(seqs):
    """seqs: {fn: [(block insns list)]}. Returns ({key: set(fn)}, {fn: [(key, start index)]})."""
    occ, where = collections.defaultdict(set), collections.defaultdict(list)
    for fn, blocks in seqs.items():
        base = 0
        for b in blocks:
            for j in range(0, len(b) - MOTIF_LEN + 1):
                k = A.sha(A.normalise_window(b[j:j + MOTIF_LEN]))
                occ[k].add(fn)
                where[fn].append((k, base + j))
            base += len(b)
    return occ, where


def motif_cover(occ, where, sizes):
    mot = {k for k, v in occ.items() if len(v) >= MOTIF_MIN_FNS}
    cov = {}
    for fn, n in sizes.items():
        c = set()
        for k, s in where.get(fn, ()):
            if k in mot:
                c.update(range(s, s + MOTIF_LEN))
        cov[fn] = c
    return mot, cov


def m2c_key(rec, text):
    keys = set()
    if rec["status"] == "M2C_ERROR":
        for msg in M2CERR.findall(text):
            m = re.match(r'unknown instruction:\s*(\S+)', msg)
            keys.add("M2C:unknown instruction %s" % m.group(1) if m else "M2C:" + re.sub(r'[0-9A-Fa-fx$]{3,}|\d+', "#", msg)[:50])
    elif rec["status"] != "L1":
        e = re.sub(r'^Decompilation failure in function \S+:\s*', "", rec["error"])
        keys.add("%s:%s" % (rec["status"], re.sub(r'\b(?:fn|lbl)_\w+|0x[0-9A-Fa-f]+|\$?\b\d+\b', "#", e)[:60]))
    return keys


def blockers_of(fn, rec, text, tags):
    keys = m2c_key(rec, text)
    if rec["status"] != "L1" or rec["clean"]:
        return keys, []
    lines = text.splitlines()
    proto_lines, rest = set(), []
    for m in EXTERN.finditer(text):
        decl, name = m.group(1), m.group(2)
        proto_lines.add(m.group(0))
        if re.search(r'(?<![\w])\?(?![\w])', decl):
            keys.add("HELPER:" + name)
    body = [ln for ln in lines if ln not in proto_lines and not EXTERN.match(ln)]
    own = next((ln for ln in body if re.match(r'^[^\s/].*\(.*\)\s*\{\s*$', ln)), "")
    if re.search(r'(?<![\w])\?(?![\w])', source_lint.strip_noise(own)):
        keys.add("SELF_SIG:" + fn)
    rest_txt = "\n".join(ln for ln in body if ln != own)
    if source_lint._QMARK_TYPE.search(source_lint.strip_noise(rest_txt)):
        keys.add("QTYPE_LOCAL:" + fn)
    untyped = []
    code = source_lint.strip_noise(text)
    for base, _, op, off in UNKREF.findall(code):
        if base.startswith("lbl_"):
            keys.add("FIELD:%s+0x%s" % (base, off.upper()))
            continue
        tm = re.search(r'\b(\w+)\s*\*\s*' + re.escape(base) + r'\b', code) if op == "->" else None
        if tm and tm.group(1) in tags:
            keys.add("FIELD:%s+0x%s" % (tm.group(1), off.upper()))
        else:
            untyped.append("0x" + off.upper())
    if untyped:
        keys.add("FIELD_UNTYPED:" + fn)
    for x in rec.get("lint_composed", []):
        if x.startswith("UNDECLARED_TYPE"):
            for t in re.findall(r'type\(s\) (.*) used', x)[0].split(", "):
                keys.add("UNDECLARED:" + t)
    return keys, sorted(set(untyped))


def entry_evidence(ins):
    """Linear read-before-write of r3..r10 / f1..f8 from entry, and r3/f1 written before a blr (callee body evidence)."""
    written, read_first, ret = set(), set(), set()
    for i in ins:
        for r in A.reads(i):
            if r in extract.ARGS + extract.FARGS and r not in written:
                read_first.add(r)
        if i.m in A.CALLS:
            break
        written |= A.writes(i)
        if i.m == "blr":
            ret |= {r for r in ("r3", "f1") if r in written}
    return sorted(read_first, key=lambda r: (r[0], int(r[1:]))), sorted(ret)


def main(d):
    facts = [json.loads(l) for l in open(os.path.join(d, "facts.jsonl"))]
    F = {r["fn"]: r for r in facts}
    names = sorted(F)
    N = len(names)
    recs = {}
    for arm in ("ctx_run1", "ctx_run2", "noctx_run1", "noctx_run2"):
        recs[arm] = {json.loads(l)["fn"]: json.loads(l) for l in open(os.path.join(d, "m2c", arm, "records.jsonl"))}
    ctext = {fn: (open(os.path.join(d, "m2c", "ctx_run1", "c", fn + ".c"), encoding="utf-8").read()
                  if os.path.exists(os.path.join(d, "m2c", "ctx_run1", "c", fn + ".c")) else "") for fn in names}
    htext = open(os.path.join(d, "ctx", "tennis_context.h"), encoding="utf-8").read()
    tags, proto = header_info(htext)
    draws = set(open(os.path.join(d, "w12_draw_ids.txt")).read().split())
    w7 = {r["fn"]: r for r in json.load(open(W7))}
    P = A.parse_program(ASM)

    # ---- merge m2c_with_ctx into facts
    for fn in names:
        r = recs["ctx_run1"][fn]
        F[fn]["m2c_with_ctx"] = dict(status=r["status"], clean=r["clean"], n_unresolved_types=r["n_unresolved_types"],
                                     n_unk_fields=r["n_unk_fields"], lint_codes=r["lint_codes"], c_sha256=r["c_sha256"])
    with open(os.path.join(d, "facts.jsonl"), "w") as w:
        for fn in [r["fn"] for r in facts]:
            w.write(json.dumps(F[fn], sort_keys=True) + "\n")

    # ---- knowledge shock
    def clean(arm):
        return {fn for fn, r in recs[arm].items() if r["clean"]}
    c1, c2, n1, n2 = clean("ctx_run1"), clean("ctx_run2"), clean("noctx_run1"), clean("noctx_run2")
    newly = sorted(c1 - n1)
    proto_names = set(proto)
    ks_rows = []
    for fn in newly:
        t = ctext[fn]
        ks_rows.append(dict(fn=fn, tags=sorted(tg for tg in tags if re.search(r'\b%s\b' % tg, t)),
                            header_prototypes=sorted(p for p in proto_names if p != fn and re.search(r'\b%s\b' % p, t)),
                            own_prototype_in_header=fn in proto_names, in_24_draws=fn in draws))
    tag_count = collections.Counter(tg for r in ks_rows for tg in r["tags"])
    shock = dict(
        definition=dict(before="m2c WITHOUT --context; clean = L1 and source_lint(M2C_TYPES + text) == []",
                        after="m2c WITH --context out/p1p2/ctx/tennis_context.h (sha256 = the gex44 header); clean = L1 and "
                              "source_lint(compose(text)) == []", lint_family_flags="C / -lang c"),
        n=N, clean_before=len(n1), clean_after=len(c1), newly_clean=len(newly), newly_dirty=sorted(n1 - c1),
        newly_clean_outside_24_draws=sorted(r["fn"] for r in ks_rows if not r["in_24_draws"]),
        newly_clean_inside_24_draws=sorted(r["fn"] for r in ks_rows if r["in_24_draws"]),
        newly_clean_with_no_struct_tag=sorted(r["fn"] for r in ks_rows if not r["tags"]),
        struct_tags_referenced_by_newly_clean=dict(sorted(tag_count.items())), struct_tags_total=len(tags),
        rows=ks_rows,
        reproduce=dict(ctx_clean_sets_equal=c1 == c2, noctx_clean_sets_equal=n1 == n2,
                       ctx_sha_equal=all(recs["ctx_run1"][f]["c_sha256"] == recs["ctx_run2"][f]["c_sha256"] for f in names),
                       noctx_sha_equal=all(recs["noctx_run1"][f]["c_sha256"] == recs["noctx_run2"][f]["c_sha256"] for f in names)),
        status_counts={arm: dict(collections.Counter(r["status"] for r in recs[arm].values())) for arm in recs},
        w7_status_counts=dict(collections.Counter(w7[f]["m2c"] for f in names)),
        knowledge_leverage_ratio_input=dict(newly_clean=len(newly), newly_clean_outside_draws=len([r for r in ks_rows if not r["in_24_draws"]]),
                                            tokens="filled by the coordinator (W11 3.02M GEX44 + laptop sessions, W12-prep 2.50M)"))
    json.dump(shock, open(os.path.join(d, "knowledge_shock.json"), "w"), indent=1)

    # ---- per-function structure: blocks, motifs, idiom spans, known-struct access sites
    rng = random.Random(SEED)
    blocks, bsizes, seqs, spans, known = {}, {}, {}, {}, {}
    for fn in names:
        ins = P.fns[fn]
        bl, ed, back = A.cfg(fn, ins, P.labels[fn], P.tables)
        blocks[fn] = (bl, len(ed), back)
        bsizes[fn] = [e - s for s, e in bl]
        seqs[fn] = [ins[s:e] for s, e in bl]
        spans[fn] = idioms.spans(ins)
        _, _, sites = extract.track(ins)
        regs = proto.get(fn, {})
        cited = {tg: {o for _, o in rows if o is not None} for tg, rows in tags.items()}
        known[fn] = {k for k, o, off in sites if o in regs and off in cited[regs[o]]}

    def arity_profile(fn):
        return tuple(sorted(max(s[0] for s in v) for v in F[fn]["helper_sig"].values()))

    def skey(fn, sizes, ar):
        bl, ne, back = blocks[fn]
        return (len(bl), ne, back, A.sha(",".join(map(str, sizes))), ar)
    sk = {fn: skey(fn, bsizes[fn], arity_profile(fn)) for fn in names}
    struct_groups = key_groups(sk)
    # red A: pool all block sizes and redistribute (block counts kept); red B: arity profiles permuted across functions
    pool = [s for fn in names for s in bsizes[fn]]
    rng.shuffle(pool)
    it, redA = iter(pool), {}
    for fn in names:
        redA[fn] = skey(fn, [next(it) for _ in bsizes[fn]], arity_profile(fn))
    perm = names[:]
    rng.shuffle(perm)
    redB = {fn: skey(fn, bsizes[fn], arity_profile(perm[k])) for k, fn in enumerate(names)}
    s_real = groups_summary(struct_groups, N)
    s_redA, s_redB = groups_summary(key_groups(redA), N), groups_summary(key_groups(redB), N)

    # data family
    dsets, dsets_anch = {}, {}
    for fn in names:
        regs = proto.get(fn, {})
        full, anch = set(), set()
        for o, off, wd, rw, op, use in F[fn]["field_accesses"]:
            a, ok = anchor(o, regs)
            full.add((a, off, wd))
            if ok:
                anch.add((a, off, wd))
        dsets[fn], dsets_anch[fn] = full, anch

    def shuffled_sets(sets):
        part = [f for f in names if len(sets[f]) >= DATA_MIN]
        el = [e for f in part for e in sorted(sets[f])]
        rng.shuffle(el)
        out, it2 = {f: set() for f in names}, iter(el)
        for f in part:
            out[f] = {next(it2) for _ in sets[f]}
        return out
    data_groups, data_groups_anch = jaccard_groups(dsets), jaccard_groups(dsets_anch)
    d_real, d_red = groups_summary(data_groups, N), groups_summary(jaccard_groups(shuffled_sets(dsets)), N)
    da_real, da_red = groups_summary(data_groups_anch, N), groups_summary(jaccard_groups(shuffled_sets(dsets_anch)), N)

    # idiom family
    ik = {fn: (tuple(sorted(F[fn]["idiom_hits"].items())) or None) for fn in names}
    toks = [k for fn in names for k, v in sorted(F[fn]["idiom_hits"].items()) for _ in range(v)]
    rng.shuffle(toks)
    it3, ired = iter(toks), {}
    for fn in names:
        n_t = sum(F[fn]["idiom_hits"].values())
        ired[fn] = tuple(sorted(collections.Counter(next(it3) for _ in range(n_t)).items())) or None
    idiom_groups = key_groups(ik)
    i_real, i_red = groups_summary(idiom_groups, N), groups_summary(key_groups(ired), N)

    # motifs
    occ, where = motif_index(seqs)
    sizes = {fn: F[fn]["size_insns"] for fn in names}
    motifs, cov = motif_cover(occ, where, sizes)
    red_seqs = {}
    for fn in names:
        bl2 = []
        for b in seqs[fn]:
            b = b[:]
            rng.shuffle(b)
            bl2.append(b)
        red_seqs[fn] = bl2
    occ_r, where_r = motif_index(red_seqs)
    motifs_r, cov_r = motif_cover(occ_r, where_r, sizes)
    tot = sum(sizes.values())
    m_real = dict(motifs=len(motifs), fns_with_motif=sum(1 for f in names if cov[f]), covered_insns=sum(len(c) for c in cov.values()),
                  covered_fraction=sum(len(c) for c in cov.values()) / tot)
    m_red = dict(motifs=len(motifs_r), fns_with_motif=sum(1 for f in names if cov_r[f]), covered_insns=sum(len(c) for c in cov_r.values()),
                 covered_fraction=sum(len(c) for c in cov_r.values()) / tot)
    mid = {k: "M%05d" % j for j, k in enumerate(sorted(motifs, key=lambda k: (-len(occ[k]), k)))}

    def gid(groups, prefix):
        out = {}
        for j, g in enumerate(groups):
            for f in g:
                out[f] = ("%s%04d" % (prefix, j)) if len(g) >= 2 else None
        return out
    sg, dg, dag, ig = gid(struct_groups, "S"), gid(data_groups, "D"), gid(data_groups_anch, "DA"), gid(idiom_groups, "I")
    for fn in names:  # outside a partition (data set below DATA_MIN, zero idiom hits): no group id; basis recorded per fn
        for m in (sg, dg, dag, ig):
            m.setdefault(fn, None)

    verdict = {
        "structural_family": "PROVEN" if collapse(s_real, s_redA) and collapse(s_real, s_redB) else "INCONCLUSIVE",
        "data_family": "PROVEN" if collapse(d_real, d_red) else "INCONCLUSIVE",
        "data_family_anchored": "PROVEN" if collapse(da_real, da_red) else "INCONCLUSIVE",
        "idiom_family": "PROVEN" if collapse(i_real, i_red) else "INCONCLUSIVE",
        "motifs": "PROVEN" if m_red["covered_fraction"] <= 0.5 * m_real["covered_fraction"] else "INCONCLUSIVE",
    }

    # residual_structural
    per_fn, resid = {}, {}
    for fn in names:
        n = sizes[fn]
        ispan = {k for v in spans[fn].values() for s in v for k in s}
        covered = cov[fn] | ispan | known[fn]
        resid[fn] = 1 - len(covered) / n if n else 0.0
        motif_ids = sorted({mid[k] for k, s in where.get(fn, ()) if k in mid})
        per_fn[fn] = dict(exact_family=w7[fn]["family"], structural_family=sg[fn], data_family=dg[fn], data_family_anchored=dag[fn],
                          data_basis=("below_DATA_MIN" if len(dsets[fn]) < DATA_MIN else "partitioned"),
                          data_anchored_basis=("below_DATA_MIN" if len(dsets_anch[fn]) < DATA_MIN else "partitioned"),
                          idiom_family=ig[fn], proof_family="UNKNOWN", motif_ids=motif_ids,
                          residual_structural=round(resid[fn], 4),
                          coverage=dict(motif=len(cov[fn]), idiom=len(ispan), known_struct=len(known[fn]), size=n))
    w7_fam = collections.Counter(w7[f]["family"] for f in names)
    w7_single = {f for f in names if w7_fam[w7[f]["family"]] == 1}
    rec_by = {
        "structural_family": {f for f in w7_single if sg[f]}, "data_family": {f for f in w7_single if dg[f]},
        "data_family_anchored": {f for f in w7_single if dag[f]}, "idiom_family": {f for f in w7_single if ig[f]},
        "motifs": {f for f in w7_single if per_fn[f]["motif_ids"]}}
    union_all = set().union(*rec_by.values())
    union_proven = set().union(*[v for k, v in rec_by.items() if verdict[k] == "PROVEN"])
    rs = sorted(resid.values())
    deciles = {"p%d" % (10 * q): round(rs[min(N - 1, int(q * N / 10))], 4) for q in range(0, 11)}
    roles = collections.Counter(F[f]["role"] for f in names)
    summary = dict(
        n=N, seed=SEED, params=dict(motif_len=MOTIF_LEN, motif_min_fns=MOTIF_MIN_FNS, data_min_set=DATA_MIN, jaccard=JAC,
                                    collapse_rule="red members_in_groups_ge2 <= 0.5 x real; motifs: red covered_fraction <= 0.5 x real"),
        structural_family=dict(real=s_real, red_pooled_block_sizes=s_redA, red_permuted_arity=s_redB, verdict=verdict["structural_family"],
                               key="(blocks, edges, back-edge loops, sha(ordered block sizes) [implies size], callee gpr-arity profile)"),
        data_family=dict(real=d_real, red_pooled_elements=d_red, verdict=verdict["data_family"],
                         key="set of (base anchor, offset, width); anchors: global (&lbl/*lbl...), header-typed arg (T:<tag>), else arg:<reg origin> (weak); sets >= 3; Jaccard >= 0.5 components"),
        data_family_anchored=dict(real=da_real, red_pooled_elements=da_red, verdict=verdict["data_family_anchored"],
                                  key="as data_family, global / header-typed anchors only"),
        idiom_family=dict(real=i_real, red_pooled_hits=i_red, verdict=verdict["idiom_family"], key="exact idiom_hits multiset; no idiom -> no group"),
        motifs=dict(real=m_real, red_shuffled_within_block=m_red, verdict=verdict["motifs"],
                    key="sha of a 6-insn window inside one basic block, registers renumbered by first use, numbers->N, symbols->S; motif iff in >= 3 Tennis functions"),
        proof_family="UNKNOWN for all 1,797: no verdicts exist yet",
        w7_singletons=len(w7_single),
        w7_singletons_in_nonsingleton_group={k: len(v) for k, v in rec_by.items()} | {
            "union_all_resolutions": len(union_all), "union_red_control_proven_resolutions": len(union_proven)},
        residual_structural_deciles=deciles, residual_structural_mean=round(sum(rs) / N, 4),
        residual_structural_eq_1=sum(1 for v in rs if v == 1.0), residual_structural_eq_0=sum(1 for v in rs if v == 0.0),
        roles=dict(roles), role_note="UNKNOWN is not a role: it is the absence of a proven label",
        known_struct_coverage_fns=sum(1 for f in names if known[f]))
    json.dump(dict(summary=summary, functions=per_fn), open(os.path.join(d, "factor.json"), "w"), indent=1, sort_keys=True)

    # ---- blockers
    bl_fn, untyped = {}, {}
    for fn in names:
        keys, ut = blockers_of(fn, recs["ctx_run1"][fn], ctext[fn], tags)
        if keys:
            bl_fn[fn] = keys
        if ut:
            untyped[fn] = ut
    idx = collections.defaultdict(list)
    for fn, ks in bl_fn.items():
        for k in ks:
            idx[k].append(fn)
    not_clean = [f for f in names if not recs["ctx_run1"][f]["clean"]]
    unexplained = [f for f in not_clean if f not in bl_fn]
    ranked = sorted(idx.items(), key=lambda kv: (-len(kv[1]), -sum(1 for f in kv[1] if bl_fn[f] == {kv[0]}), kv[0]))
    blk = [dict(rank=j + 1, key=k, kind=k.split(":")[0], n_functions=len(v),
                sole_blocker_functions=sorted(f for f in v if bl_fn[f] == {k}), functions=sorted(v)) for j, (k, v) in enumerate(ranked)]
    json.dump(dict(n_not_clean=len(not_clean), n_with_blocker=len(bl_fn), unexplained_not_clean=unexplained,
                   kinds=dict(collections.Counter(k.split(":")[0] for k in idx)),
                   note="FIELD_UNTYPED / SELF_SIG / QTYPE_LOCAL are per-function keys (no cross-function identity is provable from "
                        "the m2c text: base is void*); sole_blocker = the function's only key, a structural prediction, UNVERIFIED",
                   untyped_offsets=untyped, blockers=blk), open(os.path.join(d, "blockers.json"), "w"), indent=1)

    # ---- hypotheses for the top 10 blockers
    hyp = []
    for b in blk[:10]:
        k, deps = b["key"], b["functions"]
        h = dict(rank=b["rank"], key=k, n_functions=b["n_functions"])
        smallest = min(deps, key=lambda f: (sizes[f], f))
        if k.startswith("HELPER:"):
            name = k.split(":", 1)[1]
            obs = collections.Counter()
            for f in names:
                for s in F[f]["helper_sig"].get(name, []):
                    obs[tuple(s)] += 1
            ar = collections.Counter()
            rt = collections.Counter()
            for (g, fp, r3, f1), c in obs.items():
                ar["gpr_args_set=%d fpr_args_set=%d" % (g, fp)] += c
                rt["r3_read_after_call" if r3 else ("f1_read_after_call" if f1 else "no_return_use_seen")] += c
            body = P.fns.get(name)
            ev = None
            if body:
                rf, rw = entry_evidence(body)
                ev = dict(callee_size=len(body), callee_args_read_before_write=rf, callee_writes_before_blr=rw)
            h.update(hypotheses=dict(arity_at_call_sites=dict(ar), return_use_at_call_sites=dict(rt)), callee_body_evidence=ev,
                     discriminator=dict(fn=name if body else smallest, size=len(body) if body else sizes[smallest],
                                        why="the callee's own body fixes its parameter reads and return register" if body else
                                            "smallest dependent (callee body not in the program asm)"))
        elif k.startswith("FIELD:"):
            base, off = k.split(":", 1)[1].rsplit("+", 1)
            off = int(off, 16)
            ev = collections.Counter()
            have = []
            for f in deps:
                regs = proto.get(f, {})
                for o, ofs, wd, rw, op, use in F[f]["field_accesses"]:
                    a, _ = anchor(o, regs)
                    if ofs == off and (base in a):
                        ev["%s width=%d use=%s" % (op, wd, use)] += 1
                        have.append(f)
            h.update(hypotheses=dict(asm_access_evidence=dict(ev), candidates=[
                "unsigned 8" if any(x.startswith("lbz") for x in ev) else None, "signed 16" if any(x.startswith("lha") for x in ev) else None,
                "unsigned 16" if any(x.startswith("lhz") for x in ev) else None, "f32" if any(x.startswith("lfs") for x in ev) else None,
                "pointer (deref seen)" if any("use=ptr" in x for x in ev) else None,
                "32-bit scalar" if any(x.startswith("lwz") and "use=ptr" not in x for x in ev) else None]),
                discriminator=dict(fn=min(have, key=lambda f: (sizes[f], f)) if have else smallest,
                                   size=sizes[min(have, key=lambda f: (sizes[f], f))] if have else sizes[smallest],
                                   why="smallest dependent with an asm access at the offset" if have else "smallest dependent (no asm access matched the anchor)"))
            h["hypotheses"]["candidates"] = [c for c in h["hypotheses"]["candidates"] if c]
        else:
            h.update(hypotheses=dict(note="tool-side or per-function blocker: no type hypothesis is admitted by the asm"),
                     discriminator=dict(fn=smallest, size=sizes[smallest], why="smallest dependent"))
        hyp.append(h)
    json.dump(dict(note="data only; no hypothesis is resolved", hypotheses=hyp), open(os.path.join(d, "hypotheses.json"), "w"), indent=1)
    print(json.dumps(dict(knowledge_shock={k: shock[k] for k in ("clean_before", "clean_after", "newly_clean")} | {
        "outside_draws": len(shock["newly_clean_outside_24_draws"]), "newly_dirty": len(shock["newly_dirty"]), "reproduce": shock["reproduce"]},
        verdict=verdict, summary={k: summary[k] for k in ("w7_singletons", "w7_singletons_in_nonsingleton_group", "residual_structural_deciles",
                                                          "roles", "known_struct_coverage_fns")},
        motifs=dict(real=m_real, red=m_red), structural=dict(real=s_real, redA=s_redA, redB=s_redB), data=dict(real=d_real, red=d_red),
        data_anch=dict(real=da_real, red=da_red), idiom=dict(real=i_real, red=i_red),
        blockers_top20=[(b["rank"], b["key"], b["n_functions"], len(b["sole_blocker_functions"])) for b in blk[:20]],
        unexplained=len(unexplained)), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
