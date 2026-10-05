"""K2: hook output inventory over main transcripts (cache from g3_extract.py). Zero-model.
Model-visible = events carrying a 'rendered' field. hook_success has none (regression proof in g3_regress.py).
rent = rendered_chars x 0.32 x (later calls in the session)."""
import json, sys, re, os, glob, statistics as st, collections
S = json.load(open(sys.argv[1])); REPO = sys.argv[2]
TPC = 0.32
seen = set(); SS = []
for s in S:
    k = (s["sid"], s["calls"][0][0])
    if k in seen: continue
    seen.add(k); SS.append(s)
tot_ctx = sum(c[1] for s in SS for c in s["calls"])
print("sessions", len(SS), "calls", sum(len(s["calls"]) for s in SS), "sum ctx", f"{tot_ctx:,}")
ANCH = [("superpowers", r"You have superpowers"), ("tower-baseline", r"Tower baseline"), ("correction-R6", r"CORRECTION DETECTED"),
        ("cross-project-baseline", r"Cross-project baseline"), ("woz", r"\[Woz\]"), ("skill-advisor", r"SKILL ADVISOR"),
        ("compound-learnings", r"Compound Learnings"), ("persisted-output", r"persisted-output"), ("session-start-other", r"SessionStart")]
def cluster(head):
    for n, p in ANCH:
        if re.search(p, head): return n
    return "other:" + re.sub(r"\d+", "#", head[:40])
rows = collections.defaultdict(lambda: {"n": 0, "chars": [], "rent": 0.0, "frame": 0})
hs = {"n": 0, "chars": 0, "rent": 0.0}; hsys = [0, 0]; byev = collections.defaultdict(lambda: [0, 0, 0.0])
for s in SS:
    nc = len(s["calls"])
    for e in s["events"]:
        if e["t"] == "hook_success":
            hs["n"] += 1; hs["chars"] += e["so"]; hs["rent"] += e["so"] * TPC * (nc - e["i"])
        elif e["t"] == "hook_system_message":
            hsys[0] += 1; hsys[1] += 1 if e["r"] is not None else 0
        elif e["t"] == "hook_additional_context" and e["r"] is not None:
            c = cluster(e.get("head") or ""); r = rows[c]
            r["n"] += 1; r["chars"].append(e["r"]); r["rent"] += e["r"] * TPC * (nc - e["i"]); r["frame"] += e["r"] - e["cl"]
            b = byev[e.get("hn") or "?"]; b[0] += 1; b[1] += e["r"]; b[2] += e["r"] * TPC * (nc - e["i"])
tot_rent = sum(r["rent"] for r in rows.values())
print(f"HOOK_ADDITIONAL_CONTEXT (model-visible): n={sum(r['n'] for r in rows.values())} rent={tot_rent:,.0f} tok = {tot_rent/tot_ctx:.2%} of main context")
print("by emitter cluster (n | total chars | median chars | rent tok | share of ctx | host-frame chars):")
for c, r in sorted(rows.items(), key=lambda kv: -kv[1]["rent"])[:14]:
    print(f"  {c[:44]:44} {r['n']:5} {sum(r['chars']):9,} {st.median(r['chars']):7,.0f} {r['rent']:13,.0f} {r['rent']/tot_ctx:6.2%} {r['frame']:8,}")
print("by hook name (n | chars | rent):")
for h, b in sorted(byev.items(), key=lambda kv: -kv[1][2])[:10]: print(f"  {h[:34]:34} {b[0]:5} {b[1]:9,} {b[2]:13,.0f}")
print(f"HOOK_SUCCESS (NOT model-visible: no 'rendered', regression coefficient ~0.03): n={hs['n']} stdout chars={hs['chars']:,} counterfactual rent if it WERE context={hs['rent']:,.0f} tok = {hs['rent']/tot_ctx:.2%}  [Stage0 claim 11-13% REFUTED as context]")
print("hook_system_message n/with-rendered:", hsys)
frame = sum(r["frame"] for r in rows.values()); print(f"host framing in rendered hac: {frame:,} chars over {sum(r['n'] for r in rows.values())} events ({frame/max(1,sum(sum(r['chars']) for r in rows.values())):.1%} of rendered chars)")
# provenance: where are the anchor strings and how do dispatchers emit?
HK = os.path.expanduser(r"~\.claude\hooks")
print("ORIGIN (files under ~/.claude/hooks containing the anchor literal):")
for n, p in ANCH[1:7]:
    lit = {"tower-baseline": "Tower baseline", "correction-R6": "CORRECTION DETECTED", "cross-project-baseline": "Cross-project baseline", "woz": "[Woz]", "skill-advisor": "SKILL ADVISOR", "compound-learnings": "Compound Learnings"}[n]
    hit = []
    for f in glob.glob(os.path.join(HK, "**", "*.js"), recursive=True) + glob.glob(os.path.join(HK, "**", "*.py"), recursive=True):
        try:
            if lit in open(f, encoding="utf-8", errors="replace").read(): hit.append(os.path.relpath(f, HK))
        except OSError: pass
    print(f"  {n:24} -> {hit[:4]}")
disp = glob.glob(os.path.join(HK, "hook-dispatcher.js")) + [f for f in glob.glob(os.path.join(REPO, "**", "hook-dispatcher.js"), recursive=True) if ".claude" + os.sep + "worktrees" not in f and "node_modules" not in f]
print("dispatcher copies:", disp)
for f in disp[:2]:
    L = open(f, encoding="utf-8", errors="replace").read().splitlines()
    hits = [(i + 1, l.strip()[:150]) for i, l in enumerate(L) if re.search(r"additionalContext|hookSpecificOutput|systemMessage", l)]
    print(f"  {os.path.basename(os.path.dirname(f))}/{os.path.basename(f)} lines={len(L)} emit-lines={len(hits)}")
    for h in hits[:7]: print("    ", h)
