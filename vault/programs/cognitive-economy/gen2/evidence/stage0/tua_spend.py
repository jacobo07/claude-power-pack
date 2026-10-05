import glob,json,os,datetime as dt
A=dt.datetime(2026,10,5,11,13,2,tzinfo=dt.timezone.utc)
fs=glob.glob(os.path.join(os.path.expanduser(r"~\.claude\projects"),"*","242ae047*.jsonl"))
fs+= [g for f in fs for g in glob.glob(os.path.join(f[:-6],"**","*.jsonl"),recursive=True)]
seen=set(); pre=post=0; n=0
for f in fs:
  for line in open(f,encoding="utf-8",errors="replace"):
    if '"usage"' not in line: continue
    try: e=json.loads(line)
    except ValueError: continue
    m=e.get("message") or {}; u=m.get("usage")
    if not u or not e.get("timestamp"): continue
    k=m.get("id") or e.get("requestId")
    if k in seen: continue
    seen.add(k); t=sum(int(u.get(x) or 0) for x in ("input_tokens","cache_creation_input_tokens","cache_read_input_tokens","output_tokens"))
    if dt.datetime.fromisoformat(e["timestamp"].replace("Z","+00:00"))>=A: post+=t; n+=1
    else: pre+=t
print("files",len(fs),"[",", ".join(os.path.basename(os.path.dirname(f))[:40] for f in fs[:1]),"]","pre_anchor",f"{pre:,}","post_anchor",f"{post:,}","post_calls",n)