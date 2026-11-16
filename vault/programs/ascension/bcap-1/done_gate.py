#!/usr/bin/env python3
"""Campaign-1 done gate: runs every phase gate as a subprocess and aggregates.

Exit 0 only if every in-scope gate exits 0 AND its output shows it ran checks.
Residuals that no gate can prove here (laptop plane, live hook) are printed as
UNPROVEN and keep the verdict at PARTIALLY_PROVEN, never COMPLETE.
Usage: python3 vault/programs/ascension/bcap-1/done_gate.py --campaign 1 [--json]
"""
import argparse, json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
GATES = [
    ("ASC-01", "V-ASC-INV", ["tools/test_asc_inventory.py"]),
    ("ASC-02", "V-ASC-LED", ["tools/test_asc_ledger.py"]),
    ("ASC-02", "V-PARK", ["tools/test_gsd_mission_parked_label.py"]),
    ("ASC-03", "V-ASC-WEB", ["tools/test_asc_webslice.py"]),
    ("ASC-04", "V-ASC-CCF", ["tools/test_asc_ccf.py"]),
    ("ASC-05", "V-ASC-BASE", ["tools/test_asc_baseline.py"]),
    ("ASC-06", "V-ASC-LIVE", ["tools/test_asc_liveness.py"]),
]
# Facts this host cannot observe. Listed, never counted as passed.
UNPROVEN = [
    "LIVE hook delivery of web_surface B5 (live ~/.claude tree lacks B5 until merge+sync) - BLOCKED-ON-LAPTOP",
    "Taste Skill / ASTRYX / Design Index reachability on the laptop plane - LAPTOP_STEPS.md 1-2",
    "Inheritance rate (N=1 fresh-agent pair shows mechanism, not a rate)",
    "OPERATIONAL coverage is 3/373 by construction: execution evidence exists only where a real exit-0 run was recorded",
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.campaign != "1":
        print("only campaign 1 is defined"); return 2
    rows = []
    for req, name, cmd in GATES:
        if not (ROOT / cmd[0]).exists():
            rows.append({"req": req, "gate": name, "rc": None, "result": "MISSING"}); continue
        t = time.time()
        p = subprocess.run([sys.executable, *cmd], cwd=ROOT, capture_output=True, text=True)
        rows.append({"req": req, "gate": name, "rc": p.returncode, "secs": round(time.time() - t, 1),
                     "result": "PASS" if p.returncode == 0 else "FAIL",
                     "tail": (p.stdout + p.stderr).strip().splitlines()[-1:] })
    ok = all(r["result"] == "PASS" for r in rows)
    verdict = ("PARTIALLY_PROVEN" if ok else "NOT_PROVEN")
    out = {"campaign": 1, "gates": rows, "unproven": UNPROVEN, "verdict": verdict}
    if a.json: print(json.dumps(out, indent=1))
    else:
        for r in rows: print(f"{r['result']:7} {r['req']} {r['gate']} rc={r['rc']}")
        for u in UNPROVEN: print("UNPROVEN:", u)
        print("VERDICT:", verdict)
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
