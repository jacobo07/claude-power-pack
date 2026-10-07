import json,glob,os,sys
from datetime import datetime
d=os.path.expanduser(r"~\.claude\projects")
sid="87601e81-fc6a-4199-a22a-3848715634a6"
# CE-T0a: flags used to be ignored, so `--session X` silently metered the hardcoded sid above.
# Only honoured when run as this script; tranche_driver.spend execs the source with sid=/d= rewritten.
# M1: d is searched as a projects root (d and every dir under it), so a session filed under any project dir is found;
# tranche_driver narrows d to one project dir. Zero transcripts -> UNKNOWN, never 0 (non-zero exit when run as a script).
a=sys.argv[1:] if os.path.basename(sys.argv[0])=="self_spend.py" else []
if "--session" in a: sid=a[a.index("--session")+1]
if "--dir" in a: d=a[a.index("--dir")+1]
until=None
if "--until" in a: until=datetime.fromisoformat(a[a.index("--until")+1].replace("Z","+00:00")).timestamp()
roots=[d]+[x for x in glob.glob(os.path.join(d,"*")) if os.path.isdir(x)]
found={}
for r in roots:
  for f in [os.path.join(r,sid+".jsonl")]+glob.glob(os.path.join(r,sid,"**","*.jsonl"),recursive=True):
    if os.path.exists(f): found[os.path.realpath(f)]=f
files=[found[k] for k in sorted(found)]
seen=set(); calls=0; ctx=0; out=0; sub=0; subctx=0; torn=0; nousage=0; undated=0
for f in files:
  for n,line in enumerate(open(f,encoding="utf-8",errors="replace")):
    if not line.strip(): continue
    try: e=json.loads(line)
    except ValueError: torn+=1; continue
    if not isinstance(e,dict) or e.get("type")!="assistant": continue
    m=e.get("message") if isinstance(e.get("message"),dict) else {}
    k=m.get("id") or e.get("requestId") or (f,n)
    if k in seen: continue
    seen.add(k)
    if until is not None:
      try:
        if datetime.fromisoformat(str(e.get("timestamp")).replace("Z","+00:00")).timestamp()>until: continue
      except ValueError: undated+=1
    u=m.get("usage")
    if not isinstance(u,dict) or all(u.get(x) is None for x in ("input_tokens","cache_creation_input_tokens","cache_read_input_tokens","output_tokens")): nousage+=1; continue
    c=(u.get("input_tokens") or 0)+(u.get("cache_creation_input_tokens") or 0)+(u.get("cache_read_input_tokens") or 0)
    calls+=1; ctx+=c; out+=u.get("output_tokens") or 0
    if "subagents" in f: sub+=1; subctx+=c
if not files:
  print("sid",sid,"files 0 calls UNKNOWN processed UNKNOWN (no transcript under",d+")")
  if a: sys.exit(2)
else: print("sid",sid,"files",len(files),"calls",calls,"processed",f"{ctx+out:,}","(ctx",f"{ctx:,}","out",f"{out:,})","subagent calls",sub,"subagent ctx",f"{subctx:,}","torn",torn,"nousage",nousage,"undated",undated)
