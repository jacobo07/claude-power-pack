#!/usr/bin/env python3
"""test_claude_md_router.py - V-gates for the CLAUDE.md Router task (M5).

Gates:
  V-CLAUDE-MD-SIZE    ~/.claude/CLAUDE.md < 40,000 chars (SKIP if absent)
  V-CLAUDE-MD-ROUTER  has HARD-RULES router + vault pointers
  V-SAFETY-INTACT     always-on safety rules still present (trim didn't cut)
  V-TRIM-SAFE         trim() strips provenance, keeps operative comma-lists
  V-FIREWALL-BLOCKS   firewall denies a Write that would exceed 40k
  V-FIREWALL-ALLOWS   firewall allows a small Write (and non-CLAUDE.md)
  V-LINTER-RUNS       Stop linter runs without crashing
  V-BASELINE-INTACT   pytest tests/ -> 0 failed

node-dependent gates SKIP (not fail) when node is unavailable.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))
from tools.trim_claude_md import CM, TARGET_MAX  # noqa: E402

_passes = 0
_fails = 0


def _ok(g, e):
    global _passes
    _passes += 1
    print(f"  [OK]   {g}: {e}")


def _fail(g, d):
    global _fails
    _fails += 1
    print(f"  [FAIL] {g}: {d}")


def _adv(g, d):
    print(f"  [ADV]  {g}: {d}")


def _read_cm():
    try:
        return CM.read_text(encoding="utf-8-sig")
    except Exception:
        return None


def test_size():
    txt = _read_cm()
    if txt is None:
        _adv("V-CLAUDE-MD-SIZE", "no ~/.claude/CLAUDE.md on this host")
        return
    n = len(txt)
    if n < TARGET_MAX:
        _ok("V-CLAUDE-MD-SIZE", f"{n} chars < {TARGET_MAX}")
    else:
        _fail("V-CLAUDE-MD-SIZE", f"{n} >= {TARGET_MAX}")


def test_router():
    txt = _read_cm()
    if txt is None:
        _adv("V-CLAUDE-MD-ROUTER", "no CLAUDE.md")
        return
    has_hr = "HARD RULES" in txt
    has_ptr = ("Vault Index" in txt or "Knowledge Vault Protocol" in txt
               or "knowledge_vault" in txt)
    if has_hr and has_ptr:
        _ok("V-CLAUDE-MD-ROUTER", "HARD-RULES router + vault pointers present")
    else:
        _fail("V-CLAUDE-MD-ROUTER", f"hr={has_hr} ptr={has_ptr}")


def test_safety_intact():
    txt = _read_cm()
    if txt is None:
        _adv("V-SAFETY-INTACT", "no CLAUDE.md")
        return
    required = {
        "parallel-read-cap": "≤4",  # ≤4
        "bash-bridge": "Windows Bash Bridge",
        "parallel-subagent": "Parallel Subagent",
        "anti-waiting": "run_in_background",
        "pathspec": "Pathspec",
    }
    missing = [k for k, v in required.items() if v not in txt]
    if not missing:
        _ok("V-SAFETY-INTACT", "all 5 always-on safety markers present")
    else:
        _fail("V-SAFETY-INTACT", f"MISSING safety rules: {missing}")


def test_trim_safe():
    from tools.trim_claude_md import trim
    sample = (
        "## Foo (MANDATORY — 2026-05-22, cross-project)\n"
        "operative rule body\n"
        "(mix compile, mix test — sealed 2026-05-28 turn) keep-this\n"
        "tail (BL-0036, 2026-05-03) drop-this-paren\n"
    )
    out = trim(sample)
    keeps_label = "(MANDATORY)" in out
    keeps_oplist = "mix compile, mix test" in out
    drops_paren = "(BL-0036" not in out
    if keeps_label and keeps_oplist and drops_paren:
        _ok("V-TRIM-SAFE",
            "header date stripped, operative comma-list kept, dated paren cut")
    else:
        _fail("V-TRIM-SAFE",
              f"label={keeps_label} oplist={keeps_oplist} paren={drops_paren}")


def _node():
    return shutil.which("node") or shutil.which("node.exe")


def test_firewall_blocks():
    node = _node()
    if not node:
        _adv("V-FIREWALL-BLOCKS", "node unavailable")
        return
    payload = json.dumps({"tool_name": "Write", "tool_input": {
        "file_path": str(CM), "content": "x" * 50000}})
    try:
        r = subprocess.run([node, str(PP / "hooks" / "claude_md_firewall.js")],
                           input=payload, capture_output=True, text=True,
                           timeout=15)
    except Exception as exc:  # noqa: BLE001
        _fail("V-FIREWALL-BLOCKS", f"{type(exc).__name__}: {exc}")
        return
    if '"permissionDecision"' in r.stdout and '"deny"' in r.stdout:
        _ok("V-FIREWALL-BLOCKS", "50k Write -> deny")
    else:
        _fail("V-FIREWALL-BLOCKS", f"stdout={r.stdout[:120]!r}")


def test_firewall_allows():
    node = _node()
    if not node:
        _adv("V-FIREWALL-ALLOWS", "node unavailable")
        return
    fw = str(PP / "hooks" / "claude_md_firewall.js")
    small = json.dumps({"tool_name": "Write", "tool_input": {
        "file_path": str(CM), "content": "y" * 1000}})
    other = json.dumps({"tool_name": "Write", "tool_input": {
        "file_path": "C:/tmp/foo.py", "content": "z" * 50000}})
    try:
        r1 = subprocess.run([node, fw], input=small, capture_output=True,
                            text=True, timeout=15)
        r2 = subprocess.run([node, fw], input=other, capture_output=True,
                            text=True, timeout=15)
    except Exception as exc:  # noqa: BLE001
        _fail("V-FIREWALL-ALLOWS", f"{type(exc).__name__}: {exc}")
        return
    if not r1.stdout.strip() and not r2.stdout.strip():
        _ok("V-FIREWALL-ALLOWS", "1k Write + 50k non-CLAUDE.md both allowed")
    else:
        _fail("V-FIREWALL-ALLOWS",
              f"small={r1.stdout[:60]!r} other={r2.stdout[:60]!r}")


def test_linter_runs():
    node = _node()
    if not node:
        _adv("V-LINTER-RUNS", "node unavailable")
        return
    try:
        r = subprocess.run(
            [node, str(PP / "hooks" / "claude_md_linter_stop.js")],
            input="{}", capture_output=True, text=True, timeout=15)
    except Exception as exc:  # noqa: BLE001
        _fail("V-LINTER-RUNS", f"{type(exc).__name__}: {exc}")
        return
    if r.returncode == 0 and '"continue"' in r.stdout:
        _ok("V-LINTER-RUNS", "ran, emitted continue, rc 0")
    else:
        _fail("V-LINTER-RUNS", f"rc={r.returncode} out={r.stdout[:80]!r}")


def test_baseline():
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q",
             "-p", "no:cacheprovider"],
            cwd=str(PP), capture_output=True, text=True, timeout=180)
    except Exception as exc:  # noqa: BLE001
        _fail("V-BASELINE-INTACT", f"{type(exc).__name__}: {exc}")
        return
    last = (r.stdout.strip().splitlines() or [""])[-1]
    if r.returncode == 0 and "passed" in r.stdout and "failed" not in last:
        _ok("V-BASELINE-INTACT", last.strip())
    else:
        _fail("V-BASELINE-INTACT", f"rc={r.returncode} | {last}")


def main() -> int:
    print("=" * 64)
    print("test_claude_md_router -- CLAUDE.md Router V-gates (M5)")
    print("=" * 64)
    for fn in (test_size, test_router, test_safety_intact, test_trim_safe,
               test_firewall_blocks, test_firewall_allows, test_linter_runs,
               test_baseline):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            _fail(fn.__name__, f"{type(exc).__name__}: {exc}")
    total = _passes + _fails
    print(f"CLAUDE_MD_ROUTER_PASS={_passes}/{total}  fails={_fails}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
