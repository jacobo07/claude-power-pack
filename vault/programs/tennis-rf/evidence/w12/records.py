# W12 records from the judged candidate ledger (job 3 ksrmb-20261012-171117). Deterministic: reads the ledger and the
# two draws, writes evidence/w12/measure/records.jsonl and prints the rate table that MEASURE.md quotes.
# Usage: python records.py <candidate_ledger.jsonl>
import collections, json, os, sys

JOB = "ksrmb-20261012-171117"
HERE = os.path.dirname(os.path.abspath(__file__))
EXCLUDED = {"fn_8021EAA8": "unk14", "fn_8022F90C": ".unk2A"}  # W12-prep: lint UNK_FIELD, not sent

def groups():
    g = {}
    for path in (os.path.join(HERE, "..", "w5a", "draw.json"), os.path.join(HERE, "draw.json")):
        d = json.load(open(path, encoding="utf-8"))
        for grp in ("clean", "few"):
            for row in d[grp]:
                g[row["fn"]] = (grp, row["insns"], row.get("shape"))
    return g

def main(led):
    rows = [json.loads(l) for l in open(led, encoding="utf-8") if l.strip()]
    rows = [r for r in rows if r.get("job_id") == JOB]
    by = collections.defaultdict(list)
    for r in rows:
        by["fn_" + r["entity"].split(":")[1]].append(r)
    g = groups()
    out, tally, preset_match = [], collections.Counter(), collections.Counter()
    donors = sorted(f for f, rs in by.items() if all(r.get("producer") == "w10c_donor" for r in rs))
    for fn in sorted(g):
        grp, insns, shape = g[fn]
        rec = {"fn": fn, "group": grp, "insns": insns, "shape_hint": shape, "layer": "M2C_TENNIS_CONTEXT",
               "model_calls": 0, "tokens": "UNKNOWN (one shared worker session, 3,453,372 processed for all of W12)",
               "job": JOB}
        if fn in EXCLUDED:
            rec.update(verdict="EXCLUDED_LINT_UNK_FIELD", compiles="NOT_SENT", note=EXCLUDED[fn])
        else:
            rs = by[fn]
            for r in rs:
                if r.get("exact_match"):
                    preset_match[r.get("preset")] += 1
            best = max(rs, key=lambda r: (bool(r.get("exact_match")), (r.get("objdiff_result") or {}).get("match_percent") or -1))
            mp = (best.get("objdiff_result") or {}).get("match_percent")
            o2 = best.get("oracle2")
            o2 = o2.get("verdict") if isinstance(o2, dict) else o2
            if best.get("exact_match"):
                verdict = "MATCH"
            elif best.get("runner_status") == "COMPILE_FAILED":
                verdict = "FAIL BLOCKED_CONTEXT"
            else:
                verdict = "PARTIAL %.1f%% (%s, %s)" % (mp, best.get("miss_class"), o2)
            rec.update(verdict=verdict, compiles=best.get("runner_status") != "COMPILE_FAILED", best_preset=best.get("preset"),
                       units=[{"preset": r.get("preset"), "exact": r.get("exact_match"),
                               "match_percent": (r.get("objdiff_result") or {}).get("match_percent"),
                               "row_hash": r.get("row_hash")} for r in rs])
        tally[(grp, rec["verdict"].split(" ")[0])] += 1
        out.append(rec)
    os.makedirs(os.path.join(HERE, "measure"), exist_ok=True)
    with open(os.path.join(HERE, "measure", "records.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for rec in out:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
    print("ledger rows for job", len(rows), "donor controls", donors,
          "donor MATCH", sum(1 for f in donors if all(r.get("exact_match") for r in by[f])))
    print("records", len(out))
    for grp in ("clean", "few"):
        n = sum(v for (gg, _), v in tally.items() if gg == grp)
        print(grp, "n=%d" % n, {k[1]: v for k, v in tally.items() if k[0] == grp})
    print("exact-match units by preset", dict(preset_match))
    sent = [r for r in out if r["verdict"] != "EXCLUDED_LINT_UNK_FIELD"]
    m = sum(1 for r in out if r["verdict"] == "MATCH")
    print("RATE sent=%d/%d drawn=%d/%d" % (m, len(sent), m, len(out)))

if __name__ == "__main__":
    main(sys.argv[1])
