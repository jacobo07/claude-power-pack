#!/usr/bin/env python3
"""Near-miss atlas (pane 5a77ca0e, Owner 2026-11-20 "research atomically deeper"). Read-only on lanes; writes only
/home/kobii/agora/factory/research/. For a stratified sample of compiled-but-not-100% functions, recompile with the best
arm (same producer, prelude, flags and compiler as the sweep) and classify every objdiff instruction difference."""
import collections, concurrent.futures as cf, json, os, random, shutil, subprocess, sys, tempfile
sys.path.insert(0, "/home/kobii/missions/t1-campaign"); sys.path.insert(0, "/home/kobii/agora/factory"); sys.path.insert(0, "/home/kobii/agora/factory/typegen")
from modules.recon_fabric import cv1
import factory as B, factory_vs2 as V
F = "/home/kobii/agora/factory"; OUT = F + "/research"; os.makedirs(OUT, exist_ok=True)
RUNS = [("wp-vs2", F + "/typegen/wp-vs2-full", V), ("tn-vs2", F + "/typegen/tn-vs2-full", V),
        ("mkw-base", F + "/mkw-main-full", B), ("wsr-base", F + "/wsr-main-full", B)]
BANDS = [(99, 100), (95, 99), (90, 95), (70, 90), (50, 70)]
PER = int(sys.argv[1]) if len(sys.argv) > 1 else 60
random.seed(20261120)
TC0 = cv1.toolchain()


def band(p):
    for lo, hi in BANDS:
        if lo <= p < hi:
            return f"{lo}-{hi}"
    return None


def args_of(ins):
    return [p["arg"] for p in ins["instruction"]["parts"] if "arg" in p]


def classify(d, sym):
    L = next((s for s in d["left"]["symbols"] if s.get("name") == sym), None)
    R = next((s for s in d["right"]["symbols"] if s.get("name") == sym), None)
    if R is None and L is not None and isinstance(L.get("target_symbol"), int):  # objdiff pairs by index (C++ names)
        rs = d["right"]["symbols"]
        R = rs[L["target_symbol"]] if L["target_symbol"] < len(rs) else None
    if not L or not R:
        return None
    li, ri = L.get("instructions") or [], R.get("instructions") or []
    kinds = collections.Counter(); detail = collections.Counter()
    lf = [x["instruction"]["formatted"] for x in li if x.get("instruction")]
    rf = [x["instruction"]["formatted"] for x in ri if x.get("instruction")]
    for a, b in zip(li, ri):
        k = a.get("diff_kind") or b.get("diff_kind")
        if not k:
            continue
        if k == "DIFF_ARG_MISMATCH" and a.get("instruction") and b.get("instruction"):
            aa, ba = args_of(a), args_of(b)
            for x, y in zip(aa, ba):
                if x == y:
                    continue
                if "opaque" in x and "opaque" in y:
                    t = "FREG" if str(x["opaque"]).startswith("f") else "CR" if str(x["opaque"]).startswith("cr") else "REG"
                elif "reloc" in x or "reloc" in y:
                    t = "RELOC"
                elif "branch_dest" in x or "branch_dest" in y:
                    t = "BRANCH"
                else:
                    t = "IMM"
                kinds[t] += 1
            ma = a["instruction"]["parts"][0].get("opcode", {}).get("mnemonic")
            if ma in ("stwu",) or "r1)" in a["instruction"]["formatted"] and kinds.get("IMM"):
                detail["FRAME_OR_STACK"] += 1
        elif k in ("DIFF_INSERT", "DIFF_DELETE"):
            kinds["INSDEL"] += 1
        elif k in ("DIFF_OP_MISMATCH", "DIFF_REPLACE"):
            kinds["OPC"] += 1
            ma = a.get("instruction", {}).get("parts", [{}])[0].get("opcode", {}).get("mnemonic")
            mb = b.get("instruction", {}).get("parts", [{}])[0].get("opcode", {}).get("mnemonic")
            detail[f"{ma}->{mb}"] += 1
        else:
            kinds[k] += 1
    sched = len(lf) == len(rf) and sorted(lf) == sorted(rf) and lf != rf
    ks = set(kinds)
    if sched:
        cls = "SCHED_ONLY"
    elif not ks:
        cls = "NO_DIFF_REPORTED"
    elif ks <= {"REG", "FREG", "CR"}:
        cls = "REGALLOC_ONLY"
    elif ks <= {"IMM"}:
        cls = "IMM_ONLY"
    elif ks <= {"RELOC"}:
        cls = "RELOC_ONLY"
    elif ks <= {"REG", "FREG", "CR", "IMM", "RELOC", "BRANCH"}:
        cls = "ARGS_MIXED"
    elif "INSDEL" in ks and "OPC" not in ks:
        cls = "INSDEL"
    else:
        cls = "OPC" + ("+INSDEL" if "INSDEL" in ks else "")
    return {"cls": cls, "kinds": dict(kinds), "detail": dict(detail.most_common(4)), "n_left": len(lf), "n_right": len(rf),
            "len_delta": len(rf) - len(lf), "pct": L.get("match_percent")}


def one(job):
    tag, run, P, mw, row, arm = job
    w = tempfile.mkdtemp(prefix="atl-")
    try:
        src = P.prelude() + P.transform(open(f"{run}/m2c/c/{row['id'].replace(':', '_')}.c", errors="replace").read())
        open(w + "/fn.c", "w").write(src)
        tc = dict(TC0, mw=mw)
        r = subprocess.run([tc["wibo"], tc["mw"]] + P.ARMS["main"][arm].split() + ["-c", "fn.c", "-o", "fn.o"], cwd=w,
                           capture_output=True, timeout=90)
        if r.returncode != 0:
            return {"run": tag, "id": row["id"], "err": "recompile failed"}
        subprocess.run([tc["od"], "diff", "-1", row["obj"], "-2", w + "/fn.o", row["sym"], "-o", w + "/d.json", "--format", "json"],
                       capture_output=True, timeout=120)
        c = classify(json.load(open(w + "/d.json")), row["sym"])
        return {"run": tag, "id": row["id"], "sym": row["sym"], "size": row["size"], "arm": arm,
                "sweep_pct": row["arms"][arm]["pct"], **(c or {"err": "symbol missing"})}
    except Exception as e:  # noqa: BLE001 -- a probe failure is recorded per row, never silently dropped
        return {"run": tag, "id": row["id"], "err": f"{type(e).__name__}: {e}"}
    finally:
        shutil.rmtree(w, ignore_errors=True)


def main():
    jobs, census = [], {}
    for tag, run, P in RUNS:
        summ = json.load(open(run + "/summary.json"))
        mw = summ.get("compiler")
        buckets = collections.defaultdict(list); bytes_b = collections.Counter(); n_b = collections.Counter()
        for l in open(run + "/sweep.jsonl"):
            r = json.loads(l)
            st = r.get("state")
            if st != "OK":
                key = st
            elif not any(a.get("compiles") for a in r["arms"].values()):
                key = "NO_COMPILE"
            else:
                arm = max(r["arms"], key=lambda k: r["arms"][k].get("pct") or -1)
                p = r["arms"][arm]["pct"] or 0
                key = "100" if p == 100 else band(p) or "<50"
                if key not in ("100", "<50"):
                    buckets[key].append((r, arm))
            bytes_b[key] += r.get("size") or 0; n_b[key] += 1
        census[tag] = {"compiler": mw, "functions": dict(n_b), "bytes": dict(bytes_b)}
        for k, rows in buckets.items():
            for r, arm in random.sample(rows, min(PER, len(rows))):
                jobs.append((tag, run, P, mw, r, arm))
    json.dump(census, open(OUT + "/census.json", "w"), indent=1)
    print("jobs", len(jobs), flush=True)
    with open(OUT + "/nearmiss.jsonl", "w") as w, cf.ThreadPoolExecutor(10) as ex:
        for res in ex.map(one, jobs):
            w.write(json.dumps(res) + "\n")
    print("ATLAS_DONE", flush=True)


if __name__ == "__main__":
    main()
