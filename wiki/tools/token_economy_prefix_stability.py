"""Why session starts share no cache: compare the recorded prompt_snapshot (system prompt +
tool definitions) of consecutive main sessions in the SAME directory within 1 h (inside the
subscription TTL). For each pair: does the tools block match, does each system-prompt section
match, and how much did the second session's first call read from cache?
Read-only, zero model quota."""
import hashlib, json, os, sqlite3, sys, time
from collections import Counter, defaultdict

p = os.path.expanduser("~/.claude/state/usage_index/index.sqlite")
c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
END = c.execute("select max(ts) from calls").fetchone()[0]
first = {}
for f, ts, cr, cw in c.execute("select file, ts, cr, cw from calls where is_sub=0 and ts>? order by ts", (END - 7 * 86400,)):
    first.setdefault(f, (ts, cr, cw))

H = lambda x: hashlib.sha1(json.dumps(x, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:10]
snap = {}
for f in first:
    try:
        for line in open(f, encoding="utf-8"):
            if '"prompt_snapshot"' in line:
                a = json.loads(line).get("attachment") or {}
                if a.get("type") == "prompt_snapshot":
                    sp = a.get("systemPrompt") or []
                    tools = a.get("tools") or []
                    snap[f] = dict(tools=H(tools), names=[t.get("name") for t in tools],
                                   tdesc={t.get("name"): H(t) for t in tools},
                                   sec=[H(s) for s in sp], sec_txt=[(s[:60] if isinstance(s, str) else str(s)[:60]) for s in sp])
                    break
    except OSError:
        pass
print(f"main first calls={len(first)}, with prompt_snapshot={len(snap)}")

bydir = defaultdict(list)
for f, (ts, cr, cw) in first.items():
    if f in snap:
        bydir[os.path.dirname(f)].append((ts, f, cr, cw))
pairs = 0; tools_same = 0; read_when_same = []; read_when_diff = []
diff_tools = Counter(); diff_sec = Counter(); sec_label = {}
for d, lst in bydir.items():
    lst.sort()
    for (t0, f0, _, _), (t1, f1, cr1, cw1) in zip(lst, lst[1:]):
        if t1 - t0 > 3600:
            continue
        pairs += 1
        a, b = snap[f0], snap[f1]
        if a["tools"] == b["tools"]:
            tools_same += 1; read_when_same.append(cr1)
        else:
            read_when_diff.append(cr1)
            names = set(a["names"]) ^ set(b["names"])
            for n in names:
                diff_tools["added/removed:" + str(n)[:40]] += 1
            for n in set(a["names"]) & set(b["names"]):
                if a["tdesc"][n] != b["tdesc"][n]:
                    diff_tools["changed:" + str(n)[:40]] += 1
        for i, (x, y) in enumerate(zip(a["sec"], b["sec"])):
            if x != y:
                diff_sec[i] += 1; sec_label[i] = b["sec_txt"][i]
med = lambda v: sorted(v)[len(v) // 2] if v else "NA"
print(f"same-dir consecutive session pairs within 1 h: {pairs}; tools block identical in {tools_same} ({tools_same/max(pairs,1):.0%})")
print(f"  first-call cache_read median: tools same={med(read_when_same)}  tools differ={med(read_when_diff)}")
print("  tool definitions that differ between paired sessions (top 15):")
for k, v in diff_tools.most_common(15):
    print(f"    {v:>4}  {k}")
print("  system-prompt sections that differ (index: pairs, first 60 chars):")
for i, v in sorted(diff_sec.items(), key=lambda x: -x[1])[:10]:
    print(f"    sec {i:>2}: {v:>4}  {sec_label[i]!r}")
