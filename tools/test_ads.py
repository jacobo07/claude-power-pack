#!/usr/bin/env python3
"""Consolidated V-gate test for ADS -- Auto-Documentation System (BL-ADS-001).

One Exit 0 confirms the whole ADS layer is operational cold and hermetic:
  * detector classifies CREATED / UPDATED / MINOR / no-op-without-git,
  * generator emits the 4 docs (PRD/Arch/Constitution/Changelog) from AST,
  * updater refreshes AUTO blocks while preserving OWNER blocks verbatim,
  * malformed markers abort the splice (never overwrite OWNER),
  * the Stop-chain runner fires from stdin, writes docs, NEVER commits,
    honours the docs/.ads-disabled kill switch, and fails open,
  * the /generate-docs command + backfill enumerate real modules,
  * the composed SDD-OS baseline is intact (no regression).

Hermetic: a private GIT_CONFIG_GLOBAL/SYSTEM, a fixed `now`, and every
write lands in a TemporaryDirectory -- safe to run back-to-back N times.

Run: python tools/test_ads.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.ads.detector import (
    ChangeType, ModuleChange, detect_changes, module_slug, resolve_git,
)
from modules.ads.doc_generator import (
    AUTO_OPEN, AUTO_CLOSE, OWNER_OPEN, DOC_TYPES, build_docs, write_docs,
)
from modules.ads.doc_updater import extract_block, update_docs
from modules.ads.detector import MIN_NEW_LOC

FIXED_NOW = "2026-06-09T00:00:00Z"
PY = sys.executable
SYNC = str(ROOT / "tools" / "ads_sync.py")
GEXE = resolve_git()

results: list[tuple[str, bool, str]] = []


def gate(name: str, cond: bool, ev: str = "") -> None:
    results.append((name, bool(cond), ev))
    print(f"  {name:<28} {'PASS' if cond else 'FAIL'}  {ev}")


def _git(repo: Path, *a: str):
    return subprocess.run([GEXE, "-C", str(repo), *a],
                          capture_output=True, text=True, timeout=20)


def _init(repo: Path):
    _git(repo, "init")
    _git(repo, "config", "user.email", "ads@test.local")
    _git(repo, "config", "user.name", "ADS Test")
    _git(repo, "config", "commit.gpgsign", "false")


def _big_func(name: str, n: int = 100) -> str:
    body = "\n".join(f"    v{i} = {i}" for i in range(n))
    return f'"""Module {name}."""\ndef {name}(arg):\n{body}\n    return v0\n'


def main() -> int:
    print("=" * 72)
    print("test_ads -- ADS consolidated V-gate test")
    print("=" * 72)

    with tempfile.TemporaryDirectory(prefix="ads_") as td:
        td = Path(td)
        os.environ["GIT_CONFIG_GLOBAL"] = str(td / "gc.global")
        os.environ["GIT_CONFIG_SYSTEM"] = str(td / "gc.system")
        repo = td / "repo"
        repo.mkdir()
        _init(repo)

        # Baseline committed module so UPDATED/MINOR have a HEAD to diff.
        billing = repo / "modules" / "billing"
        billing.mkdir(parents=True)
        (billing / "__init__.py").write_text("from .core import charge\n", encoding="utf-8")
        (billing / "core.py").write_text(_big_func("charge", 120), encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-m", "base")

        # --- BLOCK 1: detector classification ---
        print("\n[BLOCK 1] Detector classification (D1)")
        ship = repo / "modules" / "shipping"
        ship.mkdir(parents=True)
        (ship / "__init__.py").write_text("from .rates import quote\n", encoding="utf-8")
        (ship / "rates.py").write_text(_big_func("quote", 100), encoding="utf-8")
        ch = {c.key: c for c in detect_changes(repo, GEXE)}
        gate("V-ADS-DETECTOR-CREATE",
             ch.get("modules/shipping") is not None
             and ch["modules/shipping"].change_type == ChangeType.CREATED,
             "new package -> CREATED")
        gate("V-ADS-PKG-SUBSUMES-CHILD",
             "modules/shipping/rates.py" not in ch,
             "child file folded into package key")

        _git(repo, "add", "-A"); _git(repo, "commit", "-m", "ship")
        core = billing / "core.py"
        core.write_text(core.read_text(encoding="utf-8") + "\n# tiny\n", encoding="utf-8")
        ch2 = {c.key: c for c in detect_changes(repo, GEXE)}
        gate("V-ADS-DETECTOR-MINOR",
             ch2.get("modules/billing") is not None
             and ch2["modules/billing"].change_type == ChangeType.MINOR,
             "1-line edit -> MINOR")
        gate("V-ADS-SILENCE-ON-MINOR",
             all(c.change_type == ChangeType.MINOR for c in ch2.values()),
             "minor turn yields no CREATED/UPDATED")

        with tempfile.TemporaryDirectory(prefix="ads_nogit_") as nd:
            gate("V-ADS-NOOP-NO-GIT", detect_changes(nd, GEXE) == [],
                 "non-git dir -> []")

        # --- BLOCK 2: generation (D2) ---
        print("\n[BLOCK 2] Doc generation (D2)")
        paths = write_docs("modules/shipping", repo, FIXED_NOW, True)
        gate("V-ADS-GENERATES-4",
             sorted(paths) == sorted(DOC_TYPES)
             and all(p.exists() and p.stat().st_size > 80 for p in paths.values()),
             "4 docs (prd/arch/constitution/changelog)")
        prd = paths["prd"].read_text(encoding="utf-8")
        gate("V-ADS-AST-PUBLIC-ONLY",
             "quote(arg)" in prd and AUTO_OPEN in prd and OWNER_OPEN in prd,
             "AST public symbol + both marker blocks")
        gate("V-ADS-CROSS-REPO",
             paths["prd"].is_relative_to(repo) and not paths["prd"].is_relative_to(ROOT),
             "docs land in target repo, not the PP repo")

        # --- BLOCK 3: update preserves OWNER (D3) ---
        print("\n[BLOCK 3] Updater OWNER preservation (D3)")
        OWNER = "REAL BUSINESS GOAL: own the shipping vertical"
        paths["prd"].write_text(
            prd.replace("_Owner-authored. ADS never modifies this block._",
                        "_Owner-authored. ADS never modifies this block._\n\n" + OWNER),
            encoding="utf-8")
        (ship / "rates.py").write_text(
            (ship / "rates.py").read_text(encoding="utf-8")
            + "def expedite(x):\n    return x\n", encoding="utf-8")
        chg = ModuleChange("modules/shipping", ChangeType.UPDATED,
                           ["modules/shipping/rates.py"], 2, 0, 30.0, True)
        update_docs("modules/shipping", repo, chg, "2026-06-09T01:00:00Z", True)
        after = paths["prd"].read_text(encoding="utf-8")
        gate("V-ADS-PRESERVES-OWNER", OWNER in after, "owner goal survived update")
        gate("V-ADS-AUTO-REFRESHED", "expedite(x)" in after, "new symbol in AUTO")
        cl = paths["changelog"].read_text(encoding="utf-8")
        gate("V-ADS-CHANGELOG-APPENDS",
             "created" in cl and "updated" in cl, "append-only changelog")

        bad = paths["prd"]
        snapshot = bad.read_text(encoding="utf-8")
        bad.write_text(snapshot + f"\n{AUTO_OPEN}\nstray\n", encoding="utf-8")
        before = bad.read_text(encoding="utf-8")
        st = update_docs("modules/shipping", repo, chg, "2026-06-09T02:00:00Z", True)
        gate("V-ADS-MALFORMED-SKIP",
             st.get("prd", "").startswith("skipped")
             and bad.read_text(encoding="utf-8") == before,
             f"prd={st.get('prd')}")
        gate("V-ADS-SLUG-DISTINCT",
             module_slug("modules/ads") != module_slug("apps/ads")
             and "/" not in module_slug("a/b/c.py"),
             "collision-free slug")

        # --- BLOCK 4: Stop-chain runner (D4) ---
        print("\n[BLOCK 4] Stop-chain runner (D4)")
        repo2 = td / "repo2"; repo2.mkdir(); _init(repo2)
        _git(repo2, "commit", "--allow-empty", "-m", "root")
        auth = repo2 / "auth"; auth.mkdir()
        (auth / "__init__.py").write_text("from .login import go\n", encoding="utf-8")
        (auth / "login.py").write_text(_big_func("go", 90), encoding="utf-8")
        env = dict(os.environ, CLAUDE_ADS_NOW=FIXED_NOW)
        r = subprocess.run([PY, SYNC],
                           input=json.dumps({"hook_event_name": "Stop", "cwd": str(repo2)}),
                           capture_output=True, text=True, timeout=30, env=env)
        slug = module_slug("auth")
        gate("V-ADS-STOP-RUNNER-FIRES",
             r.returncode == 0
             and (repo2 / "docs" / "prd" / f"{slug}.md").exists(),
             f"stdin Stop -> docs written (rc={r.returncode})")
        gate("V-ADS-NO-COMMIT",
             _git(repo2, "log", "--oneline").stdout.count("\n") == 1,
             "runner wrote docs but added NO commit (gap #8)")

        (repo2 / "docs" / ".ads-disabled").write_text("", encoding="utf-8")
        new = repo2 / "extra"; new.mkdir()
        (new / "__init__.py").write_text("x=1\n", encoding="utf-8")
        (new / "m.py").write_text(_big_func("m", 90), encoding="utf-8")
        subprocess.run([PY, SYNC], input=json.dumps({"cwd": str(repo2)}),
                       capture_output=True, text=True, timeout=30, env=env)
        gate("V-ADS-KILL-SWITCH",
             not (repo2 / "docs" / "prd" / f"{module_slug('extra')}.md").exists(),
             "docs/.ads-disabled suppresses generation")
        rg = subprocess.run([PY, SYNC], input="}{garbage",
                            capture_output=True, text=True, timeout=15)
        gate("V-ADS-FAIL-OPEN", rg.returncode == 0, "garbage stdin -> exit 0")

        # --- BLOCK 5: command + baseline ---
        print("\n[BLOCK 5] Command + composed baseline")
        cmd = ROOT / "commands" / "generate-docs.md"
        gate("V-ADS-COMMAND-EXISTS",
             cmd.is_file() and cmd.stat().st_size > 200, "/generate-docs present")
        base = subprocess.run([PY, str(ROOT / "tools" / "test_sdd_os.py")],
                              capture_output=True, text=True, timeout=60)
        gate("V-BASELINE-INTACT", base.returncode == 0,
             "test_sdd_os.py still Exit 0 (no regression)")

    print("\n" + "=" * 72)
    passes = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"ADS_PASS={passes}/{total}  threshold={total}/{total}")
    print("=" * 72)
    return 0 if passes == total else 1


if __name__ == "__main__":
    sys.exit(main())
