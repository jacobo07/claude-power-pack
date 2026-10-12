"""Lint the W11 m2c outputs with gex44/source_lint.py (unchanged): raw m2c text and the composed unit
(tennis_context.compose), per family/flags of the job-2 units for the same entity. Writes lint.json."""
import json, os, sys
G = sys.argv[1]; O = sys.argv[2]; JOB2 = sys.argv[3]
sys.path.insert(0, G)
import source_lint, tennis_context
fam = {}
for l in open(JOB2, encoding="utf-8"):
    r = json.loads(l); fam.setdefault(r["entity"].split(":")[1], set()).add((r.get("family"), r.get("flags")))
res = {}
for line in open(os.path.join(O, "results.tsv"), encoding="utf-8"):
    p = line.rstrip("\n").split("\t"); fid = p[0].split(":")[1]
    c = open(os.path.join(O, "c", p[0].replace(":", "_") + ".c"), encoding="utf-8").read()
    raw, comp = set(), set()
    for f, fl in sorted(fam.get(fid, {("C", "-lang c")}), key=str):
        raw.update(source_lint.lint_unit(c, f, fl)); comp.update(source_lint.lint_unit(tennis_context.compose(c), f, fl))
    res["fn_" + fid] = {"admit": p[1], "m2c_errors": p[3], "c_sha256": p[4], "lint_raw": sorted(raw), "lint_composed": sorted(comp),
                        "families": sorted({f for f, _ in fam.get(fid, set())}), "flag_sets": len(fam.get(fid, ()))}
json.dump(res, open(os.path.join(O, "lint.json"), "w"), indent=1, sort_keys=True)
for k, v in sorted(res.items()):
    print(k, v["admit"], "CLEAN" if not (v["lint_raw"] or v["lint_composed"]) else "DIRTY", v["lint_raw"], v["lint_composed"], v["flag_sets"])
