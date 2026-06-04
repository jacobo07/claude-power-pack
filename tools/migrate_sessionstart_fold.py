#!/usr/bin/env python3
"""
Idempotent settings.json migration for the SessionStart hub fold.

Sibling of migrate_hub_fold.py, but for the DIFFERENT mechanism SessionStart
uses. migrate_hub_fold.py folds Stop / UserPromptSubmit / PostToolUse into
hook-dispatcher.js CHAIN_MAP and EXPLICITLY leaves SessionStart untouched.
SessionStart instead uses session_start_hub.js -- a single Node process that
detached-spawns the folded hooks (SCS C23). So the migration is:

  Remove the standalone SessionStart entries whose concern session_start_hub.js
  now spawns, so SessionStart spawns ONE hub process instead of N.

SAFETY CONTRACT (every guard must hold or the stray is KEPT):
  1. session_start_hub.js MUST be registered as a SessionStart entry (the fold
     target must run at runtime). If it is absent, removing a stray would
     ORPHAN the concern -> skip everything, remove nothing.
  2. REACHABILITY (the strong guard): a stray is removed ONLY if the hub source
     ACTUALLY references its basename (i.e. the hub really spawns it). A
     basename in FOLD_SET that the hub does not spawn is NOT reachable via the
     hub -> KEEP it. Presence in this list is intent; presence in the hub
     source is proof.
  3. Only the SessionStart event is considered. Every other event is left
     byte-untouched.
  4. Only FOLD_SET basenames may be removed. The hub entry itself and every
     non-candidate (lazarus-*, restart-target-consumer, learning-sentinel,
     token-shield-refresh, terminal-slot-recorder) are never touched -- they
     are stdout-consumed or load-bearing recovery (UKDL T-SESSIONFOLD-001).

IDEMPOTENT: a second run finds nothing removable -> no backup, no write.
Default is DRY-RUN. Pass --apply to write (backup taken first, verified).

Usage:
  python tools/migrate_sessionstart_fold.py            # dry-run
  python tools/migrate_sessionstart_fold.py --apply    # apply (backup first)
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

SETTINGS = Path(os.path.expanduser("~/.claude/settings.json"))
PP = Path(__file__).resolve().parents[1]
HUB = PP / "hooks" / "session_start_hub.js"
HUB_BASENAME = "session_start_hub.js"

# Candidate strays (intent). A candidate is removed only if guard #2 holds.
# These are the fire-and-forget hooks folded into the hub (BL-SESSION-FOLD-001).
FOLD_SET = [
    "mark-live-session.js",
    "zero-command-bootstrap.js",
    "first-time-project.js",
]


def _cmd(hook: dict) -> str:
    return hook.get("command", "") or ""


def hub_referenced_basenames() -> set[str]:
    """Basenames the hub source actually mentions (the reachability proof)."""
    try:
        src = HUB.read_text(encoding="utf-8")
    except OSError:
        return set()
    return {b for b in FOLD_SET if b in src}


def hub_is_registered(groups: list) -> bool:
    for grp in groups:
        for h in grp.get("hooks", []):
            if HUB_BASENAME in _cmd(h):
                return True
    return False


def migrate(apply: bool) -> int:
    if not SETTINGS.exists():
        print(f"FATAL: settings.json not found at {SETTINGS}")
        return 2
    if not HUB.exists():
        print(f"FATAL: hub not found at {HUB} (cannot prove reachability)")
        return 2

    with SETTINGS.open(encoding="utf-8") as fh:
        data = json.load(fh)  # round-trip validates JSON
    hooks = data.get("hooks", {})
    groups = hooks.get("SessionStart", [])

    # Guard #1: the fold target must be registered, else removing orphans.
    if not hub_is_registered(groups):
        print("SKIP: session_start_hub.js is NOT a SessionStart entry. "
              "Removing strays would orphan their concern. Register the hub "
              "first. Nothing removed.")
        return 0

    reachable = hub_referenced_basenames()
    lines: list[str] = []
    removed = 0
    new_groups = []

    for grp in groups:
        kept = []
        for h in grp.get("hooks", []):
            cmd = _cmd(h)
            match = next((b for b in FOLD_SET if b in cmd), None)
            # Never remove the hub itself; only FOLD_SET candidates.
            if match and HUB_BASENAME not in cmd:
                if match in reachable:
                    removed += 1
                    lines.append(f"  REMOVE {match} (hub spawns it -> reachable)")
                    continue
                lines.append(f"  KEEP {match} (candidate but hub does NOT "
                             f"spawn it -> not reachable)")
            kept.append(h)
        if kept:
            ng = dict(grp)
            ng["hooks"] = kept
            new_groups.append(ng)

    before = sum(len(g.get("hooks", [])) for g in groups)
    after = sum(len(g.get("hooks", [])) for g in new_groups)
    print("\n".join(lines) if lines else "  (no FOLD_SET candidates present)")
    print(f"\nSessionStart entries: {before} -> {after}  (removable: {removed})")

    if removed == 0:
        print("Nothing to migrate (already folded or idempotent re-run). No write.")
        return 0

    if not apply:
        print("\nDRY-RUN. Re-run with --apply to write (backup taken first).")
        return 0

    hooks["SessionStart"] = new_groups
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = SETTINGS.with_suffix(SETTINGS.suffix + f".bak.{ts}")
    shutil.copy2(SETTINGS, backup)
    if not backup.exists() or backup.stat().st_size == 0:
        print(f"FATAL: backup verification failed ({backup}). Aborting, no write.")
        return 2
    print(f"\nBackup OK: {backup} ({backup.stat().st_size} bytes)")

    with SETTINGS.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    with SETTINGS.open(encoding="utf-8") as fh:
        json.load(fh)  # re-validate
    print(f"APPLIED. settings.json rewritten, JSON valid. "
          f"Removed {removed} folded SessionStart strays.")
    return 0


if __name__ == "__main__":
    sys.exit(migrate("--apply" in sys.argv[1:]))
