#!/usr/bin/env python
"""Emit l1/GRAPH.md: every non-terminal row (work or wait) grouped into proposed work units with C(n)."""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

L1 = Path(__file__).resolve().parent.parent / "vault/specs/gsdx-factory/l1"
PROF = {"slim-t2": (19000, 1700), "top": (121000, 2000)}


def unit_of(o: dict):
    c, d = o["claimed"], (o.get("depends_on") or "")
    if c == "DETERMINISTIC":
        return ("U-ZERO", "ZERO_MODEL", "W4 reforecast / W8 closeout gates over receipts")
    if c == "DEFERRED_EXTERNAL":
        return ("U-DEFER", "none", "recorded, never funded")
    if c == "CHEAP_COGNITION":
        if "doctrine" in o.get("reason", ""):
            return ("U-DOCTRINE", "slim-t2", "write enforcing text/gates for unenforced doctrine rows")
        return ("U-KB-W8", "slim-t2", "W8 knowledge writer + PGO owner rows")
    if "INST2" in d and "W3" not in d:
        return ("U-W3", "slim-t2", "W3 S2/S3 residual: calls_unit, per-class g/r, R4 reconcile")
    if "W3" in d:
        return ("U-W6", "slim-t2", "W6 Part A A-G2..A-G5 after W3")
    if "W7" in d:
        return ("U-W7", "top", "W7 Part B coordination on GEX44")
    if "GEX44" in d:
        return ("U-W5", "top", "W5 port control plane to GEX44 (+UWCP evaluation)")
    if "CP50" in d:
        return ("U-CP50", "top", "transfer canaries after P3/CP50")
    return ("U-W7", "top", "W7 Part B coordination on GEX44")


def main() -> None:
    obs = json.loads((L1 / "obligations.json").read_text(encoding="utf-8"))["obligations"]
    g = defaultdict(list)
    meta = {}
    for o in obs:
        if o["claimed"] in ("DETERMINISTIC", "DEFERRED_EXTERNAL", "CHEAP_COGNITION", "WAIT_DEPENDENCY"):
            u = unit_of(o)
            g[u[0]].append(o["id"])
            meta[u[0]] = u
    rows = []
    for k, ids in sorted(g.items()):
        _, tier, cls = meta[k]
        if tier in PROF:
            F, gg = PROF[tier]
            n = max(1, math.ceil(len(ids) / (6 if tier == "slim-t2" else 4)))
            cost = n * F + gg * n * (n - 1) // 2
        else:
            n, cost = 0, 0
        dep = {"U-W3": "WAIT ce-lifecycle-v3 INST2", "U-W6": "WAIT W3", "U-W5": "WAIT GEX44 port prerequisites (DEPLOY rules)",
               "U-CP50": "WAIT CP50 criterion", "U-W7": "WAIT W5 + P3", "U-KB-W8": "after W7",
               "U-ZERO": "after receipts exist", "U-DOCTRINE": "none", "U-DEFER": "none"}[k]
        rows.append((k, len(ids), cls, tier, n, cost, dep, ids))
    L = ["# L1 GRAPH: proposed work units from non-terminal obligation rows", "",
         "Source: l1/obligations.json (595 rows; dispose gate exit 0). Only work or wait rows appear; terminal rows",
         "(ALREADY_SATISFIED, REUSE_EXISTING, MERGE, SUPERSEDED) are probed non-work. n is an ESTIMATE (rows/6 slim-t2, rows/4 top).",
         "C(n) = n*F + g*n*(n-1)/2; slim-t2 F=19,000 g=1,700; top F=121,000 g=2,000.", "",
         "| unit | rows | work class | tier | n | C(n) | dependency |", "|---|---|---|---|---|---|---|"]
    for k, nr, cls, tier, n, cost, dep, _ in rows:
        L.append(f"| {k} | {nr} | {cls} | {tier} | {n} | {cost:,} | {dep} |")
    L += ["", f"Total modelled: {sum(r[5] for r in rows):,} tokens (expected, before p_repair).", "", "## Rows per unit"]
    for k, nr, cls, tier, n, cost, dep, ids in rows:
        short = ", ".join(i[2:34] for i in ids[:14]) + (f", ... +{len(ids) - 14}" if len(ids) > 14 else "")
        L.append(f"- **{k}** ({nr}): {short}")
    (L1 / "GRAPH.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    top = sorted(rows, key=lambda r: -r[5])[:5]
    (L1 / "graph.summary.json").write_text(json.dumps(
        [{"unit": r[0], "rows": r[1], "tier": r[3], "n": r[4], "cost": r[5], "dependency": r[6]} for r in top], indent=1))
    print("GRAPH", len(L), "lines;", [(r[0], r[5]) for r in top])


if __name__ == "__main__":
    main()
