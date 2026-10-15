#!/usr/bin/env python3
"""test_d12c.py -- run: python -I test_d12c.py (reads evidence next to this file's parent dir)."""
import json, os, random, re, sys
H = os.path.dirname(os.path.abspath(__file__)); E = H if os.path.exists(H + "/summary.json") else os.path.dirname(H)
S = json.load(open(E + "/summary.json")); S1 = json.load(open(E + "/step1.json")); SP = json.load(open(E + "/split.json"))
J = json.load(open(E + "/joint_arm.json"))
ok = []
def chk(n, c): ok.append(bool(c)); print(("PASS " if c else "FAIL ") + n)
chk("step1 reproduces: B1 unlock 12, L unlock 0, 91 dependents",
    S1["step1_B1"]["unlock"] == 12 and S1["step1_L"]["unlock"] == 0 and S1["n_c0004_dependents"] == 91 and S1["step1_reproduced"])
P = SP["population"]; r = random.Random("%s:P" % SP["seed"]); sh = P[:]; r.shuffle(sh)
chk("split seeded (20261015) and reproduces", SP["seed"] == 20261015 and sorted(sh[:len(P) // 2]) == SP["pack"] and sorted(sh[len(P) // 2:]) == SP["held_out"])
chk("split disjoint, excludes B1 targets", not set(SP["pack"]) & set(SP["held_out"]) and not set(P) & set(SP["b1_targets"]) and len(SP["pack"]) + len(SP["held_out"]) == len(P))
src = open(E + "/d12c.py").read() if os.path.exists(E + "/d12c.py") else ""
chk("split file is written before composition (source order)", src.index('"/split.json"') < src.index("joint arm"))
jdsrc = open(E + "/joint_delta.py").read()
fn = re.search(r"def select_bundles.*?\n\n\ndef ", jdsrc, re.S).group(0)
body = "\n".join(l.split("#")[0] for l in re.sub(r'""".*?"""', "", fn, flags=re.S).split("\n"))
chk("selector reads no degree field", not re.search(r"deg", body) and S["selector_reproduces_d12a_top10"])
chk("controls: noop byte-identical, unlock 0", S["control_noop"]["byte_identical"] and S["control_noop"]["unlock"] == 0)
mn = S["control_matched_null"]
chk("controls: matched null closes no target set, unlock 0 beyond L alone", isinstance(mn, dict) and mn["unlock"] == mn["vs_L_alone_in_same_universe"])
w = S["control_wrong_width"]
chk("controls: wrong width does not raise lint-clean", w["unlock_wrong"] <= w["unlock_right"] and w["held_wrong"] <= w["held_right"])
chk("every composed fact cites pack-half-only prototype (no diff vs full callsites)", S["pack_only_proto_differs_from_full"] == [])
chk("joint arm rows trace to curve", len(S["curve_heldout"]) == len([x for x in J if "error" not in x]))
sys.exit(0 if all(ok) else 1)

