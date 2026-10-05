"""K4: offline factorial attribution (CEILINGS / counterfactuals, zero-model). One script, reuses ksr_floor.py's grid formula.
Unit: processed = input + cache_write + cache_read + output, deduped by message id.
Scenarios, applied sequentially (e) = a -> b -> c -> d with no double counting (each stage works on the previous stage's ctx)."""
import glob, json, os, re, sys, collections, datetime as dt
BASE = os.path.expanduser(r"~\.claude\projects")
TPC = 0.32
D_MEAS, D_IMPL = 3705, 8966          # K1: measured first-call delta (n=1) / instructions -28,020 chars x 0.32
ARM = dt.datetime(2026, 10, 3, 19, 40, tzinfo=dt.timezone.utc); EPOCH = dt.datetime(2000, 1, 1, tzinfo=dt.timezone.utc)
META = {"gsd-planner", "gsd-phase-researcher", "gsd-plan-checker"}
IO_W = "be2a71eb 50d3a9f0 affe87e4 63bc3ed8 dc79aa64 5f5bc46f 4f1b398d dfc0acda".split()
KME_W = "67ca9fa1 41e4bea7 2f9049a0".split()
def T(s): return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
def tlen(c):
    if c is None: return 0
    if isinstance(c, str): return len(c)
    if isinstance(c, list): return sum(tlen(x) for x in c)
    if isinstance(c, dict):
        if isinstance(c.get("text"), str): return len(c["text"])
        return tlen(c.get("content")) if "content" in c else 0
    return 0
def load(files, lo, seen):
    """returns transcripts: dict path -> {main:bool, calls:[ctx,out], hac:[(callidx,chars)], hs:[(callidx,chars)], stype}"""
    T_, agent_type = {}, {}
    for f in files:
        main = (os.sep + "subagents" + os.sep) not in f
        calls, hac, hs, tu = [], [], [], {}
        for line in open(f, encoding="utf-8", errors="replace"):
            if main and '"agentId"' in line and '"tool_use_id"' in line:
                try:
                    o = json.loads(line); a = (o.get("toolUseResult") or {})
                    if isinstance(a, dict) and a.get("agentId"):
                        for b in (o.get("message") or {}).get("content") or []:
                            if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id") in tu: agent_type[a["agentId"]] = tu[b["tool_use_id"]]
                except ValueError: pass
                continue
            if '"usage"' not in line and '"attachment"' not in line and '"subagent_type"' not in line: continue
            try: o = json.loads(line)
            except ValueError: continue
            ty = o.get("type"); m = o.get("message") or {}
            if ty == "assistant":
                for b in m.get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use" and isinstance(b.get("input"), dict) and b["input"].get("subagent_type"): tu[b.get("id")] = b["input"]["subagent_type"]
                u = m.get("usage")
                if u and o.get("timestamp"):
                    k = m.get("id") or o.get("requestId") or o.get("uuid")
                    if T(o["timestamp"]) < lo or k in seen: continue
                    seen.add(k)
                    calls.append([(u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0), u.get("output_tokens") or 0])
            elif ty == "attachment" and o.get("timestamp") and T(o["timestamp"]) >= lo:
                a = o.get("attachment") or {}
                if a.get("type") == "hook_additional_context" and "rendered" in o: hac.append((len(calls), tlen(o["rendered"])))
                elif a.get("type") == "hook_success" and isinstance(a.get("stdout"), str): hs.append((len(calls), len(a["stdout"])))
        if calls: T_[f] = {"main": main, "calls": calls, "hac": hac, "hs": hs}
    for f, t in T_.items():
        if not t["main"]:
            aid = re.sub(r"^agent-", "", os.path.basename(f))[:-6]; st = agent_type.get(aid)
            mf = f[:-6] + ".meta.json"
            if st is None and os.path.exists(mf):
                try: st = json.load(open(mf, encoding="utf-8")).get("agentType")
                except ValueError: pass
            t["stype"] = st
    return T_
def grid(ts, N, S):
    cf = 0
    for t in ts:
        c = [x[0] for x in t["calls"]]; f0 = c[0]
        for i in range(len(c)):
            seg = (i // N) * N; base = c[seg]; cf += c[i] if seg == 0 else min(c[i], f0 + S + (c[i] - base))
    return cf
def run(name, files, lo, ctrl=None):
    seen = set(); TT = load(files, lo, seen); ts = list(TT.values())
    ctx = sum(x[0] for t in ts for x in t["calls"]); out = sum(x[1] for t in ts for x in t["calls"]); base = ctx + out
    calls = sum(len(t["calls"]) for t in ts)
    L = [f"=== {name}: transcripts={len(ts)} (main {sum(t['main'] for t in ts)}) calls={calls} ctx={ctx:,} out={out:,} processed={base:,}"]
    if ctrl: L.append(f"    CONTROL ctx expected {ctrl:,} -> {'EXACT MATCH' if ctx == ctrl else 'MISMATCH delta ' + format(ctx - ctrl, ',')}")
    P = lambda lab, v: L.append(f"    {lab:62} {v/1e6:10.2f}M  {100*(v-base)/base:+6.1f}%")
    P("BASE (measured)", base)
    def sub_floor(ts, d): return [dict(t, calls=[[max(0, c[0] - d), c[1]] for c in t["calls"]]) for t in ts]
    def sub_hook(ts, key):
        r = []
        for t in ts:
            if not t["main"] or not t[key]: r.append(t); continue
            add = [0.0] * (len(t["calls"]) + 1)
            for i, ch in t[key]:
                if i < len(add): add[i] += ch * TPC
            run_, cs = 0.0, []
            for j, c in enumerate(t["calls"]): run_ += add[j]; cs.append([max(0, c[0] - run_), c[1]])
            r.append(dict(t, calls=cs))
        return r
    tot = lambda ts: sum(x[0] + x[1] for t in ts for x in t["calls"])
    for d, lab in ((D_MEAS, "measured n=1"), (D_IMPL, "instructions-implied")):
        P(f"(a) floor-only, -{d:,}/call ({lab})  [CEILING]", tot(sub_floor(ts, d)))
    hacT = sub_hook(ts, "hac"); P("(b) hook-only: remove hook_additional_context rent (main calls)  [CEILING]", tot(hacT))
    hsT = sub_hook(ts, "hs"); P("(b') hook_success rent IF it were context (REFUTED, NOT a saving)", tot(hsT))
    meta = [t for t in ts if not t["main"] and t.get("stype") in META]; unk = [t for t in ts if not t["main"] and t.get("stype") is None]
    bm = collections.Counter(t.get("stype") for t in ts if not t["main"])
    L.append(f"    subagent runs by type: {dict(bm.most_common(8))}; meta runs={len(meta)} (processed {tot(meta)/1e6:.2f}M) unclassified={len(unk)}")
    keep = [t for t in ts if t not in meta]
    for c in (0, 2e6, 5e6): P(f"(c) meta-work-only: drop planner/researcher/checker runs, +c={c/1e6:.0f}M/run  [CEILING]", tot(keep) + c * len(meta))
    for N in (10, 20, 40):
        for S in (10000, 30000): P(f"(d) bounded workers N={N} S={S//1000}k on measured  [CEILING]", grid(ts, N, S) + out)
    for d, lab in ((D_MEAS, "meas"), (D_IMPL, "impl")):
        cur = sub_floor(ts, d); cur = sub_hook(cur, "hac"); mm = [t for t in cur if not t["main"] and t.get("stype") in META]; cur2 = [t for t in cur if t not in mm]
        for c in (0, 2e6, 5e6):
            for N, S in ((20, 10000), (40, 30000)):
                P(f"(e) combined a({lab})>b>c(c={c/1e6:.0f}M)>d(N={N},S={S//1000}k)  [CEILING]", grid(cur2, N, S) + sum(x[1] for t in cur2 for x in t["calls"]) + c * len(mm))
    return "\n".join(L)
out = []
kdir = os.path.join(BASE, "C--Users-User-Apps-recon-work-wt-keosdtk-home")
out.append(run("KSR (call-level ts>=2026-10-03T19:40Z, all transcripts)", glob.glob(os.path.join(kdir, "**", "*.jsonl"), recursive=True), ARM, 273912110))
iod = os.path.join(BASE, "C--Users-User-Apps-io-device-trust")
out.append(run("InfinityOps odr-device-trust (8 workers + subagents)", [f for w in IO_W for f in glob.glob(os.path.join(iod, w + "-*.jsonl")) + glob.glob(os.path.join(iod, w + "-*", "**", "*.jsonl"), recursive=True)], EPOCH))
kd = os.path.join(BASE, "C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files")
out.append(run("KME KobiiCraft (3 workers + subagents)", [f for w in KME_W for f in glob.glob(os.path.join(kd, w + "-*.jsonl")) + glob.glob(os.path.join(kd, w + "-*", "**", "*.jsonl"), recursive=True)], EPOCH))
open(sys.argv[1], "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print("\n".join(out))
