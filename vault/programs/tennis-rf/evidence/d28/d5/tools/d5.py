#!/usr/bin/env python3
"""D5 causal unlock sweep (WU-D5v2).  Run on GEX44:
  export KSR_DECOMP_TOOLS=/opt/ksr-decomp; /opt/ksr-decomp/venv/bin/python d5.py <step> <out_dir>
steps: draw | cror | cands | all
Chain per candidate: unknown -> intervention (header/asm delta on a COPY) -> incremental re-eval (m2c+lint on the dependents only,
20 cores) -> measured unlock -> verdict SUPPORT / CONTRADICTION / ABSTAIN.  D4 rank grants no authority.  No model calls.
"""
import collections, hashlib, json, multiprocessing as mp, os, random, re, sys

M = "/home/kobii/missions/tennis-w11"
D28 = M + "/out/d28"
sys.path.insert(0, D28 + "/d1d/tools")
import m2c_run as R          # noqa: E402  (unchanged P1P2 runner: one(), init())
import factor as Fa          # noqa: E402
import asmlib as A           # noqa: E402

P = R.P
SEED = 20261013
JOBS = 20
CTX0 = D28 + "/d1d/ctx/tennis_context.h"
CROR_KEY = "M2C:unknown instruction cror"

_C = {}


def load():
    if _C:
        return _C
    _C["text"], _C["tables"] = P.blocks(R.ASM)
    _C["facts"] = {}
    for l in open(D28 + "/d1d/facts.jsonl"):
        r = json.loads(l)
        _C["facts"][r["fn"]] = r
    _C["base"] = {}
    for l in open(D28 + "/d1d/m2c/ctx_run1/records.jsonl"):
        r = json.loads(l)
        _C["base"][r["fn"]] = r
    _C["basec"] = {fn: open(D28 + "/d1d/m2c/ctx_run1/c/%s.c" % fn, encoding="utf-8").read()
                   if os.path.exists(D28 + "/d1d/m2c/ctx_run1/c/%s.c" % fn) else "" for fn in _C["base"]}
    _C["bl"] = json.load(open(D28 + "/d1d/blockers.json"))
    _C["keyfns"] = {b["key"]: b["functions"] for b in _C["bl"]["blockers"]}
    _C["frontier"] = json.load(open(D28 + "/d4/frontier.json"))
    _C["dom"] = json.load(open(D28 + "/d4/dominators.json"))
    _C["hctx"] = open(CTX0, encoding="utf-8").read()
    _C["tags"], _C["proto"] = Fa.header_info(_C["hctx"])
    return _C


# ------------------------------------------------------------------ cror rewrite (tool-side, asm preprocessing)
CROR = re.compile(r'^(\s*/\*.*?\*/\s*)cror\s+eq,\s*(cr\d)?(gt|lt),\s*(cr\d)?eq\s*$')
INS = re.compile(r'^(\s*/\*.*?\*/\s*)(\w+)\s*(.*?)\s*$')
CMPS = ("cmp", "fcmp", "cmpl", "cmpw", "cmplw", "cmpwi", "cmplwi", "fcmpo", "fcmpu", "cmpli", "cmpi")
# cr0.eq' = bit | eq.   bne -> taken iff NOT(bit|eq)  == the strict opposite compare:  gt -> lt ; lt -> gt
#                       beq -> taken iff (bit|eq)      == ge / le
REWRITE = {("gt", "bne"): "blt", ("gt", "beq"): "bge", ("lt", "bne"): "bgt", ("lt", "beq"): "ble"}
CR0_READERS = re.compile(r'^(beq|bne|blt|bgt|ble|bge|bso|bns|bdnzt|bdnzf|mfcr|crand|cror|crxor|crnor|crandc|crorc|creqv|crnand|isel)\b')


def cror_rewrite(block):
    """Return (new_block, stats). Rewrites `cror eq, [crN]{gt|lt}, [crN]eq ; bne|beq T` -> `b{lt|gt|ge|le} [crN,] T` (+ nop).
    Bails (leaves the cror, so the function stays blocked) when the next line is not that branch, or when cr0.eq is read
    again on the fall-through path before the next compare (the OR-ed bit would then matter)."""
    lines = block.split("\n")
    n_cror = n_done = 0
    why = collections.Counter()
    i = 0
    while i < len(lines):
        m = CROR.match(lines[i])
        if not m:
            i += 1
            continue
        n_cror += 1
        pre, crn, bit, crn2 = m.group(1), m.group(2), m.group(3), m.group(4)
        if (crn or "") != (crn2 or ""):
            why["MIXED_CR_FIELDS"] += 1
            i += 1
            continue
        mb = INS.match(lines[i + 1]) if i + 1 < len(lines) else None
        if not mb or mb.group(2) not in ("bne", "beq"):
            why["NEXT_NOT_BNE_BEQ"] += 1
            i += 1
            continue
        ops = mb.group(3).split(",")
        if len(ops) != 1:
            why["BRANCH_HAS_CR_OPERAND"] += 1
            i += 1
            continue
        live = False
        for j in range(i + 2, min(len(lines), i + 12)):
            s = lines[j].strip()
            if not s or s.startswith((".", "#")) or (s.endswith(":") and not s.startswith("/*")):
                break
            mj = INS.match(lines[j])
            if not mj:
                continue
            mn = mj.group(2)
            if mn.startswith(CMPS) or mn in ("blr", "b", "bctr"):
                break
            if CR0_READERS.match(mn) and "cr" not in mj.group(3):
                live = True
                break
        if live:
            why["EQ_LIVE_ON_FALLTHROUGH"] += 1
            i += 1
            continue
        newmn = REWRITE[(bit, mb.group(2))]
        target = ops[0].strip()
        lines[i] = pre + "nop"
        lines[i + 1] = mb.group(1) + newmn + " " + ((crn + ", ") if crn else "") + target
        n_done += 1
        i += 2
    return "\n".join(lines), dict(n_cror=n_cror, n_rewritten=n_done, bailed=dict(why))


# ------------------------------------------------------------------ incremental re-evaluation
def make_ctx(path, extra_lines):
    open(path, "w", encoding="utf-8", newline="\n").write(load()["hctx"].rstrip("\n") + "\n" + "".join(l + "\n" for l in extra_lines))
    return path


def run_set(fns, ctx_path, transform=None, jobs=JOBS):
    """m2c + lint on `fns` only, context = ctx_path. Returns ({fn: (rec, c_text)}, {fn: transform stats})."""
    C = load()
    flags = P.build_flags(False, ctx_path)
    jl, stats = [], {}
    for fn in sorted(fns):
        block = C["text"][fn]
        if transform:
            block, stats[fn] = transform(block)
        extra = []
        for t in sorted(set(P.TABLE_REF.findall(block))):
            if t in C["tables"]:
                block, tab = P.adapt_table(block, C["tables"][t], fn, int(C["facts"][fn]["addr"], 16))
                extra.append(tab)
        jl.append((fn, C["facts"][fn]["addr"], block, extra))
    out = {}
    if not jl:
        return out, stats
    R.init(flags, ctx_path, "ctx")
    rec, c = R.one(jl[0])           # warm the context cache before forking (as m2c_run does)
    out[rec["fn"]] = (rec, c)
    with mp.get_context("fork").Pool(jobs, initializer=R.init, initargs=(flags, ctx_path, "ctx")) as pool:
        for rec, c in pool.imap_unordered(R.one, jl[1:], chunksize=1):
            out[rec["fn"]] = (rec, c)
    return out, stats


def keys_after(fn, rec, c):
    C = load()
    return sorted(Fa.blockers_of(fn, rec, c, C["tags"])[0])


def measure(deps, new, key=None):
    """newly lint-clean fns, new errors, dependents that lost `key`."""
    C = load()
    unlocked, errs, resolved = [], [], []
    for fn in sorted(deps):
        b, (n, c) = C["base"][fn], new[fn]
        if not b["clean"] and n["clean"]:
            unlocked.append(fn)
        if b["clean"] and not n["clean"]:
            errs.append([fn, "REGRESSION clean->not clean"])
        elif n["status"] != "L1" and n["error"] != b["error"]:
            errs.append([fn, "NEW_FAILURE %s %s" % (n["status"], n["error"][:80])])
        elif b["status"] == "L1" and n["status"] == "L1" and not n["clean"]:
            nc = set(n["lint_codes"]) - set(b["lint_codes"])
            if nc:
                errs.append([fn, "NEW_LINT_CODES %s" % sorted(nc)])
        if key and key in C["keyfns"] and fn in C["keyfns"][key]:
            if key not in keys_after(fn, n, c):
                resolved.append(fn)
    return unlocked, errs, resolved


# ------------------------------------------------------------------ step: cror
def step_cror(out):
    C = load()
    deps = sorted(C["keyfns"][CROR_KEY])
    sole = sorted(next(b for b in C["bl"]["blockers"] if b["key"] == CROR_KEY)["sole_blocker_functions"])
    d = out + "/cror_ctx"
    os.makedirs(d, exist_ok=True)
    ctx = make_ctx(d + "/ctx_cror_wave1.h", [])
    new, st = run_set(deps, ctx, cror_rewrite)
    unl, errs, _ = measure(deps, new)
    still_cror = [f for f in deps if CROR_KEY in keys_after(f, *new[f])]
    sole_unl = [f for f in sole if f in unl]
    # wave 2: fns whose ONLY blocker is HELPER:F with F newly clean -> F's now-clean signature becomes F's prototype
    newly = set(unl)
    after = {f: set(C["bl"].get("_k", {}).get(f, [])) for f in []}
    keysof = collections.defaultdict(set)
    for b in C["bl"]["blockers"]:
        for f in b["functions"]:
            keysof[f].add(b["key"])
    w2 = {}
    protos = []
    for F in sorted(newly):
        sig = next((l for l in new[F][1].split("\n") if re.match(r'^[A-Za-z_][\w\s\*]*\b%s\(' % re.escape(F), l) and l.rstrip().endswith("{")), None)
        if sig and "?" not in sig:
            protos.append((F, sig.rstrip().rstrip("{").rstrip() + ";"))
    pf = {F for F, _ in protos}
    w2deps = sorted(f for f, ks in keysof.items() if ks and all(k.startswith("HELPER:") and k.split(":", 1)[1] in pf for k in ks))
    if w2deps:
        ctx2 = make_ctx(d + "/ctx_cror_wave2.h", [p for _, p in protos])
        new2, _ = run_set(w2deps, ctx2)
        unl2, errs2, _ = measure(w2deps, new2)
        w2 = dict(prototypes_from_now_clean_callees=dict(protos), dependents=w2deps, newly_clean=unl2, new_errors=errs2)
    else:
        w2 = dict(prototypes_from_now_clean_callees=dict(protos), dependents=[], newly_clean=[], new_errors=[],
                  note="no function has a HELPER blocker set contained in the newly clean callees")
    res = dict(
        intervention="asm-preprocessing rewrite of `cror eq,[crN]{gt|lt},[crN]eq ; bne|beq T` into the equivalent strict/inclusive "
                     "branch on the same bit: gt+bne->blt, gt+beq->bge, lt+bne->bgt, lt+beq->ble (crN operand kept). The cror becomes a nop. "
                     "Exact for every total-order compare (integer cmp, and fcmp on ordered operands). Residual difference: float UNORDERED "
                     "(NaN) sets only the UN bit, so the original takes the `bne` and the rewrite does not; C has no UN, m2c already ignores it. "
                     "Not applied when cr0.eq is read again on the fall-through path or the branch is not the very next instruction.",
        dependents_total=len(deps), dependents_sole=len(sole),
        rewrite_stats=dict(n_cror=sum(s["n_cror"] for s in st.values()), n_rewritten=sum(s["n_rewritten"] for s in st.values()),
                           bailed=dict(sum((collections.Counter(s["bailed"]) for s in st.values()), collections.Counter()))),
        wave1=dict(newly_clean=unl, n_newly_clean=len(unl), sole_dependents_unlocked=sole_unl, n_sole_unlocked=len(sole_unl),
                   new_errors=errs, still_blocked_by_cror=still_cror,
                   not_unlocked={f: keys_after(f, *new[f]) for f in deps if f not in unl}),
        wave2=w2,
        baseline_clean_before=sum(1 for r in C["base"].values() if r["clean"]),
        total_unlock=len(unl) + len(w2["newly_clean"]))
    json.dump(res, open(out + "/cror_unlock.json", "w"), indent=1, sort_keys=True)
    json.dump({f: dict(sha=new[f][0]["c_sha256"], clean=new[f][0]["clean"]) for f in deps}, open(out + "/cror_wave1_sha.json", "w"), indent=1, sort_keys=True)
    print("CROR dependents=%d rewritten=%d wave1_unlock=%d (sole %d/%d) new_errors=%d wave2_unlock=%d" % (
        len(deps), res["rewrite_stats"]["n_rewritten"], len(unl), len(sole_unl), len(sole), len(errs), len(w2["newly_clean"])))
    return res


# ------------------------------------------------------------------ step: draw
def helper_vars():
    C = load()
    return {v["var"]: v for v in C["frontier"]["vars"] if v["kind"] == "HELPER"}


def rank_all():
    C = load()
    vs = sorted(C["frontier"]["vars"], key=lambda v: (-(v["score"][0] + v["score"][1]) / 2, v["var"]))
    return {v["var"]: i + 1 for i, v in enumerate(vs)}


def quartiles(items):
    n = len(items)
    cuts = [round(n * k / 4) for k in range(5)]
    return [items[cuts[k]:cuts[k + 1]] for k in range(4)]


def step_draw(out):
    C = load()
    hv = helper_vars()
    top = {r["var"]: r["rank"] for r in C["dom"]["top30"]}
    gr = rank_all()
    order_ok = {v for v, _ in sorted(gr.items(), key=lambda t: t[1])[:30]} == set(top)
    rng = random.Random(SEED)

    def deg(v):
        return hv[v]["blocked_direct"][1]
    top_h = sorted((v for v in hv if v in top), key=lambda v: (-deg(v), v))
    low_h = sorted((v for v in hv if v not in top), key=lambda v: (-deg(v), v))
    picks = []

    def draw(pop, k_extra, stratum):
        qs = quartiles(pop)
        for qi, q in enumerate(qs):
            picks.append(dict(var=rng.choice(q), stratum="%s:Q%d" % (stratum, qi + 1)))
        for qi in rng.sample(range(4), k_extra):
            rest = [v for v in qs[qi] if v not in {p["var"] for p in picks}]
            picks.append(dict(var=rng.choice(rest), stratum="%s:Q%d(extra)" % (stratum, qi + 1)))
    draw(top_h, 2, "top30")
    draw(low_h, 1, "below30")
    for p in picks:
        v = hv[p["var"]]
        p.update(d4_rank=top.get(p["var"], gr[p["var"]]), d4_rank_source="dominators.json" if p["var"] in top else "recomputed (score midpoint, var tiebreak)",
                 d4_degree_blocked_direct=v["blocked_direct"], d4_score=v["score"], n_fns=v["n_fns"])
    res = dict(seed=SEED, population="HELPER vars of frontier.json (the only kind whose intervention the asm lets a script state); cror handled as its own experiment",
               n_top30_helpers=len(top_h), n_below_helpers=len(low_h), stratification="degree = blocked_direct[1]; contiguous quartiles of the degree-sorted population; 1 per quartile + extras from seeded random quartiles (2 top30, 1 below30)",
               top30_set_equals_recomputed_global_top30=order_ok, picks=picks)
    json.dump(res, open(out + "/draw.json", "w"), indent=1, sort_keys=True)
    print("DRAW", [(p["var"], p["d4_rank"], p["d4_degree_blocked_direct"][1]) for p in picks], "top30_consistent", order_ok)
    return res


# ------------------------------------------------------------------ step: candidates
_A = {}


def prog():
    if "p" not in _A:
        _A["p"] = A.parse_program(Fa.ASM)
    return _A["p"]


def callee_evidence(F):
    ins = prog().fns[F]
    read_first, ret = Fa.entry_evidence(ins)
    g = [int(r[1:]) for r in read_first if r[0] == "r"]
    f = [int(r[1:]) for r in read_first if r[0] == "f"]
    return dict(min_gpr=(max(g) - 2) if g else 0, min_fpr=len(f), ret_regs=ret)


def callsites(F):
    C = load()
    s = []
    for fn, fr in C["facts"].items():
        s += [tuple(x) for x in fr["helper_sig"].get(F, [])]
    return s


def helper_hyps(F):
    ev = callee_evidence(F)
    cs = callsites(F)
    cnt = collections.Counter(s[0] for s in cs)
    ars = sorted({a for a in cnt if a >= ev["min_gpr"]}, key=lambda a: (-cnt[a], a))[:3]
    if ev["min_gpr"] not in ars:
        ars.append(ev["min_gpr"])
    read = any(s[2] for s in cs)
    rets = ["f32"] if "f1" in ev["ret_regs"] else (["s32", "void *"] if read else ["void"])
    hyps = []
    for a in ars:
        for r in rets:
            ps = ["s32"] * a + ["f32"] * ev["min_fpr"]
            hyps.append(dict(arity_gpr=a, nfpr=ev["min_fpr"], ret=r, proto="%s %s(%s);" % (r, F, ", ".join(ps) if ps else "void")))
    return hyps, dict(callee=ev, n_callsites=len(cs), gpr_arity_counts=dict(cnt), r3_read_after_call=read)


def asm_admits(F, hyp):
    """Deterministic consistency check of a delta against the asm; False = contradicts a load/use fact."""
    ev = callee_evidence(F)
    cs = callsites(F)
    if hyp["arity_gpr"] < ev["min_gpr"]:
        return False, "fewer GPR params (%d) than the callee reads at entry (%d)" % (hyp["arity_gpr"], ev["min_gpr"])
    if hyp["nfpr"] < ev["min_fpr"]:
        return False, "fewer FPR params than the callee reads at entry"
    if hyp["ret"] == "void" and any(s[2] for s in cs):
        return False, "void return but callers read r3 after the call"
    return True, ""


def eval_delta(F, proto_line, tag, out):
    C = load()
    key = "HELPER:" + F
    deps = sorted(C["keyfns"][key])
    ctx = make_ctx("%s/cands_ctx/%s.h" % (out, tag), [proto_line])
    new, _ = run_set(deps, ctx)
    unl, errs, res = measure(deps, new, key)
    return dict(dependents=len(deps), newly_clean=unl, n_unlock=len(unl), new_errors=errs, resolved_key_in=res,
                sha=hashlib.sha256("".join(new[f][0]["c_sha256"] for f in deps).encode()).hexdigest())


def step_cands(out):
    C = load()
    os.makedirs(out + "/cands_ctx", exist_ok=True)
    draw = json.load(open(out + "/draw.json"))
    rows = []
    for p in draw["picks"]:
        var = p["var"]
        F = var.split(":", 1)[1]
        if re.search(r'\b%s\b' % re.escape(F), C["hctx"]):
            rows.append(dict(p, verdict="ABSTAIN", why="MODEL_NEEDED: F already declared in the context header; the blocker is not a missing prototype"))
            continue
        if F not in prog().fns:
            rows.append(dict(p, verdict="ABSTAIN", why="MODEL_NEEDED: callee body not in the asm corpus; no entry evidence"))
            continue
        hyps, ev = helper_hyps(F)
        hr = []
        for hi, h in enumerate(hyps):
            ok, why = asm_admits(F, h)
            if not ok:
                hr.append(dict(h, admitted=False, rejected_because=why))
                continue
            r = eval_delta(F, h["proto"], "%s_h%d" % (F, hi), out)
            hr.append(dict(h, admitted=True, measured=r,
                           verdict="SUPPORT" if r["n_unlock"] > 0 and not r["new_errors"] else "CONTRADICTION"))
        adm = [h for h in hr if h["admitted"]]
        sup = [h for h in adm if h["verdict"] == "SUPPORT"]
        if not adm:
            v, why = "ABSTAIN", "MODEL_NEEDED: no hypothesis survives the asm consistency check"
        elif sup:
            v, why = "SUPPORT", ("CONFLICT: %d surviving hypotheses with different prototypes, all kept" % len(sup)) if len(sup) > 1 else ""
        else:
            v, why = "CONTRADICTION", "best admitted hypothesis unlocks %d (no new error counted as unlock)" % max(h["measured"]["n_unlock"] for h in adm)
        un = [h["measured"]["n_unlock"] for h in adm]
        rows.append(dict(p, evidence=ev, hypotheses=hr, verdict=v, note=why, conflict=len(sup) > 1,
                         measured_unlock_max=max(un) if un else None, measured_unlock_min_surviving=min(h["measured"]["n_unlock"] for h in sup) if sup else None,
                         resolved_key_max=max(h["measured"]["resolved_key_in"].__len__() for h in adm) if adm else None))
        print("CAND", var, p["d4_rank"], p["d4_degree_blocked_direct"][1], v, rows[-1]["measured_unlock_max"])
    json.dump(rows, open(out + "/cands_raw.json", "w"), indent=1, sort_keys=True)
    return rows


def spearman(x, y):
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    rx, ry = rk(x), rk(y)
    n = len(x)
    mx, my = sum(rx) / n, sum(ry) / n
    sx = sum((a - mx) ** 2 for a in rx) ** .5
    sy = sum((b - my) ** 2 for b in ry) ** .5
    return None if sx == 0 or sy == 0 else sum((a - mx) * (b - my) for a, b in zip(rx, ry)) / (sx * sy)


def step_all(out):
    os.makedirs(out, exist_ok=True)
    cr = step_cror(out)
    step_draw(out)
    rows = step_cands(out)
    C = load()
    cror_row = dict(var=CROR_KEY, stratum="cror (own experiment)", d4_rank=17, d4_degree_blocked_direct=[len(next(b for b in C["bl"]["blockers"] if b["key"] == CROR_KEY)["sole_blocker_functions"]), len(C["keyfns"][CROR_KEY])],
                    verdict="SUPPORT" if cr["total_unlock"] > 0 and not cr["wave1"]["new_errors"] else "CONTRADICTION", measured_unlock_max=cr["total_unlock"])
    allr = [cror_row] + rows
    pts = [(r["d4_degree_blocked_direct"][1], r["measured_unlock_max"]) for r in allr if r.get("measured_unlock_max") is not None]
    pts_nocror = pts[1:]
    sp = lambda p: dict(n=len(p), rho=spearman([a for a, _ in p], [b for _, b in p]), n_zero_unlock=sum(1 for _, b in p if b == 0),
                        degrees=[a for a, _ in p], unlocks=[b for _, b in p])
    cu = dict(note="verdicts are per candidate; HELPER candidates are measured as a SINGLE prototype delta, so a function with other blockers cannot unlock (low bound 0 in D4)",
              cror=cr, candidates=allr,
              spearman_degree_vs_unlock=dict(with_cror=sp(pts), without_cror=sp(pts_nocror),
                                              reading="rho None = a constant series (all unlocks equal); with n this small and heavy ties no claim about degree's causal value is supported either way"))
    json.dump(cu, open(out + "/causal_unlock.json", "w"), indent=1, sort_keys=True)
    print("ALL_DONE", {r["var"]: r["verdict"] for r in allr}, cu["spearman_degree_vs_unlock"]["with_cror"]["rho"], cu["spearman_degree_vs_unlock"]["without_cror"]["rho"])


if __name__ == "__main__":
    step, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    {"cror": step_cror, "draw": step_draw, "cands": step_cands, "all": step_all}[step](out)
