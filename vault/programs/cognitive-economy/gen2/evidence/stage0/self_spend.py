import json,glob,os,sys
d=os.path.expanduser(r"~\.claude\projects\C--Users-User--claude-skills-claude-power-pack")
sid="87601e81-fc6a-4199-a22a-3848715634a6"
# CE-T0a: flags used to be ignored, so `--session X` silently metered the hardcoded sid above.
# Only honoured when run as this script; tranche_driver.spend execs the source with sid=/d= rewritten.
a=sys.argv[1:] if os.path.basename(sys.argv[0])=="self_spend.py" else []
if "--session" in a: sid=a[a.index("--session")+1]
if "--dir" in a: d=a[a.index("--dir")+1]
files=[os.path.join(d,sid+".jsonl")]+glob.glob(os.path.join(d,sid,"**","*.jsonl"),recursive=True)
files=[f for f in files if os.path.exists(f)]
seen=set(); calls=0; ctx=0; out=0; sub=0; subctx=0
for f in files:
  for line in open(f,encoding="utf-8",errors="replace"):
    if '"usage"' not in line: continue
    try: e=json.loads(line)
    except ValueError: continue
    m=e.get("message") or {}; u=m.get("usage")
    if not u: continue
    k=m.get("id") or e.get("requestId")
    if k in seen: continue
    seen.add(k)
    c=(u.get("input_tokens") or 0)+(u.get("cache_creation_input_tokens") or 0)+(u.get("cache_read_input_tokens") or 0)
    calls+=1; ctx+=c; out+=u.get("output_tokens") or 0
    if "subagents" in f: sub+=1; subctx+=c
if not files: print("sid",sid,"files 0 calls None processed None (no transcript under",d+")")
else: print("sid",sid,"files",len(files),"calls",calls,"processed",f"{ctx+out:,}","(ctx",f"{ctx:,}","out",f"{out:,})","subagent calls",sub,"subagent ctx",f"{subctx:,}")
