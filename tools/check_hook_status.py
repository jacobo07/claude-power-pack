#!/usr/bin/env python3
"""PP Hook Status -- real-time activation snapshot.

Shows whether each PP hook is registered in ~/.claude/settings.json,
whether jit_skill_loader is wired into UserPromptSubmit, which PP
agents are installed at ~/.claude/agents/, and the five most recent
proactive advisories captured in vault/pp_agents/throttle/.

Run from anywhere. No mutation. Exit 0 iff every PP hook is
registered AND jit_skill_loader is present.

Sealed BL-HOOKS-REG-001 (2026-05-29).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

PP_PATH = Path(__file__).resolve().parents[1]
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
AGENTS_DIR = Path.home() / ".claude" / "agents"
THROTTLE_DIR = PP_PATH / "vault" / "pp_agents" / "throttle"

PP_HOOK_MARKERS = [
    ("uqf_pre_edit_gate",
     "PreToolUse",
     "pp-code-reviewer + pp-uqf-auditor on .py writes"),
    ("osa_deploy_detector",
     "PostToolUse",
     "omni-singularity on deploy command"),
    ("bug-hunter-ceps-bridge",
     "PostToolUse",
     "pp-ceps-analyst on Bash error"),
    ("session-start-check",
     "SessionStart",
     "pp-tco-advisor at session start"),
    ("jobs_woz_gate",
     "Stop",
     "Jobs/Woz judge on assistant turn"),
    ("budget_monitor",
     "SessionStart",
     "programmatic-credit runway telemetry (--quiet)"),
]


def main() -> int:
    if not SETTINGS_PATH.is_file():
        print(f"[FAIL] settings.json not at {SETTINGS_PATH}",
              file=sys.stderr)
        return 2

    raw = SETTINGS_PATH.read_text(encoding="utf-8-sig")
    try:
        data = json.loads(raw)
    except ValueError as exc:
        print(f"[FAIL] settings.json malformed: {exc}", file=sys.stderr)
        return 2

    print("=" * 60)
    print("PP AGENT STATUS")
    print("=" * 60)
    print(f"Settings: {SETTINGS_PATH}")
    print(f"PP root : {PP_PATH}")
    print()

    print("HOOKS (auto-fire when their event matches):")
    all_hooks_registered = True
    for marker, event, description in PP_HOOK_MARKERS:
        registered = marker in raw
        tag = "[OK]  " if registered else "[GAP] "
        print(f"  {tag}[{event:13s}] {marker:30s} -> {description}")
        if not registered:
            all_hooks_registered = False
    print()

    hooks = data.get("hooks", {})
    ups = hooks.get("UserPromptSubmit", [])
    jit_active = any("jit_skill_loader" in str(entry) for entry in ups)
    print("USER PROMPT SUBMIT (already active via jit_skill_loader):")
    tag = "[OK]" if jit_active else "[GAP]"
    print(f"  {tag} jit_skill_loader -> proactive dispatcher "
          "(every PP agent)")
    print()

    print("GLOBAL AGENTS (~/.claude/agents/):")
    if AGENTS_DIR.is_dir():
        pp_agents = sorted(
            list(AGENTS_DIR.glob("pp-*.md")) +
            list(AGENTS_DIR.glob("omni-*.md")))
        for agent in pp_agents:
            print(f"  [OK] {agent.stem}")
        if not pp_agents:
            print("  [GAP] no PP agents found at ~/.claude/agents/")
    else:
        print(f"  [GAP] agents dir missing: {AGENTS_DIR}")
    print()

    print("LAST ADVISORIES FIRED (vault/pp_agents/throttle/):")
    if THROTTLE_DIR.is_dir():
        entries = []
        for f in THROTTLE_DIR.glob("*.json"):
            try:
                body = json.loads(f.read_text(encoding="utf-8"))
                ts = body.get("last_fire", "")
                advisory = body.get("last_advisory", "")
                count = int(body.get("fire_count", 0))
                entries.append((ts, f.stem, count, advisory))
            except (OSError, ValueError):
                continue
        entries.sort(reverse=True)
        for ts, name, count, advisory in entries[:5]:
            short_ts = ts[:19] if ts else "unknown"
            short_adv = (advisory or "").replace("\n", " ")[:80]
            print(f"  [{short_ts}] {name:36s} fired={count:3d}  "
                  f"{short_adv}")
        if not entries:
            print("  (no advisories yet -- proactive agents stay silent "
                  "until their signal fires)")
    else:
        print(f"  (throttle dir not present yet: {THROTTLE_DIR})")
    print()

    print("=" * 60)
    if all_hooks_registered and jit_active:
        print("[ALL ACTIVE] PP agents respond automatically across "
              "every repo.")
        return 0
    print("[ACTION REQUIRED]")
    if not all_hooks_registered:
        print("  -> cd ~/.claude/skills/claude-power-pack")
        print("  -> python tools/register_global_hooks.py")
        print("  -> close + reopen Claude Code, then re-run this script.")
    if not jit_active:
        print("  -> jit_skill_loader missing from UserPromptSubmit.")
        print("  -> Verify ~/.claude/settings.json manually.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
