import re,sys,glob,json,os
asm=os.environ.get("TENNIS_ASM","/home/kobii/missions/tennis-w11/wst_tennis/step0/split_sports/out/asm")
fns=sys.argv[1:]
want=set(fns)
for p in glob.glob(os.path.join(asm,"*.s")):
    cur=None;buf=[]
    for l in open(p,encoding="utf-8",errors="replace"):
        m=re.match(r'\.fn\s+"?([^",\s]+)',l)
        if m and m.group(1) in want: cur=m.group(1);buf=[]
        if cur: buf.append(l.rstrip())
        if cur and l.startswith(".endfn"):
            print("=====",cur);print("\n".join(re.sub(r'/\*.*?\*/\s*','',x) for x in buf));cur=None
