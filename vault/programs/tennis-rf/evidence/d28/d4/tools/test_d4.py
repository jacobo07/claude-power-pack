#!/usr/bin/env python3
"""V-D4-* gates. Usage: test_d4.py <d3_out> <d4_out>   (expects <d4_out>_rerun from a second frontier.py run)"""
import json, sys, os
D3, D4 = sys.argv[1:3]
fails = []


def chk(n, ok, info=""):
    print(("PASS " if ok else "FAIL ") + n + " " + str(info))
    if not ok:
        fails.append(n)


fr = json.load(open(os.path.join(D4, "frontier.json")))
dom = json.load(open(os.path.join(D4, "dominators.json")))
cz = json.load(open(os.path.join(D4, "causal.json")))
rc = json.load(open(os.path.join(D4, "redcontrol.json")))
res = {}
for l in open(os.path.join(D3, "residuals.jsonl")):
    r = json.loads(l)
    res[r["fn"]] = r


def has(f, v):
    return any(x["id"] == v for x in res[f]["unresolved_vars"])


bad = [v["var"] for v in fr["vars"] if not v["residual_rows"] or not all(f in res and has(f, v["var"]) for f in v["residual_rows"])]
chk("V-D4-TRACE", not bad, "untraced=%s" % bad[:3])
cnt = {}
for r in res.values():
    if not r["lint_clean"]:
        for x in r["unresolved_vars"]:
            if x["type"] != "field_offset_untyped":
                cnt[x["id"]] = cnt.get(x["id"], 0) + 1
chk("V-D4-DIRECT-COUNT", all(v["blocked_direct"][1] == cnt[v["var"]] for v in fr["vars"]) and len(cnt) == len(fr["vars"]), len(cnt))
chk("V-D4-RANGE", all(v["blocked_direct"][0] <= v["blocked_direct"][1] and v["blocked_transitive"][0] <= v["blocked_transitive"][1]
                      and v["blocked"][0] <= v["blocked"][1] and v["score"][0] <= v["score"][1] for v in fr["vars"]))
chk("V-D4-TOP30", len(dom["top30"]) == 30 and all(d["evidence_rows"] for d in dom["top30"]))
chk("V-D4-RED-FALLS", rc["transitive_control"]["falls"], json.dumps(rc["transitive_control"]))
print("INFO score-level control (reported, direct part degree-invariant):", json.dumps(rc["falls"]))
chk("V-D4-CAUSAL", cz["n_classes"] == len(cz["rows"]) and all(r["functions"] for r in cz["rows"]))
chk("V-D4-REPRO", open(os.path.join(D4, "outputs.sha256")).read().strip() == open(os.path.join(D4 + "_rerun", "outputs.sha256")).read().strip())
print("TEST_D4 " + ("OK" if not fails else "FAIL " + ",".join(fails)))
sys.exit(1 if fails else 0)
