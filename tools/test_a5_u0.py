#!/usr/bin/env python3
import os, re, sys, json, tempfile, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a5_ledger as L
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "vault/programs/cognitive-economy/a5")
DS = os.path.join(A, "inputs/dataset-dws-optimization-1.md")
disp = json.load(open(os.path.join(ROOT, "vault/config/a5-dispositions.json"), encoding="utf-8"))
ids = L.parse_dataset(DS)
res = []
def t(name, ok): res.append(ok); print(("ok  " if ok else "FAIL ") + name)

rows, problems = L.build(ids, disp)
t("no problems", not problems)
t("one row per id", sorted(r["id"] for r in rows) == sorted(i["id"] for i in ids) and len({r["id"] for r in rows}) == len(rows))
t("OMITTED count 0", sum(r["disposition"] == "OMITTED" for r in rows) == 0)
# independent count: numbered headings per part, via a separate scan
lines = open(DS, encoding="utf-8-sig").read().split("\n")
def cnt(lo, hi):
    n = 0
    for l in lines[lo:hi]:
        m = re.match(r"^(\d+)\. ", l)
        if m and int(m.group(1)) == n + 1: n += 1
    return n
c = (cnt(400, 1890), cnt(1890, 3910), cnt(3910, len(lines)))
t("per-part counts match dataset %s" % (c,), c == (64, 100, 100))
t("id count == headings + R-1", len(ids) == sum(c) + 1)
# bad disposition refused / control admitted
bad = copy.deepcopy(disp); bad["families"][0]["disposition"] = "MAYBE"
t("unknown disposition refused", bool(L.build(ids, bad)[1]))
good = copy.deepcopy(disp); good["families"][0]["disposition"] = "NEGATIVE_ROI"
t("control: valid disposition admitted", not L.build(ids, good)[1])
# mutant: drop one id from dispositions' view -> OMITTED appears
mut = [i for i in ids if i["id"] != "P2-50"]
r2, p2 = L.build(mut, disp)
t("mutant: dataset id missing -> problem (red)", bool(p2))
# mutant: drop id from disposition table -> OMITTED
m2 = copy.deepcopy(disp); m2["families"][0]["ids"] = m2["families"][0]["ids"].replace("P2:50-52", "P2:51-52")
r3, _ = L.build(ids, m2)
t("mutant: unclaimed id -> OMITTED", sum(r["disposition"] == "OMITTED" for r in r3) == 1)
# UNKNOWN needs missing
u = copy.deepcopy(disp); u["families"][0]["disposition"] = "UNKNOWN"; u["families"][0].pop("missing", None)
t("UNKNOWN without missing refused", bool(L.build(ids, u)[1]))
print("A5_U0_PASS=%d/%d" % (sum(res), len(res)))
sys.exit(0 if all(res) else 1)
