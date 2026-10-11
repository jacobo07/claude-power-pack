"""W7 step 1a: corpus for all 1,797 Tennis candidates (ids main:ADDR) so m2c_producer can run over every one. No compile."""
import json, sys
sys.path.insert(0, r"C:\Users\User\Apps\recon_work\wst_tennis\step0"); sys.path.insert(0, r"C:\Users\User\Apps\recon_work\wst_tennis\step1")
import probe_step1 as p1, probe_tennis as p0
rows = json.load(open(r"C:\Users\User\Apps\recon_work\wst_tennis\w3\tennis_fns.json"))
addr = p1.scan_graph(p0.SPORTS)[5]
out = open(r"C:\Users\User\Apps\recon_work\wst_tennis\w7\corpus.jsonl", "w")
miss = 0
for r in rows:
    a = addr.get(r["fn"])
    if a is None:
        miss += 1; continue
    h = "%08X" % a
    out.write(json.dumps({"id": "main:" + h, "module": "main", "kind": "FUNCTION", "name": r["fn"], "start": h}) + "\n")
print(len(rows), "rows; no address:", miss)
