#!/usr/bin/env python3
"""D7 incremental recompile. GEX44: KSR_DECOMP_TOOLS=/opt/ksr-decomp /opt/ksr-decomp/venv/bin/python -I d7.py <step> <out>
steps: full (whole-corpus timing runs, per variant) | replay | controls. No model calls."""
import hashlib, json, os, re, sys, time
D28 = "/home/kobii/missions/tennis-w11/out/d28"
sys.path.insert(0, D28 + "/d5/tools"); sys.path.insert(0, D28 + "/tools")
import d5, dirty  # noqa: E402

F = "fn_801D022C"
VARIANTS = [("D5_void_void", "void fn_801D022C(void);"),
 ("fixed5_void", "void fn_801D022C(s32 arg0, s32 arg1, s32 arg2, s32 arg3, s32 arg4);"),
 ("fixed5_ptr_void", "void fn_801D022C(void *arg0, s32 arg1, s32 arg2, s32 arg3, s32 arg4);"),
 ("var5_ptr_void", "void fn_801D022C(void *arg0, s32 arg1, s32 arg2, s32 arg3, s32 arg4, ...);"),
 ("var5_s32_void", "void fn_801D022C(s32 arg0, s32 arg1, s32 arg2, s32 arg3, s32 arg4, ...);")]
SIG = re.compile(r'^[A-Za-z_][\w\s\*]*\bfn_[0-9A-F]{8}\(.*$', re.M)


def sig(c, fn):
    for l in c.split("\n"):
        if re.match(r'^[A-Za-z_][\w\s\*]*\b%s\(' % re.escape(fn), l) and l.rstrip().endswith("{"):
            return l.strip()
    return ""


def total_sha(recs, fns):
    return hashlib.sha256("".join(recs[f]["c_sha256"] for f in sorted(fns)).encode()).hexdigest()


def clean_set(recs):
    return sorted(f for f, r in recs.items() if r["clean"])


def incremental(C, ctxpath, hdr_new, out):
    """dirty closure -> rerun -> fixpoint over callers of fns whose emitted signature changed."""
    t0 = time.time()
    asm = d5.load()["text"]
    seed, info = dirty.closure(C, C["hctx"], open(hdr_new, encoding="utf-8").read(), asm)
    # D4 rule: a dependent's emitted signature reaches other functions only as a *header prototype* (m2c reads the
    # context, not neighbours' C), i.e. only when the dependent is newly lint-clean and its signature is then adopted
    # (wave 2). So the replay is one level: the static closure. Wave 2 is measured separately in wave2().
    done, levels = {}, []
    recs = {f: dict(r) for f, r in C["base"].items()}
    cs = dict(C["basec"])
    new, _ = d5.run_set(sorted(seed), ctxpath)
    for f in seed:
        recs[f] = new[f][0]; cs[f] = new[f][1]; done[f] = 0
    levels.append(len(seed))
    return recs, cs, dict(seed=seed, levels=levels, closure=sorted(done), info=info, wall_s=round(time.time() - t0, 2))


def ctx_for(tag, proto, out):
    return "%s/ctx/%s.h" % (out, tag)


def wave2(C, recs, cs, ctx):
    """Transitive unlock: functions whose every blocker is HELPER:g with g newly clean; g's emitted signature becomes the
    prototype for them (same rule as D5 wave 2). Measured, not predicted."""
    newly = sorted(f for f in recs if recs[f]["clean"] and not C["base"][f]["clean"])
    protos = []
    for g in newly:
        s = sig(cs[g], g)
        if s and "?" not in s:
            protos.append(s.rstrip("{").rstrip() + ";")
    pf = set(newly)
    keysof = {}
    for k, v in C["keyfns"].items():
        for f in v:
            keysof.setdefault(f, set()).add(k)
    deps = sorted(f for f, ks in keysof.items() if ks and all(k.startswith("HELPER:") and k.split(":", 1)[1] in pf for k in ks))
    if not deps:
        return dict(newly_clean_in=newly, dependents=[], newly_clean=[], note="no function is blocked only by newly clean callees")
    p = ctx + ".w2.h"
    open(p, "w", encoding="utf-8", newline="\n").write(open(ctx, encoding="utf-8").read().rstrip("\n") + "\n" + "".join(l + "\n" for l in protos))
    new, _ = d5.run_set(deps, p)
    return dict(newly_clean_in=newly, dependents=deps, newly_clean=sorted(f for f in deps if new[f][0]["clean"]))


def main():
    step, out = sys.argv[1], sys.argv[2]
    os.makedirs(out + "/ctx", exist_ok=True)
    Cd = d5.load()
    C = dirty.load()
    if step == "full":
        res = {}
        for tag, proto in VARIANTS:
            ctx = d5.make_ctx("%s/ctx/%s.h" % (out, tag), [proto])
            t0 = time.time()
            new, _ = d5.run_set(sorted(C["base"]), ctx)
            w = time.time() - t0
            recs = {f: new[f][0] for f in new}
            res[tag] = dict(wall_s=round(w, 2), clean=clean_set(recs), sha=total_sha(recs, recs),
                            sigchanged=sorted(f for f in new if sig(new[f][1], f) != sig(C["basec"][f], f)),
                            changed=sorted(f for f in new if recs[f]["c_sha256"] != C["base"][f]["c_sha256"]))
            print("FULL", tag, round(w, 1), len(res[tag]["clean"]), len(res[tag]["changed"]), flush=True)
        json.dump(res, open(out + "/full_runs.json", "w"), indent=1, sort_keys=True)
    elif step == "replay":
        full = json.load(open(out + "/full_runs.json"))
        res = {}
        for tag, proto in VARIANTS:
            ctx = "%s/ctx/%s.h" % (out, tag)
            recs, cs, inf = incremental(C, ctx, ctx, out)
            cl = clean_set(recs)
            fr = full[tag]
            clos = set(inf["closure"])
            res[tag] = dict(closure_size=len(clos), levels=inf["levels"], seed_size=len(inf["seed"]), wall_s_incremental=inf["wall_s"],
                            wall_s_full=fr["wall_s"], clean_incremental=len(cl), clean_full=len(fr["clean"]),
                            clean_diff=sorted(set(cl) ^ set(fr["clean"])), sha_incremental=total_sha(recs, recs), sha_full=fr["sha"],
                            sha_equal=total_sha(recs, recs) == fr["sha"],
                            full_changed_outside_closure=sorted(set(fr["changed"]) - clos),
                            direct_unlock=sorted(f for f in inf["seed"] if recs[f]["clean"] and not C["base"][f]["clean"]),
                            transitive_unlock=None,
                            n_full_unlock=len(set(fr["clean"]) - set(clean_set(C["base"]))), info=inf["info"])
            w2 = wave2(C, recs, cs, ctx_for(tag, proto, out))
            res[tag]["wave2"] = w2
            print("REPLAY", tag, res[tag]["closure_size"], res[tag]["clean_diff"], res[tag]["sha_equal"], res[tag]["wall_s_incremental"], res[tag]["wall_s_full"], flush=True)
        json.dump(res, open(out + "/replay.json", "w"), indent=1, sort_keys=True)
    elif step == "controls":
        res = {}
        # (a) unused fact
        unused = C["hctx"].rstrip("\n") + "\nvoid zz_d7_unused_fact(s32 a0);\n"
        asm = Cd["text"]
        seed, inf = dirty.closure(C, C["hctx"], unused, asm)
        res["unused_fact"] = dict(closure=seed, size=len(seed), info=inf)
        # (b) widely used struct: most-mentioned typedef tag in baseline C; flip its first 4-byte int member type
        cnt = {}
        for m in re.finditer(r'typedef struct (\w+) \{(.*?)\n\} (\w+);', C["hctx"], re.S):
            tag, body, tn = m.groups()
            n = sum(1 for t in C["basec"].values() if re.search(r'\b(%s|%s)\b' % (tag, tn), t))
            mm = re.search(r'^(\s+)(s32|u32) (\w+);', body, re.M)
            if mm: cnt[tag] = (n, tn, mm.group(0), mm.group(1) + ("u32" if mm.group(2) == "s32" else "s32") + " " + mm.group(3) + ";")
        tag = max(cnt, key=lambda k: (cnt[k][0], k))
        n, tn, oldl, newl = cnt[tag]
        hdr = C["hctx"].replace(oldl, newl, 1)
        assert hdr != C["hctx"]
        p = out + "/ctx/wide_struct.h"
        open(p, "w", encoding="utf-8", newline="\n").write(hdr)
        recs, cs, inf = incremental(C, p, p, out)
        full, _ = d5.run_set(sorted(C["base"]), p)
        fchanged = sorted(f for f in full if full[f][0]["c_sha256"] != C["base"][f]["c_sha256"])
        res["wide_struct"] = dict(tag=tag, typedef=tn, edit=[oldl.strip(), newl.strip()], mentions=n, closure_size=len(inf["closure"]),
                                  full_changed=len(fchanged), full_changed_outside_closure=sorted(set(fchanged) - set(inf["closure"])),
                                  clean_equal=clean_set(recs) == sorted(f for f in full if full[f][0]["clean"]),
                                  sha_equal=total_sha(recs, recs) == total_sha({f: full[f][0] for f in full}, full), info=inf["info"])
        # (c) D6 saw change: D5_void_void newly-clean fns inside its closure
        fr = json.load(open(out + "/full_runs.json"))["D5_void_void"]
        newly = sorted(set(fr["clean"]) - set(clean_set(C["base"])))
        seed2, _ = dirty.closure(C, C["hctx"], open(out + "/ctx/D5_void_void.h", encoding="utf-8").read(), asm)
        res["d6_changed_in_closure"] = dict(d6_saw_change=newly, missing=sorted(set(newly) - set(seed2)), closure=len(seed2))
        json.dump(res, open(out + "/controls.json", "w"), indent=1, sort_keys=True)
        print("CONTROLS", res["unused_fact"]["size"], res["wide_struct"]["closure_size"], res["wide_struct"]["full_changed_outside_closure"], res["d6_changed_in_closure"]["missing"])


main()