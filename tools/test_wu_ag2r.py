"""Gate for WU-AG2R: Part A rows are all dispositioned (no WAIT on W3, no reasonless UNKNOWN)."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IDS = """S-mission-a-minimum-done-gate S-mission-a-canaries S-mission-a-master-done-gate S-mission-a-objective-rewrite
S-a-g2-through-a-g5-recompilation S-mission-a-economic-done-gate S-part-a-reported-state S-phase-10-part-a-completion
S-a-g2-a-g3-learning-gate S-part-a-done-gate S-master-done-gate-part-a""".split()
P = ROOT / "vault/specs/gsdx-factory/partA/obligations.json"


def main() -> int:
    fails = []
    if not P.exists():
        print("FAIL partA/obligations.json missing")
        return 1
    d = json.loads(P.read_text(encoding="utf-8-sig"))
    if sorted(d.get("expect", [])) != sorted(IDS):
        fails.append("expect list != the 11 ids")
    with tempfile.TemporaryDirectory() as t:
        p = subprocess.run([sys.executable, str(ROOT / "tools/gsd_dossier.py"), "dispose", "--obligations", str(P),
                            "--out", t, "--repo", str(ROOT), "--check"], capture_output=True, text=True, timeout=300)
        print(p.stdout.strip())
        if p.returncode != 0:
            fails.append(f"dispose --check rc={p.returncode}")
        res = json.loads((Path(t) / "dispositions.json").read_text(encoding="utf-8"))
    for o in res["obligations"]:
        if o["disposition"] == "WAIT_DEPENDENCY" and "W3" in str(o.get("depends_on")):
            fails.append(f"{o['id']} still waits on W3")
        if o["disposition"] == "UNKNOWN" and not o.get("reason"):
            fails.append(f"{o['id']} UNKNOWN without reason")
    if len(res["obligations"]) != 11:
        fails.append("row count != 11")
    for f in fails:
        print("FAIL", f)
    print("PASS" if not fails else "FAILED")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
