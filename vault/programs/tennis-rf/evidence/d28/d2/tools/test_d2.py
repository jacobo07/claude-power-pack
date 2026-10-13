"""V-D2-* checks for WU-D2. Laptop-light, stdlib only.  python test_d2.py   (exit 0 = all pass)"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import admission_rule  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (" -- " + detail if detail else ""))
    if not ok:
        fails.append(name)


J = lambda n: json.load(open(os.path.join(D, n), encoding="utf-8"))

c = J("causality.json")
check("V-D2-CAUSALITY-ROWS", c["n_rows"] == 22 and len(c["rows"]) == 22 and len({r["fn"] for r in c["rows"]}) == 22)
check("V-D2-CAUSALITY-TAGS", c["n_header_tags"] == 35, str(c["n_header_tags"]))
check("V-D2-CAUSALITY-USED", all(r["n_header_facts_used"] > 0 for r in c["rows"]))
check("V-D2-CAUSALITY-ANCHOR", all(r["used_tags"] or r["own_prototype"] or r["called_prototypes"] or r["externs"] or r["prelude_types"] for r in c["rows"]))

n = J("near_match.json")
check("V-D2-NEARMATCH-ROWS", n["n_partial"] == 9 and len(n["per_function"]) == 9)
check("V-D2-NEARMATCH-CLASS", all(v["primary"] for v in n["per_function"].values()))
check("V-D2-NEARMATCH-RATIO", abs(n["compression_ratio"] - n["distinct_classes"] / n["n_partial"]) < 1e-9
      and n["distinct_classes"] == len(n["primary_class_counts"]))
check("V-D2-NEARMATCH-REDCTRL", n["red_control"]["passed"] and n["positive_control_pass"])

a = J("shock_attribution.json")
rc = a["reconcile"]
check("V-D2-ATTR-SHOCK", a["shock"]["newly_clean"] == 276 - 175 == 101)
check("V-D2-ATTR-RECONCILE", rc["sum_check"] and rc["alone_sum"] + rc["shared_functions"] + rc["redundant_no_single_tag"]
      + rc["not_reproduced_with_full_header"] == 101, json.dumps(rc, sort_keys=True))
check("V-D2-ATTR-CREDIT", abs(rc["credit_total"] - (101 - rc["redundant_no_single_tag"] - rc["not_reproduced_with_full_header"])) < 1e-3)
check("V-D2-ATTR-TAGS", a["n_tags"] == 35 and len(a["per_fact"]) == 35)
check("V-D2-ATTR-REDCTRL", a["red_control"]["passed"] and len(a["red_control"]["fake_names"]) == 5)
r = J("shock_residual.json")
check("V-D2-ATTR-RESIDUAL-NAMED", r["n_redundant"] == rc["redundant_no_single_tag"] and r["n_clean_without_any_struct"] + r["n_needs_both"] == r["n_redundant"] and r["n_clean_without_any_prototype"] == 0,
      "clean_no_struct=%d clean_no_proto=%d needs_both=%d" % (r["n_clean_without_any_struct"], r["n_clean_without_any_prototype"], r["n_needs_both"]))

# admission rule: positive = 80252F34 composed unit, negatives = every other judged output's token pattern is checked on
# the same header; here: the header alone and a NULL-defined copy must be clean.
hdr = open(os.path.join(D, "tennis_context.h"), encoding="utf-8").read()
src = open(os.path.join(D, "main_80252F34.c"), encoding="utf-8").read()
check("V-D2-RULE-POSITIVE", admission_rule.lint_macros(hdr + "\n" + src) != [], str(admission_rule.lint_macros(hdr + "\n" + src)))
check("V-D2-RULE-HEADER-CLEAN", admission_rule.lint_macros(hdr) == [])
check("V-D2-RULE-NEAR-MISS", admission_rule.lint_macros(hdr + "\n#define NULL 0\n" + src) == [])
check("V-D2-RULE-COMMENT-BLIND", admission_rule.lint_macros(hdr + "\n/* NULL */ int x;") == [])
print("TEST_D2 %s" % ("OK" if not fails else "FAILED: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
