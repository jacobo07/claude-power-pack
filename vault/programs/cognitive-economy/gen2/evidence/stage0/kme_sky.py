import glob, json, os, statistics as st
d=os.path.expanduser(r"~\.claude\projects\C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files")
seen=set(); per={}
for sid8 in ("67ca9fa1","41e4bea7","2f9049a0"):
  main=glob.glob(os.path.join(d,sid8+"*.jsonl"))[0]; sid=os.path.basename(main)[:-6]
  for g in [main]+glob.glob(os.path.join(d,sid,"**","*.jsonl"),recursive=True):
    s=[]
    for line in open(g,encoding="utf-8",errors="replace"):
      if '"usage"' not in line: continue
      try: e=json.loads(line)
      except ValueError: continue
      m=e.get("message") or {}; u=m.get("usage")
      if not u: continue
      k=m.get("id") or e.get("requestId")
      if k in seen: continue
      seen.add(k)
      s.append((e.get("timestamp",""),(u.get("input_tokens") or 0)+(u.get("cache_creation_input_tokens") or 0)+(u.get("cache_read_input_tokens") or 0),u.get("output_tokens") or 0))
    if s: s.sort(); per[g]=s
  sub=[c for g,s in per.items() if sid in g for _,c,_ in s]
  print(sid8,"calls",len(sub),"ctx",f"{sum(sub):,}")
allc=[c for s in per.values() for _,c,_ in s]; out=sum(o for s in per.values() for *_,o in s)
print("TOTAL transcripts",len(per),"calls",len(allc),"ctx",f"{sum(allc):,}","out",f"{out:,}","median",f"{st.median(allc):,.0f}","first-call median",f"{st.median([s[0][1] for s in per.values()]):,.0f}")
ts=sorted(t for s in per.values() for t,_,_ in s if t); print("span",ts[0],ts[-1])
fl=sum(min(c,s[0][1]) for s in per.values() for _,c,_ in s); print("floor share",f"{fl/sum(allc):.1%}")