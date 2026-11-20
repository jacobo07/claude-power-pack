#!/usr/bin/env python3
"""V-BURN-CENSUS gates for tools/burn_census.py (BAMR P5). Fixtures only; both poles of every judgement."""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import burn_census as bc  # noqa: E402

passes = fails = 0


def gate(name, cond, ev):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print("%s %s: %s" % ("PASS" if cond else "FAIL", name, ev))


def rec(mid, state, reason, tokens=None, origin="A", fp="A", measured=True):
    r = {"mission_id": mid, "state": state, "reason": reason, "epoch": 2, "progress_origin": origin,
         "progress": {"fp": fp, "measured": measured}}
    if tokens is not None:
        r["cost_mark"] = {"tokens": tokens}
    return r


recs = [rec("m-1", "HALTED", "no_progress: 3 epochs", 5_000_000),                 # spent, tree unchanged
        rec("m-2", "HALTED", "no_progress: 3 epochs", 1_000_000, fp="B"),         # spent, tree changed
        rec("m-3", "HALTED", "no_progress: 3 epochs"),                             # tokens unknown
        rec("m-4", "COMPLETED", "ALL_COMPLETE", 9_000_000, fp="C"),
        rec("m-5", "HALTED", "budget: older than 48.0 h", 2_000_000, measured=False)]
res = bc.census(recs)
top = res["classes"][0]
gate("V-BURN-RANK", top["cls"] == "HALTED | no_progress: N epochs" and top["no_change_tokens"] == 5_000_000,
     "unchanged-tree spend ranks first: %s %s" % (top["cls"], top["no_change_tokens"]))
gate("V-BURN-UNKNOWN-NOT-ZERO", top["tokens_unknown"] == 1 and top["tokens_measured"] == 6_000_000 and res["totals"]["tokens_unknown"] == 1,
     "a missing cost_mark is counted unknown, not as 0 tokens")
bud = [c for c in res["classes"] if c["cls"].startswith("HALTED | budget")][0]
gate("V-BURN-UNMEASURED-PROGRESS", bud["change_unknown"] == 1 and bud["no_change_tokens"] == 0,
     "progress.measured=False cannot be read as 'no progress'")
gate("V-BURN-CHANGED-NOT-BURN", [c for c in res["classes"] if c["cls"].startswith("COMPLETED")][0]["no_change_tokens"] == 0,
     "a mission whose tree changed contributes no no-change tokens")
gate("V-BURN-CLASS-MASK", bc.reason_class("HALTED", "worker m-0221f0c0e076 died after 12.5 h") ==
     bc.reason_class("HALTED", "worker m-01b37af0d384 died after 3 h"), "ids and numbers are masked into one class")

with tempfile.TemporaryDirectory() as tmp:
    for r in recs:
        json.dump(r, open(os.path.join(tmp, "gsd-mission-%s.json" % r["mission_id"]), "w"))
    open(os.path.join(tmp, "gsd-mission-bad.json"), "w").write("{nope")
    p = subprocess.run([sys.executable, os.path.join(HERE, "burn_census.py"), "--state-dir", tmp, "--json"],
                       capture_output=True, text=True)
    out = json.loads(p.stdout) if p.returncode == 0 else {}
    gate("V-BURN-CLI", out.get("totals", {}).get("missions") == 5 and out.get("unreadable_records") == 1,
         "process boundary: 5 records read, 1 unreadable reported (rc=%d)" % p.returncode)

print("BURN_CENSUS_PASS=%d/%d" % (passes, passes + fails))
sys.exit(0 if fails == 0 else 1)
