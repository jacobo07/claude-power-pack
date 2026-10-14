"""D8v2: tournament.json from rejudge_l0.json (job 5) + the arm A history. usage: python tournament.py"""
import json, os
from math import sqrt
HERE = os.path.dirname(os.path.abspath(__file__))
rj = json.load(open(os.path.join(HERE, "rejudge_l0.json"), encoding="utf-8"))
for u in rj["units"]:
    u.pop("objdiff", None)   # was read from a key the receipt row does not carry; the ledger holds objdiff
json.dump(rj, open(os.path.join(HERE, "rejudge_l0.json"), "w", encoding="utf-8", newline="\n"), indent=1)


def wilson(k, n, z=1.959964):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 3), round(c + h, 3)]


def rate(k, n):
    return {"match": k, "n": n, "rate": round(k / n, 3), "wilson95": wilson(k, n)}


fns = {}
for u in rj["units"]:
    if u["producer"] != "d8v2_armB":
        continue
    f = fns.setdefault(u["entity"], {"insns": u["insns"], "presets": {}})
    f["presets"][u["preset"]] = u["class"]
o4p = [e for e, f in fns.items() if f["presets"].get("O4p") == "MATCH"]
anyp = [e for e, f in fns.items() if "MATCH" in f["presets"].values()]
nontriv = [e for e, f in fns.items() if f["insns"] >= 2]
donors = [u for u in rj["units"] if u["producer"] == "w10c_donor"]
D8V2_TOKENS = {"L26": 1101816, "L27": 1121020, "L28_at_handoff": 992574}   # goal-lineage, 2026-10-14
t = {
    "job_id": rj["job_id"], "judge": "oracle2 re-run on returned objects with the batch L0 (rejudge_l0.json); the "
    "ledger rows for this job read ORACLE_REFUSED because the profile L0 lacked the held-out rows (kept as written)",
    "draw": {"n": 40, "seed": 20261013, "arm_B_eligible_lint_clean": 14},
    "donors": {"match": sum(1 for d in donors if d["class"] == "MATCH"), "n": len(donors)},
    "arms": {
        "A": {"source": "history", "W12": rate(12, 22), "W10c_no_context": {"match": 0, "n": 12}},
        "B": {"fn_O4p": rate(len(o4p), len(fns)), "fn_any_preset": rate(len(anyp), len(fns)),
              "nontrivial_ge2_insns": rate(sum(1 for e in o4p if e in nontriv), len(nontriv)),
              "trivial_1_insn": rate(sum(1 for e in o4p if e not in nontriv), len(fns) - len(nontriv)),
              "per_drawn_fn": rate(len(o4p), 40), "model_calls_per_fn": 0,
              "misses": sorted(e for e in fns if e not in o4p),
              "per_fn": fns},
        "D": {"verdict": "EMPTY/INCONCLUSIVE", "why": "no motif->C emitter exists (factor/residual/frontier measure cover only)"},
        "E": {"verdict": "EMPTY/INCONCLUSIVE", "why": "D6 certified 0 facts; D4 ranking degree-driven"},
        "F": {"verdict": "= B", "why": "D contributes no candidates"},
    },
    "tokens": {"d8v2_leases": D8V2_TOKENS, "sum": sum(D8V2_TOKENS.values()),
               "per_O4p_match_lower_bound": round(sum(D8V2_TOKENS.values()) / max(1, len(o4p))),
               "note": "tooling/coordination spend of the unit, not generation: candidate sources are the reused "
                       "ctx_run1 m2c output (0 model calls); excludes the closing coordinator session"},
}
json.dump(t, open(os.path.join(HERE, "tournament.json"), "w", encoding="utf-8", newline="\n"), indent=1)
print(json.dumps({k: t["arms"]["B"][k] for k in ("fn_O4p", "nontrivial_ge2_insns", "trivial_1_insn", "per_drawn_fn",
                                                 "misses")}), t["donors"], t["tokens"]["per_O4p_match_lower_bound"])
