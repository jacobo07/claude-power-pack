#!/usr/bin/env python3
"""verify_hard_rules.py -- sub-verifier for BL-HARDRULE-001.

Seven binary sub-checks:
  H1 extractor          modules.hard_rules.extractor importable +
                        load_candidates() returns list
  H2 writer             modules.hard_rules.writer importable +
                        list_hard_rules returns list
  H3 cli                tools/bug_to_hardrule.py exists; --list rc=0
  H4 cascade-signal     modules.pp_agents.signals.cascade importable
  H5 dispatcher         pp-cascade-guard registered in dispatcher
  H6 agent-file         ~/.claude/agents/pp-cascade-guard.md present
  H7 archive-or-claude  CLAUDE.md OR vault/hard_rules/HARD_RULES.md
                        has the sentinel block

Exit 0 iff all 7 pass. Prints HARDRULES_PROBE=N/7 line for verify_spp.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

HOME = Path.home()


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    try:
        from modules.hard_rules.extractor import load_candidates
        cands = load_candidates()
        if isinstance(cands, list):
            checks.append(("extractor", True,
                           f"{len(cands)} candidate(s)"))
        else:
            checks.append(("extractor", False,
                           f"unexpected {type(cands).__name__}"))
    except Exception as exc:
        checks.append(("extractor", False,
                       f"{type(exc).__name__}: {exc}"))

    try:
        from modules.hard_rules.writer import list_hard_rules
        rules = list_hard_rules()
        if isinstance(rules, list):
            checks.append(("writer", True,
                           f"{len(rules)} rules listed"))
        else:
            checks.append(("writer", False,
                           f"unexpected {type(rules).__name__}"))
    except Exception as exc:
        checks.append(("writer", False,
                       f"{type(exc).__name__}: {exc}"))

    cli = PP / "tools" / "bug_to_hardrule.py"
    if not cli.is_file():
        checks.append(("cli", False, f"missing: {cli}"))
    else:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run(
            [sys.executable, str(cli), "--list"],
            capture_output=True, text=True, timeout=30, env=env,
        )
        if proc.returncode == 0:
            checks.append(("cli", True, "--list rc=0"))
        else:
            checks.append(("cli", False,
                           f"--list rc={proc.returncode}"))

    try:
        from modules.pp_agents.signals.cascade import _build_cascade_map
        m = _build_cascade_map()
        if isinstance(m, dict):
            checks.append(("cascade-signal", True,
                           f"{len(m)} pattern(s)"))
        else:
            checks.append(("cascade-signal", False,
                           f"unexpected {type(m).__name__}"))
    except Exception as exc:
        checks.append(("cascade-signal", False,
                       f"{type(exc).__name__}: {exc}"))

    try:
        from modules.pp_agents.proactive_dispatcher import AGENT_CONFIGS
        if "pp-cascade-guard" in AGENT_CONFIGS:
            checks.append(("dispatcher", True,
                           "pp-cascade-guard registered"))
        else:
            checks.append(("dispatcher", False,
                           f"agents: {sorted(AGENT_CONFIGS.keys())}"))
    except Exception as exc:
        checks.append(("dispatcher", False,
                       f"{type(exc).__name__}: {exc}"))

    agent_file = HOME / ".claude" / "agents" / "pp-cascade-guard.md"
    if agent_file.is_file() and agent_file.stat().st_size > 200:
        checks.append(("agent-file", True,
                       f"{agent_file.stat().st_size} bytes"))
    else:
        checks.append(("agent-file", False,
                       f"is_file={agent_file.is_file()}"))

    claude_md = PP / "CLAUDE.md"
    archive = PP / "vault" / "hard_rules" / "HARD_RULES.md"
    sentinel_start = "<!-- PP-HARD-RULES-START -->"
    sentinel_end = "<!-- PP-HARD-RULES-END -->"
    has_block = False
    for path in (claude_md, archive):
        if not path.is_file():
            continue
        body = path.read_text(encoding="utf-8-sig")
        if sentinel_start in body and sentinel_end in body:
            has_block = True
            break
    if has_block:
        checks.append(("archive-or-claude", True,
                       "sentinel block present"))
    else:
        checks.append(("archive-or-claude", False,
                       "sentinel block not found"))

    passes_n = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    for name, ok, msg in checks:
        tag = "PASS" if ok else "FAIL"
        print(f"{tag}  {name:18s} {msg}")
    print()
    print(f"HARDRULES_PROBE={passes_n}/{total}")
    return 0 if passes_n == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
