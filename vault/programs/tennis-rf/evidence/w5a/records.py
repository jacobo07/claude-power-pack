import json
D=r"C:\Users\User\.claude\skills\claude-power-pack\vault\programs\tennis-rf\evidence\w5a"
dr=json.load(open(D+r"\draw.json")); tr={r["fn"]:r for r in json.load(open(D+r"\transform.json"))}
model={"fn_80254440":"vtable calls + 7 unk fields","fn_80252F34":"'?' return + 5 unk fields"}
out=[]
for grp in("clean","few"):
    for r in dr[grp]:
        f=r["fn"];t=tr[f]
        layer="MODEL" if f in model else "DET_TYPE_REPAIR"
        out.append(dict(fn=f,group=grp,insns=r["insns"],shape_hint=r["shape"],layer=layer,
          verdict="UNJUDGED_NO_ORACLE",compiles="UNKNOWN",model_calls=0 if layer!="MODEL" else 1,
          tokens="UNKNOWN",proof_cost=("PMN: "+model[f]) if f in model else None,
          unresolved_before=t["unresolved_before"],unresolved_after=t["unresolved_after"] if layer!="MODEL" else 0,
          unk_fields_left=t["unk_fields"],donor_proven=False,no_work=False,
          note="call-site-inferred prototypes unverified vs asm" if t["unresolved_before"] else ""))
open(D+r"\measure\records.jsonl","w").write("\n".join(json.dumps(x) for x in out)+"\n")
print(len(out))