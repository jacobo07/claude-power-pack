#!/usr/bin/env python3
"""audit_spawn_windows.py -- F0 regression gate: no visible cmd.exe window.

Every child-process spawn from a PP-owned hook MUST carry ``windowsHide: true``
(Node) or ``-WindowStyle Hidden`` / ``-NoNewWindow`` (PowerShell), or it flashes
a console window on Windows each time the hook fires. FASE -1 (2026-06-22) found
all PP-owned hooks already compliant; this gate keeps it that way -- a future
spawn that forgets the flag fails the gate instead of shipping a flash.

The flash sources are NOT only in the PP repo (2026-06-23 extension): the live
``~/.claude/settings.json`` registers hook *commands* directly, and a
``powershell.exe`` / ``cmd.exe`` launcher there without a hide flag flashes too
(the SessionEnd orphan-reaper was exactly this). ``--settings`` audits those.

Scheduled Tasks are the THIRD source (2026-06-30 extension, T-SPAWN-WINDOW-001):
a Windows Scheduled Task running ``LogonType=InteractiveToken`` with a console
launcher (``python.exe``, ``node.exe``) or a ``powershell.exe`` / ``cmd.exe``
action that lacks a hide flag flashes a window in the Owner's interactive
session every time it fires -- the empirical cause of the "cmd.exe colgado"
interruptions (7 of 8 PP tasks were flashing: 5 python.exe + 2 unhidden
PowerShell). The fix is ``pythonw.exe`` for python tasks and
``-WindowStyle Hidden`` for PowerShell tasks. ``--schtasks`` audits those.

Scope:
  * default          -- PP-owned hooks under the repo (hooks/, modules/**/hooks/).
                        A missing flag here is a real PP defect -> FAIL (exit 1).
  * --settings       -- ALSO audit ~/.claude/settings.json hook commands for
                        powershell/cmd launchers missing the hide flag. Contributes
                        to the exit code (host-local, so opt-in not default).
  * --schtasks       -- ALSO audit Windows Scheduled Task actions (host-local,
                        Windows-only). A flashing task whose launcher references a
                        PP/.claude path is OWNED -> gated FAIL. Any other flashing
                        task (OneDrive/NVIDIA/Opera/Owner's other projects) is
                        ADVISORY only -- never fail the PP gate on tasks PP does
                        not own (honest scoping; cf. HR-001).
  * --live           -- ALSO scan ~/.claude/hooks (the copies Claude Code runs).
                        Non-PP/third-party files (gsd-*, get-shit-done) are
                        reported ADVISORY only -- never fail the PP gate on code
                        PP does not own (honest scoping; cf. HR-001).

Node hook commands in settings.json are NOT flagged: Claude Code spawns hook
processes itself (hidden) and their child spawns are covered by the JS scan.
What PP cannot control -- Claude Code's own Bash/PowerShell tool spawning and
plugin-internal MCP child processes -- is out of scope by construction.

Heuristic, not a JS/PS parser: for each spawn/spawnSync/exec* call we balance
parens (string-aware) to isolate the call text, then look for the hide flag
inside it. execSync/execFileSync with a string command can also flash, so they
are audited too.

Usage:
  python tools/audit_spawn_windows.py                 # PP gate, exit 0/1
  python tools/audit_spawn_windows.py --settings      # + settings.json gate
  python tools/audit_spawn_windows.py --schtasks      # + Scheduled Task gate
  python tools/audit_spawn_windows.py --live          # + advisory live scan
  python tools/audit_spawn_windows.py --json          # machine output
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
_LIVE_HOOKS = Path.home() / ".claude" / "hooks"
_SETTINGS_JSON = Path.home() / ".claude" / "settings.json"

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
# Accepted hidden-window markers in a settings.json launcher command string.
_CMD_HIDE = ("-windowstyle hidden", "-w hidden", "-nonewwindow")

# Console launchers a Scheduled Task can use that flash a window unless run via
# their windowless variant. python.exe -> pythonw.exe; node.exe has no clean
# windowless variant (must run under a hidden launcher).
_CONSOLE_TASK_EXE = ("python.exe", "py.exe", "node.exe")
_SHELL_TASK_EXE = ("powershell.exe", "pwsh.exe", "powershell", "cmd.exe", "cmd")

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


def _cmd_needs_hide(cmd: str) -> str | None:
    """Reason a settings.json hook *command* would flash a window, else None.

    Node launchers are fine: Claude Code spawns the hook hidden and the hook's
    own child spawns are covered by the JS scan. Only a powershell/cmd launcher
    that does not itself request a hidden window is a flash risk."""
    low = cmd.lower()
    if "powershell" in low or "pwsh" in low:
        return (None if any(t in low for t in _CMD_HIDE)
                else "powershell launcher without -WindowStyle Hidden")
    if low.startswith("cmd.exe") or low.startswith("cmd /c") \
            or low.startswith('"cmd.exe"') or low.startswith("cmd ") :
        return "cmd.exe launcher (cannot self-hide; flashes unless parent hides)"
    return None


def _scan_settings_hooks(path: Path | None = None) -> list[dict]:
    """Audit ~/.claude/settings.json hook command strings (host-local)."""
    p = path or _SETTINGS_JSON
    findings: list[dict] = []
    if not p.is_file():
        return findings
    try:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return findings
    hooks = data.get("hooks", {})
    if not isinstance(hooks, dict):
        return findings
    for event, groups in hooks.items():
        if not isinstance(groups, list):
            continue
        for group in groups:
            for h in (group.get("hooks") or []):
                cmd = h.get("command")
                if not isinstance(cmd, str):
                    continue
                reason = _cmd_needs_hide(cmd)
                if reason:
                    findings.append({
                        "file": str(p), "event": event,
                        "reason": reason, "kind": "settings-hook",
                        "snippet": cmd[:100],
                    })
    return findings


# ---------------------------------------------------------------------------
# Scheduled Task scan (Windows-only, host-local, opt-in via --schtasks)
# ---------------------------------------------------------------------------

def _list_task_names() -> list[str]:
    """Root-level (non-Microsoft) Scheduled Task names via schtasks csv."""
    try:
        out = subprocess.run(
            ["schtasks", "/query", "/fo", "csv", "/nh"],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    names: set[str] = set()
    for line in out.stdout.splitlines():
        line = line.strip()
        if not line.startswith('"'):
            continue
        name = line.split('","', 1)[0].strip('"').strip()
        # Root tasks look like ``\PP-Miner-V2`` (single backslash). Microsoft
        # built-ins live under ``\Microsoft\...`` (multiple) -> excluded.
        if name.startswith("\\") and name.count("\\") == 1:
            names.add(name)
    return sorted(names)


def _task_exec_actions(name: str) -> list[tuple[str, str]]:
    """(Command, Arguments) pairs for each Exec action of a task via /xml."""
    try:
        out = subprocess.run(
            ["schtasks", "/query", "/tn", name, "/xml"],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    txt = out.stdout.lstrip("﻿")
    try:
        root = ET.fromstring(txt)
    except ET.ParseError:
        return []
    actions: list[tuple[str, str]] = []
    for el in root.iter():
        if not el.tag.endswith("Exec"):
            continue
        cmd = ""
        args = ""
        for child in el:
            if child.tag.endswith("Command"):
                cmd = (child.text or "").strip()
            elif child.tag.endswith("Arguments"):
                args = (child.text or "").strip()
        actions.append((cmd, args))
    return actions


def _task_flash_reason(cmd: str, args: str) -> str | None:
    """Reason a Scheduled Task action would flash a window, else None."""
    base = os.path.basename(cmd).lower().strip('"')
    low_args = args.lower()
    if base in _CONSOLE_TASK_EXE:
        if base in ("python.exe", "py.exe"):
            return "python.exe console app (use pythonw.exe to avoid flash)"
        return "node.exe console app (no windowless variant; hide via launcher)"
    if base in _SHELL_TASK_EXE:
        if "powershell" in base or "pwsh" in base:
            return (None if any(t in low_args for t in _CMD_HIDE)
                    else "powershell action without -WindowStyle Hidden")
        return "cmd.exe action (flashes; wrap target to hide)"
    return None


def _task_is_owned(cmd: str, args: str) -> bool:
    """True if the task launches a script PP/.claude owns (-> gated FAIL)."""
    blob = f"{cmd} {args}".lower().replace("/", "\\")
    return "claude-power-pack" in blob or "\\.claude\\" in blob


def _scan_schtasks() -> list[dict]:
    """Audit Windows Scheduled Task actions for window-flash launchers."""
    if os.name != "nt":
        return []
    findings: list[dict] = []
    for name in _list_task_names():
        for cmd, args in _task_exec_actions(name):
            reason = _task_flash_reason(cmd, args)
            if not reason:
                continue
            findings.append({
                "task": name, "kind": "schtask", "reason": reason,
                "owned": _task_is_owned(cmd, args),
                "snippet": f"{os.path.basename(cmd)} {args}".strip()[:100],
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


def audit(include_live: bool = False,
          include_settings: bool = False,
          include_schtasks: bool = False) -> dict:
    pp_files = _pp_hook_files()
    pp_findings: list[dict] = []
    for f in pp_files:
        pp_findings.extend(_scan(f))

    settings_findings: list[dict] = []
    if include_settings:
        settings_findings = _scan_settings_hooks()

    schtasks_findings: list[dict] = []
    if include_schtasks:
        schtasks_findings = _scan_schtasks()
    schtasks_owned_fail = [f for f in schtasks_findings if f.get("owned")]

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

    gated_fail = len(pp_findings)
    if include_settings:
        gated_fail += len(settings_findings)
    if include_schtasks:
        gated_fail += len(schtasks_owned_fail)
    return {
        "pp_files_scanned": len(pp_files),
        "pp_findings": pp_findings,
        "settings_findings": settings_findings,
        "schtasks_findings": schtasks_findings,
        "live_advisory": live_advisory,
        "passed": gated_fail == 0,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--settings", action="store_true",
                    help="also gate ~/.claude/settings.json hook launchers")
    ap.add_argument("--schtasks", action="store_true",
                    help="also gate Windows Scheduled Task actions (owned only)")
    ap.add_argument("--live", action="store_true",
                    help="also scan ~/.claude/hooks (advisory only)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    result = audit(include_live=args.live, include_settings=args.settings,
                   include_schtasks=args.schtasks)
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

    if args.settings:
        sf = result["settings_findings"]
        if sf:
            print(f"\n  -- settings.json launchers ({len(sf)}; GATED) --")
            for f in sf:
                print(f"  [FAIL] settings.json[{f['event']}] -- "
                      f"{f['reason']} | {f['snippet']}")
        else:
            print("\n  [OK] settings.json hook launchers all hide their window")

    if args.schtasks:
        tf = result["schtasks_findings"]
        owned = [f for f in tf if f.get("owned")]
        adv = [f for f in tf if not f.get("owned")]
        if owned:
            print(f"\n  -- Scheduled Tasks ({len(owned)} PP-owned; GATED) --")
            for f in owned:
                print(f"  [FAIL] {f['task']} -- {f['reason']} | {f['snippet']}")
        else:
            print("\n  [OK] all PP-owned Scheduled Tasks hide their window")
        if adv:
            print(f"  -- Scheduled Tasks ({len(adv)} third-party; advisory) --")
            for f in adv:
                print(f"  [ADVISORY] {f['task']} -- {f['reason']} "
                      f"| {f['snippet']}")

    if args.live:
        adv = result["live_advisory"]
        if adv:
            print(f"\n  -- LIVE advisory ({len(adv)}; not gated) --")
            for f in adv:
                tag = "third-party" if f.get("third_party") else "PP-live-drift"
                loc = f.get("line", f.get("event", "?"))
                print(f"  [ADVISORY:{tag}] {f['file']}:{loc} "
                      f"{f['kind']} | {f['snippet']}")
        else:
            print("\n  -- LIVE advisory: clean --")

    total = n
    extra = ""
    if args.settings:
        extra += f" settings_fails={len(result['settings_findings'])}"
    if args.schtasks:
        owned_n = len([f for f in result['schtasks_findings'] if f.get('owned')])
        extra += f" schtask_owned_fails={owned_n}"
    print(f"SPAWN_WINDOW_AUDIT_PASS={ok}/{total}  "
          f"threshold={total}/{total}  fails={len(fails)}{extra}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
