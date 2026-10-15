import json,collections
sp=json.load(open('split_lbl_80513E74.json')); a=json.load(open('arm2_hdr_e74_v1.h.json'))
CL={'C0004','C0001','C0035','C0585','C4246'}  # clusters whose root is lbl_80513E74 (or its fields)
rows={}
for l in open('../d12/residuals_v1.jsonl'):
    r=json.loads(l); rows[r['fn']]=r
out={}
for nm,S in (('in_sample',sp['pack']),('held_out',sp['held_out'])):
    before=after=moved=zero=0
    for f in S:
        v=rows[f]['unresolved_vars']; b=len(v)
        keep=[x for x in v if not (x.get('cluster') in CL)]
        before+=b; after+=len(keep); moved+= (len(keep)<b); zero+= (len(keep)==0)
    out[nm]=dict(n=len(S),vars_before=before,vars_after=after,fns_with_fewer_vars=moved,fns_zero_vars_left=zero,
        newly_lint_clean=len(a[nm]['newly_clean']),new_lint_regressions=a[nm]['errors'])
print(json.dumps(out)); json.dump(out,open('arm2_e74_ladder.json','w'),indent=1)