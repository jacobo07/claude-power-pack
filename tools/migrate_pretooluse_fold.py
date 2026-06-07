#!/usr/bin/env python3
"""
Idempotent settings.json migration for the PreToolUse hub fold.

Sibling of migrate_sessionstart_fold.py / migrate_hub_fold.py, for the
PreToolUse event's MULTI-CHAIN mechanism. Unlike Stop / UserPromptSubmit
(one dispatcher entry per event) or SessionStart (one hub process),
PreToolUse registers SEVERAL hook-dispatcher.js entries -- one per matcher
(PreToolUse-Bash-chain, PreToolUse-Edit-chain, PreToolUse-Read-chain). A
standalone PreToolUse hook is folded by:

  1. adding its script to the matching CHAIN_MAP[chain] in hook-dispatcher.js
     (done by hand, mirror-protocol committed), then
  2. removing the standalone settings.json entry so the event spawns the
     dispatcher chain instead of the standalone + the chained copy (which
     double-run -- benign but wasteful).

SAFETY CONTRACT (every guard must hold or the stray is KEPT):
  1. The target chain's dispatcher entry MUST be registered in PreToolUse (the
     fold target must run). If absent -> removing the stray would ORPHAN its
     concern -> KEEP everything for that chain.
  2. REACHABILITY: the stray's basename MUST appear in CHAIN_MAP[chain] of the
     dispatcher source (proof the chain really runs it). Intent (FOLD_MAP) is
     not enough; presence in the dispatcher source is the proof.
  3. MATCHER-COMPAT (the PreToolUse-specific critical guard): the stray's own
     matcher tokens MUST be a SUBSET of the chain entry's matcher tokens. A
     stray matched on Bash|PowerShell folded into a Bash-only chain would DROP
     PowerShell coverage -> KEEP it. This is exactly why session-file-guard /
     auto-test-gate (matcher Bash|PowerShell) are NOT in FOLD_MAP: there is no
     PowerShell-inclusive chain to fold them into without losing coverage.
  4. Only the PreToolUse event is touched; every other event is byte-untouched.
     Only FOLD_MAP basenames may be removed (the dispatcher entries themselves
     and all non-candidates are never touched).

IDEMPOTENT: a second run finds nothing removable -> no backup, no write.
Default is DRY-RUN. Pass --apply to write (backup taken first, verified).

Usage:
  python tools/migrate_pretooluse_fold.py            # dry-run
  python tools/migrate_pretooluse_fold.py --apply    # apply (backup first)
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

SETTINGS = Path(os.path.expanduser("~/.claude/settings.json"))
DISPATCHER = Path(os.path.expanduser("~/.claude/hooks/hook-dispatcher.js"))
EVENT = "PreToolUse"

# basename -> the CHAIN_MAP chain key it was folded into. A candidate is removed
# only if guards 1-3 all hold. Broad-matcher hooks (Bash|PowerShell) and
# matcher=Task / all-tools hooks are deliberately ABSENT: no compatible chain.
FOLD_MAP = {
    "windows-bash-bridge-guard.js": "PreToolUse-Bash-chain",
    "uqf_pre_edit_gate.js": "PreToolUse-Edit-chain",
    "claude_md_firewall.js": "PreToolUse-Edit-chain",
}


def _cmd(hook: dict) -> str:
    return hook.get("command", "") or ""


def _matcher_tokens(matcher: str) -> set[str]:
    return {p.strip() for p in (matcher or "").split("|") if p.strip()}


def parse_chain_map(src: str) -> dict[str, set[str]]:
    """Extract CHAIN_MAP { 'key': [ {script:'.../base.js'}, ... ] } into
    { chain_key: set(basenames) }. Line-oriented, identical model to
    migrate_hub_fold.parse_chain_map."""
    out: dict[str, set[str]] = {}
    in_map = False
    cur = None
    key_re = re.compile(r"^\s*'([A-Za-z0-9_-]+)'\s*:\s*\[")
    script_re = re.compile(r"script:\s*'([^']+)'")
    for line in src.splitlines():
        if not in_map:
            if "const CHAIN_MAP" in line:
                in_map = True
            continue
        if line.rstrip() == "};":
            break
        m = key_re.match(line)
        if m:
            cur = m.group(1)
            out.setdefault(cur, set())
            continue
        if cur:
            sm = script_re.search(line)
            if sm:
                out[cur].add(os.path.basename(sm.group(1)))
    return out


def chain_entry_matcher(groups: list, chain_key: str) -> set[str] | None:
    """Matcher tokens of the PreToolUse group whose dispatcher entry carries
    --event=chain_key. None if that chain entry is not registered."""
    for grp in groups:
        for h in grp.get("hooks", []):
            cmd = _cmd(h)
            if "hook-dispatcher.js" in cmd and f"--event={chain_key}" in cmd:
                return _matcher_tokens(grp.get("matcher", ""))
    return None


def migrate(apply: bool) -> int:
    if not SETTINGS.exists():
        print(f"FATAL: settings.json not found at {SETTINGS}")
        return 2
    if not DISPATCHER.exists():
        print(f"FATAL: dispatcher not found at {DISPATCHER}")
        return 2

    chain_map = parse_chain_map(DISPATCHER.read_text(encoding="utf-8"))
    with SETTINGS.open(encoding="utf-8") as fh:
        data = json.load(fh)  # round-trip validates JSON
    hooks = data.get("hooks", {})
    groups = hooks.get(EVENT, [])

    lines: list[str] = []
    removed = 0
    new_groups = []

    for grp in groups:
        grp_matcher = _matcher_tokens(grp.get("matcher", ""))
        kept = []
        for h in grp.get("hooks", []):
            cmd = _cmd(h)
            match = next((b for b in FOLD_MAP if b in cmd), None)
            if match and "hook-dispatcher.js" not in cmd:
                chain_key = FOLD_MAP[match]
                chain_matcher = chain_entry_matcher(groups, chain_key)
                reachable = chain_map.get(chain_key, set())
                # Guard 1: target chain must be registered.
                if chain_matcher is None:
                    lines.append(f"  KEEP {match} (guard1: {chain_key} not "
                                 f"registered -> would orphan)")
                    kept.append(h)
                    continue
                # Guard 2: dispatcher source must actually run it.
                if match not in reachable:
                    lines.append(f"  KEEP {match} (guard2: not in "
                                 f"CHAIN_MAP[{chain_key}] -> not reachable)")
                    kept.append(h)
                    continue
                # Guard 3: matcher-compat (no coverage loss).
                if not grp_matcher.issubset(chain_matcher):
                    lost = grp_matcher - chain_matcher
                    lines.append(f"  KEEP {match} (guard3: matcher "
                                 f"{sorted(grp_matcher)} not subset of "
                                 f"{chain_key} {sorted(chain_matcher)}; would "
                                 f"drop {sorted(lost)})")
                    kept.append(h)
                    continue
                removed += 1
                lines.append(f"  REMOVE {match} (folded -> {chain_key}, "
                             f"matcher {sorted(grp_matcher)} subset OK)")
                continue
            kept.append(h)
        if kept:
            ng = dict(grp)
            ng["hooks"] = kept
            new_groups.append(ng)

    before = sum(len(g.get("hooks", [])) for g in groups)
    after = sum(len(g.get("hooks", [])) for g in new_groups)
    print("\n".join(lines) if lines else "  (no FOLD_MAP candidates present)")
    print(f"\n{EVENT} entries: {before} -> {after}  (removable: {removed})")

    if removed == 0:
        print("Nothing to migrate (already folded or idempotent re-run). No write.")
        return 0

    if not apply:
        print("\nDRY-RUN. Re-run with --apply to write (backup taken first).")
        return 0

    hooks[EVENT] = new_groups
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
          f"Removed {removed} folded {EVENT} strays.")
    return 0


if __name__ == "__main__":
    sys.exit(migrate("--apply" in sys.argv[1:]))
