#!/usr/bin/env python3
"""D12c joint helper-prototype + layout bundle, held-out. GEX44, no model.
  KSR_DECOMP_TOOLS=/opt/ksr-decomp /opt/ksr-decomp/venv/bin/python d12c.py <out_dir>
Selector (select_bundles) reads var sets only. Prototypes are derived with pack-half callsites only."""
import collections, hashlib, json, os, random, re, sys
OUT = sys.argv[1]
M = "/home/kobii/missions/tennis-w11"; D28 = M + "/out/d28"
sys.argv = [sys.argv[0], D28 + "/d12"]          # joint_delta reads argv[1] at import
for p in (D28 + "/d5/tools", D28 + "/d7", D28 + "/d1d/tools", D28 + "/tools", D28 + "/d12"):
    sys.path.insert(0, p)
import d5, dirty, joint_delta as jd  # noqa
SEED = 20261015
L_FILE = D28 + "/d12b/hdr_e74_v1.h"
L_LINES = open(L_FILE).read().rstrip("\n").split("\n")
B1 = ["HELPER:fn_801C7770", "HELPER:fn_801C9670", "HELPER:fn_801C83F4"]
res = {}
C = dirty.load(); d5.load()
tgt, sc = jd.load_inputs()
asm = d5.load()["text"]
jd.D12 = OUT                                    # scratch ctx files go to OUT


def log(*a):
    print(*a, flush=True)


def clo(lines):
    c, _ = dirty.closure(C, C["hctx"], C["hctx"].rstrip("\n") + "\n" + "".join(l + "\n" for l in lines), asm)
    return set(c)


def run(lines, fns, tag):
    ctx = d5.make_ctx("%s/ctx_%s.h" % (OUT, tag), lines)
    new, _ = d5.run_set(sorted(fns), ctx)
    return new


# ---- components (script-stateable) and bundle selector inputs
ru = {r["fn"] for r in tgt if any(v["type"] in jd.M2C for v in r["unresolved_vars"])}
specs, fvars = {}, {}
for r in tgt:
    if r["fn"] in ru or r["fn"] not in C["base"]:
        continue
    ids, ok = set(), True
    for v in r["unresolved_vars"]:
        cid, spec = jd.component_for(v, r["fn"], sc, C["hctx"], C)
        if cid == "SKIP":
            continue
        if cid is None:
            ok = False; break
        ids.add(cid); specs[cid] = spec
    if ok and ids and not C["base"][r["fn"]]["clean"]:
        fvars[r["fn"]] = frozenset(ids)
jd.TOP = 40
ranked, ncand = jd.select_bundles(fvars)
rec = json.load(open(D28 + "/d12/joint_delta.json"))["bundles"]
res["selector_reproduces_d12a_top10"] = [b for b, _ in ranked[:10]] == [b["bundle"] for b in rec]
log("selector reproduces D12a top10:", res["selector_reproduces_d12a_top10"], "ncand", ncand)

# ---- step 1 reproduce
b1_comps = [(c, specs[c]) for c in B1]
b1_lines, why = jd.build_lines(b1_comps, sc, C)
b1_targets = next(t for b, t in ranked if b == sorted(B1))
clo_b1 = clo(b1_lines)
fns1 = sorted(clo_b1 | set(b1_targets))
nB = run(b1_lines, fns1, "b1")
unB, errB, _ = d5.measure(fns1, nB)
res["step1_B1"] = dict(targets=b1_targets, n_targets=len(b1_targets), closure=len(clo_b1), unlock=len(unB), newly_clean=unB, errors=errB)
log("B1 unlock", len(unB), "expect 12")
dep91 = sorted({m["fn"] for c in json.load(open(D28 + "/d12/struct_clusters.json"))["clusters"] for m in c["members"]
                if c["cluster"] == "C0004"})
res["n_c0004_dependents"] = len(dep91)
clo_L = clo(L_LINES)
fnsL = sorted(clo_L | set(dep91))
nL = run(L_LINES, fnsL, "L")
unL, errL, _ = d5.measure(fnsL, nL)
res["step1_L"] = dict(closure=len(clo_L), fns_run=len(fnsL), unlock=len(unL), newly_clean=unL, errors=errL)
log("L unlock", len(unL), "expect 0")
res["step1_reproduced"] = (len(unB) == 12 and len(unL) == 0 and len(dep91) == 91)
json.dump(res, open(OUT + "/step1.json", "w"), indent=1)
if not res["step1_reproduced"]:
    log("STEP1 MISMATCH: stop"); sys.exit(3)

# ---- step 2 split (written before any composition)
P = sorted((clo_b1 | set(dep91)) - set(b1_targets))
rng = random.Random("%s:P" % SEED); sh = P[:]; rng.shuffle(sh)
pack, held = sorted(sh[:len(sh) // 2]), sorted(sh[len(sh) // 2:])
assert not set(pack) & set(held)
json.dump(dict(seed=SEED, rule="Random('%d:P').shuffle(sorted P); first half pack" % SEED, population=P, pack=pack, held_out=held,
               b1_targets=b1_targets), open(OUT + "/split.json", "w"), indent=1)
log("split", len(P), len(pack), len(held))
PS, HS, TS = set(pack), set(held), set(b1_targets)

# ---- pack-only prototype derivation for every helper used
orig_cs = d5.callsites


def cs_pack(F):
    Cc = d5.load(); s = []
    for fn, fr in Cc["facts"].items():
        if fn in HS:
            continue
        s += [tuple(x) for x in fr["helper_sig"].get(F, [])]
    return s


def proto_for(F, packonly):
    d5.callsites = cs_pack if packonly else orig_cs
    try:
        hyps, _ = d5.helper_hyps(F)
        ok = [h for h in hyps if d5.asm_admits(F, h)[0]]
        return ok[0]["proto"] if ok else None
    finally:
        d5.callsites = orig_cs


# ---- step 3 joint arm
seq, applied = [], set()
order = [(b, t) for b, t in ranked]
b1set = set(B1)
steps_def = [("B1", sorted(B1), b1_targets)]
applied |= b1set
for b, t in order:
    if len(steps_def) >= 10:
        break
    if set(b) <= applied:
        continue
    steps_def.append(("rank%d" % (order.index((b, t)) + 1), b, t)); applied |= set(b)
res["steps_available"] = len(steps_def)
rows, cum, prev_zero = [], set(), 0
pack_proto_diff = []
Lc_cache = {}
for si, (name, comps_ids, tg) in enumerate(steps_def):
    cum |= set(comps_ids)
    ids = sorted(cum)
    for c in ids:
        if specs[c]["kind"] == "helper":
            F = c.split(":", 1)[1]
            pp, fp = proto_for(F, True), proto_for(F, False)
            if pp != fp:
                pack_proto_diff.append([F, pp, fp])
    cl_, why = jd.build_lines([(c, specs[c]) for c in ids], sc, C)
    if cl_ is None:
        rows.append(dict(step=si, name=name, error=why)); continue
    targets_all = sorted({t for s in steps_def[:si + 1] for t in s[2]})
    U = sorted(clo(cl_) | clo(cl_ + L_LINES) | clo_L | PS | HS | set(targets_all))
    nBk = run(cl_, U, "s%d_B" % si)
    nBL = run(cl_ + L_LINES, U, "s%d_BL" % si)
    nLk = nL if all(f in nL for f in U) else run(L_LINES, U, "s%d_L" % si)
    uB, eB, _ = d5.measure(U, nBk); uBL, eBL, _ = d5.measure(U, nBL); uL, eL, _ = d5.measure(U, nLk)
    base = C["base"]
    newcodes = collections.Counter()
    for f in U:
        n = nBL[f][0]
        if base[f]["status"] == "L1" and n["status"] == "L1":
            for cd in set(n["lint_codes"]) - set(base[f]["lint_codes"]):
                newcodes[cd] += 1
    hidden = {t: d5.keys_after(t, nBL[t][0], nBL[t][1]) for t in targets_all if not nBL[t][0]["clean"]}
    hidden_new = {t: k for t, k in hidden.items() if k}
    # vars resolved cumulative: unresolved vars named in cum components for fns in U
    vres = len(cum)
    row = dict(step=si, name=name, components=ids, cum_vars_resolved=vres, universe=len(U),
               unlock_B=len(uB), unlock_L=len(uL), unlock_BL=len(uBL),
               complementarity=len(uBL) - len(uB) - len(uL),
               new_BL_pack=sorted(set(uBL) & PS), new_BL_held=sorted(set(uBL) & HS), new_BL_b1_targets=sorted(set(uBL) & TS),
               new_BL_other=sorted(set(uBL) - PS - HS - TS),
               new_B_pack=sorted(set(uB) & PS), new_B_held=sorted(set(uB) & HS),
               new_L_held=sorted(set(uL) & HS),
               hidden_blockers_revealed=hidden_new, new_lint_codes=dict(newcodes),
               regressions=eBL, regressions_B=eB)
    rows.append(row)
    log("STEP", si, name, "B", len(uB), "L", len(uL), "BL", len(uBL), "pack", len(row["new_BL_pack"]), "held", len(row["new_BL_held"]),
        "hidden", len(hidden_new), dict(newcodes))
    json.dump(rows, open(OUT + "/joint_arm.json", "w"), indent=1)
    # stop-loss: B1+L and next 2 bundles
    if si >= 2 and all(not r.get("new_BL_held") and not r.get("hidden_blockers_revealed") for r in rows[:3]):
        res["stop_loss"] = "B1+L and next 2 bundles: held-out newly lint-clean 0 and no hidden blocker revealed"
        break
res["pack_only_proto_differs_from_full"] = pack_proto_diff
res["steps_run"] = len(rows)

# ---- curve (held-out only): cumulative vars resolved vs held-out lint-clean
curve, seen = [], set()
for r in rows:
    if "error" in r:
        continue
    seen |= set(r["new_BL_held"])
    curve.append([r["cum_vars_resolved"], len(seen)])
res["curve_heldout"] = curve

# ---- controls
Ub1 = sorted(PS | HS | set(b1_targets))
# noop
noop = run([], sorted(C["base"])[:30] if False else [t for t in sorted(C["base"]) if C["base"][t]["clean"]][:30], "noop")
res["control_noop"] = dict(byte_identical=all(noop[f][0]["c_sha256"] == C["base"][f]["c_sha256"] for f in noop), n=len(noop),
                           unlock=len(d5.measure(sorted(noop), noop)[0]))
# matched null: same size (3 comps), no target set closed
deg = collections.Counter(v for s in fvars.values() for v in s)
want = sorted(deg[c] for c in B1)
bydeg = collections.defaultdict(list)
for c in sorted(specs):
    if specs[c]["kind"] == "helper":
        bydeg[deg[c]].append(c)
rnd = random.Random(SEED); null = None
pool = [c for c in sorted(specs) if specs[c]["kind"] == "helper" and c not in B1]
for _ in range(4000):
    cand = []
    for dq in want:
        dd = min(bydeg, key=lambda k: (abs(k - dq), k))
        cand.append(rnd.choice([c for c in bydeg[dd] if c not in cand and c not in B1] or pool))
    if len(set(cand)) == 3 and not any(fvars[f] <= set(cand) for f in fvars):
        null = sorted(cand); break
if null:
    nl, _w = jd.build_lines([(c, specs[c]) for c in null], sc, C)
    Un = sorted(clo(nl + L_LINES) | PS | HS)
    nn = run(nl + L_LINES, Un, "null")
    res["control_matched_null"] = dict(bundle=null, unlock=len(d5.measure(Un, nn)[0]), vs_L_alone_in_same_universe=len(d5.measure(Un, run(L_LINES, Un, "nullL"))[0]))
else:
    res["control_matched_null"] = "NOT_FOUND"
# wrong width at +0xA4C: u8 -> u32 (must not raise lint-clean over the right-width joint step 0)
wrong = [l.replace("u8 f_A4C; /* +0xA4C */", "u32 f_A4C; /* +0xA4C */") for l in L_LINES]
assert wrong != L_LINES
Uw = sorted(clo(b1_lines + wrong) | PS | HS | set(b1_targets))
nw = run(b1_lines + wrong, Uw, "wrong")
nr = run(b1_lines + L_LINES, Uw, "right")
res["control_wrong_width"] = dict(unlock_wrong=len(d5.measure(Uw, nw)[0]), unlock_right=len(d5.measure(Uw, nr)[0]),
                                  held_wrong=len(set(d5.measure(Uw, nw)[0]) & HS), held_right=len(set(d5.measure(Uw, nr)[0]) & HS))
json.dump(res, open(OUT + "/summary.json", "w"), indent=1)
log("DONE", json.dumps({k: v for k, v in res.items() if k.startswith("control")}))
