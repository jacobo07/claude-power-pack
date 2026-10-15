#!/usr/bin/env python3
"""D12a step 3: joint delta over conjunctive bundles.  GEX44:
  KSR_DECOMP_TOOLS=/opt/ksr-decomp /opt/ksr-decomp/venv/bin/python joint_delta.py <d12_dir>
Needs d5.py + d7 (dirty.py, d7.py) in M/out/d28/tools or d5/tools.  No model calls.
Selector uses ONLY (target set, bundle size): Expected Bulk Unlock = targets closed / bundle size.  No degree field is read
by select_bundles (degree appears only in the matched-null CONTROL builder)."""
import collections, hashlib, itertools, json, os, re, sys

D12 = sys.argv[1]
M = "/home/kobii/missions/tennis-w11"
D28 = M + "/out/d28"
for p in (D28 + "/d5/tools", D28 + "/d7", D28 + "/d1d/tools", D28 + "/tools"):
    sys.path.insert(0, p)
import d5, dirty  # noqa: E402


def sig(c, fn):  # copy of d7.sig (d7.py runs main() on import)
    for l in c.split("\n"):
        if re.match(r'^[A-Za-z_][\w\s\*]*\b%s\(' % re.escape(fn), l) and l.rstrip().endswith("{"):
            return l.strip()
    return ""

TOP, MAX_BUNDLE, MAX_TARGET_CAND = 10, 8, 4000
M2C = ("m2c", "m2c_failed")
LOADS = {"lbz": "u8", "lbzu": "u8", "lhz": "u16", "lha": "s16", "lwz": "u32", "lfs": "f32", "lfd": "f64", "lhzu": "u16", "lwzu": "u32"}


def ctype(op, w):
    base = op.rstrip("ux")
    if base in ("stfs", "lfs"):
        return "f32"
    if base in ("stfd", "lfd"):
        return "f64"
    if base == "lha":
        return "s16"
    return {1: "u8", 2: "u16", 4: "u32", 8: "u64"}.get(w)


def load_inputs():
    rows = [json.loads(l) for l in open(D12 + "/residuals_v1.jsonl") if l.strip()]
    tgt = [r for r in rows if r["distance"] in (2, 3, 4, 5)]
    sc = {c["cluster"]: c for c in json.load(open(D12 + "/struct_clusters.json"))["clusters"]}
    return tgt, sc


def component_for(var, fn, sc, hctx, C):
    """-> (component id, spec) or (None, reason).  Only script-stateable components."""
    t = var["type"]
    if t == "field_untyped":
        return "SKIP", None
    if t == "helper":
        F = var["id"].split(":", 1)[1]
        if re.search(r'\b%s\b' % re.escape(F), hctx):
            return None, "helper already declared in context"
        if F not in d5.prog().fns:
            return None, "helper body not in corpus (MODEL_NEEDED)"
        hyps, _ = d5.helper_hyps(F)
        ok = [h for h in hyps if d5.asm_admits(F, h)[0]]
        if not ok:
            return None, "no helper prototype survives the asm check (MODEL_NEEDED)"
        return var["id"], dict(kind="helper", proto=ok[0]["proto"], n_admitted=len(ok))
    if t == "struct_field":
        cl = sc[var["cluster"]]
        if cl["status"] == "CONFLICT":
            return None, "cluster CONFLICT kept"
        roots = {m["root"] for m in cl["members"]}
        if len(roots) != 1:
            return None, "cluster has several roots"
        root = json.loads(next(iter(roots)))
        if root[0] == "ARG" and root[1] == fn:
            if re.search(r'\b%s\s*\(' % re.escape(fn), hctx):
                return None, "fn already prototyped in context"
            return var["id"], dict(kind="struct", cluster=var["cluster"], root=root)
        return None, "root %s not ARG of own fn (nested/global: MODEL_NEEDED)" % root[0]
    return None, "var type %s not script-stateable" % t


def build_lines(comps, sc, C):
    """context lines for a set of component ids."""
    lines, structs = [], collections.defaultdict(dict)
    for cid, spec in comps:
        if spec["kind"] == "helper":
            lines.append(spec["proto"])
        else:
            off = int(cid.rsplit("+", 1)[1], 16)
            structs[spec["cluster"]][off] = spec
    for cl, offs in sorted(structs.items()):
        mem = sc[cl]["members"]
        fn = json.loads(mem[0]["root"])[1]
        argi = json.loads(mem[0]["root"])[2]
        fields, end = [], 0
        for off in sorted(offs):
            ms = [m for m in mem if m["offset"] == off]
            tys = {ctype(m["op"], m["width"]) for m in ms}
            if len(tys) != 1 or None in tys:
                return None, "width/type ambiguity at %s+0x%X" % (cl, off)
            ty = tys.pop()
            w = {"u8": 1, "s8": 1, "u16": 2, "s16": 2, "u32": 4, "f32": 4, "u64": 8, "f64": 8}[ty]
            if off < end:
                return None, "overlap at %s+0x%X" % (cl, off)
            if off > end:
                fields.append("    u8 pad_%02X[0x%X];" % (end, off - end))
            fields.append("    %s f_%02X;" % (ty, off))
            end = off + w
        tag = "S_" + cl
        s = C["basec"].get(fn, "")
        sg = sig(s, fn)
        if not sg or "?" in sg:
            return None, "no emitted signature for %s" % fn
        m = re.match(r'^(.*?)\b%s\((.*)\)\s*\{$' % re.escape(fn), sg)
        args = [a.strip() for a in m.group(2).split(",")] if m.group(2).strip() != "void" else []
        if argi >= len(args):
            return None, "arg%d absent from emitted signature of %s" % (argi, fn)
        args[argi] = "%s *arg%d" % (tag, argi)
        lines.append("typedef struct %s {\n%s\n} %s;" % (tag, "\n".join(fields), tag))
        lines.append("%s%s(%s);" % (m.group(1), fn, ", ".join(args) or "void"))
    return lines, None


def select_bundles(fvars):
    """fvars: {fn: frozenset(stateable component ids)} -> ranked bundles.  Reads only var sets (no degree)."""
    cand = {}
    fns = sorted(fvars)
    byvar = collections.defaultdict(list)
    for f in fns:
        for v in fvars[f]:
            byvar[v].append(f)
    seeds = [fvars[f] for f in fns]
    for f in fns:
        for v in fvars[f]:
            for g in byvar[v]:
                if g > f:
                    seeds.append(fvars[f] | fvars[g])
    for B in seeds:
        B = frozenset(B)
        if len(B) < 2 or len(B) > MAX_BUNDLE or B in cand:
            continue
        tg = tuple(g for g in fns if fvars[g] <= B)
        cand[B] = tg
    ranked = sorted(cand.items(), key=lambda kv: (-len(kv[1]) / len(kv[0]), -len(kv[1]), sorted(kv[0])))
    return [(sorted(B), list(tg)) for B, tg in ranked[:TOP]], len(cand)


def run_ctx(C, hctx_lines, fns):
    ctx = d5.make_ctx(D12 + "/ctx_tmp.h", hctx_lines)
    new, _ = d5.run_set(sorted(fns), ctx)
    return new


def dirty_set(C, lines):
    old = C["hctx"]
    new = old.rstrip("\n") + "\n" + "".join(l + "\n" for l in lines)
    clo, info = dirty.closure(C, old, new, d5.load()["text"])
    return clo, info


def measure_bundle(C, comps, sc, targets):
    lines, why = build_lines(comps, sc, C)
    if lines is None:
        return dict(error=why)
    clo, info = dirty_set(C, lines)
    fns = sorted(set(clo) | set(targets))
    new = run_ctx(C, lines, fns)
    unl, errs, _ = d5.measure(fns, new)
    tg_clean = [t for t in targets if new[t][0]["clean"]]
    hidden = {}
    for t in targets:
        if not new[t][0]["clean"]:
            hidden[t] = d5.keys_after(t, new[t][0], new[t][1])
    return dict(closure_size=len(clo), newly_clean=unl, targets_closed_clean=tg_clean, hidden_blockers=hidden, new_errors=errs,
                sha=hashlib.sha256("".join(new[f][0]["c_sha256"] for f in fns).encode()).hexdigest())


def main():
    tgt, sc = load_inputs()
    C = dirty.load()
    hctx = C["hctx"]
    d5.load()
    ru = {r["fn"] for r in tgt if any(v["type"] in M2C for v in r["unresolved_vars"])}
    specs, fvars, reasons = {}, {}, collections.Counter()
    for r in tgt:
        if r["fn"] in ru or r["fn"] not in C["base"]:
            reasons["RESIDUAL_UNKNOWN or not in base"] += 1
            continue
        ids, ok = set(), True
        for v in r["unresolved_vars"]:
            cid, spec = component_for(v, r["fn"], sc, hctx, C)
            if cid == "SKIP":
                continue
            if cid is None:
                ok = False
                reasons[spec] += 1
                break
            ids.add(cid)
            specs[cid] = spec
        if ok and ids and not C["base"][r["fn"]]["clean"]:
            fvars[r["fn"]] = frozenset(ids)
    print("stateable target fns", len(fvars), "components", len(specs), dict(reasons))
    bundles, ncand = select_bundles(fvars)
    out = dict(n_stateable_targets=len(fvars), n_components=len(specs), unstateable_reasons=dict(reasons), n_candidate_bundles=ncand,
               selector="select_bundles reads var sets only (EBU = targets/size); bundles of size>=2 only", bundles=[], controls={})
    single_cache = {}

    def single(cid, targets_hint):
        if cid not in single_cache:
            single_cache[cid] = measure_bundle(C, [(cid, specs[cid])], specs and sc, [])
        return single_cache[cid]

    stop_zero = 0
    for bi, (B, tg) in enumerate(bundles):
        comps = [(c, specs[c]) for c in B]
        res = measure_bundle(C, comps, sc, tg)
        row = dict(bundle=B, size=len(B), targets=tg, ebu=round(len(tg) / len(B), 3), **res)
        if "error" not in res:
            sings = {c: len(measure_bundle(C, [(c, specs[c])], sc, [])["newly_clean"]) for c in B}
            row["single_unlock"] = sings
            row["unlock"] = len(res["newly_clean"])
            row["complementarity"] = row["unlock"] - sum(sings.values())
        out["bundles"].append(row)
        print("BUNDLE", bi, len(B), len(tg), row.get("unlock"), row.get("complementarity"), res.get("error", ""), flush=True)
        if bi < 3 and row.get("unlock", 0) == 0 and not any(res.get("hidden_blockers", {}).values()) and "error" not in res:
            stop_zero += 1
        if bi == 2 and stop_zero == 3:
            out["stop_loss"] = "top 3 bundles unlocked 0 and revealed nothing: stopped"
            break
    # ---- controls
    empty = [t for t in sorted(C["base"]) if C["base"][t]["clean"]][:30]
    new = run_ctx(C, [], empty)
    out["controls"]["noop"] = dict(lines=0, dirty=len(dirty_set(C, [])[0]), unlock=len(d5.measure(empty, new)[0]),
                                   byte_identical=all(new[f][0]["c_sha256"] == C["base"][f]["c_sha256"] for f in empty), sample=len(empty))
    wrong = None
    for cid, sp in specs.items():
        if sp["kind"] == "helper":
            F = cid.split(":", 1)[1]
            ev = d5.callee_evidence(F)
            if ev["min_gpr"] > 0:
                h = dict(arity_gpr=0, nfpr=0, ret="void")
                wrong = dict(helper=F, hypothesis="void %s(void);" % F, admitted=d5.asm_admits(F, h)[0], reason=d5.asm_admits(F, h)[1])
                break
    out["controls"]["d5_wrong_delta"] = wrong
    # matched null: same size, same per-component fn-degree multiset (degree used ONLY here), closes no target set
    deg = collections.Counter(v for s in fvars.values() for v in s)
    if out["bundles"]:
        B0 = out["bundles"][0]["bundle"]
        want = sorted(deg[c] for c in B0)
        pool = sorted(specs, key=lambda c: (deg[c], c))
        null = None
        import random
        rnd = random.Random(20261014)
        bydeg = collections.defaultdict(list)
        for c in pool:
            bydeg[deg[c]].append(c)
        for _ in range(4000):
            cand = []
            for dq in want:   # per slot: a component of the same degree (nearest available if none)
                dd = min(bydeg, key=lambda k: (abs(k - dq), k))
                cand.append(rnd.choice([c for c in bydeg[dd] if c not in cand] or pool))
            if len(set(cand)) == len(want) and not any(fvars[f] <= set(cand) for f in fvars):
                null = sorted(cand)
                break
        if null:
            r0 = measure_bundle(C, [(c, specs[c]) for c in null], sc, [])
            out["controls"]["matched_null"] = dict(bundle=null, unlock=len(r0.get("newly_clean", [])), closes_target_set=False, result=r0.get("error", "ok"))
        else:
            out["controls"]["matched_null"] = "NOT_FOUND (no degree-matched non-closing set in 4000 draws)"
    json.dump(out, open(D12 + "/joint_delta.json", "w"), indent=1, sort_keys=True)
    print(json.dumps({k: v for k, v in out.items() if k != "bundles"})[:1500])


if __name__ == "__main__":
    main()

