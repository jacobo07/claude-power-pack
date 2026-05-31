#!/usr/bin/env python3
"""optimize_session_start.py -- ONE-TIME OWNER SETUP.

Reduces ~/.claude/settings.json SessionStart wall time from ~7400 ms
(measured 2026-05-31, BL-LAG-001) to <500 ms by:

  1. REMOVING the duplicate orphan-dev-server-reaper.ps1 entry from
     SessionStart. Its only job (per the script's own header doc) is
     cleanup on session END; the SessionStart copy was a 4700 ms
     no-op gain because no orphans exist at session start by definition.
     The SessionEnd registration is preserved (that one matters).

  2. WRAPPING two remaining slow Owner-side hooks in
     hooks/async_wrapper.js (PP-internal, detached spawner):
       - auto-compact-session-start-cleanup.ps1  (~900 ms)
       - tco_compact_gate.py --session-start-check  (~540 ms)
     Both do cleanup / advisory work that does NOT need to be
     synchronous at SessionStart.

USAGE:
    python tools/optimize_session_start.py --dry-run    # preview
    python tools/optimize_session_start.py              # commit

Idempotent. Backup written before changes. The Owner re-runs after a
settings.json mutation that re-introduces the slow entries.

Sealed BL-LAG-001 (2026-05-31).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PP_PATH = Path(__file__).resolve().parents[1]
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
ASYNC_WRAPPER = (PP_PATH / "hooks" / "async_wrapper.js").as_posix()


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


# Markers (substring matches) that identify the entries we touch.
ORPHAN_REAPER_MARKER = "orphan-dev-server-reaper.ps1"
WRAP_TARGETS = [
    {
        "marker": "auto-compact-session-start-cleanup.ps1",
        "label": "auto-compact-session-start-cleanup",
    },
    {
        "marker": "tco_compact_gate.py",
        "label": "tco-compact-gate-session-start",
    },
]
ASYNC_WRAPPED_TAG = "async_wrapper.js"  # idempotency tag


def _build_wrapped(orig_cmd: str) -> str:
    """Wrap a command in async_wrapper.js. Idempotent: already-wrapped
    commands are returned unchanged."""
    if ASYNC_WRAPPED_TAG in orig_cmd:
        return orig_cmd
    # Wrap with " -- " separator the wrapper expects.
    return f'node "{ASYNC_WRAPPER}" -- {orig_cmd}'


def _plan_changes(settings: dict) -> tuple[list[str], dict]:
    """Compute the set of changes. Returns (description, new_settings)."""
    new = json.loads(json.dumps(settings))  # deep copy
    desc: list[str] = []

    hooks = new.get("hooks", {})
    ss = hooks.get("SessionStart", [])
    if not isinstance(ss, list):
        return ["[SKIP] SessionStart is not a list"], new

    # Pass 1: drop the orphan reaper entry on SessionStart.
    keep: list[dict] = []
    for entry in ss:
        kill = False
        for hh in entry.get("hooks", []):
            cmd = hh.get("command", "")
            if ORPHAN_REAPER_MARKER in cmd:
                kill = True
                desc.append(f"DROP SessionStart entry: {cmd[:80]}")
                break
        if not kill:
            keep.append(entry)
    ss = keep

    # Pass 2: wrap slow entries.
    for entry in ss:
        for hh in entry.get("hooks", []):
            cmd = hh.get("command", "")
            for target in WRAP_TARGETS:
                if target["marker"] in cmd and ASYNC_WRAPPED_TAG not in cmd:
                    new_cmd = _build_wrapped(cmd)
                    hh["command"] = new_cmd
                    desc.append(
                        f"WRAP ({target['label']}): {cmd[:80]} -> "
                        f"async_wrapper")
                    break

    hooks["SessionStart"] = ss
    new["hooks"] = hooks
    return desc, new


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Reduce SessionStart wall time by detaching slow hooks.")
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
    print("PP SessionStart OPTIMIZER  --  ONE-TIME OWNER SETUP")
    print("=" * 60)
    print(f"Target : {SETTINGS_PATH}")
    print(f"Mode   : {'DRY RUN (no changes)' if args.dry_run else 'COMMIT'}")
    print()

    if not desc:
        print("[OK] No changes needed. SessionStart already optimal.")
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
    backup = SETTINGS_PATH.with_suffix(f".pre-pp-lag-opt-{iso}.bak")
    shutil.copy2(SETTINGS_PATH, backup)
    print(f"[BACKUP] {backup}")

    _atomic_write_json(SETTINGS_PATH, new)

    print()
    print("=" * 60)
    print("OPTIMIZED")
    print("=" * 60)
    print(f"Backup     : {backup}")
    print()
    print("NEXT STEPS:")
    print("  1. Close every active Claude Code session.")
    print("  2. Reopen Claude Code (or `claude --resume`).")
    print(f"  3. Verify timing: python {PP_PATH / 'tools' / 'measure_session_start.py'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
