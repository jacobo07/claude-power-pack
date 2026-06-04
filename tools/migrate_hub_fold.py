#!/usr/bin/env python3
"""
Idempotent settings.json migration for the hook-hub fold.

Removes the standalone Stop / UserPromptSubmit / PostToolUse hook entries that
have already been folded into hook-dispatcher.js CHAIN_MAP AND are reachable at
runtime, so each event spawns ONE dispatcher process instead of N (the standalone
+ the chained copy were double-running, benign but wasteful).

SAFETY CONTRACT (every guard must hold or the stray is KEPT):
  1. The event must carry a hook-dispatcher.js entry (the chain target) --
     otherwise removing the stray would orphan it. Skip the whole event if absent.
  2. REACHABILITY (the strong guard): a stray is removed ONLY if it is actually
     reachable at runtime. The dispatcher dispatches by the EXACT `--event=X` arg
     settings.json passes: `CHAIN_MAP[X]` is tried first, else `EVENT_MAP[X]`.
     So the stray's basename must live in `CHAIN_MAP[X]` where X is the literal
     --event arg of THIS event's dispatcher invocation. Presence in the
     dispatcher source is NOT enough -- a chain that no --event arg names is an
     ORPHAN (e.g. UserPromptSubmit-chain / PostToolUse-Bash-chain exist in source
     but settings.json calls --event=*-default, which routes to EVENT_MAP, never
     the chain). Removing an orphan-chain's stray would DROP it. KEEP it.
  3. Only Stop / UserPromptSubmit / PostToolUse are considered. PreToolUse,
     SessionStart, SessionEnd are left byte-untouched (not folded yet).
  4. Explicit candidate list (FOLD_MAP) bounds what may be removed; non-candidates
     (hook-dispatcher.js, auto-compact-stop-launcher.ps1, kg-sync-hook.js, ...)
     are never touched.

IDEMPOTENT: a second run finds nothing removable -> no backup, no write.
Default is DRY-RUN. Pass --apply to write (backup taken first, verified).

Usage:
  python tools/migrate_hub_fold.py            # dry-run
  python tools/migrate_hub_fold.py --apply    # apply (backup first)
"""
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone

SETTINGS = os.path.expanduser("~/.claude/settings.json")
DISPATCHER = os.path.expanduser("~/.claude/hooks/hook-dispatcher.js")

# Candidate strays per event (what we INTEND to fold). A candidate is removed
# only if guard #2 (reachability) also holds.
FOLD_MAP = {
    "Stop": [
        "claude_md_linter_stop.js", "mark-live-session.js",
        "research-intent-detector.js", "background-verifier.js",
        "jobs_woz_gate.js", "jit_correlate_stop.js",
        "session_snapshot_stop.js",
    ],
    "UserPromptSubmit": [
        "correction-guard.js", "prd-keyword-sentinel.js",
        "jit_skill_loader.py",
    ],
    "PostToolUse": [
        "tty-restore.js", "bug-hunter-learning.js",
        "osa_deploy_detector.js", "bug-hunter-ceps-bridge.js",
    ],
}


def _cmd(hook):
    return hook.get("command", "") or ""


def parse_chain_map(disp_src):
    """Extract CHAIN_MAP { 'key': [ {script:'.../base.js'}, ... ] } from the
    dispatcher source into { chain_key: set(basenames) }. Line-oriented: track
    the current chain key (a line like  'Some-chain': [ ) and collect basenames
    from `script: '...'` lines until the CHAIN_MAP object closes (a `};` at
    column 0)."""
    out = {}
    in_map = False
    cur = None
    key_re = re.compile(r"^\s*'([A-Za-z0-9_-]+)'\s*:\s*\[")
    script_re = re.compile(r"script:\s*'([^']+)'")
    for line in disp_src.splitlines():
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


def event_arg(groups):
    """The literal --event=X arg of the hook-dispatcher.js invocation in this
    event's groups (the runtime dispatch key). None if no dispatcher entry."""
    for grp in groups:
        for h in grp.get("hooks", []):
            cmd = _cmd(h)
            if "hook-dispatcher.js" in cmd:
                m = re.search(r"--event=(\S+)", cmd)
                if m:
                    return m.group(1).strip('"')
    return None


def migrate(apply):
    if not os.path.exists(SETTINGS):
        print(f"FATAL: settings.json not found at {SETTINGS}")
        return 2
    if not os.path.exists(DISPATCHER):
        print(f"FATAL: dispatcher not found at {DISPATCHER}")
        return 2

    chain_map = parse_chain_map(open(DISPATCHER, encoding="utf-8").read())
    with open(SETTINGS, encoding="utf-8") as fh:
        data = json.load(fh)  # round-trip validates JSON
    hooks = data.get("hooks", {})

    lines = []
    removed_total = 0

    for event, candidates in FOLD_MAP.items():
        groups = hooks.get(event, [])
        arg = event_arg(groups)
        if arg is None:
            lines.append(f"{event}: SKIP (no hook-dispatcher.js entry -> would orphan)")
            continue
        reachable = chain_map.get(arg)
        if reachable is None:
            lines.append(
                f"{event}: SKIP -- dispatcher arg --event={arg} is NOT a CHAIN_MAP "
                f"key (routes to EVENT_MAP bundle). The fold chain is an ORPHAN; "
                f"removing strays would drop them. Wire the chain first."
            )
            continue

        before = sum(len(grp.get("hooks", [])) for grp in groups)
        new_groups = []
        for grp in groups:
            kept = []
            for h in grp.get("hooks", []):
                cmd = _cmd(h)
                match = next((b for b in candidates if b in cmd), None)
                if match:
                    if match in reachable:
                        removed_total += 1
                        lines.append(
                            f"  {event}: REMOVE {match} (reachable via --event={arg})")
                        continue
                    lines.append(
                        f"  {event}: KEEP {match} (in candidates but NOT in "
                        f"CHAIN_MAP[{arg}] -> not reachable)")
                kept.append(h)
            if kept:
                ng = dict(grp)
                ng["hooks"] = kept
                new_groups.append(ng)
        after = sum(len(grp.get("hooks", [])) for grp in new_groups)
        hooks[event] = new_groups
        lines.append(f"{event}: {before} -> {after} hook entries")

    print("\n".join(lines))
    print(f"\nTOTAL removable: {removed_total}")

    if removed_total == 0:
        print("Nothing to migrate (already folded or idempotent re-run). No write.")
        return 0

    if not apply:
        print("\nDRY-RUN. Re-run with --apply to write (backup taken first).")
        return 0

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = f"{SETTINGS}.bak.{ts}"
    shutil.copy2(SETTINGS, backup)
    if not os.path.exists(backup) or os.path.getsize(backup) == 0:
        print(f"FATAL: backup verification failed ({backup}). Aborting, no write.")
        return 2
    print(f"\nBackup OK: {backup} ({os.path.getsize(backup)} bytes)")

    with open(SETTINGS, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    with open(SETTINGS, encoding="utf-8") as fh:
        json.load(fh)  # re-validate
    print(f"APPLIED. settings.json rewritten, JSON valid. Removed {removed_total} folded strays.")
    return 0


if __name__ == "__main__":
    sys.exit(migrate("--apply" in sys.argv[1:]))
