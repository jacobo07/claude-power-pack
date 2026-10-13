#!/usr/bin/env python3
"""V-D3-* gates.  Usage: test_d3.py <d3_out>"""
import json, sys, os, collections

D = sys.argv[1]
fails = []


def chk(name, ok, info=""):
    print(("PASS " if ok else "FAIL ") + name + " " + str(info))
    if not ok:
        fails.append(name)


res = [json.loads(l) for l in open(os.path.join(D, "residuals.jsonl"))]
cen = json.load(open(os.path.join(D, "census.json")))
au = json.load(open(os.path.join(D, "autonomy.json")))
chk("V-D3-ROWS", len(res) == 1797 and len({r["fn"] for r in res}) == 1797, len(res))
# UNKNOWN never zero: no non-clean row may carry residual_size 0; None must be present for the code-less rows
chk("V-D3-UNKNOWN-NOT-ZERO", all(r["residual_size"] != 0 for r in res if not r["lint_clean"])
    and sum(1 for r in res if r["residual_size"] is None) > 0,
    "size None=%d" % sum(1 for r in res if r["residual_size"] is None))
expl = {r["fn"] for r in res if any(c.startswith("LINT_CLEAN_BUT_COMPILE_FAILED") for c in r["conflicts"])}
exc = [r["fn"] for r in res if r["lint_clean"] and r["distance"] > 1]
chk("V-D3-CLEAN-LE1", set(exc) <= expl, "exceptions=%s (each = measured W12 compile failure, explained)" % exc)
w = {r["fn"]: r for r in res if r["w12_verdict"]}
chk("V-D3-W12-22", len([f for f, r in w.items() if not r["w12_verdict"].startswith("EXCLUDED")]) == 22, len(w))
bad = []
for f, r in w.items():
    v = r["w12_verdict"]
    if v == "MATCH" and r["distance"] != 0:
        bad.append(f)
    elif v.startswith("PARTIAL") and r["distance"] != 1:
        bad.append(f)
    elif v.startswith("FAIL") and r["distance"] != 2:
        bad.append(f)
    elif v.startswith("EXCLUDED") and r["distance"] < 2:
        bad.append(f)
chk("V-D3-W12-AGREE", not bad, bad)
chk("V-D3-MATCH12", sum(1 for r in w.values() if r["w12_verdict"] == "MATCH") == 12)
hist = au["histogram"]
chk("V-D3-HIST-SUMS", sum(hist.values()) == 1797 and
    {int(k): v for k, v in collections.Counter(r["distance"] for r in res).items()} == {int(k): v for k, v in hist.items() if v})
other = cen["other_contradictions"]
chk("V-D3-CONTRADICTIONS", set(other) <= expl and all(len(v) == 1 for v in other.values()),
    "empty_residual_not_clean=%d unexplained_not_clean=%d other=%s" % (len(cen["empty_residual_not_clean"]), len(cen["unexplained_not_clean"]), list(other)))
chk("V-D3-RED", cen["red_control"]["verdict"] == "PROVEN", cen["red_control"])
c = au["cost"]
chk("V-D3-COST-NO-INVENTED-RATE", all(c[k]["rate"] == "UNKNOWN" for k in ("class3", "class4", "class5"))
    and c["priced_total_tokens_upper_bound"].startswith("UNKNOWN"))
print("TEST_D3 " + ("OK" if not fails else "FAILED " + ",".join(fails)))
sys.exit(1 if fails else 0)
