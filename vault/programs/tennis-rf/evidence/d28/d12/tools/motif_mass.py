"""D12a step 5: motif / VALID-idiom mass per class 2-5 (class = D3 'distance'). STRUCTURE, not cost.
python -I motif_mass.py <p1p2_tools_dir> <asm_dir> <residuals_v1.jsonl> <idioms_status.json> <out.json>"""
import collections, json, sys
sys.path.insert(0, sys.argv[1])
import asmlib as A, idioms as I
asm, res, ist, out = sys.argv[2:6]
valid = {k for k, v in json.load(open(ist)).items() if v["status"] == "VALID"}
P = A.parse_program(asm)
agg = collections.defaultdict(lambda: dict(fns=0, insns=0, motif_insns=0, idiom_insns=0, fns_with_valid_idiom=0,
        fns_not_in_asm=0, proof_family=collections.Counter(), idiom_insns_by=collections.Counter()))
for l in open(res):
    r = json.loads(l); d = r["distance"]
    if d not in (2, 3, 4, 5): continue
    a = agg[d]; a["fns"] += 1; c = r["certified"]
    a["insns"] += c["size_insns"] or 0; a["motif_insns"] += c["motif_cover_insns"] or 0
    a["proof_family"][c["proof_family"]] += 1
    ins = P.fns.get(r["fn"])
    if ins is None: a["fns_not_in_asm"] += 1; continue
    cov = set(); hit = False
    for k, sp in I.spans(ins).items():
        if k not in valid: continue
        hit = True
        for s in sp:
            n = set(s); cov |= n; a["idiom_insns_by"][k] += len(n)
    a["idiom_insns"] += len(cov); a["fns_with_valid_idiom"] += hit
res_out = {"label": "STRUCTURE, not cost", "valid_idioms": sorted(valid), "classes": {}}
tot = collections.Counter()
for d in sorted(agg):
    a = agg[d]; n = a["insns"]
    res_out["classes"][str(d)] = dict(fns=a["fns"], insns=n, motif_insns=a["motif_insns"], motif_fraction=a["motif_insns"] / n if n else None,
        valid_idiom_insns=a["idiom_insns"], valid_idiom_fraction=a["idiom_insns"] / n if n else None,
        fns_with_valid_idiom=a["fns_with_valid_idiom"], fns_not_in_asm=a["fns_not_in_asm"],
        proof_family=dict(a["proof_family"]), idiom_insns_by=dict(a["idiom_insns_by"]))
    for k in ("fns", "insns", "motif_insns", "idiom_insns", "fns_with_valid_idiom"): tot[k] += a[k]
res_out["all_2_5"] = dict(tot, motif_fraction=tot["motif_insns"] / tot["insns"], valid_idiom_fraction=tot["idiom_insns"] / tot["insns"])
json.dump(res_out, open(out, "w"), indent=1, sort_keys=True)
print(json.dumps(res_out["all_2_5"]))
