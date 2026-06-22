#!/usr/bin/env python3
"""audit_spawn_windows.py -- F0 regression gate: no visible cmd.exe window.

Every child-process spawn from a PP-owned hook MUST carry ``windowsHide: true``
(Node) or ``-WindowStyle Hidden`` / ``-NoNewWindow`` (PowerShell), or it flashes
a console window on Windows each time the hook fires. FASE -1 (2026-06-22) found
all PP-owned hooks already compliant; this gate keeps it that way -- a future
spawn that forgets the flag fails the gate instead of shipping a flash.

Scope:
  * default          -- PP-owned hooks under the repo (hooks/, modules/**/hooks/).
                        A missing flag here is a real PP defect -> FAIL (exit 1).
  * --live           -- ALSO scan ~/.claude/hooks (the copies Claude Code runs).
                        Non-PP/third-party files (gsd-*, get-shit-done) are
                        reported ADVISORY only -- never fail the PP gate on code
                        PP does not own (honest scoping; cf. HR-001).

Heuristic, not a JS/PS parser: for each spawn/spawnSync/exec* call we balance
parens (string-aware) to isolate the call text, then look for the hide flag
inside it. execSync/execFileSync with a string command can also flash, so they
are audited too. False-positive guard: a call whose first arg is a JS string
that is clearly not a process (none today) would still be flagged -- acceptable,
since the fix (add windowsHide) is harmless.

Usage:
  python tools/audit_spawn_windows.py                 # PP gate, exit 0/1
  python tools/audit_spawn_windows.py --live          # + advisory live scan
  python tools/audit_spawn_windows.py --json          # machine output
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
_LIVE_HOOKS = Path.home() / ".claude" / "hooks"

# Node spawn-family call openers. spawnSync before spawn so the longer token
# wins. Bare ``exec`` is deliberately EXCLUDED: ``regex.exec(str)`` /
# ``re.exec()`` collide with it and child_process.exec is rare + async (low
# flash risk) in these hooks. The synchronous flashers (execSync/execFileSync)
# and the spawn family are what matter for the no-visible-window contract.
_NODE_CALL = re.compile(
    r"\b(spawnSync|spawn|execFileSync|execSync)\s*\(")
# PowerShell process launcher.
_PS_CALL = re.compile(r"Start-Process\b", re.IGNORECASE)

_NODE_HIDE = "windowshide"
_PS_HIDE = ("-windowstyle hidden", "-windowstyle' hidden", "-nonewwindow")

# Third-party (non-PP) live hooks: advisory only, never fail the PP gate.
_THIRD_PARTY = ("gsd-", "get-shit-done", "carl-")


def _is_third_party(path: Path) -> bool:
    return any(tok in path.name.lower() for tok in _THIRD_PARTY)


def _line_of(text: str, idx: int) -> int:
    return text.count("\n", 0, idx) + 1


def _balanced_call(text: str, open_paren: int) -> str:
    """Return the substring from ``open_paren`` ('(') to its matching ')',
    skipping over ' " ` quoted strings so parens inside strings do not throw
    off the depth count. If unbalanced (truncated), returns to end of text."""
    depth = 0
    i = open_paren
    n = len(text)
    quote = ""
    while i < n:
        c = text[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = ""
        elif c in "'\"`":
            quote = c
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[open_paren:i + 1]
        i += 1
    return text[open_paren:]


def _scan_js(path: Path) -> list[dict]:
    findings: list[dict] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return findings
    for m in _NODE_CALL.finditer(text):
        open_paren = text.index("(", m.start())
        call = _balanced_call(text, open_paren)
        if _NODE_HIDE not in call.lower():
            findings.append({
                "file": str(path),
                "line": _line_of(text, m.start()),
                "kind": m.group(1),
                "lang": "js",
                "snippet": text[m.start():m.start() + 80]
                .splitlines()[0].strip(),
            })
    return findings


def _scan_ps(path: Path) -> list[dict]:
    findings: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8",
                               errors="replace").splitlines()
    except OSError:
        return findings
    for i, ln in enumerate(lines, start=1):
        if not _PS_CALL.search(ln):
            continue
        low = ln.lower()
        if any(tok in low for tok in _PS_HIDE):
            continue
        findings.append({
            "file": str(path), "line": i, "kind": "Start-Process",
            "lang": "ps1", "snippet": ln.strip()[:80],
        })
    return findings


def _pp_hook_files() -> list[Path]:
    """PP-owned hook scripts: repo hooks/ + modules/**/hooks/, .js and .ps1,
    excluding backups, pycache, tests, and node_modules."""
    out: list[Path] = []
    roots = [_PP_ROOT / "hooks"]
    roots += list((_PP_ROOT / "modules").glob("**/hooks"))
    seen: set[Path] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for p in root.rglob("*"):
            if p.suffix not in (".js", ".ps1"):
                continue
            if p in seen:
                continue
            low = str(p).lower()
            if any(b in low for b in (".bak", "node_modules", "__pycache__",
                                      f"{os.sep}tests{os.sep}", ".removed")):
                continue
            seen.add(p)
            out.append(p)
    return sorted(out)


def _scan(path: Path) -> list[dict]:
    return _scan_ps(path) if path.suffix == ".ps1" else _scan_js(path)


def audit(include_live: bool = False) -> dict:
    pp_files = _pp_hook_files()
    pp_findings: list[dict] = []
    for f in pp_files:
        pp_findings.extend(_scan(f))

    live_advisory: list[dict] = []
    if include_live and _LIVE_HOOKS.is_dir():
        for p in sorted(_LIVE_HOOKS.glob("*.js")) + \
                sorted(_LIVE_HOOKS.glob("*.ps1")):
            low = str(p).lower()
            if any(b in low for b in (".bak", ".removed")):
                continue
            for fnd in _scan(p):
                fnd["third_party"] = _is_third_party(p)
                live_advisory.append(fnd)

    return {
        "pp_files_scanned": len(pp_files),
        "pp_findings": pp_findings,
        "live_advisory": live_advisory,
        "passed": len(pp_findings) == 0,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--live", action="store_true",
                    help="also scan ~/.claude/hooks (advisory only)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    result = audit(include_live=args.live)
    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result["passed"] else 1

    n = result["pp_files_scanned"]
    fails = result["pp_findings"]
    ok = n - len({(f["file"]) for f in fails})
    for f in fails:
        rel = os.path.relpath(f["file"], _PP_ROOT)
        print(f"  [FAIL] {rel}:{f['line']} {f['kind']} -- "
              f"no hide flag -> console flash | {f['snippet']}")
    if not fails:
        print(f"  [OK] all {n} PP hook spawns carry the hide flag")

    if args.live:
        adv = result["live_advisory"]
        if adv:
            print(f"\n  -- LIVE advisory ({len(adv)}; not gated) --")
            for f in adv:
                tag = "third-party" if f.get("third_party") else "PP-live-drift"
                print(f"  [ADVISORY:{tag}] {f['file']}:{f['line']} "
                      f"{f['kind']} | {f['snippet']}")
        else:
            print("\n  -- LIVE advisory: clean --")

    total = n
    print(f"SPAWN_WINDOW_AUDIT_PASS={ok}/{total}  "
          f"threshold={total}/{total}  fails={len(fails)}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
