"""Gen3 T2 extractor (zero-model). Per call: ts, ctx, out, tool_use names + key input fields, tool_result sizes/fail flags,
git commit/revert markers. Workload lists/windows/controls are copied from gen3_t1/g3_k4_factorial.py:
  ARM/EPOCH = line 8, META = line 9, IO_W = line 10, KME_W = line 11, KSR control 273,912,110 = line 110,
  agentId -> subagent_type linkage = load() lines 28-34 and 42, .meta.json fallback lines 57-60.
usage: python t2_extract.py OUT_CACHE.json OUT_SUMMARY.txt"""
import glob, json, os, re, sys, datetime as dt
BASE = os.path.expanduser(r"~\.claude\projects")
ARM = dt.datetime(2026, 10, 3, 19, 40, tzinfo=dt.timezone.utc); EPOCH = dt.datetime(2000, 1, 1, tzinfo=dt.timezone.utc)   # k4 line 8
IO_W = "be2a71eb 50d3a9f0 affe87e4 63bc3ed8 dc79aa64 5f5bc46f 4f1b398d dfc0acda".split()   # k4 line 10
KME_W = "67ca9fa1 41e4bea7 2f9049a0".split()                                               # k4 line 11
CTRL = {"KSR": 273912110, "InfinityOps": 373740097, "KME": 107407089}                       # KSR: k4 line 110; others: k4_out.txt ctx=
WRITE_RE = re.compile(r"(Set-Content|Add-Content|Out-File|WriteAllText|\bsed\s+-i|\btee\b|Copy-Item|Move-Item|New-Item|(?<![0-9&>])>>?\s*[\w'\"$~./\\])", re.I)
NOISE_RE = re.compile(r"(2>&1|\d?>\s*\$null|>\s*/dev/null|>\s*nul\b|\*>&1|>&\d)", re.I)
TEST_RE = re.compile(r"(pytest|mix\s+test|npm\s+(run\s+)?test|node\s+\S*test\S*|python\S*\s+\S*test_\S+|unittest|cargo\s+test|--selftest|go\s+test|vitest|jest)", re.I)
TMP_RE = re.compile(r"(\\temp\\|/tmp/|/tmp\b|scratchpad|\$env:temp|\\appdata\\local\\temp|\.tmp\b)", re.I)
FAIL_RE = re.compile(r"(\b[1-9]\d* failed\b|Traceback \(most recent|AssertionError|\bFAIL\b|\bFAILED\b|exit code [1-9]|Exit code [1-9]|No such file or directory|cannot find path)", re.I)
SUBJ_RE = re.compile(r"git[^\n]*\bcommit\b[^\n]*?(?:-m|--message)\s+(?:\"([^\"]+)\"|'([^']+)')", re.I)
def T(s): return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
def tlen(c):
    if c is None: return 0
    if isinstance(c, str): return len(c)
    if isinstance(c, list): return sum(tlen(x) for x in c)
    if isinstance(c, dict):
        if isinstance(c.get("text"), str): return len(c["text"])
        return tlen(c.get("content")) if "content" in c else 0
    return 0
def ttext(c):
    if isinstance(c, str): return c
    if isinstance(c, list): return " ".join(ttext(x) for x in c)
    if isinstance(c, dict): return c["text"] if isinstance(c.get("text"), str) else ttext(c.get("content"))
    return ""
def tool_rec(b):
    inp = b.get("input") if isinstance(b.get("input"), dict) else {}
    n = b.get("name") or "?"
    fp = inp.get("file_path") or inp.get("notebook_path") or inp.get("path")
    cmd = inp.get("command") if isinstance(inp.get("command"), str) else ""
    r = {"n": n, "fp": fp if isinstance(fp, str) else None, "cmd": cmd[:200], "wr": False, "tmp": False, "test": None, "git": None, "subj": None}
    if cmd:
        c2 = NOISE_RE.sub(" ", cmd)
        r["wr"] = bool(WRITE_RE.search(c2)); r["tmp"] = bool(TMP_RE.search(cmd))
        m = TEST_RE.search(cmd); r["test"] = m.group(0).lower()[:24] if m else None
        if re.search(r"git[^\n]*\bcommit\b", cmd, re.I):
            r["git"] = "commit"; s = SUBJ_RE.search(cmd)
            if s: r["subj"] = (s.group(1) or s.group(2))[:120]
            else:
                hd = re.search(r"-F\s+\S+", cmd)
                r["subj"] = "F:" + hd.group(0)[:60] if hd else None
        elif re.search(r"git[^\n]*\b(revert|reset)\b", cmd, re.I): r["git"] = "revert"
    return r
def load(files, lo, seen):
    TT, agent_type, agent_results = [], {}, []
    for f in files:
        main = (os.sep + "subagents" + os.sep) not in f
        calls, local, tu, idx_of_tool = [], {}, {}, {}
        for line in open(f, encoding="utf-8", errors="replace"):
            if '"usage"' not in line and '"tool_use_id"' not in line: continue
            try: o = json.loads(line)
            except ValueError: continue
            ty = o.get("type"); m = o.get("message") or {}
            if ty == "assistant":
                u = m.get("usage"); blocks = m.get("content") or []
                if not u or not o.get("timestamp"): continue
                k = m.get("id") or o.get("requestId") or o.get("uuid")
                if k in local: ci = local[k]
                else:
                    if T(o["timestamp"]) < lo or k in seen: continue
                    seen.add(k); ci = len(calls); local[k] = ci
                    calls.append({"ts": o["timestamp"], "ctx": (u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0),
                                  "out": u.get("output_tokens") or 0, "tools": [], "res": [], "txt": 0})
                for b in blocks:
                    if not isinstance(b, dict): continue
                    if b.get("type") == "tool_use":
                        calls[ci]["tools"].append(tool_rec(b)); idx_of_tool[b.get("id")] = ci
                        if isinstance(b.get("input"), dict) and b["input"].get("subagent_type"): tu[b.get("id")] = b["input"]["subagent_type"]
                    elif b.get("type") == "text": calls[ci]["txt"] += len(b.get("text") or "")
            elif ty == "user":
                content = m.get("content")
                if not isinstance(content, list): continue
                tur = o.get("toolUseResult") or {}
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        tid = b.get("tool_use_id"); ci = idx_of_tool.get(tid)
                        txt = ttext(b.get("content")); sz = tlen(b.get("content"))
                        fail = bool(b.get("is_error")) or bool(FAIL_RE.search(txt[:4000]))
                        if ci is not None: calls[ci]["res"].append({"id": tid, "size": sz, "fail": fail})
                        if main and isinstance(tur, dict) and tur.get("agentId") and tid in tu:
                            agent_type[tur["agentId"]] = tu[tid]
                            agent_results.append({"main_f": f, "agentId": tur["agentId"], "stype": tu[tid], "chars": sz, "after": len(calls) - 1})
        if calls: TT.append({"f": f, "sid": os.path.basename(f)[:8] if main else re.sub(r"^agent-", "", os.path.basename(f))[:-6], "main": main, "stype": None, "calls": calls})
    for t in TT:
        if not t["main"]:
            aid = t["sid"]; st = agent_type.get(aid); mf = t["f"][:-6] + ".meta.json"
            if st is None and os.path.exists(mf):
                try: st = json.load(open(mf, encoding="utf-8")).get("agentType")
                except ValueError: pass
            t["stype"] = st
    for a in agent_results: a["stype"] = agent_type.get(a["agentId"], a["stype"])
    return TT, agent_results
def files_for(name):
    if name == "KSR":
        return glob.glob(os.path.join(BASE, "C--Users-User-Apps-recon-work-wt-keosdtk-home", "**", "*.jsonl"), recursive=True), ARM
    d, W = (os.path.join(BASE, "C--Users-User-Apps-io-device-trust"), IO_W) if name == "InfinityOps" else (os.path.join(BASE, "C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files"), KME_W)
    return [f for w in W for f in glob.glob(os.path.join(d, w + "-*.jsonl")) + glob.glob(os.path.join(d, w + "-*", "**", "*.jsonl"), recursive=True)], EPOCH
cache, L = {}, []
for name in ("KSR", "InfinityOps", "KME"):
    files, lo = files_for(name); TT, ar = load(files, lo, set())
    ctx = sum(c["ctx"] for t in TT for c in t["calls"]); out = sum(c["out"] for t in TT for c in t["calls"]); n = sum(len(t["calls"]) for t in TT)
    cache[name] = {"ctrl": {"expected_ctx": CTRL[name], "ctx": ctx, "match": ctx == CTRL[name]}, "transcripts": TT, "agent_results": ar}
    tools = sum(len(c["tools"]) for t in TT for c in t["calls"])
    L.append(f"{name}: transcripts={len(TT)} calls={n} ctx={ctx:,} out={out:,} expected_ctx={CTRL[name]:,} -> {'EXACT MATCH' if ctx == CTRL[name] else 'MISMATCH delta ' + format(ctx - CTRL[name], ',')}; tool_uses={tools} agent_results={len(ar)}")
json.dump(cache, open(sys.argv[1], "w"))
open(sys.argv[2], "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n"); print("\n".join(L))
