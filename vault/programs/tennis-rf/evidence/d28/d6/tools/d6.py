#!/usr/bin/env python3
"""D6 direct-unlock measurement. GEX44: export KSR_DECOMP_TOOLS=/opt/ksr-decomp; <venv>/python -I d6.py <step> <out>
steps: asmcheck | variants | full <variant-index>
Reuses d5.py (load, run_set, measure). Baseline = d1d ctx_run1 (1797 fns, 276 clean). No model calls."""
import hashlib, json, os, sys
sys.path.insert(0, "/home/kobii/missions/tennis-w11/out/d28/d5/tools")
import d5  # noqa: E402

F = "fn_801D022C"
VARIANTS = [
    ("D5_void_void", "void fn_801D022C(void);"),
    ("fixed5_void", "void fn_801D022C(s32 arg0, s32 arg1, s32 arg2, s32 arg3, s32 arg4);"),
    ("fixed5_ptr_void", "void fn_801D022C(void *arg0, s32 arg1, s32 arg2, s32 arg3, s32 arg4);"),
    ("var5_ptr_void", "void fn_801D022C(void *arg0, s32 arg1, s32 arg2, s32 arg3, s32 arg4, ...);"),
    ("var5_s32_void", "void fn_801D022C(s32 arg0, s32 arg1, s32 arg2, s32 arg3, s32 arg4, ...);"),
]


def summarize(fns, new):
    C = d5.load()
    unl, errs, _ = d5.measure(fns, new)
    clean = sorted(f for f in fns if new[f][0]["clean"])
    return dict(n=len(fns), newly_clean=unl, n_unlock=len(unl), new_errors=errs, n_clean_after=len(clean),
                sha=hashlib.sha256("".join(new[f][0]["c_sha256"] for f in sorted(fns)).encode()).hexdigest())


def main():
    step, out = sys.argv[1], sys.argv[2]
    os.makedirs(out + "/ctx", exist_ok=True)
    C = d5.load()
    deps = sorted(C["keyfns"]["HELPER:" + F])
    if step == "variants":
        rows = []
        for tag, proto in VARIANTS:
            ctx = d5.make_ctx("%s/ctx/%s.h" % (out, tag), [proto])
            try:
                new, _ = d5.run_set(deps, ctx)
                r = summarize(deps, new)
            except Exception as e:  # prototype rejected by the parser is a result
                r = dict(error=str(e)[:200])
            rows.append(dict(tag=tag, proto=proto, **r))
            print("VAR", tag, r.get("n_unlock"), r.get("error"), r.get("new_errors"))
        json.dump(rows, open(out + "/variants.json", "w"), indent=1, sort_keys=True)
    elif step == "full":
        tag, proto = VARIANTS[int(sys.argv[3])]
        ctx = d5.make_ctx("%s/ctx/full_%s.h" % (out, tag), [proto])
        allf = sorted(C["base"])
        new, _ = d5.run_set(allf, ctx)
        r = summarize(allf, new)
        base_clean = sum(1 for f in allf if C["base"][f]["clean"])
        r.update(tag=tag, proto=proto, n_clean_before=base_clean)
        json.dump(r, open(out + "/full_%s.json" % tag, "w"), indent=1, sort_keys=True)
        os.makedirs(out + "/c_" + tag, exist_ok=True)
        for f in r["newly_clean"]:
            open("%s/c_%s/%s.c" % (out, tag, f), "w", encoding="utf-8").write(new[f][1])
        print("FULL", tag, "before", base_clean, "after", r["n_clean_after"], "newly", r["newly_clean"], "errs", r["new_errors"])


main()
