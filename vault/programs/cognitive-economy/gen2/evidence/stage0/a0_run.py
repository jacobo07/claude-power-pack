import glob, io, json, os, re, contextlib, datetime as dt
EV=r"C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cognitive-economy\gen2\evidence\stage0"
IO=os.path.join(EV,"infinityops")
base=os.path.expanduser(r"~\.claude\projects")
ksr_p=os.path.join(base,"C--Users-User-Apps-recon-work-wt-keosdtk-home")
arm=dt.datetime(2026,10,3,19,40,tzinfo=dt.timezone.utc)
ksr_w=[]
for f in glob.glob(os.path.join(ksr_p,"*.jsonl")):
    first=None
    for line in open(f,encoding="utf-8",errors="replace"):
        if '"usage"' in line and '"timestamp"' in line:
            try: first=json.loads(line)["timestamp"]; break
            except Exception: continue
    if first and dt.datetime.fromisoformat(first.replace("Z","+00:00"))>=arm: ksr_w.append(os.path.basename(f)[:8])
loads={"ksr":(ksr_p,sorted(ksr_w)),
       "kme":(os.path.join(base,"C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files"),["67ca9fa1","41e4bea7","2f9049a0"])}
for name,(proj,w) in loads.items():
    out=os.path.join(EV,name+"_a0.txt"); buf=io.StringIO()
    buf.write(f"WORKLOAD {name} PROJ {proj}\nWORKERS {w}\n")
    for s in ("io_context_rent.py","io_attachments.py","io_subagents.py"):
        src=open(os.path.join(IO,s),encoding="utf-8").read()
        src=re.sub(r'^(PROJ|P)\s*=.*$', lambda m: f'{m.group(1)} = {proj!r}', src, count=1, flags=re.M)
        src=re.sub(r'^(WORKERS|W)\s*=\s*\[.*?\]', lambda m: f'{m.group(1)} = {w!r}', src, count=1, flags=re.M|re.S)
        buf.write(f"\n===== {s} =====\n")
        try:
            with contextlib.redirect_stdout(buf): exec(compile(src,s,"exec"),{"__name__":"__main__"})
        except Exception as e: buf.write(f"ERROR {type(e).__name__}: {e}\n")
    open(out,"w",encoding="utf-8").write(buf.getvalue()); print(name,len(w),"workers ->",out,len(buf.getvalue()),"chars")