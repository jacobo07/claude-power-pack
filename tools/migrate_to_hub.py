#!/usr/bin/env python3
"""migrate_to_hub.py -- ONE-TIME OWNER SETUP for SCS C23.

Collapses the five PP-owned SessionStart entries in
~/.claude/settings.json into ONE hub entry running
hooks/session_start_hub.js. The five entries being consolidated:

    1. node "<PP>/hooks/jit_warm.js"
    2. node "<PP>/hooks/restart_resume.js"
    3. node "<PP>/hooks/async_wrapper.js" -- auto-compact-session-start-cleanup.ps1
    4. node "<PP>/hooks/async_wrapper.js" -- tco_compact_gate.py --session-start-check
    5. node "<PP>/hooks/async_wrapper.js" -- auto-vault-bootstrap.js

Replaced with ONE entry:

    node "<PP>/hooks/session_start_hub.js"

Owner-side hooks (not under PP control) are left UNTOUCHED. The hub does
all the same work as the five entries combined (verified by per-hook
log line in %TEMP%/pp-session-hub.log).

Rationale: T-NODE-COLD-001 (Node cold-start floor) -- each separate
entry pays 30-150 ms on Windows, even when the body is a one-line
spawn-and-exit. One hub entry pays the cold start ONCE, with all four
detached child spawns adding ~3 ms each.

USAGE:
    python tools/migrate_to_hub.py --dry-run    # preview
    python tools/migrate_to_hub.py              # commit

Idempotent. Backup written before any change. Safe to re-run after a
settings.json mutation re-introduces a PP entry that is already in the
hub.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PP_PATH = Path(__file__).resolve().parents[1]
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
HUB_PATH = (PP_PATH / "hooks" / "session_start_hub.js").as_posix()

# Substrings that identify the PP-owned SessionStart entries to collapse.
# Any settings.json entry whose first hook's command contains one of these
# substrings AND is on SessionStart is removed and replaced by the hub.
PP_ENTRY_MARKERS = (
    "jit_warm.js",
    "restart_resume.js",
    "async_wrapper.js",
)
# Marker that identifies the hub entry itself (for idempotency).
HUB_ENTRY_MARKER = "session_start_hub.js"


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".",
                               dir=str(path.parent), suffix=".tmp")
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


def _entry_is_pp(entry: dict) -> bool:
    for hh in entry.get("hooks", []):
        cmd = hh.get("command", "")
        for marker in PP_ENTRY_MARKERS:
            if marker in cmd:
                return True
    return False


def _entry_is_hub(entry: dict) -> bool:
    for hh in entry.get("hooks", []):
        if HUB_ENTRY_MARKER in hh.get("command", ""):
            return True
    return False


def _build_hub_entry() -> dict:
    return {
        "hooks": [
            {
                "type": "command",
                "command": f'node "{HUB_PATH}"',
            }
        ],
    }


def _plan_changes(settings: dict) -> tuple[list[str], dict]:
    new = json.loads(json.dumps(settings))  # deep copy
    desc: list[str] = []

    hooks = new.get("hooks", {})
    ss = hooks.get("SessionStart", [])
    if not isinstance(ss, list):
        return ["[SKIP] SessionStart is not a list"], new

    # Detect existing PP entries + existing hub.
    pp_entries: list[dict] = []
    other_entries: list[dict] = []
    hub_already_present = False
    for entry in ss:
        if _entry_is_hub(entry):
            hub_already_present = True
            other_entries.append(entry)
        elif _entry_is_pp(entry):
            pp_entries.append(entry)
        else:
            other_entries.append(entry)

    if not pp_entries and hub_already_present:
        return ["[OK] Hub already present + no stale PP entries -- nothing to do"], new
    if not pp_entries and not hub_already_present:
        return ["[OK] No PP entries to migrate -- adding hub only"], _add_hub(new, other_entries)

    # Build the migration.
    for entry in pp_entries:
        # Reach into the entry's first hook command for the description.
        cmd = entry.get("hooks", [{}])[0].get("command", "?")
        desc.append(f"DROP PP entry: {cmd[:90]}")
    if not hub_already_present:
        desc.append(f'ADD hub entry: node "{HUB_PATH}"')
        other_entries.append(_build_hub_entry())
    else:
        desc.append("KEEP existing hub entry (idempotent)")

    hooks["SessionStart"] = other_entries
    new["hooks"] = hooks
    return desc, new


def _add_hub(settings: dict, other_entries: list[dict]) -> dict:
    other_entries = list(other_entries) + [_build_hub_entry()]
    hooks = settings.get("hooks", {})
    hooks["SessionStart"] = other_entries
    settings["hooks"] = hooks
    return settings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--dry-run", action="store_true",
                    help="Preview planned changes; do not write.")
    args = ap.parse_args(argv)

    if not SETTINGS_PATH.is_file():
        print(f"[FAIL] settings.json missing at {SETTINGS_PATH}",
              file=sys.stderr)
        return 2

    raw = SETTINGS_PATH.read_text(encoding="utf-8-sig")
    try:
        data = json.loads(raw)
    except ValueError as exc:
        print(f"[FAIL] settings.json malformed: {exc}", file=sys.stderr)
        return 2

    desc, new = _plan_changes(data)

    print("=" * 60)
    print("PP SessionStart HUB MIGRATION  --  ONE-TIME OWNER SETUP")
    print("=" * 60)
    print(f"Target : {SETTINGS_PATH}")
    print(f"Hub    : {HUB_PATH}")
    print(f"Mode   : {'DRY RUN (no changes)' if args.dry_run else 'COMMIT'}")
    print()

    if not desc:
        print("[OK] Nothing to do.")
        return 0

    print(f"Planned changes ({len(desc)}):")
    for line in desc:
        print(f"  - {line}")
    print()

    if args.dry_run:
        print("=" * 60)
        print("DRY RUN COMPLETE -- settings.json untouched.")
        return 0

    iso = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = SETTINGS_PATH.with_suffix(f".pre-hub-migrate-{iso}.bak")
    shutil.copy2(SETTINGS_PATH, backup)
    print(f"[BACKUP] {backup}")

    _atomic_write_json(SETTINGS_PATH, new)

    print()
    print("=" * 60)
    print("MIGRATED")
    print("=" * 60)
    print(f"Backup : {backup}")
    print()
    print("NEXT STEPS:")
    print("  1. Close every active Claude Code session.")
    print("  2. Reopen Claude Code (or `claude --resume`).")
    print(f"  3. Verify timing: "
          f"python {PP_PATH / 'tools' / 'measure_session_start.py'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
