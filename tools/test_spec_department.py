#!/usr/bin/env python3
"""test_spec_department.py -- V-gates for the Spec-Driven Department.

Exercises the three backing signals (spec_compliance, premise_risk,
error_recurrence), their dispatcher registration, the clean-context
silence invariant, and the JIT context-feed wiring that keeps
pp-spec-guardian from becoming a CLASE 0 orphan. V-gate convention per
rules/python/testing.md. Exit 0 iff all gates pass.

Sealed BL-SPEC-DEPT-001 (2026-06-03).

Gates:
  V-DEPT-SPEC-SIGNAL    large prompt + no spec   -> pp-spec-guardian fires
  V-DEPT-SPEC-SILENT    small prompt             -> silent
  V-DEPT-SPEC-HASSPEC   large prompt + spec.md   -> silent
  V-DEPT-PREMISE-SIGNAL CLASE 1 + session errors -> pp-premise-guardian
  V-DEPT-PREMISE-SILENT no session errors        -> silent
  V-DEPT-ERROR-SILENT   no session errors        -> silent
  V-DEPT-ERROR-NOCRASH  session errors           -> None|signal, no crash
  V-DEPT-REGISTERED     all 3 in AGENT_CONFIGS
  V-DEPT-DISPATCH-CLEAN clean context            -> [] (regression guard)
  V-DEPT-DISPATCH-SPEC  large prompt via dispatch -> surfaces spec-guardian
  V-DEPT-AGENTS-EXIST   3 agent .md in vault/agents/
  V-DEPT-INSTALLER      install_department_agents.ps1 exists
  V-DEPT-CTX-FEED       jit_skill_loader feeds prompt+cwd into ctx_in
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS  {gate:<22} {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL  {gate:<22} {diag}")


def _check(gate: str, cond: bool, ev_ok: str, ev_fail: str) -> None:
    _ok(gate, ev_ok) if cond else _fail(gate, ev_fail)


def _reset_throttle(project: str) -> None:
    tdir = PP / "vault" / "pp_agents" / "throttle"
    if not tdir.is_dir():
        return
    for f in tdir.glob(f"*_{project}.json"):
        try:
            f.unlink()
        except OSError:
            pass


def main() -> int:
    from modules.pp_agents import proactive_dispatcher as pd
    from modules.pp_agents.signals import (
        error_recurrence,
        premise_risk,
        spec_compliance,
    )

    empty = tempfile.mkdtemp(prefix="dept_vg_")

    s = spec_compliance.evaluate(
        "build a complete auth system from scratch", empty, "p")
    _check("V-DEPT-SPEC-SIGNAL",
           s is not None and s.agent_name == "pp-spec-guardian",
           "spec-guardian fires on large + no-spec",
           f"unexpected {s!r}")

    s = spec_compliance.evaluate("fix the typo in the readme", empty, "p")
    _check("V-DEPT-SPEC-SILENT", s is None,
           "silent on small task", f"fired unexpectedly {s!r}")

    Path(empty, "SPEC.md").write_text("# spec", encoding="utf-8")
    s = spec_compliance.evaluate(
        "build a complete auth system from scratch", empty, "p")
    _check("V-DEPT-SPEC-HASSPEC", s is None,
           "silent when a spec already exists", f"fired {s!r}")

    p = premise_risk.evaluate(
        "AttributeError: module has no attribute X", True, "p")
    _check("V-DEPT-PREMISE-SIGNAL",
           p is not None and p.agent_name == "pp-premise-guardian",
           "premise-guardian fires on CLASE 1 + errors",
           f"unexpected {p!r}")

    p = premise_risk.evaluate(
        "AttributeError: module has no attribute X", False, "p")
    _check("V-DEPT-PREMISE-SILENT", p is None,
           "silent without session errors", f"fired {p!r}")

    e = error_recurrence.evaluate(False, "p")
    _check("V-DEPT-ERROR-SILENT", e is None,
           "silent without session errors", f"fired {e!r}")

    try:
        e = error_recurrence.evaluate(True, "p")
        ok = e is None or e.agent_name == "pp-error-analyst"
        _check("V-DEPT-ERROR-NOCRASH", ok,
               "ran without crash", f"unexpected {e!r}")
    except Exception as exc:
        _fail("V-DEPT-ERROR-NOCRASH", f"raised {type(exc).__name__}: {exc}")

    registered = [a for a in (
        "pp-spec-guardian", "pp-premise-guardian", "pp-error-analyst")
        if a in pd.AGENT_CONFIGS]
    _check("V-DEPT-REGISTERED", len(registered) == 3,
           "3/3 in AGENT_CONFIGS", f"only {registered}")

    clean = pd.dispatch({
        "project": "vg-dept-clean", "last_written_code": "",
        "last_written_file": "", "current_error": "",
        "session_had_errors": False, "errors_fixed": 0,
    })
    _check("V-DEPT-DISPATCH-CLEAN", clean == [],
           "clean context -> [] (invariant held)",
           f"emitted {len(clean)}")

    proj = f"vg-dept-spec-{tempfile.mkdtemp().rsplit('_', 1)[-1]}"
    _reset_throttle(proj)
    fresh = tempfile.mkdtemp(prefix="dept_vg_disp_")
    adv = pd.dispatch({
        "project": proj,
        "prompt": "build a complete auth system from scratch",
        "cwd": fresh,
        "last_written_code": "", "last_written_file": "",
        "current_error": "", "session_had_errors": False,
        "errors_fixed": 0,
    })
    _reset_throttle(proj)
    _check("V-DEPT-DISPATCH-SPEC",
           any("pp-spec-guardian" in a for a in adv),
           "spec-guardian surfaced via dispatch",
           f"advisories={adv!r}")

    agents_dir = PP / "vault" / "agents"
    md = [(agents_dir / f"{n}.md").is_file() for n in (
        "pp-spec-guardian", "pp-premise-guardian", "pp-error-analyst")]
    _check("V-DEPT-AGENTS-EXIST", all(md),
           "3 agent .md staged in vault/agents/",
           f"missing some: {md}")

    installer = PP / "tools" / "install_department_agents.ps1"
    _check("V-DEPT-INSTALLER", installer.is_file(),
           "installer present", "install_department_agents.ps1 missing")

    jit = (PP / "tools" / "jit_skill_loader.py").read_text(
        encoding="utf-8")
    feeds = ('"prompt": str(data.get("prompt")' in jit
             and '"cwd": cwd_raw' in jit)
    _check("V-DEPT-CTX-FEED", feeds,
           "JIT ctx_in feeds prompt+cwd (spec signal not starved)",
           "ctx_in does not feed prompt/cwd -> CLASE 0 orphan risk")

    total = _passes + _fails
    print(f"SPEC_DEPARTMENT_PASS={_passes}/{total}  "
          f"threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
