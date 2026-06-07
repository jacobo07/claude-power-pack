#!/usr/bin/env python3
"""Consolidated V-gate test for CPP Setup OS (Sprint 3 / M14, SCS C40).

One Exit 0 confirms the 3 implemented pillars work cold:
  * scanner builds a ProjectProfile from disk (sourced fields),
  * ROI analyzer ranks recommendations (secret firewall first),
  * secure installer produces a dry-run plan with rollback + a
    secret-scan gate (CRITICAL -> blocked).

Hermetic: every gate uses a fresh temp repo, never the live PP tree.
Run: python tools/test_setup_os.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.setup_os import Source, scan, summarize
from modules.setup_os.roi_analyzer import analyze
from modules.setup_os.secure_installer import dry_run

COMMAND_MD_MIN_BYTES = 200
FAKE_KEY = "sk-ant-" + ("A" * 50)   # clearly-fake, real-shape (HR-SECRET-005)
IMPACTS = {"High", "Medium", "Low"}
EFFORTS = {"S", "M", "L"}

results: list[tuple[str, bool, str]] = []


def gate(name: str, cond: bool, evidence: str = "") -> None:
    results.append((name, bool(cond), evidence))
    print(f"  {name:<26} {'PASS' if cond else 'FAIL'}  {evidence}")


def _make_repo(base: Path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return base


def main() -> int:
    print("=" * 72)
    print("test_setup_os -- CPP Setup OS consolidated V-gate test")
    print("=" * 72)

    with tempfile.TemporaryDirectory(prefix="setup_os_") as td:
        base = Path(td)

        # --- BLOCK 1: scanner (M11) ---
        print("\n[BLOCK 1] Scanner (M11)")
        py_repo = _make_repo(base / "pyrepo", {
            "requirements.txt": "pytest\nrequests\n",
            "app.py": "def main():\n    return 0\n",
            "conftest.py": "import pytest\n",
            "README.md": "# demo\n",
        })
        prof = scan(py_repo)
        gate("V-SCANNER-RUNS",
             prof is not None and isinstance(summarize(prof), str),
             "scan returns a ProjectProfile + summary")
        gate("V-SCANNER-DETECTS",
             prof.language_primary.value == "Python"
             and str(prof.package_manager.value).startswith("pip")
             and prof.test_runner.value == "pytest"
             and prof.language_primary.source == Source.INFERRED,
             f"lang={prof.language_primary.value}, "
             f"pkg={prof.package_manager.value}, "
             f"tests={prof.test_runner.value}")

        # --- BLOCK 2: ROI analyzer (M12) ---
        print("\n[BLOCK 2] ROI analyzer (M12)")
        gap_repo = _make_repo(base / "gaprepo", {
            "app.py": "x = 1\n",
            ".env": "DB_URL=postgres://localhost/x\n",  # secret-sensitive
        })
        recs = analyze(scan(gap_repo))
        gate("V-ROI-PRIORITIZES",
             len(recs) >= 5
             and recs[0].category == "secret"
             and all(r.impact in IMPACTS and r.effort in EFFORTS
                     for r in recs),
             f"{len(recs)} recs, first={recs[0].id if recs else None}, "
             "all carry impact+effort")

        # --- BLOCK 3: secure installer (M13) ---
        print("\n[BLOCK 3] Secure installer (M13)")
        clean_repo = _make_repo(base / "clean", {
            "app.py": "def f():\n    return 1\n",
            "README.md": "# clean\n",
        })
        clean_plan = dry_run(analyze(scan(clean_repo)), clean_repo)
        gate("V-INSTALLER-DRYRUN",
             clean_plan.dry_run is True
             and len(clean_plan.rollback_recipe) == len(clean_plan.steps)
             and len(clean_plan.steps) >= 1,
             f"dry-run plan: {len(clean_plan.steps)} steps, "
             f"{len(clean_plan.rollback_recipe)} rollbacks")
        gate("V-SECRETS-CLEAN-SAFE",
             clean_plan.secret_critical_hits == 0
             and clean_plan.safe_to_apply,
             f"clean repo: crit={clean_plan.secret_critical_hits}, "
             f"safe={clean_plan.safe_to_apply}")

        dirty_repo = _make_repo(base / "dirty", {
            "leak.py": f'KEY = "{FAKE_KEY}"\n',
        })
        dirty_plan = dry_run(analyze(scan(dirty_repo)), dirty_repo)
        gate("V-SECRETS-BLOCKS",
             dirty_plan.secret_critical_hits >= 1
             and not dirty_plan.safe_to_apply
             and dirty_plan.blocked_reason is not None
             and FAKE_KEY not in (dirty_plan.blocked_reason or ""),
             f"leak repo: crit={dirty_plan.secret_critical_hits}, "
             f"blocked, no raw value leaked")

    # --- BLOCK 4: commands + baseline ---
    print("\n[BLOCK 4] Commands + baseline")
    cmds = [ROOT / "commands" / f"{c}.md"
            for c in ("scan-repo", "analyze-roi", "setup-repo")]
    gate("V-COMMANDS-EXIST",
         all(p.is_file() and p.stat().st_size > COMMAND_MD_MIN_BYTES
             for p in cmds),
         f"{sum(p.is_file() for p in cmds)}/3 setup-os commands present")
    gate("V-BASELINE-INTACT",
         len(list(Source)) == 6 and hasattr(scan, "__call__"),
         "Source enum 6 members; package imports clean")

    print("\n" + "=" * 72)
    passes = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"SETUP_OS_PASS={passes}/{total}  threshold={total}/{total}")
    print("=" * 72)
    return 0 if passes == total else 1


if __name__ == "__main__":
    sys.exit(main())
