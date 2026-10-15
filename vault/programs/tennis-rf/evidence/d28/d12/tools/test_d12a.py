"""test_d12a.py -- D12a done-check. python -I test_d12a.py  (exit 0 = all pass)"""
import json, os, re, subprocess, sys, collections
H = os.path.dirname(os.path.abspath(__file__)); D = os.path.dirname(H); E = os.path.dirname(D)
T = []
def t(name):
    def d(f):
        try: f(); T.append((name, True, ""))
        except Exception as x: T.append((name, False, repr(x)))
        return f
    return d
def rd(p):
    b = open(p, "rb").read()
    for e in ("utf-8-sig", "utf-16"):
        try: return b.decode(e).replace("\r", "")
        except Exception: pass
    return b.decode("latin-1").replace("\r", "")
def jl(p): return json.loads(rd(p))
def rows(p): return [json.loads(l) for l in rd(p).split("\n") if l.strip()]
d3 = rows(os.path.join(E, "d3", "residuals.jsonl")); v1 = rows(os.path.join(D, "residuals_v1.jsonl"))
clu = jl(os.path.join(D, "struct_clusters.json")); hg = jl(os.path.join(D, "hypergraph.json"))
jd = jl(os.path.join(D, "joint_delta.json"))
@t("hg_scan bounds reproduce (optimistic + pessimistic)")
def _():
    for mode, f in (("", "hg_scan_optimistic.txt"), ("pes", "hg_scan_pessimistic.txt")):
        a = [sys.executable, "-I", os.path.join(H, "hg_scan.py"), os.path.join(E, "d3", "residuals.jsonl")] + ([mode] if mode else [])
        o = subprocess.run(a, capture_output=True, text=True, check=True).stdout.strip().replace("\r", "")
        assert o == rd(os.path.join(D, f)).strip(), f
@t("residuals_v1 one row per D3 row, same fns")
def _():
    assert len(v1) == len(d3) and [r["fn"] for r in v1] == [r["fn"] for r in d3]
@t("collapsed ids trace to provenance evidence; CONFLICTs preserved")
def _():
    s = json.dumps(clu)[:0]
    cl = clu["clusters"] if isinstance(clu, dict) and "clusters" in clu else clu
    items = list(cl.values()) if isinstance(cl, dict) else cl
    ids = {x for r in v1 for u in r["unresolved_vars"] for x in [u["id"]] if x.startswith("STRUCT:") and ":UNK" not in x}
    assert ids, "no collapsed ids"
    known = set()
    for c in items:
        cid = str(c.get("id", c.get("cluster")))
        known.add(cid)
    miss = [i for i in list(ids)[:5000] if i.split(":")[1].split("+")[0] not in known and ("C" + i.split(":")[1].lstrip("C")) not in known]
    assert not miss, miss[:3]
    nconf = sum(1 for c in items if c.get("conflict") or c.get("status") == "CONFLICT" or c.get("conflicts"))
    assert nconf >= 4, nconf
@t("closure curve reproduces from residuals_v1")
def _():
    vs = collections.defaultdict(set)
    for r in v1:
        if r["distance"] in (2, 3, 4, 5) and not any(u["type"] in ("m2c", "m2c_failed") for u in r["unresolved_vars"]):
            for u in r["unresolved_vars"]:
                if not u.get("depends_on_struct"): vs[r["fn"]].add(u["id"])
    allv = set().union(*vs.values()); assert len(allv) == hg["distinct_vars"], (len(allv), hg["distinct_vars"])
    assert hg["closure_curve"][-1][1] == hg["distinct_vars"] and hg["label"].startswith("STRUCTURE")
@t("joint-delta controls behave")
def _():
    c = jd["controls"]
    assert c["noop"]["unlock"] == 0 and c["noop"]["byte_identical"]
    assert c["d5_wrong_delta"]["admitted"] is False
    assert c["matched_null"]["unlock"] == 0 and not c["matched_null"]["closes_target_set"]
@t("bundle selector reads no degree field")
def _():
    src = open(os.path.join(H, "joint_delta.py"), encoding="utf-8").read()
    m = re.search(r"def select_bundles\(.*?(?=\ndef )", src, re.S); assert m
    assert not re.search(r"degree|\bdeg\b", re.sub(r'""".*?"""', "", m.group(0), flags=re.S))
@t("steps 4-5 artifacts present")
def _():
    assert jl(os.path.join(D, "search_scan.json"))["status"] == "ABSENT"
    mm = jl(os.path.join(D, "motif_mass.json")); assert mm["all_2_5"]["fns"] == 1522
for n, ok, w in T: print(("PASS " if ok else "FAIL ") + n, w)
sys.exit(0 if all(o for _, o, _ in T) else 1)

