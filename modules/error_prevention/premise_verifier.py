#!/usr/bin/env python3
"""Premise Verifier -- PP BL-PREMISE-001.

Verify that a plan's premises are TRUE before executing it. Structural
fix for the two error classes the agent repeats most:
  CLASE 1 -- plan assumes an API (function/class/const) that doesn't exist
  CLASE 2 -- plan assumes repo state (a file) that isn't verified

Premise kinds (list of dicts):
  {"type": "file_exists",     "path": "tools/x.py"}
  {"type": "function_exists", "module": "modules.x.y", "function": "f"}
  {"type": "attr_exists",     "module": "modules.x.y", "attr": "C"}

Use assert_premises([...]) BEFORE acting on a plan that names files or
APIs; it returns False (and prints a correction with the REAL API) when
any premise fails. Empirical origin: a plan asserted a 4-param
compile_contract that does not exist -- exactly what this catches.
"""
from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class PremiseResult:
    premise: str
    verified: bool
    evidence: str
    correction: str | None = None


def _ensure_path() -> None:
    p = str(PP_ROOT)
    if p not in sys.path:
        sys.path.insert(0, p)


def verify_file_exists(path: str) -> PremiseResult:
    p = Path(path)
    if not p.is_absolute():
        p = PP_ROOT / path
    exists = p.is_file()
    return PremiseResult(
        premise=f"file exists: {path}",
        verified=exists,
        evidence=f"{p} -- {'exists' if exists else 'NOT FOUND'}",
        correction=(None if exists
                    else f"locate it: Glob '**/{Path(path).name}'"),
    )


def verify_attr_exists(module: str, attr: str) -> PremiseResult:
    """Verify a module imports AND exposes `attr` (function/class/const).

    A module that fails to import (e.g. a broken/orphan module) yields
    verified=False with the import error as evidence -- an API that can't
    be imported is not usable, which is the right answer for a premise.
    """
    _ensure_path()
    try:
        mod = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 -- import error IS the evidence
        return PremiseResult(
            premise=f"{attr} in {module}",
            verified=False,
            evidence=f"import failed: {type(exc).__name__}: {exc}",
            correction=f"module does not import cleanly: {module}",
        )
    ok = hasattr(mod, attr)
    actual = [n for n in dir(mod) if not n.startswith("_")][:20]
    return PremiseResult(
        premise=f"{attr} in {module}",
        verified=ok,
        evidence=("present" if ok else f"absent; public names: {actual}"),
        correction=(None if ok else f"real API of {module}: {actual}"),
    )


def verify_function_exists(module_path: str,
                           function_name: str) -> PremiseResult:
    """Back-compat alias matching the plan's naming."""
    return verify_attr_exists(module_path, function_name)


def verify_premises(premises: list[dict]) -> list[PremiseResult]:
    out: list[PremiseResult] = []
    for p in premises:
        t = p.get("type")
        if t == "file_exists":
            out.append(verify_file_exists(p.get("path", "")))
        elif t in ("function_exists", "attr_exists"):
            mod = p.get("module", "")
            name = p.get("function") or p.get("attr") or ""
            out.append(verify_attr_exists(mod, name))
        else:
            out.append(PremiseResult(
                premise=str(p), verified=False,
                evidence=f"unknown premise type: {t}",
                correction="supported: file_exists, "
                           "function_exists/attr_exists"))
    return out


def assert_premises(premises: list[dict]) -> bool:
    """Verify premises; print corrections and return False on any failure.
    Call this BEFORE acting on a plan (HR-PREMISE-001)."""
    results = verify_premises(premises)
    failed = [r for r in results if not r.verified]
    if failed:
        print("PREMISE VERIFICATION FAILED:")
        for r in failed:
            print(f"  [FAIL] {r.premise}")
            print(f"         evidence: {r.evidence}")
            if r.correction:
                print(f"         fix: {r.correction}")
        return False
    return True


def _self_test() -> int:
    prem = [
        {"type": "file_exists", "path": "tools/jit_skill_loader.py"},
        {"type": "function_exists", "module": "modules.one_shot.compiler",
         "function": "compile_contract"},
        {"type": "function_exists", "module": "modules.one_shot.compiler",
         "function": "nonexistent_function"},
    ]
    results = verify_premises(prem)
    for r in results:
        tag = "OK  " if r.verified else "FAIL"
        print(f"  [{tag}] {r.premise} -- {r.evidence[:60]}")
    good = (results[0].verified and results[1].verified
            and not results[2].verified)
    print("PREMISE_VERIFIER_SELFTEST:", "OK" if good else "FAIL")
    return 0 if good else 1


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json
    ap = argparse.ArgumentParser(
        description="Verify plan premises (BL-PREMISE-001).")
    ap.add_argument("--premises",
                    help="JSON file of premises; '-' = stdin")
    ap.add_argument("--self-test", action="store_true",
                    help="run the built-in self-test")
    args = ap.parse_args(argv)
    if args.self_test or not args.premises:
        return _self_test()
    raw = (sys.stdin.read() if args.premises == "-"
           else Path(args.premises).read_text(encoding="utf-8"))
    return 0 if assert_premises(json.loads(raw)) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
