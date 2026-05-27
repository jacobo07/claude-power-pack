#!/usr/bin/env python3
"""V-* gates for UQF (ECC absorption).

15 V-gates covering: principle registry, P01 pre-report gate,
P02 zero-findings, P03 false-positives, P04 proof-triad,
P06 error-never-silent, anti-pattern detectors, auditor, CEPS
confidence extensions, and pytest baseline.

Each gate prints PASS/FAIL with a one-line diagnostic; final line
is `UQF_PASS=N/M  threshold=15/15`. Exit 0 iff all pass.
"""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


passes = 0
fails = 0


def _ok(name, msg=""):
    global passes
    passes += 1
    print(f"PASS  {name:30s} {msg}")


def _fail(name, msg=""):
    global fails
    fails += 1
    print(f"FAIL  {name:30s} {msg}")


def main() -> int:
    # ---- V-UQF-REGISTRY: at least 8 principles registered ----
    from modules.uqf.principles import (
        load_all_principles, get_all, clear_registry
    )
    clear_registry()
    n = load_all_principles()
    if n >= 8:
        _ok("V-UQF-REGISTRY", f"loaded {n} principles")
    else:
        _fail("V-UQF-REGISTRY", f"only {n} loaded (need >=8)")

    # ---- V-UQF-PRE-REPORT-PASS ----
    from modules.uqf.principles.pre_report_gate import PreReportGate
    pre = PreReportGate()
    r = pre.check(
        {"line": "42", "failure_mode": "NPE",
         "surrounding_context": "x.val",
         "severity_defensible": True},
        "code",
    )
    if r.passed:
        _ok("V-UQF-PRE-REPORT-PASS", f"score={r.score}")
    else:
        _fail("V-UQF-PRE-REPORT-PASS", f"unexpected fail: {r.evidence}")

    # ---- V-UQF-PRE-REPORT-FAIL ----
    r2 = pre.check(
        {"line": "", "failure_mode": "",
         "surrounding_context": "", "severity_defensible": False},
        "code",
    )
    if not r2.passed:
        _ok("V-UQF-PRE-REPORT-FAIL", f"score={r2.score} missing keys")
    else:
        _fail("V-UQF-PRE-REPORT-FAIL", "incomplete should have failed")

    # ---- V-UQF-ZERO-FINDINGS ----
    from modules.uqf.principles.zero_findings_valid import ZeroFindingsValid
    zf = ZeroFindingsValid()
    rz = zf.check([], "code")
    if rz.passed and rz.score == 1.0:
        _ok("V-UQF-ZERO-FINDINGS", "[] accepted as clean")
    else:
        _fail("V-UQF-ZERO-FINDINGS", f"unexpected: {rz}")

    # ---- V-UQF-FALSE-POS ----
    from modules.uqf.principles.false_positives_catalog import (
        CommonFalsePositivesCatalog,
    )
    fp = CommonFalsePositivesCatalog()
    rf = fp.check("consider adding error handling here", "code")
    if not rf.passed:
        _ok("V-UQF-FALSE-POS", f"caught FP: {rf.evidence}")
    else:
        _fail("V-UQF-FALSE-POS", "FP not caught")

    # ---- V-UQF-PROOF-TRIAD ----
    from modules.uqf.principles.proof_triad import HighCriticalProofTriad
    pt = HighCriticalProofTriad()
    rt = pt.check(
        {"severity": "HIGH", "text": "something bad"},
        "code",
    )
    if not rt.passed:
        _ok("V-UQF-PROOF-TRIAD", f"HIGH without triad rejected score={rt.score}")
    else:
        _fail("V-UQF-PROOF-TRIAD", "HIGH without triad should fail")

    # ---- V-UQF-ERROR-SILENT ----
    from modules.uqf.principles.error_never_silent import ErrorNeverSilent
    en = ErrorNeverSilent()
    bad = "try:\n  foo()\nexcept:\n  pass"
    re_ = en.check(bad, "code")
    if not re_.passed:
        _ok("V-UQF-ERROR-SILENT", f"bare-except detected: {re_.evidence[:50]}")
    else:
        _fail("V-UQF-ERROR-SILENT", "bare-except should fail")

    # ---- V-UQF-ERROR-TYPED ----
    good = "try:\n  foo()\nexcept ValueError as e:\n  raise"
    re2 = en.check(good, "code")
    if re2.passed:
        _ok("V-UQF-ERROR-TYPED", "typed-except OK")
    else:
        _fail("V-UQF-ERROR-TYPED", f"typed should pass: {re2.evidence}")

    # ---- V-UQF-PROMPT-DEFENSE ----
    from modules.uqf.principles.prompt_defense_baseline import (
        PromptDefenseBaseline,
    )
    pdb = PromptDefenseBaseline()
    claude_md_path = os.path.expanduser("~/CLAUDE.md")
    try:
        content = open(claude_md_path, encoding="utf-8").read()
    except OSError:
        content = ""
    rp = pdb.check(content, "prompts")
    if rp.passed:
        _ok("V-UQF-PROMPT-DEFENSE", f"CLAUDE.md covered={rp.score*6:.0f}/6")
    else:
        _fail("V-UQF-PROMPT-DEFENSE",
              f"CLAUDE.md missing baseline: score={rp.score:.2f}")

    # ---- V-UQF-ANTI-BARE ----
    from modules.uqf.anti_patterns import (
        detect_bare_except, detect_missing_type_hints,
        run_all as run_ap,
    )
    bare_hits = detect_bare_except(bad)
    if len(bare_hits) == 1:
        _ok("V-UQF-ANTI-BARE", f"detected at line {bare_hits[0].line}")
    else:
        _fail("V-UQF-ANTI-BARE", f"expected 1 hit, got {len(bare_hits)}")

    # ---- V-UQF-ANTI-TYPE-HINTS ----
    no_hints = "def public_func(a, b):\n    return a + b"
    hints = detect_missing_type_hints(no_hints)
    if len(hints) == 1:
        _ok("V-UQF-ANTI-TYPE-HINTS", f"detected `public_func`")
    else:
        _fail("V-UQF-ANTI-TYPE-HINTS",
              f"expected 1 hit, got {len(hints)}")

    # ---- V-UQF-AUDITOR-SCORE ----
    from modules.uqf.auditor import UQFAuditor
    a = UQFAuditor()
    rep = a.audit_file("tools/ceps.py")
    if 0 <= rep.score_pct <= 100:
        _ok("V-UQF-AUDITOR-SCORE",
            f"ceps.py={rep.score_pct:.1f}% (in 0-100)")
    else:
        _fail("V-UQF-AUDITOR-SCORE",
              f"score out of range: {rep.score_pct}")

    # ---- V-UQF-CEPS-CONFIDENCE ----
    from tools.ceps import compute_confidence
    c1 = compute_confidence(2, True)
    if 0.6 <= c1 <= 0.75:
        _ok("V-UQF-CEPS-CONFIDENCE",
            f"compute_confidence(2,True)={c1}")
    else:
        _fail("V-UQF-CEPS-CONFIDENCE",
              f"expected ~0.7, got {c1}")

    # ---- V-UQF-CEPS-PROMOTE ----
    from tools.ceps import promote_to_global
    if (promote_to_global("p", ["a", "b"]) and
            not promote_to_global("p", ["a", "a"]) and
            not promote_to_global("p", ["a"])):
        _ok("V-UQF-CEPS-PROMOTE", "promotion logic correct")
    else:
        _fail("V-UQF-CEPS-PROMOTE", "promotion logic broken")

    # ---- V-BASELINE-INTACT: pytest tests/ ----
    pyt = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"],
        capture_output=True, text=True, cwd=str(ROOT), timeout=180,
    )
    last_line = (pyt.stdout.strip().splitlines() or [""])[-1]
    if pyt.returncode == 0 and "passed" in last_line:
        _ok("V-BASELINE-INTACT", f"rc=0 last='{last_line[:60]}'")
    else:
        _fail("V-BASELINE-INTACT",
              f"rc={pyt.returncode} last='{last_line[:60]}'")

    total = passes + fails
    print()
    print(f"UQF_PASS={passes}/{total}  threshold=15/15")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    raise SystemExit(main())
