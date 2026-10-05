import collections, datetime as dt, glob, json, os, statistics as st
PROJ=os.path.expanduser(r"~\.claude\projects\C--Users-User-Apps-recon-work-wt-keosdtk-home")
ARM=dt.datetime(2026,10,3,19,40,tzinfo=dt.timezone.utc)
seen=set(); seqs=collections.defaultdict(list)
for f in glob.glob(os.path.join(PROJ,"**","*.jsonl"),recursive=True):
    key_f=os.path.relpath(f,PROJ)
    for line in open(f,encoding="utf-8",errors="replace"):
        if '"usage"' not in line: continue
        try: e=json.loads(line)
        except ValueError: continue
        m=e.get("message") or {}; u=m.get("usage")
        if not u or not e.get("timestamp"): continue
        t=dt.datetime.fromisoformat(e["timestamp"].replace("Z","+00:00"))
        if t<ARM: continue
        k=m.get("id") or e.get("requestId")
        if k in seen: continue
        seen.add(k)
        ctx=(u.get("input_tokens") or 0)+(u.get("cache_creation_input_tokens") or 0)+(u.get("cache_read_input_tokens") or 0)
        seqs[key_f].append((t,ctx,u.get("output_tokens") or 0))
rows=[]; allc=[]
for k,s in seqs.items():
    s.sort(); c=[x[1] for x in s]; allc+=c
    rows.append((k,len(c),c[0],st.median(c),max(c),sum(c)))
n=len(allc); tot=sum(allc)
firsts=[r[2] for r in rows]
floor=st.median(firsts)
print("transcripts",len(rows),"calls",n,"ctx_total",f"{tot:,}")
print("first-call median",f"{floor:,.0f}","p25/p75",f"{st.quantiles(firsts,n=4)[0]:,.0f}",f"{st.quantiles(firsts,n=4)[2]:,.0f}")
print("per-call median",f"{st.median(allc):,.0f}","mean",f"{tot/n:,.0f}")
lens=sorted(r[1] for r in rows); print("calls/transcript median",st.median(lens),"max",lens[-1],"n>=50",sum(1 for l in lens if l>=50))
big=sorted(rows,key=lambda r:-r[5])[:6]
for r in big: print("T",r[0][:60],"calls",r[1],"first",f"{r[2]:,}","med",f"{r[3]:,.0f}","max",f"{r[4]:,}","sum",f"{r[5]:,}")
# floor vs growth share: sum over calls of min(ctx, first) vs excess
fl=sum(min(c,s[0][1]) for k,s in seqs.items() for (_,c,_) in s); print("floor share",f"{fl/tot:.1%}","growth share",f"{1-fl/tot:.1%}")
# ceiling: fresh worker every N calls, capsule S tokens replaces accumulated growth
for N in (10,20,40):
  for S in (10000,30000):
    cf=0
    for k,s in seqs.items():
        f0=s[0][1]
        for i,(_,c,_) in enumerate(s):
            seg=(i//N)*N; base=s[seg][1]
            cf+= c if seg==0 else min(c, f0+S+(c-base))
    print(f"N={N} S={S//1000}k counterfactual {cf/1e6:.1f}M vs {tot/1e6:.1f}M -> ceiling {1-cf/tot:.1%}")