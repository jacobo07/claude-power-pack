"""WU-P1P2 gates (V-P1P2-*). Reads only the outputs in <p1p2_dir>; exit 0 only if every gate passes.

    python3 -I test_p1p2.py <p1p2_dir>
"""
import json
import os
import sys

IDIOMS = ("switch_jump_table", "bool_from_compare", "float_to_int", "struct_copy", "vtable_call", "ptmf_call",
          "stack_guard_prolog")


def main(d):
    res = []

    def gate(name, ok, ev):
        res.append(ok)
        print("%s %s %s" % ("PASS" if ok else "FAIL", name, ev))

    facts = [json.loads(l) for l in open(os.path.join(d, "facts.jsonl")) if l.strip()]
    gate("V-P1P2-FACTS-ROWS", len(facts) == 1797 and len({f["fn"] for f in facts}) == 1797, "rows=%d" % len(facts))

    summ = json.load(open(os.path.join(d, "extract_summary.json")))
    labelled = {f["role"] for f in facts if f["role"] != "UNKNOWN"}
    missing = sorted(r for r in labelled if r not in summ.get("role_rules", {}))
    gate("V-P1P2-ROLE-RULES", not missing, "labelled=%s missing_rule=%s" % (sorted(labelled), missing))

    ex = os.path.join(d, "idioms_test.txt")
    gate("V-P1P2-IDIOM-EXAMPLES", os.path.exists(ex),
         "idioms_test.txt %s (needs >=1 positive and >=1 negative asm example per idiom: %s)"
         % ("present" if os.path.exists(ex) else "ABSENT", ",".join(IDIOMS)))

    out = json.load(open(os.path.join(d, "factor.json")))
    v = out["summary"].get("verdict") or {}
    if not v:
        v = json.load(open(os.path.join(d, "factor.out"))).get("verdict", {}) if os.path.exists(os.path.join(d, "factor.out")) else {}
    for g in ("data_family", "structural_family", "motifs"):
        gate("V-P1P2-RED-%s" % g.upper(), v.get(g) == "PROVEN", "verdict=%s" % v.get(g))

    ks = json.load(open(os.path.join(d, "knowledge_shock.json")))
    rep = ks.get("reproduce", {})
    gate("V-P1P2-SHOCK-REPRODUCE", bool(rep) and all(rep.values()), json.dumps(rep, sort_keys=True))

    ids = open(os.path.join(d, "w12_clean_ids.txt")).read().split()
    by = {f["fn"]: f for f in facts}
    dirty = [i for i in ids if ((by.get(i) or {}).get("m2c_with_ctx") or {}).get("clean") is not True]
    all_clean = sum(1 for f in facts if (f.get("m2c_with_ctx") or {}).get("clean") is True)
    gate("V-P1P2-CLEAN-FIELD-LIVE", all_clean == ks.get("clean_after"),
         "facts clean=True count %d == knowledge_shock clean_after %s (the predicate can say yes)" % (all_clean, ks.get("clean_after")))
    gate("V-P1P2-W12-NO-REGRESSION", len(ids) == 22 and not dirty, "ids=%d not_clean=%s" % (len(ids), dirty))

    print("P1P2_GATES=%d/%d" % (sum(res), len(res)))
    return 0 if all(res) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
