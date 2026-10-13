"""D2 step 2: near-match decomposition of the PARTIAL W12 functions from objdiff trims (deterministic, no model).
usage: near_match.py <units_dir> <records.jsonl> <out_json> [--selftest-seeds N]
Left = target (retail) side, right = our compiled output. SIZE_+-N = (our insns - target insns).
Class precedence (first rule that fires is the primary; every fired signal is also listed):
  FLAG/CODEGEN  an @sda21 form on one side vs @ha/@l on the other (sdata threshold) OR a target if/return compare
                (cmpwi;bne;li;blr) replaced by our cntlzw/srwi boolean idiom
  PTMF_R12      target computes a table entry address into r12 (mulli;add r12) that we lack
  POINTER_STRIDE the only divergence is an addi/lwz/stw immediate on identical registers (non-r1)
  SIZE_+-N      instruction count differs (after the rules above)
  REGALLOC      every divergence is a register-operand ARG_MISMATCH / extra mr
  OTHER
"""
import json, os, random, re, sys

def load(path):
    j = json.load(open(path, encoding="utf-8")); return j["left"]["symbols"][0], j["right"]["symbols"][0]

def rows(L, R):
    out = []
    n = max(len(L["instructions"]), len(R["instructions"]))
    for k in range(n):
        a = L["instructions"][k] if k < len(L["instructions"]) else {}
        b = R["instructions"][k] if k < len(R["instructions"]) else {}
        out.append((a.get("instruction", {}).get("formatted"), b.get("instruction", {}).get("formatted"),
                    a.get("diff_kind"), b.get("diff_kind")))
    return out

def norm(s):
    return re.sub(r"0x[0-9a-f]+$", "T", s) if s and s.split()[0] in ("b", "beq", "bne", "blt", "bgt", "ble", "bge") else s

def classify(rs):
    nL = sum(1 for r in rs if r[0]); nR = sum(1 for r in rs if r[1])
    div = [(i, r) for i, r in enumerate(rs) if r[2] or r[3] or (r[0] != r[1] and norm(r[0]) != norm(r[1]))]
    div = [(i, r) for i, r in div if r[2] or r[3]]
    if not div:
        return dict(primary="NONE", signals=[], n_target=nL, n_ours=nR, first_diverging=None, n_diverging=0)
    sig = []
    L = " ; ".join(r[0] for _, r in div if r[0]); Rr = " ; ".join(r[1] for _, r in div if r[1])
    ltxt = " ".join(r[0] for r in rs if r[0]); rtxt = " ".join(r[1] for r in rs if r[1])
    if ("@sda21" in ltxt) != ("@sda21" in rtxt):
        sig.append("FLAG/CODEGEN:sda21_vs_ha_l")
    if re.search(r"cmpwi.*bne.*li r3, 0x1.*blr", L.replace(" ; ", " ")) and "cntlzw" in Rr:
        sig.append("FLAG/CODEGEN:bool_idiom")
    if re.search(r"mulli r\d+, r\d+, 0x\w+", L) and re.search(r"add r12", L) and not re.search(r"add r12", Rr):
        sig.append("PTMF_R12")
    kinds = {r[2] for _, r in div} | {r[3] for _, r in div}
    if kinds == {"DIFF_ARG_MISMATCH"} and len(div) == 1:
        a, b = div[0][1][0], div[0][1][1]
        ma, mb = a.split(None, 1), b.split(None, 1)
        if ma[0] == mb[0] and ma[0] in ("addi", "lwz", "stw", "lha", "lhz") and "r1," not in ma[1] and "(r1)" not in ma[1]:
            ra = re.findall(r"r\d+", a); rb = re.findall(r"r\d+", b)
            if ra == rb:
                sig.append("POINTER_STRIDE")
    if nR != nL:
        sig.append("SIZE_%+d" % (nR - nL))
    only_reg = all((r[2] == "DIFF_ARG_MISMATCH" and r[3] == "DIFF_ARG_MISMATCH" and
                    bool(r[0]) and bool(r[1]) and r[0].split()[0] == r[1].split()[0]) or (r[2] == "DIFF_INSERT" and bool(r[1]) and r[1].startswith("mr ")) for _, r in div)
    if only_reg and not any(s.startswith(("FLAG", "PTMF", "POINTER")) for s in sig):
        sig.append("REGALLOC")
    prim = None
    for pref in ("FLAG/CODEGEN", "PTMF_R12", "POINTER_STRIDE", "SIZE_", "REGALLOC"):
        m = [s for s in sig if s.startswith(pref)]
        if m:
            prim = m[0].split(":")[0] if pref == "FLAG/CODEGEN" else m[0]; break
    first = div[0]
    return dict(primary=prim or "OTHER", signals=sig, n_target=nL, n_ours=nR, n_diverging=len(div),
                first_diverging=dict(index=first[0], target=first[1][0], ours=first[1][1]))

def allrows0(units, r):
    return rows(*load(os.path.join(units, "w10c2-tns_%s-%s-as_is.diff.json" % (r["fn"][3:], r["best_preset"]))))

def main():
    units, rec, out = sys.argv[1:4]
    recs = [json.loads(l) for l in open(rec, encoding="utf-8")]
    part = [r for r in recs if r["verdict"].startswith("PARTIAL")]
    res = {}
    for r in part:
        f = os.path.join(units, "w10c2-tns_%s-%s-as_is.diff.json" % (r["fn"][3:], r["best_preset"]))
        L, R = load(f); rs = rows(L, R)
        c = classify(rs); c["verdict"] = r["verdict"]; c["preset"] = r["best_preset"]; c["match_percent"] = L["match_percent"]
        res[r["fn"]] = c
    prim = [v["primary"] for v in res.values()]
    classes = sorted(set(prim))
    # positive control: an exact-match unit's diff must classify NONE
    ctl = {}
    for r in recs:
        if r["verdict"] == "MATCH" and any(u["preset"] == "O2" and u["exact"] for u in r["units"]):
            f = os.path.join(units, "w10c2-tns_%s-O2-as_is.diff.json" % r["fn"][3:])
            if os.path.exists(f):
                L, R = load(f); ctl[r["fn"]] = classify(rows(L, R))["primary"]
    # positive control: target vs target (identical sides, diff markers removed) must classify NONE
    for r in part:
        ctl["self:" + r["fn"]] = classify([(a[0], a[0], None, None) for a in allrows0(units, r)])["primary"]
    # red control: give every PARTIAL function another PARTIAL function's diff rows (random derangement, 20 seeds),
    # reclassify; the class must follow the rows, not the function id, so agreement with the real assignment must be low
    allrows = {r["fn"]: rows(*load(os.path.join(units, "w10c2-tns_%s-%s-as_is.diff.json" % (r["fn"][3:], r["best_preset"])))) for r in part}
    fns = [r["fn"] for r in part]; agree = []
    for seed in range(20261013, 20261033):
        rnd = random.Random(seed)
        while True:
            p = fns[:]; rnd.shuffle(p)
            if all(a != b for a, b in zip(fns, p)): break
        agree.append(sum(classify(allrows[p[i]])["primary"] == res[fns[i]]["primary"] for i in range(len(fns))) / len(fns))
    doc = dict(n_partial=len(part), per_function=res, primary_class_counts={c: prim.count(c) for c in classes},
               distinct_classes=len(classes), compression_ratio=len(classes) / len(part),
               sub_signal_counts={s: sum(s in v["signals"] for v in res.values()) for s in sorted({s for v in res.values() for s in v["signals"]})},
               positive_control_match_units=ctl, positive_control_pass=bool(ctl) and all(v == "NONE" for v in ctl.values()),
               red_control=dict(method="derange diff rows across the PARTIAL functions, 20 seeds, reclassify",
                                mean_agreement_with_real=sum(agree) / len(agree), max_agreement=max(agree),
                                pass_rule="mean agreement <= 0.5", passed=sum(agree) / len(agree) <= 0.5))
    json.dump(doc, open(out, "w"), indent=1, sort_keys=True)
    for k, v in res.items(): print(k, v["verdict"], v["primary"], v["signals"])
    print("classes", doc["primary_class_counts"], "ratio", doc["compression_ratio"], "ctl", ctl, "red", doc["red_control"]["mean_agreement_with_real"])

main()