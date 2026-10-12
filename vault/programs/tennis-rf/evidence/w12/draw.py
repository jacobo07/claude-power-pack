import json,random,os
# W12 draw: the W5a method (evidence/w5a/draw.py), seed 20261012, pool = W3 sample60 L1 rows minus the 12 W5a picks.
H=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S=os.path.join(H,"w3","sample60_table.md")
rows=[]
for l in open(S,encoding="utf-8"):
    c=[x.strip() for x in l.split("|")]
    if len(c)>8 and c[1].startswith("fn_"):
        rows.append(dict(fn=c[1],unit=c[2],insns=int(c[3]),shape=c[4],status=c[5],ut=int(c[6]),unk=int(c[7])))
prev=json.load(open(os.path.join(H,"w5a","draw.json"),encoding="utf-8"))
taken={r["fn"] for r in prev["clean"]+prev["few"]}
L1=[r for r in rows if r["status"]=="L1" and r["fn"] not in taken]
rnd=random.Random(20261012)
def strat(pool,n):
    pool=sorted(pool,key=lambda r:r["insns"]); n=min(n,len(pool)); k=len(pool)/n; out=[]
    for i in range(n):
        lo=int(i*k); hi=max(lo+1,int((i+1)*k)); out.append(rnd.choice(pool[lo:hi]))
    return out
pc=[r for r in L1 if r["ut"]==0]; pf=[r for r in L1 if r["ut"] in (1,2)]
clean=strat(pc,6); few=strat(pf,6)
out=dict(seed=20261012,method="w5a/draw.py strata by insns",pool_clean=len(pc),pool_few=len(pf),excluded_w5a=sorted(taken),clean=clean,few=few)
json.dump(out,open(os.path.join(H,"w12","draw.json"),"w",encoding="utf-8"),indent=1)
print("pool clean",len(pc),"few",len(pf))
for r in clean+few: print(r["fn"],r["insns"],r["ut"])
