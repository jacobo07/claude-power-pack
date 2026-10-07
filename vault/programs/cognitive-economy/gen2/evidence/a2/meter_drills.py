"""Mutation drills for the program meter (measure/attribute.py + stage0/self_spend.py).

Each drill mutates an isolated copy through tools/mutation_drill.py and requires the NAMED gate of
tools/test_ce_meter_truth.py to fail. Summary: METER_DRILL_KILLED=n/m (exit 0 only when every mutant is KILLED).
Run from anywhere: python vault/programs/cognitive-economy/gen2/evidence/a2/meter_drills.py
"""
import json, os, subprocess, sys, tempfile

W = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", ".."))
ATTR = "vault/programs/cognitive-economy/measure/attribute.py"
SELF = "vault/programs/cognitive-economy/gen2/evidence/stage0/self_spend.py"
TEST = "tools/test_ce_meter_truth.py"

DRILLS = [
    ("single-dir-attribute", ATTR, "V-METER-F1-FIND-ANY-DIR",
     "for pdir in [root] + sorted(d for d in root.iterdir() if d.is_dir()):",
     "for pdir in [root]:"),
    ("single-dir-selfspend", SELF, "V-METER-F1-SELFSPEND-ANY-DIR",
     'roots=[d]+[x for x in glob.glob(os.path.join(d,"*")) if os.path.isdir(x)]',
     "roots=[d]"),
    ("drop-text-only-from-session-total", ATTR, "V-METER-F2-TOTAL-INCLUDES-UNATTRIBUTED",
     'tot["processed"] += c["processed"]',
     'tot["processed"] += c["processed"] if c["tools"] else 0'),
    ("drop-unattributed-from-aggregate", ATTR, "V-METER-ATTRIBUTION-NEVER-REDUCES-TOTAL",
     '"total_processed": sum(t["processed"] for t in totals.values()),',
     '"total_processed": sum(s["processed"] for s in sessions.values()),'),
    ("null-as-zero", ATTR, "V-METER-MISSING-IS-UNKNOWN",
     'return {"sid": sid, "verdict": "UNKNOWN", "host": host, "why": where}',
     'return {"sid": sid, "verdict": "AGREE", "host": host, "calls": 0, "processed": 0}'),
    ("disagree-carries-number", ATTR, "V-METER-DISAGREE-NO-NUMBER",
     'elif (mine["calls"], mine["processed"]) != (other["calls"], other["processed"]):',
     "elif False:"),
]


def main() -> int:
    killed = 0
    with tempfile.TemporaryDirectory() as td:
        for name, f, gate, old, new in DRILLS:
            spec = os.path.join(td, f"{name}.json")
            with open(spec, "w", encoding="utf-8") as fh:
                json.dump({"file": f, "test": TEST, "gate": gate, "old": old, "new": new, "repo_root": W,
                           "copy_dirs": ["vault/programs/cognitive-economy"]}, fh)
            p = subprocess.run([sys.executable, os.path.join(W, "tools", "mutation_drill.py"), "--spec", spec], cwd=W,
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            verdict = next((l.strip() for l in reversed(p.stdout.splitlines()) if l.startswith("MUTANT")), f"rc={p.returncode}")
            print(f"{'PASS' if p.returncode == 0 else 'FAIL'} V-METER-DRILL-{name.upper()}  {verdict}")
            killed += p.returncode == 0
    print(f"METER_DRILL_KILLED={killed}/{len(DRILLS)}")
    return 0 if killed == len(DRILLS) else 1


if __name__ == "__main__":
    sys.exit(main())
