import json,random,re,sys
S=r"C:\Users\User\.claude\skills\claude-power-pack\vault\programs\tennis-rf\evidence\w3\sample60_table.md"
rows=[]
for l in open(S,encoding="utf-8"):
    c=[x.strip() for x in l.split("|")]
    if len(c)>8 and c[1].startswith("fn_"):
        rows.append(dict(fn=c[1],unit=c[2],insns=int(c[3]),shape=c[4],status=c[5],ut=int(c[6]),unk=int(c[7])))
L1=[r for r in rows if r["status"]=="L1"]
rnd=random.Random(20261011)
def strat(pool,n):
    pool=sorted(pool,key=lambda r:r["insns"]); k=len(pool)/n; out=[]
    for i in range(n):
        lo=int(i*k); hi=max(lo+1,int((i+1)*k)); out.append(rnd.choice(pool[lo:hi]))
    return out
clean=strat([r for r in L1 if r["ut"]==0],6)
few=strat([r for r in L1 if r["ut"] in(1,2)],6)
json.dump(dict(seed=20261011,clean=clean,few=few),open(r"C:\Users\User\.claude\skills\claude-power-pack\vault\programs\tennis-rf\evidence\w5a\draw.json","w"),indent=1)
for r in clean+few: print(r)
