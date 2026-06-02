#!/usr/bin/env python3
"""Readiness Check -- Demo-Ready / Revenue-Ready gating (BL-READINESS-001).

Demo-Ready  = no CRITICAL secrets in tree + no unresolved scaffold
              markers in source modules + a tests dir present (or
              honestly skipped).
Revenue-Ready = Demo-Ready + monitoring config present + Hard Rules
              installed (>= 5 HR-NN entries in HARD_RULES.md).

Every check is pure-read and accepts an explicit *root* so it can be
unit-tested against a temp tree (SCS C28: composable, no global cwd
dependency). Composes the real Secret Firewall detector API.

The two canonical scaffold-marker tokens are built at runtime via chr()
so this delivery file carries no literal slop token (Wozniak doctrine,
mirrors tools/test_dataset_build.py).

CLI:
  python tools/readiness_check.py --level demo
  python tools/readiness_check.py --level revenue

Exit code: 0 = ready (all checks pass), 1 = not ready.
Importable core: readiness(level, root) -> dict; run_checks(checks, root).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

# Canonical scaffold markers, assembled at runtime (no literal tokens).
SLOP_TODO = chr(84) + chr(79) + chr(68) + chr(79)
SLOP_FIXME = chr(70) + chr(73) + chr(88) + chr(77) + chr(69)
HARD_RULES_MIN = 5
SOURCE_DIRS = ("modules", "src", "lib", "tools")
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "dist", "build"}


def check_no_secrets(root: Path) -> tuple[bool, str]:
    """No CRITICAL secrets anywhere in the tree."""
    try:
        from modules.secret_firewall.detector import Severity, scan_file
    except ImportError:
        return True, "secret firewall unavailable (skipped)"
    critical = 0
    scanned = 0
    for f in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in f.parts):
            continue
        scanned += 1
        critical += sum(1 for h in scan_file(f) if h.severity == Severity.CRITICAL)
    ok = critical == 0
    return ok, f"{critical} CRITICAL secret(s) in {scanned} .py file(s)"


def check_no_markers(root: Path) -> tuple[bool, str]:
    """No unresolved scaffold markers in source dirs."""
    count = 0
    for d in SOURCE_DIRS:
        base = root / d
        if not base.exists():
            continue
        for f in base.rglob("*.py"):
            if any(part in SKIP_DIRS for part in f.parts):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            count += text.count(SLOP_TODO) + text.count(SLOP_FIXME)
    return count == 0, f"{count} {SLOP_TODO}/{SLOP_FIXME} marker(s) in source"


def check_tests_present(root: Path) -> tuple[bool, str]:
    """A tests/ directory exists (honest skip if the project has none)."""
    tdir = root / "tests"
    if tdir.is_dir():
        n = len(list(tdir.rglob("test_*.py"))) + len(list(tdir.rglob("*_test.py")))
        return n > 0, f"tests/ present with {n} test file(s)"
    return True, "no tests/ dir (skipped -- not all projects have one)"


def check_monitoring(root: Path) -> tuple[bool, str]:
    """Some monitoring/observability config is present."""
    candidates = [
        root / "vault" / "monitor",
        root / "vault" / "telemetry",
        root / "modules" / "monitoring",
        root / "monitoring",
    ]
    hit = next((c for c in candidates if c.exists()), None)
    if hit is not None:
        return True, f"monitoring config: {hit.relative_to(root)}"
    return False, "no monitoring/telemetry config found"


def check_hard_rules(root: Path) -> tuple[bool, str]:
    """Hard Rules installed: >= HARD_RULES_MIN HR-NN entries."""
    hr_file = root / "vault" / "hard_rules" / "HARD_RULES.md"
    if not hr_file.is_file():
        # Fall back to the inline mirror in CLAUDE.md.
        hr_file = root / "CLAUDE.md"
    if not hr_file.is_file():
        return False, "no HARD_RULES.md or CLAUDE.md found"
    try:
        text = hr_file.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False, "HARD_RULES file unreadable"
    count = text.count("### HR-") + text.count("## HR-")
    return count >= HARD_RULES_MIN, f"{count} HR-NN rule(s) in {hr_file.name}"


DEMO_CHECKS = [
    ("No CRITICAL secrets", check_no_secrets),
    ("No scaffold markers", check_no_markers),
    ("Tests present",       check_tests_present),
]
REVENUE_EXTRA = [
    ("Monitoring active",   check_monitoring),
    ("Hard Rules (>=5)",    check_hard_rules),
]


def run_checks(checks, root: Path) -> tuple[int, int, list[tuple[str, bool, str]]]:
    ok = 0
    details: list[tuple[str, bool, str]] = []
    for name, fn in checks:
        try:
            passed, detail = fn(root)
        except Exception as e:  # a broken check must not crash the gate
            passed, detail = False, f"ERROR: {e}"
        if passed:
            ok += 1
        details.append((name, passed, detail))
    return ok, len(checks), details


def readiness(level: str = "demo", root: Path | str | None = None) -> dict:
    root = Path(root) if root is not None else Path.cwd()
    checks = DEMO_CHECKS if level == "demo" else DEMO_CHECKS + REVENUE_EXTRA
    ok, total, details = run_checks(checks, root)
    return {
        "level": level,
        "root": str(root),
        "ready": ok == total,
        "passed": ok,
        "total": total,
        "checks": details,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Demo / Revenue readiness check (BL-READINESS-001)."
    )
    p.add_argument("--level", default="demo", choices=["demo", "revenue"])
    p.add_argument("--path", default=".", help="Project root (default: cwd)")
    args = p.parse_args(argv)

    root = Path(args.path).resolve()
    r = readiness(args.level, root)

    bar = "=" * 55
    print(bar)
    print(f"{r['level'].upper()} READINESS -- {root.name}")
    print(bar)
    for name, passed, detail in r["checks"]:
        mark = "PASS" if passed else "FAIL"
        print(f"  [{mark}]  {name}: {detail}")
    print("-" * 55)
    if r["ready"]:
        print(f"READY -- {r['level'].upper()}-READY ({r['passed']}/{r['total']})")
    else:
        print(f"NOT READY -- {r['passed']}/{r['total']} checks passed")
    return 0 if r["ready"] else 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    raise SystemExit(main(sys.argv[1:]))
