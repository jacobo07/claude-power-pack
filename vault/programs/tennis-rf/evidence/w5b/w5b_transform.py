import json,random,re,glob,os,sys
B=r"C:\Users\User\.claude\skills\claude-power-pack\vault\programs\tennis-rf"
S=B+r"\evidence\w3\sample60_table.md"; M=r"C:\Users\User\Apps\recon_work\wst_tennis\w3\m2c_out\c"
O=B+r"\evidence\w5b"; CL=B+r"\measure\claims.jsonl"
rows=[]
for l in open(S,encoding="utf-8"):
    c=[x.strip() for x in l.split("|")]
    if len(c)>8 and c[1].startswith("fn_"):
        rows.append(dict(fn=c[1],insns=int(c[3]),shape=c[4],status=c[5],ut=int(c[6]),unk=int(c[7])))
hard=[r for r in rows if r["status"]=="L1" and r["ut"]>=3]
print("hard pool",len(hard))
rnd=random.Random(20261012); hard.sort(key=lambda r:r["insns"]); k=len(hard)/6; pick=[]
for i in range(6):
    lo=int(i*k); hi=max(lo+1,int((i+1)*k)); pick.append(rnd.choice(hard[lo:hi]))
PROTO=re.compile(r'^(\S[^()=;]*?)\s+(fn_[0-9A-Fa-f]+)\(([^)]*)\);\s*/\* extern \*/',re.M)
DEF=re.compile(r'^(?!extern)(\S[^()=;]*?)\s+\*?(fn_[0-9A-Fa-f]+)\(([^)]*)\)\s*\{',re.M)
# claims: load existing (transform READS this file)
claims={}
if os.path.exists(CL):
    for l in open(CL):
        r=json.loads(l); claims[r["claim"]]=r
known={}
for p in glob.glob(M+r"\*.c"):
    t=open(p).read()
    for m in list(PROTO.finditer(t))+list(DEF.finditer(t)):
        if "?" not in m.group(1)+m.group(3): known.setdefault(m.group(2),(m.group(1),m.group(3)))
for n,c in claims.items():
    m=re.fullmatch(r"proto (fn_\w+)",n)
    if m: known[m.group(1)]=tuple(c["value"])
new=[];recs=[]
for r in pick:
    f=r["fn"]; t=open(M+r"\main_%s.c"%f[3:]).read(); ut0=t.count("?"); abst=[]; learned=[]
    def fix(m):
        rt,n,a=m.groups()
        if n in known: return "%s %s(%s); /* extern */"%(known[n][0],n,known[n][1])
        cs=re.findall(r"^\s*"+n+r"\(([^;]*)\);",t,re.M); allc=len(re.findall(n+r"\(",t))-1
        if cs and len(cs)==allc and len({len(c.split(",")) if c.strip() else 0 for c in cs})==1 and all(c.strip()=="" or all(re.fullmatch(r"-?(0x[0-9A-Fa-f]+|\d+)|arg\d+",x.strip()) for x in c.split(",")) for c in cs):
            kk=len(cs[0].split(",")) if cs[0].strip() else 0
            a2=", ".join(["s32"]*kk) if kk else "void"
            learned.append((n,("void",a2))); return "void %s(%s); /* extern, call-site inferred */"%(n,a2)
        abst.append(n); return m.group(0)
    t2=PROTO.sub(lambda m: fix(m) if "?" in m.group(1)+m.group(3) else m.group(0),t)
    for n,v in learned:
        key="proto "+n
        if key not in claims:
            claims[key]=dict(claim=key,value=list(v),evidence="call-site inference in %s (all calls literal/arg args, uniform arity)"%f,confidence="LOW: arity only, types s32 assumed, no oracle",invalidators="asm shows float/ptr args or return value used",consumers=["typerepair w5b transform"]); new.append(claims[key])
    open(O+r"\cand_%s.c"%f,"w").write(t2)
    recs.append(dict(fn=f,insns=r["insns"],unresolved_before=ut0,unresolved_after=t2.count("?"),abstained=abst,unk_fields=len(re.findall(r'unk[0-9A-F]+',t2)),claims_learned=[n for n,_ in learned],model_tokens="UNKNOWN",verdict="NOT_RUN_NO_ORACLE"))
os.makedirs(os.path.dirname(CL),exist_ok=True)
with open(CL,"w") as fh:
    for c in claims.values(): fh.write(json.dumps(c)+"\n")
json.dump(dict(seed=20261012,picks=pick,records=recs),open(O+r"\w5b_records.json","w"),indent=1)
for x in recs: print(x)
print("claims",len(claims),"new",len(new))
