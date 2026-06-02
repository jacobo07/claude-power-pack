#!/usr/bin/env python3
"""PP Global Hooks Registration -- ONE-TIME OWNER SETUP.

Registers the PP hooks in ``~/.claude/settings.json`` so the proactive
agents activate while the Owner works. This script is deliberately
NOT invoked by Claude Code in auto-mode. The Owner runs it manually
from their terminal AFTER closing all Claude Code sessions.

USAGE:
    python tools/register_global_hooks.py --dry-run    # preview
    python tools/register_global_hooks.py              # commit

HOOKS REGISTERED:
    H1 PreToolUse  Write|Edit|MultiEdit -> uqf_pre_edit_gate.js
       (pp-code-reviewer + pp-uqf-auditor advisories on .py writes)
    H2 PostToolUse Bash                  -> osa_deploy_detector.js
       (OSA audit recommendation when deploy verb detected)
    H3 PostToolUse Bash                  -> bug-hunter-ceps-bridge.js
       (pp-ceps-analyst auto-capture on Bash errors)
    H4 SessionStart                       -> tco_compact_gate.py
       --session-start-check
       (pp-tco-advisor warning if context_pct >= 70)
    H5 Stop                              -> jobs_woz_gate.js
       (Jobs/Woz advisory on assistant turn slop tokens)
    H6 SessionStart                       -> jit_warm.js
       (jit_skill_loader pre-warmer -- masks first-prompt lag,
        sealed BL-JIT-001 2026-05-31)
    H7 SessionStart                       -> restart_resume.js
       (/restart marker detector, universal kclaude fallback)
    H8 PreToolUse  Bash                  -> cascade_check_bash.js
       (Cascade Prevention block on dangerous/C4 commands;
        HR-CASCADE-001/002)
    H9 PreToolUse  Write|Edit|MultiEdit  -> secret_firewall_gate.js
       (Secret Firewall block on CRITICAL secret; HR-SECRET-001)
    H10 Stop                             -> output_contract_stop.js
       (OutputContracts slop advisory, never blocks; HR-OUTPUT-001)

Sealed BL-HOOKS-REG-001 (2026-05-29) + BL-JIT-001 (2026-05-31)
+ BL-INTEGRATION-WIRING (2026-06-02, +cascade/secret/output).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import os
from datetime import datetime, timezone
from pathlib import Path

PP_PATH = Path(__file__).resolve().parents[1]
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"


def _hooks_to_register() -> list[dict]:
    """Spec for the five PP hooks.

    Each entry: event, matcher (optional), command string, marker.
    Markers are unique substrings used for idempotency detection.
    """
    pp = str(PP_PATH)
    return [
        {
            "event": "PreToolUse",
            "matcher": "Write|Edit|MultiEdit",
            "command":
                f'node "{pp}/hooks/uqf_pre_edit_gate.js"',
            "marker": "uqf_pre_edit_gate",
            "description":
                "pp-code-reviewer + pp-uqf-auditor on .py writes",
        },
        {
            "event": "PostToolUse",
            "matcher": "Bash",
            "command":
                f'node "{pp}/hooks/osa_deploy_detector.js"',
            "marker": "osa_deploy_detector",
            "description": "OSA audit recommendation on deploy commands",
        },
        {
            "event": "PostToolUse",
            "matcher": "Bash",
            "command":
                f'node "{pp}/hooks/bug-hunter-ceps-bridge.js"',
            "marker": "bug-hunter-ceps-bridge",
            "description": "pp-ceps-analyst auto-capture on Bash errors",
        },
        {
            "event": "SessionStart",
            "matcher": None,
            "command":
                f'python "{pp}/tools/tco_compact_gate.py" '
                "--session-start-check",
            "marker": "session-start-check",
            "description":
                "pp-tco-advisor warning when context_pct >= 70",
        },
        {
            "event": "Stop",
            "matcher": None,
            "command":
                f'node "{pp}/hooks/jobs_woz_gate.js"',
            "marker": "jobs_woz_gate",
            "description": "Jobs/Woz advisory on assistant turn slop",
        },
        {
            "event": "SessionStart",
            "matcher": None,
            "command":
                f'node "{pp}/hooks/jit_warm.js"',
            "marker": "jit_warm",
            "description":
                "jit_skill_loader pre-warmer (mask first-prompt lag)",
        },
        {
            "event": "SessionStart",
            "matcher": None,
            "command":
                f'node "{pp}/hooks/restart_resume.js"',
            "marker": "restart_resume",
            "description":
                "/restart marker detector (universal kclaude fallback)",
        },
        {
            "event": "PreToolUse",
            "matcher": "Bash",
            "command":
                f'node "{pp}/hooks/cascade_check_bash.js"',
            "marker": "cascade_check_bash",
            "description":
                "Cascade Prevention block on dangerous/C4 Bash commands "
                "(HR-CASCADE-001/002)",
        },
        {
            "event": "PreToolUse",
            "matcher": "Write|Edit|MultiEdit",
            "command":
                f'node "{pp}/hooks/secret_firewall_gate.js"',
            "marker": "secret_firewall_gate",
            "description":
                "Secret Firewall block on CRITICAL secret in writes "
                "(HR-SECRET-001)",
        },
        {
            "event": "Stop",
            "matcher": None,
            "command":
                f'node "{pp}/hooks/output_contract_stop.js"',
            "marker": "output_contract_stop",
            "description":
                "OutputContracts advisory on slop tokens, never blocks "
                "(HR-OUTPUT-001)",
        },
    ]


def _verify_hook_files_exist(specs: list[dict]) -> list[Path]:
    """Return list of missing file paths."""
    pp = str(PP_PATH)
    missing: list[Path] = []
    for spec in specs:
        cmd = spec["command"]
        if " " not in cmd:
            continue
        first_arg = cmd.split('"')
        if len(first_arg) < 2:
            continue
        target = Path(first_arg[1])
        if not target.is_file():
            missing.append(target)
    return missing


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent),
                               suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _classify(specs: list[dict], existing_str: str) -> tuple[list, list]:
    pending = []
    already = []
    for s in specs:
        if s["marker"] in existing_str:
            already.append(s)
        else:
            pending.append(s)
    return pending, already


def _build_entry(spec: dict) -> dict:
    entry: dict = {"hooks": [{
        "type": "command",
        "command": spec["command"],
    }]}
    if spec["matcher"]:
        entry["matcher"] = spec["matcher"]
    return entry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=("Register the PP hooks in "
                     "~/.claude/settings.json (ONE-TIME OWNER SETUP)."))
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the planned changes without "
                             "modifying settings.json or creating a "
                             "backup.")
    args = parser.parse_args(argv)

    if not SETTINGS_PATH.is_file():
        print(f"[FAIL] settings.json not found at {SETTINGS_PATH}",
              file=sys.stderr)
        return 2

    specs = _hooks_to_register()
    missing = _verify_hook_files_exist(specs)
    if missing:
        print("[FAIL] Hook files missing on disk:")
        for m in missing:
            print(f"  - {m}")
        print()
        print("Run this script from the PP repo root after the missing")
        print("hooks have been created.")
        return 3

    existing_raw = SETTINGS_PATH.read_text(encoding="utf-8-sig")
    try:
        existing = json.loads(existing_raw)
    except ValueError as exc:
        print(f"[FAIL] settings.json malformed: {exc}", file=sys.stderr)
        return 2

    pending, already = _classify(specs, existing_raw)

    print("=" * 60)
    print("PP HOOKS REGISTRATION  --  ONE-TIME OWNER SETUP")
    print("=" * 60)
    print(f"Repo  : {PP_PATH}")
    print(f"Target: {SETTINGS_PATH}")
    print(f"Mode  : {'DRY RUN (no changes)' if args.dry_run else 'COMMIT'}")
    print()

    if already:
        print(f"Already registered ({len(already)}):")
        for spec in already:
            print(f"  [{spec['event']:13s}] {spec['marker']}")
        print()

    if not pending:
        print(f"[OK] All {len(specs)} PP hooks already registered. "
              "Nothing to do.")
        return 0

    print(f"To register ({len(pending)}):")
    for spec in pending:
        match = spec["matcher"] or "*"
        print(f"  [{spec['event']:13s}] matcher={match}")
        print(f"    -> {spec['command']}")
        print(f"       ({spec['description']})")
    print()

    if args.dry_run:
        print("=" * 60)
        print("DRY RUN COMPLETE -- settings.json untouched.")
        print("Re-run without --dry-run to commit.")
        return 0

    iso = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = SETTINGS_PATH.with_suffix(f".pre-pp-hooks-{iso}.bak")
    shutil.copy2(SETTINGS_PATH, backup)
    print(f"[BACKUP] {backup}")

    hooks_root = existing.setdefault("hooks", {})
    for spec in pending:
        event = spec["event"]
        bucket = hooks_root.setdefault(event, [])
        if not isinstance(bucket, list):
            print(f"[FAIL] hooks.{event} is not a list; aborting.")
            return 4
        bucket.append(_build_entry(spec))

    _atomic_write_json(SETTINGS_PATH, existing)

    print()
    print("=" * 60)
    print("REGISTERED")
    print("=" * 60)
    for spec in pending:
        print(f"  [{spec['event']:13s}] {spec['marker']}")

    print()
    print("NEXT STEPS:")
    print("  1. Close every active Claude Code session (hooks load")
    print("     once at session start).")
    print("  2. Reopen Claude Code (or `claude --resume`).")
    print("  3. Run: python tools/check_hook_status.py")
    print(f"  4. Backup kept at: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
