#!/usr/bin/env python3
"""D3 Semantic Residual Compiler v0.  residual(fn) = facts(fn) - certified(header facts, VALID idioms, motif cover, proof).
Usage: residual.py <M_out> <d3_out>      (M_out = .../out ; reads d28/d1d/*, d3_out/in/w12_records.jsonl)
UNKNOWN is never counted as zero: a function whose m2c did not produce code has residual size None."""
import json, sys, os, collections, random, math

# ---- distance-to-autonomy rule (the rule IS the distance() function) ----
# 0 lint-clean AND compile-verified (W12 verdict MATCH)
# 1 lint-clean (compile-verified but not MATCH, or not yet compiled) -- unless a measured compile failure exists (then 2)
# 2 not clean; every blocker key is a certified-fact gap: FIELD_UNTYPED, FIELD, SELF_SIG, QTYPE_LOCAL, HELPER
#   (a header/prototype/field-type fact, fillable by script from the asm; D2: the prototype/extern table is the lever)
# 3 not clean; some blocker is M2C:* (m2c cannot translate an instruction: needs a hypothesis / tool-side change)
# 4 not clean; some blocker is M2C_FAILED:* (no C emitted: control-flow recovery needs model reasoning)
# 5 not clean and no blocker explains it (UNKNOWN)
FACT_GAP = {"FIELD_UNTYPED", "FIELD", "SELF_SIG", "QTYPE_LOCAL", "HELPER"}
RULE = ("0=lint-clean+W12 MATCH; 1=lint-clean; 2=only fact-gap blockers (FIELD_UNTYPED,FIELD,SELF_SIG,QTYPE_LOCAL,HELPER) "
        "or clean+measured compile failure; 3=an M2C:* blocker; 4=an M2C_FAILED:* blocker; 5=not clean and unexplained")


def distance(clean, verdict, kinds, status):
    if clean:
        if verdict == "MATCH":
            return 0
        if verdict and verdict.startswith("FAIL"):
            return 2
        return 1
    if not kinds:
        return 5
    if "M2C_FAILED" in kinds:
        return 4
    if "M2C" in kinds:
        return 3
    if kinds <= FACT_GAP:
        return 2
    return 5


def load(M, D):
    d1 = os.path.join(M, "d28", "d1d")
    rows = [json.loads(l) for l in open(os.path.join(d1, "facts.jsonl"))]
    bl = json.load(open(os.path.join(d1, "blockers.json")))
    fac = json.load(open(os.path.join(d1, "factor.json")))
    hyp = json.load(open(os.path.join(d1, "hypotheses.json")))["hypotheses"]
    idi = json.load(open(os.path.join(d1, "idioms_status.json")))
    w12 = {}
    p = os.path.join(D, "in", "w12_records.jsonl")
    if os.path.exists(p):
        for l in open(p):
            r = json.loads(l)
            w12[r["fn"]] = r["verdict"]
    return rows, bl, fac, hyp, idi, w12


def build(rows, bl, fac, hyp, idi, w12, perm=None):
    keys_of = collections.defaultdict(list)
    sole = {}
    for b in bl["blockers"]:
        for f in b["functions"]:
            keys_of[f].append((b["key"], b["kind"]))
        for f in b["sole_blocker_functions"]:
            sole[f] = b["key"]
    if perm is not None:  # red control: permute fn -> blocker set across functions
        fns = [r["fn"] for r in rows]
        vals = [keys_of.get(f, []) for f in fns]
        perm.shuffle(vals)
        keys_of = {f: v for f, v in zip(fns, vals) if v}
    unt = bl["untyped_offsets"]
    hyp_keys = {h["key"] for h in hyp}
    valid_idioms = {k for k, v in idi.items() if v.get("status") == "VALID"}
    ff = fac["functions"]
    out = []
    for r in rows:
        fn = r["fn"]
        m = r["m2c_with_ctx"]
        clean = bool(m["clean"])
        ks = keys_of.get(fn, [])
        kinds = {k for _, k in ks}
        verdict = w12.get(fn)
        code_ok = m["status"] == "L1"
        uv = []
        for off in unt.get(fn, []):
            uv.append({"type": "field_offset_untyped", "id": off})
        for key, kd in ks:
            uv.append({"type": kd.lower(), "id": key})
        # size: None (UNKNOWN) when m2c emitted no code, or when not clean with nothing named
        if not code_ok:
            size = None
        elif clean:
            size = len(uv)
        elif uv:
            size = len(uv)
        else:
            size = None
        cert_idioms = sorted(set(r["idiom_hits"]) & valid_idioms)
        cov = ff.get(fn, {}).get("coverage", {})
        certified = {"header_facts": "tennis_context.h" if clean else None, "valid_idioms": cert_idioms,
                     "motif_cover_insns": cov.get("motif", 0), "size_insns": cov.get("size", r["size_insns"]),
                     "proof_family": ff.get(fn, {}).get("proof_family", "UNKNOWN")}
        conflicts = []
        if clean and ks:
            conflicts.append("CLEAN_BUT_BLOCKED: lint-clean yet blockers listed")
        if clean and m["lint_codes"]:
            conflicts.append("CLEAN_BUT_LINT_CODES")
        if (not clean) and code_ok and not ks and not m["lint_codes"] and not unt.get(fn):
            conflicts.append("EMPTY_RESIDUAL_NOT_CLEAN: no blocker, no lint code, no untyped offset, yet not lint-clean")
        if (not clean) and code_ok and not ks and (m["lint_codes"] or unt.get(fn)):
            conflicts.append("UNEXPLAINED_NOT_CLEAN: lint codes/untyped offsets present but no blocker key (blockers.json unexplained list)")
        if verdict == "MATCH" and not clean:
            conflicts.append("MATCH_BUT_NOT_CLEAN")
        if verdict and verdict.startswith("FAIL") and clean:
            conflicts.append("LINT_CLEAN_BUT_COMPILE_FAILED: lint checks types only; D2 admission_gap: NULL undeclared")
        ob = []
        for key, kd in ks:
            tail = key.split(":", 1)[-1]
            ob.append({"HELPER": "declare prototype for " + tail, "FIELD": "type global field " + tail,
                       "FIELD_UNTYPED": "type fields of own base at offsets " + ",".join(unt.get(fn, [])),
                       "SELF_SIG": "own signature fact", "QTYPE_LOCAL": "type unresolved local",
                       "M2C": "m2c hypothesis/tool-side: " + tail,
                       "M2C_FAILED": "control-flow recovery: " + tail}.get(kd, key))
        out.append({"fn": fn, "role": r["role"], "size_insns": r["size_insns"], "lint_clean": clean, "m2c_status": m["status"],
                    "w12_verdict": verdict, "residual_size": size, "unresolved_vars": uv, "n_blocker_keys": len(ks),
                    "blocker_kinds": sorted(kinds), "certified": certified, "conflicts": conflicts, "obligations": ob,
                    "expected_unlock": {"sole_blocker_key": sole.get(fn), "unverified": True,
                                        "has_hypothesis_entry": any(k in hyp_keys for k, _ in ks)},
                    "distance": distance(clean, verdict, kinds, m["status"])})
    return out


def main():
    M, D = sys.argv[1], sys.argv[2]
    rows, bl, fac, hyp, idi, w12 = load(M, D)
    res = build(rows, bl, fac, hyp, idi, w12)
    with open(os.path.join(D, "residuals.jsonl"), "w") as f:
        for r in res:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    cb = lambda rs: sum(1 for r in rs if any(c.startswith("CLEAN_BUT_BLOCKED") for c in r["conflicts"]))
    red = [cb(build(rows, bl, fac, hyp, idi, w12, perm=random.Random(s))) for s in range(20261101, 20261121)]
    real = cb(res)
    sizes = [r["residual_size"] for r in res]
    known = sorted(s for s in sizes if s is not None)
    census = {"n": len(res), "residual_size_unknown": sum(1 for s in sizes if s is None),
              "residual_size_hist": {str(k): v for k, v in sorted(collections.Counter(known).items())},
              "residual_size_quantiles": {str(q): known[int(q * (len(known) - 1))] for q in (0, .25, .5, .75, .9, 1)},
              "by_role_n": dict(collections.Counter(r["role"] for r in res)),
              "by_role_distance": {k: dict(sorted(collections.Counter(r["distance"] for r in res if r["role"] == k).items()))
                                   for k in sorted({r["role"] for r in res})},
              "empty_residual_not_clean": [r["fn"] for r in res if any(c.startswith("EMPTY_RESIDUAL_NOT_CLEAN") for c in r["conflicts"])],
              "unexplained_not_clean": [r["fn"] for r in res if any(c.startswith("UNEXPLAINED_NOT_CLEAN") for c in r["conflicts"])],
              "other_contradictions": {r["fn"]: r["conflicts"] for r in res
                                       if any(not c.startswith(("EMPTY_RESIDUAL", "UNEXPLAINED")) for c in r["conflicts"])},
              "red_control": {"metric": "lint-clean functions handed a foreign blocker set (CLEAN_BUT_BLOCKED)", "real": real,
                              "permuted_min": min(red), "permuted_mean": sum(red) / len(red), "n_perm": len(red),
                              "verdict": "PROVEN" if real == 0 and min(red) >= 100 else "INCONCLUSIVE"}}
    json.dump(census, open(os.path.join(D, "census.json"), "w"), indent=1)
    dh = collections.Counter(r["distance"] for r in res)
    n = {c: dh.get(c, 0) for c in range(6)}
    W12_TOK, W12_N = 3453372, 22
    ceil_fn = W12_TOK / W12_N
    ms, mt = 22, 12
    p = mt / ms
    z = 1.96
    den = 1 + z * z / ms
    ctr = (p + z * z / (2 * ms)) / den
    hw = z * math.sqrt(p * (1 - p) / ms + z * z / (4 * ms * ms)) / den
    n1 = n[1]
    cost = {
        "basis": "MEASURED only: W12 compile-verified rate 12/22 with model_calls 0 per function; D2 near-match compression 5 classes / 9 PARTIAL; "
                 "D2 shock: 101 functions flipped lint-clean by header with 0 model calls. W12 tokens: 3,453,372 processed / 52 calls for the WHOLE W12 "
                 "session (prep+build+send+judge of 22 fns) = a ceiling, NOT a per-function rate.",
        "class0": {"n": n[0], "work": 0},
        "class1": {"n": n1, "match_rate": "12/22", "wilson95": [round(ctr - hw, 3), round(ctr + hw, 3)],
                   "expected_match_range": [round(n1 * (ctr - hw), 1), round(n1 * (ctr + hw), 1)],
                   "expected_match_point": round(n1 * p, 1), "needs_followup_expected_point": round(n1 * (1 - p), 1),
                   "followup_tokens_per_fn": "UNKNOWN (no measured model-assisted near-match rate)",
                   "near_match_compression_measured": "5 classes / 9 PARTIAL"},
        "class2": {"n": n[2], "rate": "UNKNOWN (only the 101 shock flips are measured, on a different population)",
                   "tokens_per_fn": "UNKNOWN", "model_calls_per_fn_in_shock": 0},
        "class3": {"n": n[3], "rate": "UNKNOWN", "tokens_range": [0, "UNKNOWN"]},
        "class4": {"n": n[4], "rate": "UNKNOWN", "tokens_range": [0, "UNKNOWN"]},
        "class5": {"n": n[5], "rate": "UNKNOWN", "tokens_range": [0, "UNKNOWN"]},
        "ceiling_tokens_per_fn_not_a_rate": round(ceil_fn),
        "ceiling_total_if_every_nonzero_fn_cost_the_W12_aggregate": round(ceil_fn * (len(res) - n[0])),
        "priced_total_tokens_lower_bound": 0,
        "priced_total_tokens_upper_bound": "UNKNOWN (classes 2-5 have no measured per-function token rate)",
        "functions_priced": n[0] + n[1], "functions_unpriced": n[2] + n[3] + n[4] + n[5]}
    json.dump({"rule": RULE, "histogram": n, "n": len(res),
               "w12_check": {r["fn"]: {"verdict": r["w12_verdict"], "distance": r["distance"]} for r in res if r["w12_verdict"]},
               "cost": cost}, open(os.path.join(D, "autonomy.json"), "w"), indent=1)
    print("RESIDUAL OK rows=%d hist=%s size_unknown=%d red=%s" % (len(res), n, census["residual_size_unknown"], census["red_control"]["verdict"]))


if __name__ == "__main__":
    main()
