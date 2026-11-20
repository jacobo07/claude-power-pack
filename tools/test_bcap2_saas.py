#!/usr/bin/env python3
"""test_bcap2_saas.py -- BCAP2-06 style-3 gate (V-SAAS-*). Run: python3 tools/test_bcap2_saas.py ; exit 0 iff all pass.

Scope: style 3 (enterprise systematic) as a structural axis, option (b). Styles 1 and 2 are NOT covered (browser/access plane).
Poles: the doc's invariant claims are recomputed from the bench data (clean passes; seeded mutants of the data are caught);
the scorer family set is pinned unchanged (no F11)."""
from __future__ import annotations
import copy, json, re, statistics, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = F = 0
BENCH = ROOT / "vault/programs/bcap-2/saas-styles/ENTERPRISE_BENCH.json"
DOC = ROOT / "vault/knowledge_base/visual-patterns/enterprise-systematic-structural-axis.md"


def check(n, c, d=""):
    global P, F
    print(f"  [{'PASS' if c else 'FAIL'}] {n}: {d}")
    P, F = (P + 1, F) if c else (P, F + 1)


def invariants(bench):
    s = bench["systems"].values()
    g = lambda k: [x[k] for x in s if x[k] is not None]
    ink, text, rows = g("ink_contrast"), g("text_px"), g("row_px")
    return {
        "ink_min": min(ink), "ink_max": max(ink), "ink_ok": min(ink) >= 4.5,
        "text_range": (min(text), max(text)), "text_13_14": sum(1 for t in text if t in (13, 14)),
        "zebra_no": sum(1 for x in s if x["zebra"] is False),
        "weight_ge600": sum(1 for w in g("header_weight") if w >= 600),
        "row_min": min(rows), "row_max": max(rows), "row_median": statistics.median(rows),
        "div_min": min(g("divider_contrast")), "div_max": max(g("divider_contrast")),
    }


bench = json.loads(BENCH.read_text(encoding="utf-8"))
doc = DOC.read_text(encoding="utf-8")
inv = invariants(bench)
check("bench has 7 systems", len(bench["systems"]) == 7, str(len(bench["systems"])))
check("ink contrast 6.69-16.86 and above floor", (inv["ink_min"], inv["ink_max"]) == (6.69, 16.86) and inv["ink_ok"], str((inv["ink_min"], inv["ink_max"])))
check("body text 12-14px, 13-14 in 6/7", inv["text_range"] == (12, 14) and inv["text_13_14"] == 6, str(inv["text_range"]))
check("no zebra 5/7", inv["zebra_no"] == 5, str(inv["zebra_no"]))
check("header weight >=600 in 4/7", inv["weight_ge600"] == 4, str(inv["weight_ge600"]))
check("row height 32-55 median 45 (not an invariant)", (inv["row_min"], inv["row_max"], inv["row_median"]) == (32, 55, 45), str(inv["row_median"]))
check("divider 1.14-2.15", (inv["div_min"], inv["div_max"]) == (1.14, 2.15), str((inv["div_min"], inv["div_max"])))
for claim in ("6.69-16.86", "13-14 in 6/7", "32-55px, median 45", "1.14-2.15", "no zebra in 5/7", ">=600 in 4/7"):
    check(f"doc states bench figure {claim!r}", claim in doc)
# unmeasured stays unmeasured: Lightning header/divider are None, not 0
check("unmeasured is None not zero", bench["systems"]["Lightning"]["header_px"] is None and bench["systems"]["Lightning"]["divider_contrast"] is None)
# seeded mutants must be caught by the same recomputation
m = copy.deepcopy(bench); m["systems"]["Ant"]["ink_contrast"] = 3.0
check("MUTANT low-contrast system is caught", not invariants(m)["ink_ok"])
m = copy.deepcopy(bench); m["systems"]["Carbon"]["zebra"] = True
check("MUTANT extra zebra changes the recorded 5/7", invariants(m)["zebra_no"] != 5)
m = copy.deepcopy(bench); m["systems"]["Lightning"]["row_px"] = 99
check("MUTANT row height shifts range", invariants(m)["row_max"] != 55)
# decision pin: no F11, scorer unchanged
src = (ROOT / "modules/cdio/scorer.py").read_text(encoding="utf-8")
check("scorer KNOWN_FAMILIES still F1..F10", re.search(r'KNOWN_FAMILIES = \{f"F\{i\}" for i in range\(1, 11\)\}', src) is not None)
check("doc records not-F11 decision and unresolved styles 1/2", "not** a new aesthetic family F11" in doc and "Styles 1" in doc)
print(f"V-SAAS: {P} PASS / {F} FAIL")
sys.exit(1 if F else 0)
