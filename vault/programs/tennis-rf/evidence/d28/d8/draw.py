import json,re,random,os,glob,sys
# D8 held-out draw. Seed 20261013, never redraw. Strata = D3 distance class 1,2,3, fixed allocation 14/16/10.
H=os.path.dirname(os.path.abspath(__file__)); E=os.path.dirname(H); W=os.path.normpath(os.path.join(E,"..",".."))  # fix: draw #0 had W=evidence/ so exclusion matched 0 files; never used, discarded before any send
SEED=20261013; ALLOC={1:14,2:16,3:10}
if os.path.exists(os.path.join(H,"draw.json")): sys.exit("draw.json exists: never redraw")
pat=re.compile(r"fn_[0-9A-Fa-f]{8}")
excl=set(); src=[]
# Receipt-named attribution sources only. D7 full_runs.json (population scan of all 263 lint-clean fns) and D2 shock_*.json
# (corpus-wide shock tables) are population scans, not attribution of single functions: not excluded (decision recorded here).
LIST=["evidence/w12/draw.json","evidence/d28/d2/causality.json","evidence/d28/d2/near_match.json","evidence/d28/d5/draw.json",
"evidence/d28/d5/causal_unlock.json","evidence/d28/d5/cror_unlock.json","evidence/d28/d6/variants.json","evidence/d28/d6/records.jsonl",
"evidence/d28/d6/full_var5_ptr_void.json","evidence/d28/d7/controls.json","evidence/d28/d7/replay.json"]
for p in [os.path.join(W,x) for x in LIST]+glob.glob(os.path.join(W,"evidence","w5a","*")):
    if os.path.isfile(p):
        t=open(p,encoding="utf-8",errors="replace").read(); f=set(pat.findall(t))
        if f:
            src.append((os.path.relpath(p,W),len(f))); excl|=f
R=[json.loads(l) for l in open(os.path.join(E,"d3","residuals.jsonl"),encoding="utf-8")]
rnd=random.Random(SEED); out=[]; pools={}
for d,n in ALLOC.items():
    pool=sorted([r for r in R if r["distance"]==d and r["fn"] not in excl and r["w12_verdict"] is None],key=lambda r:(r["size_insns"],r["fn"]))
    pools[d]=len(pool); print(d,len(pool),sum(1 for x in pool if x["lint_clean"]),sum(1 for x in pool if x["certified"]["motif_cover_insns"]>=x["size_insns"])); n=min(n,len(pool)); k=len(pool)/n
    for i in range(n):
        lo=int(i*k); hi=max(lo+1,int((i+1)*k)); r=rnd.choice(pool[lo:hi])
        out.append(dict(fn=r["fn"],distance=d,size_insns=r["size_insns"],lint_clean=r["lint_clean"],m2c_status=r["m2c_status"],motif_cover_insns=r["certified"]["motif_cover_insns"]))
assert len({o["fn"] for o in out})==len(out)
json.dump(dict(seed=SEED,alloc=ALLOC,method="stratified by D3 distance, within-stratum size-sorted equal bins, one seeded pick per bin",pools_after_exclusion=pools,n_excluded=len(excl),excl_sources=src,fns=out),open(os.path.join(H,"draw.json"),"w"),indent=1)
print(pools,len(excl)); 
for o in out: print(o)