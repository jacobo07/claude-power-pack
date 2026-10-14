"""WU-A6 mutation drill: each mutation in a fresh mktemp copy; the A6 suite must go red on each."""
import json, shutil, subprocess, sys, tempfile
from pathlib import Path
CLONE = Path(sys.argv[1])
SRC = (CLONE / "tools/gsd_mission.py").read_text()
MUT = [
 ("control-unmutated", "", ""),
 ("enforce-LOW", 'return contract.get("confidence") in (None, "MEDIUM", "HIGH")', 'return True'),
 ("deflate-LOW-declares", 'if conf not in ("MEDIUM", "HIGH") or not declare:', 'if not declare:'),
 ("det-path-skipped", '        det = deterministic_script(rec)\n', '        det = deterministic_script(rec) and None\n'),
 ("det-outside-tree-allowed", 'if not script.is_relative_to(root) or not script.is_file() or script.suffix not in (".py", ".sh"):', 'if False:'),
 ("det-fail-completes", '    if rc != 0:\n        lr.ledger_append(mid, "deterministic_failed"', '    if rc is None:\n        lr.ledger_append(mid, "deterministic_failed"'),
 ("deflate-env-not-delivered", '**({"env": {**os.environ, **unit_env}} if unit_env else {})', '**({})'),
]
rows = []
for name, a, b in MUT:
    assert not a or SRC.count(a) == 1, (name, SRC.count(a))
    d = Path(tempfile.mkdtemp(prefix="a6-mut-"))
    shutil.copytree(CLONE / "tools", d / "tools", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(CLONE / "vault/config", d / "vault/config")
    for rel in ("vault/programs/ccr/stage3/a3/pgo-classes.json",):
        (d / rel).parent.mkdir(parents=True, exist_ok=True); shutil.copy(CLONE / rel, d / rel)
    (d / "tools/gsd_mission.py").write_text(SRC.replace(a, b) if a else SRC)
    r = subprocess.run([sys.executable, str(d / "tools/test_gsd_mission_ccr_a6.py")], capture_output=True, text=True, timeout=600)
    fails = [l for l in r.stdout.splitlines() if l.startswith("FAIL")]
    tail = (r.stdout.strip().splitlines() or [r.stderr.strip()[-200:]])[-1]
    rows.append({"mutation": name, "rc": r.returncode, "killed": r.returncode != 0 if a else None, "summary": tail, "failing_gates": [f.split()[1] for f in fails]})
    shutil.rmtree(d)
print(json.dumps(rows, indent=1))
