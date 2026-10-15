"""D8v2: re-judge job 5's RETURNED objects with oracle2 against the batch's own L0 (w8/inputs/tennis_L0.jsonl).

The ledger judge (candidate.py judge) ran oracle2 against the profile L0 (w10/factory/corpus/tennis_L0.jsonl, 25 rows,
the W12 draw only), so every held-out unit came back ORACLE_REFUSED "L0 row is None". The ledger is an append-only
chain with no supersede path, so its 31 rows are kept as written; this script writes a SEPARATE judgment.
Same returned bytes (rederive re-hashes them), same oracle2, same classify_unit; only l0_path differs.
usage (env KSR_CAPSULE_PROFILE=tennis, MATCH_ACCEL_GEX44=<Tennis F root>, cwd = the gex44 tool dir):
    python rejudge_l0.py <job_id> <l0.jsonl> <out.json>"""
import json, sys
sys.path.insert(0, ".")
import candidate as C, reproduce, stage

job_id, l0, out_path = sys.argv[1:4]
found = stage.find_job_record(job_id)
if not found:
    sys.exit("no local job record names %s" % job_id)
job = reproduce.load_job(found[0].parent)
tree = stage.gex44_root() / "returns" / job_id
out = reproduce.out_dir_of(tree)
receipt = reproduce._load(out / "receipt.json")
rows_by = dict((r.get("unit_id"), r) for r in ((receipt.get("results") or {}).get("units") or []) if isinstance(r, dict))
l0_rows = dict((r["id"], r) for r in (json.loads(x) for x in open(l0, encoding="utf-8") if x.strip()))
units = []
for unit in job["task"]["units"]:
    row = rows_by.get(unit["unit_id"])
    d = C.rederive(out, unit, row)
    if d["disagrees"]:
        units.append({"unit_id": unit["unit_id"], "class": "INVALID_CUSTODY", "disagrees": d["disagrees"]})
        continue
    o2 = C.oracle2(d["object"], unit["symbol"], unit["entity"], C.asm_unit_of(unit["target_obj"]), l0_path=l0) \
        if d["object"] is not None else None
    c = C.classify_unit(unit, row, d, o2)
    units.append({"unit_id": unit["unit_id"], "entity": unit["entity"], "preset": unit["preset"],
                  "producer": unit["producer"], "insns": (l0_rows.get(unit["entity"]) or {}).get("insns"),
                  "class": c["class"], "rule": c["rule"], "oracle2": (o2 or {}).get("verdict"), "oracle2_detail": (o2 or {}).get("detail")})
json.dump({"job_id": job_id, "l0": l0, "units": units}, open(out_path, "w", encoding="utf-8", newline="\n"), indent=1)
for u in units:
    print(u["unit_id"], u.get("insns"), u["class"], u.get("objdiff"), u.get("oracle2"))
