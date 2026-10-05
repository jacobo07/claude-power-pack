import glob, json, os, statistics
from collections import Counter
P = os.path.expanduser(r"~\.claude\projects\C--Users-User-Apps-io-device-trust")
W = ["be2a71eb","50d3a9f0","affe87e4","63bc3ed8","dc79aa64","5f5bc46f","4f1b398d","dfc0acda"]
K = ("input_tokens","cache_creation_input_tokens","cache_read_input_tokens")
rows=[]; kinds=Counter()
for w in W:
    sid = os.path.basename(glob.glob(os.path.join(P, f"{w}-*.jsonl"))[0])[:-6]
    for f in glob.glob(os.path.join(P, sid, "subagents", "*.jsonl")):
        ctx=[]; seen=set(); out=0; agent="?"
        meta=f[:-6]+".meta.json"
        if os.path.exists(meta):
            try: agent=json.load(open(meta,encoding="utf-8")).get("agentType","?")
            except Exception: pass
        for line in open(f,encoding="utf-8",errors="replace"):
            try: o=json.loads(line)
            except ValueError: continue
            m=o.get("message") or {}; u=m.get("usage")
            if o.get("type")=="assistant" and u:
                i=m.get("id") or o.get("uuid")
                if i in seen: continue
                seen.add(i); ctx.append(sum(int(u.get(k) or 0) for k in K)); out+=int(u.get("output_tokens") or 0)
        if ctx:
            rows.append((agent,len(ctx),ctx[0],int(statistics.mean(ctx)),sum(ctx),out)); kinds[agent]+=sum(ctx)
tot=sum(r[4] for r in rows)
print(f"subagent transcripts={len(rows)} calls={sum(r[1] for r in rows)} context_total={tot:,}")
print(f"floor mean={int(statistics.mean(r[2] for r in rows)):,} min={min(r[2] for r in rows):,} max={max(r[2] for r in rows):,}")
print(f"context/call mean={int(tot/sum(r[1] for r in rows)):,}")
for a,v in kinds.most_common(): print(f"  {a:32} {v:14,}  {v/tot*100:5.1f}%  n={sum(1 for r in rows if r[0]==a)} calls={sum(r[1] for r in rows if r[0]==a)}")