"""WU-D2 step 4 residual: what supports the 85 'redundant' newly-clean functions (no single struct tag flips them)?
    d2_resid.py <out_dir> <w12_records.jsonl>      (imports d2_run for the header model; m2c + lint only)
Group variants: NO_STRUCTS (drop every struct + everything naming one; untagged prototypes/externs stay),
NO_PROTOS (keep structs, drop every non-comment line = prototypes/externs)."""
import json, os, re, sys, collections, multiprocessing as mp
import d2_run as D

R, P = D.R, D.P
OUT = D.OUT


def build(variant):
    if variant == "NO_STRUCTS":
        removed = set(D.TAGS)
        keep = []
        for kind, text, dt in D.CHUNKS:
            if kind == "comment":
                keep.append((kind, text, dt)); continue
            if kind == "struct" or (set(re.findall(r"\b\w+\b", text)) & removed):
                continue
            keep.append((kind, text, dt))
        return D.render(keep)
    if variant == "NO_PROTOS":
        keep = [c for c in D.CHUNKS if c[0] in ("comment", "struct")]
        return D.render(keep)
    raise KeyError(variant)


def main():
    sa = json.load(open(OUT + "/shock_attribution.json"))
    red = sa["residual"]["redundant_no_single_tag"]
    facts = {json.loads(l)["fn"]: json.loads(l) for l in open(D.P1 + "/facts.jsonl")}
    text, tables = P.blocks(R.ASM)
    jobs = {}
    for fn in red:
        block, extra = text[fn], []
        for t in sorted(set(P.TABLE_REF.findall(block))):
            if t in tables:
                block, tab = P.adapt_table(block, tables[t], fn, int(facts[fn]["addr"], 16))
                extra.append(tab)
        jobs[fn] = (fn, facts[fn]["addr"], block, extra)
    variants = {v: build(v) for v in ("NO_STRUCTS", "NO_PROTOS")}
    paths = {}
    for v, txt in variants.items():
        paths[v] = "%s/ctx/ctx_%s.h" % (OUT, v)
        open(paths[v], "w", encoding="utf-8").write(txt)
    R.init(P.build_flags(False, paths["NO_STRUCTS"]), paths["NO_STRUCTS"], "ctx")
    for v in variants:
        R.G.update(flags=P.build_flags(False, paths[v]), context=paths[v], ctx_text=variants[v], arm="ctx")
        R.one(jobs[red[0]])
    tasks = [(v, paths[v], variants[v], jobs[fn]) for v in variants for fn in red]
    res = collections.defaultdict(dict)
    with mp.get_context("fork").Pool(D.JOBS, initializer=R.init,
                                     initargs=(P.build_flags(False, paths["NO_STRUCTS"]), paths["NO_STRUCTS"], "ctx")) as pool:
        for v, fn, clean, status, codes in pool.imap_unordered(D.eval_variant, tasks, chunksize=4):
            res[v][fn] = clean
    out = dict(n_redundant=len(red),
               clean_without_any_struct=sorted(f for f in red if res["NO_STRUCTS"][f]),
               clean_without_any_prototype=sorted(f for f in red if res["NO_PROTOS"][f]))
    out["n_clean_without_any_struct"] = len(out["clean_without_any_struct"])
    out["n_clean_without_any_prototype"] = len(out["clean_without_any_prototype"])
    both_dirty = sorted(f for f in red if not res["NO_STRUCTS"][f] and not res["NO_PROTOS"][f])
    out["needs_both_classes_or_a_named_group"] = both_dirty
    out["n_needs_both"] = len(both_dirty)
    json.dump(out, open(OUT + "/shock_residual.json", "w"), indent=1, sort_keys=True)
    print("RESID redundant=%d clean_no_struct=%d clean_no_proto=%d needs_both=%d" % (
        len(red), out["n_clean_without_any_struct"], out["n_clean_without_any_prototype"], len(both_dirty)))


if __name__ == "__main__":
    main()
