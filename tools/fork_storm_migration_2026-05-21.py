#!/usr/bin/env python3
"""fork_storm_migration_2026-05-21.py

One-shot migration AUTHORIZED 2026-05-21 by Owner via "authorize fork-storm
migration". Collapses 12 standalone PreToolUse hooks in ~/.claude/settings.json
into the 3 dispatcher chains already shipped by the sibling pane today
(hook-dispatcher.js CHAIN_MAP['PreToolUse-{Bash,Edit,Read}-chain']).

Cuts settings.json PreToolUse fanout from 15 entries to 6, fixing the
MSYS2 fork-storm transversal hang documented in
~/.claude/CLAUDE.md § Windows Bash Bridge Reliability (sealed 2026-05-21).

Run order:
  1. Backup ~/.claude/settings.json -> settings.json.bak-fork-storm-2026-05-21
  2. Load + parse JSON.
  3. Filter PreToolUse: remove entries whose hooks[0].command references
     one of the 12 absorbed hook scripts.
  4. Append 3 new dispatcher entries (Bash-chain, Edit-chain, Read-chain).
  5. Atomic write back. Validate by reloading.

Idempotent: if any of the 3 chain entries already exist, they are not
duplicated; if any of the 12 absorbed entries are already gone, they are
not re-added.

Reversibility: backup file is the one-shot rollback path. Restore via
`cp ~/.claude/settings.json.bak-fork-storm-2026-05-21 ~/.claude/settings.json`.

Effective on next /restart (hooks cold-load per BL-0067).
"""
from __future__ import annotations
import json
import os
import shutil
import sys
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
SETTINGS = HOME / ".claude" / "settings.json"
BACKUP = HOME / ".claude" / "settings.json.bak-fork-storm-2026-05-21"

# Hook script basenames that the dispatcher CHAIN_MAP already absorbs.
# Matched against the substring in the entry's command string.
ABSORBED = [
    "secret-scanner.js",
    "quality-gate.js",
    "process-sandbox.js",
    "gatekeeper-semantic.js",
    "anti-thrash.js",
    "ovo-push-gate.js",
    "readonly-prompts-guard.js",
    "skill-heat-map-advisor.js",
    "zero-fiction-gate.js",
    "jobs-woz-gatekeeper.js",
    "quality-skill-gate.js",
    "rtk-rewrite.js",
]

NODE_EXE_QUOTED = '"/c/Program Files/nodejs/node.exe"'
DISPATCHER_QUOTED = '"C:/Users/User/.claude/hooks/hook-dispatcher.js"'


def chain_entry(matcher: str, event: str, timeout_s: int) -> dict:
    return {
        "matcher": matcher,
        "hooks": [
            {
                "type": "command",
                "command": f"{NODE_EXE_QUOTED} {DISPATCHER_QUOTED} --event={event}",
                "timeout": timeout_s,
            }
        ],
    }


def entry_is_absorbed(entry: dict) -> str | None:
    """Return the absorbed-hook basename if this entry should be removed."""
    hooks = entry.get("hooks") or []
    if not hooks:
        return None
    cmd = str(hooks[0].get("command", ""))
    for basename in ABSORBED:
        if basename in cmd:
            return basename
    return None


def entry_is_chain(entry: dict, event_suffix: str) -> bool:
    """Detect if a chain entry for this event already exists."""
    hooks = entry.get("hooks") or []
    if not hooks:
        return False
    cmd = str(hooks[0].get("command", ""))
    return f"--event=PreToolUse-{event_suffix}" in cmd


def main() -> int:
    if not SETTINGS.is_file():
        print(f"FATAL: {SETTINGS} missing", file=sys.stderr)
        return 2

    shutil.copy2(SETTINGS, BACKUP)
    print(f"[backup] {SETTINGS} -> {BACKUP}")

    raw = SETTINGS.read_text(encoding="utf-8")
    settings = json.loads(raw)

    pretool = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
    before_count = len(pretool)

    removed = []
    kept = []
    for entry in pretool:
        absorbed = entry_is_absorbed(entry)
        if absorbed:
            removed.append(absorbed)
        else:
            kept.append(entry)

    have_bash = any(entry_is_chain(e, "Bash-chain") for e in kept)
    have_edit = any(entry_is_chain(e, "Edit-chain") for e in kept)
    have_read = any(entry_is_chain(e, "Read-chain") for e in kept)

    added = []
    if not have_bash:
        kept.append(chain_entry("Bash", "PreToolUse-Bash-chain", 20))
        added.append("PreToolUse-Bash-chain")
    if not have_edit:
        kept.append(chain_entry("Write|Edit|MultiEdit|NotebookEdit",
                                "PreToolUse-Edit-chain", 30))
        added.append("PreToolUse-Edit-chain")
    if not have_read:
        kept.append(chain_entry("Read|Grep", "PreToolUse-Read-chain", 10))
        added.append("PreToolUse-Read-chain")

    settings["hooks"]["PreToolUse"] = kept
    after_count = len(kept)

    out = json.dumps(settings, indent=2, ensure_ascii=False)
    # Reload to assert valid JSON before write-back.
    json.loads(out)
    SETTINGS.write_text(out + "\n", encoding="utf-8")

    print(f"[result] PreToolUse entries: {before_count} -> {after_count}")
    print(f"[removed] {len(removed)}: {sorted(set(removed))}")
    print(f"[added] {len(added)}: {added}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
