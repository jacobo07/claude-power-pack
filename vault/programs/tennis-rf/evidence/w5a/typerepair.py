import re,glob,json,os
M=r"C:\Users\User\Apps\recon_work\wst_tennis\w3\m2c_out\c"
D=r"C:\Users\User\.claude\skills\claude-power-pack\vault\programs\tennis-rf\evidence\w5a"
draw=json.load(open(D+r"\draw.json"))
fns=[r["fn"] for r in draw["clean"]+draw["few"]]
PROTO=re.compile(r'^(\S[^()=;]*?)\s+(fn_[0-9A-Fa-f]+)\(([^)]*)\);\s*/\* extern \*/',re.M)
DEF=re.compile(r'^(?!extern)(\S[^()=;]*?)\s+\*?(fn_[0-9A-Fa-f]+)\(([^)]*)\)\s*\{',re.M)
known={}
for p in glob.glob(M+r"\*.c"):
    t=open(p).read()
    for m in PROTO.finditer(t):
        if "?" not in m.group(1)+m.group(3): known.setdefault(m.group(2),(m.group(1),m.group(3)))
    for m in DEF.finditer(t):
        if "?" not in m.group(1)+m.group(3): known.setdefault(m.group(2),(m.group(1),m.group(3)))
out=[];recs=[]
for f in fns:
    t=open(M+r"\main_%s.c"%f[3:]).read()
    ut0=t.count("?"); abst=[]
    def fix(m):
        r,n,a=m.groups()
        if n in known: return "%s %s(%s); /* extern */"%(known[n][0],n,known[n][1])
        cs=re.findall(r"^\s*"+n+r"\(([^;]*)\);",t,re.M); allc=len(re.findall(n+r"\(",t))-1
        if cs and len(cs)==allc and all(c.strip()=="" or all(re.fullmatch(r"-?(0x[0-9A-Fa-f]+|\d+)|arg\d+",x.strip()) for x in c.split(",")) for c in cs) and len({len(c.split(",")) if c.strip() else 0 for c in cs})==1:
            k=len(cs[0].split(",")) if cs[0].strip() else 0
            return "void %s(%s); /* extern, call-site inferred */"%(n,", ".join(["s32"]*k) if k else "void")
        # abstain unless 'void' result inferred: caller ignores result and args are literals
        abst.append(n); return m.group(0)
    t2=PROTO.sub(lambda m: fix(m) if "?" in m.group(1)+m.group(3) else m.group(0),t)
    # unk fields -> byte-offset casts only for simple arg->unkN (type unknown => abstain on non-int width)
    unk=len(re.findall(r'unk[0-9A-F]+',t2))
    open(D+r"\cand_%s.c"%f,"w").write(t2)
    recs.append(dict(fn=f,unresolved_before=ut0,unresolved_after=t2.count("?"),abstained=abst,unk_fields=unk,resolved_from_signatures=sorted(set(re.findall(r'fn_[0-9A-F]+',t))-set(abst)&set(known))))
json.dump(recs,open(D+r"\transform.json","w"),indent=1)
for r in recs: print(r)
