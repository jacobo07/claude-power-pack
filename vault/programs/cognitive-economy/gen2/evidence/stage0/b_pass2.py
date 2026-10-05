"""B pass 1 -- zero-model call-elimination ceiling. A model call (assistant message, deduped by id) is
CLEAR when every tool_use in it is mechanical (status/list/poll/sleep/existence/unchanged reread/task-output
poll) and its visible text is short; TESTRUN when it only invokes a known test/gate command (POTENTIAL);
ASSURANCE when it spawns a reviewer/verifier/checker agent; END when it has no tool_use (turn closer);
else MODEL. Cost of a call = its processed tokens (input+cache_write+cache_read+output)."""
import glob, json, os, re, sys
from collections import Counter, defaultdict
base=os.path.expanduser(r"~\.claude\projects")
W={"infinityops":("C--Users-User-Apps-io-device-trust",["be2a71eb","50d3a9f0","affe87e4","63bc3ed8","dc79aa64","5f5bc46f","4f1b398d","dfc0acda"]),
   "ksr":("C--Users-User-Apps-recon-work-wt-keosdtk-home",["2fe0f58c","61dad5d8","850791eb","968c93b1","9a585a1f","af96e154","faf821d9"]),
   "kme":("C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files",["67ca9fa1","41e4bea7","2f9049a0"])}
K=("input_tokens","cache_creation_input_tokens","cache_read_input_tokens","output_tokens")
MECH_CMD=re.compile(r"^\s*(?:\$\w+\s*=\s*['\"][^'\"]*['\"]\s*$|&\s*(?:['\"][^'\"]*git(?:\.exe)?['\"]|\$\w+|\S*git(?:\.exe)?)|git)\s+(?:-C\s+\S+\s+)?(?:status|log|diff\s+--stat|rev-parse|branch|show\s+--stat)\b|"
  r"^\s*(?:ls|dir|pwd|Get-ChildItem|Test-Path|Get-Item|Get-Process|Get-Date|Start-Sleep|sleep|wc|Measure-Object|echo|Write-Output|cat\s+\S+\s*$|Get-Content\s+.*-Tail)\b",re.I)
TEST_CMD=re.compile(r"\b(pytest|python\S*\s+\S*test_\S+\.py|mvn\s+.*test|npm\s+(run\s+)?test|node\s+\S*test|mix\s+test|vitest|jest|tsc\s+--noEmit|--selftest|--final)\b",re.I)
MECH_TOOLS={"TaskOutput","BashOutput","TaskList","TaskGet","TodoWrite","TaskUpdate","TaskCreate","ToolSearch","Glob"}
ASSUR=re.compile(r"review|verif|check|audit",re.I)
def classify(blocks, readstate):
    uses=[b for b in blocks if b.get("type")=="tool_use"]
    text=sum(len(b.get("text","")) for b in blocks if b.get("type")=="text")
    if not uses: return "END"
    kinds=[]
    for u in uses:
        n=u.get("name",""); i=u.get("input") or {}
        if n in ("Bash","PowerShell"):
            c=i.get("command","")
            parts=[p for p in re.split(r";|&&|\|\||\n",c) if p.strip()]
            if parts and all(MECH_CMD.search(p) for p in parts): kinds.append("CLEAR")
            elif TEST_CMD.search(c): kinds.append("TESTRUN")
            else: kinds.append("MODEL")
        elif n=="Read":
            p=i.get("file_path"); kinds.append("CLEAR" if p in readstate and readstate[p]=="clean" else "MODEL"); readstate[p]="clean"
        elif n in ("Edit","Write","MultiEdit","NotebookEdit"):
            readstate[i.get("file_path")]="dirty"; kinds.append("MODEL")
        elif n in ("Agent","Task"):
            kinds.append("ASSURANCE" if ASSUR.search((i.get("subagent_type") or "")+" "+(i.get("description") or "")) else "MODEL")
        elif n in MECH_TOOLS: kinds.append("CLEAR")
        else: kinds.append("MODEL")
    if "MODEL" in kinds: return "MODEL"
    if "ASSURANCE" in kinds: return "ASSURANCE"
    if "TESTRUN" in kinds: return "TESTRUN"
    return "CLEAR" if text<=400 else "MODEL"
out=[]
for name,(pd,ws) in W.items():
    P=os.path.join(base,pd); cnt=Counter(); tok=Counter(); files=[]
    for w in ws:
        f=glob.glob(os.path.join(P,f"{w}-*.jsonl"))[0]; sid=os.path.basename(f)[:-6]
        files.append(("main",f)); files+= [("sub",g) for g in glob.glob(os.path.join(P,sid,"subagents","*.jsonl"))]
    for kind,f in files:
        seen={}; order=[]; rs={}
        for line in open(f,encoding="utf-8",errors="replace"):
            try: o=json.loads(line)
            except ValueError: continue
            m=o.get("message") or {}
            if o.get("type")!="assistant" or not m.get("usage"): continue
            i=m.get("id") or o.get("uuid")
            if i not in seen: seen[i]={"u":m["usage"],"b":[]}; order.append(i)
            seen[i]["b"]+= [b for b in (m.get("content") or []) if isinstance(b,dict)]
            seen[i]["u"]=m["usage"]
        for i in order:
            c=classify(seen[i]["b"],rs); t=sum(int(seen[i]["u"].get(k) or 0) for k in K)
            cnt[(kind,c)]+=1; tok[(kind,c)]+=t
    N=sum(cnt.values()); T=sum(tok.values())
    out.append(f"== {name}: calls={N:,} processed={T:,}")
    for c in ("CLEAR","TESTRUN","ASSURANCE","END","MODEL"):
        n=sum(v for (k,cc),v in cnt.items() if cc==c); t=sum(v for (k,cc),v in tok.items() if cc==c)
        nm=cnt[("main",c)]; ns=cnt[("sub",c)]
        out.append(f"  {c:9} calls={n:5,} ({n/N:5.1%})  processed={t:13,} ({t/T:5.1%})  main={nm} sub={ns}")
s="\n".join(out); print(s)
open(r"C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cognitive-economy\gen2\evidence\stage0\b_pass2.txt","w",encoding="utf-8").write(__doc__+"\n"+s+"\n")