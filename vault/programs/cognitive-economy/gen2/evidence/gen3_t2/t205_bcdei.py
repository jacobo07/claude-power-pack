"""T2-0.5 items b,c,d,e,i + blind-sample prep (f). Zero-model. usage: python t205_bcdei.py CACHE OUTDIR SCRATCH
Reuses t2_instruments.py label functions (exec of its head) and the cached extraction; no re-extract."""
import sys, json, os, re, random, statistics as st, collections, glob
CACHE, D, SC = sys.argv[1], sys.argv[2], sys.argv[3]
src = open(os.path.join(D, "t2_instruments.py"), encoding="utf-8").read()
head = src.split("# ---------------------------------------------------------------- A+B+F")[0]
mid = src[src.index("def pclass"):src.index("def instr_GHI")]
sys.argv = ["x", CACHE, D]; g = {"__name__": "t2i"}; exec(compile(head, "t2i", "exec"), g); exec(compile(mid, "t2i_mid", "exec"), g)
WL = g["WL"]; NAMES = g["NAMES"]; EDIT = g["EDIT"]; META = g["META"]; proc = g["proc"]; scratch = g["scratch"]
TPC = 0.447; CLB = {"KSR": 67207, "InfinityOps": 120842, "KME": 0}
LT = {nm: g["label_wl"](WL[nm]) for nm in NAMES}
out = {"instrument": "T2-0.5 b,c,d,e,i", "workloads": {}}; R = random.Random(5)
def runs_of(lab):
    r = []; i = 0; n = len(lab)
    while i < n:
        if lab[i] == "CONTROL_LOOP":
            j = i
            while j + 1 < n and lab[j + 1] == "CONTROL_LOOP": j += 1
            r.append((i, j)); i = j + 1
        else: i += 1
    return r
def fps_of(c, edit_only=False):
    return {x["fp"] for x in c["tools"] if x["fp"] and not scratch(x["fp"]) and (not edit_only or x["n"] in EDIT)}
def nextd(lab, b):
    for k in range(b + 1, len(lab)):
        if lab[k] in ("DELTA", "REPAIR"): return k
    return None
def classify(calls, lab, a, b, mode="exact", thr=300, dmap=None):
    k = nextd(lab, b)
    rf = set().union(*[fps_of(calls[i]) for i in range(a, b + 1)])
    df = (dmap[k] if dmap is not None else fps_of(calls[k], True)) if k is not None else set()
    if mode == "exact": ev = bool(rf & df)
    else: ev = bool({os.path.dirname(p) for p in rf} & {os.path.dirname(p) for p in df})
    fe = k is not None and lab[k] == "REPAIR" and any(r["fail"] for i in range(a, b + 1) for r in calls[i]["res"])
    if ev or fe: return "EVIDENCE"
    return "INTERPRETATION" if sum(calls[i]["txt"] for i in range(a, b + 1)) >= thr else "SCHEDULING"
def split(lt, **kw):
    acc = {c: {"runs": 0, "calls": 0, "proc": 0} for c in ("EVIDENCE", "INTERPRETATION", "SCHEDULING")}; per = {}
    for t, lab in lt:
        L = []
        for a, b in runs_of(lab):
            cl = classify(t["calls"], lab, a, b, **kw); L.append((a, b, cl)); x = acc[cl]
            x["runs"] += 1; x["calls"] += b - a + 1; x["proc"] += sum(proc(t["calls"][i]) for i in range(a, b + 1))
        per[id(t)] = L
    return acc, per
def share(acc, key):
    tot = sum(v[key] for v in acc.values()) or 1
    return {k: round(100 * v[key] / tot, 2) for k, v in acc.items()}
def tl(n, fp=None, ro=True): return {"n": n, "fp": fp, "cmd": "", "wr": not ro, "tmp": False, "test": None, "git": None, "subj": None}
def cc(i, tools, txt=0): return {"ts": "2026-01-01T00:00:%02dZ" % i, "ctx": 1000, "out": 10, "tools": tools, "res": [{"id": "x", "size": 10, "fail": False}], "txt": txt}
pl = [cc(0, [tl("Edit", "z.py", False)]), cc(1, [tl("Read", "a.py")]), cc(2, [tl("Edit", "a.py", False)]), cc(3, [tl("Grep", "q.py")], 500), cc(4, [tl("Edit", "b.py", False)]),
      cc(5, [tl("Bash")]), cc(6, [tl("Edit", "c.py", False)])]
pl_lab = g["label_session"](pl); pr = runs_of(pl_lab); pl_cls = [classify(pl, pl_lab, a, b) for a, b in pr]
planted_ok = pl_cls == ["EVIDENCE", "INTERPRETATION", "SCHEDULING"]
dir_pl = [cc(0, [tl("Edit", "d/z.py", False)]), cc(1, [tl("Read", "d/a.py")]), cc(2, [tl("Edit", "d/b.py", False)])]
dl = g["label_session"](dir_pl); mut_changed = classify(dir_pl, dl, *runs_of(dl)[0]) != classify(dir_pl, dl, *runs_of(dl)[0], mode="dir")
for nm in NAMES:
    acc, per = split(LT[nm]); accd, _ = split(LT[nm], mode="dir"); acc0, _ = split(LT[nm], thr=0)
    base = sum(proc(c) for t, _ in LT[nm] for c in t["calls"]); nr = sum(v["runs"] for v in acc.values())
    nulls = []
    for _ in range(60):
        ac = {c: 0 for c in acc}
        for t, lab in LT[nm]:
            ks = [k for k, L in enumerate(lab) if L in ("DELTA", "REPAIR")]; fl = [fps_of(t["calls"][k], True) for k in ks]; R.shuffle(fl); dm = dict(zip(ks, fl))
            for a, b in runs_of(lab): ac[classify(t["calls"], lab, a, b, dmap=dm)] += 1
        nulls.append(100 * ac["EVIDENCE"] / nr)
    out["workloads"][nm] = {"c": {"runs": nr, "calls_pct": share(acc, "calls"), "proc_pct": share(acc, "proc"), "proc_pct_of_workload": {k: round(100 * v["proc"] / base, 2) for k, v in acc.items()},
                                  "evidence_runs_pct_real": round(100 * acc["EVIDENCE"]["runs"] / nr, 2), "evidence_runs_pct_shuffled_null": [round(st.mean(nulls), 2), round(st.pstdev(nulls), 2)],
                                  "mutant_dir_match_evidence_calls_pct": share(accd, "calls")["EVIDENCE"], "mutant_thr0_scheduling_calls_pct": share(acc0, "calls")["SCHEDULING"]}}
    out["workloads"][nm]["_per"] = per
def total_for(nm, P, T, W, N=10, S=10000):
    lt = LT[nm]; per = out["workloads"][nm]["_per"]; tot = 0
    for t, lab in lt:
        meta = t.get("stype") in META
        if P and meta: continue
        calls = t["calls"]; drop = set()
        if T:
            for a, b, cl in per[id(t)]:
                if cl == "SCHEDULING": drop |= set(range(a, b + 1))
                elif cl == "EVIDENCE": drop |= set(range(a + 1, b + 1))
        f0 = calls[0]["ctx"]; ctxs = []; outs = 0; rem = 0.0
        for i, c in enumerate(calls):
            if i in drop: rem += sum(r["size"] for r in c["res"]) * TPC; continue
            ctxs.append(max(min(c["ctx"], f0), c["ctx"] - rem)); outs += c["out"]
        if W:
            for i, cx in enumerate(ctxs):
                seg = (i // N) * N; base = ctxs[seg]; tot += cx if seg == 0 else min(cx, f0 + S + (cx - base))
                if i > 0 and i % N == 0: tot += S + f0
        else: tot += sum(ctxs)
        tot += outs
    if P: tot += sum(1 for t, _ in lt if t.get("stype") in META) * CLB[nm]
    return tot
COMBOS = {"historical": (0, 0, 0), "workers only": (0, 0, 1), "packets only": (1, 0, 0), "transaction only": (0, 1, 0), "workers+packets": (1, 0, 1), "packets+transaction": (1, 1, 0), "full": (1, 1, 1)}
for nm in NAMES:
    wl = out["workloads"][nm]; base = total_for(nm, 0, 0, 0); exp = WL[nm]["ctrl"]["expected_ctx"] + sum(c["out"] for t, _ in LT[nm] for c in t["calls"])
    res = {k: total_for(nm, *v) for k, v in COMBOS.items()}; res5 = {"workers S=5k": total_for(nm, 0, 0, 1, S=5000), "full S=5k": total_for(nm, 1, 1, 1, S=5000)}
    sv = {k: round(100 * (v - base) / base, 2) for k, v in res.items()}
    single = {k: res[k] - base for k in ("workers only", "packets only", "transaction only")}
    W_, P_, T_ = single["workers only"], single["packets only"], single["transaction only"]
    inter = {"workers x packets": (res["workers+packets"] - base) - (W_ + P_), "packets x transaction": (res["packets+transaction"] - base) - (P_ + T_),
             "full minus sum of singles": (res["full"] - base) - (W_ + P_ + T_)}
    prod = (res["workers only"] / base) * (res["packets only"] / base) * (res["transaction only"] / base)
    lt = LT[nm]; eps = g["episodes"](lt); fps = [g["fam"](e) for e in eps]; cnt = collections.Counter(fps); seen = set(); npr = 0
    for e, f in zip(eps, fps):
        if cnt[f] >= 2 and f in seen: npr += e["proc"]
        seen.add(f)
    r_np = npr / base; full = res["full"]
    rec = {str(rho): round(100 * (full * (1 - rho * r_np) - base) / base, 2) for rho in (0.25, 0.5, 1.0)}
    wl["d"] = {"base_check": [base, exp, base == exp], "processed": res, "pct_vs_historical": sv, "pct_S5k": {k: round(100 * (v - base) / base, 2) for k, v in res5.items()},
               "interaction_tokens": inter, "naive_product_pct": round(100 * (prod - 1), 2), "naive_sum_pct": round(100 * (W_ + P_ + T_) / base, 2)}
    wl["b"] = {"recurrence_nonfirst_share_of_base_pct": round(100 * r_np, 2), "sequence_full_then_recurrence_pct": rec, "full_pct": sv["full"],
               "naive_independent_product_with_rho0.5_pct": round(100 * (prod * (1 - 0.5 * r_np) - 1), 2)}
    mains = [t for t, _ in lt if t["main"]]; f_main = st.median([t["calls"][0]["ctx"] for t in mains]); grow = st.median([(t["calls"][-1]["ctx"] - t["calls"][0]["ctx"]) / max(1, len(t["calls"]) - 1) for t in mains if len(t["calls"]) > 5])
    wl["e_in"] = {"f_main": f_main, "growth_per_call": grow, "calls_per_delta": round(sum(len(x["calls"]) for x, _ in lt) / max(1, len(eps)), 2), "episodes": len(eps), "meta_transcripts": sum(1 for t, _ in lt if t.get("stype") in META)}
    wl.pop("_per")
out["controls"] = {"planted_classes": pl_cls, "planted_ok": planted_ok, "mutant_dir_match_changes_class": mut_changed, "base_checks": {nm: out["workloads"][nm]["d"]["base_check"] for nm in NAMES}}
ein = [out["workloads"][nm]["e_in"] for nm in NAMES]; f = st.median([x["f_main"] for x in ein]); gr = st.median([x["growth_per_call"] for x in ein]); cpe = {"LOW": min(x["calls_per_delta"] for x in ein), "CENTRAL": st.median([x["calls_per_delta"] for x in ein]), "HIGH": max(x["calls_per_delta"] for x in ein)}
EP = {"LOW": 3, "CENTRAL": 4, "HIGH": 6}; REV = {"LOW": 8, "CENTRAL": 12, "HIGH": 20}; NET = {"LOW": 0.64, "CENTRAL": 1.16, "HIGH": 2.41}; PTS = 4
def seg_cost(k): return k * f + gr * k * (k - 1) / 2
eb = {}
for lv in ("LOW", "CENTRAL", "HIGH"):
    k = round(cpe[lv] * EP[lv]); sub = PTS * seg_cost(k) + seg_cost(REV[lv]); calls = PTS * k + REV[lv]
    res_ = max(NET[lv] / 100 * sub, 2 * f); eb[lv] = {"calls_per_point": k, "points": PTS, "review_calls": REV[lv], "calls": calls, "subtotal": round(sub), "repair_reserve": round(res_), "total": round(sub + res_)}
eb["breaker_calls"] = int(-(-eb["CENTRAL"]["calls"] * 1.25 // 1)); eb["inputs"] = {"floor_main_median": f, "growth_per_call": gr, "calls_per_delta_episode": cpe}
out["e"] = eb
cut = "2026-10-05T12:34"; ic = {}
for nm in NAMES:
    dirs = sorted({os.path.dirname(t["f"]) for t in WL[nm]["transcripts"] if t["main"]}); n = 0; tot = 0
    for dd in dirs:
        for fp in glob.glob(os.path.join(dd, "*.jsonl")):
            tot += 1
            try:
                for line in open(fp, encoding="utf-8", errors="replace"):
                    m = re.search(r'"timestamp":"([^"]+)"', line)
                    if m: n += (m.group(1) >= cut); break
            except OSError: pass
    ic[nm] = {"dirs": len(dirs), "main_sessions_total": tot, "started_after_cutoff": n}
out["i"] = ic
json.dump(out, open(os.path.join(D, "out_T205_bcdei.json"), "w"), indent=1, default=str)
print(json.dumps({k: v for k, v in out.items() if k != "workloads"}, indent=1))
for nm in NAMES:
    w = out["workloads"][nm]; print(nm, "C", json.dumps(w["c"])); print(nm, "D", json.dumps(w["d"])); print(nm, "B", json.dumps(w["b"])); print(nm, "Ein", json.dumps(w["e_in"]))
smp = json.load(open(os.path.join(D, "t2_unclassified_sample_60.json")))["calls"]; ids = list(range(60)); dup = R.sample(ids, 15); items = [(i, i) for i in ids] + [(i, 100 + i) for i in dup]; R.shuffle(items)
json.dump({"order": items}, open(os.path.join(SC, "f_map.json"), "w"))
print("=====BLIND")
for pos, (i, _) in enumerate(items):
    c = smp[i]; tx = "; ".join("%s %s %s" % (x[0], os.path.basename(x[1] or "")[:34], (x[2] or "")[:60]) for x in c["tools"]) or "(no tool)"
    print("%02d %s %dk | %s" % (pos, c["stype"] or "main", c["ctx"] // 1000, tx))