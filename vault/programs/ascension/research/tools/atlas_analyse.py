import json, collections
R = "/home/kobii/agora/factory/research"
rs = [json.loads(l) for l in open(R + "/nearmiss.jsonl")]
ok = [r for r in rs if "cls" in r]
print("rows", len(rs), "classified", len(ok), "errors", collections.Counter(r.get("err") for r in rs if "err" in r).most_common(3))
agree = sum(1 for r in ok if r.get("pct") is not None and abs(r["pct"] - r["sweep_pct"]) < 0.01)
print("recompile pct == sweep pct:", agree, "/", len(ok))
def band(p):
    for lo, hi in [(99, 100), (95, 99), (90, 95), (70, 90), (50, 70)]:
        if lo <= p < hi: return f"{lo}-{hi}"
CL = ["REGALLOC_ONLY", "SCHED_ONLY", "IMM_ONLY", "RELOC_ONLY", "ARGS_MIXED", "INSDEL", "OPC", "OPC+INSDEL", "NO_DIFF_REPORTED"]
print("\nclass share by band (all runs pooled, n per band):")
print("band     n  " + " ".join(f"{c[:9]:>9}" for c in CL))
for b in ["99-100", "95-99", "90-95", "70-90", "50-70"]:
    xs = [r for r in ok if band(r["sweep_pct"]) == b]
    c = collections.Counter(r["cls"] for r in xs)
    print(f"{b:7} {len(xs):4}  " + " ".join(f"{100*c[k]/max(1,len(xs)):8.0f}%" for k in CL))
print("\nclass by run (>=90 only):")
for run in sorted({r["run"] for r in ok}):
    xs = [r for r in ok if r["run"] == run and r["sweep_pct"] >= 90]
    print(run, len(xs), collections.Counter(r["cls"] for r in xs).most_common())
ins = [r for r in ok if r["cls"] in ("INSDEL", "OPC+INSDEL") and r["sweep_pct"] >= 90]
print("\n>=90 INSDEL len_delta (right-left instrs):", collections.Counter(max(-5, min(5, r["len_delta"])) for r in ins).most_common())
op = collections.Counter()
for r in ok:
    if r["sweep_pct"] >= 90:
        for k, v in r.get("detail", {}).items(): op[k] += v
print("top opcode substitutions / details (>=90):", op.most_common(25))
kk = collections.Counter()
for r in ok:
    if r["sweep_pct"] >= 90:
        for k, v in r.get("kinds", {}).items(): kk[k] += v
print("diff kinds total (>=90):", kk.most_common())
sz = collections.defaultdict(list)
for r in ok:
    sz[r["cls"]].append(r["size"])
print("median size by class:", {k: sorted(v)[len(v)//2] for k, v in sz.items()})
c = json.load(open(R + "/census.json"))
print("\nCENSUS (functions / bytes):")
for run, d in c.items():
    tb = sum(d["bytes"].values())
    print(run, {k: f"{d['functions'][k]}/{100*d['bytes'][k]/tb:.1f}%B" for k in sorted(d["functions"], key=lambda k: -d["bytes"][k])})
