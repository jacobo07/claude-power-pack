#!/usr/bin/env python3
"""D4 frontier / semantic dominators / causal graph / red control.
Usage: frontier.py <d3_out> <d1d_out> <near_match.json> <d4_out>
Deterministic (seed 28). No model calls."""
import json, sys, os, collections, random, re, hashlib

D3, D1D, NEAR, OUT = sys.argv[1:5]
SEED = 28
os.makedirs(OUT, exist_ok=True)

# ---- rules (stated; also written into frontier.json) ----
# VAR = every unresolved_vars id except type field_offset_untyped (per-function offsets inside the per-function
# FIELD_UNTYPED key; no cross-function identity is provable). Direct block: fn lists VAR in unresolved_vars and is not lint-clean.
# SIGNATURE-BEARING vars: HELPER:F (prototype of F) and SELF_SIG:F (F's own signature). Transitive rule: a caller of a
# function blocked by a signature-bearing var is blocked in turn ONLY when its own signature uses the unresolved type.
# That is not decidable from the asm, so: transitive LOW = 0 (none proven), transitive HIGH = every non-clean, not
# directly blocked ancestor reachable over call edges from the subject F (pass-through assumption). Non-signature vars
# (FIELD, FIELD_UNTYPED, QTYPE_LOCAL, M2C, M2C_FAILED) are local to a body: transitive = [0,0].
# Direct LOW = functions for which VAR is the SOLE var (resolving it alone unlocks them); direct HIGH = all direct.
# blocked = [direct_sole + 0, direct_all + trans_high]. COST classes (units, range [lo,hi]) are a fixed table:
COST = {"HELPER": ("SCRIPT_PROTOTYPE", 1, 2), "SELF_SIG": ("SCRIPT_PROTOTYPE", 1, 2),
        "FIELD": ("SCRIPT_GLOBAL_FIELD_TYPE", 2, 4), "QTYPE_LOCAL": ("LOCAL_TYPE_INFERENCE", 2, 4),
        "FIELD_UNTYPED": ("STRUCT_INFERENCE", 3, 6), "M2C": ("TOOL_SIDE_M2C", 4, 8), "M2C_FAILED": ("MODEL_CFG_RECOVERY", 6, 12)}


def kind(v):
    return v.split(":", 1)[0]


res = [json.loads(l) for l in open(os.path.join(D3, "residuals.jsonl"))]
facts = {}
for l in open(os.path.join(D1D, "facts.jsonl")):
    r = json.loads(l)
    facts[r["fn"]] = r
rid = {r["fn"]: r for r in res}
corp = set(rid)


def varset(r):
    return sorted({v["id"] for v in r["unresolved_vars"] if v["type"] != "field_offset_untyped"})


VARS = {f: varset(r) for f, r in rid.items() if not r["lint_clean"]}
callers = {f: [c for c in facts[f]["callers"] if c in corp] for f in corp}


def ancestors(F):
    seen = set()
    st = [F]
    while st:
        x = st.pop()
        for c in callers.get(x, []):
            if c not in seen:
                seen.add(c)
                st.append(c)
    seen.discard(F)
    return seen


def compute(VARS, subject_map=None):
    byvar = collections.defaultdict(set)
    for f, vs in VARS.items():
        for v in vs:
            byvar[v].add(f)
    out = {}
    for v, fs in byvar.items():
        k = kind(v)
        sole = {f for f in fs if len(VARS[f]) == 1}
        th = set()
        if k in ("HELPER", "SELF_SIG"):
            subj = v.split(":", 1)[1]
            if subject_map:
                subj = subject_map.get(subj, subj)
            if subj in corp:
                th = {a for a in ancestors(subj) if a in VARS and a not in fs}
        cls, clo, chi = COST[k]
        blo, bhi = len(sole), len(fs) + len(th)
        out[v] = {"var": v, "kind": k, "blocked_direct": [len(sole), len(fs)], "blocked_transitive": [0, len(th)],
                  "blocked": [blo, bhi], "resolution_cost": {"class": cls, "units": [clo, chi]},
                  "score": [round(blo / chi, 4), round(bhi / clo, 4)], "_fns": sorted(fs), "_sole": sorted(sole)}
    return out


def rank(fr):
    return sorted(fr.values(), key=lambda d: (-(d["score"][0] + d["score"][1]) / 2, -d["score"][1], d["var"]))


fr = compute(VARS)
rk = rank(fr)
rules = open(__file__).read().split("# ---- rules")[1].split("COST =")[0]
frontier = {"rules": rules, "n_vars": len(fr), "n_nonclean_fns": len(VARS),
            "vars": [dict({k: v for k, v in d.items() if not k.startswith("_")}, n_fns=len(d["_fns"]), residual_rows=d["_fns"][:50])
                     for d in sorted(fr.values(), key=lambda d: d["var"])]}
json.dump(frontier, open(os.path.join(OUT, "frontier.json"), "w"), indent=1)

top = rk[:30]
dom = {"score_def": "score=[blocked_low/cost_hi, blocked_high/cost_lo]; potential energy = blocked range (fns); ranked by score midpoint",
       "top30": [dict({"rank": i + 1}, **{k: v for k, v in d.items() if not k.startswith("_")},
                      evidence_rows=[{"fn": f, "distance": rid[f]["distance"], "obligations": rid[f]["obligations"][:2],
                                      "sole": f in d["_sole"]} for f in d["_fns"][:8]]) for i, d in enumerate(top)]}
json.dump(dom, open(os.path.join(OUT, "dominators.json"), "w"), indent=1)

# ---- causal ----
near = json.load(open(NEAR))["per_function"]


def wcls(v):
    if not v:
        return None
    return v if (v.startswith("FAIL") or v.startswith("EXCL")) else v.split(" ")[0]


classes = collections.defaultdict(set)
for f, r in rid.items():
    for c in facts[f]["m2c_with_ctx"].get("lint_codes", []):
        classes["lint:" + c].add(f)
    for b in r["blocker_kinds"]:
        classes["blocker:" + b].add(f)
    w = wcls(r["w12_verdict"])
    if w:
        classes["w12:" + w].add(f)
for f, d in near.items():
    classes["near:" + d["primary"]].add(f)
rows = []
for cname, fs in sorted(classes.items()):
    fs = sorted(fs)
    sets = [set(VARS.get(f, [])) for f in fs]
    shared = set.intersection(*sets) if sets else set()
    cnt = collections.Counter(v for s in sets for v in s)
    if cname.startswith("near:"):
        root = {"type": "RULE", "id": cname[5:], "note": "PARTIAL fns are lint-clean: cause is a codegen rule (D2 near_match primary), no unresolved var"}
        shared_root = True
    elif shared:
        root = {"type": "VAR", "id": sorted(shared)[0], "all_shared": sorted(shared)[:5]}
        shared_root = True
    elif not any(sets):
        root = {"type": "NONE", "id": "NO_UNRESOLVED_VAR", "note": "functions in this class carry no unresolved var"}
        shared_root = False
    else:
        root = {"type": "NO_SHARED_ROOT", "id": cnt.most_common(1)[0][0], "coverage": cnt.most_common(1)[0][1]}
        shared_root = False
    rows.append({"class": cname, "root_cause": root, "n_functions": len(fs), "functions": fs, "single_shared_root": shared_root})
comp = [r["class"] for r in rows if r["single_shared_root"]]
causal = {"method": "class (lint code | blocker kind | W12 verdict | D2 near-match primary) -> root (intersection of its functions' var sets, or the D2 rule) -> functions",
          "n_classes": len(rows),
          "compression": {"classes_with_single_shared_root": len(comp), "of": len(rows), "classes": comp,
                          "note": "a class whose functions all share one root cause compresses to that one row"},
          "rows": rows}
json.dump(causal, open(os.path.join(OUT, "causal.json"), "w"), indent=1)


# ---- red control ----
def stats(tp):
    return {"mean_low": round(sum(d["score"][0] for d in tp) / len(tp), 4),
            "mean_high": round(sum(d["score"][1] for d in tp) / len(tp), 4),
            "mean_mid": round(sum((d["score"][0] + d["score"][1]) / 2 for d in tp) / len(tp), 4)}


real = stats(top)
pairs = [(f, v) for f, vs in VARS.items() for v in vs]
nperm = 20
per = []
for p in range(nperm):
    rng = random.Random(SEED + p)
    cols = [v for _, v in pairs]
    rng.shuffle(cols)
    # repair duplicates (same var twice on one fn) by swapping columns so every fn keeps its exact var count
    for _ in range(200):
        seen = set(); dup = []
        for i, ((f, _), v) in enumerate(zip(pairs, cols)):
            if (f, v) in seen: dup.append(i)
            seen.add((f, v))
        if not dup: break
        for i in dup:
            j = rng.randrange(len(cols)); cols[i], cols[j] = cols[j], cols[i]
    NV = collections.defaultdict(set)
    for (f, _), v in zip(pairs, cols):
        NV[f].add(v)
    NV = {f: sorted(s) for f, s in NV.items()}
    nodes = sorted(corp)
    sh = nodes[:]
    rng.shuffle(sh)
    smap = dict(zip(nodes, sh))
    per.append(stats(rank(compute(NV, subject_map=smap))[:30]))
red = {"method": "pool all (fn,var) pairs; reassign var column at random (var degrees and fn degrees preserved, co-occurrence destroyed) and permute call-subject identity of HELPER/SELF_SIG vars; recompute top-30",
       "n_perm": nperm, "seed": SEED, "real": real,
       "shuffled_mean": {k: round(sum(p[k] for p in per) / nperm, 4) for k in real},
       "shuffled_max": {k: max(p[k] for p in per) for k in real},
       "falls": {k: real[k] > max(p[k] for p in per) for k in real}}
# transitive-only control: keep VARS, permute only the call-subject identity (what the call graph adds to the score)
def tstat(tp):
    return round(sum(d["blocked_transitive"][1] for d in tp) / len(tp), 4)
tper = []
for p in range(nperm):
    rng = random.Random(SEED + 100 + p)
    nodes = sorted(corp); sh = nodes[:]; rng.shuffle(sh)
    tper.append(tstat(rank(compute(VARS, subject_map=dict(zip(nodes, sh))))[:30]))
red["transitive_control"] = {"method": "permute subject identity only (direct sets fixed); stat = mean transitive-high over each run's own top-30",
    "real": tstat(top), "shuffled_mean": round(sum(tper) / nperm, 4), "shuffled_max": max(tper), "falls": tstat(top) > max(tper)}
red["note"] = ("Direct blocked counts are degree counts: any var-degree-preserving shuffle leaves them unchanged, so the score-level "
               "control (falls{}) is INCONCLUSIVE for the direct part by construction and is reported, not gated. The call-graph "
               "contribution is what a shuffle can falsify: transitive_control.")
json.dump(red, open(os.path.join(OUT, "redcontrol.json"), "w"), indent=1)
dom["red_control_verdict"] = ("RED_FALLS" if red["transitive_control"]["falls"] else "RED_DOES_NOT_FALL: transitive part indistinguishable from permuted call subjects; ranking is degree-driven and INCONCLUSIVE as a structural claim")
json.dump(dom, open(os.path.join(OUT, "dominators.json"), "w"), indent=1)
print(json.dumps(red, indent=1))
print("frontier vars", len(fr), "causal classes", len(rows), "compressed", len(comp))
h = hashlib.sha256()
for n in ("frontier", "dominators", "causal", "redcontrol"):
    h.update(open(os.path.join(OUT, n + ".json"), "rb").read())
open(os.path.join(OUT, "outputs.sha256"), "w").write(h.hexdigest() + "\n")
