"""V-ASC-LIVE -- Phase 6 gate: the campaign's modules are reachable from a live surface (positive pole),
and the same scanner flags an unwired module in a seeded tree (negative pole).

Run: python3 tools/test_asc_liveness.py   (exit 0 = every check passes). Never calls a model.
"""
import sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.liveness import reachability as R  # noqa: E402

fails = []
def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond: fails.append(name)

MODS = ["backlog_autopilot/inventory", "backlog_autopilot/ledger",
        "backlog_autopilot/webslice", "backlog_autopilot/promotion"]
rows = {r["unit"]: r for r in R.scan(ROOT)}
for m in MODS:
    r = rows.get(m)
    check(f"{m} present in scan (discovered, not curated)", r is not None)
    check(f"{m} REACHABLE via a live surface", bool(r) and r["status"] == R.REACHABLE and bool(r["via"]))
    check(f"{m} not an offender", not any(o["unit"] == m for o in R.offenders(list(rows.values()), repo_root=ROOT)))

# negative pole: seeded unwired module in a throwaway repo must be ORPHAN and an offender
with tempfile.TemporaryDirectory() as t:
    tr = Path(t)
    (tr / "modules/zz").mkdir(parents=True)
    (tr / "modules/zz/__init__.py").write_text("")
    (tr / "modules/zz/lonely.py").write_text("def f():\n    return 1\n")
    (tr / "commands").mkdir()
    (tr / "commands/x.md").write_text("nothing references the module here\n")
    (tr / "vault/liveness").mkdir(parents=True)
    (tr / "vault/liveness/reachability_registry.json").write_text('{"known_orphans": [], "modules": {}}')
    srows = R.scan(tr)
    lone = [r for r in srows if r["unit"] == "zz/lonely"]
    check("seeded unwired module is ORPHAN", bool(lone) and lone[0]["status"] != R.REACHABLE)
    check("seeded unwired module is a gate offender", any(o["unit"] == "zz/lonely" for o in R.offenders(srows, repo_root=tr)))
    (tr / "commands/x.md").write_text("run `python3 -m modules.zz.lonely`\n")
    wired = [r for r in R.scan(tr) if r["unit"] == "zz/lonely"]
    check("wiring it through a command flips it REACHABLE", bool(wired) and wired[0]["status"] == R.REACHABLE)

print("FAILED: %d" % len(fails) if fails else "ALL PASS")
sys.exit(1 if fails else 0)
