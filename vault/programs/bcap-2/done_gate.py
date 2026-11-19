"""BCAP-2 closeout gate (Phase 10). Aggregates the item gates, liveness for the modules this campaign added, and the ledger rows.
Exit 0 means the campaign is CONSISTENT AND HONEST (every gate that exists passes, no BCAP-2 module is an undeclared orphan, no item claims
more than PARTIALLY_PROVEN where residuals are recorded). It does NOT mean any backlog is ACTIVATED: plan law 4 needs each backlog's own criteria.
python3 vault/programs/bcap-2/done_gate.py [--json]"""
import json, os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
CANDIDATES = ["/home/kobii/w4-gate/venv/bin/python3", "/home/kobii/costaluz-pgtest/venv/bin/python3"]  # read-only use as interpreter; need pytest+coverage+pytest_cov
ITEMS = [  # id, backlog, gate script (None = no code gate: scan-only phase), verdict
    ("BCAP2-01", "CPP-DBG-001", "tools/test_bcap2_dbg.py"), ("BCAP2-02", "CPP-TDD-001", "tools/test_bcap2_tdd.py"),
    ("BCAP2-03", "CPP-AGSK-001", "tools/test_bcap2_agsk.py"), ("BCAP2-04", "Anime.js", "tools/test_bcap2_animejs.py"),
    ("BCAP2-05", "Synsation", "tools/test_bcap2_synsation.py"), ("BCAP2-06", "SaaS styles", None),
    ("BCAP2-07", "Brand identity", "tools/test_bcap2_brand.py"), ("BCAP2-08", "21 design resources", "tools/test_bcap2_d21.py"),
    ("BCAP2-08b", "21 resources B/C slice", "tools/test_bcap2_d21_bc.py"),
    ("BCAP2-09", "CPP-RUFLO-001", "tools/test_bcap2_ruflo.py")]
NEW_MODULES = ("ruflo_gate", "cdicf/source_intake", "cdicf/reference_intel", "cdicf/reference_records", "cdicf/prompt_schema", "cdicf/component_install", "cdicf/component_meta", "cdicf/motion_select", "ccf/asset_validator", "ccf/kit_readiness", "ccf/territories", "ccf/techniques", "ccf/critique", "ccf/identity_set", "ccf/provider_policy", "ccf/visual_dna", "ccf/brand_truth", "cdio/ux_contracts")


def run(cmd, env=None):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env, timeout=900)
    return p.returncode, p.stdout


def main():
    py = next((c for c in CANDIDATES if Path(c).exists() and subprocess.run([c, "-c", "import pytest,coverage,pytest_cov"], capture_output=True).returncode == 0), sys.executable)
    env = dict(os.environ, BCAP2_TDD_PYTHON=py)
    rows, bad = [], []
    for iid, name, gate in ITEMS:
        if gate is None:
            rows.append((iid, name, "NO_CODE_GATE (scan + Owner decision only)", "PARTIALLY_PROVEN")); continue
        rc, out = run([sys.executable, gate], env)
        npass = sum(1 for l in out.splitlines() if l.lstrip().lstrip("[").startswith("PASS"))
        nfail = sum(1 for l in out.splitlines() if l.lstrip().lstrip("[").startswith("FAIL"))
        rows.append((iid, name, f"exit {rc}, {npass} PASS / {nfail} FAIL", "PARTIALLY_PROVEN" if rc == 0 else "GATE_RED"))
        if rc:
            bad.append(gate)
    rc, out = run([sys.executable, "modules/liveness/reachability.py"])
    orphans = [l for l in out.splitlines() if "ORPHAN" in l and any(m in l for m in NEW_MODULES)]
    if orphans:
        bad.append("liveness: " + "; ".join(orphans))
    led = [("ruflo HOLDS", "vault/programs/bcap-2/ruflo/HOLDS.json"), ("d21 sources", "vault/programs/bcap-2/design-resources/SOURCES.json")]
    for n, f in led:
        try:
            json.loads((ROOT / f).read_text())
        except Exception as e:
            bad.append(f"ledger {n}: {e}")
    state = (ROOT / ".planning/workstreams/bcap2/STATE.md").read_text()
    import re
    if re.search(r"^###.*:\s*ACTIVATED\b", state, re.M):
        bad.append("a STATE.md phase heading claims ACTIVATED: re-read it against law 4")
    if "--json" in sys.argv:
        print(json.dumps({"rows": rows, "bad": bad}, indent=1))
    else:
        for r in rows:
            print(" | ".join(r))
        print("liveness: no BCAP-2 module is an undeclared orphan" if not orphans else "liveness: RED")
    print("BCAP2_DONE_GATE", "FAIL " + str(bad) if bad else "PASS (consistent; no item is ACTIVATED)")
    return 1 if bad else 0


sys.exit(main())
