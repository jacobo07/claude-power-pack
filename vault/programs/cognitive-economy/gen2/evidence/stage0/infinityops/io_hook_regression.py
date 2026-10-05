import glob, json, os
P = os.path.expanduser(r"~\.claude\projects\C--Users-User-Apps-io-device-trust")
W = ["be2a71eb","50d3a9f0","affe87e4","63bc3ed8","dc79aa64","5f5bc46f","4f1b398d","dfc0acda"]
K = ("input_tokens","cache_creation_input_tokens","cache_read_input_tokens")
X=[]; Y=[]
for w in W:
    f=glob.glob(os.path.join(P,f"{w}-*.jsonl"))[0]
    seen=set(); prev=None; acc=[0.0,0.0,0.0]
    for line in open(f,encoding="utf-8",errors="replace"):
        try: o=json.loads(line)
        except ValueError: continue
        m=o.get("message") or {}; u=m.get("usage"); t=o.get("type")
        if t=="assistant" and u:
            i=m.get("id") or o.get("uuid")
            if i in seen: continue
            seen.add(i); c=sum(int(u.get(k) or 0) for k in K)
            if prev is not None and acc!=[0,0,0]: X.append(acc[:]); Y.append(c-prev)
            prev=c; acc=[0.0,0.0,0.0]
            for b in (m.get("content") or []):
                if b.get("type")=="text": acc[0]+=len(b.get("text",""))
                elif b.get("type")=="tool_use": acc[0]+=len(json.dumps(b.get("input",{})))
        elif t=="user":
            c=m.get("content")
            acc[0]+= len(c) if isinstance(c,str) else len(json.dumps(c))
        elif t=="attachment":
            a=o.get("attachment") or {}; at=a.get("type","")
            if at=="prompt_snapshot": continue
            n=len(json.dumps(a))
            if at.startswith("hook_success"): acc[1]+=n
            else: acc[2]+=n
# OLS without intercept, 3 features, normal equations
import itertools
def dot(a,b): return sum(x*y for x,y in zip(a,b))
cols=list(zip(*X)); A=[[dot(cols[i],cols[j]) for j in range(3)] for i in range(3)]; bvec=[dot(cols[i],Y) for i in range(3)]
# solve 3x3
import copy
M=[A[i]+[bvec[i]] for i in range(3)]
for i in range(3):
    p=max(range(i,3),key=lambda r:abs(M[r][i])); M[i],M[p]=M[p],M[i]
    for r in range(3):
        if r!=i:
            f=M[r][i]/M[i][i]; M[r]=[a-f*b for a,b in zip(M[r],M[i])]
coef=[M[i][3]/M[i][i] for i in range(3)]
print(f"calls={len(Y)}  tokens per char: conversation={coef[0]:.3f}  hook_success={coef[1]:.3f}  other_attachments={coef[2]:.3f}")
print(f"chars totals: conversation={sum(cols[0]):,.0f} hook_success={sum(cols[1]):,.0f} other_att={sum(cols[2]):,.0f}; sum dY={sum(Y):,}")