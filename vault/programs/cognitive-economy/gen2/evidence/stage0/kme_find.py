import json,glob,os,time
d=os.path.expanduser(r"~\.claude\projects\C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files")
cut=time.mktime((2026,10,3,0,0,0,0,0,-1))
for f in sorted(glob.glob(os.path.join(d,"*.jsonl")),key=os.path.getmtime):
  if os.path.getmtime(f)<cut: continue
  first=None; n=0; firstuser=None
  for i,line in enumerate(open(f,encoding="utf-8",errors="replace")):
    if firstuser is None and '"type":"user"' in line.replace(" ",""):
      try:
        e=json.loads(line); c=e["message"]["content"]; firstuser=(c if isinstance(c,str) else json.dumps(c))[:90]
      except Exception: pass
    if "m-2648e6c25747" in line:
      n+=1; first=first if first is not None else i
  if n: print(os.path.basename(f)[:8],"hits",n,"first_line",first,"|",(firstuser or "").replace("\n"," ")[:90])