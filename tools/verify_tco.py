#!/usr/bin/env python3
"""verify_tco.py -- TCO_GATE probe (verify_spp row).

5 binary sub-checks. Exit 0 iff ALL pass.

  T1 tools/tco_compact_gate.py imports without error
  T2 tco_compact_gate.py CLI runs (no flags) -> exit 0 + text output
  T3 tco_compact_gate.py --route subagent_explore -> str contains 'sonnet'
  T4 vault/config/model-routing.json parses as JSON + >= 7 rules
  T5 ~/CLAUDE.md (project root) contains 'Session Cost Discipline'
     header AND a 'tco_compact_gate' reference

Reality Contract: each check is a real action, never synthetic. Failure
is reported with one diagnostic line. No silent passes.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
HOME_CLAUDE_MD = Path(os.path.expanduser("~/CLAUDE.md"))


def t1():
    """Import the gate module fresh from disk."""
    proc = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, r'%s'); import tco_compact_gate"
         % str(PP / "tools")],
        capture_output=True, text=True, timeout=15,
    )
    if proc.returncode == 0:
        return True, "tco_compact_gate import OK"
    return False, f"import FAIL rc={proc.returncode}: {proc.stderr.strip()[:120]}"


def t2():
    """CLI no-flags should print compact-gate state + exit 0."""
    proc = subprocess.run(
        [sys.executable, str(PP / "tools" / "tco_compact_gate.py")],
        capture_output=True, text=True, timeout=15,
    )
    out = proc.stdout or ""
    if proc.returncode == 0 and "context-pct" in out:
        return True, f"rc=0 stdout_lines={len(out.splitlines())}"
    return False, f"rc={proc.returncode} stdout_head={out[:100]!r}"


def t3():
    """Routing CLI: --route subagent_explore -> sonnet."""
    proc = subprocess.run(
        [sys.executable, str(PP / "tools" / "tco_compact_gate.py"),
         "--route", "subagent_explore"],
        capture_output=True, text=True, timeout=15,
    )
    out = (proc.stdout or "").strip()
    if proc.returncode == 0 and "sonnet" in out:
        return True, f"-> {out}"
    return False, f"rc={proc.returncode} stdout={out!r}"


def t4():
    """Routing JSON parses + >=7 rules."""
    path = PP / "vault" / "config" / "model-routing.json"
    if not path.is_file():
        return False, f"missing: {path}"
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return False, f"JSON parse FAIL: {exc}"
    n = len(cfg.get("rules", []))
    if n >= 7:
        return True, f"rules={n} default={cfg.get('default_model')}"
    return False, f"only {n} rules"


def t5():
    """Project CLAUDE.md anchors."""
    if not HOME_CLAUDE_MD.is_file():
        return False, f"missing: {HOME_CLAUDE_MD}"
    body = HOME_CLAUDE_MD.read_text(encoding="utf-8", errors="replace")
    if "Session Cost Discipline" not in body:
        return False, "CLAUDE.md missing 'Session Cost Discipline'"
    if "tco_compact_gate" not in body:
        return False, "CLAUDE.md missing 'tco_compact_gate' reference"
    return True, "Session Cost Discipline + tco_compact_gate refs present"


def main():
    checks = [("T1-import", t1), ("T2-cli", t2), ("T3-route", t3),
              ("T4-routing-json", t4), ("T5-claude-md", t5)]
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
    print(f"TCO_PROBE = {ok}/{total}")
    return 0 if ok == total else 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    raise SystemExit(main())
