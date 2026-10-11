import importlib.util, json, collections, os, re
spec=importlib.util.spec_from_file_location("pt", r"C:\Users\User\Apps\recon_work\wst_tennis\step0\probe_tennis.py")
pt=importlib.util.module_from_spec(spec); spec.loader.exec_module(pt)
OUT=r"C:\Users\User\Apps\recon_work\wst_tennis\w3"
sf,sstr,srefs,sunit=pt.scan(pt.SPORTS)
rf,_,_,_=pt.scan(pt.RESORT)
units=["auto_03_801BC5B8_text.s","auto_03_80202950_text.s","auto_03_8023FE44_text.s","auto_03_80257B08_text.s","auto_03_80278300_text.s","auto_03_8032BC4C_text.s"]
tf=sorted(fn for fn,u in sunit.items() if u in units and fn in sf)
rex=collections.defaultdict(list); rlo=collections.defaultdict(list)
for fn,b in rf.items():
    if b:
        e,l=pt.shapes(b); rex[e].append(fn); rlo[l].append(fn)
proven=set()
for l in open(r"C:\Users\User\Apps\recon_work\decomp_factory\levels\levels.jsonl",encoding="utf-8"):
    r=json.loads(l)
    if r["dimensions"]["SRC"]["verdict"]=="PROVEN": proven.add(r["name"])
# call graph
CALL=re.compile(r'\bbl\s+(fn_[0-9A-Fa-f]+)')
fanout={fn:len(set(CALL.findall("\n".join(sf[fn])))) for fn in tf}
fanin=collections.Counter()
for fn in sf:
    for c in set(CALL.findall("\n".join(sf[fn]))): fanin[c]+=1
rows=[]
for fn in tf:
    b=sf[fn]
    if not b: continue
    e,l=pt.shapes(b)
    m="exact" if e in rex else ("loose" if l in rlo else "none")
    donors=rex.get(e,[]) if m=="exact" else rlo.get(l,[]) if m=="loose" else []
    rows.append(dict(fn=fn,unit=sunit[fn],insns=len(b),match=m,donors=donors[:5],donor_proven=[d for d in donors if d in proven][:5],fanin=fanin[fn],fanout=fanout[fn]))
json.dump(rows,open(OUT+r"\tennis_fns.json","w"),indent=0)
c=collections.Counter(r["match"] for r in rows)
print(len(rows),c, "exact with proven donor:",sum(1 for r in rows if r["donor_proven"]))
for r in rows:
    if r["donor_proven"]: print(r["fn"],r["unit"],r["insns"],r["donor_proven"],len(r["donors"]))