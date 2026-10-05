"""Gen3 T2-0 instruments A+B+F, E, C, D, G, H, I (zero-model). usage: python t2_instruments.py CACHE.json OUTDIR
Every instrument: machine-readable JSON, positive control, negative/shuffled control, one mutant that must change the verdict.
Unit: processed = ctx + out (ctx = input + cache_creation + cache_read), dedup by message id (done in t2_extract.py)."""
import json, os, re, sys, random, hashlib, statistics as st, collections
CACHE, OUT = sys.argv[1], sys.argv[2]
cache = json.load(open(CACHE))
TMP_RE = re.compile(r"(\\temp\\|/tmp/|/tmp\b|scratchpad|\$env:temp|\\appdata\\local\\temp|\.tmp\b)", re.I)
EDIT = {"Edit", "Write", "NotebookEdit", "MultiEdit"}; SHELL = {"Bash", "PowerShell"}
READ_ONLY = {"Read", "Grep", "Glob", "ToolSearch", "WebFetch", "WebSearch", "TaskOutput", "TaskList", "TaskGet", "LSP", "Monitor"}
REPAIR_SUBJ = re.compile(r"\b(fix|fixes|fixed|revert|hotfix|repair|amend|correct)\b", re.I)
META = {"gsd-planner", "gsd-phase-researcher", "gsd-plan-checker"}        # k4 line 9
TOK_PER_CHAR_TR = 0.447                                                       # gen3_t1/regress_out.txt: tool_result 0.447 tok/char
RNG = random.Random(7)
def scratch(fp): return bool(fp and TMP_RE.search(fp))
def t_delta(t, bw):
    if t["n"] in EDIT: return bool(t["fp"]) and not scratch(t["fp"])
    if t["git"] == "commit": return True
    return bool(bw and t["n"] in SHELL and t["wr"] and not t["tmp"] and not t["git"])
def t_ro(t):
    if t["n"] in READ_ONLY: return True
    return t["n"] in SHELL and not t["wr"] and not t["git"]
def proc(c): return c["ctx"] + c["out"]
def other_sub(c):
    if not c["tools"]: return "notool"
    ns = {t["n"] for t in c["tools"]}
    if ns & {"Agent", "Task"}: return "dispatch"
    if ns & {"TaskCreate", "TaskUpdate", "TodoWrite", "AskUserQuestion", "Skill"}: return "taskmgmt"
    return "other_tool"
def label_session(calls, bw=True, prec="RDC", strict=True, win=10, first_commit=None):
    n = len(calls); isd = [False] * n; isr = [False] * n; last_edit = {}; fails = [any(r["fail"] for r in c["res"]) for c in calls]
    for i, c in enumerate(calls):
        tl = c["tools"]
        single_fail = len(tl) == 1 and tl[0]["n"] in EDIT and fails[i]
        d = (not single_fail) and any(t_delta(t, bw) for t in tl); r = False
        for t in tl:
            if t["git"] == "revert": r = True
            if d and t["git"] == "commit" and t["subj"] and REPAIR_SUBJ.search(t["subj"]) and first_commit and c["ts"] > first_commit: r = True
            if d and t["n"] in EDIT and t["fp"] and not scratch(t["fp"]):
                j = last_edit.get(t["fp"])
                if j is not None and i - j <= win and any(fails[k] for k in range(j, i)): r = True
        for t in tl:
            if t["n"] in EDIT and t["fp"] and not scratch(t["fp"]): last_edit[t["fp"]] = i
        isd[i], isr[i] = d, r
    pre = [False] * n; suf = [False] * n; a = False
    for i in range(n): pre[i] = a; a = a or isd[i] or isr[i]
    a = False
    for i in range(n - 1, -1, -1): suf[i] = a; a = a or isd[i] or isr[i]
    lab = []
    for i, c in enumerate(calls):
        if prec == "RDC":
            L = "REPAIR" if isr[i] else "DELTA" if isd[i] else None
        else:
            L = "DELTA" if isd[i] else "REPAIR" if isr[i] else None
        if L is None:
            if c["tools"] and all(t_ro(t) for t in c["tools"]) and (not strict or (pre[i] and suf[i])): L = "CONTROL_LOOP"
            else: L = "OTHER"
        lab.append(L)
    return lab
def first_commit_ts(wl):
    ts = [c["ts"] for t in wl["transcripts"] for c in t["calls"] for x in c["tools"] if x["git"] == "commit"]
    return min(ts) if ts else None
def label_wl(wl, sessions=None, **o):
    fc = first_commit_ts(wl); S = sessions if sessions is not None else wl["transcripts"]
    return [(t, label_session(t["calls"], first_commit=fc, **o)) for t in S]
def metrics(lt):
    calls = sum(len(t["calls"]) for t, _ in lt); P = collections.Counter(); N = collections.Counter(); runs = 0
    for t, lab in lt:
        prev = None
        for c, L in zip(t["calls"], lab):
            P[L] += proc(c); N[L] += 1
            if L == "CONTROL_LOOP" and prev != "CONTROL_LOOP": runs += 1
            prev = L
    tp = sum(P.values()); D = N["DELTA"]; ctx = sum(c["ctx"] for t, _ in lt for c in t["calls"])
    return {"calls": calls, "ctx_sum": ctx, "processed": tp, "counts": dict(N), "processed_by_label": dict(P),
            "call_share_pct": {k: round(100 * v / calls, 3) for k, v in N.items()}, "proc_share_pct": {k: round(100 * v / tp, 3) for k, v in P.items()},
            "share_sum_calls_pct": round(100 * sum(N.values()) / calls, 6), "share_sum_proc_pct": round(100 * sum(P.values()) / tp, 6),
            "control_loop_runs": runs, "SDD": D / calls, "ATCR": calls / (D + runs) if D + runs else None,
            "repair_amplification": (P["REPAIR"] / P["DELTA"]) if P["DELTA"] else None}
def jd(name, obj):
    p = os.path.join(OUT, name); open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(obj, indent=1, default=str)); return p
WL = cache; NAMES = ["KSR", "InfinityOps", "KME"]
SUM = []
def S(x): SUM.append(x); print(x)
# ---------------------------------------------------------------- A+B+F
def mk(n, fp=None, cmd="", wr=False, tmp=False, test=None, git=None, subj=None): return {"n": n, "fp": fp, "cmd": cmd, "wr": wr, "tmp": tmp, "test": test, "git": git, "subj": subj}
def mkc(tools, ts="2026-01-01T00:00:0%dZ", i=0, fail=False): return {"ts": ts % i if "%d" in ts else ts, "ctx": 1000, "out": 10, "tools": tools, "res": [{"id": "x", "size": 10, "fail": fail}], "txt": 0}
def synth():
    seq = [([mk("Read", "a.py")], 0, False),                                   # OTHER (before first delta, strict)
           ([mk("Bash", cmd="git commit -m 'feat: a'", git="commit", subj="feat: a")], 1, False),   # DELTA (first commit)
           ([mk("Edit", "src/a.py")], 2, False),                               # DELTA
           ([mk("Bash", cmd="pytest", test="pytest")], 3, True),               # CONTROL_LOOP (failed test run between deltas)
           ([mk("Edit", "src/a.py")], 4, False),                               # REPAIR (re-touch after failure)
           ([mk("Read", "b.py")], 5, False), ([mk("Grep")], 6, False),         # CONTROL_LOOP x2
           ([mk("Write", "docs/decision.md")], 7, False),                      # DELTA
           ([mk("Write", "C:\\Users\\x\\AppData\\Local\\Temp\\s.txt")], 8, False),   # scratch write: not delta -> OTHER
           ([mk("Bash", cmd="git commit -m 'fix: a'", git="commit", subj="fix: a")], 9, False),   # REPAIR (fix subject, prior commit)
           ([], 10, False)]                                                    # OTHER (no tool)
    exp = ["OTHER", "DELTA", "DELTA", "CONTROL_LOOP", "REPAIR", "CONTROL_LOOP", "CONTROL_LOOP", "DELTA", "OTHER", "REPAIR", "OTHER"]
    return [mkc(t, i=i, fail=f) for t, i, f in seq], exp
def instr_ABF():
    res = {"instrument": "A+B+F", "definition": "one label per call, REPAIR > DELTA > CONTROL_LOOP > OTHER; strict CONTROL_LOOP = read-only calls with a DELTA/REPAIR call earlier AND later in the session; wide = relax the boundary (sensitivity)", "workloads": {}}
    wl_out = {}; null_rows = {}
    for nm in NAMES:
        wl = WL[nm]; lt = label_wl(wl); m = metrics(lt); lw = metrics(label_wl(wl, strict=False))
        base = wl["ctrl"]["expected_ctx"]
        m["control_ctx_equals_base"] = (m["ctx_sum"] == base); m["wide_sensitivity"] = {k: lw[k] for k in ("call_share_pct", "proc_share_pct", "SDD", "ATCR", "repair_amplification", "control_loop_runs")}
        oth = m["call_share_pct"].get("OTHER", 0); m["unclassifiable_other_pct"] = oth
        sub = collections.Counter(other_sub(c) for t, lab in lt for c, L in zip(t["calls"], lab) if L == "OTHER"); m["other_subtypes"] = dict(sub)
        # stratified 60-call sample (OTHER calls) by (is_subagent, subtype)
        sample = []
        if oth > 5.0:
            pools = collections.defaultdict(list)
            for t, lab in lt:
                for ci, (c, L) in enumerate(zip(t["calls"], lab)):
                    if L == "OTHER": pools[(("sub" if not t["main"] else "main"), other_sub(c))].append({"workload": nm, "file": t["f"], "call_index": ci, "ts": c["ts"], "stype": t["stype"], "ctx": c["ctx"], "tools": [(x["n"], x["fp"], x["cmd"][:80]) for x in c["tools"]]})
            tot = sum(len(v) for v in pools.values()); per = 60 // 3
            for k, v in sorted(pools.items()):
                q = max(1, round(per * len(v) / tot)) if tot else 0; RNG.shuffle(v); sample += v[:q]
            sample = sample[:per]
        m["sample_for_human_judgment"] = sample
        res["workloads"][nm] = m; wl_out[nm] = lt
        # shuffled null: permute tools/res among calls within each session (ctx/out fixed)
        reps = []
        for _ in range(30):
            sh = []
            for t in wl["transcripts"]:
                cs = t["calls"]; idx = list(range(len(cs))); RNG.shuffle(idx)
                sh.append({"calls": [dict(cs[i], tools=cs[idx[i]]["tools"], res=cs[idx[i]]["res"]) for i in range(len(cs))], "main": t["main"], "f": t["f"], "stype": t["stype"]})
            mm = metrics(label_wl(wl, sessions=sh)); reps.append(mm)
        def ms(k): v = [r[k] for r in reps if r[k] is not None]; return [st.mean(v), st.pstdev(v)]
        null_rows[nm] = {"SDD": ms("SDD"), "ATCR": ms("ATCR"), "repair_share_pct": [st.mean([r["proc_share_pct"].get("REPAIR", 0) for r in reps]), st.pstdev([r["proc_share_pct"].get("REPAIR", 0) for r in reps])],
                         "control_runs": ms("control_loop_runs")}
    # controls
    calls, exp = synth(); got = label_session(calls, first_commit="2026-01-01T00:00:01Z")
    pos = {"expected": exp, "got": got, "pass": got == exp}
    allread = [mkc([mk("Read", "x")], i=i) for i in range(6)]; ar = label_session(allread)
    neg1 = {"all_read_session_labels": ar, "pass": "DELTA" not in ar and "REPAIR" not in ar}
    sens = {nm: {"real_ATCR": res["workloads"][nm]["ATCR"], "shuffled_ATCR_mean_sd": null_rows[nm]["ATCR"], "real_control_runs": res["workloads"][nm]["control_loop_runs"], "shuffled_control_runs": null_rows[nm]["control_runs"],
                 "real_repair_proc_pct": res["workloads"][nm]["proc_share_pct"].get("REPAIR", 0), "shuffled_repair_proc_pct": null_rows[nm]["repair_share_pct"], "shuffled_SDD": null_rows[nm]["SDD"], "real_SDD": res["workloads"][nm]["SDD"]} for nm in NAMES}
    for nm in NAMES:
        r = sens[nm]; r["order_signal_ATCR_z"] = (r["real_ATCR"] - r["shuffled_ATCR_mean_sd"][0]) / (r["shuffled_ATCR_mean_sd"][1] or 1e-9)
    mut = {}
    for nm in NAMES:
        mA = metrics(label_wl(WL[nm], bw=False)); mB = metrics(label_wl(WL[nm], prec="DRC"))
        r0 = res["workloads"][nm]
        mut[nm] = {"mutant_no_bash_write": {"SDD": mA["SDD"], "base_SDD": r0["SDD"]}, "mutant_DELTA_over_REPAIR": {"repair_proc_pct": mB["proc_share_pct"].get("REPAIR", 0), "base_repair_proc_pct": r0["proc_share_pct"].get("REPAIR", 0), "amp": mB["repair_amplification"], "base_amp": r0["repair_amplification"]}}
    changed = any(abs(v["mutant_no_bash_write"]["SDD"] - v["mutant_no_bash_write"]["base_SDD"]) > 0.005 for v in mut.values()) and any(abs(v["mutant_DELTA_over_REPAIR"]["repair_proc_pct"] - v["mutant_DELTA_over_REPAIR"]["base_repair_proc_pct"]) > 0.05 for v in mut.values())
    res["controls"] = {"positive_synthetic": pos, "negative_all_read": neg1, "shuffled_null": sens,
                       "ctx_equals_base": {nm: res["workloads"][nm]["control_ctx_equals_base"] for nm in NAMES}, "shares_sum_100": {nm: (res["workloads"][nm]["share_sum_calls_pct"] == 100 and abs(res["workloads"][nm]["share_sum_proc_pct"] - 100) < 1e-6) for nm in NAMES},
                       "mutants": mut, "mutant_verdict_changed": changed}
    res["controls"]["all_pass"] = bool(pos["pass"] and neg1["pass"] and changed and all(res["controls"]["ctx_equals_base"].values()) and all(res["controls"]["shares_sum_100"].values()))
    jd("out_A_B_F.json", res)
    for nm in NAMES:
        m = res["workloads"][nm]
        S(f"[A/B/F] {nm}: calls={m['calls']} ctx={m['ctx_sum']:,} base_ok={m['control_ctx_equals_base']} calls%={m['call_share_pct']} proc%={m['proc_share_pct']} SDD={m['SDD']:.4f} ATCR={m['ATCR']:.3f} runs={m['control_loop_runs']} repairAmp={m['repair_amplification']} OTHER%={m['unclassifiable_other_pct']:.1f} wide:{m['wide_sensitivity']['call_share_pct']}")
    S(f"[A/B/F] controls: pos={pos['pass']} neg={neg1['pass']} mutant_changed={changed} all_pass={res['controls']['all_pass']}")
    return wl_out, res
LAB, RES_ABF = instr_ABF()
# ---------------------------------------------------------------- E JOIN TAX
def join_tax(wl, rate=TOK_PER_CHAR_TR, comp=True, ar=None):
    by = {t["f"]: t for t in wl["transcripts"]}; rows = []
    for a in (ar if ar is not None else wl["agent_results"]):
        t = by.get(a["main_f"])
        if not t: continue
        c = [x["ctx"] for x in t["calls"]]; later = 0
        for j in range(a["after"] + 1, len(c)):
            if comp and j > 0 and c[j] < 0.7 * c[j - 1]: break
            later += 1
        rows.append({"agentId": a["agentId"], "stype": a["stype"], "chars": a["chars"], "later_calls": later, "tax_tokens": a["chars"] * rate * later})
    return rows
def instr_E():
    res = {"instrument": "E", "definition": "overlay (not a share): result tokens (chars*0.447 tok/char) x later parent calls carrying it; carry stops at a context drop >30% (compaction/clear)", "workloads": {}}
    for nm in NAMES:
        wl = WL[nm]; base = sum(proc(c) for t in wl["transcripts"] for c in t["calls"]); rows = join_tax(wl); tax = sum(r["tax_tokens"] for r in rows)
        bys = collections.defaultdict(float)
        for r in rows: bys[r["stype"]] += r["tax_tokens"]
        res["workloads"][nm] = {"base_processed": base, "results": len(rows), "result_tokens": sum(r["chars"] for r in rows) * TOK_PER_CHAR_TR, "join_tax_tokens": tax, "join_tax_pct_of_base": 100 * tax / base,
                                "mean_later_calls": st.mean([r["later_calls"] for r in rows]) if rows else 0, "by_stype_tokens": dict(bys), "rate_0.32_pct": 100 * sum(r["chars"] * 0.32 * r["later_calls"] for r in rows) / base,
                                "no_compaction_mutant_pct": 100 * sum(r["tax_tokens"] for r in join_tax(wl, comp=False)) / base}
    syn = {"transcripts": [{"f": "s", "calls": [{"ctx": 1000 + i} for i in range(12)]}], "agent_results": [{"main_f": "s", "agentId": "a", "stype": "x", "chars": 1000, "after": 1}]}
    pos = join_tax(syn)[0]["tax_tokens"]; exp = 1000 * TOK_PER_CHAR_TR * 10
    syn2 = {"transcripts": syn["transcripts"], "agent_results": [dict(syn["agent_results"][0], after=11)]}; neg = join_tax(syn2)[0]["tax_tokens"]
    syn3 = {"transcripts": [{"f": "s", "calls": [{"ctx": 1000}] * 4 + [{"ctx": 100}] * 6}], "agent_results": [{"main_f": "s", "agentId": "a", "stype": "x", "chars": 1000, "after": 1}]}
    c_on, c_off = join_tax(syn3)[0]["tax_tokens"], join_tax(syn3, comp=False)[0]["tax_tokens"]
    shuf = {}
    for nm in NAMES:
        wl = WL[nm]; ar = [dict(a) for a in wl["agent_results"]]; pos_ = [a["after"] for a in ar]; RNG.shuffle(pos_)
        for a, p in zip(ar, pos_): a["after"] = p     # positions shuffled across results (mixes main sessions too: invalid ones dropped by length)
        shuf[nm] = sum(r["tax_tokens"] for r in join_tax(wl, ar=ar))
    res["controls"] = {"positive_synthetic": {"expected": exp, "got": pos, "pass": abs(pos - exp) < 1e-6}, "negative_result_at_last_call": {"got": neg, "pass": neg == 0}, "shuffled_positions_tokens": shuf,
                       "mutant_no_compaction_stop_synthetic": {"with_stop": c_on, "without": c_off, "verdict_changed": c_off != c_on}}
    res["controls"]["all_pass"] = res["controls"]["positive_synthetic"]["pass"] and res["controls"]["negative_result_at_last_call"]["pass"] and c_off != c_on
    jd("out_E.json", res)
    for nm in NAMES:
        w = res["workloads"][nm]; S(f"[E] {nm}: results={w['results']} result_tokens={w['result_tokens']:,.0f} join_tax={w['join_tax_tokens']:,.0f} = {w['join_tax_pct_of_base']:.2f}% of base (0.32 tok/char: {w['rate_0.32_pct']:.2f}%; no-compaction-stop: {w['no_compaction_mutant_pct']:.2f}%) mean_later={w['mean_later_calls']:.1f}")
    S(f"[E] controls all_pass={res['controls']['all_pass']}")
    return res
RES_E = instr_E()
# ---------------------------------------------------------------- C WORKER LIFETIME
def grid_total(TT, N, S_, floor, rehyd=True, k4=False):
    tot = 0
    for t in TT:
        c = [x["ctx"] for x in t["calls"]]; f0 = c[0] if k4 else floor
        for i in range(len(c)):
            if N is None: tot += c[i]; continue
            seg = (i // N) * N; base = c[seg]
            tot += c[i] if seg == 0 else min(c[i], f0 + S_ + (c[i] - base))
            if rehyd and not k4 and i > 0 and i % N == 0: tot += S_ + floor
    return tot + sum(x["out"] for t in TT for x in t["calls"])
NS = [1, 3, 5, 10, 20, 40, None]; SS = [5000, 10000, 30000, 60000]
def instr_C():
    res = {"instrument": "C", "definition": "restart every N calls with handoff S; per-call floor = median first-call ctx over the workload's transcripts; ctx'=min(ctx, floor+S+growth since restart); rehydration charge (S+floor) per restart", "workloads": {}}
    for nm in NAMES:
        TT = WL[nm]["transcripts"]; fl = [t["calls"][0]["ctx"] for t in TT]; floor = st.median(fl); base = grid_total(TT, None, 0, floor)
        grid = {}; grid_nr = {}
        for N in NS:
            for S_ in SS:
                grid[f"N={N or 'inf'},S={S_//1000}k"] = 100 * (grid_total(TT, N, S_, floor) - base) / base
                grid_nr[f"N={N or 'inf'},S={S_//1000}k"] = 100 * (grid_total(TT, N, S_, floor, rehyd=False) - base) / base
        best = min(grid, key=grid.get); best_nr = min(grid_nr, key=grid_nr.get)
        k4g = {f"N={N},S={S_//1000}k": 100 * (grid_total(TT, N, S_, floor, k4=True) - base) / base for N in (10, 20, 40) for S_ in (10000, 30000)}
        res["workloads"][nm] = {"floor_median_ctx": floor, "floor_sample_size": len(fl), "floor_min_max": [min(fl), max(fl)], "base_processed": base, "grid_pct_vs_base_with_rehydration": grid, "grid_pct_no_rehydration": grid_nr,
                                "argmin_with_rehydration": [best, grid[best]], "argmin_no_rehydration_mutant": [best_nr, grid_nr[best_nr]], "k4d_formula_reproduced_pct": k4g, "k4d_best": min(k4g.items(), key=lambda x: x[1])}
    # controls
    pos = {}
    TT = WL["KSR"]["transcripts"]; b = grid_total(TT, None, 0, 0); v = grid_total(TT, 20, 10000, 0, k4=True)
    pos["k4_formula_KSR_N20_S10k_processed"] = v; pos["k4_published"] = 171950000; pos["pass"] = abs(v - 171.95e6) < 0.02e6
    neg = {nm: grid_total(WL[nm]["transcripts"], None, 0, 0) == sum(proc(c) for t in WL[nm]["transcripts"] for c in t["calls"]) for nm in NAMES}
    neg2 = {nm: abs(grid_total(WL[nm]["transcripts"], 5, 10**9, res["workloads"][nm]["floor_median_ctx"], rehyd=False) - res["workloads"][nm]["base_processed"]) == 0 for nm in NAMES}
    chg = any(res["workloads"][nm]["argmin_with_rehydration"][0] != res["workloads"][nm]["argmin_no_rehydration_mutant"][0] for nm in NAMES)
    res["controls"] = {"positive_k4_reproduction": pos, "negative_N_inf_is_base": neg, "negative_huge_S_clamps_to_base": neg2, "mutant_drop_rehydration_changes_argmin": chg}
    res["controls"]["all_pass"] = bool(pos["pass"] and all(neg.values()) and all(neg2.values()) and chg)
    jd("out_C.json", res)
    for nm in NAMES:
        w = res["workloads"][nm]; S(f"[C] {nm}: floor median={w['floor_median_ctx']:,.0f} n={w['floor_sample_size']} (min {w['floor_min_max'][0]:,} max {w['floor_min_max'][1]:,}); argmin(with rehyd)={w['argmin_with_rehydration'][0]} {w['argmin_with_rehydration'][1]:+.1f}%; without rehyd={w['argmin_no_rehydration_mutant'][0]} {w['argmin_no_rehydration_mutant'][1]:+.1f}%; k4(d) best={w['k4d_best'][0]} {w['k4d_best'][1]:+.1f}%; N=20,S=10k {w['grid_pct_vs_base_with_rehydration']['N=20,S=10k']:+.1f}%; N=inf S any 0")
    S(f"[C] controls all_pass={res['controls']['all_pass']} (k4 repro {pos['k4_formula_KSR_N20_S10k_processed']:,} vs 171.95M)")
    return res
RES_C = instr_C()
# ---------------------------------------------------------------- D PACKET COMPILE KILL-TEST
def words(s): return re.findall(r"\S+", s)
def ngr(w, n): return {hash(tuple(w[i:i + n])) for i in range(len(w) - n + 1)}
def ttext(c):
    if isinstance(c, str): return c
    if isinstance(c, list): return " ".join(ttext(x) for x in c)
    if isinstance(c, dict): return c["text"] if isinstance(c.get("text"), str) else ttext(c.get("content"))
    return ""
def run_events(f):
    ev = []; seen = set()
    for line in open(f, encoding="utf-8", errors="replace"):
        try: o = json.loads(line)
        except ValueError: continue
        ty = o.get("type"); m = o.get("message") or {}; ct = m.get("content")
        if ty == "user":
            if isinstance(ct, str): ev.append(("in", ct))
            elif isinstance(ct, list):
                for b in ct:
                    if isinstance(b, dict) and b.get("type") == "tool_result": ev.append(("in", ttext(b.get("content"))))
                    elif isinstance(b, dict) and b.get("type") == "text": ev.append(("in", b.get("text") or ""))
        elif ty == "assistant" and isinstance(ct, list):
            for b in ct:
                if not isinstance(b, dict): continue
                txt = None
                if b.get("type") == "text": txt = b.get("text")
                elif b.get("type") == "tool_use" and isinstance(b.get("input"), dict):
                    i = b["input"]; txt = i.get("content") if b.get("name") == "Write" else i.get("new_string") if b.get("name") == "Edit" else None
                    if b.get("name") == "MultiEdit": txt = " ".join(e.get("new_string", "") for e in i.get("edits", []) if isinstance(e, dict))
                if txt and isinstance(txt, str):
                    k = (m.get("id"), hash(txt))
                    if k not in seen: seen.add(k); ev.append(("out", txt))
    return ev
def overlap(ev, n, swap_inputs=None):
    inp = set(); tot = ov = 0; in_chars = 0
    if swap_inputs is not None:
        for kind, t in swap_inputs:
            if kind == "in": inp |= ngr(words(t), n)
    for kind, t in ev:
        w = words(t)
        if kind == "in":
            in_chars += len(t)
            if swap_inputs is None: inp |= ngr(w, n)
        else:
            g = [hash(tuple(w[i:i + n])) for i in range(len(w) - n + 1)]; tot += len(g); ov += sum(1 for x in g if x in inp)
    return tot, ov, in_chars
def instr_D(thr=0.5):
    res = {"instrument": "D", "definition": "per planner/researcher/checker run (k4 META set): share of output 8-grams (assistant text + Write/Edit content) already present in its own paid inputs (prompt + tool_results received BEFORE the output). LOWER bound on compile cost c = unique input tokens read once (chars*0.447) + novel output tokens; compared with break-even = mean processed per run (k4 ~4.1M for KSR).", "workloads": {}}
    allruns = {}
    for nm in NAMES:
        runs = [t for t in WL[nm]["transcripts"] if not t["main"] and t["stype"] in META]; rows = []
        for t in runs:
            ev = run_events(t["f"]); tot, ov, inch = overlap(ev, 8); tot1, ov1, _ = overlap(ev, 1)
            outtok = sum(c["out"] for c in t["calls"]); P = sum(proc(c) for c in t["calls"]); share = ov / tot if tot else 0
            cl = inch * TOK_PER_CHAR_TR + outtok * (1 - share)
            rows.append({"f": os.path.basename(t["f"]), "stype": t["stype"], "processed": P, "out_tokens": outtok, "out_8grams": tot, "overlap_8gram": ov, "overlap_share": share, "overlap_share_unigram_mutant": (ov1 / tot1 if tot1 else 0), "input_chars": inch, "c_lower_bound": cl})
            allruns.setdefault(nm, []).append((ev, tot))
        n = len(rows); be = st.mean([r["processed"] for r in rows]) if rows else None
        sh = [r["overlap_share"] for r in rows]; clm = st.mean([r["c_lower_bound"] for r in rows]) if rows else None
        w_share = sum(r["overlap_8gram"] for r in rows) / max(1, sum(r["out_8grams"] for r in rows))
        res["workloads"][nm] = {"runs": n, "break_even_per_run": be, "c_lower_bound_mean": clm, "overlap_share_mean": st.mean(sh) if sh else None, "overlap_share_pooled": w_share, "overlap_share_by_stype": {s: st.mean([r["overlap_share"] for r in rows if r["stype"] == s]) for s in {r["stype"] for r in rows}},
                                "copy_heavy": (w_share >= thr) if rows else None, "verdict": (("KILL" if clm >= be else "SURVIVE (lower bound does not kill; survival is NOT proven)") if rows else "N/A (no meta runs)"), "unigram_mutant_pooled": sum(r["overlap_share_unigram_mutant"] * r["out_8grams"] for r in rows) / max(1, sum(r["out_8grams"] for r in rows)), "rows": rows}
    # controls: positive = output copies an input; negative = outputs scored against another run's inputs
    pos_ev = [("in", "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi"), ("out", "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi")]
    pt, po, _ = overlap(pos_ev, 8); neg_ev = [("in", "one two three four five six seven eight nine ten eleven twelve"), ("out", "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi")]
    nt, no_, _ = overlap(neg_ev, 8)
    shuf = {}
    for nm in NAMES:
        L = allruns.get(nm, [])
        if len(L) < 2: continue
        vals = []
        for k, (ev, _) in enumerate(L):
            other = L[(k + 1) % len(L)][0]; t_, o_, _ = overlap([e for e in ev if e[0] == "out"], 8, swap_inputs=other); vals.append(o_ / t_ if t_ else 0)
        shuf[nm] = {"mismatched_pairing_mean_overlap": st.mean(vals), "real_pooled": res["workloads"][nm]["overlap_share_pooled"]}
    mut_changed = any(res["workloads"][nm].get("copy_heavy") is not None and ((res["workloads"][nm]["unigram_mutant_pooled"] >= thr) != res["workloads"][nm]["copy_heavy"]) for nm in NAMES)
    res["controls"] = {"positive_copy": {"share": po / pt if pt else 0, "pass": pt > 0 and po == pt}, "negative_disjoint": {"share": no_ / nt if nt else 0, "pass": nt > 0 and no_ == 0}, "shuffled_pairing": shuf, "mutant_unigram_flips_copy_heavy": mut_changed}
    res["controls"]["all_pass"] = bool(res["controls"]["positive_copy"]["pass"] and res["controls"]["negative_disjoint"]["pass"] and mut_changed)
    jd("out_D.json", res)
    for nm in NAMES:
        w = res["workloads"][nm]
        if w["runs"]: S(f"[D] {nm}: runs={w['runs']} overlap8_pooled={100*w['overlap_share_pooled']:.1f}% mean={100*w['overlap_share_mean']:.1f}% (unigram mutant {100*w['unigram_mutant_pooled']:.1f}%) c_lb_mean={w['c_lower_bound_mean']:,.0f} break_even={w['break_even_per_run']:,.0f} -> {w['verdict']}")
        else: S(f"[D] {nm}: no planner/researcher/checker runs")
    S(f"[D] controls all_pass={res['controls']['all_pass']}; mismatched-pairing overlap: {shuf}")
    return res
RES_D = instr_D()
# ---------------------------------------------------------------- G / H / I
def pclass(t):
    if t["n"] in EDIT and t["fp"]:
        b = os.path.basename(t["fp"]).lower(); ext = os.path.splitext(b)[1]
        kind = "test" if re.search(r"test|spec", b) else "ledger" if re.search(r"ledger|state|progress|resum", b) else "decision" if re.search(r"decision|adr", b) else "plan" if re.search(r"plan|prd|roadmap|requirement", b) else "doc" if ext in (".md", ".txt") else "src"
        return f"{ext}:{kind}"
    return "bash:commit" if t["git"] == "commit" else "bash:write"
def episodes(lt):
    eps = []
    for t, lab in lt:
        start = 0
        for i, (c, L) in enumerate(zip(t["calls"], lab)):
            if L in ("DELTA", "REPAIR"):
                if L == "DELTA":
                    cs = t["calls"][start:i + 1]; names = [x["n"] for cc in cs for x in cc["tools"]]
                    dt_ = next((x for x in c["tools"] if x["n"] in EDIT or x["git"] == "commit" or x["wr"]), c["tools"][0] if c["tools"] else {"n": "?", "fp": None, "git": None})
                    eps.append({"names": names, "pc": pclass(dt_) if c["tools"] else "?", "test": next((x["test"] for cc in cs for x in cc["tools"] if x.get("test")), None), "proc": proc(c)})
                start = i + 1
    return eps
def collapse(names):
    o = []
    for x in names:
        if not o or o[-1] != x: o.append(x)
    return tuple(o[-4:])
def fam(e, mode="seq", names=None, pc=None):
    nm = e["names"] if names is None else names; pcl = e["pc"] if pc is None else pc
    if mode == "seq": return (collapse(nm), pcl, e["test"])
    if mode == "set": return (tuple(sorted(set(nm))), pcl, e["test"])
    return (pcl,)
def recur(fps, procs):
    cnt = collections.Counter(fps); rec = [f for f in fps if cnt[f] >= 2]
    tp = sum(procs); rp = sum(p for f, p in zip(fps, procs) if cnt[f] >= 2)
    return {"episodes": len(fps), "families": len(cnt), "recurring_families": sum(1 for v in cnt.values() if v >= 2), "recurring_episode_share": len(rec) / len(fps) if fps else 0, "recurring_proc_share": rp / tp if tp else 0}
def instr_GHI():
    G = {"instrument": "G", "definition": "episode = calls since previous DELTA/REPAIR up to a DELTA call; family=(collapsed last-4 tool names, path class, test cmd); recurring = family seen >=2; NULL = tool order shuffled within episode + path classes permuted across episodes (200 reps)", "workloads": {}}
    H = {"instrument": "H", "definition": "non-recurring DELTA (G primary family) processed tokens / workload processed = approximate floor of genuinely new cognition (not quality-judged)", "workloads": {}}
    I = {"instrument": "I", "definition": "label -> boundary-miss class", "workloads": {}}
    mutH = {}
    for nm in NAMES:
        lt = LAB[nm]; eps = episodes(lt); procs = [e["proc"] for e in eps]; base = metrics(lt)["processed"]
        real = recur([fam(e) for e in eps], procs); realset = recur([fam(e, "set") for e in eps], procs); path_only = recur([fam(e, "path") for e in eps], procs)
        nulls = []
        for _ in range(200):
            pcs = [e["pc"] for e in eps]; RNG.shuffle(pcs)
            fp = []
            for e, p in zip(eps, pcs):
                nmz = list(e["names"]); RNG.shuffle(nmz); fp.append(fam(e, "seq", names=nmz, pc=p))
            nulls.append(recur(fp, procs))
        ne = [x["recurring_episode_share"] for x in nulls]; npr = [x["recurring_proc_share"] for x in nulls]
        G["workloads"][nm] = {"real": real, "set_variant_sensitivity": realset, "null_episode_share_mean_sd": [st.mean(ne), st.pstdev(ne)], "null_proc_share_mean_sd": [st.mean(npr), st.pstdev(npr)],
                              "recurrence_above_null_episode_pp": 100 * (real["recurring_episode_share"] - st.mean(ne)), "recurrence_above_null_proc_pp": 100 * (real["recurring_proc_share"] - st.mean(npr)), "z_episode": (real["recurring_episode_share"] - st.mean(ne)) / (st.pstdev(ne) or 1e-9),
                              "share_of_DELTA_context_in_recurring_families_pct": 100 * real["recurring_proc_share"], "mutant_path_class_only": path_only}
        dproc = sum(procs); nonrec = dproc * (1 - real["recurring_proc_share"])
        mt = metrics(lt); rep = mt["processed_by_label"].get("REPAIR", 0)
        H["workloads"][nm] = {"workload_processed": base, "DELTA_processed": dproc, "nonrecurring_DELTA_processed": nonrec, "irreducible_floor_pct_of_workload": 100 * nonrec / base, "pct_of_DELTA": 100 * (1 - real["recurring_proc_share"]) if dproc else None,
                              "nonrecurring_DELTA_calls": round(real["episodes"] * (1 - real["recurring_episode_share"])), "mutant_path_only_floor_pct": 100 * dproc * (1 - path_only["recurring_proc_share"]) / base, "repair_pct_excluded": 100 * rep / base}
        P = mt["processed_by_label"]; N = mt["counts"]; calls = mt["calls"]
        rp = real["recurring_proc_share"]; re_ = real["recurring_episode_share"]
        dn, dp = N.get("DELTA", 0), P.get("DELTA", 0)
        classes = {"control-loop miss": (N.get("CONTROL_LOOP", 0), P.get("CONTROL_LOOP", 0)), "repair/proof miss": (N.get("REPAIR", 0), P.get("REPAIR", 0)), "transformation miss (recurring DELTA)": (dn * re_, dp * rp), "novelty (non-recurring DELTA)": (dn * (1 - re_), dp * (1 - rp)), "unknown (OTHER)": (N.get("OTHER", 0), P.get("OTHER", 0))}
        I["workloads"][nm] = {k: {"call_pct": 100 * v[0] / calls, "proc_pct": 100 * v[1] / base} for k, v in classes.items()}
        I["workloads"][nm]["sum_proc_pct"] = sum(100 * v[1] / base for v in classes.values()); I["workloads"][nm]["sum_call_pct"] = sum(100 * v[0] / calls for v in classes.values())
        mutH[nm] = {"mutant_OTHER_as_CONTROL": 100 * (P.get("CONTROL_LOOP", 0) + P.get("OTHER", 0)) / base, "base_unknown_pct": 100 * P.get("OTHER", 0) / base}
    # controls G/H/I
    mk_e = lambda nm, pc: {"names": nm, "pc": pc, "test": None, "proc": 100}
    pos_eps = [mk_e(["Read", "Edit"], ".py:src")] * 3 + [mk_e(["Grep", "Bash", "Edit"], ".md:doc")]
    pos = recur([fam(e) for e in pos_eps], [e["proc"] for e in pos_eps])
    neg_eps = [mk_e(["Read"] * (i + 1) + ["Bash"] * i, f".x{i}:src") for i in range(6)]; neg = recur([fam(e) for e in neg_eps], [100] * 6)
    chgG = any(abs(G["workloads"][nm]["mutant_path_class_only"]["recurring_proc_share"] - G["workloads"][nm]["real"]["recurring_proc_share"]) > 0.02 for nm in NAMES)
    chgH = any(abs(H["workloads"][nm]["mutant_path_only_floor_pct"] - H["workloads"][nm]["irreducible_floor_pct_of_workload"]) > 0.5 for nm in NAMES)
    chgI = any(mutH[nm]["mutant_OTHER_as_CONTROL"] != 100 * (metrics(LAB[nm])["processed_by_label"].get("CONTROL_LOOP", 0)) / metrics(LAB[nm])["processed"] for nm in NAMES)
    G["controls"] = {"positive_synthetic": {"recurring_episode_share": pos["recurring_episode_share"], "pass": abs(pos["recurring_episode_share"] - 0.75) < 1e-9}, "negative_all_distinct": {"recurring_episode_share": neg["recurring_episode_share"], "pass": neg["recurring_episode_share"] == 0},
                     "shuffled_null_is_in_workloads": "see null_*_mean_sd", "mutant_path_class_only_changes_share": chgG}
    G["controls"]["all_pass"] = bool(G["controls"]["positive_synthetic"]["pass"] and G["controls"]["negative_all_distinct"]["pass"] and chgG)
    H["controls"] = {"positive_synthetic_floor": {"nonrecurring_proc_share_of_DELTA": 1 - pos["recurring_proc_share"], "pass": abs((1 - pos["recurring_proc_share"]) - 0.25) < 1e-9}, "negative_all_distinct_floor_is_100pct_of_DELTA": {"value": 1 - neg["recurring_proc_share"], "pass": neg["recurring_proc_share"] == 0}, "mutant_path_only_changes_floor": chgH}
    H["controls"]["all_pass"] = bool(H["controls"]["positive_synthetic_floor"]["pass"] and H["controls"]["negative_all_distinct_floor_is_100pct_of_DELTA"]["pass"] and chgH)
    sums = all(abs(I["workloads"][nm]["sum_proc_pct"] - 100) < 1e-6 and abs(I["workloads"][nm]["sum_call_pct"] - 100) < 1e-6 for nm in NAMES)
    I["controls"] = {"positive_shares_sum_100": sums, "negative_shuffled": "label-shuffle null is the A/B/F shuffled-order control", "mutant_OTHER_as_CONTROL": mutH, "mutant_changes_verdict": chgI}
    I["controls"]["all_pass"] = bool(sums and chgI)
    jd("out_G.json", G); jd("out_H.json", H); jd("out_I.json", I)
    for nm in NAMES:
        g = G["workloads"][nm]; h = H["workloads"][nm]; i_ = I["workloads"][nm]
        S(f"[G] {nm}: episodes={g['real']['episodes']} families={g['real']['families']} recurring_fams={g['real']['recurring_families']} rec_ep={100*g['real']['recurring_episode_share']:.1f}% null={100*g['null_episode_share_mean_sd'][0]:.1f}+-{100*g['null_episode_share_mean_sd'][1]:.1f} above_null={g['recurrence_above_null_episode_pp']:+.1f}pp z={g['z_episode']:.1f}; DELTA ctx in recurring fams={g['share_of_DELTA_context_in_recurring_families_pct']:.1f}% (null {100*g['null_proc_share_mean_sd'][0]:.1f}%); set-variant rec_ep={100*g['set_variant_sensitivity']['recurring_episode_share']:.1f}%")
        S(f"[H] {nm}: irreducible floor = {h['irreducible_floor_pct_of_workload']:.1f}% of workload processed ({h['pct_of_DELTA']:.1f}% of DELTA), nonrecurring DELTA calls ~{h['nonrecurring_DELTA_calls']}; path-only mutant {h['mutant_path_only_floor_pct']:.1f}%")
        S(f"[I] {nm}: " + "; ".join(f"{k} {v['proc_pct']:.1f}%/{v['call_pct']:.1f}%calls" for k, v in i_.items() if isinstance(v, dict)))
    S(f"[G] controls all_pass={G['controls']['all_pass']} [H] {H['controls']['all_pass']} [I] {I['controls']['all_pass']}")
instr_GHI()
# ---------------------------------------------------------------- sample file, summary, manifest
smp = []
for nm in NAMES: smp += RES_ABF["workloads"][nm]["sample_for_human_judgment"]
jd("t2_unclassified_sample_60.json", {"note": "stratified sample of OTHER (unclassifiable) calls for later HUMAN judgment; no model was used to judge", "n": len(smp), "calls": smp})
open(os.path.join(OUT, "t2_summary.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(SUM) + "\n")
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
here = os.path.dirname(os.path.abspath(__file__)); man = {"note": "sha256 of each script and output; controls summarized from out_*.json", "files": {}, "controls_all_pass": {}}
for fn in ("meter.py", "t2_extract.py", "t2_instruments.py", "t2_extract_out.txt", "t2_summary.txt", "t2_unclassified_sample_60.json", "out_A_B_F.json", "out_E.json", "out_C.json", "out_D.json", "out_G.json", "out_H.json", "out_I.json"):
    p = os.path.join(here if fn.startswith(("meter", "t2_extract.py", "t2_instruments")) else OUT, fn)
    if os.path.exists(p): man["files"][fn] = sha(p)
man["files"]["t2_cache.json(scratchpad, not committed)"] = sha(CACHE)
for k in ("A_B_F", "E", "C", "D", "G", "H", "I"): man["controls_all_pass"][k] = json.load(open(os.path.join(OUT, f"out_{k}.json")))["controls"]["all_pass"]
jd("manifest.json", man); print(json.dumps(man["controls_all_pass"]))
