"""WU-D1d gates (V-D1D-*). exit 0 only if all pass.   python3 -I test_d1d.py <d1d_dir>"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
IDIOMS = ("switch_jump_table", "bool_from_compare", "float_to_int", "struct_copy", "vtable_call", "ptmf_call", "stack_guard_prolog")
def main(d):
    res = []
    def gate(n, ok, ev):
        res.append(ok); print("%s %s %s" % ("PASS" if ok else "FAIL", n, ev))
    py = sys.executable
    p = subprocess.run([py, "-I", os.path.join(HERE, "test_factor_partition.py")], capture_output=True, text=True)
    gate("V-D1D-FIXTURE-RED-GREEN", p.returncode == 0, p.stdout.strip().replace("\n", " | "))
    st = json.load(open(os.path.join(d, "idioms_status.json")))
    gate("V-D1D-IDIOM-STATUS", set(st) == set(IDIOMS) and all(v["status"] in ("VALID", "ABSTAIN") and v.get("why") for v in st.values()),
         {k: v["status"] for k, v in st.items()})
    txt = open(os.path.join(d, "idioms_test.txt")).read()
    bad = [n for n, v in st.items() if v["status"] == "VALID" and not (("idiom=%s label=POS" % n) in txt and ("idiom=%s label=NEG" % n) in txt)]
    gate("V-D1D-IDIOM-BOTH-OR-ABSTAIN", not bad, "valid without both fixtures: %s" % bad)
    facts = [json.loads(l) for l in open(os.path.join(d, "facts.d1d.jsonl"))]
    ab = {n for n, v in st.items() if v["status"] == "ABSTAIN"}
    leak = sum(1 for r in facts for k in r["idiom_hits"] if k in ab)
    gate("V-D1D-ABSTAIN-REMOVED", leak == 0, "abstained idiom hits left in downstream facts: %d" % leak)
    cs = json.load(open(os.path.join(d, "cluster_status.json")))
    g = cs["groupings"]
    gate("V-D1D-RED-CONTROL-PER-GROUPING", set(g) >= {"structural_family", "data_family", "data_family_anchored", "idiom_family", "motifs"}
         and all(v["status"] in ("VALID", "INCONCLUSIVE") and ("red_single_seed" in v or "red_pooled_block_sizes" in v) for v in g.values()), {k: v["status"] for k, v in g.items()})
    s = g["structural_family"]
    gate("V-D1D-PERMUTATIONS", cs["n_permutations"] == 20 and len(cs["seeds"]) == 20 and len(s["red_pooled_block_sizes"]["values"]) == 20,
         "seeds %s..%s real=%s red %s-%s/%s-%s" % (cs["seeds"][0], cs["seeds"][-1], s["real"], s["red_pooled_block_sizes"]["min"], s["red_pooled_block_sizes"]["max"], s["red_permuted_arity"]["min"], s["red_permuted_arity"]["max"]))
    gate("V-D1D-STRUCTURAL-REAL-REPRODUCES", s["real"] == s["p1p2_single_red"][2] == 926, "real=%s" % s["real"])
    # rerun reproduces
    import shutil, tempfile
    t = tempfile.mkdtemp(prefix="d1d_rerun_")
    for f in ("factor.json", "facts.jsonl", "idioms_test.txt"):
        shutil.copy(os.path.join(d, f), t)
    env = dict(os.environ, KSR_DECOMP_TOOLS=os.environ.get("KSR_DECOMP_TOOLS", "/opt/ksr-decomp"))
    r = subprocess.run([py, "-I", os.path.join(HERE, "d1d_run.py"), t], capture_output=True, text=True, env=env)
    same = r.returncode == 0 and all(open(os.path.join(t, f)).read() == open(os.path.join(d, f)).read() for f in ("idioms_status.json", "cluster_status.json"))
    gate("V-D1D-RERUN-REPRODUCES", same, "rc=%d %s" % (r.returncode, r.stderr[-200:]))
    print("D1D_GATES=%d/%d" % (sum(res), len(res)))
    return 0 if all(res) else 1
if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
