import collections, json, sqlite3
F = "/home/kobii/agora/factory"
c = sqlite3.connect(F + "/ledger/ledger.db")
census = json.load(open(F + "/research/census.json"))
RUN = {"wp-vs2": "typegen/wp-vs2-full", "tn-vs2": "typegen/tn-vs2-full", "mkw-base": "mkw-main-full", "wsr-base": "wsr-main-full"}
def bucket(p):
    for lo, hi in [(99, 100), (95, 99), (90, 95), (70, 90), (50, 70)]:
        if lo <= p < hi: return f"{lo}-{hi}"
    return "<50"
allok = True
for tag, run in RUN.items():
    per = {}
    for fid, state, comp, pct in c.execute("SELECT fid, state, compiles, pct FROM attempt WHERE run=?", (run,)):
        cur = per.get(fid)
        if state not in ("MATCH", "NEAR99", "NEAR95", "NEAR90", "COMPILES", "NO_COMPILE"):
            per[fid] = ("S", state); continue
        v = pct if comp else -1
        if cur is None or (cur[0] == "P" and v > cur[1]):
            per[fid] = ("P", v)
    got = collections.Counter()
    for k, v in per.values():
        got[v if k == "S" else "NO_COMPILE" if v < 0 else "100" if v == 100 else bucket(v)] += 1
    want = collections.Counter({k: v for k, v in census[tag]["functions"].items()})
    want = collections.Counter({("XF_ERROR" if k.startswith("XF_ERROR") else k): v for k, v in want.items()})
    ok = got == want
    allok &= ok
    print(tag, "AC(a)", "EQUAL" if ok else f"DIFF got-want={dict(got - want)} want-got={dict(want - got)}")
print("AC(a) PASS" if allok else "AC(a) FAIL")
