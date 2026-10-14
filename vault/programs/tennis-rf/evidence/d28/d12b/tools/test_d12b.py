#!/usr/bin/env python3
"""test_d12b.py -- run: python -I test_d12b.py (from anywhere)."""
import json, os, random, sys
H = os.path.dirname(os.path.abspath(__file__)); E = os.path.dirname(H)
sc = json.load(open(E + "/scaling.json")); sp = json.load(open(E + "/split_lbl_80513E74.json"))
lad = json.load(open(E + "/arm2_e74_ladder.json")); arm = json.load(open(E + "/arm2_hdr_e74_v1.h.json"))
ok = []
def chk(name, c): ok.append(c); print(("PASS " if c else "FAIL ") + name)
# 1 draw reproduces from seed (same shuffle rule as arm2.py)
U = sp["dependents"]; r = random.Random("%s:%s" % (sp["seed"], sp["key"])); sh = U[:]; r.shuffle(sh)
chk("draw reproduces from seed", sorted(sh[:len(U) // 2]) == sp["pack"] and sorted(sh[len(U) // 2:]) == sp["held_out"])
chk("held-out disjoint from evidence pack", not set(sp["pack"]) & set(sp["held_out"]) and len(sp["pack"]) + len(sp["held_out"]) == len(U))
chk("every row cited by scaling.json exists", all(os.path.exists(os.path.join(E, v)) for v in sc["rows"].values()))
a = sc["arm2"]
chk("arm2 figures trace to ladder/compile rows",
    a["in_sample"]["vars_before"] == lad["in_sample"]["vars_before"] and a["held_out"]["vars_after"] == lad["held_out"]["vars_after"]
    and a["held_out"]["newly_lint_clean"] == len(arm["held_out"]["newly_clean"]) and a["in_sample"]["n"] == arm["in_sample"]["n"])
chk("held-out transfer percent traces", round(100 * (lad["held_out"]["vars_before"] - lad["held_out"]["vars_after"]) / lad["held_out"]["vars_before"], 1) == 5.0)
chk("naive baseline and factory forecast are separate fields", "naive_baseline" in sc and "factory_forecast" in sc and sc["naive_baseline"] is not sc["factory_forecast"])
chk("unmeasured values are UNPRICED, not filled", sc["naive_baseline"]["status"] == "UNPRICED" and sc["factory_forecast"]["status"] == "UNPRICED")
chk("donors consistent with job 4 NOT_SENT (no rate stated)", sc["job4"]["status"] == "NOT_SENT" and sc["job4"]["donors"] == "N/A" and sc["naive_baseline"]["tokens_per_verified_match"] is None)
sys.exit(0 if all(ok) else 1)