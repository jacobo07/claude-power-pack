#!/usr/bin/env python3
"""verify_proactive_agents.py -- sub-verifier for BL-PROACTIVE-001.

Six binary sub-checks:
  P1 core-import       proactive_core + dispatcher importable
  P2 dispatch-clean    dispatch({}) returns list (silence OK)
  P3 hook-present      hooks/jobs_woz_gate.js exists + non-empty
  P4 throttle-dir      vault/pp_agents/throttle/ creatable + writable
  P5 agents-proactive  7 PP agents at ~/.claude/agents/ all carry the
                       'PROACTIVE MODE' section
  P6 decorator-wired   jit_skill_loader has @_pp_proactive_inject in
                       its decorator stack

Exit 0 iff all 6 pass. Prints PROACTIVE_PROBE=N/6 line for verify_spp.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

HOME = Path.home()
AGENTS_DIR = HOME / ".claude" / "agents"


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    # P1 core-import
    try:
        from modules.pp_agents.proactive_core import (
            AgentConfig,
            ProactiveSignal,
            evaluate_and_fire,
        )
        from modules.pp_agents.proactive_dispatcher import (
            dispatch,
            dispatch_to_additional_context,
            MAX_ADVISORIES_PER_TURN,
        )
        checks.append(("core-import", True,
                       f"cap={MAX_ADVISORIES_PER_TURN}"))
    except Exception as exc:
        checks.append(("core-import", False,
                       f"{type(exc).__name__}: {exc}"))
        # Without imports the rest is moot; report and continue degraded.

    # P2 dispatch-clean
    try:
        from modules.pp_agents.proactive_dispatcher import dispatch
        result = dispatch({"project": "verify-probe"})
        if isinstance(result, list):
            checks.append(("dispatch-clean", True,
                           f"{len(result)} advisor(ies) (0 expected)"))
        else:
            checks.append(("dispatch-clean", False,
                           f"unexpected type: {type(result).__name__}"))
    except Exception as exc:
        checks.append(("dispatch-clean", False,
                       f"{type(exc).__name__}: {exc}"))

    # P3 hook-present
    hook = PP / "hooks" / "jobs_woz_gate.js"
    if hook.is_file() and hook.stat().st_size > 200:
        checks.append(("hook-present", True,
                       f"{hook.stat().st_size} bytes"))
    else:
        checks.append(("hook-present", False,
                       f"missing or empty: {hook}"))

    # P4 throttle-dir
    throttle_dir = PP / "vault" / "pp_agents" / "throttle"
    try:
        throttle_dir.mkdir(parents=True, exist_ok=True)
        probe = throttle_dir / ".verify_probe.json"
        probe.write_text(json.dumps({"probe": True}), encoding="utf-8")
        ok = probe.is_file() and probe.stat().st_size > 0
        try:
            probe.unlink()
        except OSError:
            pass
        if ok:
            checks.append(("throttle-dir", True, str(throttle_dir)))
        else:
            checks.append(("throttle-dir", False, "probe write failed"))
    except Exception as exc:
        checks.append(("throttle-dir", False,
                       f"{type(exc).__name__}: {exc}"))

    # P5 agents-proactive
    expected = [
        "omni-singularity.md",
        "pp-code-reviewer.md",
        "pp-monitor.md",
        "pp-uqf-auditor.md",
        "pp-tco-advisor.md",
        "pp-ceps-analyst.md",
        "pp-never-again.md",
    ]
    missing: list[str] = []
    no_marker: list[str] = []
    for name in expected:
        p = AGENTS_DIR / name
        if not p.is_file():
            missing.append(name)
            continue
        body = p.read_text(encoding="utf-8")
        if "PROACTIVE MODE" not in body:
            no_marker.append(name)
    if not missing and not no_marker:
        checks.append(("agents-proactive", True,
                       f"7/7 carry PROACTIVE MODE section"))
    else:
        checks.append(("agents-proactive", False,
                       f"missing={missing} no_marker={no_marker}"))

    # P6 decorator-wired
    loader = PP / "tools" / "jit_skill_loader.py"
    if not loader.is_file():
        checks.append(("decorator-wired", False, f"missing: {loader}"))
    else:
        body = loader.read_text(encoding="utf-8")
        has_def = "def _pp_proactive_inject" in body
        has_use = "@_pp_proactive_inject" in body
        if has_def and has_use:
            checks.append(("decorator-wired", True,
                           "def + @stack both present"))
        else:
            checks.append(("decorator-wired", False,
                           f"def={has_def} use={has_use}"))

    passes_n = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    for name, ok, msg in checks:
        tag = "PASS" if ok else "FAIL"
        print(f"{tag}  {name:18s} {msg}")
    print()
    print(f"PROACTIVE_PROBE={passes_n}/{total}")
    return 0 if passes_n == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
