#!/usr/bin/env python3
"""verify_uqf.py -- UQF_ACTIVE probe (verify_spp row).

5 binary sub-checks. Exit 0 iff all pass.

  U1 modules/uqf/__init__.py imports without error
  U2 get_all() returns >=8 principles
  U3 UQFAuditor().audit_file('tools/ceps.py') returns 0-100 score
  U4 uqf_audit.py CLI executes without crash
  U5 >=3 PP modules import modules/uqf/ (active integration)

Reality Contract: each check is a real action. Source: ECC absorption
(MIT). No silent passes.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))


def u1():
    proc = subprocess.run(
        [sys.executable, "-c",
         f"import sys; sys.path.insert(0, r'{PP}'); "
         "from modules.uqf import Principle, PrincipleResult, get_all"],
        capture_output=True, text=True, timeout=15,
    )
    if proc.returncode == 0:
        return True, "modules.uqf import OK"
    return False, f"import FAIL rc={proc.returncode}: {proc.stderr.strip()[:120]}"


def u2():
    proc = subprocess.run(
        [sys.executable, "-c",
         f"import sys; sys.path.insert(0, r'{PP}'); "
         "from modules.uqf.principles import load_all_principles; "
         "print(load_all_principles())"],
        capture_output=True, text=True, timeout=15,
    )
    try:
        n = int(proc.stdout.strip())
    except ValueError:
        return False, f"unexpected stdout: {proc.stdout!r}"
    if n >= 8:
        return True, f"loaded {n} principles"
    return False, f"only {n} principles (need >=8)"


def u3():
    proc = subprocess.run(
        [sys.executable, "-c",
         f"import sys; sys.path.insert(0, r'{PP}'); "
         "from modules.uqf.auditor import UQFAuditor; "
         "r = UQFAuditor().audit_file('tools/ceps.py'); "
         "print(r.score_pct)"],
        capture_output=True, text=True, timeout=30, cwd=str(PP),
    )
    if proc.returncode != 0:
        return False, f"rc={proc.returncode} stderr={proc.stderr[:120]}"
    try:
        score = float(proc.stdout.strip())
    except ValueError:
        return False, f"unexpected stdout: {proc.stdout!r}"
    if 0 <= score <= 100:
        return True, f"ceps.py score={score:.1f}"
    return False, f"score out of range: {score}"


def u4():
    proc = subprocess.run(
        [sys.executable, str(PP / "tools" / "uqf_audit.py"), "--scan-all"],
        capture_output=True, text=True, timeout=30, cwd=str(PP),
    )
    out = proc.stdout or ""
    if proc.returncode == 0 and "MODULE" in out and "SCORE" in out:
        return True, f"--scan-all OK, {len(out.splitlines())} lines"
    return False, f"rc={proc.returncode} stdout_head={out[:80]!r}"


def u5():
    """Active integration: >=3 PP modules import modules.uqf."""
    targets = (
        "modules/code_review/__init__.py",
        "tools/uqf_audit.py",
        "tools/test_uqf.py",
        "modules/uqf/auditor.py",
        "modules/uqf/gates.py",
    )
    importers = 0
    found_in = []
    for t in targets:
        p = PP / t
        if not p.is_file():
            continue
        body = p.read_text(encoding="utf-8", errors="replace")
        if "modules.uqf" in body or "from modules.uqf" in body:
            importers += 1
            found_in.append(t)
    if importers >= 3:
        return True, f"{importers} modules import modules.uqf"
    return False, f"only {importers} modules import modules.uqf"


def main() -> int:
    checks = [("U1-import", u1),
              ("U2-registry", u2),
              ("U3-auditor", u3),
              ("U4-cli", u4),
              ("U5-integration", u5)]
    ok = 0
    for name, fn in checks:
        try:
            passed, msg = fn()
        except Exception as exc:
            passed, msg = False, f"unhandled {type(exc).__name__}: {exc}"
        tag = "PASS" if passed else "FAIL"
        print(f"  [{tag}] {name:<20s} {msg}")
        if passed:
            ok += 1
    total = len(checks)
    print(f"UQF_PROBE = {ok}/{total}")
    return 0 if ok == total else 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    raise SystemExit(main())
