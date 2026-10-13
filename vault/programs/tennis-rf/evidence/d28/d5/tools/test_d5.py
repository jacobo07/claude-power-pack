#!/usr/bin/env python3
"""test_d5: V-D5-*.  /opt/ksr-decomp/venv/bin/python -I test_d5.py <d5_out>   (GEX44; imports d5.py from the same dir)"""
import hashlib, itertools, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import d5  # noqa: E402

out = sys.argv[1]
T = os.path.join(out, "test_tmp")
os.makedirs(T, exist_ok=True)
cu = json.load(open(out + "/causal_unlock.json"))
fails = []


def gate(name, ok, info=""):
    print(("PASS " if ok else "FAIL ") + name + " " + info)
    if not ok:
        fails.append(name)


C = d5.load()
cands = [r for r in cu["candidates"] if r["var"].startswith("HELPER:")]

# V-D5-DRAW: the draw reproduces from the seed
d0 = json.load(open(out + "/draw.json"))
d1 = d5.step_draw(T)
gate("V-D5-DRAW", d0 == json.load(open(T + "/draw.json")) and d0["seed"] == d5.SEED, "seed=%s picks=%d" % (d0["seed"], len(d0["picks"])))
gate("V-D5-DRAW-STRATA", len(d0["picks"]) == 11 and sum(1 for p in d0["picks"] if p["d4_rank"] <= 30) == 6, "6 top-30 + 5 below")

# V-D5-SUPPORT-REPRO: every SUPPORT reproduces on rerun (cror wave1 sha + each surviving hypothesis)
ok = True
n = 0
for r in cands:
    if r["verdict"] != "SUPPORT":
        continue
    F = r["var"].split(":", 1)[1]
    for hi, h in enumerate(r["hypotheses"]):
        if h.get("verdict") == "SUPPORT":
            os.makedirs(T + "/cands_ctx", exist_ok=True)
            m = d5.eval_delta(F, h["proto"], "rerun_%s_h%d" % (F, hi), T)
            n += 1
            ok &= (m["sha"] == h["measured"]["sha"] and m["n_unlock"] == h["measured"]["n_unlock"] and m["newly_clean"] == h["measured"]["newly_clean"])
gate("V-D5-SUPPORT-REPRO", ok and n > 0, "reran %d SUPPORT hypotheses" % n)

cr = cu["cror"]
deps = sorted(C["keyfns"][d5.CROR_KEY])
new, _ = d5.run_set(deps, d5.make_ctx(T + "/cror_re.h", []), d5.cror_rewrite)
sh = json.load(open(out + "/cror_wave1_sha.json"))
gate("V-D5-CROR-REPRO", all(sh[f]["sha"] == new[f][0]["c_sha256"] for f in deps) and
     sorted(f for f in deps if not C["base"][f]["clean"] and new[f][0]["clean"]) == sorted(cr["wave1"]["newly_clean"]), "67 dependents rerun")

# V-D5-CONTRADICTION: each CONTRADICTION carries its falsifying result (unlock 0 or a new error) for every admitted hypothesis
bad = []
for r in cu["candidates"]:
    if r["verdict"] != "CONTRADICTION":
        continue
    if r["var"] == d5.CROR_KEY:
        if not (cr["total_unlock"] == 0 or cr["wave1"]["new_errors"]):
            bad.append(r["var"])
        continue
    adm = [h for h in r["hypotheses"] if h["admitted"]]
    if not adm or not all(h["measured"]["n_unlock"] == 0 or h["measured"]["new_errors"] for h in adm):
        bad.append(r["var"])
gate("V-D5-CONTRADICTION", not bad, "bad=%s" % bad)

# control 1: a delta that contradicts the asm is rejected (callee fn_801CD7D0 reads r3,r4 at entry -> 0 params is a contradiction;
# void return contradicts callers reading r3 after the call)
F = "fn_801CD7D0"
ev = d5.callee_evidence(F)
rej0, _ = d5.asm_admits(F, dict(arity_gpr=0, nfpr=0, ret="s32"))
cs = d5.callsites("fn_800B4508")
rej1, _ = d5.asm_admits("fn_800B4508", dict(arity_gpr=1, nfpr=0, ret="void"))
good, _ = d5.asm_admits(F, dict(arity_gpr=ev["min_gpr"], nfpr=ev["min_fpr"], ret="s32"))
gate("V-D5-CONTROL-WRONG-DELTA", (not rej0) and (not rej1) and good, "callee min_gpr=%d; arity 0 rejected=%s; void-with-r3-read rejected=%s; consistent delta admitted=%s" % (ev["min_gpr"], not rej0, not rej1, good))

# control 2: a no-op delta yields unlock 0 and byte-identical output
F2 = cands[0]["var"].split(":", 1)[1]
m = d5.eval_delta(F2, "/* no-op delta */", "noop", T)
dd = sorted(C["keyfns"]["HELPER:" + F2])
base_sha = hashlib.sha256("".join(C["base"][f]["c_sha256"] for f in dd).encode()).hexdigest()
gate("V-D5-CONTROL-NOOP", m["n_unlock"] == 0 and not m["new_errors"] and m["sha"] == base_sha, "unlock=%d output_identical_to_baseline=%s" % (m["n_unlock"], m["sha"] == base_sha))

# cror rewrite is exact on total orders: truth table of (lt,gt,eq) one-hot compare results
tt = True
for state in ("lt", "gt", "eq"):
    lt, gt, eq = state == "lt", state == "gt", state == "eq"
    for bit, br in (("gt", "bne"), ("gt", "beq"), ("lt", "bne"), ("lt", "beq")):
        orig_eq = (gt if bit == "gt" else lt) or eq
        orig_taken = (not orig_eq) if br == "bne" else orig_eq
        new_taken = {"blt": lt, "bge": not lt, "bgt": gt, "ble": not gt}[d5.REWRITE[(bit, br)]]
        tt &= orig_taken == new_taken
gate("V-D5-CROR-EXACT-TOTAL-ORDER", tt, "12 cases")
blk = "/* 1 1  4C 41 13 82 */\tcror eq, gt, eq\n/* 2 2  40 82 00 44 */\tbne .L_x\n"
nb, st = d5.cror_rewrite(blk)
gate("V-D5-CROR-REWRITE-FIRES", "blt .L_x" in nb and st["n_rewritten"] == 1, nb.replace("\n", " | "))
nb2, st2 = d5.cror_rewrite("/* 1 1  4C 41 13 82 */\tcror eq, gt, eq\n/* 3 */\tmfcr r0\n")
gate("V-D5-CROR-BAILS", st2["n_rewritten"] == 0 and "cror" in nb2, "unsafe shape left untouched")

print("TEST_D5 %s" % ("PASS" if not fails else "FAIL " + ",".join(fails)))
sys.exit(0 if not fails else 1)
