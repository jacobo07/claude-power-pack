#!/usr/bin/env python3
"""WU-DOCTRINE done-gate. Re-runs `gsd_dossier dispose --check` on a COPY of l1/obligations.json and requires that
the 41 'doctrine without an enforcer' rows each carry a passing probe (REUSE_EXISTING / cmd_rc0 -> doctrine gate).
Fails on the pre-state (rows still CHEAP_COGNITION)."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
L1 = ROOT / "vault" / "specs" / "gsdx-factory" / "l1"
UNENFORCED = 41


def main() -> int:
    ob = json.loads((L1 / "obligations.json").read_text(encoding="utf-8-sig"))
    rows = ob["obligations"]
    rv = json.loads((L1 / "review.json").read_text(encoding="utf-8-sig"))
    doc = [r for r in rows if r["id"] in rv and rv[r["id"]].get("reason", "").startswith("DOCTRINE-ENFORCER")]
    bad = []
    if len(doc) != UNENFORCED:
        bad.append(f"expected {UNENFORCED} rows with a DOCTRINE-ENFORCER disposition, found {len(doc)}")
    for r in doc:
        ev = r.get("evidence") or []
        if r["claimed"] != "REUSE_EXISTING" or not any(e.get("kind") == "cmd_rc0" for e in ev):
            bad.append(f"{r['id']}: claimed={r['claimed']} without a cmd_rc0 gate probe")
    with tempfile.TemporaryDirectory() as td:
        cp = Path(td) / "obligations.json"
        cp.write_text(json.dumps(ob), encoding="utf-8")
        p = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "gsd_dossier.py"), "dispose", "--obligations",
                            str(cp), "--out", str(Path(td) / "out"), "--repo", str(ROOT), "--check"],
                           capture_output=True, text=True, errors="replace", timeout=600)
        print(p.stdout.strip().splitlines()[-1] if p.stdout.strip() else "no output", "rc=", p.returncode)
        res = json.loads((Path(td) / "out" / "dispositions.json").read_text(encoding="utf-8"))
        if p.returncode != 0:
            bad.append(f"dispose --check rc={p.returncode}")
        cheap = [o["id"] for o in res["obligations"] if o["disposition"] == "CHEAP_COGNITION" and "doctrine" in o["reason"]]
        if cheap:
            bad.append(f"{len(cheap)} rows still CHEAP_COGNITION doctrine-without-enforcer")
    # the gate the rows point to must itself bite: a mutated doctrine file must make it fail
    g = ROOT / "tools" / "gsdx_doctrine_gate.py"
    if not g.exists():
        bad.append("tools/gsdx_doctrine_gate.py missing")
    else:
        p = subprocess.run([sys.executable, "-I", str(g), "--selftest"], capture_output=True, text=True, timeout=300)
        if p.returncode != 0:
            bad.append(f"doctrine gate selftest rc={p.returncode}: {p.stdout.strip()[-200:]}")
    for b in bad:
        print("FAIL", b)
    print("WU-DOCTRINE", "FAIL" if bad else "PASS", f"rows={len(doc)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
